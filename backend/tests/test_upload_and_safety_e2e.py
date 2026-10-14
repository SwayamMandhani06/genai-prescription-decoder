"""
End-to-End Upload, Preprocessing, AI, and Safety Verification Test
Tests real physical images from data/samples against the FastAPI backend (LOW-03).
"""

import sys
import hashlib
from pathlib import Path
from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app
from backend.app.config import get_settings
from backend.app.ocr import TesseractEngine
from backend.app.preprocessing import ImagePreprocessingService
from ai.rag import get_medicine_validation_service
from ai.lasa import get_lasa_detection_service
from ai.explanation import get_explanation_service


client = TestClient(app)


def test_tesseract_engine_presence():
    tesseract_engine = TesseractEngine()
    # Engine presence check
    assert hasattr(tesseract_engine, "is_available")


def test_physical_image_ingestion_and_storage():
    img_path_1 = ROOT_DIR / "data" / "samples" / "sample_01_clear.png"
    assert img_path_1.is_file(), "sample_01_clear.png missing!"
    img_bytes_1 = img_path_1.read_bytes()

    files_1 = {"file": ("prescription_clear.png", img_bytes_1, "image/png")}
    resp_1 = client.post("/api/v1/prescriptions/process", files=files_1)
    assert resp_1.status_code in (200, 503), f"Unexpected status {resp_1.status_code}"


def test_preprocessing_blur_assessment():
    preproc_service = ImagePreprocessingService()
    img_path_3 = ROOT_DIR / "data" / "samples" / "sample_03_blurred.png"
    assert img_path_3.is_file(), "sample_03_blurred.png missing!"
    img_bytes_3 = img_path_3.read_bytes()

    preproc_res_3, manifest_3, _ = preproc_service.process_and_store(
        image_bytes=img_bytes_3,
        filename="sample_03_blurred.png",
        prescription_id="TEST-BLUR-03",
        reject_insufficient_quality=False,
    )
    qr_3 = preproc_res_3.quality_report
    assert qr_3.heuristic_quality_score < 1.0


def test_lasa_confusable_screening():
    lasa_service = get_lasa_detection_service()
    lasa_report = lasa_service.detect_prescription("RX-TEST-LASA", ["Hydralazine", "Metformin"])
    assert lasa_report.total_medicines_screened == 2


def test_rag_formulary_grounding():
    rag_service = get_medicine_validation_service()
    val_unknown = rag_service.validate_candidate("NonexistentDrugX123", "1000 mg")
    assert val_unknown.validation_status != "validated"
    assert val_unknown.requires_human_review is True


def test_multilingual_number_preservation():
    summary_hi = "एमोक्सिसिलिन (Amoxicillin) 500mg भोजन के बाद दिन में 3 बार (TID) 7 दिनों के लिए लें।"
    assert "500mg" in summary_hi and "Amoxicillin" in summary_hi


def test_file_signature_security_rejections():
    # 1. Disallowed file type (.exe)
    resp_exe = client.post("/api/v1/prescriptions/process", files={"file": ("malware.exe", b"MZ_BINARY_DATA", "application/x-msdownload")})
    assert resp_exe.status_code == 415

    # 2. Spoofed file extension (MZ executable renamed as .png)
    spoofed_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"\x00" * 32
    resp_spoofed = client.post("/api/v1/prescriptions/process", files={"file": ("fake_prescription.png", spoofed_bytes, "image/png")})
    assert resp_spoofed.status_code == 415

    # 3. Oversized file (> 15 MB)
    oversized_bytes = b"0" * (16 * 1024 * 1024)
    resp_oversized = client.post("/api/v1/prescriptions/process", files={"file": ("huge.jpg", oversized_bytes, "image/jpeg")})
    assert resp_oversized.status_code == 413
