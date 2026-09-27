"""
Integration Tests for Phase 6 Multimodal Extraction Service & Pipeline
"""

import hashlib
import pytest
from backend.app.multimodal.service import MultimodalExtractionService
from backend.app.multimodal.adapter import MockMultimodalModelAdapter
from backend.app.multimodal.config import MultimodalConfig
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions, PipelineProcessingError
from backend.app.schemas.error import ErrorCode


@pytest.mark.asyncio
async def test_multimodal_extraction_service_end_to_end(sample_prescription_image):
    """Verifies complete MultimodalExtractionService execution, hashing, and traceability."""
    service = MultimodalExtractionService(
        adapter=MockMultimodalModelAdapter(),
        config=MultimodalConfig(provider="mock"),
    )

    res = await service.extract_prescription(
        image_bytes=sample_prescription_image,
        prescription_id="RX-TEST-1234",
        original_image_url="/uploads/prescriptions/RX-TEST-1234.png",
        scenario="single_medicine_confident",
    )

    assert res.prescription_id == "RX-TEST-1234"
    assert res.original_image_url == "/uploads/prescriptions/RX-TEST-1234.png"
    assert res.source_image_sha256 == hashlib.sha256(sample_prescription_image).hexdigest()
    assert res.duration_seconds >= 0.0
    assert res.model.provider == "mock"
    assert res.model.is_mock is True
    assert len(res.medicines) == 1
    assert res.medicines[0].medicine_name.value == "Amoxicillin"
    assert res.fields["medicine_name"].value == "Amoxicillin"
    assert res.requires_human_review is False
    assert res.raw_model_response is not None


@pytest.mark.asyncio
async def test_multimodal_extraction_service_corrupt_response_handling(sample_prescription_image):
    """Verifies that unparsable model responses raise PipelineProcessingError."""
    service = MultimodalExtractionService(
        adapter=MockMultimodalModelAdapter(),
        config=MultimodalConfig(provider="mock"),
    )

    with pytest.raises(PipelineProcessingError) as exc_info:
        await service.extract_prescription(
            image_bytes=sample_prescription_image,
            prescription_id="RX-CORRUPT-01",
            original_image_url="/test.png",
            scenario="processing_failure",
        )

    assert exc_info.value.code == ErrorCode.PROCESSING_FAILED
    assert exc_info.value.stage == "multimodal_response_parsing"


@pytest.mark.asyncio
async def test_multimodal_prescription_pipeline_integration(sample_prescription_image):
    """Verifies MultimodalPrescriptionPipeline end-to-end integration with Phase 4 preprocessing."""
    from backend.app.multimodal import MultimodalConfig, MockMultimodalModelAdapter, MultimodalExtractionService
    mock_config = MultimodalConfig(provider="mock", configuration_status="mock")
    mock_service = MultimodalExtractionService(
        adapter=MockMultimodalModelAdapter(),
        config=mock_config,
    )
    pipeline = MultimodalPrescriptionPipeline(service=mock_service, config=mock_config)

    options = PipelineOptions(mock_scenario="multiple_medicines")
    response = await pipeline.process_prescription(
        image_bytes=sample_prescription_image,
        filename="rx_sample.png",
        public_image_url="/uploads/prescriptions/test.png",
        options=options,
    )

    # Contract assertions
    assert response.prescription_id.startswith("RX-")
    assert response.original_image_url == "/uploads/prescriptions/test.png"
    assert response.processed_image_url is not None
    assert response.quality_report is not None
    assert response.preprocessing_manifest is not None

    # Phase 6 Extensions
    assert response.medicines is not None
    assert len(response.medicines) == 2
    assert response.multimodal_result is not None

    # UI presentation model assertions
    assert len(response.data.extracted_entities) > 0
    assert response.data.extracted_entities[0].bounding_box is not None
