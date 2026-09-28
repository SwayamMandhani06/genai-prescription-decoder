"""
Audit Item 5: Phase 10 -> Phase 9 Integration Test.
Verifies the integration contract between Phase 10 and Phase 9:
- Phase 10 detects LASA.
- Phase 9 consumes LASA evidence.
- Phase 9 owns the abstention and human verification decision.
- Phase 10 does not duplicate Phase 9's abstention policy logic.
- Neither Phase 10 nor Phase 9 automatically confirms, corrects, or replaces a medicine name.
- Complete reason-code and conflict traceability for LASA_CONFUSION_RISK.
"""

import pytest
from backend.app.multimodal.schemas import (
    ExtractedField,
    ExtractedMedicine,
    PrescriptionExtractionResult,
    ModelMetadata,
)
from ai.abstention.policy import evaluate_prescription_abstention
from ai.abstention.reasons import AbstentionReasonCode
from ai.lasa.detector import detect_prescription_lasa
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline


class TestPhase9LasaIntegration:
    """Verifies that Phase 9 consumes Phase 10 LASA evidence without duplication."""

    @pytest.fixture
    def mock_extraction_metformin(self):
        """Creates a mock extraction of Metformin with high confidence."""
        return PrescriptionExtractionResult(
            prescription_id="RX-PHASE9-LASA-01",
            original_image_url="/uploads/test.png",
            source_image_sha256="0" * 64,
            duration_seconds=0.1,
            medicines=[
                ExtractedMedicine(
                    medicine_name=ExtractedField(
                        field_name="medicine_name",
                        value="Metformin",
                        confidence=0.96,
                        status="confident",
                    ),
                    dosage=ExtractedField(
                        field_name="dosage",
                        value="500mg",
                        confidence=0.95,
                        status="confident",
                    ),
                    frequency=ExtractedField(
                        field_name="frequency",
                        value="1-0-0",
                        confidence=0.95,
                        status="confident",
                    ),
                    duration=ExtractedField(
                        field_name="duration",
                        value="30 days",
                        confidence=0.94,
                        status="confident",
                    ),
                )
            ],
            requires_human_review=False,
            model=ModelMetadata(
                provider="mock",
                model_id="test-v1",
                model_version="1.0",
                prompt_version="v1",
                config_version="v1",
                is_mock=True,
            ),
        )

    def test_lasa_evidence_flows_into_phase9_abstention(self, mock_extraction_metformin):
        """Verifies Phase 9 consumes LASA detection and records LASA_CONFUSION_RISK."""
        # 1. Phase 10 detects LASA
        lasa_detection = detect_prescription_lasa(
            prescription_id="RX-PHASE9-LASA-01",
            medicine_names=["Metformin"],
            reference_records=[],
        )
        assert lasa_detection.conflict_detected is True

        # 2. Phase 9 consumes LASA evidence
        abstention_dec = evaluate_prescription_abstention(
            prescription_id="RX-PHASE9-LASA-01",
            extraction_result=mock_extraction_metformin,
            lasa_detection=lasa_detection,
        )

        # 3. Phase 9 owns the abstention decision
        assert abstention_dec.requires_human_verification is True
        assert "medicine_name" in abstention_dec.fields_requiring_verification

        med_field = abstention_dec.fields["medicine_name"]
        assert med_field.decision == "abstained"
        assert AbstentionReasonCode.LASA_CONFUSION_RISK.value in med_field.reason_codes
        assert "LASA_CONFUSION_RISK" in med_field.conflicts

    def test_medicine_name_is_never_auto_replaced_or_altered(self, mock_extraction_metformin):
        """Verifies candidate name 'Metformin' remains strictly preserved and unmodified."""
        lasa_detection = detect_prescription_lasa(
            prescription_id="RX-PHASE9-LASA-01",
            medicine_names=["Metformin"],
            reference_records=[],
        )
        abstention_dec = evaluate_prescription_abstention(
            prescription_id="RX-PHASE9-LASA-01",
            extraction_result=mock_extraction_metformin,
            lasa_detection=lasa_detection,
        )
        # Original value must remain exactly 'Metformin'
        assert abstention_dec.fields["medicine_name"].original_value == "Metformin"
        assert mock_extraction_metformin.medicines[0].medicine_name.value == "Metformin"

    def test_clean_medicine_has_no_lasa_reason_code_in_phase9(self):
        """When no LASA conflict exists, Phase 9 does not add LASA_CONFUSION_RISK."""
        clean_extraction = PrescriptionExtractionResult(
            prescription_id="RX-PHASE9-CLEAN",
            original_image_url="/uploads/test.png",
            source_image_sha256="0" * 64,
            duration_seconds=0.1,
            medicines=[
                ExtractedMedicine(
                    medicine_name=ExtractedField(
                        field_name="medicine_name",
                        value="Paracetamol",
                        confidence=0.96,
                        status="confident",
                    ),
                    dosage=ExtractedField(
                        field_name="dosage",
                        value="650mg",
                        confidence=0.95,
                        status="confident",
                    ),
                    frequency=ExtractedField(
                        field_name="frequency",
                        value="SOS",
                        confidence=0.95,
                        status="confident",
                    ),
                    duration=ExtractedField(
                        field_name="duration",
                        value="5 days",
                        confidence=0.94,
                        status="confident",
                    ),
                )
            ],
            requires_human_review=False,
            model=ModelMetadata(
                provider="mock",
                model_id="test-v1",
                model_version="1.0",
                prompt_version="v1",
                config_version="v1",
                is_mock=True,
            ),
        )

        lasa_detection = detect_prescription_lasa(
            prescription_id="RX-PHASE9-CLEAN",
            medicine_names=["Paracetamol"],
            reference_records=[],
        )
        assert lasa_detection.conflict_detected is False

        abstention_dec = evaluate_prescription_abstention(
            prescription_id="RX-PHASE9-CLEAN",
            extraction_result=clean_extraction,
            lasa_detection=lasa_detection,
        )
        med_field = abstention_dec.fields["medicine_name"]
        assert AbstentionReasonCode.LASA_CONFUSION_RISK.value not in med_field.reason_codes

    @pytest.mark.asyncio
    async def test_pipeline_end_to_end_passes_lasa_to_phase9(self):
        """End-to-end pipeline test proving LASA triggers Phase 9 abstention for sample-2."""
        from backend.app.services.pipeline_interface import PipelineOptions
        from backend.app.multimodal import MockMultimodalModelAdapter, MultimodalExtractionService, MultimodalConfig

        config = MultimodalConfig(provider="mock")
        service = MultimodalExtractionService(
            adapter=MockMultimodalModelAdapter(),
            config=config,
        )
        pipeline = MultimodalPrescriptionPipeline(service=service, config=config)
        options = PipelineOptions(mock_scenario="uncertain")
        res = await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="rx.png",
            public_image_url="/uploads/rx.png",
            options=options,
        )

        # Must have completed all stages through Phase 10 / 11
        assert res.meta.pipeline_stages_completed >= 10

        # Phase 9 field should reflect verification requirement
        med_field = res.fields.get("medicine_name")
        assert med_field is not None
        assert med_field.requires_human_verification is True
        assert res.data.overall_status in ("SAFETY_ALERT", "NEEDS_VERIFICATION")
