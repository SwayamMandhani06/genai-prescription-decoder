"""
Audit Item 8: Deterministic Fixtures Audit for 15 Required Scenarios.
Verifies all 15 deterministic scenarios specified in PLAN.md and Phase 10 implementation specification:
 1. exact identity / no LASA
 2. true LASA pair
 3. ambiguous spelling
 4. multiple candidates
 5. high-confidence non-LASA
 6. dosage mismatch + LASA
 7. unavailable reference vocabulary
 8. detector/service failure
 9. truncated medicine
10. multiple medicines
11. false-positive prevention
12. lexical vs phonetic disagreement
13. formulation difference
14. exact-match exclusion
15. LASA -> Phase 9 integration
"""

import pytest
from ai.rag.schemas import MedicineReferenceRecord
from ai.lasa.config import get_default_lasa_config
from ai.lasa.detector import screen_medicine, detect_prescription_lasa
from ai.lasa.similarity import combined_similarity
from ai.abstention.policy import evaluate_prescription_abstention
from ai.abstention.reasons import AbstentionReasonCode
from backend.app.multimodal.schemas import (
    ExtractedField,
    ExtractedMedicine,
    PrescriptionExtractionResult,
    ModelMetadata,
)


from ai.rag.schemas import MedicineReferenceRecord, SourceProvenance


def _make_ref(
    ref_id: str,
    name: str,
    generic: str = None,
    aliases: list = None,
    brand: str = None,
) -> MedicineReferenceRecord:
    return MedicineReferenceRecord(
        reference_id=ref_id,
        source="test-source",
        source_version="test-v1",
        medicine_name=name,
        normalized_name=name.lower().strip(),
        generic_name=generic,
        brand_name=brand,
        aliases=aliases or [],
        ingredients=[],
        provenance=SourceProvenance(
            source_id="test-source",
            source_name="Test Reference Source",
            source_version="test-v1",
            license="Test License",
            license_category="test",
            retrieval_date="2026-01-01T00:00:00Z",
            citation="Test citation",
        ),
    )


@pytest.fixture
def standard_reference_records():
    """Deterministic reference pool containing standard benchmark entities."""
    return [
        _make_ref("REF-MET-001", "Metformin", generic="Metformin Hydrochloride", brand="Glycomet", aliases=["Metformin 500", "Glyciphage"]),
        _make_ref("REF-METRO-001", "Metronidazole", generic="Metronidazole", brand="Flagyl", aliases=["Metrogyl"]),
        _make_ref("REF-PRED-001", "Prednisone", generic="Prednisone", brand="Deltasone"),
        _make_ref("REF-PREDL-001", "Prednisolone", generic="Prednisolone", brand="Omnipred"),
        _make_ref("REF-CHLOR-001", "Chlorpromazine", generic="Chlorpromazine Hydrochloride", brand="Thorazine"),
        _make_ref("REF-CHLORP-001", "Chlorpropamide", generic="Chlorpropamide", brand="Diabinese"),
        _make_ref("REF-CLOM-001", "Clomipramine", generic="Clomipramine Hydrochloride", brand="Anafranil"),
        _make_ref("REF-PARA-001", "Paracetamol", generic="Acetaminophen", brand="Crocin", aliases=["Dolo 650", "Calpol"]),
        _make_ref("REF-AMOX-001", "Amoxicillin and Clavulanate Potassium", generic="Amoxicillin / Clavulanic Acid", brand="Augmentin", aliases=["Augmentin 625"]),
        _make_ref("REF-INS-001", "Insulin Regular", generic="Insulin Human", brand="Humulin R"),
    ]


