"""
Unit Tests for Experiment Configuration and Dataset Versioning (Phase 3)
"""

import json
from pathlib import Path
import pytest

from backend.app.dataset.config import (
    ExperimentConfig,
    DatasetVersionInfo,
    load_experiment_config,
    save_experiment_config
)


def test_experiment_config_loading_and_hashing():
    """Verifies that experiment_config.json loads cleanly and computes deterministic config hash."""
    config_p = Path("data/metadata/experiment_config.json")
    assert config_p.exists()

    cfg = load_experiment_config(config_p)
    assert cfg.experiment_id == "EXP-P03-BASELINE-DATASET"
    assert cfg.configuration_status == "prospective"
    assert cfg.implementation_status == "not_implemented"
    assert "Phase 12" in cfg.planned_phase
    assert cfg.evaluation_protocol.protocol_status == "prospective_target"
    assert cfg.random_seed == 42
    assert cfg.config_hash is not None
    assert len(cfg.config_hash) == 64
    assert cfg.compute_hash() == cfg.config_hash


def test_dataset_version_info_matches_physical_files():
    """Verifies that data/metadata/dataset_version.json checksums match active files on disk."""
    import hashlib
    version_p = Path("data/metadata/dataset_version.json")
    assert version_p.exists()

    with open(version_p, "r", encoding="utf-8") as f:
        data = json.load(f)
    vinfo = DatasetVersionInfo.model_validate(data)

    def file_hash(p: Path) -> str:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    assert vinfo.manifest_checksum == file_hash(Path("data/manifests/dataset_manifest.json"))
    assert vinfo.ground_truth_checksum == file_hash(Path("data/annotations/sample_annotations.json"))
    assert vinfo.splits_checksum == file_hash(Path("data/splits/sample_splits.json"))
    assert vinfo.total_samples == 7


def test_experiment_config_serialization_roundtrip(tmp_path: Path):
    """Verifies that saving and reloading an experiment config preserves exact fields and hash."""
    config_p = Path("data/metadata/experiment_config.json")
    cfg = load_experiment_config(config_p)

    out_file = tmp_path / "test_exp.json"
    save_experiment_config(cfg, out_file)

    reloaded = load_experiment_config(out_file)
    assert reloaded.config_hash == cfg.config_hash
    assert reloaded.experiment_id == cfg.experiment_id
    assert reloaded.evaluation_protocol.confidence_threshold == cfg.evaluation_protocol.confidence_threshold
