"""
Phase 4: Preprocessing Artifact Management
Handles persistent storage of derived image representations, metadata descriptors,
and cryptographic manifests in `data/processed/preprocessing_runs/<prescription_id>/`.
Guarantees and formally verifies the original image immutability invariant.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .config import PreprocessingConfig
from .metadata import ImageMetadata
from .pipeline import PreprocessingResult
from .quality import QualityReport


class PreprocessedArtifactRecord(BaseModel):
    """
    Describes an individual derived image artifact generated during preprocessing.
    """
    type: str = Field(..., description="Semantic artifact type: grayscale, normalized, denoised, enhanced, deskewed, thresholded")
    relative_path: str = Field(..., description="Path relative to the repository or run directory")
    file_size_bytes: int = Field(..., description="File size in bytes")
    sha256: str = Field(..., description="Cryptographic SHA-256 fingerprint of the derived artifact")
    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")


class PreprocessingRunManifest(BaseModel):
    """
    Formal run manifest conforming strictly to Phase 4 specification.
    """
    prescription_id: str = Field(..., description="Unique accession / prescription tracking ID")
    source_image_sha256: str = Field(..., description="Original immutable source image SHA-256 hash")
    source_image_filename: Optional[str] = Field(None, description="Original source image filename")
    preprocessing_config_id: str = Field(..., description="Configuration identifier (e.g. 'p04_standard_v1')")
    preprocessing_config_hash: str = Field(..., description="Deterministic fingerprint of execution configuration")
    status: str = Field("completed", description="Execution status of preprocessing run")
    quality_status: str = Field(..., description="Assessed quality status (acceptable, degraded_but_usable, insufficient)")
    heuristic_quality_score: float = Field(..., description="Engineering heuristic quality score [0.0 - 1.0]")
    deskew_applied_angle_deg: float = Field(0.0, description="Corrective deskew rotation applied")
    primary_artifact_type: str = Field("enhanced", description="Primary derived artifact recommended for downstream OCR")
    artifacts: List[PreprocessedArtifactRecord] = Field(default_factory=list, description="List of generated derived artifacts")


class PreprocessingArtifactManager:
    """
    Manages filesystem serialization and cryptographic validation of derived preprocessing artifacts.
    """
    def __init__(
        self,
        base_runs_dir: Optional[Path] = None,
        public_preprocessed_dir: Optional[Path] = None,
    ):
        self.base_runs_dir = base_runs_dir or Path("data/processed/preprocessing_runs")
        self.public_preprocessed_dir = public_preprocessed_dir or Path("backend/uploads/preprocessed")

        self.base_runs_dir.mkdir(parents=True, exist_ok=True)
        self.public_preprocessed_dir.mkdir(parents=True, exist_ok=True)

    def persist_run(
        self,
        prescription_id: str,
        result: PreprocessingResult,
        original_image_path: Optional[Path] = None,
    ) -> Tuple[PreprocessingRunManifest, Path]:
        """
        Saves all derived image representations and JSON manifests to disk.
        Formally verifies that original image bytes and hash were NOT modified.
        """
        # 1. Enforce and verify immutability invariant
        current_source_hash = hashlib.sha256(result.original_image_bytes).hexdigest()
        if current_source_hash != result.original_metadata.original_sha256:
            raise RuntimeError(
                f"IMMUTABILITY VIOLATION: Source image bytes mutated during preprocessing! "
                f"Expected {result.original_metadata.original_sha256}, got {current_source_hash}"
            )

        if original_image_path and original_image_path.exists():
            with open(original_image_path, "rb") as f:
                disk_bytes = f.read()
            disk_hash = hashlib.sha256(disk_bytes).hexdigest()
            if disk_hash != result.original_metadata.original_sha256:
                raise RuntimeError(
                    f"IMMUTABILITY VIOLATION: Original file on disk '{original_image_path}' was modified! "
                    f"Expected {result.original_metadata.original_sha256}, got {disk_hash}"
                )

        # 2. Setup run-specific output directories
        run_dir = self.base_runs_dir / prescription_id
        run_dir.mkdir(parents=True, exist_ok=True)

        public_run_dir = self.public_preprocessed_dir / prescription_id
        public_run_dir.mkdir(parents=True, exist_ok=True)

        # 3. Save derived image artifacts
        artifact_records: List[PreprocessedArtifactRecord] = []

        for name, pil_img in result.derived_images.items():
            filename = f"{name}.png"
            target_path = run_dir / filename
            public_path = public_run_dir / filename

            # Save in research run directory
            pil_img.save(target_path, format="PNG", optimize=True)

            # Also mirror to public preprocessed directory for HTTP serving
            pil_img.save(public_path, format="PNG", optimize=True)

            # Compute artifact hash
            with open(target_path, "rb") as f:
                artifact_bytes = f.read()
            artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()

            artifact_records.append(
                PreprocessedArtifactRecord(
                    type=name,
                    relative_path=str(target_path.as_posix()),
                    file_size_bytes=len(artifact_bytes),
                    sha256=artifact_sha256,
                    width=pil_img.width,
                    height=pil_img.height,
                )
            )

        # 4. Save metadata.json
        metadata_path = run_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(result.original_metadata.model_dump_json(indent=2))

        # 5. Save quality.json
        quality_path = run_dir / "quality.json"
        with open(quality_path, "w", encoding="utf-8") as f:
            f.write(result.quality_report.model_dump_json(indent=2))

        # 6. Save manifest.json
        manifest = PreprocessingRunManifest(
            prescription_id=prescription_id,
            source_image_sha256=result.original_metadata.original_sha256,
            source_image_filename=original_image_path.name if original_image_path else None,
            preprocessing_config_id=result.config.id,
            preprocessing_config_hash=result.config.compute_config_hash(),
            status="completed",
            quality_status=result.quality_report.overall_status,
            heuristic_quality_score=result.quality_report.heuristic_quality_score,
            deskew_applied_angle_deg=result.deskew_applied_angle,
            primary_artifact_type="enhanced" if "enhanced" in result.derived_images else "grayscale",
            artifacts=artifact_records,
        )

        manifest_path = run_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        # Mirror manifest to public run directory as well
        with open(public_run_dir / "manifest.json", "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        return manifest, run_dir

    def get_run_manifest(self, prescription_id: str) -> Optional[PreprocessingRunManifest]:
        """Loads a stored preprocessing run manifest if it exists."""
        manifest_path = self.base_runs_dir / prescription_id / "manifest.json"
        if not manifest_path.exists():
            return None
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PreprocessingRunManifest.model_validate(data)
