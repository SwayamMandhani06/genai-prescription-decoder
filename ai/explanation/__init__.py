"""
Phase 11: Multilingual Patient-Friendly Explanation Layer.
Provides deterministic, verified, patient-friendly explanations in English, Hindi, and Marathi
strictly preserving medicine names and numerical quantities without clinical hallucinations.
"""

from ai.explanation.config import (
    CONFIG_HASH,
    POLICY_VERSION,
    SUPPORTED_LANGUAGES,
    TEMPLATE_VERSION,
    TERMINOLOGY_VERSION,
)
from ai.explanation.eligibility import (
    EligibilityEvaluation,
    ExplanationEligibilityGate,
)
from ai.explanation.generator import PosologyExplanationGenerator
from ai.explanation.schemas import (
    ExplanationEligibilityStatus,
    ExplanationResult,
    ExplanationValidationResult,
    LanguageCode,
    LanguageExplanationPack,
    MultilingualPrescriptionExplanation,
    PosologyTimingSlot,
)
from ai.explanation.service import (
    ExplanationService,
    get_explanation_service,
)
from ai.explanation.templates import (
    PosologyTemplateEngine,
    STATUS_MESSAGES,
)
from ai.explanation.terminology import (
    CORE_CONCEPTS,
    FREQUENCY_TERMS,
    MEAL_RELATIONS,
    SAFETY_PRECAUTIONS,
    build_schedule_slots,
    normalize_frequency_to_key,
    normalize_meal_relation_to_key,
)
from ai.explanation.validators import (
    ExplanationFidelityValidator,
    MedicineNameFidelityValidator,
    NumericFidelityValidator,
    UnsupportedFactValidator,
)

__all__ = [
    "CONFIG_HASH",
    "POLICY_VERSION",
    "SUPPORTED_LANGUAGES",
    "TEMPLATE_VERSION",
    "TERMINOLOGY_VERSION",
    "ExplanationEligibilityStatus",
    "LanguageCode",
    "PosologyTimingSlot",
    "ExplanationValidationResult",
    "LanguageExplanationPack",
    "ExplanationResult",
    "MultilingualPrescriptionExplanation",
    "EligibilityEvaluation",
    "ExplanationEligibilityGate",
    "CORE_CONCEPTS",
    "FREQUENCY_TERMS",
    "MEAL_RELATIONS",
    "SAFETY_PRECAUTIONS",
    "build_schedule_slots",
    "normalize_frequency_to_key",
    "normalize_meal_relation_to_key",
    "PosologyTemplateEngine",
    "STATUS_MESSAGES",
    "NumericFidelityValidator",
    "MedicineNameFidelityValidator",
    "UnsupportedFactValidator",
    "ExplanationFidelityValidator",
    "PosologyExplanationGenerator",
    "ExplanationService",
    "get_explanation_service",
]
