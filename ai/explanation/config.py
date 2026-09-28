"""
Phase 11: Multilingual Explanation Configuration.
Defines policy versions, supported vernaculars, safety thresholds, and immutable configuration hashes.
"""

import hashlib
import json
from typing import Dict, List, Any
from pydantic import BaseModel, Field

from ai.explanation.schemas import LanguageCode

POLICY_VERSION = "explanation_policy_v1"
TEMPLATE_VERSION = "explanation_template_v1"
TERMINOLOGY_VERSION = "explanation_terminology_v1"

EXPLANATION_PROVENANCE_METADATA: Dict[str, Any] = {
    "module": "AURA-Rx Phase 11 Multilingual Patient Explanation Engine",
    "policy_version": POLICY_VERSION,
    "template_version": TEMPLATE_VERSION,
    "terminology_version": TERMINOLOGY_VERSION,
    "supported_languages": ["en", "hi", "mr"],
    "language_names": {
        "en": "English",
        "hi": "हिन्दी (Hindi)",
        "mr": "मराठी (Marathi)",
    },
    "scope_disclosure": (
        "This explanation engine is an assistive posology clarification aid. "
        "It translates already extracted and verified prescription facts into accessible language. "
        "It does NOT diagnose diseases, prescribe medications, modify dosages, or independently reinterpret handwriting."
    ),
    "factual_invariants": [
        "Medicine names remain in canonical Roman script to eliminate phonetic transliteration errors.",
        "All numeric dosage strengths and durations are preserved verbatim.",
        "Clinical abbreviations (BD, TDS, PC, AC) map to standardized daily visual periods.",
        "Uncertain, abstained, or confusable fields explicitly mandate clinician verification.",
    ],
}


class ExplanationConfig(BaseModel):
    """
    Phase 11 Multilingual Explanation Engine Configuration.
    Ensures deterministic, auditable, and reproducible patient posology explanations.
    """
    policy_version: str = Field(
        POLICY_VERSION,
        description="Active explanation policy ruleset identifier",
    )
    template_version: str = Field(
        TEMPLATE_VERSION,
        description="Version identifier for deterministic multilingual templates",
    )
    terminology_version: str = Field(
        TERMINOLOGY_VERSION,
        description="Version identifier for clinical concept vocabulary mappings",
    )
    supported_languages: List[LanguageCode] = Field(
        default_factory=lambda: ["en", "hi", "mr"],
        description="List of enabled vernacular languages for explanation generation",
    )
    enforce_numeric_fidelity: bool = Field(
        True,
        description="When True, rejects generated explanations if numeric tokens differ from source facts",
    )
    enforce_medicine_fidelity: bool = Field(
        True,
        description="When True, rejects generated explanations if medicine name is altered or translated",
    )
    enforce_unsupported_fact_check: bool = Field(
        True,
        description="When True, rejects generated explanations containing unapproved clinical indications or diagnoses",
    )
    allow_unverified_definitive_instruction: bool = Field(
        False,
        description="Safety gate: if False, abstained or unverified medicines cannot produce definitive intake instructions",
    )
    default_language: LanguageCode = Field(
        "en",
        description="Default fallback language code",
    )

    @property
    def config_hash(self) -> str:
        """
        Computes deterministic SHA-256 fingerprint of the normalized configuration.
        """
        payload = {
            "policy_version": self.policy_version,
            "template_version": self.template_version,
            "terminology_version": self.terminology_version,
            "supported_languages": sorted(self.supported_languages),
            "enforce_numeric_fidelity": self.enforce_numeric_fidelity,
            "enforce_medicine_fidelity": self.enforce_medicine_fidelity,
            "enforce_unsupported_fact_check": self.enforce_unsupported_fact_check,
            "allow_unverified_definitive_instruction": self.allow_unverified_definitive_instruction,
            "default_language": self.default_language,
        }
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @property
    def provenance(self) -> Dict[str, Any]:
        return {
            **EXPLANATION_PROVENANCE_METADATA,
            "config_hash": self.config_hash,
        }


def get_default_explanation_config() -> ExplanationConfig:
    """Returns the default, production-ready ExplanationConfig instance."""
    return ExplanationConfig()


DEFAULT_EXPLANATION_CONFIG = get_default_explanation_config()
CONFIG_HASH = DEFAULT_EXPLANATION_CONFIG.config_hash
SUPPORTED_LANGUAGES: List[LanguageCode] = ["en", "hi", "mr"]
