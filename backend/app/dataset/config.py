"""
Experiment Configuration and Dataset Versioning Management (Phase 3)
Enables fully reproducible experiment declarations and cryptographic dataset version tags.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class EvaluationProtocolConfig(BaseModel):
    """Protocol settings for prospective downstream evaluation phases."""
    protocol_status: str = Field(default="prospective_target", description="Design target criteria for Phase 12; not current benchmark results")
    metrics: List[str] = Field(
        default_factory=lambda: ["wer", "cer", "entity_f1", "posology_f1", "abstention_auroc"],
        description="Target evaluation metrics"
    )
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    abstention_entropy_threshold: float = Field(default=0.40, ge=0.0, le=1.0)
    iou_spatial_threshold: float = Field(default=0.50, ge=0.0, le=1.0)


class ExperimentConfig(BaseModel):
    """Declarative specification for reproducible pipeline experiments."""
    experiment_id: str = Field(..., min_length=3, description="Canonical experiment name")
    description: str = Field(..., description="Objective and hypotheses of experiment")
    configuration_status: str = Field(default="prospective", description="Must be 'prospective' during data foundation phases")
    implementation_status: str = Field(default="not_implemented", description="Indicates whether target models are implemented")
    planned_phase: str = Field(default="Phase 12 (Evaluation & Ablation)", description="Phase wherein this experiment will be executed")
    dataset_version: str = Field(default="1.0.0", description="Target dataset version identifier")
    split_version: str = Field(default="1.0.0", description="Target dataset split identifier")
    random_seed: int = Field(default=42, description="Random seed for all stochastic operations")
    preprocessing_version: str = Field(default="p04_standard_dewarp", description="Preprocessing recipe identifier")
    model_identifier: str = Field(..., description="Target model architecture or comparison baseline")
    evaluation_protocol: EvaluationProtocolConfig = Field(default_factory=EvaluationProtocolConfig)
    output_directory: str = Field(default="experiments/results", description="Relative output path for artifacts")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Configuration creation timestamp"
    )
    config_hash: Optional[str] = Field(None, description="SHA-256 fingerprint of the configuration")

    def compute_hash(self) -> str:
        payload = json.dumps(
            {
                "experiment_id": self.experiment_id,
                "configuration_status": self.configuration_status,
                "implementation_status": self.implementation_status,
                "planned_phase": self.planned_phase,
                "dataset_version": self.dataset_version,
                "split_version": self.split_version,
                "random_seed": self.seed if hasattr(self, 'seed') else self.random_seed,
                "preprocessing_version": self.preprocessing_version,
                "model_identifier": self.model_identifier,
                "evaluation_protocol": self.evaluation_protocol.model_dump(),
            },
            sort_keys=True
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def update_hash(self) -> None:
        self.config_hash = self.compute_hash()


class DatasetVersionInfo(BaseModel):
    """Version descriptor capturing the state of manifests, annotations, and splits."""
    dataset_version: str = Field(..., description="Semantic version (e.g. '1.0.0')")
    release_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Release timestamp"
    )
    total_samples: int = Field(..., ge=0, description="Total number of ground-truth annotated samples")
    manifest_checksum: str = Field(..., description="SHA-256 hash of dataset_manifest.json")
    ground_truth_checksum: str = Field(..., description="SHA-256 hash of ground_truth_annotations.json")
    splits_checksum: str = Field(..., description="SHA-256 hash of sample_splits.json")
    git_commit_reference: Optional[str] = Field(None, description="Git commit hash when version was sealed")
    description: str = Field(..., description="Release changelog summary")


def load_experiment_config(config_path: Path) -> ExperimentConfig:
    """Loads and validates an ExperimentConfig from JSON."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = ExperimentConfig.model_validate(data)
    cfg.update_hash()
    return cfg


def save_experiment_config(config: ExperimentConfig, config_path: Path) -> None:
    """Saves an ExperimentConfig with updated cryptographic hash."""
    config.update_hash()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
