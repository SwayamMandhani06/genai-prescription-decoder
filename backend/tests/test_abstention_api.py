"""
Integration tests for Phase 9 Abstention and Human Verification FastAPI Endpoints.
Verifies:
- GET  /api/v1/abstention/config
- POST /api/v1/abstention/evaluate
- GET  /api/v1/abstention/fixtures
- GET  /api/v1/abstention/fixtures/{fixture_id}
- POST /api/v1/verification/{id}/fields/{field}/confirm
- POST /api/v1/verification/{id}/fields/{field}/correct
- POST /api/v1/verification/{id}/fields/{field}/unreadable
- GET  /api/v1/verification/{id}
- Error handling on invalid/empty inputs
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestAbstentionApi:
    def test_get_abstention_config(self):
        res = client.get("/api/v1/abstention/config")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["policy_version"] == "abstention_policy_v1"
        assert data["min_calibrated_confidence"] == 0.80
        assert data["require_calibration_for_acceptance"] is True
        assert len(data["config_hash"]) == 64

    def test_evaluate_field_accepted(self):
        payload = {
            "field_name": "medicine_name",
            "value": "Augmentin 625 Duo",
            "status": "confident",
            "presence": "present",
            "extraction_state": "extracted",
            "raw_confidence": 0.95,
            "calibrated_confidence": 0.92,
            "calibration_status": "calibrated",
            "calibration_method": "platt_scaling",
        }
        res = client.post("/api/v1/abstention/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["decision"] == "accepted"
        assert data["requires_human_verification"] is False
        assert len(data["reason_codes"]) == 0

    def test_evaluate_field_abstained_insufficient_data(self):
        payload = {
            "field_name": "dosage",
            "value": "1000 mg",
            "status": "confident",
            "presence": "present",
            "extraction_state": "extracted",
            "raw_confidence": 0.95,
            "calibrated_confidence": None,
            "calibration_status": "insufficient_data",
        }
        res = client.post("/api/v1/abstention/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["decision"] == "abstained"
        assert data["requires_human_verification"] is True
        assert "CALIBRATION_INSUFFICIENT_DATA" in data["reason_codes"]
        assert data["observed_dosage_preserved"] is True

    def test_get_fixtures_list_and_single(self):
        res = client.get("/api/v1/abstention/fixtures")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 15

        res_single = client.get("/api/v1/abstention/fixtures/CASE-09-01-HIGH-CONFIDENCE-ACCEPT")
        assert res_single.status_code == 200
        assert res_single.json()["fixture_id"] == "CASE-09-01-HIGH-CONFIDENCE-ACCEPT"

        res_404 = client.get("/api/v1/abstention/fixtures/INVALID-FIXTURE-ID")
        assert res_404.status_code == 404

    def test_verification_workflow_actions(self):
        presc_id = "RX-API-TEST-001"

        # 1. Confirm action
        confirm_res = client.post(
            f"/api/v1/verification/{presc_id}/fields/medicine_name/confirm",
            json={"original_value": "Augmentin 625 Duo", "reason": "Accurate transcription."},
        )
        assert confirm_res.status_code == 200
        conf_data = confirm_res.json()
        assert conf_data["verification_status"] == "confirmed"
        assert conf_data["original_value"] == "Augmentin 625 Duo"

        # 2. Correct action
        correct_res = client.post(
            f"/api/v1/verification/{presc_id}/fields/dosage/correct",
            json={"original_value": "50 mg", "corrected_value": "500 mg", "reason": "Corrected missed numeral."},
        )
        assert correct_res.status_code == 200
        corr_data = correct_res.json()
        assert corr_data["verification_status"] == "corrected"
        assert corr_data["original_value"] == "50 mg"
        assert corr_data["verified_value"] == "500 mg"

        # 3. Mark unreadable action
        unread_res = client.post(
            f"/api/v1/verification/{presc_id}/fields/duration/unreadable",
            json={"original_value": "???", "reason": "Optical stroke degradation."},
        )
        assert unread_res.status_code == 200
        unread_data = unread_res.json()
        assert unread_data["verification_status"] == "unreadable"
        assert unread_data["verified_value"] is None

        # 4. Retrieve complete verification state
        state_res = client.get(f"/api/v1/verification/{presc_id}")
        assert state_res.status_code == 200
        state_data = state_res.json()
        assert state_data["prescription_id"] == presc_id
        assert len(state_data["records"]) == 3
        assert len(state_data["audit_trail"]) == 3

    def test_verification_correct_empty_value_fails(self):
        res = client.post(
            "/api/v1/verification/RX-FAIL/fields/dosage/correct",
            json={"corrected_value": "   "},
        )
        assert res.status_code == 422
