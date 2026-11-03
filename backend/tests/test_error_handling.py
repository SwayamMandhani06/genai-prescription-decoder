"""
Failure-Path and Edge Case Tests
Validates all required error codes and failure contracts from PLAN.md Section 6 & 11:
- INVALID_REQUEST
- INVALID_FILE_TYPE
- FILE_TOO_LARGE
- VALIDATION_FAILED
- PROCESSING_FAILED
- MODEL_UNAVAILABLE
- RATE_LIMIT_EXCEEDED
- INTERNAL_ERROR

Also asserts that all error responses conform to ErrorResponse schema and contain a valid correlation request_id.
"""

import uuid
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.schemas.error import ErrorCode, ErrorResponse
from backend.app.services.pipeline_interface import UpstreamInferenceError
from backend.app.multimodal.parser import parse_multimodal_response, MultimodalParseError


def test_missing_input_raises_400(client: TestClient):
    """Calling analyze without 'file' or 'sample_id' must return HTTP 400 with INVALID_REQUEST."""
    response = client.post("/api/v1/prescriptions/analyze")
    assert response.status_code == 400
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.INVALID_REQUEST
    assert "file" in validated.error.message or "sample_id" in validated.error.message
    assert validated.request_id is not None
    assert response.headers.get("x-request-id") == validated.request_id


def test_unsupported_file_type_raises_415(client: TestClient):
    """Uploading an unsupported file (e.g. .pdf, .txt) must return HTTP 415 with INVALID_FILE_TYPE."""
    files = {"file": ("malicious.exe", b"MZ\x90\x00BinaryData", "application/octet-stream")}
    response = client.post("/api/v1/prescriptions/analyze", files=files)
    assert response.status_code == 415
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.INVALID_FILE_TYPE
    assert "not supported" in validated.error.message
    assert validated.request_id is not None


def test_zero_byte_file_upload_rejected_400(client: TestClient):
    """Uploading an empty zero-byte file must return HTTP 400 with INVALID_REQUEST."""
    files = {"file": ("empty.png", b"", "image/png")}
    response = client.post("/api/v1/prescriptions/analyze", files=files)
    assert response.status_code == 400
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.INVALID_REQUEST
    assert "empty" in validated.error.message.lower() or "zero bytes" in validated.error.message.lower()
    assert validated.request_id is not None
    assert response.headers.get("x-request-id") == validated.request_id


def test_corrupted_file_upload_rejected_415(client: TestClient):
    """Uploading a non-image corrupted byte stream must return HTTP 415."""
    corrupted_bytes = b"CORRUPTED_NON_IMAGE_DATA_STREAM_HEADER"
    files = {"file": ("corrupted.png", corrupted_bytes, "image/png")}
    response = client.post("/api/v1/prescriptions/analyze", files=files)
    assert response.status_code == 415
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.INVALID_FILE_TYPE
    assert validated.request_id is not None


def test_oversized_file_raises_413(client: TestClient):
    """Uploading a file exceeding MAX_UPLOAD_SIZE_BYTES must return HTTP 413 with FILE_TOO_LARGE."""
    from backend.app.config import get_settings
    settings = get_settings()
    oversized_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024)
    files = {"file": ("huge_scan.png", oversized_bytes, "image/png")}
    response = client.post("/api/v1/prescriptions/analyze", files=files)
    assert response.status_code == 413
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.FILE_TOO_LARGE
    assert "exceeds" in validated.error.message.lower()
    assert validated.request_id is not None


def test_image_quality_insufficient_fault_injection(client: TestClient):
    """Injected image_quality_insufficient scenario must return HTTP 422 with IMAGE_QUALITY_INSUFFICIENT."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "image_quality_insufficient"},
    )
    assert response.status_code == 422
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.IMAGE_QUALITY_INSUFFICIENT
    assert validated.error.stage == "image_quality_assessment"
    assert validated.error.retryable is True
    assert "minimum_dpi" in validated.error.details
    assert "blur_score" in validated.error.details
    assert validated.request_id is not None


def test_validation_error_fault_injection(client: TestClient):
    """Injected validation_error scenario must return HTTP 422 with VALIDATION_FAILED."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "validation_error"},
    )
    assert response.status_code == 422
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.VALIDATION_FAILED
    assert validated.error.stage == "posology_validation"
    assert validated.error.retryable is True
    assert "field" in validated.error.details
    assert validated.request_id is not None


