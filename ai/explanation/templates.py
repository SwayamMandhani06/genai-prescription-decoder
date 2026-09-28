"""
Phase 11: Controlled Multilingual Explanation Templates.
Implements deterministic, verified posology sentence builders and instruction renderers
in English, Hindi, and Marathi. Enforces strict information fidelity and preserves
raw medicine names and numerical quantities without alteration.
"""

import re
from typing import Dict, List, Optional
from ai.explanation.schemas import ExplanationEligibilityStatus, LanguageCode
from ai.explanation.terminology import (
    CORE_CONCEPTS,
    FREQUENCY_TERMS,
    MEAL_RELATIONS,
    SAFETY_PRECAUTIONS,
    get_concept,
    get_frequency_label,
    get_meal_relation_label,
    get_precautions,
)

# ------------------------------------------------------------------------------
# Template Constants & Versions
# ------------------------------------------------------------------------------

TEMPLATE_VERSION = "explanation_template_v1"


def format_duration_for_lang(duration: Optional[str], language: LanguageCode) -> Optional[str]:
    """
    Translates duration units (days, weeks, months) to Hindi and Marathi
    while strictly preserving the exact numeric quantities.
    """
    if not duration:
        return None
    d = duration.strip()
    if language == "hi":
        d = re.sub(r"\b(\d+(?:\.\d+)?)\s*days?\b", r"\1 दिनों", d, flags=re.IGNORECASE)
        d = re.sub(r"\b(\d+(?:\.\d+)?)\s*weeks?\b", r"\1 सप्ताह", d, flags=re.IGNORECASE)
        d = re.sub(r"\b(\d+(?:\.\d+)?)\s*months?\b", r"\1 महीने", d, flags=re.IGNORECASE)
    elif language == "mr":
        d = re.sub(r"\b(\d+(?:\.\d+)?)\s*days?\b", r"\1 दिवस", d, flags=re.IGNORECASE)
        d = re.sub(r"\b(\d+(?:\.\d+)?)\s*weeks?\b", r"\1 आठवडे", d, flags=re.IGNORECASE)
        d = re.sub(r"\b(\d+(?:\.\d+)?)\s*months?\b", r"\1 महिने", d, flags=re.IGNORECASE)
    return d

