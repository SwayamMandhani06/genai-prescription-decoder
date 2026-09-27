"""
Unit Tests for Phase 6 Conservative Post-Processing
"""

import pytest
from backend.app.multimodal.schemas import (
    ExtractedField,
    ExtractedMedicine,
    ModelMetadata,
)
from backend.app.multimodal.postprocess import (
    normalize_whitespace,
    postprocess_extracted_field,
    postprocess_extracted_medicine,
    build_aggregate_fields,
    finalize_extraction_result,
)


def test_normalize_whitespace():
    """Verifies that consecutive whitespace is collapsed without mutating None."""
    assert normalize_whitespace("  Amoxicillin   500mg  ") == "Amoxicillin 500mg"
    assert normalize_whitespace("") is None
    assert normalize_whitespace(None) is None


def test_postprocess_field_candidate_deduplication():
    """Verifies candidate deduplication and null value handling."""
    f = ExtractedField(
        value="Amoxicillin",
        status="confident",
        candidates=["amoxicillin", "Amoxicillin", "Ampicillin"],
    )
    res = postprocess_extracted_field(f)
    assert res.value == "Amoxicillin"
    # Case-insensitive dedup preserves distinct entries
    assert len(res.candidates) == 2
    # Check both are present (case-insensitive)
    lower_candidates = [c.lower() for c in res.candidates]
    assert "amoxicillin" in lower_candidates
    assert "ampicillin" in lower_candidates

    # If value is None, status cannot remain 'confident' and presence must be absent
    f_empty = ExtractedField(value=None, status="confident")
    res_empty = postprocess_extracted_field(f_empty)
    assert res_empty.status == "uncertain"
    assert res_empty.presence == "absent"
    assert res_empty.extraction_state == "missing"


def test_postprocess_medicine_status_bubbling():
    """Verifies that any uncertain or flagged field bubbles up to medicine-level status."""
    med = ExtractedMedicine(
        medicine_name=ExtractedField(value="Augmentin", status="confident"),
        dosage=ExtractedField(value="625 mg", status="confident"),
        frequency=ExtractedField(value="1-0-1", status="uncertain"),  # Uncertain!
        duration=ExtractedField(value="5 days", status="confident"),
        abbreviations=["BD"],
        status="confident",
    )
    processed = postprocess_extracted_medicine(med)
    assert processed.status == "uncertain"

    # Flagged field bubbles to flagged
    med_flagged = ExtractedMedicine(
        medicine_name=ExtractedField(value="Atorvastatin", status="confident"),
        dosage=ExtractedField(value="80 mg", status="flagged"),
        frequency=ExtractedField(value="0-0-1", status="confident"),
        duration=ExtractedField(value="30 days", status="confident"),
        abbreviations=["HS"],
        status="confident",
    )
    processed_flagged = postprocess_extracted_medicine(med_flagged)
    assert processed_flagged.status == "flagged"


def test_finalize_extraction_result_conservative_review():
    """Verifies that requires_human_review is set True whenever uncertainty or missing fields exist."""
    meta = ModelMetadata(
        provider="mock",
        model_id="mock-model",
        model_version="1.0",
        prompt_version="v1",
        config_version="v1",
        is_mock=True,
    )

    # 1. Fully confident case
    med_confident = ExtractedMedicine(
        medicine_name=ExtractedField(value="Amoxicillin", status="confident"),
        dosage=ExtractedField(value="500 mg", status="confident"),
        frequency=ExtractedField(value="1-0-1", status="confident"),
        duration=ExtractedField(value="5 days", status="confident"),
        abbreviations=["BD"],
        status="confident",
    )
    res_confident = finalize_extraction_result(
        prescription_id="RX-TEST-01",
        original_image_url="/test.jpg",
        source_image_sha256="aabbcc",
        medicines=[med_confident],
        model_metadata=meta,
        duration_seconds=0.5,
        model_demands_review=False,
    )
    assert res_confident.requires_human_review is False
    assert res_confident.fields["medicine_name"].value == "Amoxicillin"

    # 2. Case with missing dosage -> requires review
    med_missing_dosage = ExtractedMedicine(
        medicine_name=ExtractedField(value="Azithromycin", status="confident"),
        dosage=ExtractedField(value=None, status="uncertain"),
        frequency=ExtractedField(value="1-0-0", status="confident"),
        duration=ExtractedField(value="3 days", status="confident"),
        status="uncertain",
    )
    res_uncertain = finalize_extraction_result(
        prescription_id="RX-TEST-02",
        original_image_url="/test.jpg",
        source_image_sha256="aabbcc",
        medicines=[med_missing_dosage],
        model_metadata=meta,
        duration_seconds=0.5,
        model_demands_review=False,
    )
    assert res_uncertain.requires_human_review is True

    # 3. Empty extraction -> requires review
    res_empty = finalize_extraction_result(
        prescription_id="RX-TEST-03",
        original_image_url="/test.jpg",
        source_image_sha256="aabbcc",
        medicines=[],
        model_metadata=meta,
        duration_seconds=0.1,
    )
    assert res_empty.requires_human_review is True
