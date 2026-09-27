"""
Unit Tests for MockPrescriptionPipeline Service
Verifies deterministic mock outputs and failure path handling.
"""

import pytest
from backend.app.services.mock_pipeline import MockPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions, PipelineProcessingError
from backend.app.schemas.error import ErrorCode


@pytest.mark.asyncio
async def test_mock_pipeline_confident_default():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions()
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx_sample.png",
        public_image_url="/uploads/rx_sample.png",
        options=options,
    )
    assert res.status == "success"
    assert res.original_image_url == "/uploads/rx_sample.png"
    assert res.fields["medicine_name"].value == "Augmentin 625 Duo"
    assert res.fields["medicine_name"].status == "confident"
    assert res.requires_human_review is False


@pytest.mark.asyncio
async def test_mock_pipeline_uncertain():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions(mock_scenario="uncertain")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx_sample.png",
        public_image_url="/uploads/rx_sample.png",
        options=options,
    )
    assert res.data.overall_status == "NEEDS_VERIFICATION"
    assert res.fields["frequency"].status == "uncertain"
    assert res.requires_human_review is True


@pytest.mark.asyncio
async def test_mock_pipeline_lasa():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions(mock_scenario="lasa_warning")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx_sample.png",
        public_image_url="/uploads/rx_sample.png",
        options=options,
    )
    assert res.data.overall_status == "SAFETY_ALERT"
    assert len(res.lasa_flags) > 0
    assert res.lasa_flags[0].conflict_with == "Metronidazole"
    assert res.requires_human_review is True


@pytest.mark.asyncio
async def test_mock_pipeline_abstained():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions(mock_scenario="abstained")
    res = await pipeline.process_prescription(
        image_bytes=b"dummy",
        filename="rx_sample.png",
        public_image_url="/uploads/rx_sample.png",
        options=options,
    )
    assert res.data.overall_status == "ABSTAINED"
    assert res.data.document_confidence < 0.4
    assert res.requires_human_review is True


@pytest.mark.asyncio
async def test_mock_pipeline_image_quality_insufficient_fault():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions(mock_scenario="image_quality_insufficient")
    with pytest.raises(PipelineProcessingError) as exc_info:
        await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="rx_sample.png",
            public_image_url="/uploads/rx_sample.png",
            options=options,
        )
    err = exc_info.value
    assert err.code == ErrorCode.IMAGE_QUALITY_INSUFFICIENT
    assert err.status_code == 422
    assert err.stage == "image_quality_assessment"
    assert err.original_image_url == "/uploads/rx_sample.png"
    assert "minimum_dpi" in err.details


@pytest.mark.asyncio
async def test_mock_pipeline_validation_error_fault():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions(mock_scenario="validation_error")
    with pytest.raises(PipelineProcessingError) as exc_info:
        await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="rx_sample.png",
            public_image_url="/uploads/rx_sample.png",
            options=options,
        )
    err = exc_info.value
    assert err.code == ErrorCode.VALIDATION_FAILED
    assert err.status_code == 422
    assert err.stage == "posology_validation"
    assert err.original_image_url == "/uploads/rx_sample.png"


@pytest.mark.asyncio
async def test_mock_pipeline_server_error_fault():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions(mock_scenario="server_error")
    with pytest.raises(PipelineProcessingError) as exc_info:
        await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="rx_sample.png",
            public_image_url="/uploads/rx_sample.png",
            options=options,
        )
    err = exc_info.value
    assert err.code == ErrorCode.PROCESSING_FAILED
    assert err.status_code == 500


@pytest.mark.asyncio
async def test_mock_pipeline_model_unavailable_fault():
    pipeline = MockPrescriptionPipeline()
    options = PipelineOptions(mock_scenario="model_unavailable")
    with pytest.raises(PipelineProcessingError) as exc_info:
        await pipeline.process_prescription(
            image_bytes=b"dummy",
            filename="rx_sample.png",
            public_image_url="/uploads/rx_sample.png",
            options=options,
        )
    err = exc_info.value
    assert err.code == ErrorCode.MODEL_UNAVAILABLE
    assert err.status_code == 503
