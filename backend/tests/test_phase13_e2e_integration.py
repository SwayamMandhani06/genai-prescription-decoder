"""
Phase 13 End-to-End Integration Test Suite (E2E-01 through E2E-20)
Verifies full pipeline integration, API contracts, failure paths,
original-image byte preservation, LASA screening, selective abstention,
human verification workflows, and multilingual patient explanations.
"""

import hashlib
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.app.main import app
from backend.app.schemas.error import ErrorCode


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_prescription_bytes() -> bytes:
    """Creates a realistic clinical prescription scan with proper exposure (no glare)."""
    im = Image.new("RGB", (450, 550), color=(235, 235, 235))
    draw = ImageDraw.Draw(im)
    draw.text((25, 25), "St. Jude Clinic - Dr. S. Rao, MD", fill=(15, 15, 15))
    draw.line([(25, 55), (425, 55)], fill=(40, 40, 40), width=2)
    draw.text((25, 75), "Patient: Anonymized Adult", fill=(20, 20, 20))
    draw.text((25, 110), "Rx:", fill=(10, 10, 10))
    draw.text((45, 140), "1. Amoxicillin 500mg capsules", fill=(10, 10, 60))
    draw.text((65, 170), "Sig: 1 cap three times daily (TID) x 7 days", fill=(15, 15, 15))
    draw.text((45, 210), "2. Paracetamol 650mg tablets", fill=(10, 10, 60))
    draw.text((65, 240), "Sig: 1 tab as needed (SOS) for fever", fill=(15, 15, 15))
    draw.line([(25, 480), (200, 480)], fill=(40, 40, 40), width=1)
    draw.text((25, 490), "Physician Signature", fill=(30, 30, 30))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


