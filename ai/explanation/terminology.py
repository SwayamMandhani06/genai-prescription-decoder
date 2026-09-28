"""
Phase 11: Controlled Multilingual Prescription Terminology.
Provides deterministic, verified semantic translations for prescription concepts,
abbreviations, posology schedules, and precautions across English, Hindi, and Marathi.
"""

from typing import Dict, List, Optional
from ai.explanation.schemas import LanguageCode, PosologyTimingSlot

# ------------------------------------------------------------------------------
# Core Clinical Concepts
# ------------------------------------------------------------------------------

CORE_CONCEPTS: Dict[str, Dict[LanguageCode, str]] = {
    "medicine": {
        "en": "Medicine",
        "hi": "दवा",
        "mr": "औषध",
    },
    "dosage": {
        "en": "Dose",
        "hi": "खुराक",
        "mr": "मात्रा",
    },
    "frequency": {
        "en": "Frequency",
        "hi": "बारंबारता",
        "mr": "वारंवारता",
    },
    "duration": {
        "en": "Duration",
        "hi": "अवधि",
        "mr": "कालावधी",
    },
    "as_written": {
        "en": "as written on the prescription",
        "hi": "जैसा कि प्रिस्क्रिप्शन में लिखा है",
        "mr": "जसे प्रिस्क्रिप्शनमध्ये लिहिले आहे",
    },
    "prescribed_dose": {
        "en": "prescribed dose",
        "hi": "निर्धारित खुराक",
        "mr": "ठरवून दिलेला डोस",
    },
    "verification_notice": {
        "en": "Requires clinician or pharmacist verification before use.",
        "hi": "उपयोग से पहले डॉक्टर या फार्मासिस्ट द्वारा सत्यापन आवश्यक है।",
        "mr": "वापरण्यापूर्वी डॉक्टर किंवा फार्मासिस्टद्वारे खात्री करणे आवश्यक आहे.",
    },
}

# ------------------------------------------------------------------------------
# Frequency & Schedule Mappings
# ------------------------------------------------------------------------------

FREQUENCY_TERMS: Dict[str, Dict[LanguageCode, str]] = {
    "once_daily": {
        "en": "once daily",
        "hi": "दिन में एक बार",
        "mr": "दिवसातून एकदा",
    },
    "twice_daily": {
        "en": "twice daily",
        "hi": "दिन में दो बार",
        "mr": "दिवसातून दोन वेळा",
    },
    "three_times_daily": {
        "en": "three times daily",
        "hi": "दिन में तीन बार",
        "mr": "दिवसातून तीन वेळा",
    },
    "four_times_daily": {
        "en": "four times daily",
        "hi": "दिन में चार बार",
        "mr": "दिवसातून चार वेळा",
    },
    "as_needed": {
        "en": "as needed when required",
        "hi": "आवश्यकता पड़ने पर",
        "mr": "गरज भासल्यास",
    },
    "at_bedtime": {
        "en": "at bedtime",
        "hi": "सोने से पहले",
        "mr": "झोपण्यापूर्वी",
    },
}

# ------------------------------------------------------------------------------
# Meal Relations & Timing
# ------------------------------------------------------------------------------

MEAL_RELATIONS: Dict[str, Dict[LanguageCode, str]] = {
    "after_meals": {
        "en": "after meals",
        "hi": "भोजन के बाद",
        "mr": "जेवणानंतर",
    },
    "before_meals": {
        "en": "before meals",
        "hi": "भोजन से पहले",
        "mr": "जेवणापूर्वी",
    },
    "with_meals": {
        "en": "with meals",
        "hi": "भोजन के साथ",
        "mr": "जेवणासोबत",
    },
    "empty_stomach": {
        "en": "on an empty stomach",
        "hi": "खाली पेट",
        "mr": "उपाशीपोटी",
    },
    "unspecified": {
        "en": "as directed by your doctor",
        "hi": "डॉक्टर के निर्देशानुसार",
        "mr": "डॉक्टरांच्या सल्ल्यानुसार",
    },
}

# ------------------------------------------------------------------------------
# Time Period Slots
# ------------------------------------------------------------------------------

PERIOD_LABELS: Dict[str, Dict[LanguageCode, str]] = {
    "morning": {
        "en": "Morning",
        "hi": "सुबह",
        "mr": "सकाळी",
    },
    "afternoon": {
        "en": "Afternoon",
        "hi": "दोपहर",
        "mr": "दुपारी",
    },
    "evening": {
        "en": "Evening",
        "hi": "शाम",
        "mr": "संध्याकाळी",
    },
    "night": {
        "en": "Night",
        "hi": "रात",
        "mr": "रात्री",
    },
}

