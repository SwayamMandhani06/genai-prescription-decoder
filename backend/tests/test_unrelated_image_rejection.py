"""
Regression Test Suite: Unrelated Image Rejection, Reliability & Safety Audit
Tests the complete input-validation, document-type assessment, and abstention pipeline
to verify that unrelated images (landscapes, selfies, receipts, packaging, blank pages, etc.)
are rejected and never produce hallucinated prescription findings.
"""

import io
import json
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from backend.app.schemas.error import ErrorCode
from backend.app.preprocessing.validator import ImageIngestionValidator, ImageValidationError
from ai.abstention.policy import evaluate_prescription_abstention
from backend.app.multimodal.schemas import PrescriptionExtractionResult, ModelMetadata


def create_solid_image_bytes(color: tuple, size: tuple = (400, 400), fmt: str = "PNG") -> bytes:
    """Creates synthetic solid image bytes (e.g. blank white page)."""
    im = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    im.save(buf, format=fmt)
    return buf.getvalue()


def create_text_document_image(text: str = "Sample Document") -> bytes:
    """Creates a basic rendered image with text strokes for testing."""
    im = Image.new("RGB", (400, 500), color=(250, 250, 250))
    draw = ImageDraw.Draw(im)
    draw.text((20, 20), text, fill=(10, 10, 10))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


# ==============================================================================
# 1. Image Content Pre-Flight & Blank Page Validation
# ==============================================================================

def test_preflight_rejects_blank_white_page():
    """Verify ImageIngestionValidator detects and rejects completely blank white page."""
    blank_bytes = create_solid_image_bytes(color=(255, 255, 255))
    validator = ImageIngestionValidator()

    with pytest.raises(ImageValidationError) as exc_info:
        validator.validate_and_load(blank_bytes, filename="blank_page.png", reject_blank=True)

    assert exc_info.value.code == ErrorCode.IMAGE_QUALITY_INSUFFICIENT
    assert exc_info.value.status_code == 422
    assert "blank or devoid of handwritten ink strokes" in exc_info.value.message.lower()


def test_preflight_rejects_solid_black_page():
    """Verify ImageIngestionValidator detects and rejects solid black non-content image."""
    black_bytes = create_solid_image_bytes(color=(0, 0, 0))
    validator = ImageIngestionValidator()

    with pytest.raises(ImageValidationError) as exc_info:
        validator.validate_and_load(black_bytes, filename="black_page.png", reject_blank=True)

    assert exc_info.value.code == ErrorCode.IMAGE_QUALITY_INSUFFICIENT
    assert exc_info.value.status_code == 422


def test_preflight_accepts_valid_image_with_strokes(sample_prescription_image):
    """Verify ImageIngestionValidator successfully loads image with sufficient variation and strokes."""
    validator = ImageIngestionValidator()
    img, meta = validator.validate_and_load(sample_prescription_image, filename="valid_rx.png")
    assert img.mode == "RGB"
    assert meta.width >= 150
    assert meta.height >= 150


# ==============================================================================
# 2. Document-Type Assessment & Rejection Endpoints
# ==============================================================================

def test_reject_landscape_photograph(client: TestClient, sample_prescription_image):
    """Uploading a landscape photo must be rejected with 422 and actionable reason."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("landscape.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "landscape"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == ErrorCode.VALIDATION_FAILED.value
    assert data["error"]["stage"] == "document_type_assessment"
    assert "landscape photograph" in data["error"]["message"].lower()
    assert data["error"]["details"]["document_type"] == "unrelated_image"


def test_reject_selfie_or_portrait(client: TestClient, sample_prescription_image):
    """Uploading a selfie/portrait must be rejected with 422 and actionable reason."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("selfie.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "selfie"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == ErrorCode.VALIDATION_FAILED.value
    assert "selfie or portrait" in data["error"]["message"].lower()
    assert data["error"]["details"]["document_type"] == "unrelated_image"


def test_reject_food_or_animal_photo(client: TestClient, sample_prescription_image):
    """Uploading a food/animal photo must be rejected with 422 and actionable reason."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("pet_food.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "food_animal"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == ErrorCode.VALIDATION_FAILED.value
    assert "food or animal" in data["error"]["message"].lower()


def test_reject_shopping_payment_receipt(client: TestClient, sample_prescription_image):
    """Uploading a shopping receipt must be rejected with 422 and not hallucinate medicines."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("store_receipt.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "receipt"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == ErrorCode.VALIDATION_FAILED.value
    assert "receipt" in data["error"]["message"].lower()
    assert data["error"]["details"]["document_type"] == "receipt"


def test_reject_medicine_packaging_without_prescription(client: TestClient, sample_prescription_image):
    """Commercial packaging/box alone must not be accepted as an authorized doctor prescription."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("medicine_box.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "packaging_only"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == ErrorCode.VALIDATION_FAILED.value
    assert "commercial medicine packaging" in data["error"]["message"].lower()
    assert data["error"]["details"]["document_type"] == "packaging_only"


def test_reject_medical_literature_or_textbook(client: TestClient, sample_prescription_image):
    """Printed medical reference literature must not be treated as a patient prescription order."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("textbook_page.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "medical_literature"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == ErrorCode.VALIDATION_FAILED.value
    assert "medical literature" in data["error"]["message"].lower()
    assert data["error"]["details"]["document_type"] == "medical_literature"


