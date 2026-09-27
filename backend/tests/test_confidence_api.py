"""
API Integration tests for Phase 8 Confidence & Calibration Endpoints.
Tests:
- GET  /api/v1/confidence/config
- POST /api/v1/confidence/evaluate
- POST /api/v1/confidence/metrics
- GET  /api/v1/confidence/fixtures
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


class TestConfidenceAPI:
    def test_get_confidence_config(self, client):
        response = client.get("/api/v1/confidence/config")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "config_version" in data
        assert "config_hash" in data
        assert "calibration_status" in data

    def test_evaluate_confidence_endpoint_uncalibrated(self, client):
        payload = {
            "raw_score": 0.85,
            "field_name": "medicine_name",
            "source": "multimodal_model",
        }
        response = client.post("/api/v1/confidence/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["raw_signal"]["raw_value"] == 0.85
        assert data["calibration_status"] in ("calibrated", "insufficient_data", "uncalibrated")

    def test_evaluate_confidence_endpoint_null_score(self, client):
        payload = {
            "raw_score": None,
            "field_name": "duration",
            "source": "absent_field",
        }
        response = client.post("/api/v1/confidence/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["raw_signal"]["raw_value"] is None
        assert data["calibration_status"] == "not_available"

    def test_compute_metrics_endpoint_success(self, client):
        payload = {
            "confidences": [0.9, 0.8, 0.7, 0.2, 0.1],
            "labels": [1, 1, 1, 0, 0],
            "num_bins": 5,
        }
        response = client.post("/api/v1/confidence/metrics", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "ece" in data
        assert "mce" in data
        assert "brier_score" in data
        assert data["sample_count"] == 5
        assert len(data["bins"]) == 5

    def test_compute_metrics_endpoint_mismatch_error(self, client):
        payload = {
            "confidences": [0.9, 0.8],
            "labels": [1],
        }
        response = client.post("/api/v1/confidence/metrics", json=payload)
        assert response.status_code == 400
        assert "Length mismatch" in response.json()["detail"]

    def test_get_confidence_fixtures(self, client):
        response = client.get("/api/v1/confidence/fixtures")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 14
        assert len(data["fixtures"]) == 14
