"""
Phase 4 Unit Tests: Preprocessing Pipeline
Tests all transformation stages (orientation, grayscale, illumination normalization,
denoising, contrast enhancement, deskew, Sauvola thresholding), reproducibility, and determinism.
"""

import io
from pathlib import Path
import pytest
from PIL import Image, ImageDraw

from backend.app.preprocessing.config import PreprocessingConfig
from backend.app.preprocessing.pipeline import PrescriptionPreprocessingPipeline


def _generate_test_script_image() -> bytes:
    im = Image.new("RGB", (400, 500), color=(245, 245, 245))
    draw = ImageDraw.Draw(im)
    draw.text((25, 25), "Rx Prescription Note", fill=(20, 20, 20))
    draw.line([(25, 50), (375, 50)], fill=(50, 50, 50), width=2)
    draw.text((25, 80), "Metformin 500mg BD PC", fill=(30, 30, 90))
    draw.text((25, 120), "Atorvastatin 10mg OD HS", fill=(30, 30, 90))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


class TestPrescriptionPreprocessingPipeline:

    def setup_method(self):
        self.config = PreprocessingConfig()
        self.pipeline = PrescriptionPreprocessingPipeline(self.config)

    def test_pipeline_generates_all_derived_representations(self):
        """Verifies that the 5 unconditional derived representations are produced (deskewed.png is conditional on detected skew angle)."""
        data = _generate_test_script_image()
        result = self.pipeline.process(data, "test.png")

        assert "grayscale" in result.derived_images
        assert "normalized" in result.derived_images
        assert "denoised" in result.derived_images
        assert "enhanced" in result.derived_images
        assert "thresholded" in result.derived_images

        # Check dimensions match original
        for name, img in result.derived_images.items():
            assert img.width == 400
            assert img.height == 500

    def test_illumination_correction_improves_contrast_in_shadowed_regions(self):
        """Verifies that illumination normalization brightens paper background while retaining ink."""
        # Create image with uneven gradient background (shadow from 50 to 250)
        im = Image.new("L", (300, 300))
        for y in range(300):
            for x in range(300):
                im.putpixel((x, y), int(50 + (x / 300.0) * 180))
        # Add black ink text
        draw = ImageDraw.Draw(im)
        draw.text((50, 150), "TEST INK", fill=0)
        buf = io.BytesIO()
        im.save(buf, format="PNG")

        result = self.pipeline.process(buf.getvalue(), "shadow.png")
        norm_img = result.derived_images["normalized"]

        # Background in previously dark left side (x=20, y=150) should be brightened
        orig_val = im.getpixel((20, 150))
        norm_val = norm_img.getpixel((20, 150))
        assert norm_val > orig_val

    def test_sauvola_threshold_produces_binary_image(self):
        """Verifies that Sauvola threshold representation contains only 0 and 255 pixels."""
        data = _generate_test_script_image()
        result = self.pipeline.process(data, "test.png")
        thresh = result.derived_images["thresholded"]

        unique_vals = set(thresh.getdata())
        # Should only contain 0 (ink) and 255 (background)
        assert unique_vals.issubset({0, 255})
        assert 0 in unique_vals  # Ink strokes exist
        assert 255 in unique_vals  # Background exists

    def test_determinism_and_reproducibility(self):
        """Verifies that running the same image and configuration twice produces byte-for-byte identical results."""
        data = _generate_test_script_image()

        res1 = self.pipeline.process(data, "test.png")
        res2 = self.pipeline.process(data, "test.png")

        # Compare derived image bytes
        for name in res1.derived_images:
            b1 = io.BytesIO()
            b2 = io.BytesIO()
            res1.derived_images[name].save(b1, format="PNG")
            res2.derived_images[name].save(b2, format="PNG")
            assert b1.getvalue() == b2.getvalue(), f"Derived representation {name} was not deterministic!"

        # Compare quality report
        assert res1.quality_report.heuristic_quality_score == res2.quality_report.heuristic_quality_score
        assert res1.quality_report.overall_status == res2.quality_report.overall_status

    def test_config_hash_stability(self):
        """Verifies that configuration SHA-256 fingerprint is stable across instances."""
        c1 = PreprocessingConfig()
        c2 = PreprocessingConfig()
        assert c1.compute_config_hash() == c2.compute_config_hash()

        # Modify parameter and verify hash changes
        c3 = PreprocessingConfig(illumination_sigma=45.0)
        assert c3.compute_config_hash() != c1.compute_config_hash()
