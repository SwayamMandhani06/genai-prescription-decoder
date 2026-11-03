"""
Phase 6: Visual Evidence Grounding
Maps extracted clinical fields to visual document regions without coordinate fabrication.
Enforces fallback to 'image_level' when reliable spatial coordinates cannot be determined.
Provides document region segmentation models and vitals/lab filtering guards.
"""

import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from .schemas import BoundingBox, VisualEvidence, EvidenceSource, EvidenceType

RegionType = Literal["HEADER_CLINIC", "PATIENT_INFO", "VITALS_DIAGNOSIS", "MEDICATION_LINE", "ADVICE_FOLLOWUP"]

# Common non-medication clinical terms that must never be classified as medications
VITALS_LAB_PATTERNS = [
    re.compile(r"^\s*(?:b\.?p\.?|blood\s*pressure)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:pulse|p\.?r\.?|heart\s*rate|hr)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:temp(?:erature)?|t(?:emp)?\.?)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:spo2|o2\s*sat|saturation)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:rr|resp(?:iratory)?\s*rate)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:weight|wt|height|ht|bmi)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:cbc|complete\s*blood\s*count|hb|hemoglobin)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:tlc|dlc|esr|platelet(?:s)?|wbc|rbc)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:lft|liver\s*function\s*test|kft|rft|kidney\s*function\s*test)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:serum\s*(?:creatinine|urea|bilirubin|electrolytes))\b", re.IGNORECASE),
    re.compile(r"^\s*(?:hba1c|blood\s*sugar|fbs|ppbs|rbs)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:urine\s*(?:r\/m|routine|c\/s|analysis))\b", re.IGNORECASE),
    re.compile(r"^\s*(?:lipid\s*profile|thyroid|tsh|t3|t4)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:x-?ray|usg|ultrasound|ecg|ekg|mri|ct\s*scan)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:c\/o|complaints?\s*of|diagnosis|dx|k\/c\/o)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:fever|cough|cold|headache|pain|vomiting|diarrhea)\s*$", re.IGNORECASE),
]


def is_vitals_or_lab_item(text: Optional[str]) -> bool:
    """Returns True if the text represents vital signs, lab investigations, or clinical symptoms."""
    if not text:
        return False
    clean = text.strip()
    return any(pattern.search(clean) for pattern in VITALS_LAB_PATTERNS)


class DocumentRegion(BaseModel):
    """Segmented region within a medical prescription document."""
    region_type: RegionType = Field(..., description="Document zone classification")
    line_index: Optional[int] = Field(None, description="1-based visual line index")
    bounding_box: Optional[BoundingBox] = Field(None, description="Percentage bounding box [0.0 - 100.0]")
    raw_text: Optional[str] = Field(None, description="Raw transcription or text observed in region")
    note: Optional[str] = Field(None, description="Clinical or layout context note")


def resolve_visual_evidence(
    box_data: Optional[Dict[str, Any]],
    source: EvidenceSource = "original_image",
    note: Optional[str] = None,
    line_index: Optional[int] = None,
    region_type: Optional[str] = None,
) -> VisualEvidence:
    """
    Validates and constructs VisualEvidence metadata.
    If valid percentage coordinates [0.0 - 100.0] are provided, assigns 'visual_region'.
    Otherwise, safely falls back to 'image_level' without fabricating dummy coordinates.
    """
    if not box_data or not isinstance(box_data, dict):
        return VisualEvidence(
            source=source,
            evidence_type="image_level",
            region=None,
            note=note,
            line_index=line_index,
            region_type=region_type,
        )

    try:
        x = float(box_data.get("x", -1.0))
        y = float(box_data.get("y", -1.0))
        w = float(box_data.get("width", -1.0))
        h = float(box_data.get("height", -1.0))

        # Check bounds: must be positive and within 0 - 100 percentage
        if (0.0 <= x <= 100.0) and (0.0 <= y <= 100.0) and (0.0 < w <= 100.0) and (0.0 < h <= 100.0):
            bbox = BoundingBox(
                x=round(x, 2),
                y=round(y, 2),
                width=round(w, 2),
                height=round(h, 2),
            )
            return VisualEvidence(
                source=source,
                evidence_type="visual_region",
                region=bbox,
                note=note or "Spatial visual region grounded on prescription pad",
                line_index=line_index,
                region_type=region_type,
            )
    except (ValueError, TypeError):
        pass

    # Safe fallback: never invent fake coordinates
    return VisualEvidence(
        source=source,
        evidence_type="image_level",
        region=None,
        note=note or "Grounded at whole document level",
        line_index=line_index,
        region_type=region_type,
    )
