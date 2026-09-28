"""
Phase 10 Tests: LASA Pipeline Integration.
Verifies that LASA detection is properly integrated into the MultimodalPrescriptionPipeline
as Stage 10, and that LASA flags, screening, and detection results propagate correctly
to the PrescriptionAnalyzeResponse.
"""

import pytest
from backend.app.services.pipeline_interface import PipelineOptions
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.multimodal import MockMultimodalModelAdapter, MultimodalExtractionService, MultimodalConfig


@pytest.fixture
def pipeline():
    """Creates a multimodal pipeline with mock adapter."""
    config = MultimodalConfig(provider="mock")
    service = MultimodalExtractionService(
        adapter=MockMultimodalModelAdapter(),
        config=config,
    )
    return MultimodalPrescriptionPipeline(service=service, config=config)


@pytest.mark.asyncio
async def test_pipeline_includes_lasa_detection(pipeline):
    """Verify lasa_detection field is present in response."""
    options = PipelineOptions(mock_scenario="confident")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx.png",
        public_image_url="/uploads/rx.png",
        options=options,
    )
    assert res.lasa_detection is not None
    assert "prescription_id" in res.lasa_detection
    assert "has_any_lasa_conflict" in res.lasa_detection
    assert "provenance" in res.lasa_detection
    assert "medicines" in res.lasa_detection


@pytest.mark.asyncio
async def test_pipeline_stage_count_is_10(pipeline):
    """Pipeline stages completed should be 10 with LASA detection."""
    options = PipelineOptions(mock_scenario="confident")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx.png",
        public_image_url="/uploads/rx.png",
        options=options,
    )
    assert res.meta.pipeline_stages_completed == 10


@pytest.mark.asyncio
async def test_pipeline_lasa_flags_populated(pipeline):
    """Verify lasa_flags list is present (may be empty for non-confusable meds)."""
    options = PipelineOptions(mock_scenario="confident")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx.png",
        public_image_url="/uploads/rx.png",
        options=options,
    )
    assert isinstance(res.lasa_flags, list)


@pytest.mark.asyncio
async def test_pipeline_lasa_screening_populated(pipeline):
    """Verify lasa_screening is populated in data envelope."""
    options = PipelineOptions(mock_scenario="confident")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx.png",
        public_image_url="/uploads/rx.png",
        options=options,
    )
    assert res.data.lasa_screening is not None
    assert hasattr(res.data.lasa_screening, "has_warning")
    assert hasattr(res.data.lasa_screening, "prescribed_candidate")
    assert hasattr(res.data.lasa_screening, "similarity_score")


@pytest.mark.asyncio
async def test_pipeline_lasa_provenance_has_config_hash(pipeline):
    """Verify provenance includes SHA-256 config hash."""
    options = PipelineOptions(mock_scenario="confident")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx.png",
        public_image_url="/uploads/rx.png",
        options=options,
    )
    prov = res.lasa_detection["provenance"]
    assert len(prov["config_hash"]) == 64
    assert prov["policy_version"] == "lasa_policy_v1"


@pytest.mark.asyncio
async def test_pipeline_uncertain_scenario_has_lasa(pipeline):
    """Verify LASA detection runs even for uncertain scenarios."""
    options = PipelineOptions(mock_scenario="uncertain")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx.png",
        public_image_url="/uploads/rx.png",
        options=options,
    )
    assert res.lasa_detection is not None
    assert res.meta.pipeline_stages_completed == 10


@pytest.mark.asyncio
async def test_pipeline_abstained_scenario_has_lasa(pipeline):
    """Verify LASA detection runs for abstained scenarios."""
    options = PipelineOptions(mock_scenario="abstained")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx.png",
        public_image_url="/uploads/rx.png",
        options=options,
    )
    assert res.lasa_detection is not None
