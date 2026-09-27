"""
Phase 6: Conservative Multimodal Post-Processing
Performs non-interpretive normalization on parsed multimodal extractions:
- Whitespace stripping and null-coalescing
- Conservative human review determination (flags uncertain/missing elements)
- Aggregation of primary fields dictionary for backward compatibility with PLAN.md Section 8
- Strict avoidance of medical inference, drug name mutation, or clinical alteration.
"""

from typing import Dict, List, Optional
from .schemas import (
    ExtractedField,
    ExtractedMedicine,
    PrescriptionExtractionResult,
    ModelMetadata,
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
    """Applies conservative field-level normalization across an individual medicine line item."""
    norm_name = postprocess_extracted_field(med.medicine_name)
    norm_dosage = postprocess_extracted_field(med.dosage)
    norm_freq = postprocess_extracted_field(med.frequency)
    norm_dur = postprocess_extracted_field(med.duration)

    norm_abbrevs = []
    for a in med.abbreviations:
        c_a = normalize_whitespace(a)
        if c_a and c_a not in norm_abbrevs:
            norm_abbrevs.append(c_a)

    # Determine status conservatively: any uncertain/flagged field propagates to item status
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
) -> PrescriptionExtractionResult:
    """
    Finalizes the complete PrescriptionExtractionResult with conservative post-processing:
    - Normalizes all medicine entries
    - Derives requires_human_review strictly:
      True if model demanded review OR if any medicine or field has status != 'confident'
      OR if no medicines were extracted.
    - Generates aggregate fields dictionary.
    """
    processed_medicines = [postprocess_extracted_medicine(m) for m in medicines]

    # Compute conservative human review requirement
    requires_review = model_demands_review
    if not processed_medicines:
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
        medicines=processed_medicines,
        fields=fields,
        requires_human_review=requires_review,
        raw_model_response=raw_model_response,
        duration_seconds=round(duration_seconds, 3),
    )
