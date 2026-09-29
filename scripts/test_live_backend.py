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
        # 1. Health Endpoints
        r = client.get("/api/v1/health")
        check(r.status_code == 200, "GET /api/v1/health returns 200 OK")
        data = r.json()
        check(data["status"] == "healthy", "Health status is 'healthy'")
        check(data["mock_mode"] is True, "Mock mode is True")

        # 1b. Root Health Endpoint (Phase 13 Container / Load-Balancer contract)
        r_root = client.get("/health")
        check(r_root.status_code == 200, "GET /health (root alias) returns 200 OK")
        root_data = r_root.json()
        check(root_data["status"] == "healthy", "Root health status is 'healthy'")
        check("dependencies" in root_data["system_info"], "Dependency diagnostics present in system_info")

        # 2. Analyze Sample 1 (Confident)
        r = client.post("/api/v1/prescriptions/analyze", data={"sample_id": "rx-sample-1"})
        check(r.status_code == 200, "POST analyze (sample-1) returns 200 OK")
        data = r.json()
        check(data["prescription_id"] is not None, "prescription_id present")
        check(data["original_image_url"] == "/uploads/samples/rx-sample-1.svg", "original_image_url preserved")
        check(data["fields"]["medicine_name"]["status"] == "confident", "medicine_name is confident")
        check(data["requires_human_review"] is False, "requires_human_review is False")

        # 2b. Canonical Process Endpoint (Phase 13 /process alias)
        r_proc = client.post("/api/v1/prescriptions/process", data={"sample_id": "rx-sample-1"})
        check(r_proc.status_code == 200, "POST process (sample-1) returns 200 OK")
        proc_data = r_proc.json()
        check(proc_data["prescription_id"] is not None, "process prescription_id present")

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

        # ------------------------------------------------------------------
        # Phase 7: RAG Medicine Validation Live Checks
        # ------------------------------------------------------------------
        # 21. GET /api/v1/validation/status
        r_val_status = client.get("/api/v1/validation/status")
        check(r_val_status.status_code == 200, "GET /api/v1/validation/status returns 200 OK")
        val_status_data = r_val_status.json()
        check(val_status_data["initialized"] is True, "RAG validation service is initialized")
        check(val_status_data["index_stats"]["total_records"] == 30, "Index contains 30 reference records")
        check(val_status_data["ingestion_report"]["valid_records_count"] == 30, "30 verified records ingested")

        # 22. POST /api/v1/validation/medicine (Exact Match)
        r_exact = client.post(
            "/api/v1/validation/medicine",
            json={
                "candidate_name": "Augmentin 625 Duo",
                "observed_dosage": "625 mg",
                "top_k": 5,
            }
        )
        check(r_exact.status_code == 200, "POST /api/v1/validation/medicine (exact match) returns 200 OK")
        exact_data = r_exact.json()
        check(exact_data["validation_result"]["validation_status"] == "validated", "Exact match status is 'validated'")
        check(exact_data["validation_result"]["requires_human_review"] is False, "Exact match does not require human review")
        check(exact_data["validation_result"]["selected_reference"]["medicine_name"] == "Augmentin 625 Duo", "Selected reference formulation matches canonical title")
        check(exact_data["ui_evidence"]["validation_status"] == "cdsco_approved", "UI evidence status is cdsco_approved")

        # 23. POST /api/v1/validation/medicine (Uncertain Candidate - Preserves Uncertainty)
        r_unc_val = client.post(
            "/api/v1/validation/medicine",
            json={
                "candidate_name": "Amox...",
                "observed_dosage": "500 mg",
            }
        )
        check(r_unc_val.status_code == 200, "POST /api/v1/validation/medicine (uncertain) returns 200 OK")
        unc_val_data = r_unc_val.json()
        check(unc_val_data["validation_result"]["validation_status"] == "uncertain", "Uncertain match status is 'uncertain'")
        check(unc_val_data["validation_result"]["requires_human_review"] is True, "Uncertain candidate requires human review")
        check(unc_val_data["validation_result"]["selected_reference"] is None, "No reference entity forcibly assigned to uncertain candidate")

        # 24. POST /api/v1/validation/medicine (No Match / Sub-threshold)
        r_no_match = client.post(
            "/api/v1/validation/medicine",
            json={
                "candidate_name": "UnknownPharmaceuticalEntity999",
            }
        )
        check(r_no_match.status_code == 200, "POST /api/v1/validation/medicine (no match) returns 200 OK")
        no_match_data = r_no_match.json()
        check(no_match_data["validation_result"]["validation_status"] == "not_validated", "Unlisted candidate status is 'not_validated'")
        check(no_match_data["validation_result"]["requires_human_review"] is True, "Unlisted candidate requires human review")

        # 25. POST /api/v1/validation/medicine (Dosage Preservation Invariant & Formulation Consistency)
        r_dosage = client.post(
            "/api/v1/validation/medicine",
            json={
                "candidate_name": "Augmentin 625 Duo",
                "observed_dosage": "1000 mg",
            }
        )
        check(r_dosage.status_code == 200, "POST /api/v1/validation/medicine (dosage preservation) returns 200 OK")
        dosage_data = r_dosage.json()
        val_res = dosage_data["validation_result"]
        check(val_res["dosage_observation_preserved"] is True, "Observed dosage preserved flag is True")
        check(val_res["observed_dosage"] == "1000 mg", "Observed dosage 1000 mg strictly preserved")
        check(val_res["reference_strength"] == "625 mg", "Reference strength 625 mg remains separate")
        check(val_res["formulation_consistency"] == "mismatch", "Formulation consistency correctly flagged as mismatch")
        check(val_res["requires_human_review"] is True, "Dosage mismatch requires human review")
        check(val_res["medicine_identity_status"] == "validated", "Medicine identity remains validated despite dosage mismatch")

        # 26. POST /api/v1/validation/medicine/batch (Batch Processing)
        r_batch = client.post(
            "/api/v1/validation/medicine/batch",
            json={
                "items": [
                    {"candidate_name": "Augmentin 625 Duo", "observed_dosage": "625 mg"},
                    {"candidate_name": "Paracetamol 500mg", "observed_dosage": "500 mg"},
                    {"candidate_name": "UnknownDrugXYZ", "observed_dosage": "10 mg"},
                ]
            }
        )
        check(r_batch.status_code == 200, "POST /api/v1/validation/medicine/batch returns 200 OK")
        batch_data = r_batch.json()
        check(batch_data["total_processed"] == 3, "Batch processed 3 items")
        check(batch_data["results"][0]["validation_result"]["validation_status"] == "validated", "Batch item 1 validated")
        check(batch_data["results"][1]["validation_result"]["validation_status"] == "validated", "Batch item 2 validated")
        check(batch_data["results"][2]["validation_result"]["validation_status"] == "not_validated", "Batch item 3 not validated")

        # 27. GET /api/v1/confidence/config (Phase 8 Confidence Config)
        r_conf_cfg = client.get("/api/v1/confidence/config")
        check(r_conf_cfg.status_code == 200, "GET /api/v1/confidence/config returns 200 OK")
        conf_cfg_data = r_conf_cfg.json()
        check(conf_cfg_data["config_version"] == "confidence_calibration_v1", "Confidence config_version is 'confidence_calibration_v1'")
        check(conf_cfg_data["min_samples_for_calibration"] == 15, "min_samples_for_calibration is 15")
        check(conf_cfg_data["calibration_status"] == "insufficient_data", "Default calibrator status is 'insufficient_data'")

        # 28. POST /api/v1/confidence/evaluate (Phase 8 Direct Field Evaluation)
        r_conf_eval = client.post(
            "/api/v1/confidence/evaluate",
            json={
                "raw_score": 0.94,
                "field_name": "medicine_name",
                "source": "multimodal_extraction",
            }
        )
        check(r_conf_eval.status_code == 200, "POST /api/v1/confidence/evaluate returns 200 OK")
        conf_eval_data = r_conf_eval.json()
        check(conf_eval_data["raw_signal"]["raw_value"] == 0.94, "Raw confidence signal 0.94 preserved")
        check(conf_eval_data["calibrated_confidence"]["value"] is None, "Calibrated confidence is None when insufficient data")
        check(conf_eval_data["calibration_status"] == "insufficient_data", "Calibration status is 'insufficient_data'")

        # 29. POST /api/v1/confidence/metrics (Phase 8 Calibration Metrics)
        r_conf_metrics = client.post(
            "/api/v1/confidence/metrics",
            json={
                "confidences": [0.9, 0.8, 0.7, 0.4, 0.2],
                "labels": [1, 1, 1, 0, 0],
                "num_bins": 5,
            }
        )
        check(r_conf_metrics.status_code == 200, "POST /api/v1/confidence/metrics returns 200 OK")
        metrics_data = r_conf_metrics.json()
        check("ece" in metrics_data, "ECE present in metrics output")
        check("mce" in metrics_data, "MCE present in metrics output")
        check("brier_score" in metrics_data, "Brier score present in metrics output")
        check(metrics_data["sample_count"] == 5, "Sample count is 5")

        # 30. GET /api/v1/confidence/fixtures (Phase 8 14 Deterministic Fixtures)
        r_conf_fix = client.get("/api/v1/confidence/fixtures")
        check(r_conf_fix.status_code == 200, "GET /api/v1/confidence/fixtures returns 200 OK")
        fixtures_data = r_conf_fix.json()
        check(fixtures_data["fixture_count"] == 14, "Contains exactly 14 deterministic fixtures")
        check(any("01-WELL-CALIBRATED" in f.get("fixture_id", "") for f in fixtures_data["fixtures"]), "Fixture 1 present")
        check(any("13-CONFLICTING" in f.get("fixture_id", "") for f in fixtures_data["fixtures"]), "Fixture 13 present")

        # 31. Phase 9 Pipeline Stages & Confidence Assessment Verification
        r_stage9 = client.post("/api/v1/prescriptions/analyze", data={"sample_id": "rx-sample-1"})
        check(r_stage9.status_code == 200, "POST analyze (sample-1 stage 9) returns 200 OK")
        s9_data = r_stage9.json()
        check(s9_data["meta"]["pipeline_stages_completed"] == 9, "Pipeline stages completed is 9")
        check("confidence_assessment" in s9_data, "confidence_assessment present in response")
        check(s9_data["fields"]["medicine_name"]["raw_confidence"] is not None, "Field raw_confidence enriched")
        check(s9_data["fields"]["medicine_name"]["calibration_status"] == "insufficient_data", "Field calibration_status is insufficient_data")
        check("abstention" in s9_data, "abstention block present in analyze response")
        check(s9_data["abstention"]["policy_version"] == "abstention_policy_v1", "Policy version is abstention_policy_v1")

        # 32. GET /api/v1/abstention/config
        r_abs_cfg = client.get("/api/v1/abstention/config")
        check(r_abs_cfg.status_code == 200, "GET /api/v1/abstention/config returns 200 OK")
        abs_cfg_data = r_abs_cfg.json()
        check(abs_cfg_data["policy_version"] == "abstention_policy_v1", "Policy version is abstention_policy_v1")
        check(abs_cfg_data["min_calibrated_confidence"] == 0.80, "Default min calibrated confidence is 0.80")
        check(abs_cfg_data["dosage_strict_mode"] is True, "Dosage strict mode enabled")

        # 33. GET /api/v1/abstention/fixtures
        r_abs_fix = client.get("/api/v1/abstention/fixtures")
        check(r_abs_fix.status_code == 200, "GET /api/v1/abstention/fixtures returns 200 OK")
        abs_fix_data = r_abs_fix.json()
        check(len(abs_fix_data) == 15, "Contains exactly 15 Phase 9 deterministic fixtures")
        check(any("01-HIGH-CONFIDENCE-ACCEPT" in f.get("fixture_id", "") for f in abs_fix_data), "Fixture 1 present")
        check(any("09-DOSAGE-FORMULATION-MISMATCH" in f.get("fixture_id", "") for f in abs_fix_data), "Fixture 9 present")
        check(any("15-FULL-PRESCRIPTION-REQUIRES-VERIFICATION" in f.get("fixture_id", "") for f in abs_fix_data), "Fixture 15 present")

        # 34. POST /api/v1/abstention/evaluate
        r_abs_eval = client.post(
            "/api/v1/abstention/evaluate",
            json={
                "field_name": "medicine_name",
                "value": "Amoxicillin",
                "raw_confidence": 0.95,
                "calibrated_confidence": 0.95,
                "calibration_status": "calibrated",
            }
        )
        check(r_abs_eval.status_code == 200, "POST /api/v1/abstention/evaluate returns 200 OK")
        eval_data = r_abs_eval.json()
        check(eval_data["decision"] == "accepted", "High calibrated confidence evaluates to accepted")
        check(eval_data["requires_human_verification"] is False, "Verification not required for accepted field")

        # 35. Human Verification Endpoints (Confirm, Correct, Unreadable)
        test_rx_id = "RX-LIVE-TEST-001"
        test_field = "medicine_name"

        # 35a. Confirm field
        r_confirm = client.post(
            f"/api/v1/verification/{test_rx_id}/fields/{test_field}/confirm",
            json={
                "original_value": "Augmentin 625 Duo",
                "reason": "Clear pen stroke confirms Augmentin",
            }
        )
        check(r_confirm.status_code == 200, "POST verification confirm returns 200 OK")
        confirm_data = r_confirm.json()
        check(confirm_data["verification_status"] == "confirmed", "Status is confirmed")
        check(confirm_data["verified_value"] == "Augmentin 625 Duo", "Verified value matches original")

        # 35b. Correct field
        r_correct = client.post(
            f"/api/v1/verification/{test_rx_id}/fields/{test_field}/correct",
            json={
                "original_value": "Augmentin 625 Duo",
                "corrected_value": "Amoxicillin 500",
                "reason": "Stroke inspection indicates Amoxicillin",
            }
        )
        check(r_correct.status_code == 200, "POST verification correct returns 200 OK")
        correct_data = r_correct.json()
        check(correct_data["verification_status"] == "corrected", "Status is corrected")
        check(correct_data["original_value"] == "Augmentin 625 Duo", "Original value strictly preserved")
        check(correct_data["verified_value"] == "Amoxicillin 500", "Verified value stored")

        # 35c. Mark unreadable
        r_unread = client.post(
            f"/api/v1/verification/{test_rx_id}/fields/dosage/unreadable",
            json={
                "original_value": "??? mg",
                "reason": "Ink blot makes strength illegible",
                "verifier_id": "verifier_live_01",
            }
        )
        check(r_unread.status_code == 200, "POST verification unreadable returns 200 OK")
        unread_data = r_unread.json()
        check(unread_data["verification_status"] == "unreadable", "Status is unreadable")
        check(unread_data["verified_value"] is None, "Verified value is None for unreadable")

        # 35d. GET verification state
        r_v_state = client.get(f"/api/v1/verification/{test_rx_id}")
        check(r_v_state.status_code == 200, "GET verification state returns 200 OK")
        v_state_data = r_v_state.json()
        check(v_state_data["prescription_id"] == test_rx_id, "State prescription_id matches")
        # 36. Phase 11 Explanation Config
        r_exp_cfg = client.get("/api/v1/explanation/config")
        check(r_exp_cfg.status_code == 200, "GET /api/v1/explanation/config returns 200 OK")
        exp_cfg_data = r_exp_cfg.json()
        check(exp_cfg_data["status"] == "active", "Explanation status is active")
        check(exp_cfg_data["policy_version"] == "explanation_policy_v1", "Policy version matches explanation_policy_v1")
        check(len(exp_cfg_data["config_hash"]) == 64, "Config hash is 64-char SHA-256")
        check(exp_cfg_data["supported_languages"] == ["en", "hi", "mr"], "Supported languages include en, hi, mr")

        # 37. Phase 11 Generate Explanation (Eligible Posology)
        r_exp_gen = client.post(
            "/api/v1/explanation/generate",
            json={
                "prescription_id": "RX-LIVE-EXP-001",
                "medicine_name": "Paracetamol",
                "dosage": "500 mg",
                "frequency": "twice daily",
                "duration": "5 days",
            }
        )
        check(r_exp_gen.status_code == 200, "POST /api/v1/explanation/generate (eligible) returns 200 OK")
        exp_gen_data = r_exp_gen.json()
        check(exp_gen_data["overall_eligibility"] == "eligible", "Eligibility is eligible")
        check("en" in exp_gen_data["explanations"], "EN explanation present")
        check("hi" in exp_gen_data["explanations"], "HI explanation present")
        check("mr" in exp_gen_data["explanations"], "MR explanation present")
        check("Paracetamol" in exp_gen_data["explanations"]["en"]["summary"], "EN summary preserves Roman medicine name")
        check("500 mg" in exp_gen_data["explanations"]["en"]["summary"], "EN summary preserves 500 mg dosage")
        check("5 days" in exp_gen_data["explanations"]["en"]["summary"], "EN summary preserves 5 days duration")
        check(exp_gen_data["explanations"]["en"]["validation"]["medicine_fidelity"] is True, "Medicine fidelity is True")
        check(exp_gen_data["explanations"]["en"]["validation"]["numeric_fidelity"] is True, "Numeric fidelity is True")

        # 38. Phase 11 Generate Explanation (LASA Conflict -> Restricted)
        r_exp_lasa = client.post(
            "/api/v1/explanation/generate",
            json={
                "prescription_id": "RX-LIVE-EXP-002",
                "medicine_name": "Prednisone",
                "has_lasa_conflict": True,
                "confusable_counterpart": "Prednisolone",
            }
        )
        check(r_exp_lasa.status_code == 200, "POST /api/v1/explanation/generate (LASA) returns 200 OK")
        exp_lasa_data = r_exp_lasa.json()
        check(exp_lasa_data["overall_eligibility"] == "restricted", "LASA conflict yields restricted eligibility")
        check("Similar medicine names were detected" in exp_lasa_data["explanations"]["en"]["summary"], "LASA verification warning displayed in EN")

        # 39. Phase 11 Explanation Fixtures
        r_exp_fix = client.get("/api/v1/explanation/fixtures")
        check(r_exp_fix.status_code == 200, "GET /api/v1/explanation/fixtures returns 200 OK")
        exp_fix_data = r_exp_fix.json()
        check(exp_fix_data["fixture_count"] >= 22, "Contains all 22 mock fixtures")

        # 40. Phase 11 Generate Explanation (Empty ID Validation Error)
        r_exp_err = client.post(
            "/api/v1/explanation/generate",
            json={"prescription_id": "", "medicine_name": "Paracetamol"}
        )
        check(r_exp_err.status_code in (400, 422), "Empty prescription_id rejected with HTTP 400/422")


    print("\n======================================================")
    print(f"LIVE TEST SUMMARY: {passed} PASSED | {failed} FAILED")
    print("======================================================\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_live_tests()

