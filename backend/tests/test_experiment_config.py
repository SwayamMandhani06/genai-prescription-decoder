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


def test_all_ten_configuration_modules_load_cleanly():
    """
    Phase 0 Smoke Test: Verifies that all 10 configuration modules across backend and AI
    packages import cleanly, instantiate their respective configuration models, and contain
    no missing-attribute or syntax defects.
    """
    # 1. backend.app.config
    import backend.app.config as root_cfg
    settings = root_cfg.get_settings()
    assert hasattr(settings, "PROJECT_NAME")
    assert hasattr(settings, "VERSION")
    assert hasattr(settings, "API_V1_PREFIX")
    assert hasattr(settings, "MULTIMODAL_MODEL_ID")
    assert hasattr(settings, "HOST")
    assert hasattr(settings, "PORT")
    assert hasattr(settings, "CORS_ORIGINS")
    assert hasattr(settings, "USE_MOCK_PIPELINE")

    # 2. ai.abstention.config
    import ai.abstention.config as abstention_cfg
    abs_config = abstention_cfg.AbstentionPolicyConfig()
    assert hasattr(abs_config, "policy_version")
    assert hasattr(abs_config, "min_calibrated_confidence")
    assert hasattr(abs_config, "require_calibration_for_acceptance")
    assert hasattr(abs_config, "abstain_on_extraction_uncertain")
    assert hasattr(abs_config, "dosage_strict_mode")

    # 3. ai.confidence.config
    import ai.confidence.config as confidence_cfg
    conf_config = confidence_cfg.ConfidenceConfig()
    assert hasattr(conf_config, "config_version")
    assert hasattr(conf_config, "default_calibration_method")
    assert hasattr(conf_config, "min_samples_for_calibration")
    assert hasattr(conf_config, "num_calibration_bins")
    assert hasattr(conf_config, "conflict_delta_threshold")
    assert callable(conf_config.compute_hash)

    # 4. ai.explanation.config
    import ai.explanation.config as explanation_cfg
    exp_config = explanation_cfg.ExplanationConfig()
    assert hasattr(exp_config, "policy_version")
    assert hasattr(exp_config, "template_version")
    assert hasattr(exp_config, "terminology_version")
    assert hasattr(exp_config, "supported_languages")
    assert hasattr(exp_config, "enforce_numeric_fidelity")
    assert exp_config.config_hash is not None

    # 5. ai.lasa.config
    import ai.lasa.config as lasa_cfg
    lasa_config = lasa_cfg.LasaConfig()
    assert hasattr(lasa_config, "orthographic_threshold")
    assert hasattr(lasa_config, "phonetic_threshold")
    assert hasattr(lasa_config, "combined_threshold")
    assert hasattr(lasa_config, "orthographic_weight")
    assert hasattr(lasa_config, "phonetic_weight")
    assert callable(lasa_config.config_hash)

    # 6. ai.rag.config
    import ai.rag.config as rag_cfg
    rag_config = rag_cfg.RAGConfig()
    assert hasattr(rag_config, "enabled")
    assert hasattr(rag_config, "reference_dir")
    assert hasattr(rag_config, "manifest_path")
    assert hasattr(rag_config, "top_k")
    assert hasattr(rag_config, "min_similarity_threshold")
    assert callable(rag_config.compute_config_hash)

    # 7. backend.app.dataset.config
    import backend.app.dataset.config as dataset_cfg
    assert hasattr(dataset_cfg, "ExperimentConfig")
    assert hasattr(dataset_cfg, "EvaluationProtocolConfig")
    assert hasattr(dataset_cfg, "DatasetVersionInfo")
    assert callable(dataset_cfg.load_experiment_config)
    assert callable(dataset_cfg.save_experiment_config)

    # 8. backend.app.multimodal.config
    import backend.app.multimodal.config as multimodal_cfg
    mm_config = multimodal_cfg.MultimodalConfig()
    assert hasattr(mm_config, "model_id")
    assert hasattr(mm_config, "max_tokens")
    assert hasattr(mm_config, "timeout_seconds")
    assert hasattr(mm_config, "provider")
    assert callable(mm_config.get_api_key)

    # 9. backend.app.ocr.config
    import backend.app.ocr.config as ocr_cfg
    ocr_config = ocr_cfg.OCRBaselineConfig()
    assert hasattr(ocr_config, "engine")
    assert hasattr(ocr_config, "psm")
    assert hasattr(ocr_config, "oem")
    assert hasattr(ocr_config, "language")
    assert hasattr(ocr_config, "tesseract_cmd")

    # 10. backend.app.preprocessing.config
    import backend.app.preprocessing.config as preprocessing_cfg
    prep_config = preprocessing_cfg.PreprocessingConfig()
    assert hasattr(prep_config, "id")
    assert hasattr(prep_config, "version")
    assert hasattr(prep_config, "thresholds")
    assert hasattr(prep_config, "enable_orientation_correction")
    assert callable(prep_config.compute_config_hash)
    thresholds = prep_config.thresholds
    assert hasattr(thresholds, "min_width")
    assert hasattr(thresholds, "min_height")
    assert hasattr(thresholds, "min_dpi")


