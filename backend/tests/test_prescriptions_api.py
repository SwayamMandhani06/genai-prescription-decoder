"""
API Integration Tests for Prescription Analysis and Retrieval Endpoints
"""

import io
import pytest
from fastapi.testclient import TestClient


def test_analyze_with_file_upload(client: TestClient, sample_prescription_image: bytes):
    """Verifies that uploading a valid image file processes successfully and saves the original image."""
    files = {"file": ("rx_test_script.png", sample_prescription_image, "image/png")}
    response = client.post("/api/v1/prescriptions/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    # Section 6 contract assertions
    assert "prescription_id" in data
    assert "original_image_url" in data
    assert data["original_image_url"].startswith("/uploads/rx_")
    assert "fields" in data
    assert "medicine_name" in data["fields"]
    assert data["fields"]["medicine_name"]["status"] == "confident"
    assert "lasa_flags" in data
    assert "validation" in data
    assert "explanation" in data
    assert "requires_human_review" in data

    # Verify that the saved original image is statically retrievable via HTTP
    img_resp = client.get(data["original_image_url"])
    assert img_resp.status_code == 200
    assert len(img_resp.content) == len(sample_prescription_image)


def test_analyze_with_sample_id_1(client: TestClient):
    """Verifies analyze endpoint using curated demo sample 1 (Confident)."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fields"]["medicine_name"]["value"] == "Augmentin 625 Duo"
    assert data["fields"]["medicine_name"]["status"] == "confident"
    assert data["requires_human_review"] is False


def test_analyze_with_sample_id_2_lasa(client: TestClient):
    """Verifies analyze endpoint using curated demo sample 2 (LASA collision)."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-2"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["lasa_flags"]) > 0
    assert data["lasa_flags"][0]["conflict_with"] == "Metronidazole"
    assert data["data"]["overall_status"] == "SAFETY_ALERT"
    assert data["requires_human_review"] is True


def test_analyze_with_sample_id_3_abstained(client: TestClient):
    """Verifies analyze endpoint using curated demo sample 3 (Severe Ambiguity / Abstained)."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        data={"sample_id": "rx-sample-3"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["overall_status"] == "ABSTAINED"
    assert data["requires_human_review"] is True


def test_get_prescription_by_id(client: TestClient):
    """Verifies retrieving prescription findings by accession ID."""
    response = client.get("/api/v1/prescriptions/DEMO-RX-01")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["accession_id"] == "DEMO-RX-01"


def test_get_prescription_not_found(client: TestClient):
    """Verifies 404 response for non-existent prescription accession ID."""
    response = client.get("/api/v1/prescriptions/NON-EXISTENT-999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_REQUEST"
