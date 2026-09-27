"""
Phase 4: Image Quality Assessment
Computes deterministic optical and textural quality metrics for prescription documents:
sharpness/blur (Laplacian variance), exposure/brightness, RMS contrast, noise ratio,
skew angle, spatial illumination unevenness, and pixel clipping.
"""

from typing import Dict, List, Literal, Optional
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field
from scipy.signal import convolve2d
from scipy.ndimage import median_filter, rotate

from .config import PreprocessingConfig, QualityThresholds
from .metadata import ImageMetadata


class ResolutionMetric(BaseModel):
    width: int
    height: int
    pixel_area: int
    effective_ppi: int
    is_sufficient: bool
    status: Literal["optimal", "acceptable", "insufficient"]


class BlurMetric(BaseModel):
    variance_of_laplacian: float = Field(..., description="High-frequency edge response variance")
    is_blurry: bool
    is_fatal: bool
    status: Literal["sharp", "moderate_blur", "severe_blur"]


class BrightnessMetric(BaseModel):
    mean_luminance: float = Field(..., ge=0.0, le=255.0, description="Mean grayscale intensity [0-255]")
    is_underexposed: bool
    is_overexposed: bool
    status: Literal["normal", "underexposed", "overexposed"]


class ContrastMetric(BaseModel):
    rms_contrast: float = Field(..., description="Grayscale pixel standard deviation")
    is_low_contrast: bool
    status: Literal["good", "moderate", "poor"]


class NoiseMetric(BaseModel):
    noise_ratio: float = Field(..., ge=0.0, le=1.0, description="Median filter residual noise ratio")
    is_noisy: bool
    status: Literal["clean", "moderate_noise", "noisy"]


class SkewMetric(BaseModel):
    estimated_angle_deg: float = Field(..., description="Detected text alignment skew angle in degrees")
    is_skewed: bool
    status: Literal["aligned", "moderate_skew", "severe_skew"]


class IlluminationMetric(BaseModel):
    unevenness_score: float = Field(..., description="Spatial 3x3 block luminance variation coefficient")
    has_shadows: bool
    status: Literal["uniform", "uneven_lighting"]


class ClippingMetric(BaseModel):
    black_clipping_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of crushed black pixels (<5)")
    white_clipping_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of saturated white pixels (>250)")
    is_clipped: bool
    status: Literal["normal", "clipped"]


class QualityReport(BaseModel):
    """
    Standardized result contract for prescription image quality evaluation.
    Clearly states that the heuristic score is an engineering index, not an AI confidence metric.
    """
    overall_status: Literal["acceptable", "degraded_but_usable", "insufficient"] = Field(
        ..., description="Deterministic quality tri-state decision"
    )
    heuristic_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Engineering optical quality index [0.0 - 1.0]"
    )
    score_explanation: str = Field(
        "Heuristic quality index computed from weighted optical metrics. "
        "Engineering heuristic only; does NOT represent model inference confidence or clinical validation.",
        description="Clarification of score semantics"
    )
    metrics: Dict[str, dict] = Field(..., description="Granular metric breakdowns")
    issues: List[str] = Field(default_factory=list, description="Critical defects causing insufficient status")
    warnings: List[str] = Field(default_factory=list, description="Degradation warnings that may affect OCR precision")
    recommendations: List[str] = Field(default_factory=list, description="Actionable operator guidance")


