"""
Phase 11 Integration Tests: Pipeline Integration.
Verifies that MultimodalPrescriptionPipeline invokes ExplanationService,
populates top-level explanation, data.posology_explanation, and
multilingual_explanation, and records pipeline_stages_completed == 11.
"""

import pytest
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions
from backend.app.multimodal import MockMultimodalModelAdapter, MultimodalExtractionService, MultimodalConfig


@pytest.mark.asyncio
async def test_multimodal_pipeline_populates_phase11_explanations():
    config = MultimodalConfig(provider="mock")
    service = MultimodalExtractionService(
        adapter=MockMultimodalModelAdapter(),
        config=config,
    )
    pipeline = MultimodalPrescriptionPipeline(service=service, config=config)
    response = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx_sample.png",
        public_image_url="http://localhost:8000/uploads/rx_sample.png",
        options=PipelineOptions(mock_scenario="confident"),
    )

    # 1. Pipeline stages completed must be 11
    assert response.meta.pipeline_stages_completed == 11

    # 2. Section 6 MultilingualSummary contract populated
    assert response.explanation is not None
    assert response.explanation.en is not None
    assert response.explanation.hi is not None
    assert response.explanation.mr is not None

    # 3. Phase 1 UI Envelope MultilingualPosology populated
    posology = response.data.posology_explanation
    assert posology is not None
    assert posology.en.summary is not None
    assert posology.hi.summary is not None
    assert posology.mr.summary is not None
    assert len(posology.en.precautions) > 0
    assert len(posology.hi.precautions) > 0
    assert len(posology.mr.precautions) > 0

    # 4. Phase 11 MultilingualPrescriptionExplanation audit model populated
    assert response.multilingual_explanation is not None
    multi_exp = response.multilingual_explanation
    assert multi_exp["policy_version"] == "explanation_policy_v1"
    assert multi_exp["template_version"] == "explanation_template_v1"
    assert "explanations" in multi_exp
    assert "en" in multi_exp["explanations"]
    assert "hi" in multi_exp["explanations"]
    assert "mr" in multi_exp["explanations"]

    # Invariant: Medicine name is in Roman script across all 3 languages
    en_sum = multi_exp["explanations"]["en"]["summary"]
    hi_sum = multi_exp["explanations"]["hi"]["summary"]
    mr_sum = multi_exp["explanations"]["mr"]["summary"]
    assert len(en_sum) > 0
    assert len(hi_sum) > 0
    assert len(mr_sum) > 0
