"""
Phase 6: Multimodal Response Parser
Extracts and parses structured JSON payload from raw multimodal vision-language model responses.
Handles Markdown code fence stripping, JSON deserialization, defensive error handling,
and converts raw medicine objects into typed representations without hallucinating data.
"""

import ast
import json
import re
from typing import Any, Dict, List, Optional
from .evidence import resolve_visual_evidence, is_vitals_or_lab_item
from .schemas import (
    BoundingBox,
    ExtractedField,
    ExtractedMedicine,
    FieldStatus,
    FieldPresence,
    ExtractionState,
    VisualEvidence,
    EvidenceSource,
)


class MultimodalParseError(Exception):
    """Raised when the multimodal model output cannot be parsed into valid structured JSON."""
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message)
        self.raw_response = raw_response


def strip_json_code_fences(text: str) -> str:
    """Strips Markdown JSON block markers (` ```json ... ``` `) and trailing whitespace."""
    if not text:
        return ""
    text = text.strip()
    
    # Match ```json ... ``` or ``` ... ```
    pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.match(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def parse_raw_field(
    field_data: Any,
    field_name: str,
    source: EvidenceSource = "original_image",
) -> ExtractedField:
    """
    Parses a single posology or medicine name field from raw model output.
    Enforces strict Phase 6 semantic distinction:
    - MISSING / ABSENT: Field is not present in the prescription or cannot be located
    - UNCERTAIN: Field appears to be present, but visual content cannot be reliably determined
    - CONFIDENT: Field is visually supported with sufficient extraction certainty
    - FLAGGED: Extraction requires explicit review or escalation
    """
    if field_data is None:
        return ExtractedField(
            value=None,
            status="uncertain",
            presence="absent",
            extraction_state="missing",
            epistemic_status="MISSING_ON_RX",
            evidence=resolve_visual_evidence(None, source=source),
            candidates=[],
            explanation=f"Field '{field_name}' is not present in the prescription or cannot be located",
            uncertainty_reason=None,
            verification_instruction=f"Confirm absence on prescription pad or obtain posology from prescribing practitioner",
        )

    if isinstance(field_data, str):
        val = field_data.strip() if field_data.strip() else None
        if val == "ILLEGIBLE" or (val and "[?]" in val):
            return ExtractedField(
                value="ILLEGIBLE" if val == "ILLEGIBLE" else val,
                status="uncertain",
                presence="present",
                extraction_state="ambiguous",
                epistemic_status="ILLEGIBLE",
                evidence=resolve_visual_evidence(None, source=source),
                candidates=[],
                explanation=f"Field '{field_name}' is visually present but unreadable/illegible",
                uncertainty_reason="Handwritten ink strokes are illegible or collapsed",
                verification_instruction="Confirm with prescriber pad or obtain clarification",
            )
        status: FieldStatus = "confident" if val else "uncertain"
        presence: FieldPresence = "present" if val else "absent"
        state: ExtractionState = "extracted" if val else "missing"
        ep_status = "EXTRACTED" if val else "MISSING_ON_RX"
        return ExtractedField(
            value=val,
            status=status,
            presence=presence,
            extraction_state=state,
            epistemic_status=ep_status,
            evidence=resolve_visual_evidence(None, source=source),
            candidates=[val] if val else [],
            explanation=f"Observed string: '{val}'" if val else f"Field '{field_name}' is not present or empty",
            uncertainty_reason=None,
            verification_instruction=None if val else f"Confirm absence on prescription pad",
        )

    if not isinstance(field_data, dict):
        str_val = str(field_data).strip() if str(field_data).strip() else None
        is_illeg = str_val == "ILLEGIBLE" or (str_val and "[?]" in str_val)
        return ExtractedField(
            value=str_val,
            status="uncertain",
            presence="present",
            extraction_state="ambiguous",
            epistemic_status="ILLEGIBLE" if is_illeg else ("MISSING_ON_RX" if not str_val else "AMBIGUOUS"),
            evidence=resolve_visual_evidence(None, source=source),
            candidates=[],
            explanation="Unrecognized field representation type",
            uncertainty_reason="Non-standard data structure returned by model",
        )

    # Dictionary representation
    raw_val = field_data.get("value")
    clean_val = str(raw_val).strip() if raw_val is not None and str(raw_val).strip() else None
    
    if clean_val == "ILLEGIBLE" or (clean_val and "[?]" in clean_val):
        return ExtractedField(
            value="ILLEGIBLE" if clean_val == "ILLEGIBLE" else clean_val,
            status="uncertain",
            presence="present",
            extraction_state="ambiguous",
            epistemic_status="ILLEGIBLE",
            evidence=resolve_visual_evidence(field_data.get("bounding_box") or field_data.get("region"), source=source),
            candidates=field_data.get("candidates", []) if isinstance(field_data.get("candidates"), list) else [],
            explanation=field_data.get("explanation") or f"Field '{field_name}' is visually present but unreadable/illegible",
            uncertainty_reason=field_data.get("uncertainty_reason") or "Handwritten ink strokes are illegible or collapsed",
            verification_instruction=field_data.get("verification_instruction") or "Confirm with prescriber pad or obtain clarification",
        )

    raw_status = field_data.get("status", "confident")
    if raw_status not in ("confident", "uncertain", "flagged"):
        raw_status = "uncertain" if not clean_val else "confident"

    # Explicit presence distinction
    raw_presence = field_data.get("presence")
    if raw_presence in ("present", "absent"):
        presence = raw_presence
    else:
        # Default to absent if value is None and no ambiguous candidates exist
        presence = "absent" if clean_val is None and not field_data.get("candidates") else "present"

    # Explicit extraction state distinction
    raw_state = field_data.get("extraction_state")
    if raw_state in ("extracted", "ambiguous", "missing"):
        extraction_state = raw_state
    else:
        if presence == "absent" or clean_val is None:
            extraction_state = "missing"
        elif raw_status in ("uncertain", "flagged"):
            extraction_state = "ambiguous"
        else:
            extraction_state = "extracted"

    # For absent fields, do not fabricate uncertainty_reason
    if presence == "absent" or extraction_state == "missing":
        unc_reason = None
        explanation = field_data.get("explanation") or f"Field '{field_name}' is not present in the prescription or cannot be located"
    else:
        unc_reason = field_data.get("uncertainty_reason")
        explanation = field_data.get("explanation")
        
    candidates = field_data.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = [str(candidates)] if candidates else []
    clean_candidates = [str(c).strip() for c in candidates if str(c).strip()]
    if clean_val and clean_val not in clean_candidates:
        clean_candidates.insert(0, clean_val)

    bbox_data = field_data.get("bounding_box") or field_data.get("region")
    evidence = resolve_visual_evidence(
        bbox_data,
        source=source,
        note=explanation,
    )

    # Determine epistemic status
    if presence == "absent" or extraction_state == "missing" or clean_val is None:
        ep_status = "MISSING_ON_RX"
    elif raw_status in ("uncertain", "flagged") or extraction_state == "ambiguous" or len(clean_candidates) > 1:
        ep_status = "AMBIGUOUS"
    else:
        ep_status = "EXTRACTED"

    return ExtractedField(
        value=clean_val,
        status=raw_status,
        presence=presence,
        extraction_state=extraction_state,
        epistemic_status=ep_status,
        evidence=evidence,
        candidates=clean_candidates,
        explanation=explanation,
        uncertainty_reason=unc_reason,
        verification_instruction=field_data.get("verification_instruction"),
    )


def parse_raw_medicine(
    med_data: Dict[str, Any],
    source: EvidenceSource = "original_image",
) -> ExtractedMedicine:
    """
    Parses a single medication dictionary item into an ExtractedMedicine schema.
    """
    medicine_name = parse_raw_field(med_data.get("medicine_name"), "medicine_name", source=source)
    dosage = parse_raw_field(med_data.get("dosage"), "dosage", source=source)
    frequency = parse_raw_field(med_data.get("frequency"), "frequency", source=source)
    duration = parse_raw_field(med_data.get("duration"), "duration", source=source)

    # Parse abbreviations
    raw_abbrevs = med_data.get("abbreviations", [])
    if isinstance(raw_abbrevs, str):
        raw_abbrevs = [raw_abbrevs]
    clean_abbrevs = [str(a).strip() for a in raw_abbrevs if str(a).strip()]

    # Parse status
    raw_status = med_data.get("status")
    if raw_status in ("confident", "uncertain", "flagged"):
        item_status: FieldStatus = raw_status
    else:
        # If any core field is uncertain or flagged, bubble up
        if any(f.status != "confident" for f in (medicine_name, dosage, frequency, duration)):
            item_status = "uncertain"
        else:
            item_status = "confident"

    # Overall confidence (raw uncalibrated LLM signal)
    raw_conf = med_data.get("overall_confidence")
    overall_conf: Optional[float] = None
    if raw_conf is not None:
        try:
            val = float(raw_conf)
            if 0.0 <= val <= 1.0:
                overall_conf = round(val, 4)
        except (ValueError, TypeError):
            pass

    # Line-level visual evidence and metadata
    line_idx = med_data.get("line_index")
    if line_idx is not None:
        try:
            line_idx = int(line_idx)
        except (ValueError, TypeError):
            line_idx = None

    raw_transcription = med_data.get("raw_transcription")
    if raw_transcription is not None:
        raw_transcription = str(raw_transcription).strip() or None

    dosage_form = med_data.get("dosage_form") or med_data.get("formulation")
    if dosage_form is not None:
        dosage_form = str(dosage_form).strip() or None

    raw_freq = med_data.get("raw_frequency")
    if not raw_freq and frequency.value:
        raw_freq = frequency.value

    raw_dur = med_data.get("raw_duration")
    if not raw_dur and duration.value:
        raw_dur = duration.value

    med_bbox = med_data.get("bounding_box") or med_data.get("region")
    evidence = resolve_visual_evidence(
        med_bbox,
        source=source,
        line_index=line_idx,
        region_type="MEDICATION_LINE",
    )

    candidates = med_data.get("candidates", [])
    if isinstance(candidates, str):
        candidates = [candidates]
    clean_candidates = [str(c).strip() for c in candidates if str(c).strip()]
    if medicine_name.value and medicine_name.value not in clean_candidates:
        clean_candidates.insert(0, medicine_name.value)

    return ExtractedMedicine(
        medicine_name=medicine_name,
        dosage=dosage,
        frequency=frequency,
        duration=duration,
        abbreviations=clean_abbrevs,
        status=item_status,
        overall_confidence=overall_conf,
        evidence=evidence,
        candidates=clean_candidates,
        line_index=line_idx,
        raw_transcription=raw_transcription,
        strength=med_data.get("strength"),
        formulation=med_data.get("formulation") or dosage_form,
        dosage_form=dosage_form,
        dosage_amount=med_data.get("dosage_amount"),
        raw_frequency=raw_freq,
        frequency_plain=med_data.get("frequency_plain"),
        raw_duration=raw_dur,
        timing_and_food=med_data.get("timing_and_food"),
        route=med_data.get("route"),
        special_instructions=med_data.get("special_instructions"),
        patient_explanation=med_data.get("patient_explanation"),
        requires_verification=bool(med_data.get("requires_verification", False)),
    )


def parse_multimodal_response(
    raw_text: str,
    source: EvidenceSource = "original_image",
) -> Dict[str, Any]:
    """
    Parses raw multimodal vision-language model response string into dictionary of:
    - medicines: List[ExtractedMedicine]
    - regions: List[Dict[str, Any]]
    - requires_human_review: bool
    - prescription_summary: Optional[str]
    - patient_details: Optional[Dict[str, Any]]
    - doctor_details: Optional[Dict[str, Any]]
    - raw_response: str
    
    Raises MultimodalParseError if JSON is corrupt or unparsable.
    """
    cleaned = strip_json_code_fences(raw_text)
    if not cleaned:
        raise MultimodalParseError("Empty response received from multimodal vision model", raw_response=raw_text)

    data = None
    try:
        data = json.loads(cleaned, strict=False)
    except Exception:
        pass

    if data is None:
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        candidate_json = (
            cleaned[first_brace : last_brace + 1]
            if (first_brace != -1 and last_brace > first_brace)
            else cleaned
        )

        # Defensive JSON sanitization: strip comments
        sanitized = re.sub(r"/\*[\s\S]*?\*/", "", candidate_json)
        sanitized = re.sub(r"(?m)^\s*//.*?$", "", sanitized)
        sanitized = re.sub(r",\s*//.*?$", ",", sanitized)

        # Strip repeated/consecutive commas
        sanitized = re.sub(r",\s*,+", ",", sanitized)

        # Iteratively strip trailing commas before closing braces/brackets
        prev = None
        while prev != sanitized:
            prev = sanitized
            sanitized = re.sub(r",\s*([\]}])", r"\1", sanitized)

        try:
            data = json.loads(sanitized, strict=False)
        except Exception as primary_exc:
            # Multi-step cumulative repair pipeline
            repaired = sanitized
            # 1. Quote unquoted property keys (preceded by '{', ',', or newline)
            repaired = re.sub(r'(?<=[{,\n])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r' "\1":', repaired)
            # 2. Quote single-quoted property keys
            repaired = re.sub(r"'([a-zA-Z_][a-zA-Z0-9_]*)'\s*:", r'"\1":', repaired)
            # 3. Insert missing commas between key-value pairs
            repaired = re.sub(r'([}\]"0-9]|true|false|null)\s*\n\s*"([a-zA-Z_][a-zA-Z0-9_]*)":', r'\1,\n "\2":', repaired)
            # 4. Insert missing commas between objects
            repaired = re.sub(r'}\s*\n\s*{', r'},\n{', repaired)
            # 5. Escape invalid backslashes (common in OCR/VLM output)
            repaired = re.sub(r'\\(?![/"\\bfnrtu])', r'\\\\', repaired)
            # 6. Iteratively re-strip trailing commas
            prev = None
            while prev != repaired:
                prev = repaired
                repaired = re.sub(r",\s*([\]}])", r"\1", repaired)

            try:
                data = json.loads(repaired, strict=False)
            except Exception:
                # 7. Python literal eval fallback (converting true/false/null to True/False/None)
                try:
                    repaired_py = re.sub(r'\btrue\b', 'True', repaired)
                    repaired_py = re.sub(r'\bfalse\b', 'False', repaired_py)
                    repaired_py = re.sub(r'\bnull\b', 'None', repaired_py)
                    py_data = ast.literal_eval(repaired_py)
                    if isinstance(py_data, dict):
                        data = py_data
                except Exception:
                    pass

                if data is None:
                    try:
                        # 8. Try replacing single quotes with double quotes
                        repaired_sq = re.sub(r"'(.*?)'", r'"\1"', repaired)
                        data = json.loads(repaired_sq, strict=False)
                    except Exception:
                        raise MultimodalParseError(
                            f"Failed to decode model JSON output: {str(primary_exc)}",
                            raw_response=raw_text,
                        ) from primary_exc

    if not isinstance(data, dict):
        raise MultimodalParseError(
            f"Expected JSON object at root of response, got {type(data).__name__}",
            raw_response=raw_text,
        )

    raw_medicines = data.get("medicines", [])
    if not isinstance(raw_medicines, list):
        raise MultimodalParseError(
            f"Expected 'medicines' to be a list, got {type(raw_medicines).__name__}",
            raw_response=raw_text,
        )

    # Document classification & rejection assessment
    raw_is_rx = data.get("is_prescription")
    doc_type = str(data.get("document_type", "prescription")).lower().strip()
    rejection_reason = data.get("rejection_reason")
    doc_conf = float(data.get("document_type_confidence", 1.0)) if data.get("document_type_confidence") is not None else 1.0

    is_prescription = True
    if raw_is_rx is False or doc_type in ("unrelated_image", "receipt", "packaging_only", "medical_literature", "blank_page", "other"):
        is_prescription = False

    raw_regions = data.get("regions", [])
    parsed_regions = [r for r in raw_regions if isinstance(r, dict)] if isinstance(raw_regions, list) else []

    parsed_medicines: List[ExtractedMedicine] = []
    # If document is verified to NOT be a prescription, reject all extracted medicines to prevent hallucination
    if is_prescription:
        for idx, item in enumerate(raw_medicines):
            if not isinstance(item, dict):
                continue
            parsed_med = parse_raw_medicine(item, source=source)
            # Stage 1 Critical Exclusion: Vitals and lab investigations must NEVER be extracted as medications
            med_val = (parsed_med.medicine_name.value or "").strip()
            if is_vitals_or_lab_item(med_val):
                continue
            parsed_medicines.append(parsed_med)
    else:
        requires_review = True

    requires_review = bool(data.get("requires_human_review", False)) if is_prescription else True

    return {
        "is_prescription": is_prescription,
        "document_type": doc_type if doc_type else ("prescription" if is_prescription else "unrelated_image"),
        "rejection_reason": rejection_reason,
        "document_type_confidence": doc_conf,
        "regions": parsed_regions,
        "medicines": parsed_medicines,
        "requires_human_review": requires_review,
        "prescription_summary": data.get("prescription_summary") if is_prescription else None,
        "patient_details": data.get("patient_details") if is_prescription else None,
        "doctor_details": data.get("doctor_details") if is_prescription else None,
        "raw_response": raw_text,
    }
