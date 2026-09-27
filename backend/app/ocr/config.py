"""
Phase 5: OCR/HTR Baseline Configuration
Centralized, reproducible configuration for conventional OCR baseline.
Guarantees determinism, records engine specifications, and computes configuration hashes.
"""

import hashlib
import json
import os
import shutil
from typing import Literal, Optional
from pydantic import BaseModel, Field


def find_default_tesseract_cmd() -> Optional[str]:
    """
    Locates the tesseract executable on the system without hardcoding.
    Searches standard PATH and typical platform installation directories.
    """
    # 1. Environment variable override
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd and os.path.isfile(env_cmd):
        return env_cmd

    # 2. System PATH
    path_cmd = shutil.which("tesseract")
    if path_cmd and os.path.isfile(path_cmd):
        return path_cmd

    # 3. Known Windows directories
    candidate_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in candidate_paths:
        if os.path.isfile(candidate):
            return candidate

    return None


class OCRBaselineConfig(BaseModel):
    """
    Centralized baseline configuration contract.
    All parameters affecting OCR inference must be recorded for scientific reproducibility.
    """
    configuration_id: str = Field(
        "ocr_tesseract_baseline_v1",
        description="Unique identifier for the baseline configuration specification",
    )
    engine: Literal["tesseract"] = Field(
        "tesseract",
        description="Conventional OCR/HTR engine moniker",
    )
    language: str = Field(
        "eng",
        description="OCR language training dataset code (e.g. 'eng')",
    )
    psm: int = Field(
        6,
        description="Page segmentation mode (6 = Assume a single uniform block of text)",
    )
    oem: int = Field(
        1,
        description="OCR Engine Mode (1 = Neural nets LSTM engine only)",
    )
    preprocessing_variant: str = Field(
        "enhanced",
        description="Preprocessing artifact representation used as input ('enhanced', 'grayscale', 'thresholded', 'original', 'deskewed')",
    )
    timeout_seconds: float = Field(
        30.0,
        description="Maximum execution timeout in seconds before terminating engine subprocess",
    )
    preserve_raw_evidence: bool = Field(
        True,
        description="Strictly preserve raw OCR output without post-hoc medical correction",
    )
    tesseract_cmd: Optional[str] = Field(
        default_factory=find_default_tesseract_cmd,
        description="Resolved path to tesseract binary",
    )

    def compute_config_hash(self) -> str:
        """
        Computes deterministic SHA-256 hash of configuration parameters.
        Excludes machine-specific binary paths to maintain cross-machine hash equivalence.
        """
        hashable_dict = {
            "configuration_id": self.configuration_id,
            "engine": self.engine,
            "language": self.language,
            "psm": self.psm,
            "oem": self.oem,
            "preprocessing_variant": self.preprocessing_variant,
            "preserve_raw_evidence": self.preserve_raw_evidence,
        }
        canonical_json = json.dumps(hashable_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
