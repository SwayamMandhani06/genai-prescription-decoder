"""
Integration tests for Phase 6 Multimodal Extraction -> Phase 7 RAG Medicine Validation.
Verifies seamless end-to-end integration:
Prescription Image -> Preprocessing (Phase 4) -> Extraction (Phase 6) -> Validation (Phase 7)
"""

import pytest
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions
from backend.app.multimodal import MultimodalConfig, MockMultimodalModelAdapter, MultimodalExtractionService


class TestRAGPipelineIntegration:
    @pytest.mark.asyncio
    async def test_multimodal_pipeline_populates_phase_7_validation(self, sample_prescription_image: bytes):
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

        # 1. Pipeline stages completed must be 7
        assert response.meta.pipeline_stages_completed == 7

        # 2. Section 6 Top-Level Validation dictionary must be populated
        assert len(response.validation) >= 1
        med_val = response.validation.get("medicine_name") or response.validation.get("medicine_1")
        assert med_val is not None
        assert "CDSCO" in med_val.source or "RxNorm" in med_val.source
        assert med_val.matched_entity_name is not None
        assert "Amoxicillin" in med_val.matched_entity_name

        # 3. Data Envelope Validation Evidence must be populated with authoritative references
        val_evidence = response.data.validation_evidence
        assert val_evidence.candidate_name == "Amoxicillin"
        assert "Amoxicillin" in val_evidence.matched_entity_name
        assert val_evidence.cdsco_schedule is not None
        assert val_evidence.rxnorm_cui is not None
        assert len(val_evidence.alternatives) >= 1

        # 4. Phase 7 Detailed Auditable Validations array must be present
        assert response.medicine_validations is not None
        assert isinstance(response.medicine_validations, list)
        assert len(response.medicine_validations) >= 1
        mv = response.medicine_validations[0]
        assert mv["input_candidate"] == "Amoxicillin"
        assert len(mv["matched_candidates"]) >= 2
        assert mv["provenance"]["config_hash"] is not None

    @pytest.mark.asyncio
    async def test_multimodal_pipeline_uncertain_scenario_preserves_uncertainty(self, sample_prescription_image: bytes):
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

        # In uncertain scenario, human review must be required
        assert response.requires_human_review is True
        assert response.data.overall_status == "NEEDS_VERIFICATION"
        assert response.medicine_validations is not None
        assert len(response.medicine_validations) >= 1
