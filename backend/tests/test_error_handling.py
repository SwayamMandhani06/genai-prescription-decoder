"""
Failure-Path and Edge Case Tests
Validates all required error codes and failure contracts from PLAN.md Section 6 & 11:
- INVALID_REQUEST
- INVALID_FILE_TYPE
- FILE_TOO_LARGE
- VALIDATION_FAILED
- PROCESSING_FAILED
- MODEL_UNAVAILABLE
"""

import pytest
from fastapi.testclient import TestClient


def test_missing_input_raises_400(client: TestClient):
    """Calling analyze without 'file' or 'sample_id' must return HTTP 400 with INVALID_REQUEST."""
    response = client.post("/api/v1/prescriptions/analyze")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_REQUEST"
    assert "file" in data["error"]["message"] or "sample_id" in data["error"]["message"]


def test_unsupported_file_type_raises_415(client: TestClient):
    """Uploading an unsupported file (e.g. .pdf, .txt) must return HTTP 415 with INVALID_FILE_TYPE."""
    files = {"file": ("malicious.exe", b"MZ\x90\x00BinaryData", "application/octet-stream")}
    response = client.post("/api/v1/prescriptions/analyze", files=files)
    assert response.status_code == 415
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_FILE_TYPE"
    assert "not supported" in data["error"]["message"]


def test_oversized_file_raises_413(client: TestClient):
    """Uploading a file exceeding 15MB must return HTTP 413 with FILE_TOO_LARGE."""
    oversized_bytes = b"0" * (16 * 1024 * 1024)  # 16 MB
    files = {"file": ("huge_scan.png", oversized_bytes, "image/png")}
    response = client.post("/api/v1/prescriptions/analyze", files=files)
    assert response.status_code == 413
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FILE_TOO_LARGE"
    assert "exceeds maximum allowed threshold" in data["error"]["message"]


def test_image_quality_insufficient_fault_injection(client: TestClient):
    """Injected image_quality_insufficient scenario must return HTTP 422 with IMAGE_QUALITY_INSUFFICIENT."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "image_quality_insufficient"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "IMAGE_QUALITY_INSUFFICIENT"
    assert data["error"]["stage"] == "image_quality_assessment"
    assert data["error"]["retryable"] is True
    assert "minimum_dpi" in data["error"]["details"]
    assert "blur_score" in data["error"]["details"]


def test_validation_error_fault_injection(client: TestClient):
    """Injected validation_error scenario must return HTTP 422 with VALIDATION_FAILED."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "validation_error"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_FAILED"
    assert data["error"]["stage"] == "posology_validation"
    assert data["error"]["retryable"] is True
    assert "field" in data["error"]["details"]


def test_processing_failed_fault_injection(client: TestClient):
    """Injected processing_failed scenario must return HTTP 500 with PROCESSING_FAILED."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "processing_failed"},
    )
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PROCESSING_FAILED"
    assert data["error"]["stage"] == "multimodal_extraction"
    assert data["error"]["retryable"] is True


def test_model_unavailable_fault_injection(client: TestClient):
    """Injected model_unavailable scenario must return HTTP 503 with MODEL_UNAVAILABLE."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "model_unavailable"},
    )
    assert response.status_code == 503
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MODEL_UNAVAILABLE"
    assert data["error"]["stage"] == "inference_dispatch"


def test_no_stack_traces_leaked(client: TestClient):
    """Verifies that internal stack traces or secrets are never exposed in JSON error responses."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1", "mock_scenario": "processing_failed"},
    )
    data = response.json()
    # Check that traceback or python file paths are not exposed in message
    assert "Traceback" not in data["error"]["message"]
    assert ".py" not in data["error"]["message"]
