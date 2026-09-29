"""
Evaluation Manifest Specification (Section 5).
Tracks code version, dataset hashes, random seeds, and experiment configurations.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

EVALUATION_ID = "aura_rx_eval_v1"
RANDOM_SEED = 42
CODE_VERSION = "1.0.0"
CONFIG_VERSION = "evaluation_config_v1"

def get_file_sha256(filepath: Path) -> str:
    if not filepath.exists():
        return "file_not_found"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def build_evaluation_manifest(root_dir: Path) -> Dict[str, Any]:
    annotations_path = root_dir / "data" / "annotations" / "sample_annotations.json"
    splits_path = root_dir / "data" / "splits" / "sample_splits.json"
    reference_manifest_path = root_dir / "data" / "reference" / "reference_manifest.json"

    manifest = {
        "evaluation_id": EVALUATION_ID,
        "code_version": CODE_VERSION,
        "config_version": CONFIG_VERSION,
        "random_seed": RANDOM_SEED,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_metadata": {
            "annotations_file": str(annotations_path.relative_to(root_dir)),
            "annotations_sha256": get_file_sha256(annotations_path),
            "splits_file": str(splits_path.relative_to(root_dir)),
            "splits_sha256": get_file_sha256(splits_path),
            "reference_manifest_file": str(reference_manifest_path.relative_to(root_dir)) if reference_manifest_path.exists() else None,
            "reference_manifest_sha256": get_file_sha256(reference_manifest_path) if reference_manifest_path.exists() else None,
            "sample_count": 7,
            "sample_role": "development_and_calibration_fixtures",
            "statistically_sufficient_clinical_benchmark": False
        },
        "experiments": [
            "EXP-01",
            "EXP-02",
            "EXP-03",
            "EXP-04",
            "EXP-05",
            "EXP-06",
            "EXP-07",
            "EXP-08",
            "EXP-09"
        ]
    }
    return manifest

def save_manifest(root_dir: Path) -> Path:
    manifest = build_evaluation_manifest(root_dir)
    target = root_dir / "eval" / "config" / "evaluation_manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return target
