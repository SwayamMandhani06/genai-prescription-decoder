"""
Confidence Signal Extraction and Conflict Detection for Phase 8.
Adheres strictly to Sections 3, 5, 6, 7, and 18 of PLAN.md:
- Isolate Phase 6 visual extraction signals
- Isolate Phase 7 RAG retrieval and validation signals
- Strictly decouple visual extraction confidence from reference correspondence
- Dosage confidence grounded strictly in visual evidence (no artificial reference inflation)
- Preserve evidentiary conflicts rather than arbitrarily averaging them
"""

from typing import Dict, List, Optional, Tuple, Any
from backend.app.multimodal.schemas import ExtractedField, ExtractedMedicine
from ai.rag.schemas import MedicineValidationResult
from .schemas import (
    RawConfidenceSignal,
    CalibratedConfidence,
    FieldConfidenceAssessment,
    MedicineIdentityConfidence,
    DosageConfidenceAssessment,
)


def extract_field_confidence_signal(
    field: ExtractedField,
    field_name: str,
    model_version: str = "gemini-3.8-flash",
    config_version: str = "v1.0",
    raw_transcription: Optional[str] = None,
    validation_res: Optional[MedicineValidationResult] = None,
    lasa_result: Optional[Any] = None,
    image_quality_flags: Optional[Dict[str, bool]] = None,
) -> RawConfidenceSignal:
    """
    Extracts the uncalibrated raw confidence signal from an ExtractedField.
    Explicitly distinguishes confident, ambiguous, missing/absent, and unverified states.
    Penalizes immediately if:
    - raw_transcription contains '[?]' or field is ILLEGIBLE
    - image quality degradation flags (blur, low resolution, glare) are active
    - RAG match is below exact/high-similarity threshold (UNVERIFIED)
    - active LASA similarity conflict exists
    Guarantees raw confidence < 0.80 on any uncertain, unverified, or illegible item.
    """
    ep_status = getattr(field, "epistemic_status", None)
    val = field.value or ""

    if field.presence == "absent" or field.extraction_state == "missing" or field.value is None or ep_status == "MISSING_ON_RX":
        return RawConfidenceSignal(
            source=f"multimodal_{model_version}",
            raw_value=None,
            signal_type="absent_field_null_signal",
            model_version=model_version,
            config_version=config_version,
        )

    # 1. Check for unreadable / illegible tokens
    has_illegible_token = (
        "[?]" in val
        or (raw_transcription and "[?]" in raw_transcription)
        or ep_status == "ILLEGIBLE"
        or val == "ILLEGIBLE"
    )

    # 2. Check for LASA conflict
    has_lasa_ambiguity = False
    if lasa_result is not None:
        if getattr(lasa_result, "has_lasa_conflict", False) or getattr(lasa_result, "conflict_detected", False):
            has_lasa_ambiguity = True

    # 3. Base signal mapping
    if has_illegible_token:
        raw_val = 0.30
        sig_type = "model_illegible_stroke_anomaly"
    elif has_lasa_ambiguity:
        raw_val = 0.45
        sig_type = "model_ambiguous_or_lasa_conflict"
    elif field.status == "uncertain" or field.extraction_state == "ambiguous" or ep_status == "AMBIGUOUS":
        candidate_count = len(field.candidates)
        if candidate_count >= 3:
            raw_val = 0.40
        elif candidate_count == 2:
            raw_val = 0.50
        else:
            raw_val = 0.60
        sig_type = "model_ambiguous_cursive_stroke"
    elif field.status == "confident" and field.extraction_state == "extracted":
        raw_val = 0.95
        sig_type = "model_confident_visual_stroke"
    else:  # flagged
        raw_val = 0.35
        sig_type = "model_flagged_stroke_anomaly"

    # 4. Penalize if out-of-formulary / unverified drug candidate
    is_unverified = False
    if field_name == "medicine_name" and validation_res is not None:
        if validation_res.validation_status in ("not_validated", "unverified", "uncertain"):
            is_unverified = True
            raw_val = min(raw_val, 0.60)
            sig_type = "retrieval_unverified_candidate"
        elif validation_res.selected_reference and float(validation_res.selected_reference.score) < 0.85:
            is_unverified = True
            raw_val = min(raw_val, 0.65)
            sig_type = "retrieval_subthreshold_similarity"
    elif ep_status == "UNVERIFIED":
        is_unverified = True
        raw_val = min(raw_val, 0.60)
        sig_type = "retrieval_unverified_candidate"

    # 5. Image quality degradation penalization
    if image_quality_flags:
        if image_quality_flags.get("blur_detected"):
            raw_val = min(raw_val, 0.55)
            sig_type += "_optical_blur_penalized"
        if image_quality_flags.get("low_resolution"):
            raw_val = min(raw_val, 0.65)
        if image_quality_flags.get("glare_detected"):
            raw_val = min(raw_val, 0.65)

    # 6. Safety Clamp Invariant: Never display >= 0.80 on UNVERIFIED, AMBIGUOUS, or [?]
    if has_illegible_token or has_lasa_ambiguity or is_unverified or ep_status in ("UNVERIFIED", "AMBIGUOUS", "ILLEGIBLE"):
        raw_val = min(raw_val, 0.70)

    return RawConfidenceSignal(
        source=f"multimodal_{model_version}",
        raw_value=round(raw_val, 4) if raw_val is not None else None,
        signal_type=sig_type,
        model_version=model_version,
        config_version=config_version,
    )


