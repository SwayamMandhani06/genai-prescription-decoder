"""
Phase 10 Tests: LASA Detector.
Tests the core LASA conflict detection logic:
- Known ISMP pair detection
- Orthographic-only flagging
- Phonetic-only flagging
- Combined threshold behavior
- Risk classification
- Candidate limiting
- Empty / missing input handling
"""

import pytest
from ai.lasa.config import LasaConfig, TALL_MAN_PAIRS
from ai.lasa.detector import screen_medicine, detect_prescription_lasa, _classify_risk, _max_risk
from ai.lasa.schemas import MedicineLasaResult, PrescriptionLasaDetection
from ai.rag.schemas import MedicineReferenceRecord, SourceProvenance


def _make_ref(
    ref_id: str,
    name: str,
    generic: str = None,
    aliases: list = None,
    brand: str = None,
) -> MedicineReferenceRecord:
    """Helper to build reference records for testing."""
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
def reference_pool():
    """A small reference pool with known confusable pairs."""
    return [
        _make_ref("REF-001", "Metformin", generic="Metformin Hydrochloride"),
        _make_ref("REF-002", "Metronidazole", generic="Metronidazole"),
        _make_ref("REF-003", "Prednisolone", generic="Prednisolone Sodium Phosphate"),
        _make_ref("REF-004", "Prednisone", generic="Prednisone"),
        _make_ref("REF-005", "Aspirin", generic="Acetylsalicylic Acid"),
        _make_ref("REF-006", "Omeprazole", generic="Omeprazole"),
        _make_ref("REF-007", "Hydroxyzine", generic="Hydroxyzine Hydrochloride"),
        _make_ref("REF-008", "Hydralazine", generic="Hydralazine Hydrochloride"),
        _make_ref("REF-009", "Chlorpromazine", generic="Chlorpromazine Hydrochloride"),
        _make_ref("REF-010", "Chlorpropamide", generic="Chlorpropamide"),
    ]


@pytest.fixture
def default_config():
    return LasaConfig()


class TestClassifyRisk:
    """Tests for risk classification logic."""

    def test_high_risk(self):
        config = LasaConfig(high_risk_threshold=0.85, medium_risk_threshold=0.70)
        assert _classify_risk(0.90, config) == "high"

    def test_medium_risk(self):
        config = LasaConfig(high_risk_threshold=0.85, medium_risk_threshold=0.70)
        assert _classify_risk(0.75, config) == "medium"

    def test_low_risk(self):
        config = LasaConfig(high_risk_threshold=0.85, medium_risk_threshold=0.70)
        assert _classify_risk(0.50, config) == "low"

    def test_boundary_high(self):
        config = LasaConfig(high_risk_threshold=0.85)
        assert _classify_risk(0.85, config) == "high"

    def test_boundary_medium(self):
        config = LasaConfig(medium_risk_threshold=0.70)
        assert _classify_risk(0.70, config) == "medium"


class TestMaxRisk:
    """Tests for risk level comparison."""

    def test_high_wins(self):
        assert _max_risk("high", "low") == "high"
        assert _max_risk("low", "high") == "high"

    def test_medium_beats_low(self):
        assert _max_risk("medium", "low") == "medium"

    def test_equal(self):
        assert _max_risk("high", "high") == "high"


