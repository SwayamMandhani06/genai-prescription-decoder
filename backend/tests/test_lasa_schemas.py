"""
Phase 10 Tests: LASA Schemas.
Tests Pydantic schema validation and serialization for all LASA detection models.
"""

import pytest
from ai.lasa.schemas import (
    LasaSimilarityDetail,
    MedicineLasaResult,
    PrescriptionLasaDetection,
    LasaDetectionProvenance,
)


class TestLasaSimilarityDetail:
    """Tests for LasaSimilarityDetail schema."""

    def test_valid_construction(self):
        detail = LasaSimilarityDetail(
            confusable_name="Metronidazole",
            confusable_reference_id="REF-CDSCO-002",
            confusable_generic_name="Metronidazole",
            orthographic_score=0.55,
            phonetic_score=0.70,
            combined_score=0.625,
            metaphone_match=False,
            similarity_type="combined",
            risk_level="medium",
            is_known_pair=True,
            tall_man_prescribed="metFORMIN",
            tall_man_confused="metRONIDAZOLE",
            clinical_context="ISMP high-risk pair flagged.",
        )
        assert detail.confusable_name == "Metronidazole"
        assert detail.risk_level == "medium"
        assert detail.is_known_pair is True

    def test_serialization(self):
        detail = LasaSimilarityDetail(
            confusable_name="Prednisone",
            orthographic_score=0.82,
            phonetic_score=0.75,
            combined_score=0.785,
            metaphone_match=True,
            similarity_type="orthographic",
            risk_level="high",
            clinical_context="High orthographic similarity.",
        )
        data = detail.model_dump()
        assert data["confusable_name"] == "Prednisone"
        assert data["orthographic_score"] == 0.82
        assert data["is_known_pair"] is False

    def test_score_bounds(self):
        with pytest.raises(Exception):
            LasaSimilarityDetail(
                confusable_name="Test",
                orthographic_score=1.5,  # out of bounds
                phonetic_score=0.5,
                combined_score=0.5,
                metaphone_match=False,
                similarity_type="orthographic",
                risk_level="low",
                clinical_context="Test",
            )


class TestMedicineLasaResult:
    """Tests for MedicineLasaResult schema."""

    def test_no_conflict(self):
        result = MedicineLasaResult(
            item_index=1,
            prescribed_candidate="Aspirin",
            normalized_candidate="aspirin",
            has_lasa_conflict=False,
            highest_risk="low",
            confusable_count=0,
            confusables=[],
        )
        assert result.has_lasa_conflict is False
        assert result.confusable_count == 0
        assert result.top_confusable_name is None

    def test_with_conflict(self):
        conf = LasaSimilarityDetail(
            confusable_name="Metronidazole",
            orthographic_score=0.55,
            phonetic_score=0.60,
            combined_score=0.575,
            metaphone_match=False,
            similarity_type="known_pair",
            risk_level="high",
            is_known_pair=True,
            tall_man_prescribed="metFORMIN",
            tall_man_confused="metRONIDAZOLE",
            clinical_context="Known pair.",
        )
        result = MedicineLasaResult(
            item_index=1,
            prescribed_candidate="Metformin",
            normalized_candidate="metformin",
            has_lasa_conflict=True,
            highest_risk="high",
            confusable_count=1,
            confusables=[conf],
            top_confusable_name="Metronidazole",
            top_confusable_score=0.575,
        )
        assert result.has_lasa_conflict is True
        assert result.highest_risk == "high"
        assert result.top_confusable_name == "Metronidazole"


class TestPrescriptionLasaDetection:
    """Tests for PrescriptionLasaDetection schema."""

    def test_no_conflicts_prescription(self):
        prov = LasaDetectionProvenance(
            policy_version="lasa_policy_v1",
            config_hash="abc123",
            orthographic_threshold=0.70,
            phonetic_threshold=0.75,
            combined_threshold=0.65,
            reference_pool_size=10,
            known_pairs_count=20,
            timestamp="2026-09-27T12:00:00Z",
        )
        detection = PrescriptionLasaDetection(
            prescription_id="RX-TEST001",
            has_any_lasa_conflict=False,
            highest_risk="low",
            total_medicines_screened=1,
            medicines_with_conflicts=0,
            medicines=[],
            summary="No conflicts detected.",
            provenance=prov,
        )
        assert detection.has_any_lasa_conflict is False
        assert detection.total_medicines_screened == 1

    def test_full_serialization(self):
        prov = LasaDetectionProvenance(
            policy_version="lasa_policy_v1",
            config_hash="abc123",
            orthographic_threshold=0.70,
            phonetic_threshold=0.75,
            combined_threshold=0.65,
            reference_pool_size=10,
            known_pairs_count=20,
            timestamp="2026-09-27T12:00:00Z",
        )
        detection = PrescriptionLasaDetection(
            prescription_id="RX-TEST001",
            has_any_lasa_conflict=True,
            highest_risk="high",
            total_medicines_screened=2,
            medicines_with_conflicts=1,
            medicines=[],
            summary="1 conflict detected.",
            provenance=prov,
        )
        data = detection.model_dump()
        assert "provenance" in data
        assert data["provenance"]["policy_version"] == "lasa_policy_v1"
        assert data["has_any_lasa_conflict"] is True


class TestLasaDetectionProvenance:
    """Tests for provenance audit metadata."""

    def test_valid_provenance(self):
        prov = LasaDetectionProvenance(
            policy_version="lasa_policy_v1",
            config_hash="sha256hash",
            orthographic_threshold=0.70,
            phonetic_threshold=0.75,
            combined_threshold=0.65,
            reference_pool_size=15,
            known_pairs_count=20,
            timestamp="2026-09-27T15:00:00Z",
        )
        assert prov.policy_version == "lasa_policy_v1"
        assert prov.reference_pool_size == 15
