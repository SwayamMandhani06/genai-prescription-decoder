"""
Audit Item 1: SAFETY_ALERT and Similarity Risk Semantics.
Verifies the strict semantic boundary between similarity/conflict severity and clinical risk:
- overall_status = SAFETY_ALERT is an application safety-review state indicating that a potential
  medicine-name conflict requires attention/verification.
- It must NOT mean: clinical danger, adverse drug event, wrong medicine, medical risk probability,
  diagnosis, or prescribing recommendation.
- LasaRiskLevel ("low", "medium", "high") denotes similarity collision severity, not clinical risk.
"""

import pytest
from ai.lasa.config import get_default_lasa_config
from ai.lasa.detector import screen_medicine, detect_prescription_lasa, _classify_risk
from ai.lasa.schemas import LasaSimilarityDetail, MedicineLasaResult, PrescriptionLasaDetection
from backend.app.schemas.prescription import LasaFlagItem, PrescriptionData, LasaScreening


class TestSafetyAlertSemantics:
    """Verifies that LASA conflict detection does NOT claim clinical risk assessment."""

    def test_risk_level_is_similarity_severity_not_clinical_risk(self):
        """Verifies _classify_risk returns similarity conflict severity."""
        config = get_default_lasa_config()
        assert _classify_risk(0.95, config) == "high"
        assert _classify_risk(0.75, config) == "medium"
        assert _classify_risk(0.50, config) == "low"

    def test_clinical_context_contains_safety_disclaimer(self):
        """Verifies that generated clinical_context explicitly disclaims clinical diagnosis."""
        config = get_default_lasa_config()
        result = screen_medicine(
            candidate_name="Metformin",
            item_index=1,
            reference_records=[],
            config=config,
        )
        assert result.has_lasa_conflict is True
        for c in result.confusables:
            # Must contain safety review state statement
            assert "application safety-review state" in c.clinical_context
            # Must NOT claim clinical danger or wrong medicine
            assert "clinical danger" not in c.clinical_context.lower() or "not indicate" in c.clinical_context.lower()
            assert "wrong medicine" not in c.clinical_context.lower() or "not indicate" in c.clinical_context.lower()
            assert "prescribing recommendation" not in c.clinical_context.lower() or "not" in c.clinical_context.lower()

    def test_prescription_summary_safety_boundaries(self):
        """Verifies prescription-level summary disclaims clinical diagnosis and prescribing recommendations."""
        detection = detect_prescription_lasa(
            prescription_id="RX-TEST-001",
            medicine_names=["Metformin"],
            reference_records=[],
        )
        assert detection.has_any_lasa_conflict is True
        assert "application safety-review" in detection.summary
        assert "not clinical danger" in detection.summary

    def test_prescription_data_schema_overall_status_safety_alert_documentation(self):
        """Verifies that PrescriptionData schema documents SAFETY_ALERT semantics."""
        field_info = PrescriptionData.model_fields["overall_status"]
        description = field_info.description or ""
        assert "application safety-review state" in description
        assert "NOT mean clinical danger" in description

    def test_lasa_flag_item_risk_documentation(self):
        """Verifies that LasaFlagItem documents risk as similarity severity, not clinical risk."""
        field_info = LasaFlagItem.model_fields["risk"]
        description = field_info.description or ""
        assert "not a clinical risk assessment" in description

    def test_detector_does_not_assert_wrong_medicine(self):
        """Verifies detector output never declares the prescribed medicine is 'wrong'."""
        result = screen_medicine(
            candidate_name="Prednisolone",
            item_index=1,
            reference_records=[],
        )
        assert result.has_lasa_conflict is True
        for c in result.confusables:
            assert "does not indicate a confirmed error, wrong medicine" in c.clinical_context.lower()
            assert "not assert clinical danger" in c.clinical_context.lower() or "not indicate" in c.clinical_context.lower()
