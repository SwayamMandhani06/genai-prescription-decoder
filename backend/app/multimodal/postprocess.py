"""
Phase 6: Conservative Multimodal Post-Processing
Performs non-interpretive normalization on parsed multimodal extractions:
- Whitespace stripping and null-coalescing
- Conservative human review determination (flags uncertain/missing elements)
- Aggregation of primary fields dictionary for backward compatibility with PLAN.md Section 8
- Strict avoidance of medical inference, drug name mutation, or clinical alteration.
"""

import re
from typing import Dict, List, Optional, Any
from .schemas import (
    ExtractedField,
    ExtractedMedicine,
    PrescriptionExtractionResult,
    ModelMetadata,
)
from ai.rag.normalization import (
    normalize_indian_frequency,
    normalize_indian_duration,
    corroborate_numeric_brand_suffix,
)


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """Collapses consecutive whitespace characters and strips edges. Preserves None."""
    if text is None:
        return None
    cleaned = " ".join(text.strip().split())
    return cleaned if cleaned else None


def postprocess_extracted_field(field: ExtractedField) -> ExtractedField:
    """
    Normalizes whitespace and formats candidates conservatively.
    Enforces strict Phase 6 semantic distinction:
    - MISSING / ABSENT: presence='absent', extraction_state='missing', value=None, status='uncertain'
    - UNCERTAIN: presence='present', extraction_state='ambiguous', status='uncertain'
    - CONFIDENT: presence='present', extraction_state='extracted', status='confident'
    - FLAGGED: status='flagged'
    """
    norm_val = normalize_whitespace(field.value)
    
    # Normalize candidates list
    norm_candidates = []
    seen = set()
    for c in field.candidates:
        c_norm = normalize_whitespace(c)
        if c_norm and c_norm.lower() not in seen:
            seen.add(c_norm.lower())
            norm_candidates.append(c_norm)
            
    if norm_val and norm_val.lower() not in seen:
        norm_candidates.insert(0, norm_val)

    # Determine presence and extraction_state adhering strictly to semantic rules
    if norm_val is None or field.presence == "absent":
        presence = "absent"
        extraction_state = "missing"
        status = "uncertain" if field.status == "confident" else field.status
        unc_reason = None
        explanation = normalize_whitespace(field.explanation) or "Field is not present in the prescription or cannot be located"
    else:
        presence = "present"
        status = field.status
        extraction_state = "ambiguous" if status in ("uncertain", "flagged") else "extracted"
        unc_reason = normalize_whitespace(field.uncertainty_reason)
        explanation = normalize_whitespace(field.explanation)

    return ExtractedField(
        value=norm_val,
        status=status,
        presence=presence,
        extraction_state=extraction_state,
        evidence=field.evidence,
        candidates=norm_candidates,
        explanation=explanation,
        uncertainty_reason=unc_reason,
        verification_instruction=normalize_whitespace(field.verification_instruction),
    )


