"""
Configuration for Phase 8: Confidence Estimation & Calibration.
Defines parameters for calibration methods, sample-size validity thresholds,
reliability bins, and cryptographic configuration hashing.
"""

import hashlib
import json
from typing import Literal
from pydantic import BaseModel, Field


class ConfidenceConfig(BaseModel):
    """Configuration settings for confidence calibration and estimation."""
    config_version: str = Field(
        "confidence_calibration_v1",
        description="Version identifier for confidence configuration"
    )
    default_calibration_method: Literal["platt_scaling", "isotonic_regression", "temperature_scaling", "none"] = Field(
        "platt_scaling",
        description="Default method to use when calibration is enabled and data is sufficient"
    )
    min_samples_for_calibration: int = Field(
        15,
        ge=5,
        description="Minimum sample count required to fit a calibration model without flagging 'insufficient_data'"
    )
    num_calibration_bins: int = Field(
        5,
        ge=2,
        le=20,
        description="Number of confidence bins for ECE and reliability diagrams (5 bins for small cohorts)"
    )
    conflict_delta_threshold: float = Field(
        0.30,
        ge=0.05,
        le=0.90,
        description="Score delta threshold indicating a conflict between visual clarity and retrieval match"
    )
    dosage_reference_weight: float = Field(
        0.0,
        description="Weight of reference strength on dosage confidence (strictly 0.0 to prevent artificial inflation)"
    )
    calibration_dataset_version: str = Field(
        "1.0.0",
        description="Expected version of ground-truth calibration split"
    )
    random_seed: int = Field(
        42,
        description="Reproducible random seed for split verification"
    )

    def compute_hash(self) -> str:
        """Computes a deterministic SHA-256 fingerprint of the active configuration."""
        dumped = self.model_dump_json()
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()[:16]


_GLOBAL_CONFIDENCE_CONFIG = ConfidenceConfig()


def get_confidence_config() -> ConfidenceConfig:
    """Returns the singleton active confidence configuration."""
    return _GLOBAL_CONFIDENCE_CONFIG
