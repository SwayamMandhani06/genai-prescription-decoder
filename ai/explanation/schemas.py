"""
Phase 11: Multilingual Patient-Friendly Explanation Schemas.
Defines structured data contracts for:
- Explanation eligibility states (eligible, restricted, abstained, unavailable)
- Posology timing slots and language packs (English, Hindi, Marathi)
- Fact preservation tracking and fidelity validation records
- Complete prescription explanation responses
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, model_validator

# ------------------------------------------------------------------------------
# Core Types & Enums
# ------------------------------------------------------------------------------

ExplanationEligibilityStatus = Literal[
    "eligible",       # Source information is sufficiently reliable for full controlled patient posology
    "restricted",     # Information described with explicit uncertainty/LASA warnings preserved
    "abstained",      # Autonomous explanation blocked due to Phase 9 abstention or unreadable field
    "unavailable",    # Explanation service could not execute or completed abnormally
]

LanguageCode = Literal["en", "hi", "mr"]


class PosologyTimingSlot(BaseModel):
    """
    Individual daily dosage schedule slot.
    Maps clinical abbreviations (e.g. 1-0-1, BD, PC) to patient-friendly visual periods.
    """
    time_slot: str = Field(..., description="Vernacular period label (e.g. Morning / सुबह / सकाळी)")
    icon_key: str = Field(..., description="Icon key: 'sun', 'cloud-sun', 'sunset', 'moon'")
    dosage_label: str = Field(..., description="Preserved dosage strength or count (e.g. 500 mg, 1 Tablet)")
    food_instruction: str = Field(..., description="Meal-relative timing (e.g. After meals / भोजन के बाद / जेवणानंतर)")


class ExplanationValidationResult(BaseModel):
    """
    Automated safety and fidelity validation results.
    Guarantees strict factual alignment before presenting explanations to patients.
    """
    medicine_fidelity: bool = Field(..., description="True if medicine name matches approved source entity verbatim")
    numeric_fidelity: bool = Field(..., description="True if all numeric dosages, frequencies, and durations match exactly")
    unsupported_fact_check: bool = Field(..., description="True if explanation contains zero ungrounded clinical claims")
    details: Optional[List[str]] = Field(default_factory=list, description="Validation notices or rejection reasons")

    @property
    def is_valid(self) -> bool:
        return self.medicine_fidelity and self.numeric_fidelity and self.unsupported_fact_check


class LanguageExplanationPack(BaseModel):
    """
    Patient-friendly explanation content in a single target vernacular.
    Conforms to Phase 1 frontend envelope while preserving factual provenance.
    """
    summary: str = Field(..., description="One-sentence patient-friendly posology summary")
    patient_instructions: str = Field(..., description="Detailed intake instruction and verification guidance")
    daily_schedule: List[PosologyTimingSlot] = Field(default_factory=list, description="Structured daily timing slots")
    precautions: List[str] = Field(default_factory=list, description="Controlled safety reminders and disclaimers")


class ExplanationResult(BaseModel):
    """
    Full explanation result for a single language with audit provenance and validation.
    """
    status: ExplanationEligibilityStatus = Field(..., description="Eligibility determination for this explanation")
    language: LanguageCode = Field(..., description="Target language code: 'en', 'hi', or 'mr'")
    summary: str = Field(..., description="Posology overview summary string")
    instructions: str = Field(..., description="Patient intake instructions")
    daily_schedule: List[PosologyTimingSlot] = Field(default_factory=list, description="Daily schedule slots")
    precautions: List[str] = Field(default_factory=list, description="Standard safety precautions")
    source_fields: List[str] = Field(default_factory=list, description="List of source clinical field keys utilized")
    facts_used: Dict[str, Any] = Field(default_factory=dict, description="Normalized canonical facts consumed")
    validation: ExplanationValidationResult = Field(..., description="Fidelity validation report")
    source_version: str = Field("explanation_policy_v1", description="Policy version used for eligibility")
    template_version: str = Field("explanation_template_v1", description="Template collection version")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC generation timestamp",
    )


class MultilingualPrescriptionExplanation(BaseModel):
    """
    Top-level Phase 11 Multilingual Explanation Output for an entire prescription.
    Provides verified patient posology in English, Hindi, and Marathi with zero independent interpretation.
    """
    prescription_id: str = Field(..., description="Prescription identifier")
    overall_eligibility: ExplanationEligibilityStatus = Field(..., description="Composite eligibility state across prescription")
    explanations: Dict[LanguageCode, ExplanationResult] = Field(..., description="Explanation results keyed by language")
    policy_version: str = Field("explanation_policy_v1", description="Phase 11 explanation policy version")
    template_version: str = Field("explanation_template_v1", description="Phase 11 template collection version")
    config_hash: str = Field(..., description="SHA-256 fingerprint of active explanation configuration")
    error_message: Optional[str] = Field(None, description="Diagnostic error details if status is unavailable")

    @model_validator(mode="after")
    def validate_eligibility_consistency(self) -> "MultilingualPrescriptionExplanation":
        if self.overall_eligibility == "unavailable" and not self.error_message:
            self.error_message = "Multilingual explanation service could not complete"
        return self
