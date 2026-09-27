"""
Schema and API Contract Conformance Tests
Verifies strict adherence to PLAN.md Section 6 Core Response Contract and Error Contract.
"""

import pytest
from pydantic import ValidationError
from backend.app.schemas.prescription import (
    FieldExtractionItem,
    LasaFlagItem,
    ValidationItem,
    MultilingualSummary,
    PrescriptionAnalyzeResponse,
)
from backend.app.schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from backend.app.fixtures.mock_fixtures import (
    get_confident_fixture,
    get_uncertain_fixture,
    get_lasa_fixture,
    get_abstained_fixture,
)


def test_section_6_field_status_semantic_constraint():
    """Verifies that field extraction status must be exactly one of: confident, uncertain, flagged."""
    # Valid statuses
    f1 = FieldExtractionItem(value="Amoxicillin", confidence=0.91, status="confident")
    assert f1.status == "confident"

    f2 = FieldExtractionItem(value="TID", confidence=0.60, status="uncertain")
    assert f2.status == "uncertain"

    f3 = FieldExtractionItem(value="Prednisolone", confidence=0.42, status="flagged")
    assert f3.status == "flagged"

    # Invalid status should be rejected by Pydantic
    with pytest.raises(ValidationError):
        FieldExtractionItem(value="Invalid", confidence=0.50, status="guessing")


def test_section_6_lasa_flag_schema():
    """Verifies that LASA flag items conform to PLAN.md Section 6 specification."""
    flag = LasaFlagItem(
        field="medicine_name",
        conflict_with="Metronidazole",
        risk="high",
        similarity_score=82.0,
        tall_man_prescribed="metFORMIN",
        tall_man_confused="metRONIDAZOLE",
        details="Similarity conflict detected.",
    )
    assert flag.field == "medicine_name"
    assert flag.conflict_with == "Metronidazole"
    assert flag.risk == "high"


def test_section_6_validation_schema():
    """Verifies validation evidence record format."""
    val = ValidationItem(
        found_in_db=True,
        source="CDSCO",
        matched_entity_name="Augmentin 625 Duo",
        generic_salt="Amoxicillin + Clavulanic Acid",
        rxnorm_cui="226829",
        cdsco_schedule="Schedule H (Prescription Drug)",
    )
    assert val.found_in_db is True
    assert val.source == "CDSCO"


def test_section_6_error_contract():
    """Verifies that ErrorResponse conforms to PLAN.md Section 6 JSON shape."""
    err = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.PROCESSING_FAILED,
            message="The prescription could not be processed.",
            stage="multimodal_extraction",
            retryable=True,
            details={"reason": "stroke_occlusion"},
        ),
        prescription_id="rx_00123",
        original_image_url="/uploads/rx_00123.jpg",
    )
    d = err.model_dump()
    assert d["error"]["code"] == "PROCESSING_FAILED"
    assert d["error"]["message"] == "The prescription could not be processed."
    assert d["error"]["stage"] == "multimodal_extraction"
    assert d["error"]["retryable"] is True
    assert d["prescription_id"] == "rx_00123"
    assert d["original_image_url"] == "/uploads/rx_00123.jpg"


def test_fixtures_adhere_to_prescription_analyze_response():
    """Verifies that all 4 fixtures strictly validate as PrescriptionAnalyzeResponse."""
    confident = get_confident_fixture()
    assert isinstance(confident, PrescriptionAnalyzeResponse)
    assert confident.status == "success"
    assert "medicine_name" in confident.fields
    assert confident.fields["medicine_name"].status == "confident"

    uncertain = get_uncertain_fixture()
    assert isinstance(uncertain, PrescriptionAnalyzeResponse)
    assert uncertain.requires_human_review is True
    assert uncertain.fields["frequency"].status == "uncertain"

    lasa = get_lasa_fixture()
    assert isinstance(lasa, PrescriptionAnalyzeResponse)
    assert len(lasa.lasa_flags) > 0
    assert lasa.lasa_flags[0].conflict_with == "Metronidazole"

    abstained = get_abstained_fixture()
    assert isinstance(abstained, PrescriptionAnalyzeResponse)
    assert abstained.data.overall_status == "ABSTAINED"
    assert abstained.requires_human_review is True
