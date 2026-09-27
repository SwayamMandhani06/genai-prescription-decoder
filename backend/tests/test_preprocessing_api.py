"""
Phase 4 API Tests: Preprocessing & Quality Endpoints Integration
Tests that POST /analyze generates preprocessed derivative artifacts, populates quality metadata,
allows static HTTP retrieval of preprocessed images, exposes GET /{id}/artifacts,
and enforces HTTP 422 IMAGE_QUALITY_INSUFFICIENT on fatal quality failures.
"""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageFilter


class TestPreprocessingApi:

    def test_analyze_with_file_upload_returns_preprocessed_urls_and_quality(
        self, client: TestClient, sample_prescription_image: bytes
    ):
        """Verifies that uploading a valid image generates preprocessed derivatives and quality telemetry."""
        files = {"file": ("clinical_rx_pad.png", sample_prescription_image, "image/png")}
        response = client.post("/api/v1/prescriptions/analyze", files=files)
        assert response.status_code == 200
        data = response.json()

        # Both original and preprocessed images must be present
        assert "original_image_url" in data
        assert "processed_image_url" in data
        assert data["original_image_url"].startswith("/uploads/rx_")
        assert data["processed_image_url"].startswith("/uploads/preprocessed/")

        # Quality report and manifest must be attached
        assert "quality_report" in data
        assert data["quality_report"] is not None
        assert "overall_status" in data["quality_report"]
        assert "heuristic_quality_score" in data["quality_report"]
        assert "preprocessing_manifest" in data

        # Telemetry should be populated with computed optical values
        telemetry = data["document_telemetry"]
        assert telemetry["estimated_dpi"] >= 72
        assert telemetry["contrast_ratio"] > 0.0

        # Verify static retrieval of both original and preprocessed images
        r_orig = client.get(data["original_image_url"])
        assert r_orig.status_code == 200
        assert len(r_orig.content) == len(sample_prescription_image)

        r_proc = client.get(data["processed_image_url"])
        assert r_proc.status_code == 200
        assert len(r_proc.content) > 0

    def test_artifacts_inspection_endpoint(
        self, client: TestClient, sample_prescription_image: bytes
    ):
        """Verifies GET /api/v1/prescriptions/{id}/artifacts retrieves all generated derived representations."""
        # 1. Upload prescription to generate run
        files = {"file": ("rx_to_inspect.png", sample_prescription_image, "image/png")}
        post_resp = client.post("/api/v1/prescriptions/analyze", files=files)
        assert post_resp.status_code == 200
        rx_id = post_resp.json()["prescription_id"]

        # 2. Query artifacts inspection endpoint
        art_resp = client.get(f"/api/v1/prescriptions/{rx_id}/artifacts")
        assert art_resp.status_code == 200
        art_data = art_resp.json()

        assert art_data["prescription_id"] == rx_id
        assert "artifacts" in art_data
        artifacts_dict = art_data["artifacts"]

        assert "grayscale" in artifacts_dict
        assert "normalized" in artifacts_dict
        assert "denoised" in artifacts_dict
        assert "enhanced" in artifacts_dict

        # Verify that all artifact URLs return HTTP 200
        for art_name, art_url in artifacts_dict.items():
            r = client.get(art_url)
            assert r.status_code == 200, f"Artifact {art_name} at {art_url} failed to load!"

    def test_artifacts_endpoint_not_found(self, client: TestClient):
        """Verifies GET /artifacts returns 404 for unknown accession ID."""
        r = client.get("/api/v1/prescriptions/NON-EXISTENT-ID/artifacts")
        assert r.status_code == 404

    def test_upload_tiny_image_returns_422_image_quality_insufficient(
        self, client: TestClient, tiny_prescription_image: bytes
    ):
        """Verifies that an image smaller than minimum dimensional threshold returns HTTP 422."""
        files = {"file": ("tiny_rx.png", tiny_prescription_image, "image/png")}
        response = client.post("/api/v1/prescriptions/analyze", files=files)
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "IMAGE_QUALITY_INSUFFICIENT"
        assert data["error"]["stage"] == "image_quality_assessment"

    def test_upload_fatally_blurry_image_returns_422_image_quality_insufficient(
        self, client: TestClient, sample_prescription_image: bytes
    ):
        """Verifies that severely blurred images are rejected with diagnostic recommendations."""
        # Open valid image and apply strong Gaussian blur
        with Image.open(io.BytesIO(sample_prescription_image)) as im:
            blurry = im.filter(ImageFilter.GaussianBlur(radius=12.0))
            buf = io.BytesIO()
            blurry.save(buf, format="PNG")
            blurry_bytes = buf.getvalue()

        files = {"file": ("blurred_prescription.png", blurry_bytes, "image/png")}
        response = client.post("/api/v1/prescriptions/analyze", files=files)
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "IMAGE_QUALITY_INSUFFICIENT"
        assert data["error"]["stage"] == "image_quality_assessment"
        assert "blur" in data["error"]["message"].lower() or "optical" in data["error"]["message"].lower()