# Standard abstention & safety disclaimers across languages
STATUS_MESSAGES: Dict[str, Dict[LanguageCode, str]] = {
    # Section 15: Uncertain information
    "uncertain_medicine": {
        "en": "The medicine name could not be read with sufficient confidence.",
        "hi": "दवा का नाम पर्याप्त विश्वास के साथ पढ़ा नहीं जा सका।",
        "mr": "औषधाचे नाव पुरेशा खात्रीने वाचता आले नाही.",
    },
    # Section 16: Missing information
    "missing_dosage": {
        "en": "The dosage is not clearly available in the prescription data.",
        "hi": "प्रिस्क्रिप्शन की उपलब्ध जानकारी में दवा की मात्रा स्पष्ट रूप से उपलब्ध नहीं है।",
        "mr": "प्रिस्क्रिप्शनच्या उपलब्ध माहितीमध्ये औषधाची मात्रा स्पष्टपणे उपलब्ध नाही.",
    },
    "missing_frequency": {
        "en": "The frequency is not clearly available in the prescription data.",
        "hi": "प्रिस्क्रिप्शन की उपलब्ध जानकारी में लेने की बारंबारता स्पष्ट रूप से उपलब्ध नहीं है।",
        "mr": "प्रिस्क्रिप्शनच्या उपलब्ध माहितीमध्ये घेण्याची वारंवारता स्पष्टपणे उपलब्ध नाही.",
    },
    "missing_duration": {
        "en": "The duration is not clearly available in the prescription data.",
        "hi": "प्रिस्क्रिप्शन की उपलब्ध जानकारी में दवा की अवधि स्पष्ट रूप से उपलब्ध नहीं है।",
        "mr": "प्रिस्क्रिप्शनच्या उपलब्ध माहितीमध्ये औषधाचा कालावधी स्पष्टपणे उपलब्ध नाही.",
    },
    "missing_medicine": {
        "en": "The medicine name is not observed in the prescription data.",
        "hi": "प्रिस्क्रिप्शन डेटा में दवा का नाम नहीं मिला है।",
        "mr": "प्रिस्क्रिप्शन डेटामध्ये औषधाचे नाव आढळले नाही.",
    },
    # Section 17: Phase 9 Abstention
    "phase9_abstained": {
        "en": "The medicine details require verification against the original prescription before a patient-friendly explanation can be provided.",
        "hi": "मरीज के अनुकूल विवरण देने से पहले मूल प्रिस्क्रिप्शन से दवा के विवरण की पुष्टि करना आवश्यक है।",
        "mr": "रुग्ण-अनुकूल स्पष्टीकरण देण्यापूर्वी मूळ प्रिस्क्रिप्शनशी औषधाच्या तपशीलाची पडताळणी करणे आवश्यक आहे.",
    },
    # Section 18: Phase 10 LASA Conflict
    "lasa_conflict": {
        "en": "Similar medicine names were detected. Please verify the medicine name against the original prescription.",
        "hi": "मिलते-जुलते दवा के नाम पाए गए हैं। कृपया मूल प्रिस्क्रिप्शन से दवा के नाम की पुष्टि करें।",
        "mr": "सारखी औषधांची नावे आढळली आहेत. कृपया मूळ प्रिस्क्रिप्शनशी तुलना करून औषधाच्या नावाची खात्री करा.",
    },
    # Section 20: Human-marked unreadable
    "marked_unreadable": {
        "en": "The medicine name could not be confirmed from the prescription.",
        "hi": "प्रिस्क्रिप्शन से दवा के नाम की पुष्टि नहीं हो सकी।",
        "mr": "प्रिस्क्रिप्शनमधून औषधाच्या नावाची पुष्टी करता आली नाही.",
    },
    # Section 38: Service unavailable
    "service_unavailable": {
        "en": "The patient-friendly explanation is currently unavailable for this prescription.",
        "hi": "इस प्रिस्क्रिप्शन के लिए मरीज-अनुकूल विवरण वर्तमान में उपलब्ध नहीं है।",
        "mr": "या प्रिस्क्रिप्शनसाठी रुग्ण-अनुकूल स्पष्टीकरण सध्या उपलब्ध नाही.",
    },
    # Verification instruction notices
    "verification_prompt": {
        "en": "Please review the original handwritten prescription image with your doctor or pharmacist.",
        "hi": "कृपया अपने डॉक्टर या फार्मासिस्ट के साथ मूल हस्तलिखित प्रिस्क्रिप्शन छवि की समीक्षा करें।",
        "mr": "कृपया तुमच्या डॉक्टरांशी किंवा फार्मासिस्टशी मूळ हस्तलिखित प्रिस्क्रिप्शन प्रतिमेची पडताळणी करा.",
    },
}


