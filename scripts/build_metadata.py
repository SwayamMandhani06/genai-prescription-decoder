"""
Builds dataset version metadata and experiment configurations (Phase 3).
"""

import sys
import json
import hashlib
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.dataset.config import (
    DatasetVersionInfo,
    ExperimentConfig,
    EvaluationProtocolConfig,
    save_experiment_config
)

def file_hash(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

manifest_p = Path("data/manifests/dataset_manifest.json")
annotations_p = Path("data/annotations/sample_annotations.json")
splits_p = Path("data/splits/sample_splits.json")

version_info = DatasetVersionInfo(
    dataset_version="1.0.0",
    total_samples=7,
    manifest_checksum=file_hash(manifest_p),
    ground_truth_checksum=file_hash(annotations_p),
    splits_checksum=file_hash(splits_p),
    git_commit_reference="262389e",
    description="Initial frozen dataset infrastructure release with 7 curated calibration/integration samples, group-aware splits, and legal provenance taxonomy."
)

version_out_p = Path("data/metadata/dataset_version.json")
with open(version_out_p, "w", encoding="utf-8") as f:
    json.dump(version_info.model_dump(), f, indent=2)

exp_config = ExperimentConfig(
    experiment_id="EXP-P03-BASELINE-DATASET",
    description="Prospective experiment configuration specifying prospective evaluation protocols for Phase 12; models are NOT implemented in Phase 3.",
    configuration_status="prospective",
    implementation_status="not_implemented",
    planned_phase="Phase 12 (Evaluation & Ablation)",
    dataset_version="1.0.0",
    split_version="1.0.0",
    random_seed=42,
    preprocessing_version="p04_standard_dewarp (planned)",
    model_identifier="trocr_swin_multimodal_hybrid_v1 (planned)",
    evaluation_protocol=EvaluationProtocolConfig(
        protocol_status="prospective_target",
        metrics=["wer", "cer", "entity_f1", "posology_f1", "abstention_auroc", "lasa_accuracy"],
        confidence_threshold=0.85,
        abstention_entropy_threshold=0.40,
        iou_spatial_threshold=0.50
    ),
    output_directory="experiments/results/p03_baseline"
)

config_out_p = Path("data/metadata/experiment_config.json")
save_experiment_config(exp_config, config_out_p)

print("Generated data/metadata/dataset_version.json and experiment_config.json successfully.")
