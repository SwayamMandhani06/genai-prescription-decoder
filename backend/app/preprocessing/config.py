"""
Phase 4: Image Preprocessing & Quality Assessment Configuration
Defines traceable, versioned configuration schemas for image validation,
quality metric thresholds, and preprocessing pipeline execution parameters.
"""

import hashlib
import json
from typing import Literal, Optional
from pydantic import BaseModel, Field


class QualityThresholds(BaseModel):
    """
    Engineering heuristic thresholds for prescription document optical quality.
    Documented as engineering heuristics; not claimed as clinical or universal constants.
    """
    # Dimensional and Density Bounds
    min_width: int = Field(150, description="Minimum acceptable image width in pixels")
    min_height: int = Field(150, description="Minimum acceptable image height in pixels")
    max_dimension: int = Field(8000, description="Maximum permitted width or height before rejection")
    min_dpi: int = Field(150, description="Minimum effective PPI threshold for clinical interpretation (heuristic pixel density)")
    nominal_dpi: int = Field(300, description="Nominal benchmark PPI for standard prescription pad pixel density")

    # Sharpness / Blur (Variance of Laplacian)
    blur_insufficient_threshold: float = Field(
        25.0,
        description="Variance of Laplacian below which severe optical/motion blur renders strokes illegible"
    )
    blur_degraded_threshold: float = Field(
        75.0,
        description="Variance of Laplacian below which moderate blur warning is flagged"
    )

    # Luminance / Exposure (0 - 255)
    min_brightness: float = Field(
        40.0,
        description="Mean grayscale luminance below which image is fatally underexposed"
    )
    max_brightness: float = Field(
        253.0,
        description="Mean grayscale luminance above which document is severely overexposed/washed out"
    )
    degraded_min_brightness: float = Field(
        70.0,
        description="Mean luminance below which low-light warning is flagged"
    )

    # Contrast (RMS Grayscale Standard Deviation)
    min_contrast: float = Field(
        7.0,
        description="Minimum RMS contrast below which ink strokes cannot be differentiated from background"
    )
    degraded_min_contrast: float = Field(
        20.0,
        description="RMS contrast below which low-contrast warning is flagged"
    )

    # High-Frequency Noise
    max_noise_ratio: float = Field(
        0.08,
        description="Maximum high-frequency residual noise ratio before degradation warning"
    )

    # Skew
    max_skew_angle_deg: float = Field(
        15.0,
        description="Maximum allowable text skew angle in degrees"
    )
    degraded_skew_angle_deg: float = Field(
        5.0,
        description="Skew angle above which alignment correction is applied"
    )

    # Spatial Illumination Unevenness (3x3 grid standard deviation / mean)
    max_uneven_illumination: float = Field(
        0.25,
        description="Illumination unevenness ratio above which shadowing is flagged"
    )

    # Pixel Saturation / Clipping
    max_black_clipping_fraction: float = Field(
        0.25,
        description="Maximum allowable fraction of completely crushed black pixels (<5)"
    )
    max_white_clipping_fraction: float = Field(
        0.92,
        description="Maximum allowable fraction of completely clipped white pixels (>250)"
    )


class PreprocessingConfig(BaseModel):
    """
    Versioned, traceable configuration specification for the Phase 4 preprocessing pipeline.
    """
    id: str = Field("p04_standard_v1", description="Unique configuration release identifier")
    version: str = Field("1.0.0", description="Semantic configuration version")
    status: Literal["implemented", "prospective"] = Field("implemented", description="Current implementation state")
    description: str = Field(
        "Standard deterministic preprocessing pipeline: orientation normalization, illumination correction, "
        "median denoising, percentile contrast enhancement, discrete deskewing, and Sauvola thresholding.",
        description="Operational summary of configuration"
    )

    # Pipeline Stage Toggles
    enable_orientation_correction: bool = Field(True, description="Apply EXIF orientation transposition")
    enable_grayscale: bool = Field(True, description="Generate 8-bit single-channel luminance representation")
    enable_illumination_correction: bool = Field(True, description="Apply Gaussian background division normalization")
    enable_denoising: bool = Field(True, description="Apply stroke-preserving median smoothing")
    enable_contrast_enhancement: bool = Field(True, description="Apply percentile contrast stretching")
    enable_deskew: bool = Field(True, description="Apply text-line alignment rotation")
    enable_adaptive_threshold: bool = Field(True, description="Generate Sauvola local adaptive binarized representation")

    # Working Resolution
    max_processing_dimension: int = Field(2400, description="Downscale boundary for processing efficiency")

    # Algorithm Hyperparameters
    illumination_sigma: float = Field(35.0, description="Gaussian kernel standard deviation for background estimation")
    denoise_kernel_size: int = Field(3, description="Odd kernel size for median filtering (3x3)")
    contrast_percentile_low: float = Field(1.0, description="Lower percentile cutoff for contrast stretching")
    contrast_percentile_high: float = Field(99.0, description="Upper percentile cutoff for contrast stretching")
    deskew_search_max_angle: float = Field(10.0, description="Maximum angle sweep range for skew search [-angle, +angle]")
    deskew_search_step: float = Field(0.5, description="Search resolution in degrees for skew detection")
    deskew_min_correction_angle: float = Field(0.5, description="Minimum skew angle required to trigger actual rotation")
    sauvola_window_size: int = Field(25, description="Odd local window dimension for Sauvola thresholding")
    sauvola_k: float = Field(0.2, description="Sauvola dynamic threshold control factor")
    sauvola_r: float = Field(128.0, description="Dynamic range divisor for standard deviation in Sauvola")

    # Nested Quality Evaluation Thresholds
    thresholds: QualityThresholds = Field(default_factory=QualityThresholds)

    def compute_config_hash(self) -> str:
        """
        Computes a deterministic SHA-256 fingerprint of the configuration parameters.
        Ensures complete reproducibility and audit traceability across preprocessing runs.
        """
        config_dict = self.model_dump()
        serialized = json.dumps(config_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