class PosologyTemplateEngine:
    """
    Renders deterministic patient-friendly explanations in English, Hindi, and Marathi.
    Ensures medicine names remain in canonical Roman script and numbers are unmutated.
    """

    @classmethod
    def render_summary(
        cls,
        language: LanguageCode,
        status: ExplanationEligibilityStatus,
        medicine_name: str,
        dosage: Optional[str] = None,
        frequency_key: Optional[str] = None,
        raw_frequency: Optional[str] = None,
        duration: Optional[str] = None,
        meal_relation_key: Optional[str] = None,
        reason_code: Optional[str] = None,
    ) -> str:
        """
        Builds the single-sentence posology summary for the target language.
        """
        # Handle non-eligible states first
        if status == "unavailable":
            return STATUS_MESSAGES["service_unavailable"][language]

        if status == "abstained":
            if reason_code == "HUMAN_MARKED_UNREADABLE":
                return STATUS_MESSAGES["marked_unreadable"][language]
            if reason_code == "MEDICINE_NAME_MISSING" or not medicine_name:
                return STATUS_MESSAGES["missing_medicine"][language]
            return STATUS_MESSAGES["phase9_abstained"][language]

        if status == "restricted":
            if reason_code == "LASA_SIMILARITY_CONFLICT":
                return STATUS_MESSAGES["lasa_conflict"][language]
            if reason_code == "EXTRACTION_OR_VALIDATION_UNCERTAIN":
                return STATUS_MESSAGES["uncertain_medicine"][language]
            return STATUS_MESSAGES["phase9_abstained"][language]

        # Fully ELIGIBLE state: synthesize controlled sentence
        return cls._render_eligible_summary(
            language=language,
            medicine_name=medicine_name,
            dosage=dosage,
            frequency_key=frequency_key,
            raw_frequency=raw_frequency,
            duration=duration,
            meal_relation_key=meal_relation_key,
        )

    @classmethod
    def _render_eligible_summary(
        cls,
        language: LanguageCode,
        medicine_name: str,
        dosage: Optional[str],
        frequency_key: Optional[str],
        raw_frequency: Optional[str],
        duration: Optional[str],
        meal_relation_key: Optional[str],
    ) -> str:
        """
        Synthesizes standard posology summary matching Section 12, 13, and 14 examples.
        Preserves medicine name and numbers verbatim.
        """
        freq_label = get_frequency_label(frequency_key, language, raw_fallback=raw_frequency)
        meal_label = get_meal_relation_label(meal_relation_key, language)

        # 1. English
        if language == "en":
            parts = [f"{medicine_name} is listed"]
            if dosage:
                parts.append(f"with a dose of {dosage}")
            if freq_label:
                parts.append(f"to be taken {freq_label}")
            if meal_label:
                parts.append(f"{meal_label}")
            if duration:
                parts.append(f"for {duration}")
            parts.append("as written on the prescription.")
            return ", ".join(parts).replace("is listed, with", "is listed with").replace("prescription.,", "prescription.")

        # 2. Hindi: "प्रिस्क्रिप्शन में {medicine_name} की मात्रा {dosage} लिखी है। इसे {freq}, {duration} तक लेने के लिए लिखा गया है।"
        elif language == "hi":
            dur_hi = format_duration_for_lang(duration, "hi")
            if dosage and freq_label and dur_hi:
                summary = f"प्रिस्क्रिप्शन में {medicine_name} की मात्रा {dosage} लिखी है। इसे {freq_label}"
                if meal_label:
                    summary += f" ({meal_label})"
                summary += f", {dur_hi} तक लेने के लिए लिखा गया है।"
                return summary
            elif dosage and freq_label:
                summary = f"प्रिस्क्रिप्शन में {medicine_name} की मात्रा {dosage} लिखी है। इसे {freq_label}"
                if meal_label:
                    summary += f" ({meal_label})"
                summary += " लेने के लिए लिखा गया है।"
                return summary
            elif dosage:
                return f"प्रिस्क्रिप्शन में {medicine_name} की मात्रा {dosage} लिखी है, जैसा कि प्रिस्क्रिप्शन में लिखा है।"
            else:
                return f"प्रिस्क्रिप्शन में {medicine_name} लिखा है, जैसा कि प्रिस्क्रिप्शन में लिखा है।"

        # 3. Marathi: "प्रिस्क्रिप्शनमध्ये {medicine_name} ची मात्रा {dosage} लिहिलेली आहे. हे {freq}, {duration} घेण्यासाठी लिहिले आहे."
        elif language == "mr":
            dur_mr = format_duration_for_lang(duration, "mr")
            if dosage and freq_label and dur_mr:
                summary = f"प्रिस्क्रिप्शनमध्ये {medicine_name} ची मात्रा {dosage} लिहिलेली आहे. हे {freq_label}"
                if meal_label:
                    summary += f" ({meal_label})"
                summary += f", {dur_mr} घेण्यासाठी लिहिले आहे."
                return summary
            elif dosage and freq_label:
                summary = f"प्रिस्क्रिप्शनमध्ये {medicine_name} ची मात्रा {dosage} लिहिलेली आहे. हे {freq_label}"
                if meal_label:
                    summary += f" ({meal_label})"
                summary += " घेण्यासाठी लिहिले आहे."
                return summary
            elif dosage:
                return f"प्रिस्क्रिप्शनमध्ये {medicine_name} ची मात्रा {dosage} लिहिलेली आहे, जसे प्रिस्क्रिप्शनमध्ये लिहिले आहे."
            else:
                return f"प्रिस्क्रिप्शनमध्ये {medicine_name} लिहिलेले आहे, जसे प्रिस्क्रिप्शनमध्ये लिहिले आहे."

        return f"{medicine_name} as written on the prescription."

    @classmethod
    def render_patient_instructions(
        cls,
        language: LanguageCode,
        status: ExplanationEligibilityStatus,
        medicine_name: str,
        dosage: Optional[str] = None,
        frequency_key: Optional[str] = None,
        duration: Optional[str] = None,
        meal_relation_key: Optional[str] = None,
        reason_code: Optional[str] = None,
    ) -> str:
        """
        Renders detailed intake steps or verification directions.
        """
        if status in ("abstained", "restricted", "unavailable"):
            verification_prompt = STATUS_MESSAGES["verification_prompt"][language]
            status_msg = STATUS_MESSAGES.get(
                "lasa_conflict" if reason_code == "LASA_SIMILARITY_CONFLICT"
                else "marked_unreadable" if reason_code == "HUMAN_MARKED_UNREADABLE"
                else "uncertain_medicine" if reason_code == "EXTRACTION_OR_VALIDATION_UNCERTAIN"
                else "service_unavailable" if status == "unavailable"
                else "phase9_abstained",
                STATUS_MESSAGES["phase9_abstained"]
            )[language]
            return f"{status_msg} {verification_prompt}"

        # Fully eligible instruction narrative
        freq_label = get_frequency_label(frequency_key, language)
        meal_label = get_meal_relation_label(meal_relation_key, language)

        if language == "en":
            lines = [f"Take {medicine_name} exactly as prescribed:"]
            if dosage:
                lines.append(f"• Dose: {dosage}")
            if freq_label:
                lines.append(f"• Frequency: {freq_label}")
            if meal_label:
                lines.append(f"• Timing: {meal_label}")
            if duration:
                lines.append(f"• Duration: {duration}")
            lines.append("• Do not alter dosage or discontinue without consulting your physician.")
            return "\n".join(lines)

        elif language == "hi":
            dur_hi = format_duration_for_lang(duration, "hi")
            lines = [f"{medicine_name} को निर्देशानुसार लें:"]
            if dosage:
                lines.append(f"• खुराक: {dosage}")
            if freq_label:
                lines.append(f"• बारंबारता: {freq_label}")
            if meal_label:
                lines.append(f"• समय: {meal_label}")
            if dur_hi:
                lines.append(f"• अवधि: {dur_hi}")
            lines.append("• डॉक्टर की सलाह के बिना खुराक में बदलाव न करें और न ही दवा बंद करें।")
            return "\n".join(lines)

        elif language == "mr":
            dur_mr = format_duration_for_lang(duration, "mr")
            lines = [f"{medicine_name} दिलेल्या निर्देशानुसार घ्या:"]
            if dosage:
                lines.append(f"• मात्रा: {dosage}")
            if freq_label:
                lines.append(f"• वारंवारता: {freq_label}")
            if meal_label:
                lines.append(f"• वेळ: {meal_label}")
            if dur_mr:
                lines.append(f"• कालावधी: {dur_mr}")
            lines.append("• डॉक्टरांच्या सल्ल्याशिवाय मात्रा बदलू नका किंवा औषध बंद करू नका.")
            return "\n".join(lines)

        return f"Take {medicine_name} as prescribed."

    @classmethod
    def render_precautions(
        cls,
        language: LanguageCode,
        status: ExplanationEligibilityStatus,
        meal_relation_key: Optional[str] = None,
        duration: Optional[str] = None,
    ) -> List[str]:
        """
        Returns vetted, language-specific precautions.
        """
        precautions = []
        if status in ("restricted", "abstained", "unavailable"):
            precautions.append(get_concept("verification_notice", language))
            return precautions

        # Standard precautions for eligible entities
        precautions.append(SAFETY_PRECAUTIONS["water"][language])
        if duration:
            precautions.append(SAFETY_PRECAUTIONS["complete_course"][language])
        if meal_relation_key == "after_meals":
            precautions.append(SAFETY_PRECAUTIONS["with_food"][language])
        precautions.append(SAFETY_PRECAUTIONS["consult_clinician"][language])
        return precautions