class TestScreenMedicine:
    """Tests for single-medicine LASA screening."""

    def test_metformin_detects_metronidazole(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        assert isinstance(result, MedicineLasaResult)
        assert result.has_lasa_conflict is True
        # Must detect Metronidazole as confusable
        confusable_names = [c.confusable_name for c in result.confusables]
        assert any("Metronidazole" in n for n in confusable_names)

    def test_metformin_known_pair_flag(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        # At least one confusable should be marked as known pair
        known_pairs = [c for c in result.confusables if c.is_known_pair]
        assert len(known_pairs) > 0

    def test_prednisolone_detects_prednisone(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Prednisolone",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        assert result.has_lasa_conflict is True
        confusable_names = [c.confusable_name for c in result.confusables]
        assert any("Prednisone" in n for n in confusable_names)

    def test_aspirin_no_conflict(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Aspirin",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        # Aspirin should not have high-similarity confusables in our pool
        assert result.prescribed_candidate == "Aspirin"
        # Any detected confusables should be low risk
        for c in result.confusables:
            assert c.combined_score < 0.85

    def test_empty_candidate(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        assert result.has_lasa_conflict is False
        assert result.confusable_count == 0

    def test_empty_reference_pool(self, default_config):
        result = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=[],
            config=default_config,
        )
        # Should still detect known ISMP pairs from Pass 2
        assert result.has_lasa_conflict is True  # Metronidazole is a known pair

    def test_candidate_not_in_pool(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Vinblastine",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        # Vinblastine has known pair Vincristine which is NOT in pool
        # but Pass 2 should still find it
        known_pairs = [c for c in result.confusables if c.is_known_pair]
        assert len(known_pairs) > 0

    def test_max_candidates_limit(self, reference_pool):
        config = LasaConfig(
            combined_threshold=0.01,  # Very low threshold to get many matches
            max_confusable_candidates=2,
        )
        result = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=reference_pool,
            config=config,
        )
        assert len(result.confusables) <= 2

    def test_confusables_sorted_by_score(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        if len(result.confusables) > 1:
            for i in range(len(result.confusables) - 1):
                assert result.confusables[i].combined_score >= result.confusables[i + 1].combined_score

    def test_hydroxyzine_detects_hydralazine(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Hydroxyzine",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        assert result.has_lasa_conflict is True
        confusable_names = [c.confusable_name for c in result.confusables]
        assert any("Hydralazine" in n for n in confusable_names)

    def test_self_not_in_confusables(self, reference_pool, default_config):
        result = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=reference_pool,
            config=default_config,
        )
        for c in result.confusables:
            assert c.confusable_name.lower() != "metformin"


class TestDetectPrescriptionLasa:
    """Tests for prescription-level LASA detection."""

    def test_single_medicine_no_conflict(self, reference_pool, default_config):
        result = detect_prescription_lasa(
            prescription_id="RX-TEST001",
            medicine_names=["Aspirin"],
            reference_records=reference_pool,
            config=default_config,
        )
        assert isinstance(result, PrescriptionLasaDetection)
        assert result.prescription_id == "RX-TEST001"
        assert result.total_medicines_screened == 1

    def test_single_medicine_with_conflict(self, reference_pool, default_config):
        result = detect_prescription_lasa(
            prescription_id="RX-TEST002",
            medicine_names=["Metformin"],
            reference_records=reference_pool,
            config=default_config,
        )
        assert result.has_any_lasa_conflict is True
        assert result.medicines_with_conflicts >= 1
        assert result.highest_risk in ("low", "medium", "high")

    def test_multiple_medicines(self, reference_pool, default_config):
        result = detect_prescription_lasa(
            prescription_id="RX-TEST003",
            medicine_names=["Metformin", "Aspirin", "Prednisolone"],
            reference_records=reference_pool,
            config=default_config,
        )
        assert result.total_medicines_screened == 3
        assert len(result.medicines) == 3

    def test_provenance_metadata(self, reference_pool, default_config):
        result = detect_prescription_lasa(
            prescription_id="RX-TEST004",
            medicine_names=["Metformin"],
            reference_records=reference_pool,
            config=default_config,
        )
        assert result.provenance.policy_version == "lasa_policy_v1"
        assert result.provenance.reference_pool_size == len(reference_pool)
        assert result.provenance.known_pairs_count == len(TALL_MAN_PAIRS)
        assert len(result.provenance.config_hash) == 64  # SHA-256

    def test_empty_medicine_list(self, reference_pool, default_config):
        result = detect_prescription_lasa(
            prescription_id="RX-TEST005",
            medicine_names=[],
            reference_records=reference_pool,
            config=default_config,
        )
        assert result.has_any_lasa_conflict is False
        assert result.total_medicines_screened == 0

    def test_summary_contains_flagged_names(self, reference_pool, default_config):
        result = detect_prescription_lasa(
            prescription_id="RX-TEST006",
            medicine_names=["Metformin"],
            reference_records=reference_pool,
            config=default_config,
        )
        if result.has_any_lasa_conflict:
            assert "Metformin" in result.summary

    def test_item_indices_are_correct(self, reference_pool, default_config):
        result = detect_prescription_lasa(
            prescription_id="RX-TEST007",
            medicine_names=["Drug A", "Drug B", "Drug C"],
            reference_records=reference_pool,
            config=default_config,
        )
        for idx, med in enumerate(result.medicines, start=1):
            assert med.item_index == idx
