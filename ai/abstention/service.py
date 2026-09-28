"""
Phase 9: Abstention and Human Verification Service.
Provides singleton dependency injection for:
- Evaluating abstention decisions over multimodal extraction and confidence signals
- Managing human verification actions (confirm, correct, mark_unreadable)
- Maintaining immutable audit trails for clinical governance
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import threading

from backend.app.multimodal.schemas import PrescriptionExtractionResult
from ai.rag.schemas import MedicineValidationResult
from ai.confidence.schemas import PrescriptionConfidenceAssessment
from ai.abstention.config import AbstentionPolicyConfig, get_default_abstention_config
from ai.abstention.policy import (
    evaluate_field_abstention,
    evaluate_medicine_abstention,
    evaluate_prescription_abstention,
)
from ai.abstention.schemas import (
    FieldAbstentionDecision,
    HumanVerificationRecord,
    PrescriptionAbstentionDecision,
    PrescriptionVerificationState,
    VerifierActionType,
    VerificationStatus,
)


class AbstentionService:
    """
    Service coordinating uncertainty-aware abstention policies and human verification audits.
    """

    def __init__(self, config: Optional[AbstentionPolicyConfig] = None):
        self._config = config or get_default_abstention_config()
        self._lock = threading.Lock()
        # In-memory store for human verification state keyed by prescription_id
        self._verification_states: Dict[str, PrescriptionVerificationState] = {}

    @property
    def config(self) -> AbstentionPolicyConfig:
        return self._config

    def set_config(self, config: AbstentionPolicyConfig) -> None:
        with self._lock:
            self._config = config

    def evaluate_prescription(
        self,
        prescription_id: str,
        extraction_result: Optional[PrescriptionExtractionResult],
        confidence_assessment: Optional[PrescriptionConfidenceAssessment] = None,
        validation_results: Optional[List[MedicineValidationResult]] = None,
        original_image_url: Optional[str] = None,
        lasa_detection: Optional[Any] = None,
    ) -> PrescriptionAbstentionDecision:
        """
        Executes Phase 9 abstention policy evaluation over Phase 6, 7, 8, and Phase 10 artifacts.
        """
        return evaluate_prescription_abstention(
            prescription_id=prescription_id,
            extraction_result=extraction_result,
            confidence_assessment=confidence_assessment,
            validation_results=validation_results,
            config=self._config,
            original_image_url=original_image_url,
            lasa_detection=lasa_detection,
        )

    # ==========================================================================
    # Human Verification State & Audit Management
    # ==========================================================================

    def get_or_create_verification_state(
        self,
        prescription_id: str,
        original_image_url: str = "",
        pending_fields: Optional[List[str]] = None,
    ) -> PrescriptionVerificationState:
        """
        Retrieves existing verification state or initializes a new one.
        """
        with self._lock:
            if prescription_id not in self._verification_states:
                now_iso = datetime.now(timezone.utc).isoformat()
                self._verification_states[prescription_id] = PrescriptionVerificationState(
                    prescription_id=prescription_id,
                    original_image_url=original_image_url,
                    overall_verification_status="pending",
                    records={},
                    audit_trail=[],
                    pending_fields=list(pending_fields or []),
                    verified_fields=[],
                    updated_at=now_iso,
                )
            return self._verification_states[prescription_id]

    def get_verification_state(self, prescription_id: str) -> Optional[PrescriptionVerificationState]:
        """
        Retrieves current human verification state for a prescription.
        """
        with self._lock:
            return self._verification_states.get(prescription_id)

    def record_verification_action(
        self,
        prescription_id: str,
        field_id: str,
        action: VerifierActionType,
        verified_value: Optional[str] = None,
        original_value: Optional[str] = None,
        reason: Optional[str] = None,
        original_image_url: str = "",
    ) -> HumanVerificationRecord:
        """
        Records a human verification action, updating the active record and appending
        to the immutable audit trail.
        """
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            state = self._verification_states.get(prescription_id)
            if state is None:
                state = PrescriptionVerificationState(
                    prescription_id=prescription_id,
                    original_image_url=original_image_url,
                    overall_verification_status="in_progress",
                    records={},
                    audit_trail=[],
                    pending_fields=[field_id],
                    verified_fields=[],
                    updated_at=now_iso,
                )
                self._verification_states[prescription_id] = state

            # Determine verification status
            if action == "confirm":
                ver_status: VerificationStatus = "confirmed"
                final_val = original_value if verified_value is None else verified_value
            elif action == "correct":
                ver_status = "corrected"
                final_val = verified_value
            elif action == "mark_unreadable":
                ver_status = "unreadable"
                final_val = None
            else:
                ver_status = "confirmed"
                final_val = verified_value

            rec_id = f"VERIF-{uuid.uuid4().hex[:12].upper()}"
            record = HumanVerificationRecord(
                verification_id=rec_id,
                prescription_id=prescription_id,
                field_id=field_id,
                original_value=original_value,
                verified_value=final_val,
                verification_status=ver_status,
                verifier_action=action,
                reason=reason,
                timestamp=now_iso,
                policy_version=self._config.policy_version,
                system_version="1.0.0",
            )

            # Update active record and append to chronological audit trail
            state.records[field_id] = record
            state.audit_trail.append(record)

            if field_id not in state.verified_fields:
                state.verified_fields.append(field_id)
            if field_id in state.pending_fields:
                state.pending_fields.remove(field_id)

            # Update overall status
            if len(state.pending_fields) == 0 and len(state.verified_fields) > 0:
                state.overall_verification_status = "completed"
            else:
                state.overall_verification_status = "in_progress"

            state.updated_at = now_iso
            return record

    def confirm_field(
        self,
        prescription_id: str,
        field_id: str,
        original_value: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> HumanVerificationRecord:
        """Human confirms the extracted value as accurate against the original script."""
        return self.record_verification_action(
            prescription_id=prescription_id,
            field_id=field_id,
            action="confirm",
            verified_value=original_value,
            original_value=original_value,
            reason=reason or "Confirmed accurate against original prescription handwriting.",
        )

    def correct_field(
        self,
        prescription_id: str,
        field_id: str,
        corrected_value: str,
        original_value: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> HumanVerificationRecord:
        """Human reviewer provides corrected transcription for ambiguous or misread text."""
        if not corrected_value or corrected_value.strip() == "":
            raise ValueError("Corrected value cannot be empty.")
        return self.record_verification_action(
            prescription_id=prescription_id,
            field_id=field_id,
            action="correct",
            verified_value=corrected_value.strip(),
            original_value=original_value,
            reason=reason or "Corrected transcription based on visual inspection of original prescription.",
        )

    def mark_field_unreadable(
        self,
        prescription_id: str,
        field_id: str,
        original_value: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> HumanVerificationRecord:
        """Human reviewer marks the handwriting stroke as clinically unreadable."""
        return self.record_verification_action(
            prescription_id=prescription_id,
            field_id=field_id,
            action="mark_unreadable",
            verified_value=None,
            original_value=original_value,
            reason=reason or "Prescription handwriting is optically unreadable or severely degraded.",
        )


# Singleton instance
_service_instance: Optional[AbstentionService] = None
_service_lock = threading.Lock()


def get_abstention_service() -> AbstentionService:
    """Dependency injector for AbstentionService."""
    global _service_instance
    with _service_lock:
        if _service_instance is None:
            _service_instance = AbstentionService()
        return _service_instance