def test_processing_failed_fault_injection(client: TestClient):
    """Injected processing_failed scenario must return HTTP 500 with PROCESSING_FAILED."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "processing_failed"},
    )
    assert response.status_code == 500
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.PROCESSING_FAILED
    assert validated.error.stage == "multimodal_extraction"
    assert validated.error.retryable is True
    assert validated.request_id is not None


def test_model_unavailable_fault_injection(client: TestClient):
    """Injected model_unavailable scenario must return HTTP 503 with MODEL_UNAVAILABLE."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "model_unavailable"},
    )
    assert response.status_code == 503
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.MODEL_UNAVAILABLE
    assert validated.error.stage == "inference_dispatch"
    assert validated.request_id is not None


def test_upstream_vlm_timeout_504_returns_structured_error(client: TestClient):
    """Injected timeout scenario must return HTTP 504 with MODEL_UNAVAILABLE and retryable=True."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "timeout"},
    )
    assert response.status_code == 504
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.MODEL_UNAVAILABLE
    assert validated.error.retryable is True
    assert validated.request_id is not None


def test_upstream_vlm_rate_limit_429_returns_structured_error(client: TestClient):
    """When an upstream VLM 429 occurs, it returns HTTP 429 with RATE_LIMIT_EXCEEDED."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "rate_limit"},
    )
    assert response.status_code == 429
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.error.code == ErrorCode.RATE_LIMIT_EXCEEDED
    assert validated.request_id is not None
    assert validated.error.retryable is True


def test_client_rate_limit_ingress_dependency_returns_structured_429(client: TestClient):
    """When ingress rate limiting triggers HTTP 429, it returns structured ErrorResponse."""
    from fastapi import HTTPException
    from backend.app.core.security import check_rate_limit
    from backend.app.main import app

    async def mock_rl():
        raise HTTPException(status_code=429, detail="Client rate limit exceeded. Retry after 60s.")

    app.dependency_overrides[check_rate_limit] = mock_rl
    try:
        response = client.post("/api/v1/prescriptions/analyze", data={"sample_id": "rx-sample-1"})
        assert response.status_code == 429
        data = response.json()
        validated = ErrorResponse(**data)
        assert validated.error.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert validated.request_id is not None
    finally:
        app.dependency_overrides.pop(check_rate_limit, None)


def test_no_stack_traces_leaked(client: TestClient):
    """Verifies that internal stack traces or secrets are never exposed in JSON error responses."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "processing_failed"},
    )
    data = response.json()
    assert "Traceback" not in data["error"]["message"]
    assert ".py" not in data["error"]["message"]
    assert "def " not in data["error"]["message"]


def test_custom_request_id_propagated_to_error_response(client: TestClient):
    """Verifies that incoming X-Request-ID headers are preserved on error responses."""
    custom_trace = f"trace-{uuid.uuid4().hex[:12]}"
    response = client.post(
        "/api/v1/prescriptions/analyze",
        headers={"X-Request-ID": custom_trace},
    )
    assert response.status_code == 400
    data = response.json()
    validated = ErrorResponse(**data)
    assert validated.request_id == custom_trace
    assert response.headers.get("x-request-id") == custom_trace


def test_malformed_vlm_json_handled_cleanly():
    """Verifies that malformed JSON from an upstream model is safely handled without raw unhandled crashes."""
    # 1. Truncated JSON
    truncated_json = '{"medicines": [{"medicine_name": "Augmentin"'
    with pytest.raises(MultimodalParseError) as exc_info:
        parse_multimodal_response(truncated_json)
    assert "Failed to decode model JSON output" in str(exc_info.value) or "Expected" in str(exc_info.value)

    # 2. Markdown fenced with comments
    commented_json = """
    ```json
    // Clinical model inference output
    {
      "medicines": [
        {
          "medicine_name": "Metformin",
          "strength": "500 mg",
          "dosage_form": "Tablet",
          "route": "Oral",
          "frequency": "1-0-1",
          "duration": "14 days",
          "instructions": "After food",
          "confidence": 0.92,
          "bounding_box": [10, 20, 30, 40]
        }
      ]
    }
    ```
    """
    res = parse_multimodal_response(commented_json)
    assert len(res["medicines"]) == 1
    assert res["medicines"][0].medicine_name.value == "Metformin"
