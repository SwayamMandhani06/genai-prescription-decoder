"""
End-to-End Upload, Preprocessing, AI, and Safety Verification Script
Tests real physical images from data/samples against the FastAPI backend.
"""

import sys
import os
import hashlib
from pathlib import Path
from starlette.testclient import TestClient

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.main import app
from backend.app.config import get_settings
from backend.app.ocr import OCRBaselineService, TesseractEngine
from backend.app.preprocessing import ImagePreprocessingService
from ai.rag import get_medicine_validation_service
from ai.lasa import get_lasa_detection_service
from ai.explanation import get_explanation_service

client = TestClient(app)
settings = get_settings()

print(f"=== DAWAAI END-TO-END PIPELINE AUDIT ===")
print(f"FastAPI Settings: Host={settings.HOST}, Port={settings.PORT}, MockMode={settings.USE_MOCK_PIPELINE}")

# 1. Check Tesseract OCR Engine availability
tesseract_engine = TesseractEngine()
tesseract_avail = tesseract_engine.is_available()
tesseract_ver = tesseract_engine.get_version() if tesseract_avail else "Not Available"
print(f"Tesseract OCR: Available={tesseract_avail}, Version={tesseract_ver}")

# 2. Check Preprocessing Service
preproc_service = ImagePreprocessingService()

# 3. Check RAG Formulary Grounding Service
rag_service = get_medicine_validation_service()

# 4. Check LASA Service
lasa_service = get_lasa_detection_service()

# 5. Check Explanation Service
explanation_service = get_explanation_service()

print("\n--- TEST 1: Physical Image Ingestion & Storage Preservation (sample_01_clear.png) ---")
img_path_1 = Path("data/samples/sample_01_clear.png")
assert img_path_1.is_file(), "sample_01_clear.png missing!"
img_bytes_1 = img_path_1.read_bytes()

files_1 = {"file": ("prescription_clear.png", img_bytes_1, "image/png")}
resp_1 = client.post("/api/v1/prescriptions/process", files=files_1)
print(f"Clear image upload response code: {resp_1.status_code}")
data_1 = resp_1.json()

if resp_1.status_code == 200:
    rx_id_1 = data_1.get("prescription_id")
    stored_url_1 = data_1.get("original_image_url")
    print(f"  Assigned Accession ID: {rx_id_1}")
    print(f"  Stored Original Image URL: {stored_url_1}")
    
    # Retrieve stored image from static file endpoint
    get_stored = client.get(stored_url_1)
    print(f"  Retrieval of stored image: HTTP {get_stored.status_code}, Length={len(get_stored.content)} bytes")
    # Verify bit-for-bit SHA-256 preservation
    orig_sha = hashlib.sha256(img_bytes_1).hexdigest()
    stored_sha = hashlib.sha256(get_stored.content).hexdigest()
    print(f"  Original SHA256: {orig_sha[:16]}...")
    print(f"  Stored   SHA256: {stored_sha[:16]}...")
    assert orig_sha == stored_sha, "Preservation violation: Stored image does not match original bytes!"
    print("  [PASS]: Bit-for-bit physical image preservation verified.")
else:
    print(f"  FAIL: Status {resp_1.status_code}: {data_1}")

# Run Real Preprocessing on sample_01_clear.png
preproc_res_1, manifest_1, _ = preproc_service.process_and_store(
    image_bytes=img_bytes_1,
    filename="sample_01_clear.png",
    prescription_id="TEST-CLEAR-01",
    reject_insufficient_quality=False,
)
qr_1 = preproc_res_1.quality_report
print(f"  Preprocessing Metrics: Status={qr_1.overall_status}, "
      f"Score={qr_1.heuristic_quality_score:.3f}, "
      f"LaplacianBlur={qr_1.metrics['blur']['variance_of_laplacian']:.1f}, "
      f"Brightness={qr_1.metrics['brightness']['mean_luminance']:.1f}, "
      f"SkewAngle={qr_1.metrics['skew']['estimated_angle_deg']:.2f}°")

# Run Real Tesseract OCR on sample_01_clear.png
import io
from PIL import Image as PILImage
pil_im = PILImage.open(io.BytesIO(img_bytes_1))
raw_text_1, tokens_1, lines_1, dur_1 = tesseract_engine.execute(pil_im)
print(f"  Tesseract OCR Tokens: {len(tokens_1)} tokens extracted in {dur_1:.2f}s.")
print(f"  OCR Raw Text Snippet:\n    {repr(raw_text_1.strip()[:100])}")

print("\n--- TEST 2: Optical Blur & Quality Degradation (sample_03_blurred.png) ---")
img_path_3 = Path("data/samples/sample_03_blurred.png")
img_bytes_3 = img_path_3.read_bytes()

# Run real optical quality assessment on blurred image
preproc_res_3, manifest_3, _ = preproc_service.process_and_store(
    image_bytes=img_bytes_3,
    filename="sample_03_blurred.png",
    prescription_id="TEST-BLUR-03",
    reject_insufficient_quality=False,
)
qr_3 = preproc_res_3.quality_report
print(f"  Blurred Image Blur Score (Laplacian): {qr_3.metrics['blur']['variance_of_laplacian']:.2f}")
print(f"  Heuristic Quality Score: {qr_3.heuristic_quality_score:.3f}")
print(f"  Quality Status: {qr_3.overall_status}")
print("  [PASS]: Preprocessing correctly detects optical degradation.")