class ImageQualityAssessor:
    """
    Evaluates optical document quality against engineering heuristics.
    """
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.thresholds: QualityThresholds = self.config.thresholds

    def assess_quality(self, pil_image: Image.Image, metadata: ImageMetadata) -> QualityReport:
        """
        Executes complete quality metric suite on a normalized PIL image and returns a typed QualityReport.
        """
        # Convert to single-channel floating-point grayscale
        gray_pil = pil_image.convert("L")
        gray_array = np.array(gray_pil, dtype=np.float32)
        h, w = gray_array.shape

        # ----------------------------------------------------------------------
        # 1. Resolution Metric (Heuristic Pixel Density)
        # ----------------------------------------------------------------------
        ppi = metadata.effective_ppi
        res_sufficient = (metadata.width >= self.thresholds.min_width and metadata.height >= self.thresholds.min_height)
        if ppi >= self.thresholds.nominal_dpi:
            res_status = "optimal"
        elif ppi >= self.thresholds.min_dpi:
            res_status = "acceptable"
        else:
            res_status = "insufficient"

        resolution_metric = ResolutionMetric(
            width=metadata.width,
            height=metadata.height,
            pixel_area=metadata.pixel_area,
            effective_ppi=ppi,
            is_sufficient=res_sufficient,
            status=res_status,
        )

        # ----------------------------------------------------------------------
        # 2. Blur / Sharpness Metric (Variance of Laplacian)
        # ----------------------------------------------------------------------
        lap_kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
        laplacian = convolve2d(gray_array, lap_kernel, mode="same", boundary="symm")
        lap_var = float(np.var(laplacian))

        is_fatal_blur = lap_var < self.thresholds.blur_insufficient_threshold
        is_blurry = lap_var < self.thresholds.blur_degraded_threshold

        if is_fatal_blur:
            blur_status = "severe_blur"
        elif is_blurry:
            blur_status = "moderate_blur"
        else:
            blur_status = "sharp"

        blur_metric = BlurMetric(
            variance_of_laplacian=round(lap_var, 2),
            is_blurry=is_blurry,
            is_fatal=is_fatal_blur,
            status=blur_status,
        )

        # ----------------------------------------------------------------------
        # 3. Brightness / Exposure Metric
        # ----------------------------------------------------------------------
        mean_lum = float(np.mean(gray_array))
        is_under = mean_lum < self.thresholds.degraded_min_brightness
        is_fatal_under = mean_lum < self.thresholds.min_brightness
        is_fatal_over = mean_lum > self.thresholds.max_brightness

        if is_fatal_under or is_under:
            brightness_status = "underexposed"
        elif is_fatal_over:
            brightness_status = "overexposed"
        else:
            brightness_status = "normal"

        brightness_metric = BrightnessMetric(
            mean_luminance=round(mean_lum, 2),
            is_underexposed=is_under,
            is_overexposed=is_fatal_over,
            status=brightness_status,
        )

        # ----------------------------------------------------------------------
        # 4. Contrast Metric (RMS Grayscale Standard Deviation)
        # ----------------------------------------------------------------------
        rms_contrast = float(np.std(gray_array))
        is_low_contrast = rms_contrast < self.thresholds.degraded_min_contrast
        is_fatal_low_contrast = rms_contrast < self.thresholds.min_contrast

        if is_fatal_low_contrast:
            contrast_status = "poor"
        elif is_low_contrast:
            contrast_status = "moderate"
        else:
            contrast_status = "good"

        contrast_metric = ContrastMetric(
            rms_contrast=round(rms_contrast, 2),
            is_low_contrast=is_low_contrast,
            status=contrast_status,
        )

        # ----------------------------------------------------------------------
        # 5. High-Frequency Noise Metric (Median Filter Residual)
        # ----------------------------------------------------------------------
        # Run median filter on downsampled version for speed if large
        if max(h, w) > 1200:
            scale = 1200.0 / max(h, w)
            small_w, small_h = int(w * scale), int(h * scale)
            small_gray = np.array(gray_pil.resize((small_w, small_h), Image.Resampling.BILINEAR), dtype=np.float32)
        else:
            small_gray = gray_array

        med = median_filter(small_gray, size=self.thresholds.denoise_kernel_size if hasattr(self.thresholds, 'denoise_kernel_size') else 3)
        noise_ratio = float(np.mean(np.abs(small_gray - med))) / 255.0
        is_noisy = noise_ratio > self.thresholds.max_noise_ratio

        noise_metric = NoiseMetric(
            noise_ratio=round(noise_ratio, 4),
            is_noisy=is_noisy,
            status="noisy" if is_noisy else ("moderate_noise" if noise_ratio > 0.04 else "clean"),
        )

        # ----------------------------------------------------------------------
        # 6. Skew Angle Estimation (Projection Profile Variance Sweep)
        # ----------------------------------------------------------------------
        skew_angle = self._estimate_skew_angle(gray_array)
        abs_skew = abs(skew_angle)
        is_skewed = abs_skew >= self.thresholds.degraded_skew_angle_deg
        is_fatal_skew = abs_skew > self.thresholds.max_skew_angle_deg

        if is_fatal_skew:
            skew_status = "severe_skew"
        elif is_skewed:
            skew_status = "moderate_skew"
        else:
            skew_status = "aligned"

        skew_metric = SkewMetric(
            estimated_angle_deg=round(skew_angle, 2),
            is_skewed=is_skewed,
            status=skew_status,
        )

        # ----------------------------------------------------------------------
        # 7. Spatial Illumination Unevenness Metric (3x3 Grid)
        # ----------------------------------------------------------------------
        block_means = []
        for r in range(3):
            for c in range(3):
                blk = gray_array[r * h // 3 : (r + 1) * h // 3, c * w // 3 : (c + 1) * w // 3]
                block_means.append(np.mean(blk))
        illum_uneven = float(np.std(block_means) / (np.mean(block_means) + 1e-5))
        has_shadows = illum_uneven > self.thresholds.max_uneven_illumination

        illumination_metric = IlluminationMetric(
            unevenness_score=round(illum_uneven, 4),
            has_shadows=has_shadows,
            status="uneven_lighting" if has_shadows else "uniform",
        )

        # ----------------------------------------------------------------------
        # 8. Pixel Clipping Metric
        # ----------------------------------------------------------------------
        total_pixels = float(h * w)
        black_clip = float(np.sum(gray_array < 5.0)) / total_pixels
        white_clip = float(np.sum(gray_array > 250.0)) / total_pixels
        is_clipped = (
            black_clip > self.thresholds.max_black_clipping_fraction
            or white_clip > self.thresholds.max_white_clipping_fraction
        )

        clipping_metric = ClippingMetric(
            black_clipping_fraction=round(black_clip, 4),
            white_clipping_fraction=round(white_clip, 4),
            is_clipped=is_clipped,
            status="clipped" if is_clipped else "normal",
        )

        # ----------------------------------------------------------------------
        # 9. Decision Logic: State Transitions (acceptable / degraded / insufficient)
        # ----------------------------------------------------------------------
        issues: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        # Check Fatal Issues -> insufficient
        if is_fatal_blur:
            issues.append(f"Severe optical defocus or motion blur detected (sharpness: {lap_var:.1f} < threshold {self.thresholds.blur_insufficient_threshold}).")
            recommendations.append("Hold the camera steady or adjust autofocus to capture sharp cursive stroke details.")
        if is_fatal_under:
            issues.append(f"Severe underexposure / dark image detected (mean luminance: {mean_lum:.1f} < threshold {self.thresholds.min_brightness}).")
            recommendations.append("Retake prescription photo under direct overhead illumination.")
        if is_fatal_over:
            issues.append(f"Severe overexposure / glare detected (mean luminance: {mean_lum:.1f} > threshold {self.thresholds.max_brightness}).")
            recommendations.append("Reduce camera flash reflection or glare on glossy prescription paper.")
        if is_fatal_low_contrast:
            issues.append(f"Ink-to-paper contrast is too faint for legible separation (RMS: {rms_contrast:.1f} < threshold {self.thresholds.min_contrast}).")
            recommendations.append("Ensure doctor ink strokes are clearly visible against the paper background.")
        if is_fatal_skew:
            issues.append(f"Extreme document skew angle detected ({skew_angle:.1f}° > {self.thresholds.max_skew_angle_deg}°).")
            recommendations.append("Align the camera parallel to the prescription pad edges.")
        if black_clip > self.thresholds.max_black_clipping_fraction:
            issues.append(f"Excessive black pixel saturation ({black_clip*100:.1f}% crushed pixels).")
            recommendations.append("Avoid harsh shadows or digital black level clipping.")

        # Check Degradation Warnings -> degraded_but_usable
        if is_blurry and not is_fatal_blur:
            warnings.append(f"Moderate stroke blur detected (sharpness: {lap_var:.1f}). Minor posology details may require verification.")
        if is_under and not is_fatal_under:
            warnings.append(f"Low ambient lighting detected (mean luminance: {mean_lum:.1f}). Applying illumination normalization.")
        if is_low_contrast and not is_fatal_low_contrast:
            warnings.append(f"Faint penmanship detected (RMS contrast: {rms_contrast:.1f}). Applying contrast stretching.")
        if is_skewed and not is_fatal_skew:
            warnings.append(f"Document skew detected ({skew_angle:.1f}°). Applying automatic rotation correction.")
        if has_shadows:
            warnings.append(f"Uneven lighting or localized shadow detected (coefficient: {illum_uneven:.3f}). Applying background division.")
        if is_noisy:
            warnings.append(f"High-frequency sensor noise detected (ratio: {noise_ratio:.4f}). Applying median stroke filter.")

        # Determine Tri-State
        if len(issues) > 0:
            overall_status: Literal["acceptable", "degraded_but_usable", "insufficient"] = "insufficient"
        elif len(warnings) > 0:
            overall_status = "degraded_but_usable"
        else:
            overall_status = "acceptable"

        # ----------------------------------------------------------------------
        # 10. Heuristic Quality Index Calculation [0.0 - 1.0]
        # (Explicitly documented as an engineering heuristic, NOT model confidence)
        # ----------------------------------------------------------------------
        # Component scores
        blur_subscore = min(1.0, max(0.0, (lap_var - 25.0) / (200.0 - 25.0)))
        brightness_subscore = 1.0 - min(1.0, abs(mean_lum - 200.0) / 160.0)
        contrast_subscore = min(1.0, max(0.0, (rms_contrast - 10.0) / 30.0))
        noise_subscore = max(0.0, 1.0 - (noise_ratio / 0.10))
        skew_subscore = max(0.0, 1.0 - (abs_skew / 15.0))
        illum_subscore = max(0.0, 1.0 - (illum_uneven / 0.35))

        # Weighted combination
        raw_score = (
            0.35 * blur_subscore
            + 0.20 * contrast_subscore
            + 0.15 * brightness_subscore
            + 0.10 * noise_subscore
            + 0.10 * skew_subscore
            + 0.10 * illum_subscore
        )

        if overall_status == "insufficient":
            heuristic_score = round(min(raw_score, 0.39), 2)
        elif overall_status == "degraded_but_usable":
            heuristic_score = round(max(0.40, min(raw_score, 0.79)), 2)
        else:
            heuristic_score = round(max(0.80, min(raw_score, 1.0)), 2)

        return QualityReport(
            overall_status=overall_status,
            heuristic_quality_score=heuristic_score,
            metrics={
                "resolution": resolution_metric.model_dump(),
                "blur": blur_metric.model_dump(),
                "brightness": brightness_metric.model_dump(),
                "contrast": contrast_metric.model_dump(),
                "noise": noise_metric.model_dump(),
                "skew": skew_metric.model_dump(),
                "illumination": illumination_metric.model_dump(),
                "clipping": clipping_metric.model_dump(),
            },
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
        )

    def _estimate_skew_angle(self, gray: np.ndarray) -> float:
        """
        Estimates document text line skew angle via projection profile variance maximization.
        Runs over downsampled inverted image for speed and numerical determinism.
        """
        h, w = gray.shape
        scale = 400.0 / max(h, w)
        if scale < 1.0:
            small_pil = Image.fromarray(gray.astype(np.uint8)).resize(
                (int(w * scale), int(h * scale)), Image.Resampling.BILINEAR
            )
            small_gray = np.array(small_pil, dtype=np.float32)
        else:
            small_gray = gray

        # Invert so ink strokes are positive signal against zero background
        inv = 255.0 - small_gray

        best_var = -1.0
        best_angle = 0.0

        search_range = self.config.deskew_search_max_angle
        step = self.config.deskew_search_step

        for angle in np.arange(-search_range, search_range + step, step):
            rot = rotate(inv, angle, reshape=False, order=1, mode="constant", cval=0.0)
            proj = np.sum(rot, axis=1)
            var = float(np.var(proj))
            if var > best_var:
                best_var = var
                best_angle = float(angle)

        return best_angle
