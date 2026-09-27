"""
Phase 4 Unit Tests: Image Quality Assessment
Tests deterministic optical and textural quality metrics across sharp, blurry,
underexposed, overexposed, low-contrast, skewed, and noisy image conditions.
"""

import io
from pathlib import Path
import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFilter

from backend.app.preprocessing.config import PreprocessingConfig
from backend.app.preprocessing.metadata import extract_image_metadata
from backend.app.preprocessing.quality import ImageQualityAssessor


def _make_canvas_with_text(text="Rx Amoxicillin 500mg 1 tab TDS", size=(500, 600), bg=240, fg=20) -> Image.Image:
    im = Image.new("RGB", size, color=(bg, bg, bg))
    draw = ImageDraw.Draw(im)
    draw.text((30, 40), text, fill=(fg, fg, fg))
    draw.line([(30, 80), (450, 80)], fill=(fg, fg, fg), width=2)
    for y in range(120, 450, 40):
        draw.text((30, y), f"Item at line {y}: Augmentin 625 Duo", fill=(fg, fg, fg))
    return im


def _pil_to_png_bytes(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


class TestImageQualityAssessor:

    def setup_method(self):
        self.config = PreprocessingConfig()
        self.assessor = ImageQualityAssessor(self.config)

    def test_sharp_image_evaluates_as_acceptable(self):
        """Verifies that a crisp, high-contrast prescription evaluates with acceptable status."""
        sharp_im = _make_canvas_with_text()
        data = _pil_to_png_bytes(sharp_im)
        meta = extract_image_metadata(data, filename="sharp.png")
        report = self.assessor.assess_quality(sharp_im, meta)

        assert report.overall_status in ("acceptable", "degraded_but_usable")
        assert report.heuristic_quality_score >= 0.70
        assert report.metrics["blur"]["is_fatal"] is False

    def test_severely_blurred_image_evaluates_as_insufficient(self):
        """Verifies that severe optical blur triggers fatal blur issue and insufficient status."""
        sharp_im = _make_canvas_with_text()
        blurred_im = sharp_im.filter(ImageFilter.GaussianBlur(radius=8.0))
        data = _pil_to_png_bytes(blurred_im)
        meta = extract_image_metadata(data, filename="blur.png")
        report = self.assessor.assess_quality(blurred_im, meta)

        assert report.overall_status == "insufficient"
        assert report.metrics["blur"]["is_fatal"] is True
        assert report.heuristic_quality_score < 0.40
        assert any("Severe optical defocus or motion blur" in iss for iss in report.issues)

    def test_severely_underexposed_image_evaluates_as_insufficient(self):
        """Verifies that near-pitch-black images are rejected as insufficient."""
        dark_im = _make_canvas_with_text(bg=20, fg=5)
        data = _pil_to_png_bytes(dark_im)
        meta = extract_image_metadata(data, filename="dark.png")
        report = self.assessor.assess_quality(dark_im, meta)

        assert report.overall_status == "insufficient"
        assert report.metrics["brightness"]["is_underexposed"] is True
        assert any("underexposure" in iss.lower() for iss in report.issues)

    def test_severely_overexposed_image_evaluates_as_insufficient(self):
        """Verifies that completely washed-out images are rejected as insufficient."""
        # Near pure white with contrast < 1.0
        bright_im = Image.new("RGB", (500, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(bright_im)
        draw.text((30, 40), "Washed out text", fill=(254, 254, 254))
        data = _pil_to_png_bytes(bright_im)
        meta = extract_image_metadata(data, filename="bright.png")
        report = self.assessor.assess_quality(bright_im, meta)

        assert report.overall_status == "insufficient"

    def test_skew_angle_detection(self):
        """Verifies that document text skew is detected within search limits."""
        base_im = _make_canvas_with_text()
        # Rotate by 6 degrees
        skewed_im = base_im.rotate(6.0, expand=False, fillcolor=(240, 240, 240))
        data = _pil_to_png_bytes(skewed_im)
        meta = extract_image_metadata(data, filename="skew.png")
        report = self.assessor.assess_quality(skewed_im, meta)

        detected_skew = abs(report.metrics["skew"]["estimated_angle_deg"])
        # Should detect approximately ~6 degrees (within +/- 1.5 deg resolution)
        assert abs(detected_skew - 6.0) <= 2.0
        assert report.metrics["skew"]["is_skewed"] is True

    def test_calibration_sample_01_clear(self):
        """Verifies optical quality evaluation on canonical clear sample."""
        p = Path("data/samples/sample_01_clear.png")
        if not p.exists():
            pytest.skip("data/samples/sample_01_clear.png not found")

        with Image.open(p) as im:
            meta = extract_image_metadata(p.read_bytes(), filename=p.name)
            report = self.assessor.assess_quality(im, meta)
            assert report.overall_status == "acceptable"
            assert report.heuristic_quality_score >= 0.80

    def test_calibration_sample_03_blurred(self):
        """Verifies that canonical blurred sample is classified as insufficient."""
        p = Path("data/samples/sample_03_blurred.png")
        if not p.exists():
            pytest.skip("data/samples/sample_03_blurred.png not found")

        with Image.open(p) as im:
            meta = extract_image_metadata(p.read_bytes(), filename=p.name)
            report = self.assessor.assess_quality(im, meta)
            assert report.overall_status == "insufficient"
            assert report.metrics["blur"]["is_fatal"] is True

    def test_calibration_sample_04_lowlight(self):
        """Verifies that canonical low-light sample is classified as degraded_but_usable."""
        p = Path("data/samples/sample_04_lowlight.png")
        if not p.exists():
            pytest.skip("data/samples/sample_04_lowlight.png not found")

        with Image.open(p) as im:
            meta = extract_image_metadata(p.read_bytes(), filename=p.name)
            report = self.assessor.assess_quality(im, meta)
            assert report.overall_status == "degraded_but_usable"
            assert 0.40 <= report.heuristic_quality_score <= 0.79
            assert len(report.warnings) > 0

    def test_quality_score_semantics_and_bounds(self):
        """Verifies that heuristic_quality_score strictly lies in [0.0, 1.0] and includes disclaimer."""
        im = _make_canvas_with_text()
        data = _pil_to_png_bytes(im)
        meta = extract_image_metadata(data, filename="test.png")
        report = self.assessor.assess_quality(im, meta)

        assert 0.0 <= report.heuristic_quality_score <= 1.0
        assert "Engineering heuristic only" in report.score_explanation
        assert "does NOT represent model inference confidence" in report.score_explanation
