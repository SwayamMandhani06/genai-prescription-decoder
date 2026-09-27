"""
Phase 6: Multimodal Response Parser
Extracts and parses structured JSON payload from raw multimodal vision-language model responses.
Handles Markdown code fence stripping, JSON deserialization, defensive error handling,
and converts raw medicine objects into typed representations without hallucinating data.
"""

import json
import re
from typing import Any, Dict, List, Optional
from .evidence import resolve_visual_evidence
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
            evidence=resolve_visual_evidence(None, source=source),
            candidates=[],
            explanation=f"Field '{field_name}' is not present in the prescription or cannot be located",
            uncertainty_reason=None,
            verification_instruction=f"Confirm absence on prescription pad or obtain posology from prescribing practitioner",
        )

    if isinstance(field_data, str):
        val = field_data.strip() if field_data.strip() else None
        status: FieldStatus = "confident" if val else "uncertain"
        presence: FieldPresence = "present" if val else "absent"
        state: ExtractionState = "extracted" if val else "missing"
        return ExtractedField(
            value=val,
            status=status,
            presence=presence,
            extraction_state=state,
            evidence=resolve_visual_evidence(None, source=source),
            candidates=[val] if val else [],
            explanation=f"Observed string: '{val}'" if val else f"Field '{field_name}' is not present or empty",
            uncertainty_reason=None,
            verification_instruction=None if val else f"Confirm absence on prescription pad",
        )

    if not isinstance(field_data, dict):
        return ExtractedField(
            value=str(field_data).strip() if str(field_data).strip() else None,
            status="uncertain",
            presence="present",
            extraction_state="ambiguous",
            evidence=resolve_visual_evidence(None, source=source),
            candidates=[],
            explanation="Unrecognized field representation type",
            uncertainty_reason="Non-standard data structure returned by model",
        )

    # Dictionary representation
    raw_val = field_data.get("value")
    clean_val = str(raw_val).strip() if raw_val is not None and str(raw_val).strip() else None
    
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

    return ExtractedField(
        value=clean_val,
        status=raw_status,
        presence=presence,
        extraction_state=extraction_state,
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

    # Line-level visual evidence
    med_bbox = med_data.get("bounding_box") or med_data.get("region")
    evidence = resolve_visual_evidence(med_bbox, source=source)

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
    )


def parse_multimodal_response(
    raw_text: str,
    source: EvidenceSource = "original_image",
) -> Dict[str, Any]:
    """
    Parses raw multimodal vision-language model response string into dictionary of:
    - medicines: List[ExtractedMedicine]
    - requires_human_review: bool
    - raw_response: str
    
    Raises MultimodalParseError if JSON is corrupt or unparsable.
    """
    cleaned = strip_json_code_fences(raw_text)
    if not cleaned:
        raise MultimodalParseError("Empty response received from multimodal vision model", raw_response=raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise MultimodalParseError(
            f"Failed to decode model JSON output: {str(exc)}",
            raw_response=raw_text,
        ) from exc

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

    parsed_medicines: List[ExtractedMedicine] = []
    for idx, item in enumerate(raw_medicines):
        if not isinstance(item, dict):
            continue
        parsed_med = parse_raw_medicine(item, source=source)
        parsed_medicines.append(parsed_med)

    requires_review = bool(data.get("requires_human_review", False))

    return {
        "medicines": parsed_medicines,
        "requires_human_review": requires_review,
        "raw_response": raw_text,
    }
