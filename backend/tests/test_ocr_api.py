"""
Phase 5 Test Suite: OCR Baseline API Routes
Tests /api/v1/ocr/baseline endpoints using TestClient.
Verifies file upload, sample accession, variant comparison, and error responses.
"""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.app.main import create_app

app = create_app()
client = TestClient(app)


def get_test_image_bytes() -> bytes:
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "Augmentin 625 mg", fill=(0, 0, 0))
    draw.text((20, 80), "1-0-1 BD 5 days", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestOCREndpoints:
    """Verifies HTTP API endpoints for research OCR baseline."""

    def test_get_engine_status(self):
        response = client.get("/api/v1/ocr/baseline/engine")
        assert response.status_code == 200
        data = response.json()
        assert data["engine"] == "tesseract"
        assert data["available"] is True
        assert data["version"] is not None
        assert "eng" in data["languages"]
        assert "default_configuration" in data

    def test_post_ocr_baseline_with_file_upload(self):
        img_bytes = get_test_image_bytes()
        files = {"file": ("prescription.png", img_bytes, "image/png")}
        data = {"preprocessing_variant": "enhanced", "psm": 6}

        response = client.post("/api/v1/ocr/baseline", files=files, data=data)
        assert response.status_code == 200
        res = response.json()
        assert res["engine"]["name"] == "tesseract"
        assert res["preprocessing_artifact"] == "enhanced"
        assert "raw_text" in res
        assert "tokens" in res
        assert "lines" in res
        assert res["processing_status"] in ("completed", "partial")

    def test_post_ocr_baseline_with_sample_id(self):
        data = {"sample_id": "sample-1", "preprocessing_variant": "enhanced"}
        response = client.post("/api/v1/ocr/baseline", data=data)
        assert response.status_code == 200
        res = response.json()
        assert res["preprocessing_artifact"] == "enhanced"
        assert len(res["source_image_sha256"]) == 64
        assert len(res["tokens"]) > 0

    def test_post_ocr_baseline_missing_input_raises_400(self):
        response = client.post("/api/v1/ocr/baseline", data={})
        assert response.status_code == 400
        assert "Either a prescription image 'file' or a curated 'sample_id'" in response.text

    def test_post_ocr_baseline_nonexistent_sample_raises_404(self):
        data = {"sample_id": "nonexistent-sample-999"}
        response = client.post("/api/v1/ocr/baseline", data=data)
        assert response.status_code == 404

    def test_post_ocr_compare_variants(self):
        img_bytes = get_test_image_bytes()
        files = {"file": ("prescription.png", img_bytes, "image/png")}
        response = client.post("/api/v1/ocr/baseline/compare", files=files)
        assert response.status_code == 200
        res = response.json()
        assert isinstance(res, dict)
        assert "original" in res
        assert "enhanced" in res
        assert "grayscale" in res
        assert "thresholded" in res
