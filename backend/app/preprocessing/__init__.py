"""
Phase 4: Image Preprocessing & Quality Assessment Package
Exports core domain models, validators, pipelines, and services.
"""

from .config import PreprocessingConfig, QualityThresholds
from .metadata import ImageMetadata, extract_image_metadata
from .validator import ImageIngestionValidator, ImageValidationError
from .quality import (
    ImageQualityAssessor,
    QualityReport,
    ResolutionMetric,
    BlurMetric,
    BrightnessMetric,
    ContrastMetric,
    NoiseMetric,
    SkewMetric,
    IlluminationMetric,
    ClippingMetric,
)
from .pipeline import PrescriptionPreprocessingPipeline, PreprocessingResult
from .artifacts import (
    PreprocessingArtifactManager,
    PreprocessingRunManifest,
    PreprocessedArtifactRecord,
)
from .service import ImagePreprocessingService

__all__ = [
    "PreprocessingConfig",
    "QualityThresholds",
    "ImageMetadata",
    "extract_image_metadata",
    "ImageIngestionValidator",
    "ImageValidationError",
    "ImageQualityAssessor",
    "QualityReport",
    "ResolutionMetric",
    "BlurMetric",
    "BrightnessMetric",
    "ContrastMetric",
    "NoiseMetric",
    "SkewMetric",
    "IlluminationMetric",
    "ClippingMetric",
    "PrescriptionPreprocessingPipeline",
    "PreprocessingResult",
    "PreprocessingArtifactManager",
    "PreprocessingRunManifest",
    "PreprocessedArtifactRecord",
    "ImagePreprocessingService",
]
