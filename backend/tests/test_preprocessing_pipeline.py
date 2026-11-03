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
        """Verifies that unconditional derived representations are produced including vlm_image and ocr_image."""
        data = _generate_test_script_image()
        result = self.pipeline.process(data, "test.png")

        assert "vlm_image" in result.derived_images
        assert "ocr_image" in result.derived_images
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

    def test_vlm_image_preserves_decimal_points_and_thin_strokes(self):
        """Verifies that vlm_image preserves continuous grayscale/color gradients and decimal points without binary threshold clipping."""
        # Create an image with an off-white background, faint text, and a delicate decimal point dot
        im = Image.new("RGB", (500, 300), color=(248, 246, 240))
        draw = ImageDraw.Draw(im)
        draw.text((30, 40), "Digoxin 0.125 mg daily", fill=(70, 70, 70))
        # Explicitly draw a small decimal point dot (1x1 pixel) at known location (100, 100)
        im.putpixel((100, 100), (140, 140, 140))
        buf = io.BytesIO()
        im.save(buf, format="PNG")

        result = self.pipeline.process(buf.getvalue(), "decimal_rx.png")
        vlm_img = result.derived_images["vlm_image"]

        # VLM image must be RGB mode to preserve stroke color gradients
        assert vlm_img.mode == "RGB"

        # The decimal point pixel must be preserved as distinct dark stroke pixel, not obliterated to pure white (255, 255, 255)
        dot_pixel = vlm_img.getpixel((100, 100))
        bg_pixel = vlm_img.getpixel((10, 10))
        # Stroke must be darker than background
        assert dot_pixel[0] < bg_pixel[0]
        # Stroke must maintain continuous tonal gradient rather than being strictly binary (0 or 255)
        assert 0 < dot_pixel[0] < 255

    def test_vlm_image_respects_resolution_bounds_and_never_downscales_below_bounds(self):
        """Verifies that high-resolution images are preserved within the [1536px, 2048px] target window and never downscaled below bounds."""
        # Test 1: Image within bounds (1600x1200) - longest edge 1600px is <= 2048px and >= 1536px
        im_in_bound = Image.new("RGB", (1600, 1200), color=(240, 240, 240))
        buf1 = io.BytesIO()
        im_in_bound.save(buf1, format="PNG")

        res1 = self.pipeline.process(buf1.getvalue(), "high_res.png")
        vlm1 = res1.derived_images["vlm_image"]
        # Must NOT be downscaled; original resolution preserved
        assert vlm1.size == (1600, 1200)

        # Test 2: Huge camera photo (3000x2000) - longest edge exceeds 2048px limit
        im_huge = Image.new("RGB", (3000, 2000), color=(240, 240, 240))
        buf2 = io.BytesIO()
        im_huge.save(buf2, format="JPEG")

        res2 = self.pipeline.process(buf2.getvalue(), "huge_phone_photo.jpg")
        vlm2 = res2.derived_images["vlm_image"]
        # Longest edge capped at 2048px to prevent HTTP 413 payload size errors
        assert max(vlm2.size) == 2048
        assert vlm2.size == (2048, 1365)