def postprocess_extracted_medicine(med: ExtractedMedicine) -> ExtractedMedicine:
    """
    Applies conservative field-level normalization across an individual medicine line item:
    - Normalizes Indian posology frequencies (1-0-1 -> BD, 1-1-1 -> TDS, etc.) while preserving raw_frequency
    - Normalizes Indian posology duration fractions (5/7 -> 5 days, 2/52 -> 2 weeks, etc.) while preserving raw_duration
    - Corroborates numeric brand suffixes (Augmentin 625, Dolo 650) against CDSCO formulary without fabricating units
    - Preserves all visual metadata (line_index, raw_transcription, evidence)
    - Enforces Zero Fabrication Rule for route: never defaults to 'Oral' unless written or implied by Tab./Cap.
    """
    norm_name = postprocess_extracted_field(med.medicine_name)
    norm_dosage = postprocess_extracted_field(med.dosage)
    norm_freq = postprocess_extracted_field(med.frequency)
    norm_dur = postprocess_extracted_field(med.duration)

    # 1. Numeric Brand Suffix Corroboration against CDSCO Approved Drugs
    raw_strength = normalize_whitespace(med.strength)
    if norm_name.value:
        clean_brand, candidate_strength = corroborate_numeric_brand_suffix(norm_name.value)
        norm_name.value = clean_brand
        if not raw_strength and candidate_strength:
            raw_strength = candidate_strength

    # Strip trailing formulation words from dosage (e.g. '500 mg tablet' -> '500 mg')
    if norm_dosage.value:
        clean_dose = re.sub(
            r'\s+(tablet|tablets|tab|tabs|capsule|capsules|cap|caps)\b',
            '',
            norm_dosage.value,
            flags=re.IGNORECASE,
        ).strip()
        norm_dosage.value = clean_dose if clean_dose else None

    # Bare-Number Dosage / Unitless Dosage Resolution:
    # If norm_dosage.value after stripping formulation words is missing/empty, just a unitless digit (e.g. "1", "2"),
    # or lacks a recognized strength unit (mg, mcg, g, ml, iu, %), AND raw_strength contains a valid strength unit,
    # set norm_dosage.value = raw_strength.
    if raw_strength:
        has_strength_unit = bool(re.search(r'\b(mg|mcg|g|ml|iu|%)\b', raw_strength, re.IGNORECASE))
        if has_strength_unit:
            dosage_is_empty = not norm_dosage.value or norm_dosage.value.upper() in ("NONE", "N/A", "MISSING")
            dosage_is_bare_digit = bool(re.match(r'^\d+(?:\.\d+)?$', str(norm_dosage.value).strip())) if norm_dosage.value else False
            dosage_lacks_unit = not bool(re.search(r'\b(mg|mcg|g|ml|iu|%)\b', str(norm_dosage.value), re.IGNORECASE)) if norm_dosage.value else False

            if dosage_is_empty or dosage_is_bare_digit or dosage_lacks_unit:
                norm_dosage.value = raw_strength
                norm_dosage.status = "confident"
                norm_dosage.presence = "present"
                norm_dosage.extraction_state = "extracted"
        elif not norm_dosage.value or norm_dosage.value.upper() in ("NONE", "N/A", "MISSING"):
            norm_dosage.value = raw_strength
            norm_dosage.status = "confident"
            norm_dosage.presence = "present"
            norm_dosage.extraction_state = "extracted"
    elif (not norm_dosage.value or norm_dosage.value.upper() in ("NONE", "N/A", "MISSING")) and raw_strength:
        norm_dosage.value = raw_strength
        norm_dosage.status = "confident"
        norm_dosage.presence = "present"
        norm_dosage.extraction_state = "extracted"

    # 2. Indian Frequency Normalization (preserving raw_frequency)
    raw_freq_token = med.raw_frequency or norm_freq.value
    raw_freq_token, norm_freq_plain = normalize_indian_frequency(raw_freq_token)
    if norm_freq.value and norm_freq_plain and norm_freq.value != norm_freq_plain:
        norm_freq.value = norm_freq_plain

    # 3. Indian Duration Normalization (preserving raw_duration)
    raw_dur_token = med.raw_duration or norm_dur.value
    raw_dur_token, norm_dur_plain = normalize_indian_duration(raw_dur_token)
    if norm_dur.value and norm_dur_plain and norm_dur.value != norm_dur_plain:
        norm_dur.value = norm_dur_plain

    norm_abbrevs = []
    for a in med.abbreviations:
        c_a = normalize_whitespace(a)
        if c_a and c_a not in norm_abbrevs:
            norm_abbrevs.append(c_a)

    # Add canonical posology abbreviations if recognized
    if raw_freq_token:
        for f_part in raw_freq_token.replace("-", " ").split():
            if f_part.upper() in ("BD", "TDS", "OD", "HS", "SOS", "PRN", "BBF", "PC", "AC", "QID"):
                up_tok = f_part.upper()
                if up_tok not in norm_abbrevs:
                    norm_abbrevs.append(up_tok)

    # 4. Route: Zero Fabrication Rule
    # If route is not explicitly extracted but dosage_form, abbreviations, or medicine_name explicitly contains oral form markers (Tab, Tablet, Cap, Capsule, Syp, Syrup, Oral), set route to "Oral"
    route_raw = med.route.value if isinstance(med.route, ExtractedField) else med.route
    route_val = normalize_whitespace(route_raw)

    dosage_form_raw = med.dosage_form.value if isinstance(med.dosage_form, ExtractedField) else (med.dosage_form or med.formulation)
    dosage_form = normalize_whitespace(dosage_form_raw)
    formulation = normalize_whitespace(med.formulation or dosage_form_raw)

    if route_val is None:
        raw_tx = med.raw_transcription or ""
        spec_inst = med.special_instructions or ""
        combined_text = f"{dosage_form or ''} {formulation or ''} {' '.join(norm_abbrevs)} {norm_name.value or ''} {raw_tx} {spec_inst}".lower()
        if re.search(r'\b(oral|tab|tablet|tablets|cap|capsule|capsules|syrup|syp)\b', combined_text):
            route_val = "Oral"
        elif re.search(r'\b(inj|injection|iv|im)\b', combined_text):
            route_val = "Injectable"
        elif any(w in combined_text for w in ("eye drop", "eye drops", "ophthalmic")):
            route_val = "Ophthalmic"
        elif any(w in combined_text for w in ("ointment", "cream", "gel", "lotion", "topical")):
            route_val = "Topical"

    if not dosage_form and route_val == "Oral":
        combined_text = f"{formulation or ''} {' '.join(norm_abbrevs)} {norm_name.value or ''}".lower()
        if any(w in combined_text for w in ("cap", "capsule")):
            dosage_form = "Capsule"
        elif any(w in combined_text for w in ("syrup", "syp")):
            dosage_form = "Syrup"
        elif any(w in combined_text for w in ("tab", "tablet")):
            dosage_form = "Tablet"

    # Determine status conservatively
    item_status = med.status
    if any(f.status != "confident" for f in (norm_name, norm_dosage, norm_freq, norm_dur)):
        item_status = "uncertain"
    if any(f.status == "flagged" for f in (norm_name, norm_dosage, norm_freq, norm_dur)):
        item_status = "flagged"

    return ExtractedMedicine(
        medicine_name=norm_name,
        dosage=norm_dosage,
        frequency=norm_freq,
        duration=norm_dur,
        abbreviations=norm_abbrevs,
        status=item_status,
        overall_confidence=med.overall_confidence,
        evidence=med.evidence,
        candidates=norm_name.candidates,
        line_index=med.line_index,
        raw_transcription=med.raw_transcription,
        strength=raw_strength,
        formulation=formulation,
        dosage_form=dosage_form,
        dosage_amount=normalize_whitespace(med.dosage_amount),
        raw_frequency=raw_freq_token,
        frequency_plain=norm_freq_plain or med.frequency_plain,
        raw_duration=raw_dur_token,
        timing_and_food=normalize_whitespace(med.timing_and_food),
        route=route_val,
        special_instructions=normalize_whitespace(med.special_instructions),
        patient_explanation=normalize_whitespace(med.patient_explanation),
        requires_verification=med.requires_verification,
    )


