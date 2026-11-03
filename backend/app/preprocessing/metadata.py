"""
Phase 4: Image Metadata Extraction
Extracts structural and cryptographic metadata from input prescription files.
Strictly ignores and strips personal/device EXIF tags to preserve privacy.
"""

import hashlib
import io
from typing import Literal, Optional
from PIL import Image, ExifTags, ImageOps
from pydantic import BaseModel, Field


class StructuredQualityFlags(BaseModel):
    """
    Standardized optical degradation flags attached to image metadata
    so downstream confidence calibrators and abstention handlers can consume them.
    """
    low_resolution: bool = Field(False, description="Effective PPI or dimension is below clinical threshold")
    blur_detected: bool = Field(False, description="Significant optical or motion blur detected")
    glare_detected: bool = Field(False, description="Overexposure, lighting saturation, or localized glare detected")
    extreme_skew: bool = Field(False, description="Text baseline rotation or document skew detected")


class ImageMetadata(BaseModel):
    """
    Standardized, privacy-safe metadata describing an ingested prescription image.
    """
    width: int = Field(..., description="Image horizontal width in pixels")
    height: int = Field(..., description="Image vertical height in pixels")
    channels: int = Field(..., description="Number of color channels (e.g. 1 for grayscale, 3 for RGB)")
    color_mode: str = Field(..., description="Pillow color mode identifier (RGB, RGBA, L, CMYK, etc.)")
    file_format: str = Field(..., description="Underlying image container format (PNG, JPEG, TIFF, etc.)")
    file_size_bytes: int = Field(..., description="Exact file size in bytes")
    aspect_ratio: str = Field(..., description="Formatted aspect ratio string (e.g. '0.80:1')")
    orientation: Literal["Portrait", "Landscape", "Square"] = Field(..., description="Geometric spatial orientation")
    exif_orientation: Optional[int] = Field(None, description="Raw EXIF orientation tag if present (1-8)")
    original_sha256: str = Field(..., description="Cryptographic SHA-256 hash of the original input bytes")
    pixel_area: int = Field(..., description="Total pixel count (width * height)")
    effective_ppi: int = Field(..., description="Heuristic pixels-per-inch estimate based on assumed standard prescription pad dimensions (not physical EXIF DPI)")
    quality_flags: StructuredQualityFlags = Field(
        default_factory=StructuredQualityFlags,
        description="Structured optical quality degradation flags for downstream confidence calibration",
    )


def extract_image_metadata(
    image_bytes: bytes,
    filename: Optional[str] = None,
    apply_exif_transpose: bool = True,
) -> ImageMetadata:
    """
    Extracts structural metadata and original cryptographic SHA-256 hash from image bytes.
    Excludes sensitive EXIF tags (e.g., GPS coordinates, camera serial numbers, user comments).
    If apply_exif_transpose is True, dimensions and orientation reflect the upright transposed orientation.
    """
    file_size_bytes = len(image_bytes)
    sha256_hash = hashlib.sha256(image_bytes).hexdigest()

    with Image.open(io.BytesIO(image_bytes)) as raw_pil:
        raw_format = raw_pil.format
        # Safe EXIF orientation extraction before any transposition
        exif_orientation = None
        try:
            exif_data = raw_pil.getexif()
            if exif_data:
                exif_orientation = exif_data.get(0x0112, None)
        except Exception:
            exif_orientation = None

        if apply_exif_transpose:
            try:
                pil_img = ImageOps.exif_transpose(raw_pil)
            except Exception:
                pil_img = raw_pil
        else:
            pil_img = raw_pil

        width, height = pil_img.size
        color_mode = pil_img.mode

        # True container format detection via magic bytes fallback
        if raw_format:
            file_format = raw_format
        elif image_bytes.startswith(b"\xff\xd8\xff"):
            file_format = "JPEG"
        elif image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            file_format = "PNG"
        elif image_bytes.startswith(b"RIFF") and len(image_bytes) >= 12 and image_bytes[8:12] == b"WEBP":
            file_format = "WEBP"
        elif image_bytes.startswith(b"II*\x00") or image_bytes.startswith(b"MM\x00*"):
            file_format = "TIFF"
        elif image_bytes.startswith(b"BM"):
            file_format = "BMP"
        else:
            file_format = filename.split(".")[-1].upper() if filename and "." in filename else "UNKNOWN"

        # Determine color channels
        channel_map = {"1": 1, "L": 1, "P": 1, "RGB": 3, "RGBA": 4, "CMYK": 4, "YCbCr": 3, "I": 1, "F": 1}
        channels = channel_map.get(color_mode, len(pil_img.getbands()))

        # Aspect ratio & orientation
        if width == height:
            orientation = "Square"
        elif height > width:
            orientation = "Portrait"
        else:
            orientation = "Landscape"

        ratio_val = f"{(width / max(height, 1)):.2f}:1"

        # Heuristic effective PPI: Standard clinical pad is approx 6 inches wide in portrait, 8.5 inches in landscape.
        # This is NOT physical EXIF DPI; it is a heuristic pixel density estimate from assumed pad dimensions.
        pad_width_inches = 6.0 if orientation == "Portrait" else 8.5
        raw_ppi = int(round(width / pad_width_inches))
        effective_ppi = max(72, min(1200, raw_ppi))

        # exif_orientation was already extracted safely from raw_pil before transposition

    return ImageMetadata(
        width=width,
        height=height,
        channels=channels,
        color_mode=color_mode,
        file_format=file_format,
        file_size_bytes=file_size_bytes,
        aspect_ratio=ratio_val,
        orientation=orientation,
        exif_orientation=exif_orientation,
        original_sha256=sha256_hash,
        pixel_area=width * height,
        effective_ppi=effective_ppi,
    )
