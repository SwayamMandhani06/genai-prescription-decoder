"""
Unit tests for Phase 8 Confidence Estimation Service.
Verifies:
- Service initialization and default insufficient_data state
- Independent multi-medicine evaluation
- Preserving field-level confidence
- Controlled calibration fitting and state transition
"""

import pytest
from backend.app.multimodal.schemas import (
    PrescriptionExtractionResult,
    ExtractedMedicine,
    ExtractedField,
    ModelMetadata,
)
from ai.confidence.service import ConfidenceEstimationService
from ai.confidence.schemas import PrescriptionConfidenceAssessment


@pytest.fixture
def mock_multi_medicine_extraction():
    return PrescriptionExtractionResult(
        prescription_id="TEST-RX-CONF-001",
        original_image_url="/uploads/test.png",
        source_image_sha256="1234567890abcdef" * 4,
        model=ModelMetadata(
            provider="mock",
            model_id="gemini-3.8-flash",
            model_version="1.0",
            prompt_version="prompt_v1",
            config_version="v1",
            is_mock=True,
        ),
        medicines=[
            ExtractedMedicine(
                medicine_name=ExtractedField(
                    value="Paracetamol 500mg",
                    status="confident",
                    presence="present",
                    extraction_state="extracted",
                ),
                dosage=ExtractedField(
                    value="500 mg",
                    status="confident",
                    presence="present",
                    extraction_state="extracted",
                ),
                frequency=ExtractedField(
                    value="1-0-1",
                    status="confident",
                    presence="present",
                    extraction_state="extracted",
                ),
                duration=ExtractedField(
                    value="3 days",
                    status="confident",
                    presence="present",
                    extraction_state="extracted",
                ),
            ),
            ExtractedMedicine(
                medicine_name=ExtractedField(
                    value="Amox...",
                    status="uncertain",
                    presence="present",
                    extraction_state="ambiguous",
                    candidates=["Amoxicillin", "Amikacin"],
                ),
                dosage=ExtractedField(
                    value="250 mg",
                    status="uncertain",
                    presence="present",
                    extraction_state="ambiguous",
                ),
                frequency=ExtractedField(
                    value="TDS",
                    status="confident",
                    presence="present",
                    extraction_state="extracted",
                ),
                duration=ExtractedField(
                    value="5 days",
                    status="confident",
                    presence="present",
                    extraction_state="extracted",
                ),
            ),
        ],
        fields={
            "medicine_name": ExtractedField(value="Paracetamol 500mg", status="confident"),
            "dosage": ExtractedField(value="500 mg", status="confident"),
        },
        requires_human_review=True,
        duration_seconds=0.12,
    )


class TestConfidenceService:
    def test_default_service_reports_insufficient_data(self, mock_multi_medicine_extraction):
        service = ConfidenceEstimationService()
        assessment = service.evaluate_prescription_confidence(mock_multi_medicine_extraction)

        assert isinstance(assessment, PrescriptionConfidenceAssessment)
        assert assessment.prescription_id == "TEST-RX-CONF-001"
        assert assessment.calibration_status == "insufficient_data"
        assert assessment.overall_calibrated_confidence is None
        assert assessment.overall_raw_score > 0.0

    def test_multi_medicine_independent_confidence(self, mock_multi_medicine_extraction):
        service = ConfidenceEstimationService()
        assessment = service.evaluate_prescription_confidence(mock_multi_medicine_extraction)

        assert len(assessment.medicines) == 2
        med_1 = assessment.medicines[0]
        med_2 = assessment.medicines[1]

        # Medicine 1 is confident
        assert med_1.medicine_name.status == "confident"
        assert med_1.overall_raw_confidence > 0.85
        assert len(med_1.conflict_flags) == 0

        # Medicine 2 is uncertain and contains conflict flags
        assert med_2.medicine_name.status == "uncertain"
        assert med_2.overall_raw_confidence < 0.80
        assert med_2.overall_raw_confidence < med_1.overall_raw_confidence
        assert "AMBIGUOUS_CURSIVE_STROKE" in med_2.conflict_flags

        # Medicine 1 does NOT inflate Medicine 2's confidence
        assert med_1.overall_raw_confidence != med_2.overall_raw_confidence

    def test_fit_calibrator_with_adequate_samples_calibrates(self, mock_multi_medicine_extraction):
        service = ConfidenceEstimationService()
        scores = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.82, 0.85, 0.88, 0.90, 0.92, 0.94, 0.95, 0.96, 0.98]
        labels = [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        service.fit_calibrator(scores, labels, method="platt_scaling")
        assert service.calibration_status == "calibrated"

        assessment = service.evaluate_prescription_confidence(mock_multi_medicine_extraction)
        assert assessment.calibration_status == "calibrated"
        assert assessment.overall_calibrated_confidence is not None
        assert 0.0 <= assessment.overall_calibrated_confidence <= 1.0

        # Field-level calibrated values are populated
        assert assessment.medicines[0].overall_calibrated_confidence is not None

    def test_n7_curated_dataset_insufficient_for_calibration(self, mock_multi_medicine_extraction):
        """
        Verifies that the N=7 curated development dataset is strictly safeguarded:
        It must NOT be used to claim statistical calibration, remaining 'insufficient_data'.
        """
        service = ConfidenceEstimationService()
        n7_scores = [0.95, 0.92, 0.88, 0.75, 0.60, 0.50, 0.40]
        n7_labels = [1, 1, 1, 1, 0, 0, 0]

        service.fit_calibrator(n7_scores, n7_labels, method="platt_scaling")
        assert service.calibration_status == "insufficient_data"

        assessment = service.evaluate_prescription_confidence(mock_multi_medicine_extraction)
        assert assessment.calibration_status == "insufficient_data"
        assert assessment.overall_calibrated_confidence is None

    def test_synthetic_n15_cohort_marked_non_clinical(self):
        """
        Verifies that N=15 synthetic verification metrics are explicitly labeled
        as non-clinical evidence (dataset_type='synthetic_verification', clinical_evidence=False).
        """
        service = ConfidenceEstimationService()
        scores = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.82, 0.85, 0.88, 0.90, 0.92, 0.94, 0.95, 0.96, 0.98]
        labels = [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        metrics = service.evaluate_metrics(
            scores=scores,
            labels=labels,
            dataset_type="synthetic_verification",
            clinical_evidence=False,
        )
        assert metrics.dataset_type == "synthetic_verification"
        assert metrics.clinical_evidence is False
        assert metrics.sample_count == 15
        assert metrics.ece >= 0.0

