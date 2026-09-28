"""
Phase 11 API Tests: Explanation Endpoints.
Tests:
- GET  /api/v1/explanation/config
- POST /api/v1/explanation/generate
- GET  /api/v1/explanation/fixtures
- Error handling, malformed requests, failure semantics
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_explanation_config():
    response = client.get("/api/v1/explanation/config")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["policy_version"] == "explanation_policy_v1"
    assert data["template_version"] == "explanation_template_v1"
    assert data["terminology_version"] == "explanation_terminology_v1"
    assert len(data["config_hash"]) == 64
    assert data["supported_languages"] == ["en", "hi", "mr"]
    assert "provenance" in data


def test_generate_explanation_valid_posology():
    payload = {
        "prescription_id": "RX-API-001",
        "medicine_name": "Paracetamol",
        "dosage": "500 mg",
        "frequency": "twice daily",
        "duration": "5 days",
    }
    response = client.post("/api/v1/explanation/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prescription_id"] == "RX-API-001"
    assert data["overall_eligibility"] == "eligible"
    assert "en" in data["explanations"]
    assert "hi" in data["explanations"]
    assert "mr" in data["explanations"]

    en = data["explanations"]["en"]
    assert "Paracetamol" in en["summary"]
    assert "500 mg" in en["summary"]
    assert "twice daily" in en["summary"]
    assert "5 days" in en["summary"]
    assert en["validation"]["medicine_fidelity"] is True
    assert en["validation"]["numeric_fidelity"] is True
    assert en["validation"]["unsupported_fact_check"] is True


def test_generate_explanation_uncertain_medicine():
    payload = {
        "prescription_id": "RX-API-002",
        "medicine_name": "Amoxi...",
        "candidate_status": "uncertain",
        "requires_human_verification": True,
    }
    response = client.post("/api/v1/explanation/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_eligibility"] == "restricted"
    assert "could not be read with sufficient confidence" in data["explanations"]["en"]["summary"]


def test_generate_explanation_lasa_conflict():
    payload = {
        "prescription_id": "RX-API-003",
        "medicine_name": "Prednisone",
        "has_lasa_conflict": True,
        "confusable_counterpart": "Prednisolone",
    }
    response = client.post("/api/v1/explanation/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_eligibility"] == "restricted"
    assert "Similar medicine names were detected" in data["explanations"]["en"]["summary"]


def test_generate_explanation_human_corrected():
    payload = {
        "prescription_id": "RX-API-004",
        "medicine_name": "Amox...",
        "human_verification_status": "corrected",
        "human_verified_value": "Amoxicillin",
        "dosage": "500 mg",
    }
    response = client.post("/api/v1/explanation/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_eligibility"] == "eligible"
    assert "Amoxicillin" in data["explanations"]["en"]["summary"]


def test_generate_explanation_service_unavailable():
    payload = {
        "prescription_id": "RX-API-005",
        "medicine_name": "Paracetamol",
        "is_service_healthy": False,
    }
    response = client.post("/api/v1/explanation/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_eligibility"] == "unavailable"
    assert "currently unavailable" in data["explanations"]["en"]["summary"]


def test_generate_explanation_empty_prescription_id_fails():
    payload = {
        "prescription_id": "",
        "medicine_name": "Paracetamol",
    }
    response = client.post("/api/v1/explanation/generate", json=payload)
    assert response.status_code in (400, 422)


def test_get_explanation_fixtures():
    response = client.get("/api/v1/explanation/fixtures")
    assert response.status_code == 200
    data = response.json()
    assert data["fixture_count"] >= 22
    assert "fixtures" in data
    assert "DEVELOPMENT TEST FIXTURES" in data["notice"]
