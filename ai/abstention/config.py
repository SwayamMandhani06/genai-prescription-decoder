"""
Phase 9: Configurable Abstention Policy and Parameters.
Maintains versioned, reproducible thresholds and decision criteria.

Adheres strictly to Phase 9 specification:
- Versioned policy configuration (abstention_policy_v1).
- No scattered numerical thresholds.
- Conservative handling of uncalibrated or insufficient calibration data.
- Cryptographic SHA-256 fingerprinting for experiment provenance.
"""

import hashlib
import json
from typing import Any, Dict
from pydantic import BaseModel, Field


class AbstentionPolicyConfig(BaseModel):
    """
    Typed, versioned configuration governing uncertainty-aware abstention decisions.
    """
    policy_version: str = Field(
        "abstention_policy_v1",
        description="Formal version identifier of the active abstention policy"
    )
    min_calibrated_confidence: float = Field(
        0.80,
        ge=0.0,
        le=1.0,
        description="Minimum empirically calibrated confidence required to automatically accept an extraction"
    )
    require_calibration_for_acceptance: bool = Field(
        True,
        description=(
            "Conservative safety default: If True, fields with calibration_status in "
            "['insufficient_data', 'uncalibrated', 'not_available'] are abstained."
        )
    )
    abstain_on_extraction_uncertain: bool = Field(
        True,
        description="If True, any field with Phase 6 status 'uncertain' or state 'ambiguous' triggers abstention"
    )
    abstain_on_field_missing: bool = Field(
        True,
        description="If True, missing or absent fields trigger abstention with FIELD_MISSING reason code"
    )
    abstain_on_conflict: bool = Field(
        True,
        description="If True, detected evidentiary conflicts (visual vs retrieval) trigger abstention"
    )
    abstain_on_multiple_candidates: bool = Field(
        True,
        description="If True, presence of competing candidate interpretations triggers abstention"
    )
    dosage_strict_mode: bool = Field(
        True,
        description=(
            "Safety-critical dosage invariant: Formulation mismatches, ambiguous numerals, or missing visual grounding "
            "strictly mandate dosage abstention. Observed dosage is never rewritten."
        )
    )
    allow_uncalibrated_acceptance: bool = Field(
        False,
        description="If True, permits fallback acceptance using min_raw_confidence_fallback when calibration is unavailable"
    )
    min_raw_confidence_fallback: float = Field(
        0.85,
        ge=0.0,
        le=1.0,
        description="Threshold used ONLY if allow_uncalibrated_acceptance is explicitly enabled"
    )
    description: str = Field(
        "Standard conservative clinical posology abstention policy prioritizing safety over autonomous guessing",
        description="Human-readable description of policy intent"
    )

    def get_config_hash(self) -> str:
        """
        Computes a deterministic 64-character SHA-256 fingerprint of policy parameters.
        Ensures experiment tracking and audit trail consistency.
        """
        payload = {
            "policy_version": self.policy_version,
            "min_calibrated_confidence": self.min_calibrated_confidence,
            "require_calibration_for_acceptance": self.require_calibration_for_acceptance,
            "abstain_on_extraction_uncertain": self.abstain_on_extraction_uncertain,
            "abstain_on_field_missing": self.abstain_on_field_missing,
            "abstain_on_conflict": self.abstain_on_conflict,
            "abstain_on_multiple_candidates": self.abstain_on_multiple_candidates,
            "dosage_strict_mode": self.dosage_strict_mode,
            "allow_uncalibrated_acceptance": self.allow_uncalibrated_acceptance,
            "min_raw_confidence_fallback": self.min_raw_confidence_fallback,
        }
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation including configuration hash."""
        d = self.model_dump()
        d["config_hash"] = self.get_config_hash()
        return d


def get_default_abstention_config() -> AbstentionPolicyConfig:
    """Returns the default, production-conservative abstention policy."""
    return AbstentionPolicyConfig()
