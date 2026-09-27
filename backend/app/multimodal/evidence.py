"""
Phase 6: Visual Evidence Grounding
Maps extracted clinical fields to visual document regions without coordinate fabrication.
Enforces fallback to 'image_level' when reliable spatial coordinates cannot be determined.
"""

from typing import Any, Dict, Optional
from .schemas import BoundingBox, VisualEvidence, EvidenceSource, EvidenceType


def resolve_visual_evidence(
    box_data: Optional[Dict[str, Any]],
    source: EvidenceSource = "original_image",
    note: Optional[str] = None,
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
            )
    except (ValueError, TypeError):
        pass

    # Safe fallback: never invent fake coordinates
    return VisualEvidence(
        source=source,
        evidence_type="image_level",
        region=None,
        note=note or "Grounded at whole document level",
    )
