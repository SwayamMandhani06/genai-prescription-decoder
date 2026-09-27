"""
Phase 9: Uncertainty-Aware Abstention and Human Verification Layer.
Adheres strictly to PLAN.md Section 18:
- Decides: Accept vs Abstain -> Require Human Verification
- Safety-critical dosage preservation and immutability
- Explicit machine-readable reason code taxonomy
- Human verification workflow (confirm, correct, mark_unreadable)
- Immutable audit trail preserving original model extraction
"""

from ai.abstention.reasons import AbstentionReasonCode, get_reason_description
from ai.abstention.config import AbstentionPolicyConfig, get_default_abstention_config
from ai.abstention.schemas import (
    FieldAbstentionDecision,
    MedicineAbstentionDecision,
    PrescriptionAbstentionDecision,
    HumanVerificationRecord,
    HumanVerificationActionRequest,
    PrescriptionVerificationState,
)
from ai.abstention.policy import (
    evaluate_field_abstention,
    evaluate_medicine_abstention,
    evaluate_prescription_abstention,
)
from ai.abstention.service import AbstentionService, get_abstention_service

__all__ = [
    "AbstentionReasonCode",
    "get_reason_description",
    "AbstentionPolicyConfig",
    "get_default_abstention_config",
    "FieldAbstentionDecision",
    "MedicineAbstentionDecision",
    "PrescriptionAbstentionDecision",
    "HumanVerificationRecord",
    "HumanVerificationActionRequest",
    "PrescriptionVerificationState",
    "evaluate_field_abstention",
    "evaluate_medicine_abstention",
    "evaluate_prescription_abstention",
    "AbstentionService",
    "get_abstention_service",
]
