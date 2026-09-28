"""
Phase 9: Uncertainty-Aware Abstention Reason Taxonomy.
Defines machine-readable, deterministic reason codes explaining why automatic acceptance was withheld
and human verification was mandated.

Adheres strictly to Phase 9 specification:
- Deterministic, standardized reason codes.
- No LASA reason codes (reserved for Phase 10).
- Preserves distinct failure/uncertainty categories.
"""

from enum import Enum
from typing import Dict


class AbstentionReasonCode(str, Enum):
    """
    Standardized, machine-readable reason codes for abstention decisions.
    """
    # Calibration-related reasons
    CALIBRATION_UNAVAILABLE = "CALIBRATION_UNAVAILABLE"
    CALIBRATION_INSUFFICIENT_DATA = "CALIBRATION_INSUFFICIENT_DATA"
    LOW_CALIBRATED_CONFIDENCE = "LOW_CALIBRATED_CONFIDENCE"

    # Multimodal visual extraction reasons
    EXTRACTION_UNCERTAIN = "EXTRACTION_UNCERTAIN"
    FIELD_MISSING = "FIELD_MISSING"
    AMBIGUOUS_CURSIVE_STROKE = "AMBIGUOUS_CURSIVE_STROKE"
    MODEL_OUTPUT_INCOMPLETE = "MODEL_OUTPUT_INCOMPLETE"

    # Reference validation & candidate reasons
    MULTIPLE_CANDIDATES = "MULTIPLE_CANDIDATES"
    VISUAL_RETRIEVAL_DISCREPANCY = "VISUAL_RETRIEVAL_DISCREPANCY"
    DOSAGE_FORMULATION_MISMATCH = "DOSAGE_FORMULATION_MISMATCH"
    VALIDATION_CONFLICT = "VALIDATION_CONFLICT"
    UNSUPPORTED_FIELD = "UNSUPPORTED_FIELD"

    # LASA medicine-name conflict reasons (Phase 10)
    LASA_CONFUSION_RISK = "LASA_CONFUSION_RISK"

    # Pipeline & system reasons
    PROCESSING_UNCERTAIN = "PROCESSING_UNCERTAIN"


# Human-readable documentation for each standardized reason code
REASON_DESCRIPTIONS: Dict[AbstentionReasonCode, str] = {
    AbstentionReasonCode.LASA_CONFUSION_RISK: (
        "Potential look-alike / sound-alike (LASA) medicine-name conflict detected against formulary "
        "or known confusable drug pairs. Autonomous acceptance is withheld; human clinical verification is mandated."
    ),
    AbstentionReasonCode.CALIBRATION_UNAVAILABLE: (
        "Empirical probability calibration is unperformed or unavailable for this field score. "
        "The system conservatively refrains from treating raw model scores as calibrated certainty."
    ),
    AbstentionReasonCode.CALIBRATION_INSUFFICIENT_DATA: (
        "The active evaluation dataset sample size is statistically insufficient (N < 15) to guarantee "
        "calibrated probability validity. Automatic acceptance requires human verification."
    ),
    AbstentionReasonCode.LOW_CALIBRATED_CONFIDENCE: (
        "The empirically calibrated confidence probability falls below the configured policy acceptance threshold."
    ),
    AbstentionReasonCode.EXTRACTION_UNCERTAIN: (
        "Visual handwriting extraction exhibited perceptual ambiguity or low stroke certainty during multimodal inference."
    ),
    AbstentionReasonCode.FIELD_MISSING: (
        "The posology field is absent, missing, or could not be located in the prescription document."
    ),
    AbstentionReasonCode.AMBIGUOUS_CURSIVE_STROKE: (
        "Handwriting strokes contain degraded ligatures, truncated cursive forms, or confusable character shapes."
    ),
    AbstentionReasonCode.MODEL_OUTPUT_INCOMPLETE: (
        "Multimodal model output was incomplete, omitted required posology keys, or required fallback handling."
    ),
    AbstentionReasonCode.MULTIPLE_CANDIDATES: (
        "Multiple plausible medicine or dosage candidates were detected with no dominant disambiguating evidence."
    ),
    AbstentionReasonCode.VISUAL_RETRIEVAL_DISCREPANCY: (
        "A divergent signal exists between visual stroke clarity and formulary database retrieval similarity. "
        "High retrieval similarity cannot erase visual handwriting uncertainty."
    ),
    AbstentionReasonCode.DOSAGE_FORMULATION_MISMATCH: (
        "Safety-critical discrepancy detected between observed prescribed dosage strength and reference formulary strengths. "
        "Observed dosage is strictly preserved and cannot be automatically accepted without human review."
    ),
    AbstentionReasonCode.VALIDATION_CONFLICT: (
        "Authoritative reference formulary validation contradicted the extracted clinical posology evidence."
    ),
    AbstentionReasonCode.UNSUPPORTED_FIELD: (
        "The field format, nomenclature, or administration route is not supported by current clinical schemas."
    ),
    AbstentionReasonCode.PROCESSING_UNCERTAIN: (
        "Upstream optical or pipeline processing encountered marginal quality or ambiguous intermediary representations."
    ),
}


def get_reason_description(code: AbstentionReasonCode) -> str:
    """Returns the standardized documentation string for an abstention reason code."""
    return REASON_DESCRIPTIONS.get(code, "Unspecified uncertainty condition requiring human verification.")
