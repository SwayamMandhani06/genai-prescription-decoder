"""
Phase 4: Image Ingestion Validation
Performs robust pre-flight validation on incoming prescription image streams:
format checking, dimensional boundary checks, corruption detection, and color space normalization.
"""

import io
from pathlib import Path
from typing import Optional, Set, Tuple
from PIL import Image, ImageOps, UnidentifiedImageError

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

        # 2. Check filename extension if supplied
        if filename:
            ext = Path(filename).suffix.lower()
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

        # 3. Verify image integrity and header decoding
        try:
            # We first verify the raw stream
            verify_stream = io.BytesIO(image_bytes)
            with Image.open(verify_stream) as test_img:
                test_img.verify()
                img_format = test_img.format
        except (UnidentifiedImageError, OSError, SyntaxError) as err:
            raise ImageValidationError(
                code=ErrorCode.INVALID_FILE_TYPE,
                message=f"Prescription file is corrupted, truncated, or not a recognized image: {str(err)}",
                status_code=415,
                retryable=False,
                details={"decoding_error": str(err), "filename": filename},
            )

        # Validate Pillow detected format
        if img_format and img_format.upper() not in self.SUPPORTED_FORMATS:
            raise ImageValidationError(
                code=ErrorCode.INVALID_FILE_TYPE,
                message=f"Detected image format '{img_format}' is not permitted for clinical interpretation.",
                status_code=415,
                retryable=False,
                details={"detected_format": img_format},
            )

        # 4. Extract metadata before any transformations
        metadata = extract_image_metadata(image_bytes, filename=filename)

        # 5. Dimensional Constraints
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

        # Lower bound: Check for images that are too small for handwriting recognition
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

        # 6. Re-open image for actual processing and color normalization
        # Note: Image.verify() closes or invalidates the stream, so open a fresh BytesIO
        load_stream = io.BytesIO(image_bytes)
        pil_img = Image.open(load_stream)

        # Apply EXIF transposition (auto-rotate based on camera sensor orientation tag)
        if self.config.enable_orientation_correction:
            try:
                pil_img = ImageOps.exif_transpose(pil_img)
            except Exception:
                pass  # Fall back to raw orientation if EXIF transpose fails

        # Normalize Color Space to RGB:
        # If RGBA, composite over pure white background so transparent strokes remain visible
        if pil_img.mode == "RGBA":
            background = Image.new("RGB", pil_img.size, (255, 255, 255))
            background.paste(pil_img, mask=pil_img.split()[3])
            normalized_img = background
        elif pil_img.mode == "P":
            # Palette mode: convert via RGBA then composite, or directly to RGB
            converted = pil_img.convert("RGBA")
            background = Image.new("RGB", pil_img.size, (255, 255, 255))
            background.paste(converted, mask=converted.split()[3])
            normalized_img = background
        elif pil_img.mode == "CMYK":
            normalized_img = pil_img.convert("RGB")
        elif pil_img.mode in ("1", "L"):
            # Monochrome / Grayscale to RGB for standardized pipeline handling
            normalized_img = pil_img.convert("RGB")
        elif pil_img.mode == "RGB":
            normalized_img = pil_img.copy()
        else:
            # Fallback conversion
            normalized_img = pil_img.convert("RGB")

        return normalized_img, metadata
