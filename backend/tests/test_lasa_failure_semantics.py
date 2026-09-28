"""
Audit Item 4: Detection Failure Semantics Test.
Verifies the strict contract requirements for detection failure states:
1. status = 'completed' and conflict_detected = False means:
   'LASA screening completed and no conflict was detected.'
2. Where screening fails or reference vocabulary is inaccessible:
   status = 'failed' or 'unavailable', and conflict_detected = None.
3. System must NEVER return conflict_detected = False when detection did not actually complete.
"""

import pytest
from ai.lasa.detector import screen_medicine, detect_prescription_lasa
from ai.lasa.schemas import PrescriptionLasaDetection, MedicineLasaResult


class TestDetectionFailureSemantics:
    """Verifies that failure/unavailability states never report clean completion."""

    def test_completed_no_conflict_semantics(self):
        """When screening completes and finds no conflicts, conflict_detected is explicitly False."""
        det = detect_prescription_lasa(
            prescription_id="RX-TEST-CLEAN",
            medicine_names=["Paracetamol"],
            reference_records=[],
        )
        assert det.status == "completed"
        assert det.conflict_detected is False
        assert det.has_any_lasa_conflict is False
        assert det.error_message is None
        assert "completed" in det.summary.lower()

    def test_completed_with_conflict_semantics(self):
        """When screening completes and finds conflicts, conflict_detected is explicitly True."""
        det = detect_prescription_lasa(
            prescription_id="RX-TEST-CONFLICT",
            medicine_names=["Metformin"],
            reference_records=[],
        )
        assert det.status == "completed"
        assert det.conflict_detected is True
        assert det.has_any_lasa_conflict is True
        assert det.error_message is None

    def test_unavailable_vocabulary_semantics(self):
        """When reference vocabulary is None (unavailable), conflict_detected MUST be None, not False."""
        det = detect_prescription_lasa(
            prescription_id="RX-TEST-UNAVAIL",
            medicine_names=["Metformin"],
            reference_records=None,  # Vocabulary unavailable
        )
        assert det.status == "unavailable"
        # CRITICAL CONTRACT REQUIREMENT: conflict_detected must NOT be False!
        assert det.conflict_detected is None
        assert det.has_any_lasa_conflict is None
        assert det.error_message is not None
        assert "unavailable" in det.summary.lower()

    def test_unavailable_single_medicine_semantics(self):
        """When screening single medicine with None reference records, has_lasa_conflict is None."""
        res = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=None,
        )
        assert res.status == "unavailable"
        assert res.has_lasa_conflict is None
        assert res.error_message is not None

    def test_failed_detector_semantics(self):
        """When an exception occurs during detection, status is 'failed' and conflict_detected is None."""
        # Pass a non-string object in medicine_names that triggers an internal error
        det = detect_prescription_lasa(
            prescription_id="RX-TEST-FAIL",
            medicine_names=[12345],  # type: ignore (triggers exception in normalization)
            reference_records=[],
        )
        assert det.status == "failed"
        assert det.conflict_detected is None
        assert det.has_any_lasa_conflict is None
        assert det.error_message is not None
        assert "failed" in det.summary.lower()

    def test_schema_prevents_false_when_not_completed(self):
        """Pydantic validator enforces that conflict_detected cannot be False when status != 'completed'."""
        det = PrescriptionLasaDetection(
            prescription_id="RX-VALIDATOR-TEST",
            status="failed",
            conflict_detected=False,  # Deliberately trying to pass False on failure
            highest_risk="low",
            total_medicines_screened=0,
            medicines_with_conflicts=0,
            medicines=[],
            summary="Testing validator",
            provenance={
                "policy_version": "lasa_policy_v1",
                "config_hash": "dummy",
                "orthographic_threshold": 0.7,
                "phonetic_threshold": 0.75,
                "combined_threshold": 0.65,
                "reference_pool_size": 0,
                "known_pairs_count": 20,
                "timestamp": "2026-09-28T00:00:00Z",
            },
        )
        # Validator must have overridden conflict_detected to None
        assert det.conflict_detected is None
        assert det.has_any_lasa_conflict is None