def extract_dosage_confidence_signal(
    dosage_field: ExtractedField,
    validation_res: Optional[MedicineValidationResult],
    model_version: str = "gemini-3.8-flash",
    config_version: str = "v1.0",
) -> DosageConfidenceAssessment:
    """
    Extracts dosage confidence strictly grounded in visual handwriting evidence.
    Reference data must NOT increase dosage confidence merely because the reference
    entity contains that dosage.
    """
    observed = dosage_field.value
    raw_sig = extract_field_confidence_signal(
        dosage_field,
        field_name="dosage",
        model_version=model_version,
        config_version=config_version,
    )

    ref_strength = None
    ref_support = "unspecified"

    if validation_res is not None and validation_res.selected_reference is not None:
        ref_strength = validation_res.selected_reference.strength
        if validation_res.formulation_consistency == "consistent":
            ref_support = "matching"
        elif validation_res.formulation_consistency == "mismatch":
            ref_support = "mismatch"
        else:
            ref_support = "not_in_reference"
    elif validation_res is not None:
        ref_support = "not_in_reference"

    explanation = (
        f"Dosage confidence is grounded strictly in visual handwriting extraction clarity (raw score: {raw_sig.raw_value}). "
        f"Observed value '{observed}' is evaluated independently of reference strength '{ref_strength}'."
    )

    if ref_support == "mismatch":
        explanation += " NOTICE: Formulation mismatch detected between observed dosage and reference strength."

    # By default uncalibrated in signal extraction stage
    calibrated_val = None
    cal_status = "uncalibrated" if raw_sig.raw_value is not None else "not_available"

    return DosageConfidenceAssessment(
        observed_dosage=observed,
        reference_strength=ref_strength,
        visual_extraction_confidence=raw_sig,
        reference_support_status=ref_support,
        calibrated=CalibratedConfidence(
            value=calibrated_val,
            calibration_method=None,
            calibration_version=None,
            calibration_status=cal_status,
        ),
        explanation=explanation,
    )


