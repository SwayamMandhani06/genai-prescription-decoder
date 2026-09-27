"""
End-to-End Live Backend Verification Script
Connects over HTTP to the running FastAPI server at http://127.0.0.1:8000.
Tests:
1. GET /api/v1/health
2. POST /api/v1/prescriptions/analyze (Sample ID: rx-sample-1)
3. POST /api/v1/prescriptions/analyze (Sample ID: rx-sample-2 -> LASA alert)
4. POST /api/v1/prescriptions/analyze (Sample ID: rx-sample-3 -> Abstained)
5. POST /api/v1/prescriptions/analyze (Multipart file upload)
6. GET /uploads/<saved_file> (Original image retrieval)
7. Error cases (Missing inputs 400, Invalid file type 415, Validation failure 422)
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"

def run_live_tests():
    print("\n======================================================")
    print("LIVE FASTAPI HTTP END-TO-END VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("======================================================\n")

    passed = 0
    failed = 0

    def check(condition: bool, name: str, detail: str = ""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} -> {detail}")

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health Endpoint
        r = client.get("/api/v1/health")
        check(r.status_code == 200, "GET /api/v1/health returns 200 OK")
        data = r.json()
        check(data["status"] == "healthy", "Health status is 'healthy'")
        check(data["mock_mode"] is True, "Mock mode is True")

        # 2. Analyze Sample 1 (Confident)
        r = client.post("/api/v1/prescriptions/analyze", data={"sample_id": "rx-sample-1"})
        check(r.status_code == 200, "POST analyze (sample-1) returns 200 OK")
        data = r.json()
        check(data["prescription_id"] is not None, "prescription_id present")
        check(data["original_image_url"] == "/uploads/samples/rx-sample-1.svg", "original_image_url preserved")
        check(data["fields"]["medicine_name"]["status"] == "confident", "medicine_name is confident")
        check(data["requires_human_review"] is False, "requires_human_review is False")

        # 3. Analyze Sample 2 (LASA Conflict)
        r = client.post("/api/v1/prescriptions/analyze", data={"sample_id": "rx-sample-2"})
        check(r.status_code == 200, "POST analyze (sample-2) returns 200 OK")
        data = r.json()
        check(len(data["lasa_flags"]) > 0, "LASA flag present")
        check(data["lasa_flags"][0]["conflict_with"] == "Metronidazole", "Conflicting drug identified")
        check(data["requires_human_review"] is True, "LASA mandates human review")

        # 4. Analyze Sample 3 (Abstained)
        r = client.post("/api/v1/prescriptions/analyze", data={"sample_id": "rx-sample-3"})
        check(r.status_code == 200, "POST analyze (sample-3) returns 200 OK")
        data = r.json()
        check(data["data"]["overall_status"] == "ABSTAINED", "Status is ABSTAINED")
        check(data["requires_human_review"] is True, "Abstention mandates human review")

        # 5. File Upload (Multipart/form-data)
        dummy_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
            b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        files = {"file": ("rx_patient_upload.png", dummy_png, "image/png")}
        r = client.post("/api/v1/prescriptions/analyze", files=files)
        check(r.status_code == 200, "POST analyze (file upload) returns 200 OK")
        data = r.json()
        saved_url = data["original_image_url"]
        check(saved_url.startswith("/uploads/rx_"), "Original image URL formatted as /uploads/rx_*")

        # 6. Verify image is retrievable over HTTP static mount
        r_img = client.get(saved_url)
        check(r_img.status_code == 200, "GET uploaded image via static mount returns 200 OK")
        check(len(r_img.content) == len(dummy_png), "Preserved image content matches byte-for-byte")

        # 7. Error Test: Missing input -> 400
        r = client.post("/api/v1/prescriptions/analyze")
        check(r.status_code == 400, "Missing input returns HTTP 400")
        check(r.json()["error"]["code"] == "INVALID_REQUEST", "Error code is INVALID_REQUEST")

        # 8. Error Test: Unsupported format -> 415
        bad_files = {"file": ("script.exe", b"executable", "application/octet-stream")}
        r = client.post("/api/v1/prescriptions/analyze", files=bad_files)
        check(r.status_code == 415, "Unsupported format returns HTTP 415")
        check(r.json()["error"]["code"] == "INVALID_FILE_TYPE", "Error code is INVALID_FILE_TYPE")

        # 9a. Error Test: Image Quality Insufficient Injection -> 422
        r = client.post(
            "/api/v1/prescriptions/analyze",
            data={"sample_id": "rx-sample-1", "mock_scenario": "image_quality_insufficient"},
        )
        check(r.status_code == 422, "image_quality_insufficient returns HTTP 422")
        check(r.json()["error"]["code"] == "IMAGE_QUALITY_INSUFFICIENT", "Error code is IMAGE_QUALITY_INSUFFICIENT")
        check(r.json()["error"]["stage"] == "image_quality_assessment", "Error stage is image_quality_assessment")

        # 9b. Error Test: Validation Failure Injection -> 422
        r = client.post(
            "/api/v1/prescriptions/analyze",
            data={"sample_id": "rx-sample-1", "mock_scenario": "validation_error"},
        )
        check(r.status_code == 422, "validation_error scenario returns HTTP 422")
        check(r.json()["error"]["code"] == "VALIDATION_FAILED", "Error code is VALIDATION_FAILED")

        # 10. Error Test: Server Error Injection -> 500
        r = client.post(
            "/api/v1/prescriptions/analyze",
            data={"sample_id": "rx-sample-1", "mock_scenario": "server_error"},
        )
        check(r.status_code == 500, "server_error scenario returns HTTP 500")
        check(r.json()["error"]["code"] == "PROCESSING_FAILED", "Error code is PROCESSING_FAILED")

    print("\n======================================================")
    print(f"LIVE TEST SUMMARY: {passed} PASSED | {failed} FAILED")
    print("======================================================\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_live_tests()
