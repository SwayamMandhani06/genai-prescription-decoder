"""
Phase 4: Image Ingestion Validation
Performs robust pre-flight validation on incoming prescription image streams:
format checking, dimensional boundary checks, corruption detection, and color space normalization.
"""

import io
from pathlib import Path
from typing import Optional, Set, Tuple
from PIL import Image, ImageOps, UnidentifiedImageError

# Security constraint: Limit maximum decompressed pixels to defend against zip/decompression bombs
Image.MAX_IMAGE_PIXELS = 50_000_000

from .config import PreprocessingConfig, QualityThresholds
from .metadata import ImageMetadata, extract_image_metadata
from ..schemas.error import ErrorCode


class ImageValidationError(Exception):
    """
    Diagnostic exception raised when an incoming image fails pre-flight validation.
    Conforms directly to the project's standardized error contract.
    """
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        stage: str = "image_ingestion_validation",
        retryable: bool = False,
        details: Optional[dict] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.stage = stage
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)


def detect_image_format_from_bytes(image_bytes: bytes) -> Optional[str]:
    """
    Detects true image container format from initial file magic bytes.
    Does not rely on filename extension or HTTP Content-Type headers.
    """
    if not image_bytes or len(image_bytes) < 4:
        return None
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if image_bytes.startswith(b"RIFF") and len(image_bytes) >= 12 and image_bytes[8:12] == b"WEBP":
        return "WEBP"
    if image_bytes.startswith(b"II*\x00") or image_bytes.startswith(b"MM\x00*"):
        return "TIFF"
    if image_bytes.startswith(b"BM"):
        return "BMP"
    return None


