"""
Phase 9: Abstention Policy Evaluation Logic.
Translates Phase 6 extraction, Phase 7 validation, and Phase 8 confidence signals
into deterministic, uncertainty-aware field-level and prescription-level acceptance decisions.

Adheres strictly to Phase 9 specification:
- Never silently guesses or chooses candidates.
- Dosage values are strictly immutable.
- Conservative handling of uncalibrated or insufficient-sample data.
- Complete reason-code and conflict traceability.
- Preserves selective prediction metadata for Phase 12 evaluation.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from backend.app.multimodal.schemas import ExtractedField, ExtractedMedicine, PrescriptionExtractionResult
from ai.rag.schemas import MedicineValidationResult
from ai.confidence.schemas import (
    FieldConfidenceAssessment,
    MedicineConfidenceAssessment,
    PrescriptionConfidenceAssessment,
)
from ai.abstention.reasons import AbstentionReasonCode, get_reason_description
from ai.abstention.config import AbstentionPolicyConfig, get_default_abstention_config
from ai.abstention.schemas import (
    FieldAbstentionDecision,
    FieldConfidenceMetadata,
    MedicineAbstentionDecision,
    PrescriptionAbstentionDecision,
)


FIELD_LABEL_MAP: Dict[str, str] = {
    "medicine_name": "Prescribed Medication",
    "dosage": "Dosage Strength",
    "frequency": "Frequency & Administration",
    "duration": "Course Duration",
    "abbreviation": "Clinical Shorthand",
}


def evaluate_field_abstention(
    field_name: str,
    extracted_field: Optional[ExtractedField],
    confidence_assessment: Optional[FieldConfidenceAssessment] = None,
    validation_result: Optional[MedicineValidationResult] = None,
    config: Optional[AbstentionPolicyConfig] = None,
    lasa_result: Optional[Any] = None,
) -> FieldAbstentionDecision:
    """
    Evaluates whether an individual posology field can be safely accepted
    or must be abstained to mandate human verification.
    """
    if config is None:
        config = get_default_abstention_config()

    field_label = FIELD_LABEL_MAP.get(field_name, field_name.replace("_", " ").title())
    original_value = extracted_field.value if extracted_field else None

    reason_codes: List[str] = []
    reasons_detail: List[str] = []
    conflicts: List[str] = []
    observed_dosage_preserved: Optional[bool] = None

    if field_name == "dosage":
        observed_dosage_preserved = True

    # ------------------------------------------------------------------
    # 1. Inspect Field Presence & Extraction State (Phase 6)
    # ------------------------------------------------------------------
    is_missing = (
        extracted_field is None
        or extracted_field.presence == "absent"
        or extracted_field.extraction_state == "missing"
        or extracted_field.value is None
        or extracted_field.value.strip() == ""
    )
    if is_missing:
        if config.abstain_on_field_missing:
            reason_codes.append(AbstentionReasonCode.FIELD_MISSING.value)
            reasons_detail.append(get_reason_description(AbstentionReasonCode.FIELD_MISSING))
    else:
        # Check extraction uncertainty
        if extracted_field.status == "uncertain" or extracted_field.extraction_state == "ambiguous":
            if config.abstain_on_extraction_uncertain:
                reason_codes.append(AbstentionReasonCode.EXTRACTION_UNCERTAIN.value)
                reasons_detail.append(get_reason_description(AbstentionReasonCode.EXTRACTION_UNCERTAIN))

        # Check for ambiguous handwriting strokes / ligatures
        if extracted_field.uncertainty_reason and any(
            w in extracted_field.uncertainty_reason.lower()
            for w in ["cursive", "stroke", "ligature", "ambiguous", "degraded", "truncated"]
        ):
            reason_codes.append(AbstentionReasonCode.AMBIGUOUS_CURSIVE_STROKE.value)
            reasons_detail.append(get_reason_description(AbstentionReasonCode.AMBIGUOUS_CURSIVE_STROKE))

        # Competing candidate hypotheses
        if len(extracted_field.candidates) > 1:
            if config.abstain_on_multiple_candidates:
                reason_codes.append(AbstentionReasonCode.MULTIPLE_CANDIDATES.value)
                cands_str = ", ".join(f"'{c}'" for c in extracted_field.candidates)
                reasons_detail.append(f"Multiple visual extraction candidates detected ({cands_str}).")

    # ------------------------------------------------------------------
    # 2. Inspect Calibration & Probabilistic Confidence (Phase 8)
    # ------------------------------------------------------------------
    raw_val: Optional[float] = None
    cal_val: Optional[float] = None
    cal_status: str = "uncalibrated"
    cal_method: Optional[str] = None

    if confidence_assessment is not None:
        raw_val = confidence_assessment.raw_signal.raw_value
        cal_val = confidence_assessment.calibrated.value
        cal_status = confidence_assessment.calibrated.calibration_status
        cal_method = confidence_assessment.calibrated.calibration_method

        if confidence_assessment.conflict_detected:
            conflicts.append("VISUAL_RETRIEVAL_DISCREPANCY")
            if config.abstain_on_conflict:
                if AbstentionReasonCode.VISUAL_RETRIEVAL_DISCREPANCY.value not in reason_codes:
                    reason_codes.append(AbstentionReasonCode.VISUAL_RETRIEVAL_DISCREPANCY.value)
                    reasons_detail.append(
                        confidence_assessment.conflict_description
                        or get_reason_description(AbstentionReasonCode.VISUAL_RETRIEVAL_DISCREPANCY)
                    )
    elif extracted_field is not None:
        raw_val = getattr(extracted_field, "confidence", None)
        if raw_val is None:
            field_status = getattr(extracted_field, "status", None)
            if field_status == "confident":
                raw_val = 0.94
            elif field_status == "uncertain":
                raw_val = 0.50
            elif field_status == "flagged":
                raw_val = 0.35

    # Process calibration status
    if cal_status == "insufficient_data":
        if config.require_calibration_for_acceptance and not config.allow_uncalibrated_acceptance:
            if AbstentionReasonCode.CALIBRATION_INSUFFICIENT_DATA.value not in reason_codes:
                reason_codes.append(AbstentionReasonCode.CALIBRATION_INSUFFICIENT_DATA.value)
                reasons_detail.append(get_reason_description(AbstentionReasonCode.CALIBRATION_INSUFFICIENT_DATA))
    elif cal_status in ["uncalibrated", "not_available"]:
        if config.require_calibration_for_acceptance and not config.allow_uncalibrated_acceptance:
            if AbstentionReasonCode.CALIBRATION_UNAVAILABLE.value not in reason_codes:
                reason_codes.append(AbstentionReasonCode.CALIBRATION_UNAVAILABLE.value)
                reasons_detail.append(get_reason_description(AbstentionReasonCode.CALIBRATION_UNAVAILABLE))
        elif config.allow_uncalibrated_acceptance:
            # Fallback uncalibrated threshold check
            if raw_val is not None and raw_val < config.min_raw_confidence_fallback:
                reason_codes.append(AbstentionReasonCode.EXTRACTION_UNCERTAIN.value)
                reasons_detail.append(
                    f"Raw model confidence ({raw_val:.2f}) falls below fallback threshold ({config.min_raw_confidence_fallback:.2f})."
                )
    elif cal_status == "calibrated":
        if cal_val is not None and cal_val < config.min_calibrated_confidence:
            reason_codes.append(AbstentionReasonCode.LOW_CALIBRATED_CONFIDENCE.value)
            reasons_detail.append(
                f"Calibrated probability ({cal_val:.2f}) is below policy threshold ({config.min_calibrated_confidence:.2f})."
            )

    # ------------------------------------------------------------------
    # 3. Inspect Reference Formulary Evidence (Phase 7)
    # ------------------------------------------------------------------
    ref_evidence_dict: Optional[Dict[str, Any]] = None

    if validation_result is not None:
        if validation_result.selected_reference:
            ref_evidence_dict = {
                "source": validation_result.selected_reference.source,
                "matched_name": validation_result.selected_reference.medicine_name,
                "score": validation_result.selected_reference.score,
                "strength": validation_result.selected_reference.strength,
                "validation_status": validation_result.validation_status,
                "formulation_consistency": validation_result.formulation_consistency,
            }

        # Check for formulation mismatch (especially relevant for dosage)
        if validation_result.formulation_consistency == "mismatch":
            conflicts.append("DOSAGE_FORMULATION_MISMATCH")
            if field_name == "dosage" or config.dosage_strict_mode:
                if AbstentionReasonCode.DOSAGE_FORMULATION_MISMATCH.value not in reason_codes:
                    reason_codes.append(AbstentionReasonCode.DOSAGE_FORMULATION_MISMATCH.value)
                    reasons_detail.append(
                        f"Observed dosage '{validation_result.observed_dosage}' differs from approved reference strength "
                        f"'{validation_result.reference_strength}'. Observed value is preserved; autonomous acceptance withheld."
                    )

        # Check for uncertain or unvalidated reference outcome
        if validation_result.validation_status == "uncertain":
            conflicts.append("UNCERTAIN_REFERENCE_VALIDATION")
            if field_name == "medicine_name":
                if AbstentionReasonCode.VALIDATION_CONFLICT.value not in reason_codes:
                    reason_codes.append(AbstentionReasonCode.VALIDATION_CONFLICT.value)
                    reasons_detail.append("Reference formulary retrieval produced uncertain or ambiguous candidate status.")

        elif validation_result.validation_status == "not_validated":
            if field_name == "medicine_name":
                if AbstentionReasonCode.UNSUPPORTED_FIELD.value not in reason_codes:
                    reason_codes.append(AbstentionReasonCode.UNSUPPORTED_FIELD.value)
                    reasons_detail.append("Candidate entity has no matching entry in CDSCO or RxNorm reference formularies.")

    # ------------------------------------------------------------------
    # 3.1 Inspect LASA Name Conflict Evidence (Phase 10)
    # ------------------------------------------------------------------
    if field_name == "medicine_name" and lasa_result is not None:
        has_conflict = getattr(lasa_result, "has_lasa_conflict", False)
        if has_conflict:
            conflicts.append("LASA_CONFUSION_RISK")
            if AbstentionReasonCode.LASA_CONFUSION_RISK.value not in reason_codes:
                reason_codes.append(AbstentionReasonCode.LASA_CONFUSION_RISK.value)
                top_name = getattr(lasa_result, "top_confusable_name", None) or "confusable drug entity"
                top_score = getattr(lasa_result, "top_confusable_score", None)
                score_str = f" ({top_score * 100:.1f}% similarity)" if top_score is not None else ""
                reasons_detail.append(
                    f"Look-Alike Sound-Alike (LASA) similarity conflict detected with {top_name}{score_str}. "
                    "Autonomous acceptance withheld; human clinical verification of medicine identity is mandated."
                )

    # ------------------------------------------------------------------
    # 4. Final Determination
    # ------------------------------------------------------------------
    decision = "abstained" if len(reason_codes) > 0 else "accepted"
    requires_human_verification = (decision == "abstained")

    # Selective prediction metadata for future Phase 12 evaluation
    selective_meta = {
        "threshold_used": config.min_calibrated_confidence,
        "policy_version": config.policy_version,
        "is_safety_critical": field_name in ["medicine_name", "dosage"],
        "coverage_candidate": decision == "accepted",
    }

    return FieldAbstentionDecision(
        field_name=field_name,
        field_label=field_label,
        original_value=original_value,
        decision=decision,
        requires_human_verification=requires_human_verification,
        reason_codes=reason_codes,
        reasons_detail=reasons_detail,
        confidence=FieldConfidenceMetadata(
            raw_value=raw_val,
            calibrated_value=cal_val,
            calibration_status=cal_status,
            calibration_method=cal_method,
        ),
        conflicts=conflicts,
        observed_dosage_preserved=observed_dosage_preserved,
        reference_evidence=ref_evidence_dict,
        selective_metadata=selective_meta,
    )


def evaluate_medicine_abstention(
    med: ExtractedMedicine,
    item_index: int,
    confidence_assessment: Optional[MedicineConfidenceAssessment] = None,
    validation_result: Optional[MedicineValidationResult] = None,
    config: Optional[AbstentionPolicyConfig] = None,
    lasa_result: Optional[Any] = None,
) -> MedicineAbstentionDecision:
    """
    Evaluates abstention decisions for all posology fields of an individual medication item.
    """
    if config is None:
        config = get_default_abstention_config()

    field_assessments: Dict[str, FieldConfidenceAssessment] = {}
    if confidence_assessment is not None:
        field_assessments["medicine_name"] = confidence_assessment.medicine_name
        field_assessments["dosage"] = confidence_assessment.dosage.visual_extraction_confidence  # handled via field mapper
        field_assessments["frequency"] = confidence_assessment.frequency
        field_assessments["duration"] = confidence_assessment.duration

    fields: Dict[str, FieldAbstentionDecision] = {}

    # 1. medicine_name
    fields["medicine_name"] = evaluate_field_abstention(
        field_name="medicine_name",
        extracted_field=med.medicine_name,
        confidence_assessment=confidence_assessment.medicine_name if confidence_assessment else None,
        validation_result=validation_result,
        config=config,
        lasa_result=lasa_result,
    )

    # 2. dosage
    fields["dosage"] = evaluate_field_abstention(
        field_name="dosage",
        extracted_field=med.dosage,
        confidence_assessment=None,  # dosage evaluated independently with strict visual grounding
        validation_result=validation_result,
        config=config,
    )

    # 3. frequency
    fields["frequency"] = evaluate_field_abstention(
        field_name="frequency",
        extracted_field=med.frequency,
        confidence_assessment=confidence_assessment.frequency if confidence_assessment else None,
        validation_result=None,
        config=config,
    )

    # 4. duration
    fields["duration"] = evaluate_field_abstention(
        field_name="duration",
        extracted_field=med.duration,
        confidence_assessment=confidence_assessment.duration if confidence_assessment else None,
        validation_result=None,
        config=config,
    )

    abstained_count = sum(1 for f in fields.values() if f.decision == "abstained")
    total_count = len(fields)
    overall_med_decision = "abstained" if abstained_count > 0 else "accepted"

    return MedicineAbstentionDecision(
        item_index=item_index,
        medicine_name=med.medicine_name.value or f"Medication #{item_index}",
        decision=overall_med_decision,
        requires_human_verification=abstained_count > 0,
        fields=fields,
        abstained_fields_count=abstained_count,
        total_fields_count=total_count,
    )


def evaluate_prescription_abstention(
    prescription_id: str,
    extraction_result: Optional[PrescriptionExtractionResult],
    confidence_assessment: Optional[PrescriptionConfidenceAssessment] = None,
    validation_results: Optional[List[MedicineValidationResult]] = None,
    config: Optional[AbstentionPolicyConfig] = None,
    original_image_url: Optional[str] = None,
    lasa_detection: Optional[Any] = None,
) -> PrescriptionAbstentionDecision:
    """
    Consolidates field-level and medicine-level abstention evaluations into a complete
    document-level determination conforming to PLAN.md Section 18.
    Consumes Phase 10 LASA detection evidence to enforce safety abstention.
    """
    if config is None:
        config = get_default_abstention_config()

    primary_fields: Dict[str, FieldAbstentionDecision] = {}
    medicine_decisions: List[MedicineAbstentionDecision] = []
    fields_requiring_verification: List[str] = []

    val_map: Dict[int, MedicineValidationResult] = {}
    if validation_results:
        for idx, vr in enumerate(validation_results):
            val_map[idx] = vr

    # Evaluate medications
    if extraction_result and extraction_result.medicines:
        for idx, med in enumerate(extraction_result.medicines):
            med_conf: Optional[MedicineConfidenceAssessment] = None
            if confidence_assessment and idx < len(confidence_assessment.medicines):
                med_conf = confidence_assessment.medicines[idx]

            med_val = val_map.get(idx)
            med_lasa = None
            if lasa_detection and hasattr(lasa_detection, "medicines") and idx < len(lasa_detection.medicines):
                med_lasa = lasa_detection.medicines[idx]

            med_dec = evaluate_medicine_abstention(
                med=med,
                item_index=idx + 1,
                confidence_assessment=med_conf,
                validation_result=med_val,
                config=config,
                lasa_result=med_lasa,
            )
            medicine_decisions.append(med_dec)

            # Record primary field mapping for medicine #1
            if idx == 0:
                for f_key, f_dec in med_dec.fields.items():
                    primary_fields[f_key] = f_dec
                    if f_dec.requires_human_verification:
                        fields_requiring_verification.append(f_key)
            else:
                for f_key, f_dec in med_dec.fields.items():
                    scoped_key = f"{f_key}_{idx + 1}"
                    primary_fields[scoped_key] = f_dec
                    if f_dec.requires_human_verification:
                        fields_requiring_verification.append(scoped_key)

    total_evaluated = len(primary_fields)
    abstained_count = len(fields_requiring_verification)
    abstention_rate = (abstained_count / total_evaluated) if total_evaluated > 0 else 0.0

    requires_verification = abstained_count > 0
    prescription_decision = "REQUIRES_HUMAN_VERIFICATION" if requires_verification else "ACCEPTED"

    if requires_verification:
        summary = (
            f"Prescription requires clinician/pharmacist human verification: "
            f"{abstained_count} of {total_evaluated} extracted posology fields triggered safety-critical "
            f"abstention conditions under {config.policy_version}."
        )
    else:
        summary = (
            f"Prescription interpretation accepted under {config.policy_version}: "
            f"All {total_evaluated} posology fields satisfied automatic acceptance criteria without conflict."
        )

    now_iso = datetime.now(timezone.utc).isoformat()

    return PrescriptionAbstentionDecision(
        prescription_id=prescription_id,
        policy_version=config.policy_version,
        prescription_decision=prescription_decision,
        requires_human_verification=requires_verification,
        fields=primary_fields,
        medicines=medicine_decisions,
        fields_requiring_verification=fields_requiring_verification,
        total_fields_evaluated=total_evaluated,
        abstained_fields_count=abstained_count,
        abstention_rate=round(abstention_rate, 4),
        summary=summary,
        original_image_url=original_image_url,
        config_hash=config.get_config_hash(),
        timestamp=now_iso,
    )
