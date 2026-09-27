"""
Unit Tests for Phase 6 Multimodal Configuration & Hashing
"""

import os
import pytest
from backend.app.multimodal.config import MultimodalConfig


def test_default_multimodal_config():
    """Verifies default configuration parameters and stability."""
    cfg = MultimodalConfig()
    assert cfg.config_version == "multimodal_extraction_v1"
    assert cfg.provider in ("gemini", "mock")
    assert cfg.model_id == "gemini-3.8-flash"
    assert cfg.temperature == 0.1
    assert cfg.max_tokens == 2048
    assert cfg.timeout_seconds == 30.0
    assert cfg.structured_output_mode == "json_object"
    assert cfg.prompt_version == "prompt_v1_clinical_vision_extraction"
    assert cfg.configuration_status == "implemented"


def test_config_hash_determinism_and_reproducibility():
    """Verifies that identical configurations produce identical SHA-256 hashes."""
    cfg1 = MultimodalConfig()
    cfg2 = MultimodalConfig()
    hash1 = cfg1.compute_config_hash()
    hash2 = cfg2.compute_config_hash()
    assert hash1 == hash2
    assert len(hash1) == 64

    # Modifying temperature or prompt must alter the hash
    cfg3 = MultimodalConfig(temperature=0.2)
    assert cfg3.compute_config_hash() != hash1


def test_api_key_resolution_without_hardcoding(monkeypatch):
    """Verifies that API keys are resolved dynamically from env vars without hardcoding."""
    cfg = MultimodalConfig()
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert cfg.get_api_key() is None

    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")
    assert cfg.get_api_key() == "test_gemini_key_123"

    # Fallback to GOOGLE_API_KEY
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key_456")
    assert cfg.get_api_key() == "test_google_key_456"
