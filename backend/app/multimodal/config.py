"""
Phase 6: Multimodal Prescription Extraction Configuration
Centralized configuration model for multimodal vision-language model execution.
Supports versioned prompt specifications, low-temperature inference, and cryptographic configuration hashing.
"""

import hashlib
import json
import os
from typing import Literal, Optional
from pydantic import BaseModel, Field


class MultimodalConfig(BaseModel):
    """
    Configuration contract for multimodal vision-language extraction.
    All parameters affecting inference must be recorded for scientific reproducibility.
    """
    config_version: str = Field(
        "multimodal_extraction_v1",
        description="Configuration schema release version",
    )
    provider: Literal["gemini", "mock"] = Field(
        "gemini",
        description="Multimodal model provider ('gemini' or 'mock')",
    )
    model_id: str = Field(
        "gemini-3.8-flash",
        description="Canonical model identifier",
    )
    model_version: str = Field(
        "gemini-3.8-flash",
        description="Exact provider model release version",
    )
    temperature: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (low temperature enforces deterministic extraction)",
    )
    max_tokens: int = Field(
        2048,
        gt=0,
        description="Maximum generation token budget",
    )
    timeout_seconds: float = Field(
        30.0,
        gt=0.0,
        description="Subprocess or HTTP request timeout in seconds",
    )
    structured_output_mode: Literal["json_object", "schema_guided"] = Field(
        "json_object",
        description="Structured JSON output enforcement mode",
    )
    prompt_version: str = Field(
        "prompt_v1_clinical_vision_extraction",
        description="Versioned clinical vision extraction prompt identifier",
    )
    api_key_env_var: str = Field(
        "GEMINI_API_KEY",
        description="Name of environment variable supplying the provider API key",
    )
    configuration_status: Literal["implemented", "mock", "unavailable"] = Field(
        "implemented",
        description="Operational readiness status of configuration",
    )

    def get_api_key(self) -> Optional[str]:
        """Resolves API key from environment variables without hardcoding secrets."""
        return os.environ.get(self.api_key_env_var) or os.environ.get("GOOGLE_API_KEY")

    def compute_config_hash(self) -> str:
        """
        Computes deterministic SHA-256 hash of configuration parameters.
        Excludes machine-specific environment variable values to maintain reproducibility.
        """
        hashable_dict = {
            "config_version": self.config_version,
            "provider": self.provider,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "structured_output_mode": self.structured_output_mode,
            "prompt_version": self.prompt_version,
        }
        canonical_json = json.dumps(hashable_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
