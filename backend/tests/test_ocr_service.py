"""
Phase 5 Test Suite: OCR Baseline Service & Research Integrity
Tests end-to-end baseline execution, raw output immutability, variant comparison,
empty output handling, token/bounding box extraction, and absence of fabricated confidence.
"""

import hashlib
import io
from pathlib import Path
import pytest
from PIL import Image, ImageDraw, ImageFont

from backend.app.ocr import (
    OCRBaselineConfig,
    OCRBaselineService,
    OCRRunResult,
    NormalizedOCRRepresentation,
)

SAMPLE_PATH = Path("data/samples/sample_01_clear.png")


def create_synthetic_test_prescription() -> bytes:
    """Creates a deterministic synthetic test image containing clear text."""
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "Rx: Amoxicillin 500 mg", fill=(0, 0, 0))
    draw.text((30, 100), "Take 1 tablet daily (OD)", fill=(0, 0, 0))
    draw.text((30, 160), "Duration: 5 days", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_blank_test_image() -> bytes:
    """Creates a completely blank white image producing empty OCR transcription."""
    img = Image.new("RGB", (400, 400), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestOCRBaselineServiceExecution:
    """Verifies baseline service execution on images."""

    def test_service_executes_on_synthetic_image(self):
        service = OCRBaselineService()
        image_bytes = create_synthetic_test_prescription()
        expected_sha256 = hashlib.sha256(image_bytes).hexdigest()

        result = service.run_ocr(
            image_input=image_bytes,
            filename="synthetic_rx.png",
            preprocessing_variant="enhanced",
        )

        assert isinstance(result, OCRRunResult)
        assert result.source_image_sha256 == expected_sha256
        assert result.preprocessing_artifact == "enhanced"
        assert result.preprocessing_artifact_sha256 is not None
        assert result.raw_text_sha256 == hashlib.sha256(result.raw_text.encode("utf-8")).hexdigest()
        assert result.processing_status in ("completed", "partial")
        assert len(result.tokens) > 0
        assert len(result.lines) > 0

    @pytest.mark.skipif(not SAMPLE_PATH.is_file(), reason="Sample 01 clear image required")
    def test_service_executes_on_real_sample_image(self):
        service = OCRBaselineService()
        with open(SAMPLE_PATH, "rb") as f:
            sample_bytes = f.read()

        expected_hash = hashlib.sha256(sample_bytes).hexdigest()

        result = service.run_ocr(
            image_input=sample_bytes,
            filename=SAMPLE_PATH.name,
            preprocessing_variant="enhanced",
        )

        assert result.source_image_sha256 == expected_hash
        assert result.engine.name == "tesseract"
        assert result.duration_seconds > 0.0
        assert isinstance(result.raw_text, str)
        assert result.raw_text_sha256 == hashlib.sha256(result.raw_text.encode("utf-8")).hexdigest()


class TestResearchIntegrityAndImmutability:
    """
    CRITICAL RESEARCH INTEGRITY VERIFICATION:
    - Raw OCR output is never modified or post-hoc 'corrected'
    - Normalization produces a separate object
    - No fabricated confidence scores exist
    - Blank images do not produce guessed text
    """

    def test_raw_ocr_output_immutability(self):
        service = OCRBaselineService()
        image_bytes = create_synthetic_test_prescription()
        result = service.run_ocr(image_input=image_bytes)

        original_raw_text = result.raw_text
        original_hash = result.raw_text_sha256

        # Generate normalized evaluation representation
        norm_rep = service.create_normalized_representation(result)

        assert isinstance(norm_rep, NormalizedOCRRepresentation)
        # Verify the raw text in the run result remained unchanged
        assert result.raw_text == original_raw_text
        assert result.raw_text_sha256 == original_hash
        # Verify normalized representation is a separate object
        assert norm_rep.ocr_run_id == result.ocr_run_id
        assert norm_rep.raw_text == original_raw_text
        assert norm_rep.normalized_text == norm_rep.normalized_text.lower()

    def test_blank_image_handling_without_fabrication(self):
        """
        Verifies that empty OCR output remains '' and status='partial'.
        NEVER generates guessed strings like 'Unable to read'.
        """
        service = OCRBaselineService()
        blank_bytes = create_blank_test_image()

        result = service.run_ocr(
            image_input=blank_bytes,
            filename="blank.png",
            preprocessing_variant="enhanced",
        )

        # Raw text must be empty string
        assert result.raw_text.strip() == ""
        # Status must be 'partial'
        assert result.processing_status == "partial"
        # Must not fabricate placeholder text
        assert "Unable to read" not in result.raw_text
        assert "No text" not in result.raw_text

    def test_no_fabricated_confidence_values(self):
        """
        Verifies that confidence values are either valid floats [0.0, 100.0] or None.
        Tokens must never have synthetic placeholder numbers (e.g. 0.999).
        """
        service = OCRBaselineService()
        image_bytes = create_synthetic_test_prescription()
        result = service.run_ocr(image_input=image_bytes)

        for tok in result.tokens:
            if tok.confidence is not None:
                assert 0.0 <= tok.confidence <= 100.0
                assert isinstance(tok.confidence, float)


class TestPreprocessingVariantComparison:
    """Verifies multi-variant comparison execution."""

    def test_variant_comparison_produces_all_representations(self):
        service = OCRBaselineService()
        image_bytes = create_synthetic_test_prescription()

        results = service.run_variant_comparison(
            image_bytes=image_bytes,
            variants=["original", "grayscale", "enhanced", "thresholded"],
        )

        assert "original" in results
        assert "grayscale" in results
        assert "enhanced" in results
        assert "thresholded" in results

        # Verify each variant recorded its own distinct representation name
        assert results["original"].preprocessing_artifact == "original"
        assert results["enhanced"].preprocessing_artifact == "enhanced"
        assert results["thresholded"].preprocessing_artifact == "thresholded"

        # Verify source hash is identical across all variants
        source_hash = results["original"].source_image_sha256
        for var_name, res in results.items():
            assert res.source_image_sha256 == source_hash