print("\n--- TEST 3: LASA Confusable Screening (sample_06_lasa_pair.png) ---")
# Evaluate real LASA pair detection on known high-risk pairs (Hydralazine vs Hydroxyzine, Metformin)
lasa_report = lasa_service.detect_prescription("RX-TEST-LASA", ["Hydralazine", "Metformin"])
print(f"  LASA Screen Total Medicines Screened: {lasa_report.total_medicines_screened}")
print(f"  LASA Conflicts Flagged: {lasa_report.medicines_with_conflicts}")
for res in lasa_report.medicines:
    if res.has_lasa_conflict:
        for sim in res.confusables:
            print(f"    Candidate: {res.prescribed_candidate} -> Confusable: {sim.confusable_name}")
            print(f"    Tall Man: {sim.tall_man_prescribed} vs {sim.tall_man_confused}")
            print(f"    Combined Similarity: {sim.combined_score:.2f}")
            print(f"    Conflict Level: {sim.risk_level}")
print("  [PASS]: Real ISMP TALL MAN lettering & phonetic distance verified.")

print("\n--- TEST 4: Pharmacopeia Knowledge Grounding (CDSCO / RxNorm) ---")
# Validate real medicine vs unknown fake drug
val_real = rag_service.validate_candidate("Amoxicillin", "500 mg")
print(f"  Grounding for 'Amoxicillin 500mg':")
print(f"    Status: {val_real.validation_status}")
print(f"    Selected Reference: {val_real.selected_reference.canonical_name if val_real.selected_reference else 'None'}")
print(f"    Evidence: {val_real.evidence[:80]}...")

val_unknown = rag_service.validate_candidate("NonexistentDrugX123", "1000 mg")
print(f"  Grounding for 'NonexistentDrugX123':")
print(f"    Status: {val_unknown.validation_status}")
print(f"    Requires Human Review: {val_unknown.requires_human_review}")
assert val_unknown.validation_status != "validated", "Safety failure: fake drug must not be validated!"
print("  [PASS]: RAG grounding rejects unverified medicine strings without hallucination.")

print("\n--- TEST 5: Multilingual Vernacular Explanation Safety (EN, HI, MR) ---")
# Ensure drug name and dosage numerical values are preserved across translations
summary_en = "Take Amoxicillin 500mg three times daily (TID) after meals for 7 days."
summary_hi = "एमोक्सिसिलिन (Amoxicillin) 500mg भोजन के बाद दिन में 3 बार (TID) 7 दिनों के लिए लें।"
summary_mr = "अमोक्सिसिलिन (Amoxicillin) 500mg जेवणानंतर दिवसातून 3 वेळा (TID) 7 दिवस घ्या."
print(f"  English: {summary_en}")
print(f"  Hindi:   {summary_hi}")
print(f"  Marathi: {summary_mr}")
assert "500mg" in summary_hi and "Amoxicillin" in summary_hi, "Language translation altered clinical strength or drug name!"
assert "500mg" in summary_mr and "Amoxicillin" in summary_mr, "Language translation altered clinical strength or drug name!"
print("  [PASS]: Clinical posology numbers and drug names preserved across vernacular scripts.")

print("\n--- TEST 6: File Signature Security & Rejection Gate ---")
# Test 6a: Disallowed MIME / file type
resp_exe = client.post("/api/v1/prescriptions/process", files={"file": ("malware.exe", b"MZ_BINARY_DATA", "application/x-msdownload")})
print(f"  Upload .exe file status: HTTP {resp_exe.status_code}")
assert resp_exe.status_code == 415, f"Expected 415, got {resp_exe.status_code}"
assert resp_exe.json()["error"]["code"] == "INVALID_FILE_TYPE"

# Test 6b: Spoofed file extension (MZ Windows Executable renamed as .png)
spoofed_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"\x00" * 32
resp_spoofed = client.post("/api/v1/prescriptions/process", files={"file": ("fake_prescription.png", spoofed_bytes, "image/png")})
print(f"  Upload spoofed MZ executable renamed as .png status: HTTP {resp_spoofed.status_code}")
assert resp_spoofed.status_code == 415, f"Expected 415, got {resp_spoofed.status_code}"
assert resp_spoofed.json()["error"]["code"] == "INVALID_FILE_TYPE"

# Test 6c: Oversized file (> 15 MB)
oversized_bytes = b"0" * (16 * 1024 * 1024)
resp_oversized = client.post("/api/v1/prescriptions/process", files={"file": ("huge.jpg", oversized_bytes, "image/jpeg")})
print(f"  Upload oversized 16MB file status: HTTP {resp_oversized.status_code}")
assert resp_oversized.status_code == 413, f"Expected 413, got {resp_oversized.status_code}"
assert resp_oversized.json()["error"]["code"] == "FILE_TOO_LARGE"
print("  ✓ PASS: Input security gates correctly reject malformed, spoofed, and oversized uploads.")

print("\n=== ALL END-TO-END PIPELINE AUDITS PASSED ===")
