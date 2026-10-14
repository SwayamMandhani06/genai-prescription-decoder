"""
Unit and Integration Regression Test for Pharmacist Human-in-the-Loop Verification
Adheres to Capstone Synopsis Fig. 1 and Audit Finding CRIT-04:
- POST /api/v1/prescriptions/{prescription_id}/verify
- Validates overridden drug against authoritative RAG index
- Checks LASA conflicts on confirmed medicine
- Sets confidence to 1.0 (PHARMACIST_VERIFIED)
- Clears abstention lock and generates verified multilingual explanation
"""

import pytest
from starlette.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_pharmacist_verification_endpoint():
    # 1. Send verification request
    payload = {
        "prescription_id": "RX-SAMPLE-TEST",
        "reviewer_id": "PHARM-MH-84920",
        "verified_items": [
            {
                "line_id": "line_1",
                "medicine_name": "Augmentin 625 Duo",
                "dosage": "625 mg",
                "frequency": "1-0-1 (BD)",
                "duration": "5 days",
                "instructions": "After food",
                "pharmacist_notes": "Handwritten cursive verified against clinical indications",
            }
        ],
        "target_languages": ["en", "hi", "mr"],
    }

    response = client.post("/api/v1/prescriptions/RX-SAMPLE-TEST/verify", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["status"] == "success"
    assert data["prescription_id"] == "RX-SAMPLE-TEST"
    assert data["data"]["document_confidence"] == 1.0

    # Verify RAG validation records
    assert "validation" in data
    assert "medicine_name" in data["validation"]
    assert data["validation"]["medicine_name"]["found_in_db"] is True


    # Verify fields confidence = 1.0 and status = confident
    med_field = data["fields"]["medicine_name"]
    assert med_field["confidence"] == 1.0
    assert med_field["status"] == "confident"
    assert med_field["calibration_status"] == "verified"
    assert med_field["abstention_decision"] == "accepted"
    assert med_field["requires_human_verification"] is False
    assert "PHARM-MH-84920" in med_field["explanation"]

    # Verify posology summary
    assert "PHARM-MH-84920" in data["explanation"]["en"]
    assert "PHARM-MH-84920" in data["explanation"]["hi"]
    assert "PHARM-MH-84920" in data["explanation"]["mr"]

    # Verify data block
    assert data["data"]["overall_status"] == "VERIFIED"
    assert data["data"]["document_confidence"] == 1.0


def test_pharmacist_verification_canonical_alias():
    payload = {
        "prescription_id": "RX-ALIAS-TEST",
        "reviewer_id": "PHARM-MH-99999",
        "verified_items": [
            {
                "line_id": "line_1",
                "medicine_name": "Paracetamol 500mg",
                "dosage": "500 mg",
                "frequency": "SOS",
                "duration": "3 days",
            }
        ],
    }

    response = client.post("/api/v1/prescriptions/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["document_confidence"] == 1.0
    assert data["fields"]["medicine_name"]["confidence"] == 1.0

