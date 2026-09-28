"""
Integration tests for Phase 9 Abstention Layer within the full AURA-Rx pipeline.
Verifies end-to-end execution:
Preprocessing (Phase 4) -> Extraction (Phase 6) -> RAG Validation (Phase 7) ->
Confidence Calibration (Phase 8) -> Abstention & Verification (Phase 9).
"""

import pytest
from backend.app.services.mock_pipeline import MockPrescriptionPipeline
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions
from backend.app.multimodal import MultimodalConfig, MockMultimodalModelAdapter, MultimodalExtractionService
from backend.app.schemas.prescription import PrescriptionAnalyzeResponse


class TestAbstentionPipelineIntegration:
    @pytest.mark.asyncio
    async def test_mock_pipeline_executes_stage_9(self):
        pipeline = MockPrescriptionPipeline()
        options = PipelineOptions(sample_id="sample-1")
        response = await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="sample-1.png",
            public_image_url="/uploads/sample-1.png",
            options=options,
        )
        assert isinstance(response, PrescriptionAnalyzeResponse)

        # 1. Pipeline stages completed is 9
        assert response.meta.pipeline_stages_completed == 9

        # 2. Abstention block is attached
        assert response.abstention is not None
        assert "prescription_decision" in response.abstention
        assert "policy_version" in response.abstention
        assert response.abstention["policy_version"] == "abstention_policy_v1"

        # 3. Section 6 fields enriched with Phase 9 decision metadata
        for f_key, f_item in response.fields.items():
            assert f_item.abstention_decision in ("accepted", "abstained")
            assert f_item.requires_human_verification is not None

    @pytest.mark.asyncio
    async def test_sample_2_lasa_flagged_triggers_human_verification(self):
        pipeline = MockPrescriptionPipeline()
        options = PipelineOptions(sample_id="sample-2", mock_scenario="lasa_warning")
        response = await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="sample-2.png",
            public_image_url="/uploads/sample-2.png",
            options=options,
        )
        assert response.meta.pipeline_stages_completed == 9
        assert response.abstention is not None
        assert response.abstention["requires_human_verification"] is True
        assert response.abstention["prescription_decision"] == "REQUIRES_HUMAN_VERIFICATION"

    @pytest.mark.asyncio
    async def test_sample_3_abstained_triggers_full_verification(self):
        pipeline = MockPrescriptionPipeline()
        options = PipelineOptions(sample_id="sample-3", mock_scenario="abstained")
        response = await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="sample-3.png",
            public_image_url="/uploads/sample-3.png",
            options=options,
        )
        assert response.meta.pipeline_stages_completed == 9
        assert response.abstention is not None
        assert response.abstention["requires_human_verification"] is True
        assert response.abstention["prescription_decision"] == "REQUIRES_HUMAN_VERIFICATION"

    @pytest.mark.asyncio
    async def test_multimodal_pipeline_populates_abstention_layer(self, sample_prescription_image: bytes):
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

        assert response.meta.pipeline_stages_completed == 10
        assert response.abstention is not None
        assert "policy_version" in response.abstention
        assert response.abstention["policy_version"] == "abstention_policy_v1"
        assert "prescription_decision" in response.abstention

        # Dosage remains immutable throughout pipeline
        dosage_field = response.fields.get("dosage")
        if dosage_field:
            assert dosage_field.value is not None
