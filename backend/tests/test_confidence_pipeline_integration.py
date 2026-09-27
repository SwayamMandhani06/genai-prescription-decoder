"""
Integration tests for Phase 6 Multimodal Extraction -> Phase 7 RAG Validation -> Phase 8 Confidence Calibration.
Verifies end-to-end execution:
Prescription Image -> Preprocessing (Phase 4) -> Extraction (Phase 6) -> Validation (Phase 7) -> Confidence (Phase 8)
"""

import pytest
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions
from backend.app.multimodal import MultimodalConfig, MockMultimodalModelAdapter, MultimodalExtractionService


class TestConfidencePipelineIntegration:
    @pytest.mark.asyncio
    async def test_multimodal_pipeline_populates_phase_8_confidence(self, sample_prescription_image: bytes):
        mock_config = MultimodalConfig(provider="mock", configuration_status="mock")
        mock_service = MultimodalExtractionService(
            adapter=MockMultimodalModelAdapter(),
            config=mock_config,
        )
        pipeline = MultimodalPrescriptionPipeline(service=mock_service, config=mock_config)
        options = PipelineOptions(mock_scenario="confident")

        response = await pipeline.process_prescription(
            image_bytes=sample_prescription_image,
            filename="prescription_sample.png",
            public_image_url="/uploads/prescriptions/test.png",
            options=options,
        )

        # 1. Pipeline stages completed must be at least 8 (now 9 with Phase 9)
        assert response.meta.pipeline_stages_completed >= 8

        # 2. Phase 8 confidence assessment dictionary must be populated
        assert response.confidence_assessment is not None
        assert isinstance(response.confidence_assessment, dict)
        assert "calibration_status" in response.confidence_assessment
        assert "overall_raw_score" in response.confidence_assessment
        assert len(response.confidence_assessment["medicines"]) >= 1

        # 3. Section 6 fields enriched with Phase 8 calibration fields
        assert len(response.fields) >= 1
        med_field = response.fields.get("medicine_name") or response.fields.get("medicine_1")
        assert med_field is not None
        assert med_field.raw_confidence is not None
        assert med_field.calibration_status in ("calibrated", "insufficient_data", "uncalibrated")

        # 4. Phase 7 Validation remains intact
        assert response.medicine_validations is not None
        assert len(response.medicine_validations) >= 1

        # 5. Dosage observation remains immutable
        dosage_field = response.fields.get("dosage")
        if dosage_field:
            assert dosage_field.value is not None

    @pytest.mark.asyncio
    async def test_multimodal_pipeline_uncertain_preserves_confidence_uncertainty(self, sample_prescription_image: bytes):
        mock_config = MultimodalConfig(provider="mock", configuration_status="mock")
        mock_service = MultimodalExtractionService(
            adapter=MockMultimodalModelAdapter(),
            config=mock_config,
        )
        pipeline = MultimodalPrescriptionPipeline(service=mock_service, config=mock_config)
        options = PipelineOptions(mock_scenario="uncertain")

        response = await pipeline.process_prescription(
            image_bytes=sample_prescription_image,
            filename="prescription_sample.png",
            public_image_url="/uploads/prescriptions/test.png",
            options=options,
        )

        assert response.meta.pipeline_stages_completed >= 8
        assert response.requires_human_review is True
        assert response.confidence_assessment is not None
        med_conf = response.confidence_assessment["medicines"][0]
        # In uncertain scenario, conflict flags or lower confidence is recorded
        assert med_conf["overall_raw_confidence"] < 0.85
