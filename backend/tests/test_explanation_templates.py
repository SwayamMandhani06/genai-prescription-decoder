"""
Phase 11 Unit Tests: Posology Explanation Templates and Terminology.
Tests deterministic posology rendering in English, Hindi, and Marathi,
ensuring Roman script preservation for drug names and exact numbers.
"""

import pytest
from ai.explanation.schemas import PosologyTimingSlot
from ai.explanation.templates import PosologyTemplateEngine, STATUS_MESSAGES
from ai.explanation.terminology import (
    build_schedule_slots,
    normalize_frequency_to_key,
    normalize_meal_relation_to_key,
)


def test_standard_english_posology_summary():
    summary = PosologyTemplateEngine.render_summary(
        language="en",
        status="eligible",
        medicine_name="Paracetamol",
        dosage="500 mg",
        frequency_key="twice_daily",
        duration="5 days",
        meal_relation_key="after_meals",
    )
    assert "Paracetamol is listed with a dose of 500 mg" in summary
    assert "twice daily" in summary
    assert "5 days" in summary
    assert "as written on the prescription" in summary


def test_standard_hindi_posology_summary():
    summary = PosologyTemplateEngine.render_summary(
        language="hi",
        status="eligible",
        medicine_name="Paracetamol",
        dosage="500 mg",
        frequency_key="twice_daily",
        duration="5 दिनों",
        meal_relation_key="after_meals",
    )
    assert "Paracetamol" in summary
    assert "500 mg" in summary
    assert "दिन में दो बार" in summary
    assert "5 दिनों" in summary
    assert "प्रिस्क्रिप्शन में" in summary


def test_standard_marathi_posology_summary():
    summary = PosologyTemplateEngine.render_summary(
        language="mr",
        status="eligible",
        medicine_name="Paracetamol",
        dosage="500 mg",
        frequency_key="twice_daily",
        duration="5 दिवस",
        meal_relation_key="after_meals",
    )
    assert "Paracetamol" in summary
    assert "500 mg" in summary
    assert "दिवसातून दोन वेळा" in summary
    assert "5 दिवस" in summary
    assert "प्रिस्क्रिप्शनमध्ये" in summary


def test_missing_fields_renderings():
    # Missing dosage
    s_en = PosologyTemplateEngine.render_summary(
        language="en",
        status="eligible",
        medicine_name="Amoxicillin",
        dosage=None,
        frequency_key="twice_daily",
    )
    assert "Amoxicillin is listed" in s_en
    assert "twice daily" in s_en

    # Missing frequency
    s_hi = PosologyTemplateEngine.render_summary(
        language="hi",
        status="eligible",
        medicine_name="Metformin",
        dosage="500 mg",
        frequency_key=None,
    )
    assert "Metformin" in s_hi
    assert "500 mg" in s_hi


def test_abstained_and_restricted_renderings():
    # Uncertain medicine
    u_en = PosologyTemplateEngine.render_summary(
        language="en",
        status="restricted",
        medicine_name="Amoxi...",
        reason_code="EXTRACTION_OR_VALIDATION_UNCERTAIN",
    )
    assert "could not be read with sufficient confidence" in u_en

    # LASA conflict
    l_en = PosologyTemplateEngine.render_summary(
        language="en",
        status="restricted",
        medicine_name="Prednisone",
        reason_code="LASA_SIMILARITY_CONFLICT",
    )
    assert "Similar medicine names were detected" in l_en

    # Human marked unreadable
    unr_en = PosologyTemplateEngine.render_summary(
        language="en",
        status="abstained",
        medicine_name="",
        reason_code="HUMAN_MARKED_UNREADABLE",
    )
    assert "could not be confirmed from the prescription" in unr_en


def test_schedule_slots_mapping():
    # 1-0-1 -> twice daily -> morning + night slots
    freq_key = normalize_frequency_to_key("1-0-1")
    assert freq_key == "twice_daily"

    slots_en = build_schedule_slots(
        frequency_key=freq_key,
        language="en",
        dosage_str="500 mg",
        meal_relation_key="after_meals",
    )
    assert len(slots_en) == 2
    assert slots_en[0].time_slot == "Morning"
    assert slots_en[0].icon_key == "sun"
    assert slots_en[0].dosage_label == "500 mg"
    assert slots_en[1].time_slot == "Night"
    assert slots_en[1].icon_key == "moon"

    slots_hi = build_schedule_slots(
        frequency_key=freq_key,
        language="hi",
        dosage_str="500 mg",
        meal_relation_key="after_meals",
    )
    assert len(slots_hi) == 2
    assert slots_hi[0].time_slot == "सुबह"
    assert slots_hi[1].time_slot == "रात"

    slots_mr = build_schedule_slots(
        frequency_key=freq_key,
        language="mr",
        dosage_str="500 mg",
        meal_relation_key="after_meals",
    )
    assert len(slots_mr) == 2
    assert slots_mr[0].time_slot == "सकाळी"
    assert slots_mr[1].time_slot == "रात्री"


def test_frequency_normalizer():
    assert normalize_frequency_to_key("BD") == "twice_daily"
    assert normalize_frequency_to_key("TDS") == "three_times_daily"
    assert normalize_frequency_to_key("1-1-1") == "three_times_daily"
    assert normalize_frequency_to_key("OD") == "once_daily"
    assert normalize_frequency_to_key("1-0-0") == "once_daily"
    assert normalize_frequency_to_key("HS") == "at_bedtime"
    assert normalize_frequency_to_key("SOS") == "as_needed"


def test_meal_relation_normalizer():
    assert normalize_meal_relation_to_key(abbreviations=["PC"]) == "after_meals"
    assert normalize_meal_relation_to_key(frequency_raw="After food") == "after_meals"
    assert normalize_meal_relation_to_key(abbreviations=["AC"]) == "before_meals"
    assert normalize_meal_relation_to_key(frequency_raw="Empty stomach") == "empty_stomach"