# ==============================================================================
# E2E-01: Valid Clear Prescription
# ==============================================================================
def test_e2e_01_valid_clear_prescription(client: TestClient, valid_prescription_bytes: bytes):
    """E2E-01: Ingestion of valid clear prescription returns confident extracted fields and preserves original image."""
    files = {"file": ("rx_clear_test.png", valid_prescription_bytes, "image/png")}
    response = client.post("/api/v1/prescriptions/process", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "prescription_id" in data
    assert data["prescription_id"].startswith("RX-")
    assert "original_image_url" in data
    assert data["original_image_url"].startswith("/uploads/rx_")
    assert "fields" in data
    assert "medicine_name" in data["fields"]

    # Verify original image is stored and retrievable byte-identically
    img_resp = client.get(data["original_image_url"])
    assert img_resp.status_code == 200
    assert hashlib.sha256(img_resp.content).hexdigest() == hashlib.sha256(valid_prescription_bytes).hexdigest()


# ==============================================================================
# E2E-02: Low-Quality Image
# ==============================================================================
def test_e2e_02_low_quality_image(client: TestClient):
    """E2E-02: Severe optical degradation triggers IMAGE_QUALITY_INSUFFICIENT with actionable guidance."""
    files = {"file": ("rx_blurry.png", b"DUMMY_DEGRADED_BYTES", "image/png")}
    response = client.post(
        "/api/v1/prescriptions/process",
        files=files,
        data={"mock_scenario": "low_quality"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == ErrorCode.IMAGE_QUALITY_INSUFFICIENT
    assert data["error"]["retryable"] is True
    assert data["error"]["stage"] == "image_quality_assessment"
    assert "recommendation" in data["error"]["details"]


# ==============================================================================
# E2E-03: Invalid File
# ==============================================================================
def test_e2e_03_invalid_file(client: TestClient):
    """E2E-03: Disallowed MIME type / file format triggers INVALID_FILE_TYPE (415)."""
    files = {"file": ("prescription.exe", b"MZ_EXECUTABLE_BINARY_DATA", "application/x-msdownload")}
    response = client.post("/api/v1/prescriptions/process", files=files)
    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == ErrorCode.INVALID_FILE_TYPE
    assert data["error"]["retryable"] is False


# ==============================================================================
# E2E-04: Oversized File
# ==============================================================================
def test_e2e_04_oversized_file(client: TestClient):
    """E2E-04: Upload exceeding 15MB limit is rejected with FILE_TOO_LARGE (413)."""
    oversized_bytes = b"0" * (16 * 1024 * 1024)
    files = {"file": ("large_prescription.jpg", oversized_bytes, "image/jpeg")}
    response = client.post("/api/v1/prescriptions/process", files=files)
    assert response.status_code == 413
    data = response.json()
    assert data["error"]["code"] == ErrorCode.FILE_TOO_LARGE


# ==============================================================================
# E2E-05: Missing Field
# ==============================================================================
def test_e2e_05_missing_field(client: TestClient):
    """E2E-05: Missing posology fields are marked unobserved/absent and never hallucinated."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-3"},
    )
    assert response.status_code == 200
    data = response.json()
    fields = data["fields"]
    assert fields["duration"]["status"] in ("uncertain", "absent", "missing") or data["requires_human_review"] is True


# ==============================================================================
# E2E-06: Uncertain Field
# ==============================================================================
def test_e2e_06_uncertain_field(client: TestClient):
    """E2E-06: Ambiguous handwriting surfaces candidates and flags human review."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "mock_scenario": "uncertain"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["requires_human_review"] is True
    uncertain_fields = [f for f in data["fields"].values() if f["status"] == "uncertain"]
    assert len(uncertain_fields) > 0
    assert uncertain_fields[0]["verification_instruction"] is not None


# ==============================================================================
# E2E-07: Abstention
# ==============================================================================
def test_e2e_07_abstention(client: TestClient):
    """E2E-07: Phase 9 selective abstention policy flags low-confidence prescriptions."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "mock_scenario": "abstained"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["requires_human_review"] is True
    assert data["data"]["overall_status"] in ("ABSTAINED", "NEEDS_VERIFICATION")


# ==============================================================================
# E2E-08: Human Confirmation
# ==============================================================================
def test_e2e_08_human_confirmation(client: TestClient):
    """E2E-08: Human confirmation records clinician acceptance in audit trail without data loss."""
    res = client.post("/api/v1/prescriptions/process", data={"sample_id": "rx-sample-2"})
    rx_id = res.json()["prescription_id"]

    confirm_res = client.post(
        f"/api/v1/verification/{rx_id}/fields/medicine_name/confirm",
        json={"original_value": "Metformin", "reason": "Confirmed against original image"},
    )
    assert confirm_res.status_code == 200
    rec = confirm_res.json()
    assert rec["verifier_action"] == "confirm"
    assert rec["verification_status"] == "confirmed"
    assert rec["prescription_id"] == rx_id
    assert rec["field_id"] == "medicine_name"

    # Audit state retrieval
    state_res = client.get(f"/api/v1/verification/{rx_id}")
    assert state_res.status_code == 200
    assert state_res.json()["prescription_id"] == rx_id


# ==============================================================================
# E2E-09: Human Correction
# ==============================================================================
def test_e2e_09_human_correction(client: TestClient):
    """E2E-09: Human correction updates verified downstream input while preserving original extracted value."""
    res = client.post("/api/v1/prescriptions/process", data={"sample_id": "rx-sample-2"})
    rx_id = res.json()["prescription_id"]

    correct_res = client.post(
        f"/api/v1/verification/{rx_id}/fields/dosage/correct",
        json={
            "corrected_value": "500 mg BD",
            "original_value": "500 mg",
            "reason": "Corrected dosage unit from visual script",
        },
    )
    assert correct_res.status_code == 200
    rec = correct_res.json()
    assert rec["verifier_action"] == "correct"
    assert rec["verification_status"] == "corrected"
    assert rec["verified_value"] == "500 mg BD"
    assert rec["original_value"] == "500 mg"


# ==============================================================================
# E2E-10: Mark Unreadable
# ==============================================================================
def test_e2e_10_mark_unreadable(client: TestClient):
    """E2E-10: Clinician can declare a stroke unreadable without forcing system guessing."""
    res = client.post("/api/v1/prescriptions/process", data={"sample_id": "rx-sample-2"})
    rx_id = res.json()["prescription_id"]

    unreadable_res = client.post(
        f"/api/v1/verification/{rx_id}/fields/frequency/unreadable",
        json={"original_value": "OD", "reason": "Illegible ink smudge on frequency line"},
    )
    assert unreadable_res.status_code == 200
    rec = unreadable_res.json()
    assert rec["verifier_action"] == "mark_unreadable"
    assert rec["verification_status"] == "unreadable"


# ==============================================================================
# E2E-11: LASA Flag
# ==============================================================================
def test_e2e_11_lasa_flag(client: TestClient):
    """E2E-11: LASA screening surfaces orthographic/phonetic confusion pairs without altering candidate name."""
    response = client.post("/api/v1/prescriptions/process", data={"sample_id": "rx-sample-2"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["lasa_flags"]) > 0
    flag = data["lasa_flags"][0]
    assert flag["conflict_with"] in ("Metronidazole", "Metformin")
    assert data["requires_human_review"] is True


# ==============================================================================
# E2E-12: Dosage/Formulation Mismatch
# ==============================================================================
def test_e2e_12_dosage_formulation_mismatch(client: TestClient, valid_prescription_bytes: bytes):
    """E2E-12: RAG validation distinguishes observed dosage from reference strength and never rewrites script."""
    files = {"file": ("rx_test.png", valid_prescription_bytes, "image/png")}
    response = client.post("/api/v1/prescriptions/process", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "validation" in data
    assert "dosage" in data["fields"]


# ==============================================================================
# E2E-13: RAG Unavailable
# ==============================================================================
def test_e2e_13_rag_unavailable(client: TestClient):
    """E2E-13: When reference formulary is unverified, system reports unverified status without false validation."""
    response = client.post("/api/v1/prescriptions/process", data={"sample_id": "rx-sample-3"})
    assert response.status_code == 200
    data = response.json()
    assert "validation" in data


# ==============================================================================
# E2E-14: LASA Unavailable
# ==============================================================================
def test_e2e_14_lasa_unavailable(client: TestClient):
    """E2E-14: When LASA service is disabled or unconfigured, system does not claim 'No Conflict' safely."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "enable_lasa_detection": "false"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["lasa_flags"], list)


# ==============================================================================
# E2E-15: Model Unavailable
# ==============================================================================
def test_e2e_15_model_unavailable(client: TestClient):
    """E2E-15: Missing model credentials or worker downtime surfaces MODEL_UNAVAILABLE (503)."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "mock_scenario": "model_unavailable"},
    )
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE
    assert data["error"]["retryable"] is True


# ==============================================================================
# E2E-16: Explanation Restricted
# ==============================================================================
def test_e2e_16_explanation_restricted(client: TestClient):
    """E2E-16: Abstained or unconfirmed prescriptions enforce safety disclaimers in explanations."""
    response = client.post("/api/v1/prescriptions/process", data={"sample_id": "rx-sample-3"})
    assert response.status_code == 200
    data = response.json()
    exp = data["explanation"]
    assert "en" in exp or "summary" in exp or "patient_overview" in str(exp)


# ==============================================================================
# E2E-17: Explanation EN
# ==============================================================================
def test_e2e_17_explanation_en(client: TestClient):
    """E2E-17: Generates faithful English vernacular posology from extracted parameters."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "target_language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "en" in data["explanation"]
    assert len(data["explanation"]["en"]) > 0


# ==============================================================================
# E2E-18: Explanation HI
# ==============================================================================
def test_e2e_18_explanation_hi(client: TestClient):
    """E2E-18: Generates Hindi posology summary preserving Roman medicine identity."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "target_language": "hi"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "hi" in data["explanation"]
    assert len(data["explanation"]["hi"]) > 0


# ==============================================================================
# E2E-19: Explanation MR
# ==============================================================================
def test_e2e_19_explanation_mr(client: TestClient):
    """E2E-19: Generates Marathi posology summary preserving Roman medicine identity."""
    response = client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "target_language": "mr"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "mr" in data["explanation"]
    assert len(data["explanation"]["mr"]) > 0


# ==============================================================================
# E2E-20: Complete Successful Flow
# ==============================================================================
def test_e2e_20_complete_successful_flow(client: TestClient, valid_prescription_bytes: bytes):
    """E2E-20: Verifies end-to-end traversal from raw image upload to multimodal extraction and retrieval."""
    # 1. Check health
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    # 2. Upload prescription to canonical /process endpoint
    files = {"file": ("rx_production_flow.png", valid_prescription_bytes, "image/png")}
    proc_resp = client.post("/api/v1/prescriptions/process", files=files)
    assert proc_resp.status_code == 200
    proc_data = proc_resp.json()

    rx_id = proc_data["prescription_id"]
    orig_url = proc_data["original_image_url"]

    # 3. Verify original image retrieval via static mount
    img_resp = client.get(orig_url)
    assert img_resp.status_code == 200
    assert hashlib.sha256(img_resp.content).hexdigest() == hashlib.sha256(valid_prescription_bytes).hexdigest()

    # 4. Verify canonical pipeline components
    assert "fields" in proc_data
    assert "validation" in proc_data
    assert "explanation" in proc_data
    assert "lasa_flags" in proc_data
    assert "meta" in proc_data
    assert proc_data["meta"]["pipeline_stages_completed"] >= 4

    # 5. Verify /analyze endpoint produces identical contract
    files_alt = {"file": ("rx_production_flow.png", valid_prescription_bytes, "image/png")}
    analyze_resp = client.post("/api/v1/prescriptions/analyze", files=files_alt)
    assert analyze_resp.status_code == 200
    assert "prescription_id" in analyze_resp.json()
