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

    # Epistemic and safety bounds reasons
    MEDICINE_ILLEGIBLE = "MEDICINE_ILLEGIBLE"
    MEDICINE_AMBIGUOUS = "MEDICINE_AMBIGUOUS"
    MEDICINE_UNVERIFIED = "MEDICINE_UNVERIFIED"
    DOSAGE_OUT_OF_BOUNDS = "DOSAGE_OUT_OF_BOUNDS"
    DECIMAL_BLUR_HAZARD = "DECIMAL_BLUR_HAZARD"
    HIGH_ALERT_LASA_UNRESOLVED = "HIGH_ALERT_LASA_UNRESOLVED"

    # Pipeline & system reasons
    PROCESSING_UNCERTAIN = "PROCESSING_UNCERTAIN"
    DOCUMENT_NOT_PRESCRIPTION = "DOCUMENT_NOT_PRESCRIPTION"
    NO_PRESCRIPTION_CONTENT_OBSERVED = "NO_PRESCRIPTION_CONTENT_OBSERVED"


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
    AbstentionReasonCode.DOCUMENT_NOT_PRESCRIPTION: (
        "The uploaded image does not contain sufficient visual or textual evidence of a medical prescription document."
    ),
    AbstentionReasonCode.NO_PRESCRIPTION_CONTENT_OBSERVED: (
        "Zero valid medication posology line items were visually identified on the submitted document."
    ),
    AbstentionReasonCode.MEDICINE_ILLEGIBLE: (
        "Prescribed medicine name contains illegible ink strokes, characters that cannot be read reliably, or '[?]'. "
        "Autonomous acceptance is withheld; human pharmacist verification is mandated."
    ),
    AbstentionReasonCode.MEDICINE_AMBIGUOUS: (
        "Prescribed medicine exhibits multiple competing interpretations or ambiguous cursive stroke formations. "
        "Autonomous acceptance is withheld; human pharmacist verification is mandated."
    ),
    AbstentionReasonCode.MEDICINE_UNVERIFIED: (
        "Prescribed drug entity is legible but not corroborated in reference formularies (CDSCO/RxNorm). "
        "Autonomous acceptance is withheld; human pharmacist verification is mandated."
    ),
    AbstentionReasonCode.DOSAGE_OUT_OF_BOUNDS: (
        "Prescribed dosage strength exceeds safe clinical bounds (e.g. 10x overdose hazard or unit mismatch). "
        "Autonomous acceptance is withheld; urgent pharmacist verification is mandated."
    ),
    AbstentionReasonCode.DECIMAL_BLUR_HAZARD: (
        "Prescribed dosage contains a decimal point on a degraded or blurry image (e.g. 0.5 vs 5 vs 50 hazard). "
        "Autonomous acceptance is withheld; human pharmacist verification is mandated."
    ),
    AbstentionReasonCode.HIGH_ALERT_LASA_UNRESOLVED: (
        "High-alert look-alike / sound-alike (LASA) medicine pair detected without disambiguating formulation or strength evidence. "
        "Autonomous acceptance is withheld; human pharmacist verification is mandated."
    ),
}


def get_reason_description(code: AbstentionReasonCode) -> str:
    """Returns the standardized documentation string for an abstention reason code."""
    return REASON_DESCRIPTIONS.get(code, "Unspecified uncertainty condition requiring human verification.")
