"""
Unit tests for Phase 9 Deterministic Mock Fixtures.
Verifies all 15 deterministic scenarios:
- Schema conformance
- Explicit mock/test-only labeling (is_mock = True)
- Correct reason codes and expected decisions
"""

import pytest
from backend.app.fixtures.abstention_fixtures import (
    ABSTENTION_FIXTURES,
    list_abstention_fixtures,
    get_abstention_fixture,
)


class TestAbstentionFixtures:
    def test_fixture_count_is_exactly_15(self):
        fixtures = list_abstention_fixtures()
        assert len(fixtures) == 15

    def test_all_fixtures_explicitly_marked_mock(self):
        for f in list_abstention_fixtures():
            assert f.get("is_mock") is True
            assert "fixture_id" in f
            assert "description" in f

    def test_scenario_01_high_confidence_accept(self):
        f = get_abstention_fixture("CASE-09-01-HIGH-CONFIDENCE-ACCEPT")
        assert f["expected_decision"]["decision"] == "accepted"
        assert f["expected_decision"]["requires_human_verification"] is False

    def test_scenario_02_low_confidence_abstain(self):
        f = get_abstention_fixture("CASE-09-02-LOW-CONFIDENCE-ABSTAIN")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "LOW_CALIBRATED_CONFIDENCE" in f["expected_decision"]["reason_codes"]

    def test_scenario_03_insufficient_calibration(self):
        f = get_abstention_fixture("CASE-09-03-CALIBRATION-INSUFFICIENT")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "CALIBRATION_INSUFFICIENT_DATA" in f["expected_decision"]["reason_codes"]

    def test_scenario_04_uncalibrated_raw_signal(self):
        f = get_abstention_fixture("CASE-09-04-CALIBRATION-UNAVAILABLE")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "CALIBRATION_UNAVAILABLE" in f["expected_decision"]["reason_codes"]

    def test_scenario_05_uncertain_extraction(self):
        f = get_abstention_fixture("CASE-09-05-UNCERTAIN-EXTRACTION")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "EXTRACTION_UNCERTAIN" in f["expected_decision"]["reason_codes"]

    def test_scenario_06_missing_field(self):
        f = get_abstention_fixture("CASE-09-06-MISSING-FIELD")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "FIELD_MISSING" in f["expected_decision"]["reason_codes"]

    def test_scenario_07_multiple_candidates(self):
        f = get_abstention_fixture("CASE-09-07-MULTIPLE-CANDIDATES")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "MULTIPLE_CANDIDATES" in f["expected_decision"]["reason_codes"]

    def test_scenario_08_visual_retrieval_conflict(self):
        f = get_abstention_fixture("CASE-09-08-VISUAL-RETRIEVAL-CONFLICT")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "VISUAL_RETRIEVAL_DISCREPANCY" in f["expected_decision"]["reason_codes"]

    def test_scenario_09_dosage_mismatch_preserved(self):
        f = get_abstention_fixture("CASE-09-09-DOSAGE-FORMULATION-MISMATCH")
        assert f["expected_decision"]["decision"] == "abstained"
        assert f["expected_decision"]["observed_dosage_preserved"] is True
        assert "DOSAGE_FORMULATION_MISMATCH" in f["expected_decision"]["reason_codes"]

    def test_scenario_10_ambiguous_cursive(self):
        f = get_abstention_fixture("CASE-09-10-AMBIGUOUS-CURSIVE")
        assert f["expected_decision"]["decision"] == "abstained"
        assert "AMBIGUOUS_CURSIVE_STROKE" in f["expected_decision"]["reason_codes"]

    def test_scenario_11_multi_medicine_mixed(self):
        f = get_abstention_fixture("CASE-09-11-MULTI-MEDICINE-MIXED-DECISIONS")
        assert f["expected_prescription_decision"] == "REQUIRES_HUMAN_VERIFICATION"
        assert f["expected_requires_human_verification"] is True

    def test_scenarios_12_14_human_verification_actions(self):
        f12 = get_abstention_fixture("CASE-09-12-HUMAN-CONFIRMATION")
        assert f12["expected_record"]["verifier_action"] == "confirm"
        assert f12["expected_record"]["verification_status"] == "confirmed"

        f13 = get_abstention_fixture("CASE-09-13-HUMAN-CORRECTION")
        assert f13["expected_record"]["verifier_action"] == "correct"
        assert f13["expected_record"]["verification_status"] == "corrected"
        assert f13["expected_record"]["verified_value"] != f13["expected_record"]["original_value"]

        f14 = get_abstention_fixture("CASE-09-14-HUMAN-MARKED-UNREADABLE")
        assert f14["expected_record"]["verifier_action"] == "mark_unreadable"
        assert f14["expected_record"]["verified_value"] is None

    def test_unknown_fixture_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_abstention_fixture("NON-EXISTENT-FIXTURE")