def extract_medicine_identity_confidence(
    name_field: ExtractedField,
    validation_res: Optional[MedicineValidationResult],
    model_version: str = "gemini-3.8-flash",
    config_version: str = "v1.0",
    conflict_delta_threshold: float = 0.30,
) -> MedicineIdentityConfidence:
    """
    Explicitly separates visual extraction confidence from reference correspondence confidence.
    Example: "Amoxi..." has low extraction confidence, but retrieval finds "Amoxicillin" with
    high similarity. The strong retrieval evidence must NOT erase the visual extraction uncertainty.
    """
    visual_sig = extract_field_confidence_signal(
        name_field,
        field_name="medicine_name",
        model_version=model_version,
        config_version=config_version,
    )

    ref_sig = None
    conflict_detected = False
    conflict_note = None

    if validation_res is not None and validation_res.selected_reference is not None:
        retrieval_score = float(validation_res.selected_reference.score)
        ref_sig = RawConfidenceSignal(
            source=f"rag_{validation_res.selected_reference.source}",
            raw_value=round(retrieval_score, 4),
            signal_type=f"retrieval_match_{validation_res.selected_reference.match_method}",
            model_version=None,
            config_version=config_version,
        )

        # Check for conflict: low visual vs high retrieval (or vice versa)
        if visual_sig.raw_value is not None:
            delta = abs(visual_sig.raw_value - retrieval_score)
            if delta >= conflict_delta_threshold:
                conflict_detected = True
                conflict_note = (
                    f"Conflicting Evidence: Visual handwriting clarity is {visual_sig.raw_value:.2f} "
                    f"while formulary retrieval similarity is {retrieval_score:.2f} (delta: {delta:.2f}). "
                    f"Nomenclature match does not erase visual stroke ambiguity."
                )

    elif validation_res is not None:
        # Validation yielded no candidate or ambiguous candidates
        top_score = 0.0
        if validation_res.matched_candidates:
            top_score = float(validation_res.matched_candidates[0].score)
        ref_sig = RawConfidenceSignal(
            source="rag_validation_engine",
            raw_value=round(top_score, 4),
            signal_type=f"retrieval_subthreshold_or_ambiguous ({validation_res.validation_status})",
            model_version=None,
            config_version=config_version,
        )
        if visual_sig.raw_value is not None and visual_sig.raw_value > 0.80 and top_score < 0.70:
            conflict_detected = True
            conflict_note = (
                f"Conflicting Evidence: Visual handwriting appeared clear ({visual_sig.raw_value:.2f}) "
                f"but candidate '{name_field.value}' has no verified formulary correspondence (top score: {top_score:.2f})."
            )

    return MedicineIdentityConfidence(
        visual_extraction_confidence=visual_sig,
        reference_correspondence_confidence=ref_sig,
        combined_calibrated=None,  # Remains None unless a multi-signal calibration model is fitted
        conflict_detected=conflict_detected,
        conflict_note=conflict_note,
    )


def extract_image_quality_confidence_signals(
    metadata: Optional[Any] = None,
    quality_report: Optional[Any] = None,
) -> Dict[str, bool]:
    """
    Extracts structured optical quality degradation flags from ImageMetadata or QualityReport
    so confidence calibrators and abstention policies can downweight or flag visual uncertainty.
    """
    if metadata is not None and hasattr(metadata, "quality_flags"):
        qf = metadata.quality_flags
        if hasattr(qf, "model_dump"):
            return qf.model_dump()
        if isinstance(qf, dict):
            return qf
    if quality_report is not None and hasattr(quality_report, "quality_flags"):
        qf = quality_report.quality_flags
        if hasattr(qf, "model_dump"):
            return qf.model_dump()
        if isinstance(qf, dict):
            return qf
    return {
        "low_resolution": False,
        "blur_detected": False,
        "glare_detected": False,
        "extreme_skew": False,
    }


def detect_confidence_conflicts(
    med: ExtractedMedicine,
    validation_res: Optional[MedicineValidationResult],
    image_metadata: Optional[Any] = None,
) -> List[str]:
    """
    Detects all evidentiary conflicts for a prescribed medication line item.
    Incorporates structured optical quality degradation flags from ImageMetadata.
    """
    conflicts: List[str] = []

    # 1. Truncated cursive stroke ambiguity
    if med.medicine_name.status == "uncertain" or med.medicine_name.extraction_state == "ambiguous":
        conflicts.append("AMBIGUOUS_CURSIVE_STROKE")

    # 2. Visual clarity vs retrieval divergence
    if validation_res is not None:
        med_id_conf = extract_medicine_identity_confidence(med.medicine_name, validation_res)
        if med_id_conf.conflict_detected:
            conflicts.append("VISUAL_RETRIEVAL_DISCREPANCY")

        # 3. Dosage / formulation mismatch
        if validation_res.formulation_consistency == "mismatch":
            conflicts.append("DOSAGE_FORMULATION_MISMATCH")

        # 4. Multi-candidate ambiguity
        if validation_res.validation_status == "uncertain":
            conflicts.append("MULTIPLE_REFERENCE_CANDIDATES")

    # 5. Image quality degradation signals attached to metadata
    if image_metadata is not None:
        q_signals = extract_image_quality_confidence_signals(metadata=image_metadata)
        if q_signals.get("blur_detected"):
            conflicts.append("OPTICAL_BLUR_DEGRADATION")
        if q_signals.get("glare_detected"):
            conflicts.append("GLARE_OVEREXPOSURE_DETECTED")
        if q_signals.get("extreme_skew"):
            conflicts.append("EXTREME_DOCUMENT_SKEW")

    return conflicts
