"""
Phase 4: Image Preprocessing Service
Unified facade coordinating ingestion validation, quality assessment,
image transformation pipeline, artifact persistence, and public URL generation.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image

from .config import PreprocessingConfig
from .metadata import ImageMetadata
from .pipeline import PrescriptionPreprocessingPipeline, PreprocessingResult
from .quality import QualityReport, ImageQualityAssessor
from .validator import ImageIngestionValidator, ImageValidationError
from .artifacts import PreprocessingArtifactManager, PreprocessingRunManifest
from ..schemas.error import ErrorCode


class ImagePreprocessingService:
    """
    Central orchestration service for Phase 4 image quality and preprocessing.
    """
    def __init__(
        self,
        config: Optional[PreprocessingConfig] = None,
        base_runs_dir: Optional[Path] = None,
        public_preprocessed_dir: Optional[Path] = None,
    ):
        self.config = config or PreprocessingConfig()
        self.validator = ImageIngestionValidator(self.config)
        self.quality_assessor = ImageQualityAssessor(self.config)
        self.pipeline = PrescriptionPreprocessingPipeline(self.config)
        self.artifact_manager = PreprocessingArtifactManager(
            base_runs_dir=base_runs_dir,
            public_preprocessed_dir=public_preprocessed_dir,
        )

    def validate_and_assess(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
    ) -> Tuple[ImageMetadata, QualityReport]:
        """
        Fast diagnostic pass: validates file structure and evaluates optical quality.
        Does not execute full image enhancement pipeline.
        """
        pil_img, metadata = self.validator.validate_and_load(image_bytes, filename=filename)
        quality_report = self.quality_assessor.assess_quality(pil_img, metadata)
        return metadata, quality_report

    def process_and_store(
        self,
        image_bytes: bytes,
        filename: Optional[str],
        prescription_id: str,
        original_image_path: Optional[Path] = None,
        reject_insufficient_quality: bool = True,
    ) -> Tuple[PreprocessingResult, PreprocessingRunManifest, str]:
        """
        Executes full preprocessing pipeline and persists derived artifacts to disk.

        Args:
            image_bytes: Raw original prescription file bytes.
            filename: Original file name.
            prescription_id: Unique accession identifier.
            original_image_path: Path to original image on disk (for immutability check).
            reject_insufficient_quality: If True, raises ImageValidationError when quality is 'insufficient'.

        Returns:
            (preprocessing_result, run_manifest, primary_processed_image_url)
        """
        # Execute pipeline
        result = self.pipeline.process(image_bytes=image_bytes, filename=filename)

        # Enforce quality gate
        if reject_insufficient_quality and result.quality_report.overall_status == "insufficient":
            raise ImageValidationError(
                code=ErrorCode.IMAGE_QUALITY_INSUFFICIENT,
                message=(
                    f"Prescription image quality is insufficient for clinical interpretation: "
                    f"{'; '.join(result.quality_report.issues)}"
                ),
                status_code=422,
                stage="image_quality_assessment",
                retryable=True,
                details={
                    "quality_status": result.quality_report.overall_status,
                    "heuristic_score": result.quality_report.heuristic_quality_score,
                    "issues": result.quality_report.issues,
                    "recommendations": result.quality_report.recommendations,
                    "metrics": result.quality_report.metrics,
                },
            )

        # Persist derived artifacts
        manifest, _ = self.artifact_manager.persist_run(
            prescription_id=prescription_id,
            result=result,
            original_image_path=original_image_path,
        )

        # Build public HTTP URL for primary derived image (served via FastAPI static mount)
        primary_name = manifest.primary_artifact_type
        primary_processed_url = f"/uploads/preprocessed/{prescription_id}/{primary_name}.png"

        return result, manifest, primary_processed_url

    def get_run_manifest(self, prescription_id: str) -> Optional[PreprocessingRunManifest]:
        """Retrieves an existing preprocessing run manifest by accession ID."""
        return self.artifact_manager.get_run_manifest(prescription_id)
