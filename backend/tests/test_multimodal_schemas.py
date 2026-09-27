"""
Unit Tests for Phase 6 Multimodal Schemas & Evidence Mapping
"""

import pytest
from pydantic import ValidationError
from backend.app.multimodal.schemas import (
    BoundingBox,
    VisualEvidence,
    ExtractedField,
    ExtractedMedicine,
    ModelMetadata,
    PrescriptionExtractionResult,
)
from backend.app.multimodal.evidence import resolve_visual_evidence


def test_bounding_box_valid_and_bounds():
    """Verifies that bounding boxes enforce [0.0 - 100.0] percentage coordinate ranges."""
    box = BoundingBox(x=10.0, y=20.0, width=30.0, height=15.0)
    assert box.x == 10.0
    assert box.y == 20.0
    assert box.width == 30.0
    assert box.height == 15.0

    # Negative coordinates must fail
    with pytest.raises(ValidationError):
        BoundingBox(x=-1.0, y=20.0, width=30.0, height=15.0)

    # Coordinates exceeding 100% must fail
    with pytest.raises(ValidationError):
        BoundingBox(x=10.0, y=20.0, width=105.0, height=15.0)


def test_resolve_visual_evidence_valid_and_fallback():
    """Verifies that evidence grounding falls back safely to 'image_level' without fabricating dummy coordinates."""
    # Valid box -> visual_region
    ev_region = resolve_visual_evidence({"x": 12.0, "y": 34.0, "width": 25.0, "height": 10.0})
    assert ev_region.evidence_type == "visual_region"
    assert ev_region.region is not None
    assert ev_region.region.x == 12.0

    # None or empty -> image_level without fake numbers
    ev_empty = resolve_visual_evidence(None)
    assert ev_empty.evidence_type == "image_level"
    assert ev_empty.region is None

    # Corrupt coordinates -> image_level
    ev_corrupt = resolve_visual_evidence({"x": "invalid", "y": 20.0, "width": 30.0, "height": 10.0})
    assert ev_corrupt.evidence_type == "image_level"
    assert ev_corrupt.region is None

    # Out of range coordinates -> image_level
    ev_out_of_bounds = resolve_visual_evidence({"x": 120.0, "y": 20.0, "width": 30.0, "height": 10.0})
    assert ev_out_of_bounds.evidence_type == "image_level"
    assert ev_out_of_bounds.region is None


def test_extracted_field_status_constraint():
    """Verifies that status strictly allows only confident, uncertain, flagged."""
    f1 = ExtractedField(value="Amoxicillin", status="confident")
    assert f1.status == "confident"

    f2 = ExtractedField(value="Amox...", status="uncertain")
    assert f2.status == "uncertain"

    f3 = ExtractedField(value="80 mg", status="flagged")
    assert f3.status == "flagged"

    with pytest.raises(ValidationError):
        ExtractedField(value="Test", status="guessed")  # type: ignore


def test_extracted_field_presence_and_semantic_distinction():
    """
    Verifies Phase 6 semantic distinction:
    - MISSING / ABSENT: presence='absent', extraction_state='missing', value=None
    - UNCERTAIN: presence='present', extraction_state='ambiguous', status='uncertain'
    - CONFIDENT: presence='present', extraction_state='extracted', status='confident'
    - FLAGGED: status='flagged'
    """
    # 1. Missing / Absent field
    f_missing = ExtractedField(
        value=None,
        status="uncertain",
        presence="absent",
        extraction_state="missing",
        explanation="Field 'dosage' is not present in the prescription or cannot be located",
    )
    assert f_missing.presence == "absent"
    assert f_missing.extraction_state == "missing"
    assert f_missing.value is None
    assert f_missing.uncertainty_reason is None

    # 2. Uncertain field (present, but ambiguous visual content)
    f_uncertain = ExtractedField(
        value="Amoxcillin",
        status="uncertain",
        presence="present",
        extraction_state="ambiguous",
        candidates=["Amoxcillin", "Ampicillin"],
        uncertainty_reason="Ambiguous cursive ligature between -ox- and -pi-",
    )
    assert f_uncertain.presence == "present"
    assert f_uncertain.extraction_state == "ambiguous"
    assert f_uncertain.status == "uncertain"
    assert len(f_uncertain.candidates) == 2

    # 3. Confident field
    f_confident = ExtractedField(
        value="Amoxicillin",
        status="confident",
        presence="present",
        extraction_state="extracted",
    )
    assert f_confident.presence == "present"
    assert f_confident.extraction_state == "extracted"
    assert f_confident.status == "confident"

    # Invalid presence must fail
    with pytest.raises(ValidationError):
        ExtractedField(value="Test", presence="unknown")  # type: ignore