def test_reject_blank_page_api(client: TestClient):
    """Uploading a blank white page is rejected before inference via pre-flight validation."""
    blank_bytes = create_solid_image_bytes((255, 255, 255))
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("blank.png", blank_bytes, "image/png")},
    )
    assert response.status_code == 422
    data = response.json()
    assert any(term in data["error"]["message"].lower() for term in ["insufficient", "blank", "contrast", "defocus"])


def test_reject_unsupported_file_extension(client: TestClient):
    """Uploading an unsupported document type (e.g. PDF/DOCX) returns clear 415 error."""
    fake_pdf = b"%PDF-1.4 Fake PDF stream"
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("document.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == ErrorCode.INVALID_FILE_TYPE.value


def test_reject_corrupted_image(client: TestClient, corrupted_image_bytes):
    """Corrupted image header must return 415 without crashing the server."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("corrupt.jpg", corrupted_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == ErrorCode.INVALID_FILE_TYPE.value


# ==============================================================================
# 3. Extraction Grounding, Uncertainty & Posology Integrity
# ==============================================================================

def test_genuine_prescription_succeeds(client: TestClient, sample_prescription_image):
    """Clear, authentic prescription continues through extraction, grounding, and posology synthesis."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("rx.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "single_medicine_confident"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("success", "abstain")
    assert "fields" in data
    assert data["fields"]["medicine_name"]["value"] == "Amoxicillin"
    assert data["fields"]["dosage"]["value"] == "500 mg"
    assert "explanation" in data
    assert len(data["explanation"]["en"]) > 0
    assert len(data["explanation"]["hi"]) > 0
    assert len(data["explanation"]["mr"]) > 0


def test_handwritten_uncertain_medicine_preserves_uncertainty(client: TestClient, sample_prescription_image):
    """Uncertain medicine name preserves candidates and uncertainty status without guessing."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("uncertain_rx.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "handwritten_uncertain_medicine"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("abstain", "success")
    med_field = data["fields"]["medicine_name"]
    assert med_field["status"] == "uncertain"
    assert "Amoxcillin" in med_field["candidates"]
    assert med_field["uncertainty_reason"] is not None
    assert med_field["verification_instruction"] is not None


def test_blurry_prescription_returns_uncertainty(client: TestClient, sample_prescription_image):
    """Blurry prescription flags fields as uncertain and does not invent missing dosage."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("blurry_rx.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "blurry_prescription"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["requires_human_review"] is True
    # Missing dosage must remain missing/uncertain, never fabricated
    dosage_field = data["fields"]["dosage"]
    assert dosage_field["status"] == "uncertain"
    assert dosage_field["value"] in ("Not Observed / Absent", "Not Observed", None)


def test_partially_cropped_prescription_flags_missing_fields(client: TestClient, sample_prescription_image):
    """Cropped prescription extracts visible fields while flagging truncated posology as missing."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("cropped_rx.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "partially_cropped"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["requires_human_review"] is True
    assert data["fields"]["medicine_name"]["value"] == "Amoxicillin"
    assert data["fields"]["frequency"]["status"] == "uncertain"
    assert data["fields"]["duration"]["status"] == "uncertain"


def test_provider_failure_returns_controlled_503(client: TestClient, sample_prescription_image):
    """When multimodal provider is unavailable, system returns 503 error; never falls back to mock results."""
    response = client.post(
        "/api/v1/prescriptions/analyze",
        files={"file": ("rx.png", sample_prescription_image, "image/png")},
        data={"mock_scenario": "model_unavailable"},
    )
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE.value


# ==============================================================================
# 4. Abstention Policy Safety On Non-Prescription or Empty Extractions
# ==============================================================================

def test_empty_extraction_abstention_safety():
    """Verify evaluate_prescription_abstention flags empty or non-prescription extraction as REQUIRES_HUMAN_VERIFICATION."""
    empty_result = PrescriptionExtractionResult(
        prescription_id="test-empty-001",
        original_image_url="/uploads/empty.png",
        source_image_sha256="0" * 64,
        model=ModelMetadata(
            provider="mock",
            model_id="mock-v1",
            model_version="1.0",
            prompt_version="1.0",
            config_version="1.0",
            is_mock=True,
        ),
        is_prescription=False,
        document_type="unrelated_image",
        rejection_reason="Landscape photo",
        medicines=[],
        duration_seconds=0.1,
    )

    decision = evaluate_prescription_abstention(
        prescription_id="test-empty-001",
        extraction_result=empty_result,
    )

    # Must mandate human verification and withhold acceptance!
    assert decision.requires_human_verification is True
    assert decision.prescription_decision == "REQUIRES_HUMAN_VERIFICATION"
    assert decision.abstained_fields_count >= 1
    assert "Document visual/textual evidence does not substantiate" in decision.summary
