"""
Phase 10 Tests: LASA API Endpoints.
Tests the FastAPI routes for LASA detection:
- GET  /api/v1/lasa/config
- POST /api/v1/lasa/screen
- POST /api/v1/lasa/detect
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestLasaAPI:
    """Tests for LASA detection API endpoints."""

    def test_get_config(self, client):
        """GET /api/v1/lasa/config returns active configuration."""
        resp = client.get("/api/v1/lasa/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "active"
        assert "policy_version" in data
        assert data["policy_version"] == "lasa_policy_v1"
        assert "config_hash" in data
        assert len(data["config_hash"]) == 64
        assert "orthographic_threshold" in data
        assert "phonetic_threshold" in data
        assert "combined_threshold" in data
        assert "known_pairs_count" in data
        assert data["known_pairs_count"] > 0

    def test_screen_known_pair(self, client):
        """POST /api/v1/lasa/screen detects Metformin → Metronidazole conflict."""
        resp = client.post(
            "/api/v1/lasa/screen",
            json={"candidate_name": "Metformin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        result = data["result"]
        assert result["prescribed_candidate"] == "Metformin"
        assert result["has_lasa_conflict"] is True
        # Must detect Metronidazole as a known pair
        confusable_names = [c["confusable_name"] for c in result["confusables"]]
        assert any("metronidazole" in n.lower() for n in confusable_names)

    def test_screen_safe_medicine(self, client):
        """POST /api/v1/lasa/screen for non-confusable medicine."""
        resp = client.post(
            "/api/v1/lasa/screen",
            json={"candidate_name": "Aspirin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        result = data["result"]
        assert result["prescribed_candidate"] == "Aspirin"

    def test_screen_empty_name_rejected(self, client):
        """POST /api/v1/lasa/screen with empty name returns 400."""
        resp = client.post(
            "/api/v1/lasa/screen",
            json={"candidate_name": ""},
        )
        assert resp.status_code == 400

    def test_detect_prescription(self, client):
        """POST /api/v1/lasa/detect runs full prescription LASA screening."""
        resp = client.post(
            "/api/v1/lasa/detect",
            json={
                "prescription_id": "RX-TEST-API-001",
                "medicine_names": ["Metformin", "Aspirin"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        result = data["result"]
        assert result["prescription_id"] == "RX-TEST-API-001"
        assert result["total_medicines_screened"] == 2
        assert len(result["medicines"]) == 2
        assert "provenance" in result
        assert result["provenance"]["policy_version"] == "lasa_policy_v1"

    def test_detect_with_single_medicine(self, client):
        """POST /api/v1/lasa/detect with a single medicine."""
        resp = client.post(
            "/api/v1/lasa/detect",
            json={
                "prescription_id": "RX-TEST-API-002",
                "medicine_names": ["Prednisolone"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["total_medicines_screened"] == 1

    def test_detect_provenance_includes_config_hash(self, client):
        """Provenance must include deterministic config hash."""
        resp = client.post(
            "/api/v1/lasa/detect",
            json={
                "prescription_id": "RX-TEST-API-003",
                "medicine_names": ["Metformin"],
            },
        )
        assert resp.status_code == 200
        prov = resp.json()["result"]["provenance"]
        assert len(prov["config_hash"]) == 64
        assert prov["reference_pool_size"] > 0
        assert prov["known_pairs_count"] > 0
