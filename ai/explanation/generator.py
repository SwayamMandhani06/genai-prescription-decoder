"""
Phase 11: Controlled Multilingual Explanation Generator.
Orchestrates:
1. Eligibility evaluation via ExplanationEligibilityGate
2. Deterministic posology rendering in English, Hindi, and Marathi
3. Real-time post-generation safety & fidelity validation
4. Packaging into canonical ExplanationResult and MultilingualPrescriptionExplanation models
"""

from typing import Any, Dict, List, Optional
from ai.explanation.config import (
    CONFIG_HASH,
    POLICY_VERSION,
    SUPPORTED_LANGUAGES,
    TEMPLATE_VERSION,
)
from ai.explanation.eligibility import ExplanationEligibilityGate, EligibilityEvaluation
from ai.explanation.schemas import (
    ExplanationEligibilityStatus,
    ExplanationResult,
    ExplanationValidationResult,
    LanguageCode,
    MultilingualPrescriptionExplanation,
    PosologyTimingSlot,
)
from ai.explanation.templates import PosologyTemplateEngine
from ai.explanation.terminology import (
    build_schedule_slots,
    normalize_frequency_to_key,
    normalize_meal_relation_to_key,
)
from ai.explanation.validators import ExplanationFidelityValidator


class PosologyExplanationGenerator:
    """
    Controlled posology generator that converts verified prescription facts into
    patient-friendly explanations without independent medical interpretation.
    """

    @classmethod
    def generate_explanation(
        cls,
        prescription_id: str,
        medicine_name: Optional[str],
        dosage: Optional[str] = None,
        frequency: Optional[str] = None,
        duration: Optional[str] = None,
        candidate_status: Optional[str] = "confident",
        validation_status: Optional[str] = "validated",
        abstention_decision: Optional[str] = "accepted",
        requires_human_verification: bool = False,
        has_lasa_conflict: bool = False,
        confusable_counterpart: Optional[str] = None,
        human_verification_status: Optional[str] = None,
        human_verified_value: Optional[str] = None,
        is_service_healthy: bool = True,
    ) -> MultilingualPrescriptionExplanation:
        """
        Generates validated posology explanations in English, Hindi, and Marathi.
        """
        # 1. Evaluate eligibility gate
        eligibility: EligibilityEvaluation = ExplanationEligibilityGate.evaluate(
            candidate_name=medicine_name,
            candidate_status=candidate_status,
            validation_status=validation_status,
            abstention_decision=abstention_decision,
            requires_human_verification=requires_human_verification,
            has_lasa_conflict=has_lasa_conflict,
            confusable_counterpart=confusable_counterpart,
            human_verification_status=human_verification_status,
            human_verified_value=human_verified_value,
            is_service_healthy=is_service_healthy,
        )

        effective_name = eligibility.effective_medicine_name
        status = eligibility.status

        # 2. Canonical fact normalization
        frequency_key = normalize_frequency_to_key(frequency)
        meal_relation_key = normalize_meal_relation_to_key(frequency)

        canonical_facts: Dict[str, Any] = {
            "effective_medicine_name": effective_name,
            "original_ai_name": eligibility.original_ai_name,
            "is_human_corrected": eligibility.is_human_corrected,
            "dosage": dosage.strip() if dosage else None,
            "frequency_raw": frequency.strip() if frequency else None,
            "frequency_key": frequency_key,
            "duration": duration.strip() if duration else None,
            "meal_relation_key": meal_relation_key,
            "eligibility_reason": eligibility.reason,
        }

        source_fields = ["medicine_name"]
        if dosage:
            source_fields.append("dosage")
        if frequency:
            source_fields.append("frequency")
        if duration:
            source_fields.append("duration")

        # 3. Generate and validate per supported language
        explanations: Dict[LanguageCode, ExplanationResult] = {}

        for lang in SUPPORTED_LANGUAGES:
            # Render summary
            summary = PosologyTemplateEngine.render_summary(
                language=lang,
                status=status,
                medicine_name=effective_name,
                dosage=canonical_facts["dosage"],
                frequency_key=frequency_key,
                raw_frequency=frequency,
                duration=canonical_facts["duration"],
                meal_relation_key=meal_relation_key,
                reason_code=eligibility.reason,
            )

            # Render instructions
            instructions = PosologyTemplateEngine.render_patient_instructions(
                language=lang,
                status=status,
                medicine_name=effective_name,
                dosage=canonical_facts["dosage"],
                frequency_key=frequency_key,
                duration=canonical_facts["duration"],
                meal_relation_key=meal_relation_key,
                reason_code=eligibility.reason,
            )

            # Render daily schedule slots
            if status == "eligible":
                daily_schedule = build_schedule_slots(
                    frequency_key=frequency_key,
                    language=lang,
                    dosage_str=canonical_facts["dosage"],
                    meal_relation_key=meal_relation_key,
                )
            else:
                daily_schedule = []

            # Render precautions
            precautions = PosologyTemplateEngine.render_precautions(
                language=lang,
                status=status,
                meal_relation_key=meal_relation_key,
                duration=canonical_facts["duration"],
            )

            # Post-generation fidelity & safety validation
            combined_text = f"{summary} {instructions}"
            validation = ExplanationFidelityValidator.validate_explanation(
                language=lang,
                status=status,
                effective_medicine_name=effective_name,
                source_facts={
                    "dosage": canonical_facts["dosage"],
                    "duration": canonical_facts["duration"],
                },
                generated_text=combined_text,
                reason_code=eligibility.reason,
            )

            # If validation failed, clamp status to unavailable to protect patient safety
            lang_status = status
            if not validation.is_valid and status == "eligible":
                lang_status = "unavailable"
                summary = PosologyTemplateEngine.render_summary(
                    language=lang,
                    status="unavailable",
                    medicine_name="",
                )
                instructions = PosologyTemplateEngine.render_patient_instructions(
                    language=lang,
                    status="unavailable",
                    medicine_name="",
                )
                daily_schedule = []
                precautions = PosologyTemplateEngine.render_precautions(
                    language=lang,
                    status="unavailable",
                )

            explanations[lang] = ExplanationResult(
                status=lang_status,
                language=lang,
                summary=summary,
                instructions=instructions,
                daily_schedule=daily_schedule,
                precautions=precautions,
                source_fields=source_fields,
                facts_used=canonical_facts,
                validation=validation,
                source_version=POLICY_VERSION,
                template_version=TEMPLATE_VERSION,
            )

        # Composite overall eligibility
        overall_eligibility: ExplanationEligibilityStatus = status
        # If any language failed validation, overall status becomes unavailable
        if any(exp.status == "unavailable" for exp in explanations.values()):
            overall_eligibility = "unavailable"

        return MultilingualPrescriptionExplanation(
            prescription_id=prescription_id,
            overall_eligibility=overall_eligibility,
            explanations=explanations,
            policy_version=POLICY_VERSION,
            template_version=TEMPLATE_VERSION,
            config_hash=CONFIG_HASH,
        )
