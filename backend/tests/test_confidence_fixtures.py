"""
Unit tests for Phase 8 Mock Fixtures.
Verifies that all 14 required mock evaluation scenarios conform to schemas
and demonstrate required scientific properties.
"""

import pytest
from backend.app.fixtures.confidence_fixtures import (
    get_all_confidence_fixtures,
    get_case_1_well_calibrated_high_confidence,
    get_case_2_overconfident_prediction,
    get_case_3_underconfident_prediction,
    get_case_4_perfectly_ambiguous_prediction,
    get_case_5_insufficient_calibration_data,
    get_case_6_missing_raw_confidence,
    get_case_7_calibration_unavailable,
    get_case_8_medicine_name_confidence,
    get_case_9_dosage_confidence_visually_grounded,
    get_case_10_frequency_confidence,
    get_case_11_duration_confidence,
    get_case_12_multiple_medicines_independent_confidence,
    get_case_13_conflicting_extraction_vs_validation,
    get_case_14_reference_supported_visually_uncertain,
)


class TestConfidenceFixtures:
    def test_all_14_fixtures_present(self):
        fixtures = get_all_confidence_fixtures()
        assert len(fixtures) == 14
        for f in fixtures:
            assert f["is_mock"] is True
            assert "fixture_id" in f
            assert "scenario" in f

    def test_fixture_1_well_calibrated(self):
        c1 = get_case_1_well_calibrated_high_confidence()
        assert c1["status"] == "confident"
        assert c1["calibrated"]["calibration_status"] == "calibrated"
        assert c1["calibrated"]["value"] >= 0.90

    def test_fixture_2_overconfident(self):
        c2 = get_case_2_overconfident_prediction()
        assert c2["raw_signal"]["raw_value"] == 0.96
        # Calibrated value is scaled down
        assert c2["calibrated"]["value"] < c2["raw_signal"]["raw_value"]
        assert c2["conflict_detected"] is True

    def test_fixture_3_underconfident(self):
        c3 = get_case_3_underconfident_prediction()
        assert c3["raw_signal"]["raw_value"] == 0.55
        # Calibrated value is scaled up based on empirical accuracy
        assert c3["calibrated"]["value"] > c3["raw_signal"]["raw_value"]

    def test_fixture_4_ambiguous_050(self):
        c4 = get_case_4_perfectly_ambiguous_prediction()
        assert c4["raw_signal"]["raw_value"] == 0.50
        assert c4["status"] == "uncertain"
        assert len(c4["candidates"]) == 2

    def test_fixture_5_insufficient_data(self):
        c5 = get_case_5_insufficient_calibration_data()
        assert c5["calibrated"]["calibration_status"] == "insufficient_data"
        assert c5["calibrated"]["value"] is None

    def test_fixture_6_missing_raw_confidence(self):
        c6 = get_case_6_missing_raw_confidence()
        assert c6["raw_signal"]["raw_value"] is None
        assert c6["calibrated"]["calibration_status"] == "not_available"

    def test_fixture_7_calibration_unavailable(self):
        c7 = get_case_7_calibration_unavailable()
        assert c7["calibrated"]["calibration_status"] == "uncalibrated"
        assert c7["calibrated"]["value"] is None

    def test_fixture_9_dosage_visual_grounding(self):
        c9 = get_case_9_dosage_confidence_visually_grounded()
        assert c9["observed_dosage"] == "500 mg"
        assert c9["reference_support_status"] == "matching"
        assert "strictly" in c9["explanation"].lower()

    def test_fixture_12_multi_medicine_independence(self):
        c12 = get_case_12_multiple_medicines_independent_confidence()
        assert len(c12["medicines"]) == 2
        med1 = c12["medicines"][0]
        med2 = c12["medicines"][1]
        assert med1["status"] == "confident"
        assert med2["status"] == "uncertain"
        assert med1["overall_raw_confidence"] != med2["overall_raw_confidence"]

    def test_fixture_13_conflicting_evidence(self):
        c13 = get_case_13_conflicting_extraction_vs_validation()
        assert c13["conflict_detected"] is True
        assert c13["visual_extraction_confidence"]["raw_value"] == 0.45
        assert c13["reference_correspondence_confidence"]["raw_value"] == 0.98

    def test_fixture_14_reference_supported_visually_uncertain(self):
        c14 = get_case_14_reference_supported_visually_uncertain()
        assert c14["visual_status"] == "uncertain"
        assert c14["retrieval_status"] == "validated"
        assert c14["retained_uncertainty"] is True
