"""
Phase 4 Unit Tests: Image Ingestion Validation
Tests supported formats, corrupted streams, dimensional bounds, color mode conversions,
and adherence to the project's error contract.
"""

import io
import pytest
from PIL import Image

from backend.app.preprocessing.config import PreprocessingConfig
from backend.app.preprocessing.validator import ImageIngestionValidator, ImageValidationError
from backend.app.schemas.error import ErrorCode


def _create_test_image(size=(300, 400), mode="RGB", color=(240, 240, 240), fmt="PNG") -> bytes:
    """Helper creating memory buffer with synthetic test image."""
    im = Image.new(mode, size, color=color)
    buf = io.BytesIO()
    im.save(buf, format=fmt)
    return buf.getvalue()


class TestImageIngestionValidator:

    def setup_method(self):
        self.config = PreprocessingConfig()
        self.validator = ImageIngestionValidator(self.config)

    def test_valid_png_and_jpeg_acceptance(self):
        """Verifies that standard PNG and JPEG prescription scans are accepted and normalized."""
        png_bytes = _create_test_image(size=(400, 500), mode="RGB", fmt="PNG")
        pil_img, meta = self.validator.validate_and_load(png_bytes, "test_rx.png")
        assert pil_img.size == (400, 500)
        assert pil_img.mode == "RGB"
        assert meta.file_format == "PNG"

        jpg_bytes = _create_test_image(size=(500, 600), mode="RGB", fmt="JPEG")
        pil_img_jpg, meta_jpg = self.validator.validate_and_load(jpg_bytes, "test_rx.jpg")
        assert pil_img_jpg.size == (500, 600)
        assert pil_img_jpg.mode == "RGB"

    def test_valid_webp_and_tiff_acceptance(self):
        """Verifies WEBP and TIFF container formats."""
        webp_bytes = _create_test_image(size=(350, 450), mode="RGB", fmt="WEBP")
        pil_img, meta = self.validator.validate_and_load(webp_bytes, "test_rx.webp")
        assert pil_img.size == (350, 450)
        assert meta.file_format == "WEBP"

        tiff_bytes = _create_test_image(size=(350, 450), mode="RGB", fmt="TIFF")
        pil_img_tiff, meta_tiff = self.validator.validate_and_load(tiff_bytes, "test_rx.tiff")
        assert pil_img_tiff.size == (350, 450)
        assert meta_tiff.file_format == "TIFF"

    def test_empty_or_zero_byte_stream_rejection(self):
        """Verifies that empty byte streams raise HTTP 400 INVALID_REQUEST."""
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_and_load(b"", "empty.png")
        assert exc_info.value.code == ErrorCode.INVALID_REQUEST
        assert exc_info.value.status_code == 400

    def test_corrupted_image_bytes_rejection(self):
        """Verifies that corrupted or non-decodable byte streams raise HTTP 415 INVALID_FILE_TYPE."""
        corrupted = b"NOT_A_VALID_IMAGE_HEADER_RANDOM_GARBAGE"
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_and_load(corrupted, "corrupted.png")
        assert exc_info.value.code == ErrorCode.INVALID_FILE_TYPE
        assert exc_info.value.status_code == 415

    def test_unsupported_file_extension_rejection(self):
        """Verifies that forbidden file extensions raise HTTP 415 INVALID_FILE_TYPE."""
        valid_bytes = _create_test_image()
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_and_load(valid_bytes, "prescription.pdf")
        assert exc_info.value.code == ErrorCode.INVALID_FILE_TYPE
        assert exc_info.value.status_code == 415

        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_and_load(valid_bytes, "payload.exe")
        assert exc_info.value.code == ErrorCode.INVALID_FILE_TYPE

    def test_oversized_dimension_rejection(self):
        """Verifies that images exceeding max_dimension raise HTTP 413 FILE_TOO_LARGE."""
        oversized = _create_test_image(size=(8500, 1000), fmt="PNG")
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_and_load(oversized, "huge.png")
        assert exc_info.value.code == ErrorCode.FILE_TOO_LARGE
        assert exc_info.value.status_code == 413

    def test_tiny_image_insufficient_resolution_rejection(self):
        """Verifies that images smaller than min_width or min_height raise HTTP 422 IMAGE_QUALITY_INSUFFICIENT."""
        tiny = _create_test_image(size=(100, 100), fmt="PNG")
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_and_load(tiny, "tiny.png")
        assert exc_info.value.code == ErrorCode.IMAGE_QUALITY_INSUFFICIENT
        assert exc_info.value.status_code == 422
        assert exc_info.value.stage == "image_quality_assessment"

    def test_rgba_transparency_compositing_on_white(self):
        """Verifies that RGBA transparent PNGs are composited over a solid white background."""
        # Create RGBA image with transparent background (alpha=0) and red stroke
        im = Image.new("RGBA", (300, 400), color=(0, 0, 0, 0))
        for x in range(50, 150):
            im.putpixel((x, 100), (200, 0, 0, 255))
        buf = io.BytesIO()
        im.save(buf, format="PNG")

        pil_img, meta = self.validator.validate_and_load(buf.getvalue(), "transparent.png")
        assert pil_img.mode == "RGB"
        # Background pixel should be pure white (255, 255, 255)
        assert pil_img.getpixel((10, 10)) == (255, 255, 255)
        # Ink stroke pixel should be preserved
        assert pil_img.getpixel((100, 100)) == (200, 0, 0)

    def test_palette_and_monochrome_conversion(self):
        """Verifies that Palette (P) and monochrome (1, L) modes are cleanly converted to RGB."""
        # Monochrome 1-bit
        im_1 = Image.new("1", (200, 200), color=1)
        buf = io.BytesIO()
        im_1.save(buf, format="PNG")
        pil_img, _ = self.validator.validate_and_load(buf.getvalue(), "mono.png")
        assert pil_img.mode == "RGB"

        # Grayscale L
        im_l = Image.new("L", (200, 200), color=180)
        buf = io.BytesIO()
        im_l.save(buf, format="PNG")
        pil_img_l, _ = self.validator.validate_and_load(buf.getvalue(), "gray.png")
        assert pil_img_l.mode == "RGB"
