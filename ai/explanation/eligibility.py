"""
Phase 11: Explanation Eligibility Gate.
Evaluates upstream multimodal extraction, RAG validation, calibrated confidence,
LASA conflict detection, and Phase 9 human verification states to determine
whether a prescription entity is eligible for patient-friendly explanation.
"""

from typing import Optional
from pydantic import BaseModel, Field

from ai.explanation.schemas import ExplanationEligibilityStatus


class EligibilityEvaluation(BaseModel):
    """
    Detailed eligibility determination result for a medication candidate.
    """
    status: ExplanationEligibilityStatus = Field(..., description="Determined eligibility status")
    effective_medicine_name: str = Field(..., description="Medicine name to use (verified value if corrected)")
    original_ai_name: str = Field(..., description="Original raw AI extraction before human verification")
    is_human_corrected: bool = Field(False, description="True if value was corrected by human clinician")
    is_human_confirmed: bool = Field(False, description="True if verbatim AI extraction was confirmed by human")
    is_unreadable: bool = Field(False, description="True if marked unreadable during human verification")
    has_lasa_conflict: bool = Field(False, description="True if an active LASA similarity conflict exists")
    confusable_name: Optional[str] = Field(None, description="Name of conflicting drug counterpart if LASA detected")
    reason: str = Field(..., description="Machine-readable eligibility justification code")
    guidance: str = Field(..., description="Explanation generation constraint instruction")


class ExplanationEligibilityGate:
    """
    Evaluates clinical evidence and enforces strict safety gating before explanation generation.
    Never allows unverified, abstained, or fabricated interpretations to become patient instructions.
    """

    @staticmethod
    def evaluate(
        candidate_name: Optional[str],
        candidate_status: Optional[str] = "confident",
        validation_status: Optional[str] = "validated",
        abstention_decision: Optional[str] = "accepted",
        requires_human_verification: bool = False,
        has_lasa_conflict: bool = False,
        confusable_counterpart: Optional[str] = None,
        human_verification_status: Optional[str] = None,
        human_verified_value: Optional[str] = None,
        is_service_healthy: bool = True,
    ) -> EligibilityEvaluation:
        """
        Pure deterministic evaluation of eligibility state across clinical pipeline dimensions.
        """
        # 1. Service failure / abnormal execution state
        if not is_service_healthy:
            return EligibilityEvaluation(
                status="unavailable",
                effective_medicine_name=candidate_name or "Unknown Medicine",
                original_ai_name=candidate_name or "Unknown Medicine",
                reason="EXPLANATION_SERVICE_UNAVAILABLE",
                guidance="Explanation engine unavailable; suppress autonomous guidance.",
            )

        # 2. Missing raw candidate
        raw_name = (candidate_name or "").strip()
        if not raw_name or raw_name.lower() in ("not observed", "unknown medicine", "missing", "null", "none"):
            return EligibilityEvaluation(
                status="abstained",
                effective_medicine_name="",
                original_ai_name="",
                reason="MEDICINE_NAME_MISSING",
                guidance="Medicine name not observed on prescription; do not invent instructions.",
            )

        # 3. Human verification states (Phase 9 audit trail takes precedence)
        if human_verification_status == "unreadable":
            return EligibilityEvaluation(
                status="abstained",
                effective_medicine_name=raw_name,
                original_ai_name=raw_name,
                is_unreadable=True,
                reason="HUMAN_MARKED_UNREADABLE",
                guidance="Field marked unreadable by human verifier; suppress medication explanation.",
            )
        elif human_verification_status == "corrected" and human_verified_value:
            # Human verified correction: eligible to explain using corrected entity, while auditing original
            return EligibilityEvaluation(
                status="eligible",
                effective_medicine_name=human_verified_value.strip(),
                original_ai_name=raw_name,
                is_human_corrected=True,
                reason="HUMAN_VERIFIED_CORRECTION",
                guidance="Use human-verified entity; preserve original extraction in audit facts.",
            )
        elif human_verification_status == "confirmed":
            return EligibilityEvaluation(
                status="eligible",
                effective_medicine_name=raw_name,
                original_ai_name=raw_name,
                is_human_confirmed=True,
                reason="HUMAN_VERIFIED_CONFIRMED",
                guidance="Use confirmed extraction; full explanation eligible.",
            )

        # 4. Phase 10 LASA Similarity Conflict (Restricted Safety Review)
        if has_lasa_conflict:
            return EligibilityEvaluation(
                status="restricted",
                effective_medicine_name=raw_name,
                original_ai_name=raw_name,
                has_lasa_conflict=True,
                confusable_name=confusable_counterpart,
                reason="LASA_SIMILARITY_CONFLICT",
                guidance="Flag similarity ambiguity; do not present candidate as definitive therapy.",
            )

        # 5. Phase 9 Autonomous Abstention Gate
        if abstention_decision == "abstained" or (requires_human_verification and candidate_status in ("abstained", "flagged")):
            return EligibilityEvaluation(
                status="abstained",
                effective_medicine_name=raw_name,
                original_ai_name=raw_name,
                reason="PHASE9_CLINICAL_ABSTENTION",
                guidance="Autonomous output abstained by Phase 9; explain verification requirement only.",
            )

        # 6. Extraction or RAG Uncertainty (Restricted Explanation)
        if candidate_status == "uncertain" or validation_status in ("uncertain", "not_validated") or requires_human_verification:
            return EligibilityEvaluation(
                status="restricted",
                effective_medicine_name=raw_name,
                original_ai_name=raw_name,
                reason="EXTRACTION_OR_VALIDATION_UNCERTAIN",
                guidance="Explain visible facts with explicit notice of required clinical verification.",
            )

        # 7. Confident, validated, non-confusable extraction -> Fully eligible
        return EligibilityEvaluation(
            status="eligible",
            effective_medicine_name=raw_name,
            original_ai_name=raw_name,
            reason="CONFIDENT_VALIDATED_ELIGIBLE",
            guidance="Full controlled patient posology explanation eligible for generation.",
        )