def build_aggregate_fields(medicines: List[ExtractedMedicine]) -> Dict[str, ExtractedField]:
    """
    Constructs the aggregate fields dictionary matching PLAN.md Section 8:
    medicine_name, dosage, frequency, duration, abbreviations.
    If multiple medicines exist, represents the primary line item and indicates multiplicity.
    """
    if not medicines:
        empty_field = ExtractedField(
            value=None,
            status="uncertain",
            presence="absent",
            extraction_state="missing",
            evidence=None,
            candidates=[],
            explanation="No medication items extracted from document",
            uncertainty_reason=None,
        )
        return {
            "medicine_name": empty_field,
            "dosage": empty_field,
            "frequency": empty_field,
            "duration": empty_field,
            "abbreviations": ExtractedField(
                value=None,
                status="uncertain",
                presence="absent",
                extraction_state="missing",
                evidence=None,
                candidates=[],
                explanation="No posology abbreviations observed",
                uncertainty_reason=None,
            ),
        }

    primary = medicines[0]
    
    # Format abbreviations field
    abbrevs_str = ", ".join(primary.abbreviations) if primary.abbreviations else None
    abbrev_field = ExtractedField(
        value=abbrevs_str,
        status="confident" if abbrevs_str else "uncertain",
        presence="present" if abbrevs_str else "absent",
        extraction_state="extracted" if abbrevs_str else "missing",
        evidence=primary.evidence,
        candidates=primary.abbreviations,
        explanation="Preserved posology abbreviations" if abbrevs_str else "No abbreviations observed",
        uncertainty_reason=None,
    )

    return {
        "medicine_name": primary.medicine_name,
        "dosage": primary.dosage,
        "frequency": primary.frequency,
        "duration": primary.duration,
        "abbreviations": abbrev_field,
    }


