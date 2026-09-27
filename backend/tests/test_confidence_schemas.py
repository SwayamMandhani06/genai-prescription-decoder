"""
Unit tests for Phase 8 Confidence Schemas.
Verifies:
- RawConfidenceSignal schema and invariants
- CalibratedConfidence schema and status definitions
- FieldConfidenceAssessment schema
- MedicineIdentityConfidence visual vs reference decoupling
- DosageConfidenceAssessment visual grounding and formulation mismatch
"""

import pytest
from pydantic import ValidationError
from ai.confidence.schemas import (
    RawConfidenceSignal,
    CalibratedConfidence,
    FieldConfidenceAssessment,
    MedicineIdentityConfidence,
    DosageConfidenceAssessment,
    MedicineConfidenceAssessment,
    PrescriptionConfidenceAssessment,
    CalibrationBin,
    CalibrationMetrics,
)


class TestConfidenceSchemas:
    def test_raw_confidence_signal_structure(self):
        sig = RawConfidenceSignal(
            source="multimodal_gemini-3.8-flash",
            raw_value=0.88,
            signal_type="model_token_logprob_surrogate",
            model_version="gemini-3.8-flash",
            config_version="v1.0",
        )
        assert sig.source == "multimodal_gemini-3.8-flash"
        assert sig.raw_value == 0.88
        assert sig.signal_type == "model_token_logprob_surrogate"

    def test_raw_confidence_signal_null_value_for_absent(self):
        sig = RawConfidenceSignal(
            source="multimodal_gemini-3.8-flash",
            raw_value=None,
            signal_type="absent_field_null_signal",
        )
        assert sig.raw_value is None

    def test_calibrated_confidence_statuses(self):
        # 1. Valid calibrated
        cal = CalibratedConfidence(
            value=0.82,
            calibration_method="platt_scaling",
            calibration_version="1.0.0",
            calibration_status="calibrated",
        )
        assert cal.value == 0.82
        assert cal.calibration_status == "calibrated"

        # 2. Insufficient data status (value must be None)
        insufficient = CalibratedConfidence(
            value=None,
            calibration_method="platt_scaling",
            calibration_status="insufficient_data",
        )
        assert insufficient.value is None
        assert insufficient.calibration_status == "insufficient_data"

        # 3. Invalid status rejected
        with pytest.raises(ValidationError):
            CalibratedConfidence(
                value=0.5,
                calibration_status="arbitrary_fabricated_status",  # type: ignore
            )

    def test_dosage_confidence_preserves_visual_grounding_independently(self):
        raw_sig = RawConfidenceSignal(
            source="multimodal_gemini-3.8-flash",
            raw_value=0.91,
            signal_type="model_confident_visual_stroke",
        )
        cal = CalibratedConfidence(
            value=None,
            calibration_status="insufficient_data",
        )
        dosage_assessment = DosageConfidenceAssessment(
            observed_dosage="1000 mg",
            reference_strength="625 mg",
            visual_extraction_confidence=raw_sig,
            reference_support_status="mismatch",
            calibrated=cal,
            explanation="Visually observed dosage 1000 mg is evaluated independently of reference strength 625 mg.",
        )
        # Dosage confidence is visual, NOT inflated by reference
        assert dosage_assessment.observed_dosage == "1000 mg"
        assert dosage_assessment.reference_strength == "625 mg"
        assert dosage_assessment.reference_support_status == "mismatch"
        assert dosage_assessment.visual_extraction_confidence.raw_value == 0.91

    def test_medicine_identity_confidence_decouples_visual_and_retrieval(self):
        visual_sig = RawConfidenceSignal(
            source="multimodal_gemini-3.8-flash",
            raw_value=0.45,
            signal_type="model_ambiguous_cursive_stroke",
        )
        retrieval_sig = RawConfidenceSignal(
            source="rag_cdsco",
            raw_value=0.98,
            signal_type="retrieval_match_token_overlap",
        )
        identity_conf = MedicineIdentityConfidence(
            visual_extraction_confidence=visual_sig,
            reference_correspondence_confidence=retrieval_sig,
            conflict_detected=True,
            conflict_note="Visual stroke is ambiguous (0.45) despite high retrieval score (0.98).",
        )
        assert identity_conf.visual_extraction_confidence.raw_value == 0.45
        assert identity_conf.reference_correspondence_confidence.raw_value == 0.98
        assert identity_conf.conflict_detected is True
        assert identity_conf.combined_calibrated is None
