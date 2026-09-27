"""
API Integration Tests for Phase 6 Multimodal Endpoints
"""

import io
import pytest
from fastapi.testclient import TestClient


def test_get_multimodal_config(client: TestClient):
    """Verifies GET /api/v1/multimodal/config returns versioned metadata and audit hash."""
    resp = client.get("/api/v1/multimodal/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["config_version"] == "multimodal_extraction_v1"
    assert "prompt_version" in data
    assert "config_hash_sha256" in data
    assert len(data["config_hash_sha256"]) == 64
    assert "is_adapter_available" in data


def test_post_multimodal_extract_success(client: TestClient, sample_prescription_image: bytes):
    """Verifies POST /api/v1/multimodal/extract processes a valid prescription image."""
    files = {"file": ("rx_test.png", io.BytesIO(sample_prescription_image), "image/png")}
    data = {"scenario": "single_medicine_confident"}

    resp = client.post("/api/v1/multimodal/extract", files=files, data=data)
    assert resp.status_code == 200
    res = resp.json()

    assert "prescription_id" in res
    assert "original_image_url" in res
    assert "medicines" in res
    assert len(res["medicines"]) == 1
    assert res["medicines"][0]["medicine_name"]["value"] == "Amoxicillin"
    assert res["requires_human_review"] is False
    assert "model" in res
    assert res["model"]["prompt_version"] == "prompt_v1_clinical_vision_extraction"


def test_post_multimodal_extract_multiple_medicines(client: TestClient, sample_prescription_image: bytes):
    """Verifies extraction of multiple prescribed medicines."""
    files = {"file": ("rx_multi.png", io.BytesIO(sample_prescription_image), "image/png")}
    data = {"scenario": "multiple_medicines"}

    resp = client.post("/api/v1/multimodal/extract", files=files, data=data)
    assert resp.status_code == 200
    res = resp.json()

    assert len(res["medicines"]) == 2
    assert res["medicines"][0]["medicine_name"]["value"] == "Paracetamol"
    assert res["medicines"][1]["medicine_name"]["value"] == "Cetirizine"


def test_post_multimodal_extract_missing_dosage_triggers_review(client: TestClient, sample_prescription_image: bytes):
    """Verifies that missing dosage triggers requires_human_review=True."""
    files = {"file": ("rx_missing.png", io.BytesIO(sample_prescription_image), "image/png")}
    data = {"scenario": "missing_dosage"}

    resp = client.post("/api/v1/multimodal/extract", files=files, data=data)
    assert resp.status_code == 200
    res = resp.json()

    assert res["medicines"][0]["dosage"]["value"] is None
    assert res["medicines"][0]["dosage"]["status"] == "uncertain"
    assert res["requires_human_review"] is True


def test_post_multimodal_extract_model_unavailable(client: TestClient, sample_prescription_image: bytes):
    """Verifies 503 MODEL_UNAVAILABLE error response."""
    files = {"file": ("rx_test.png", io.BytesIO(sample_prescription_image), "image/png")}
    data = {"scenario": "model_unavailable"}

    resp = client.post("/api/v1/multimodal/extract", files=files, data=data)
    assert resp.status_code == 503
    err = resp.json()
    assert err["error"]["code"] == "MODEL_UNAVAILABLE"


def test_post_multimodal_extract_empty_file_rejected(client: TestClient):
    """Verifies 400 rejection on empty file upload."""
    files = {"file": ("empty.png", io.BytesIO(b""), "image/png")}
    resp = client.post("/api/v1/multimodal/extract", files=files)
    assert resp.status_code == 400