def finalize_extraction_result(
    prescription_id: str,
    original_image_url: str,
    source_image_sha256: str,
    medicines: List[ExtractedMedicine],
    model_metadata: ModelMetadata,
    duration_seconds: float,
    raw_model_response: Optional[str] = None,
    preprocessed_image_url: Optional[str] = None,
    preprocessed_image_sha256: Optional[str] = None,
    model_demands_review: bool = False,
    prescription_summary: Optional[str] = None,
    patient_details: Optional[Dict[str, Any]] = None,
    doctor_details: Optional[Dict[str, Any]] = None,
    is_prescription: bool = True,
    document_type: str = "prescription",
    rejection_reason: Optional[str] = None,
    document_type_confidence: float = 1.0,
    regions: Optional[List[Dict[str, Any]]] = None,
) -> PrescriptionExtractionResult:
    """
    Finalizes the complete PrescriptionExtractionResult with conservative post-processing:
    - Normalizes all medicine entries
    - Derives requires_human_review strictly:
      True if model demanded review OR if document is rejected/not a prescription
      OR if any medicine or field has status != 'confident'
      OR if no medicines were extracted.
    - Generates aggregate fields dictionary.
    """
    processed_medicines = [postprocess_extracted_medicine(m) for m in medicines]

    # Compute conservative human review requirement
    requires_review = model_demands_review
    if not is_prescription or document_type != "prescription":
        requires_review = True
    elif not processed_medicines:
        requires_review = True
    else:
        for m in processed_medicines:
            if m.status != "confident":
                requires_review = True
                break
            if any(
                f.status != "confident" or f.value is None
                for f in (m.medicine_name, m.dosage, m.frequency, m.duration)
            ):
                requires_review = True
                break

    fields = build_aggregate_fields(processed_medicines)

    return PrescriptionExtractionResult(
        prescription_id=prescription_id,
        original_image_url=original_image_url,
        source_image_sha256=source_image_sha256,
        preprocessed_image_url=preprocessed_image_url,
        preprocessed_image_sha256=preprocessed_image_sha256,
        model=model_metadata,
        inference_mode="mock" if model_metadata.is_mock else "live",
        model_provider=model_metadata.provider,
        model_name=model_metadata.model_id,
        ocr_engine=None,
        is_prescription=is_prescription,
        document_type=document_type,
        rejection_reason=rejection_reason,
        document_type_confidence=document_type_confidence,
        regions=regions or [],
        medicines=processed_medicines,
        fields=fields,
        prescription_summary=prescription_summary,
        patient_details=patient_details,
        doctor_details=doctor_details,
        requires_human_review=requires_review,
        raw_model_response=raw_model_response,
        duration_seconds=round(duration_seconds, 3),
    )
