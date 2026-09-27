"""
Unit Tests for Phase 6 Multimodal Model Adapters
Tests both GeminiMultimodalAdapter and MockMultimodalModelAdapter across all 14 required evaluation scenarios.
"""

import json
import pytest
from backend.app.multimodal.adapter import (
    GeminiMultimodalAdapter,
    MockMultimodalModelAdapter,
)
from backend.app.multimodal.config import MultimodalConfig
from backend.app.schemas.error import ErrorCode
from backend.app.services.pipeline_interface import PipelineProcessingError


@pytest.mark.asyncio
async def test_gemini_adapter_availability_and_missing_key(monkeypatch):
    """Verifies that GeminiMultimodalAdapter safely reports availability and raises MODEL_UNAVAILABLE if key is absent."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    adapter = GeminiMultimodalAdapter()
    assert adapter.is_available() is False

    with pytest.raises(PipelineProcessingError) as exc_info:
        await adapter.extract(image_bytes=b"dummy_bytes_here")

    assert exc_info.value.code == ErrorCode.MODEL_UNAVAILABLE
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_gemini_adapter_empty_image_rejected(monkeypatch):
    """Verifies that an empty image stream is rejected."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key_for_test")
    adapter = GeminiMultimodalAdapter()
    assert adapter.is_available() is True

    with pytest.raises(PipelineProcessingError) as exc_info:
        await adapter.extract(image_bytes=b"")

    assert exc_info.value.code == ErrorCode.PROCESSING_FAILED
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_mock_adapter_all_14_scenarios():
    """
    Rigorously verifies all 14 required Phase 6 evaluation scenarios defined in Section 17.
    """
    adapter = MockMultimodalModelAdapter()
    dummy_bytes = b"MOCK_PRESCRIPTION_IMAGE_BYTES"

    # Case 1: Single medicine — all fields confident
    res1 = await adapter.extract(dummy_bytes, scenario="single_medicine_confident")
    data1 = json.loads(res1)
    assert len(data1["medicines"]) == 1
    assert data1["medicines"][0]["medicine_name"]["value"] == "Amoxicillin"
    assert data1["medicines"][0]["status"] == "confident"
    assert data1["requires_human_review"] is False

    # Case 2: Multiple medicines
    res2 = await adapter.extract(dummy_bytes, scenario="multiple_medicines")
    data2 = json.loads(res2)
    assert len(data2["medicines"]) == 2
    assert data2["medicines"][0]["medicine_name"]["value"] == "Paracetamol"
    assert data2["medicines"][1]["medicine_name"]["value"] == "Cetirizine"

    # Case 3: Missing dosage
    res3 = await adapter.extract(dummy_bytes, scenario="missing_dosage")
    data3 = json.loads(res3)
    assert data3["medicines"][0]["dosage"]["value"] is None
    assert data3["medicines"][0]["dosage"]["status"] == "uncertain"
    assert data3["requires_human_review"] is True

    # Case 4: Uncertain medicine name
    res4 = await adapter.extract(dummy_bytes, scenario="uncertain_medicine_name")
    data4 = json.loads(res4)
    assert data4["medicines"][0]["medicine_name"]["status"] == "uncertain"
    assert "Ampicillin" in data4["medicines"][0]["medicine_name"]["candidates"]

    # Case 5: Uncertain dosage
    res5 = await adapter.extract(dummy_bytes, scenario="uncertain_dosage")
    data5 = json.loads(res5)
    assert data5["medicines"][0]["dosage"]["status"] == "uncertain"
    assert "850 mg" in data5["medicines"][0]["dosage"]["candidates"]

    # Case 6: Uncertain frequency
    res6 = await adapter.extract(dummy_bytes, scenario="uncertain_frequency")
    data6 = json.loads(res6)
    assert data6["medicines"][0]["frequency"]["status"] == "uncertain"

    # Case 7: Uncertain duration
    res7 = await adapter.extract(dummy_bytes, scenario="uncertain_duration")
    data7 = json.loads(res7)
    assert data7["medicines"][0]["duration"]["status"] == "uncertain"

    # Case 8: Abbreviations present
    res8 = await adapter.extract(dummy_bytes, scenario="abbreviations_present")
    data8 = json.loads(res8)
    assert "BD" in data8["medicines"][0]["abbreviations"]
    assert "AC" in data8["medicines"][0]["abbreviations"]

    # Case 9: Multiple uncertain fields
    res9 = await adapter.extract(dummy_bytes, scenario="multiple_uncertain_fields")
    data9 = json.loads(res9)
    assert data9["medicines"][0]["medicine_name"]["status"] == "uncertain"
    assert data9["medicines"][0]["dosage"]["status"] == "uncertain"
    assert data9["medicines"][0]["frequency"]["status"] == "uncertain"

    # Case 10: Human review required
    res10 = await adapter.extract(dummy_bytes, scenario="human_review_required")
    data10 = json.loads(res10)
    assert data10["requires_human_review"] is True
    assert data10["medicines"][0]["dosage"]["status"] == "flagged"

    # Case 11: Model unavailable
    with pytest.raises(PipelineProcessingError) as exc_info11:
        await adapter.extract(dummy_bytes, scenario="model_unavailable")
    assert exc_info11.value.code == ErrorCode.MODEL_UNAVAILABLE
    assert exc_info11.value.status_code == 503

    # Case 12: Processing failure (corrupt stream)
    res12 = await adapter.extract(dummy_bytes, scenario="processing_failure")
    assert "<<CORRUPTED" in res12

    # Case 13: Invalid image
    with pytest.raises(PipelineProcessingError) as exc_info13:
        await adapter.extract(dummy_bytes, scenario="invalid_image")
    assert exc_info13.value.code == ErrorCode.PROCESSING_FAILED

    # Case 14: Empty extraction result
    res14 = await adapter.extract(dummy_bytes, scenario="empty_extraction")
    data14 = json.loads(res14)
    assert len(data14["medicines"]) == 0
    assert data14["requires_human_review"] is True
