"""
Configuration and Config Hashing for Phase 7 RAG.
Adheres to Section 18 of PLAN.md (reproducibility and auditable configuration fingerprinting).
"""

import hashlib
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class RAGConfig(BaseModel):
    """
    RAG Validation Runtime Configuration.
    """
    enabled: bool = Field(True, description="Master enable toggle for RAG validation service")
    reference_dir: str = Field("data/reference", description="Directory containing authoritative reference JSON files")
    manifest_path: str = Field("data/reference/reference_manifest.json", description="Path to reference sources manifest")
    top_k: int = Field(5, ge=1, le=20, description="Maximum number of candidates returned per query")
    min_similarity_threshold: float = Field(
        0.75,
        ge=0.0,
        le=1.0,
        description="Minimum lexical similarity score required for candidate consideration"
    )
    ambiguity_margin: float = Field(
        0.05,
        ge=0.0,
        le=0.5,
        description="Score margin within which competing candidates trigger uncertainty"
    )
    validation_score_threshold: float = Field(
        0.95,
        ge=0.5,
        le=1.0,
        description="Minimum score required for autonomous validation decision"
    )
    normalization_version: str = Field("v1.0-conservative", description="Active normalization algorithm version")
    index_version: str = Field("v1.0-in-memory", description="Active reference index representation version")

    def compute_config_hash(self) -> str:
        """
        Computes a deterministic SHA-256 hex digest of the configuration parameters
        for inclusion in validation provenance.
        """
        canonical_dict = {
            "enabled": self.enabled,
            "reference_dir": str(self.reference_dir),
            "manifest_path": str(self.manifest_path),
            "top_k": self.top_k,
            "min_similarity_threshold": self.min_similarity_threshold,
            "ambiguity_margin": self.ambiguity_margin,
            "validation_score_threshold": self.validation_score_threshold,
            "normalization_version": self.normalization_version,
            "index_version": self.index_version,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()[:16]


_default_rag_config: Optional[RAGConfig] = None


def get_rag_config() -> RAGConfig:
    """Returns singleton RAG configuration."""
    global _default_rag_config
    if _default_rag_config is None:
        _default_rag_config = RAGConfig()
    return _default_rag_config