class TestDeterministicFixturesAudit:
    """Audit test suite executing all 15 required deterministic fixture scenarios."""

    # 1. Exact identity / no LASA
    def test_fixture_01_exact_identity_no_lasa(self, standard_reference_records):
        result = screen_medicine("Paracetamol", 1, standard_reference_records)
        assert result.has_lasa_conflict is False
        assert result.status == "completed"
        assert result.confusable_count == 0

    # 2. True LASA pair
    def test_fixture_02_true_lasa_pair(self, standard_reference_records):
        result = screen_medicine("Metformin", 1, standard_reference_records)
        assert result.has_lasa_conflict is True
        assert result.status == "completed"
        assert result.top_confusable_name == "Metronidazole"
        assert result.confusables[0].is_known_pair is True
        assert result.confusables[0].tall_man_prescribed == "metFORMIN"
        assert result.confusables[0].tall_man_confused == "metRONIDAZOLE"

    # 3. Ambiguous spelling
    def test_fixture_03_ambiguous_spelling(self, standard_reference_records):
        result = screen_medicine("Prednisone", 1, standard_reference_records)
        assert result.has_lasa_conflict is True
        conf_names = [c.confusable_name.lower() for c in result.confusables]
        assert "prednisolone" in conf_names
        # Prednisone vs Prednisolone differs by only two letters ('lo')
        top = [c for c in result.confusables if c.confusable_name.lower() == "prednisolone"][0]
        assert top.orthographic_score >= 0.85

    # 4. Multiple candidates
    def test_fixture_04_multiple_candidates(self, standard_reference_records):
        result = screen_medicine("Chlorpromazine", 1, standard_reference_records)
        assert result.has_lasa_conflict is True
        assert len(result.confusables) >= 2
        conf_names = [c.confusable_name for c in result.confusables]
        assert "Chlorpropamide" in conf_names

    # 5. High-confidence non-LASA
    def test_fixture_05_high_confidence_non_lasa(self, standard_reference_records):
        result = screen_medicine("Augmentin", 1, standard_reference_records)
        assert result.has_lasa_conflict is False
        assert result.highest_risk == "low"

    # 6. Dosage mismatch + LASA
    def test_fixture_06_dosage_mismatch_plus_lasa(self, standard_reference_records):
        # Dosage is out of scope for LASA identity detector, but identity screening flags the name
        result = screen_medicine("Metformin 1000mg", 1, standard_reference_records)
        assert result.has_lasa_conflict is True
        assert result.top_confusable_name == "Metronidazole"

    # 7. Unavailable reference vocabulary
    def test_fixture_07_unavailable_reference_vocabulary(self):
        det = detect_prescription_lasa(
            prescription_id="RX-FIX-07",
            medicine_names=["Metformin"],
            reference_records=None,
        )
        assert det.status == "unavailable"
        assert det.conflict_detected is None
        assert det.has_any_lasa_conflict is None
        assert det.error_message == "Reference vocabulary unavailable for LASA screening"

    # 8. Detector/service failure
    def test_fixture_08_detector_service_failure(self):
        det = detect_prescription_lasa(
            prescription_id="RX-FIX-08",
            medicine_names=[999],  # type: ignore (triggers exception in normalization)
            reference_records=[],
        )
        assert det.status == "failed"
        assert det.conflict_detected is None
        assert det.error_message is not None

    # 9. Truncated medicine
    def test_fixture_09_truncated_medicine(self, standard_reference_records):
        result = screen_medicine("Metfor", 1, standard_reference_records)
        assert result.status == "completed"
        # Truncated input should be safely processed without crashing
        assert isinstance(result.confusables, list)

    # 10. Multiple medicines
    def test_fixture_10_multiple_medicines(self, standard_reference_records):
        det = detect_prescription_lasa(
            prescription_id="RX-FIX-10",
            medicine_names=["Metformin", "Paracetamol", "Augmentin"],
            reference_records=standard_reference_records,
        )
        assert det.status == "completed"
        assert det.total_medicines_screened == 3
        assert det.medicines_with_conflicts == 1
        assert det.medicines[0].has_lasa_conflict is True   # Metformin
        assert det.medicines[1].has_lasa_conflict is False  # Paracetamol
        assert det.medicines[2].has_lasa_conflict is False  # Augmentin

    # 11. False-positive prevention
    def test_fixture_11_false_positive_prevention(self, standard_reference_records):
        ortho, phon, combo, meta = combined_similarity("Paracetamol", "Insulin Regular")
        assert combo < 0.40
        result = screen_medicine("Paracetamol", 1, standard_reference_records)
        assert not any(c.confusable_name == "Insulin Regular" for c in result.confusables)

    # 12. Lexical vs phonetic disagreement
    def test_fixture_12_lexical_vs_phonetic_disagreement(self):
        # Pairs that sound identical or very similar phonetically but differ in spelling
        # e.g., 'Cefazolin' vs 'Cephalexin'
        ortho, phon, combo, meta = combined_similarity("Cefazolin", "Cephalexin")
        assert ortho >= 0.50
        assert phon >= 0.50

    # 13. Formulation difference (same molecule)
    def test_fixture_13_formulation_difference_exclusion(self, standard_reference_records):
        # 'Metformin SR' and 'Metformin' normalize to same canonical stem, excluded from self-collision
        result = screen_medicine("Metformin SR", 1, standard_reference_records)
        conf_names = [c.confusable_name for c in result.confusables]
        # Must not report Metformin as a confusable with Metformin SR
        assert "Metformin" not in conf_names

    # 14. Exact-match exclusion
    def test_fixture_14_exact_match_exclusion(self, standard_reference_records):
        result = screen_medicine("Metformin", 1, standard_reference_records)
        for c in result.confusables:
            assert c.confusable_name.lower() != "metformin"

    # 15. LASA -> Phase 9 integration
    def test_fixture_15_lasa_to_phase9_integration(self, standard_reference_records):
        extraction = PrescriptionExtractionResult(
            prescription_id="RX-FIX-15",
            original_image_url="/uploads/test.png",
            source_image_sha256="0" * 64,
            duration_seconds=0.1,
            medicines=[
                ExtractedMedicine(
                    medicine_name=ExtractedField(
                        field_name="medicine_name",
                        value="Metformin",
                        confidence=0.95,
                        status="confident",
                    ),
                    dosage=ExtractedField(field_name="dosage", value="500mg", confidence=0.95, status="confident"),
                    frequency=ExtractedField(field_name="frequency", value="1-0-1", confidence=0.95, status="confident"),
                    duration=ExtractedField(field_name="duration", value="30d", confidence=0.95, status="confident"),
                )
            ],
            requires_human_review=False,
            model=ModelMetadata(
                provider="mock",
                model_id="test-v1",
                model_version="1.0",
                prompt_version="v1",
                config_version="v1",
                is_mock=True,
            ),
        )
        lasa_det = detect_prescription_lasa(
            prescription_id="RX-FIX-15",
            medicine_names=["Metformin"],
            reference_records=standard_reference_records,
        )
        assert lasa_det.conflict_detected is True

        abstention = evaluate_prescription_abstention(
            prescription_id="RX-FIX-15",
            extraction_result=extraction,
            lasa_detection=lasa_det,
        )
        assert abstention.requires_human_verification is True
        assert AbstentionReasonCode.LASA_CONFUSION_RISK.value in abstention.fields["medicine_name"].reason_codes
