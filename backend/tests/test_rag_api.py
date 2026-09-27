"""
API Integration tests for Phase 7 RAG Medicine Validation Endpoints.
Tests:
- POST /api/v1/validation/medicine
- POST /api/v1/validation/medicine/batch
- GET /api/v1/validation/status
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


class TestRAGValidationAPI:
    def test_get_validation_status(self, client):
        response = client.get("/api/v1/validation/status")
        assert response.status_code == 200
        data = response.json()
        assert data["initialized"] is True
        assert "config_hash" in data
        assert data["index_stats"]["total_records"] == 30
        assert data["ingestion_report"]["valid_records_count"] == 30

    def test_validate_exact_medicine_success(self, client):
        payload = {
            "candidate_name": "Augmentin 625 Duo",
            "observed_dosage": "625 mg",
            "top_k": 5,
            "prescription_id": "TEST-RX-001"
        }
        response = client.post("/api/v1/validation/medicine", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["prescription_id"] == "TEST-RX-001"

        val_result = body["validation_result"]
        assert val_result["validation_status"] == "validated"
        assert val_result["medicine_identity_status"] == "validated"
        assert val_result["requires_human_review"] is False
        assert val_result["selected_reference"]["medicine_name"] == "Augmentin 625 Duo"
        assert val_result["dosage_observation_preserved"] is True
        assert val_result["observed_dosage"] == "625 mg"
        assert val_result["reference_strength"] == "625 mg"
        assert val_result["formulation_consistency"] == "consistent"

        ui_evidence = body["ui_evidence"]
        assert ui_evidence["candidate_name"] == "Augmentin 625 Duo"
        assert ui_evidence["matched_entity_name"] == "Augmentin 625 Duo"
        assert ui_evidence["validation_status"] == "cdsco_approved"
        assert "CDSCO" in ui_evidence["status_badge_text"]

    def test_validate_uncertain_medicine(self, client):
        payload = {
            "candidate_name": "Amox...",
            "observed_dosage": "500 mg",
        }
        response = client.post("/api/v1/validation/medicine", json=payload)
        assert response.status_code == 200
        body = response.json()
        val_result = body["validation_result"]
        assert val_result["validation_status"] == "uncertain"
        assert val_result["requires_human_review"] is True
        assert val_result["selected_reference"] is None

        ui_evidence = body["ui_evidence"]
        assert ui_evidence["validation_status"] == "unverified"
        assert "UNCERTAIN" in ui_evidence["status_badge_text"] or "AMBIGUOUS" in ui_evidence["status_badge_text"]

    def test_validate_unsupported_medicine(self, client):
        payload = {
            "candidate_name": "NonExistentFakeMed123",
        }
        response = client.post("/api/v1/validation/medicine", json=payload)
        assert response.status_code == 200
        body = response.json()
        val_result = body["validation_result"]
        assert val_result["validation_status"] == "not_validated"
        assert val_result["requires_human_review"] is True
        assert val_result["selected_reference"] is None

    def test_dosage_preservation_in_api(self, client):
        payload = {
            "candidate_name": "Augmentin 625 Duo",
            "observed_dosage": "875 mg",  # Visually extracted dosage differing from formulary 625 mg
        }
        response = client.post("/api/v1/validation/medicine", json=payload)
        assert response.status_code == 200
        body = response.json()
        val_result = body["validation_result"]
        # Dosage must NEVER be altered
        assert val_result["medicine_identity_status"] == "validated"
        assert val_result["dosage_observation_preserved"] is True
        assert val_result["observed_dosage"] == "875 mg"
        assert val_result["reference_strength"] == "625 mg"
        assert val_result["formulation_consistency"] == "mismatch"
        assert val_result["requires_human_review"] is True

    def test_batch_validation_endpoint(self, client):
        payload = {
            "items": [
                {"candidate_name": "Augmentin 625 Duo", "observed_dosage": "625 mg"},
                {"candidate_name": "Paracetamol 500mg", "observed_dosage": "500 mg"},
                {"candidate_name": "UnknownDrugXYZ", "observed_dosage": "10 mg"},
            ]
        }
        response = client.post("/api/v1/validation/medicine/batch", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["total_processed"] == 3
        results = body["results"]
        assert results[0]["validation_result"]["validation_status"] == "validated"
        assert results[1]["validation_result"]["validation_status"] == "validated"
        assert results[2]["validation_result"]["validation_status"] == "not_validated"
