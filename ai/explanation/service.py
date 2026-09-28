"""
Phase 11: Multilingual Explanation Service.
Provides high-level orchestration for generating verified patient-friendly posology
explanations across English, Hindi, and Marathi from structured prescription pipeline outputs.
"""

from typing import Any, Dict, List, Optional, Tuple
from ai.explanation.generator import PosologyExplanationGenerator
from ai.explanation.schemas import (
    LanguageCode,
    MultilingualPrescriptionExplanation,
    ExplanationResult,
)



class ExplanationService:
    """
    Central service for Phase 11 patient explanation generation.
    Consumes upstream extraction, RAG validation, confidence assessment,
    LASA screening, and Phase 9 abstention decisions.
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
        Generates structured MultilingualPrescriptionExplanation with fidelity audits.
        """
        return PosologyExplanationGenerator.generate_explanation(
            prescription_id=prescription_id,
            medicine_name=medicine_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
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

    @classmethod
    def generate_prescription_bundle(
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
    ) -> Tuple[Any, Any, MultilingualPrescriptionExplanation]:
        """
        Synthesizes the complete triple needed by PrescriptionAnalyzeResponse:
        1. MultilingualSummary (Section 6 contract: en, hi, mr summary strings)
        2. MultilingualPosology (Phase 1 UI envelope: en, hi, mr rich posology packs with slots)
        3. MultilingualPrescriptionExplanation (Phase 11 audit model with fidelity validation)
        """
        from backend.app.schemas.prescription import (
            MultilingualPosology,
            MultilingualSummary,
            PosologyLanguagePack,
            PosologyTimingSlot as BackendPosologyTimingSlot,
        )

        explanation_obj = cls.generate_explanation(
            prescription_id=prescription_id,
            medicine_name=medicine_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
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

        en_exp = explanation_obj.explanations["en"]
        hi_exp = explanation_obj.explanations["hi"]
        mr_exp = explanation_obj.explanations["mr"]

        summary = MultilingualSummary(
            en=en_exp.summary,
            hi=hi_exp.summary,
            mr=mr_exp.summary,
        )

        def to_ui_slots(slots) -> List[Any]:
            return [
                BackendPosologyTimingSlot(
                    time_slot=s.time_slot,
                    icon_key=s.icon_key,
                    dosage_label=s.dosage_label,
                    food_instruction=s.food_instruction,
                )
                for s in slots
            ]

        posology = MultilingualPosology(
            en=PosologyLanguagePack(
                summary=en_exp.summary,
                patient_instructions=en_exp.instructions,
                daily_schedule=to_ui_slots(en_exp.daily_schedule),
                precautions=en_exp.precautions,
            ),
            hi=PosologyLanguagePack(
                summary=hi_exp.summary,
                patient_instructions=hi_exp.instructions,
                daily_schedule=to_ui_slots(hi_exp.daily_schedule),
                precautions=hi_exp.precautions,
            ),
            mr=PosologyLanguagePack(
                summary=mr_exp.summary,
                patient_instructions=mr_exp.instructions,
                daily_schedule=to_ui_slots(mr_exp.daily_schedule),
                precautions=mr_exp.precautions,
            ),
        )

        return summary, posology, explanation_obj


# Global singleton helper
_EXPLANATION_SERVICE_INSTANCE: Optional[ExplanationService] = None


def get_explanation_service() -> ExplanationService:
    global _EXPLANATION_SERVICE_INSTANCE
    if _EXPLANATION_SERVICE_INSTANCE is None:
        _EXPLANATION_SERVICE_INSTANCE = ExplanationService()
    return _EXPLANATION_SERVICE_INSTANCE
