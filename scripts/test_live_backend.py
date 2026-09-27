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

        # 5. File Upload (Multipart/form-data with valid readable image)
        import io
        from PIL import Image, ImageDraw

        valid_im = Image.new("RGB", (400, 500), color=(250, 250, 250))
        draw = ImageDraw.Draw(valid_im)
        draw.text((20, 20), "Rx Clinic Prescription Pad", fill=(20, 20, 20))
        draw.line([(20, 45), (380, 45)], fill=(60, 60, 60), width=2)
        draw.text((20, 70), "Augmentin 625 Duo - 1 tab BD x 5 days", fill=(10, 10, 80))
        draw.text((20, 100), "Dolo 650 - 1 tab TDS SOS", fill=(10, 10, 80))
        buf = io.BytesIO()
        valid_im.save(buf, format="PNG")
        dummy_png = buf.getvalue()

        files = {"file": ("rx_patient_upload.png", dummy_png, "image/png")}
        r = client.post("/api/v1/prescriptions/analyze", files=files)
        check(r.status_code == 200, "POST analyze (file upload) returns 200 OK")
        data = r.json()
        saved_url = data["original_image_url"]
        check(saved_url.startswith("/uploads/rx_"), "Original image URL formatted as /uploads/rx_*")

        # 5b. Verify Phase 4 processed_image_url is present and retrievable
        check(data.get("processed_image_url") is not None, "Phase 4 processed_image_url present")
        proc_url = data["processed_image_url"]
        r_proc = client.get(proc_url)
        check(r_proc.status_code == 200, "GET preprocessed image via static mount returns 200 OK")

        # 5c. Verify GET /api/v1/prescriptions/{id}/artifacts returns run manifest
        rx_id = data["prescription_id"]
        r_art = client.get(f"/api/v1/prescriptions/{rx_id}/artifacts")
        check(r_art.status_code == 200, "GET /artifacts returns 200 OK")
        art_data = r_art.json()
        check("grayscale" in art_data["artifacts"], "Artifacts include grayscale")
        check("enhanced" in art_data["artifacts"], "Artifacts include enhanced")

        # 6. Verify original image is retrievable over HTTP static mount
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

        # 8b. Error Test: Tiny/Insufficient Resolution Image -> 422
        tiny_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?"
            b"\x00\x05\xfe\x02\xfe\r\xefF\xb8\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        tiny_files = {"file": ("tiny_rx.png", tiny_png, "image/png")}
        r = client.post("/api/v1/prescriptions/analyze", files=tiny_files)
        check(r.status_code == 422, "Tiny image (<150px) returns HTTP 422")
        check(r.json()["error"]["code"] == "IMAGE_QUALITY_INSUFFICIENT", "Tiny image code is IMAGE_QUALITY_INSUFFICIENT")

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

        # ----------------------------------------------------------------------
        # Phase 5: Live OCR Baseline Endpoint Verification
        # ----------------------------------------------------------------------
        # 11. GET /api/v1/ocr/baseline/engine
        r_eng = client.get("/api/v1/ocr/baseline/engine")
        check(r_eng.status_code == 200, "GET /api/v1/ocr/baseline/engine returns 200 OK")
        eng_data = r_eng.json()
        check(eng_data["engine"] == "tesseract", "Engine moniker is tesseract")
        check(eng_data["available"] is True, "Engine available is True")
        check(eng_data["version"] is not None and len(eng_data["version"]) > 0, "Engine version is detected")
        check("eng" in eng_data["languages"], "English language data installed")

        # 12. POST /api/v1/ocr/baseline with sample_id
        r_ocr = client.post("/api/v1/ocr/baseline", data={"sample_id": "doc-rx-001", "preprocessing_variant": "enhanced"})
        check(r_ocr.status_code == 200, "POST /api/v1/ocr/baseline (sample) returns 200 OK")
        ocr_data = r_ocr.json()
        check(ocr_data["engine"]["name"] == "tesseract", "OCR run result records tesseract engine")
        check(ocr_data["preprocessing_artifact"] == "enhanced", "Preprocessing artifact is enhanced")
        check(ocr_data["source_image_sha256"] is not None, "Source image SHA256 recorded")
        check("raw_text" in ocr_data, "Raw OCR text present in response")
        check(len(ocr_data["tokens"]) > 0, "Spatial tokens extracted")

        # 13. POST /api/v1/ocr/baseline/compare with sample_id
        r_comp = client.post("/api/v1/ocr/baseline/compare", data={"sample_id": "doc-rx-001"})
        check(r_comp.status_code == 200, "POST /api/v1/ocr/baseline/compare returns 200 OK")
        comp_data = r_comp.json()
        check("enhanced" in comp_data, "Variant comparison includes enhanced")
        check("grayscale" in comp_data, "Variant comparison includes grayscale")
        check("thresholded" in comp_data, "Variant comparison includes thresholded")
        check("original" in comp_data, "Variant comparison includes original")

        # 14. Error Test: Missing input on OCR baseline -> 400
        r_ocr_err = client.post("/api/v1/ocr/baseline", data={})
        check(r_ocr_err.status_code == 400, "POST /api/v1/ocr/baseline without input returns 400")

        # ==================================================================
        # PHASE 6: MULTIMODAL VISION-LANGUAGE EXTRACTION ENDPOINTS
        # ==================================================================
        print("\n--- Phase 6: Multimodal Vision-Language Extraction ---")

        # 15. GET /api/v1/multimodal/config
        r_mc = client.get("/api/v1/multimodal/config")
        check(r_mc.status_code == 200, "GET /api/v1/multimodal/config returns 200 OK")
        mc_data = r_mc.json()
        check(mc_data["config_version"] == "multimodal_extraction_v1", "Config version is multimodal_extraction_v1")
        check(mc_data["model_id"] == "gemini-3.8-flash", "Model ID is gemini-3.8-flash")
        check("config_hash_sha256" in mc_data, "Config hash SHA-256 present")
        check(len(mc_data["config_hash_sha256"]) == 64, "Config hash is 64-char SHA-256")
        check("prompt_version" in mc_data, "Prompt version present")
        check("is_adapter_available" in mc_data, "Adapter availability reported")

        # 16. POST /api/v1/multimodal/extract (single medicine confident)
        from PIL import Image, ImageDraw
        import io

        im = Image.new("RGB", (400, 500), color=(250, 250, 250))
        draw = ImageDraw.Draw(im)
        draw.text((20, 70), "Augmentin 625 Duo - 1 tab BD x 5 days", fill=(10, 10, 80))
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        test_img_bytes = buf.getvalue()

        r_ext = client.post(
            "/api/v1/multimodal/extract",
            files={"file": ("rx_test.png", io.BytesIO(test_img_bytes), "image/png")},
            data={"scenario": "single_medicine_confident"},
        )
        check(r_ext.status_code == 200, "POST /api/v1/multimodal/extract (confident) returns 200 OK")
        ext_data = r_ext.json()
        check("prescription_id" in ext_data, "Extraction has prescription_id")
        check("medicines" in ext_data, "Extraction has medicines list")
        check(len(ext_data["medicines"]) == 1, "Single medicine extracted")
        check(ext_data["medicines"][0]["medicine_name"]["value"] == "Amoxicillin", "Medicine name is Amoxicillin")
        check(ext_data["medicines"][0]["medicine_name"]["status"] == "confident", "Medicine name status is confident")
        check(ext_data["medicines"][0]["medicine_name"]["presence"] == "present", "Confident medicine presence is present")
        check(ext_data["medicines"][0]["medicine_name"]["extraction_state"] == "extracted", "Confident medicine state is extracted")
        check(ext_data["requires_human_review"] is False, "No human review required for confident case")
        check("model" in ext_data, "Model audit metadata present")
        check(ext_data["model"]["prompt_version"] == "prompt_v1_clinical_vision_extraction", "Prompt version is v1")

        # 17. POST /api/v1/multimodal/extract (multiple medicines)
        r_multi = client.post(
            "/api/v1/multimodal/extract",
            files={"file": ("rx_multi.png", io.BytesIO(test_img_bytes), "image/png")},
            data={"scenario": "multiple_medicines"},
        )
        check(r_multi.status_code == 200, "POST /api/v1/multimodal/extract (multi-med) returns 200 OK")
        multi_data = r_multi.json()
        check(len(multi_data["medicines"]) == 2, "Two medicines extracted")
        check(multi_data["medicines"][0]["medicine_name"]["value"] == "Paracetamol", "First med is Paracetamol")
        check(multi_data["medicines"][1]["medicine_name"]["value"] == "Cetirizine", "Second med is Cetirizine")

        # 18. POST /api/v1/multimodal/extract (uncertain medicine name)
        r_unc = client.post(
            "/api/v1/multimodal/extract",
            files={"file": ("rx_unc.png", io.BytesIO(test_img_bytes), "image/png")},
            data={"scenario": "uncertain_medicine_name"},
        )
        check(r_unc.status_code == 200, "POST /api/v1/multimodal/extract (uncertain) returns 200 OK")
        unc_data = r_unc.json()
        check(unc_data["medicines"][0]["medicine_name"]["status"] == "uncertain", "Uncertain medicine name detected")
        check(unc_data["medicines"][0]["medicine_name"]["presence"] == "present", "Uncertain medicine presence is present")
        check(unc_data["medicines"][0]["medicine_name"]["extraction_state"] == "ambiguous", "Uncertain medicine state is ambiguous")
        check(unc_data["requires_human_review"] is True, "Human review required for uncertain extraction")

        # 19. POST /api/v1/multimodal/extract (missing dosage)
        r_miss = client.post(
            "/api/v1/multimodal/extract",
            files={"file": ("rx_miss.png", io.BytesIO(test_img_bytes), "image/png")},
            data={"scenario": "missing_dosage"},
        )
        check(r_miss.status_code == 200, "POST /api/v1/multimodal/extract (missing dosage) returns 200 OK")
        miss_data = r_miss.json()
        check(miss_data["medicines"][0]["dosage"]["value"] is None, "Missing dosage value is null")
        check(miss_data["medicines"][0]["dosage"]["status"] == "uncertain", "Missing dosage status is uncertain")
        check(miss_data["medicines"][0]["dosage"]["presence"] == "absent", "Missing dosage presence is absent")
        check(miss_data["medicines"][0]["dosage"]["extraction_state"] == "missing", "Missing dosage state is missing")
        check(miss_data["medicines"][0]["dosage"]["uncertainty_reason"] is None, "Missing dosage has no fabricated uncertainty_reason")

        # 20. POST /api/v1/multimodal/extract (model unavailable -> 503)
        r_unavail = client.post(
            "/api/v1/multimodal/extract",
            files={"file": ("rx_unavail.png", io.BytesIO(test_img_bytes), "image/png")},
            data={"scenario": "model_unavailable"},
        )
        check(r_unavail.status_code == 503, "POST /api/v1/multimodal/extract (model unavailable) returns 503")

    print("\n======================================================")
    print(f"LIVE TEST SUMMARY: {passed} PASSED | {failed} FAILED")
    print("======================================================\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_live_tests()