# ------------------------------------------------------------------------------
# Standard Patient Precautions
# ------------------------------------------------------------------------------

STANDARD_PRECAUTIONS: Dict[LanguageCode, List[str]] = {
    "en": [
        "Complete the full prescribed course as directed by your physician.",
        "Do not alter or skip doses without consulting your doctor or pharmacist.",
        "Store in a cool, dry place away from direct sunlight.",
    ],
    "hi": [
        "अपने चिकित्सक द्वारा बताए अनुसार पूरा निर्धारित कोर्स पूरा करें।",
        "अपने डॉक्टर या फार्मासिस्ट से परामर्श किए बिना खुराक न बदलें और न ही छोड़ें।",
        "सीधी धूप से दूर ठंडी और सूखी जगह पर रखें।",
    ],
    "mr": [
        "आपल्या डॉक्टरांच्या सल्ल्यानुसार औषधांचा पूर्ण ठरवून दिलेला कोर्स पूर्ण करा.",
        "आपल्या डॉक्टर किंवा फार्मासिस्टचा सल्ला घेतल्याशिवाय डोस बदलू नका किंवा वगळू नका.",
        "थेट सूर्यप्रकाशापासून दूर थंड आणि कोरड्या जागी ठेवा.",
    ],
}

SAFETY_PRECAUTIONS: Dict[str, Dict[LanguageCode, str]] = {
    "water": {
        "en": "Take with a full glass of water.",
        "hi": "एक पूरे गिलास पानी के साथ लें।",
        "mr": "पूर्ण ग्लास पाण्यासोबत घ्या.",
    },
    "complete_course": {
        "en": "Complete the full prescribed course as advised.",
        "hi": "सलाह के अनुसार पूरा निर्धारित कोर्स पूरा करें।",
        "mr": "सल्ल्यानुसार औषधांचा पूर्ण ठरवून दिलेला कोर्स पूर्ण करा.",
    },
    "with_food": {
        "en": "Take with or after food to prevent stomach upset.",
        "hi": "पेट की परेशानी से बचने के लिए भोजन के साथ या बाद में लें।",
        "mr": "पोटाचा त्रास टाळण्यासाठी जेवणासोबत किंवा जेवणानंतर घ्या.",
    },
    "consult_clinician": {
        "en": "Consult your physician or pharmacist if any unexpected symptoms occur.",
        "hi": "यदि कोई अप्रत्याशित लक्षण दिखाई दे तो अपने डॉक्टर या फार्मासिस्ट से परामर्श लें।",
        "mr": "काही अनपेक्षित लक्षणे आढळल्यास आपल्या डॉक्टर किंवा फार्मासिस्टचा सल्ला घ्या.",
    },
}


def get_concept(concept_key: str, lang: LanguageCode) -> str:
    return CORE_CONCEPTS.get(concept_key, {}).get(lang, "")


def get_frequency_label(
    frequency_key: Optional[str],
    lang: LanguageCode,
    raw_fallback: Optional[str] = None,
) -> str:
    if not frequency_key:
        return raw_fallback or ""
    return FREQUENCY_TERMS.get(frequency_key, {}).get(lang, raw_fallback or "")


def get_meal_relation_label(meal_key: Optional[str], lang: LanguageCode) -> str:
    if not meal_key:
        return ""
    return MEAL_RELATIONS.get(meal_key, {}).get(lang, "")


def get_precautions(lang: LanguageCode) -> List[str]:
    return STANDARD_PRECAUTIONS.get(lang, STANDARD_PRECAUTIONS["en"])