class ImageIngestionValidator:
    """
    Validates incoming image byte streams against security, dimensional, and format policies.
    """
    SUPPORTED_EXTENSIONS: Set[str] = {
        ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"
    }

    SUPPORTED_FORMATS: Set[str] = {
        "JPEG", "PNG", "WEBP", "TIFF", "BMP"
    }

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.thresholds: QualityThresholds = self.config.thresholds

    def validate_and_load(
        self,
        image_bytes: Optional[bytes],
        filename: Optional[str] = None,
        reject_blank: bool = False,
    ) -> Tuple[Image.Image, ImageMetadata]:
        """
        Validates raw image bytes and returns:
            - Normalized Pillow Image object (RGB mode, EXIF orientation corrected)
            - Structural ImageMetadata record

        Raises:
            ImageValidationError if the image stream violates any constraint.
        """
        # 1. Check for empty or missing input
        if not image_bytes or len(image_bytes) == 0:
            raise ImageValidationError(
                code=ErrorCode.INVALID_REQUEST,
                message="Prescription image stream is empty (zero bytes received).",
                status_code=400,
                retryable=True,
                details={"provided_filename": filename, "file_size_bytes": 0},
            )

        # 2. Detect container format via magic bytes
        magic_format = detect_image_format_from_bytes(image_bytes)

        # Check filename extension if supplied
        if filename:
            ext = Path(filename).suffix.lower()
            # Non-image extensions like .pdf, .exe, .doc must be rejected even if containing image headers
            if ext and ext not in self.SUPPORTED_EXTENSIONS:
                raise ImageValidationError(
                    code=ErrorCode.INVALID_FILE_TYPE,
                    message=(
                        f"File extension '{ext}' is not supported for prescription ingestion. "
                        f"Allowed extensions: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}."
                    ),
                    status_code=415,
                    retryable=False,
                    details={"unsupported_extension": ext, "filename": filename},
                )

        # 3. Verify image integrity and header decoding via Pillow Image.open().verify()
        try:
            verify_stream = io.BytesIO(image_bytes)
            with Image.open(verify_stream) as test_img:
                test_img.verify()
                pillow_format = test_img.format
        except (UnidentifiedImageError, OSError, SyntaxError) as err:
            raise ImageValidationError(
                code=ErrorCode.INVALID_FILE_TYPE,
                message=f"Prescription file is corrupted, truncated, or not a recognized image: {str(err)}",
                status_code=415,
                retryable=False,
                details={"decoding_error": str(err), "filename": filename},
            )

        # Resolve true format prioritizing magic bytes and Pillow decoder
        detected_format = (magic_format or pillow_format or "").upper()
        if detected_format not in self.SUPPORTED_FORMATS:
            raise ImageValidationError(
                code=ErrorCode.INVALID_FILE_TYPE,
                message=f"Detected image format '{detected_format}' is not permitted for clinical interpretation.",
                status_code=415,
                retryable=False,
                details={"detected_format": detected_format},
            )

        # 4. Re-open image for actual processing and auto-apply EXIF transposition
        # Image.verify() closes/invalidates the stream, so open a fresh BytesIO stream
        load_stream = io.BytesIO(image_bytes)
        pil_img = Image.open(load_stream)

        # Apply EXIF transposition immediately so rotated phone photos are upright before OCR/VLM
        if self.config.enable_orientation_correction:
            try:
                pil_img = ImageOps.exif_transpose(pil_img)
            except Exception:
                pass  # Fall back to raw orientation if EXIF transpose fails

        # 5. Extract metadata reflecting the upright transposed dimensions
        metadata = extract_image_metadata(
            image_bytes=image_bytes,
            filename=filename,
            apply_exif_transpose=self.config.enable_orientation_correction,
        )
        # Ensure metadata geometry matches the transposed image
        metadata.width = pil_img.width
        metadata.height = pil_img.height
        metadata.pixel_area = pil_img.width * pil_img.height
        metadata.file_format = detected_format

        # 6. Dimensional Constraints
        # Upper bound: Prevent memory exhaustion / decompression bombs
        if metadata.width > self.thresholds.max_dimension or metadata.height > self.thresholds.max_dimension:
            raise ImageValidationError(
                code=ErrorCode.FILE_TOO_LARGE,
                message=(
                    f"Image dimensions ({metadata.width}x{metadata.height}px) exceed maximum allowed "
                    f"dimension of {self.thresholds.max_dimension}px."
                ),
                status_code=413,
                retryable=True,
                details={
                    "width": metadata.width,
                    "height": metadata.height,
                    "max_dimension": self.thresholds.max_dimension,
                },
            )

        # Lower bound: Check for images that are too small for character stroke resolution
        if metadata.width < self.thresholds.min_width or metadata.height < self.thresholds.min_height:
            raise ImageValidationError(
                code=ErrorCode.IMAGE_QUALITY_INSUFFICIENT,
                message=(
                    f"Image resolution ({metadata.width}x{metadata.height}px) is below minimum threshold "
                    f"({self.thresholds.min_width}x{self.thresholds.min_height}px) required for character stroke resolution."
                ),
                status_code=422,
                stage="image_quality_assessment",
                retryable=True,
                details={
                    "width": metadata.width,
                    "height": metadata.height,
                    "min_width": self.thresholds.min_width,
                    "min_height": self.thresholds.min_height,
                    "recommendation": "Provide a higher-resolution photograph or scan of the prescription pad.",
                },
            )

        # 7. Normalize Color Space to RGB:
        # If RGBA, composite over pure white background so transparent strokes remain visible
        if pil_img.mode == "RGBA":
            background = Image.new("RGB", pil_img.size, (255, 255, 255))
            background.paste(pil_img, mask=pil_img.split()[3])
            normalized_img = background
        elif pil_img.mode == "P":
            converted = pil_img.convert("RGBA")
            background = Image.new("RGB", pil_img.size, (255, 255, 255))
            background.paste(converted, mask=converted.split()[3])
            normalized_img = background
        elif pil_img.mode == "CMYK":
            normalized_img = pil_img.convert("RGB")
        elif pil_img.mode in ("1", "L"):
            normalized_img = pil_img.convert("RGB")
        elif pil_img.mode == "RGB":
            normalized_img = pil_img.copy()
        else:
            normalized_img = pil_img.convert("RGB")

        # 8. Optional preflight check for blank canvas (blank white page or uniform solid color)
        # Tuned to prevent false rejection of tinted/colored clinic pads (e.g. yellow/blue hospital stationery)
        # or low-ink paediatric notes.
        if reject_blank:
            try:
                import numpy as np
                gray_check = np.array(normalized_img.convert("L"), dtype=np.float32)
                pixel_std = float(np.std(gray_check))
                mean_lum = float(np.mean(gray_check))
                ptp_range = float(np.ptp(gray_check))

                # A page is only rejected if it is truly blank/solid canvas devoid of ink strokes.
                # Solid white/black/colored sheets have pixel_std near 0.0 and ptp_range < 12.0.
                # Tinted clinic pads or low-ink paediatric notes have strokes that create ptp_range >= 15.0.
                is_blank = (
                    (pixel_std < 1.5 and ptp_range < 12.0)
                    or (pixel_std < 2.5 and ptp_range < 15.0 and (mean_lum > 245.0 or mean_lum < 15.0))
                    or ptp_range < 6.0
                )
                if is_blank:
                    raise ImageValidationError(
                        code=ErrorCode.IMAGE_QUALITY_INSUFFICIENT,
                        message="The uploaded image appears completely blank or devoid of handwritten ink strokes and document content.",
                        status_code=422,
                        stage="image_content_validation",
                        retryable=True,
                        details={
                            "std_deviation": round(pixel_std, 2),
                            "mean_luminance": round(mean_lum, 2),
                            "dynamic_range": round(ptp_range, 2),
                            "issue": "blank_or_solid_page",
                            "recommendation": "Please upload a clear photograph of a physical prescription containing doctor handwriting or clinical text.",
                        },
                    )
            except ImageValidationError:
                raise
            except Exception:
                pass

        return normalized_img, metadata
