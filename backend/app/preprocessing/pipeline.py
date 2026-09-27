"""
Phase 4: Prescription Preprocessing Pipeline
Executes modular, deterministic document transformations:
EXIF orientation correction, grayscale conversion, Gaussian background illumination normalization,
median stroke denoising, percentile contrast enhancement, discrete deskewing, and Sauvola thresholding.
Guarantees that the original prescription image is NEVER modified.
"""

import io
from typing import Dict, Optional, Tuple
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, median_filter, rotate, uniform_filter

from .config import PreprocessingConfig
from .metadata import ImageMetadata
from .quality import QualityReport, ImageQualityAssessor
from .validator import ImageIngestionValidator


class PreprocessingResult:
    """
    Container for the outputs of the preprocessing pipeline.
    Maintains strict separation between the original image and derived representations.
    """
    def __init__(
        self,
        original_image_bytes: bytes,
        original_metadata: ImageMetadata,
        quality_report: QualityReport,
        config: PreprocessingConfig,
        derived_images: Dict[str, Image.Image],
        primary_processed_image: Image.Image,
        deskew_applied_angle: float = 0.0,
    ):
        self.original_image_bytes = original_image_bytes
        self.original_metadata = original_metadata
        self.quality_report = quality_report
        self.config = config
        self.derived_images = derived_images
        self.primary_processed_image = primary_processed_image
        self.deskew_applied_angle = deskew_applied_angle


class PrescriptionPreprocessingPipeline:
    """
    Modular, deterministic image preprocessing pipeline for handwritten prescription documents.
    """
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.validator = ImageIngestionValidator(self.config)
        self.quality_assessor = ImageQualityAssessor(self.config)

    def process(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
    ) -> PreprocessingResult:
        """
        Executes the full preprocessing pipeline on input bytes.
        Returns PreprocessingResult containing the untouched original bytes and derived artifacts.
        """
        # ----------------------------------------------------------------------
        # 1. Validation & Color Mode Normalization (EXIF Transposition)
        # ----------------------------------------------------------------------
        normalized_pil, metadata = self.validator.validate_and_load(
            image_bytes=image_bytes,
            filename=filename,
        )

        # ----------------------------------------------------------------------
        # 2. Quality Assessment
        # ----------------------------------------------------------------------
        quality_report = self.quality_assessor.assess_quality(
            pil_image=normalized_pil,
            metadata=metadata,
        )

        # ----------------------------------------------------------------------
        # 3. Grayscale Representation
        # ----------------------------------------------------------------------
        gray_pil = normalized_pil.convert("L")
        gray_array = np.array(gray_pil, dtype=np.float32)

        derived_images: Dict[str, Image.Image] = {}
        if self.config.enable_grayscale:
            derived_images["grayscale"] = gray_pil.copy()

        # ----------------------------------------------------------------------
        # 4. Illumination Correction (Gaussian Background Division)
        # ----------------------------------------------------------------------
        if self.config.enable_illumination_correction:
            sigma = self.config.illumination_sigma
            bg = gaussian_filter(gray_array, sigma=sigma)
            bg = np.maximum(bg, 10.0)  # Avoid divide by zero
            # Normalize paper background to ~220
            norm_array = (gray_array / bg) * 220.0
            norm_array = np.clip(norm_array, 0.0, 255.0)
            working_array = norm_array
            derived_images["normalized"] = Image.fromarray(norm_array.astype(np.uint8))
        else:
            working_array = gray_array.copy()

        # ----------------------------------------------------------------------
        # 5. Denoising (Median Stroke Smoothing)
        # ----------------------------------------------------------------------
        if self.config.enable_denoising:
            ksize = self.config.denoise_kernel_size
            denoised_array = median_filter(working_array, size=ksize)
            working_array = denoised_array
            derived_images["denoised"] = Image.fromarray(denoised_array.astype(np.uint8))

        # ----------------------------------------------------------------------
        # 6. Contrast Enhancement (Percentile Stretching)
        # ----------------------------------------------------------------------
        if self.config.enable_contrast_enhancement:
            p_low = self.config.contrast_percentile_low
            p_high = self.config.contrast_percentile_high
            val_low, val_high = np.percentile(working_array, (p_low, p_high))
            if val_high > val_low:
                enhanced_array = np.clip((working_array - val_low) / (val_high - val_low) * 255.0, 0.0, 255.0)
            else:
                enhanced_array = working_array
            working_array = enhanced_array
            derived_images["enhanced"] = Image.fromarray(enhanced_array.astype(np.uint8))

        # ----------------------------------------------------------------------
        # 7. Deskew (Angle Rotation if Justified)
        # ----------------------------------------------------------------------
        skew_metric = quality_report.metrics.get("skew", {})
        detected_angle = float(skew_metric.get("estimated_angle_deg", 0.0))
        deskew_applied_angle = 0.0

        if self.config.enable_deskew and abs(detected_angle) >= self.config.deskew_min_correction_angle:
            # Rotate working array by detected angle with white background fill
            deskewed_pil = Image.fromarray(working_array.astype(np.uint8)).rotate(
                -detected_angle,  # Reverse detected angle to align straight
                resample=Image.Resampling.BILINEAR,
                expand=False,
                fillcolor=255,
            )
            working_array = np.array(deskewed_pil, dtype=np.float32)
            derived_images["deskewed"] = deskewed_pil
            deskew_applied_angle = detected_angle

        # ----------------------------------------------------------------------
        # 8. Adaptive Thresholding (Sauvola Local Dynamic Binarization)
        # ----------------------------------------------------------------------
        if self.config.enable_adaptive_threshold:
            thresholded_array = self._sauvola_threshold(
                gray=working_array.astype(np.uint8),
                window_size=self.config.sauvola_window_size,
                k=self.config.sauvola_k,
                r=self.config.sauvola_r,
            )
            derived_images["thresholded"] = Image.fromarray(thresholded_array)

        # Primary processed image for downstream OCR (enhanced grayscale)
        primary_image = derived_images.get("enhanced", derived_images.get("normalized", gray_pil))

        return PreprocessingResult(
            original_image_bytes=image_bytes,
            original_metadata=metadata,
            quality_report=quality_report,
            config=self.config,
            derived_images=derived_images,
            primary_processed_image=primary_image,
            deskew_applied_angle=deskew_applied_angle,
        )

    def _sauvola_threshold(
        self,
        gray: np.ndarray,
        window_size: int = 25,
        k: float = 0.2,
        r: float = 128.0,
    ) -> np.ndarray:
        """
        Fast Sauvola local adaptive thresholding using 2D uniform filter box means.
        Produces a crisp binary image: 0 for ink strokes, 255 for paper background.
        """
        gray_f = gray.astype(np.float32)
        mean = uniform_filter(gray_f, size=window_size)
        mean_sq = uniform_filter(gray_f ** 2, size=window_size)
        std = np.sqrt(np.maximum(mean_sq - mean ** 2, 0.0))
        threshold = mean * (1.0 + k * (std / r - 1.0))
        binary = np.where(gray_f > threshold, 255, 0).astype(np.uint8)
        return binary