def normalize_frequency_to_key(frequency_raw: Optional[str]) -> str:
    """
    Deterministically normalizes raw handwritten frequency strings or abbreviations
    (e.g., '1-0-1', 'BD', 'BID', '1-1-1', 'TDS', 'OD', 'SOS') to standardized canonical keys.
    """
    if not frequency_raw:
        return "once_daily"
    clean = frequency_raw.upper().strip()

    if clean in ("1-0-1", "BD", "B.D.", "BID", "B.I.D.", "TWICE A DAY", "TWICE DAILY"):
        return "twice_daily"
    elif clean in ("1-1-1", "TDS", "T.D.S.", "TID", "T.I.D.", "THREE TIMES DAILY", "THREE TIMES A DAY"):
        return "three_times_daily"
    elif clean in ("1-1-1-1", "QID", "Q.I.D.", "FOUR TIMES DAILY"):
        return "four_times_daily"
    elif clean in ("1-0-0", "OD", "O.D.", "QD", "Q.D.", "ONCE DAILY", "ONCE A DAY"):
        return "once_daily"
    elif clean in ("0-0-1", "HS", "H.S.", "AT BEDTIME", "NIGHT"):
        return "at_bedtime"
    elif clean in ("SOS", "S.O.S.", "PRN", "P.R.N.", "AS NEEDED", "AS REQUIRED"):
        return "as_needed"
    else:
        # Fallback based on dash notation patterns
        parts = clean.split("-")
        if len(parts) >= 3:
            try:
                nums = [int(p) for p in parts if p.isdigit()]
                total = sum(nums)
                if total == 1:
                    return "once_daily" if nums[0] == 1 else "at_bedtime"
                elif total == 2:
                    return "twice_daily"
                elif total == 3:
                    return "three_times_daily"
                elif total >= 4:
                    return "four_times_daily"
            except Exception:
                pass
        return "once_daily"


def normalize_meal_relation_to_key(
    frequency_raw: Optional[str] = None,
    abbreviations: Optional[List[str]] = None,
) -> str:
    """
    Deterministically extracts meal relation from clinical abbreviations (e.g. PC, AC)
    or frequency strings.
    """
    raw_text = " ".join([a.upper().strip() for a in (abbreviations or [])])
    if frequency_raw:
        raw_text += " " + frequency_raw.upper().replace(".", " ")

    if any(k in raw_text for k in ("EMPTY STOMACH", "FASTING")):
        return "empty_stomach"
    elif any(k in raw_text for k in ("BEFORE MEALS", "BEFORE FOOD", "ANTE CIBUM", " AC ")):
        return "before_meals"
    elif any(k in raw_text for k in ("WITH FOOD", "WITH MEALS")):
        return "with_meals"
    elif any(k in raw_text for k in ("AFTER MEALS", "AFTER FOOD", "POST CIBUM", " PC ")):
        return "after_meals"

    # Also check exact abbreviation matches
    tokens = raw_text.split()
    if "AC" in tokens:
        return "before_meals"
    if "PC" in tokens:
        return "after_meals"

    return "after_meals"  # Conservative default for outpatient solid oral posology


def build_schedule_slots(
    frequency_key: Optional[str] = "once_daily",
    language: LanguageCode = "en",
    dosage_str: Optional[str] = None,
    meal_relation_key: Optional[str] = None,
    # Backward compatibility aliases
    lang: Optional[LanguageCode] = None,
    meal_key: Optional[str] = None,
) -> List[PosologyTimingSlot]:
    """
    Builds the structured daily timing slots (Morning, Afternoon, Evening, Night)
    corresponding to the normalized frequency key in the target vernacular.
    """
    target_lang: LanguageCode = lang or language
    effective_meal: str = meal_key or meal_relation_key or "after_meals"
    effective_freq: str = frequency_key or "once_daily"

    food_note = MEAL_RELATIONS.get(effective_meal, MEAL_RELATIONS["after_meals"])[target_lang]
    dose_label = dosage_str.strip() if dosage_str and dosage_str.strip() else CORE_CONCEPTS["prescribed_dose"][target_lang]

    slots: List[PosologyTimingSlot] = []

    if frequency_key == "once_daily":
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["morning"][target_lang],
            icon_key="sun",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
    elif frequency_key == "twice_daily":
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["morning"][target_lang],
            icon_key="sun",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["night"][target_lang],
            icon_key="moon",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
    elif frequency_key == "three_times_daily":
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["morning"][target_lang],
            icon_key="sun",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["afternoon"][target_lang],
            icon_key="cloud-sun",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["night"][target_lang],
            icon_key="moon",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
    elif frequency_key == "four_times_daily":
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["morning"][target_lang],
            icon_key="sun",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["afternoon"][target_lang],
            icon_key="cloud-sun",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["evening"][target_lang],
            icon_key="sunset",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["night"][target_lang],
            icon_key="moon",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
    elif frequency_key == "at_bedtime":
        slots.append(PosologyTimingSlot(
            time_slot=PERIOD_LABELS["night"][target_lang],
            icon_key="moon",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))
    elif frequency_key == "as_needed":
        slots.append(PosologyTimingSlot(
            time_slot=FREQUENCY_TERMS["as_needed"][target_lang],
            icon_key="sun",
            dosage_label=dose_label,
            food_instruction=food_note,
        ))

    return slots
