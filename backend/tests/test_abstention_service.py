"""
Unit tests for Phase 9 Abstention Service & Human Verification Workflow.
Verifies:
- Human confirmation workflow
- Human correction workflow with original value preservation
- Human mark unreadable workflow
- Chronological immutable audit trail
- Overall verification state transitions (pending -> in_progress -> completed)
- Error handling on invalid/empty inputs
"""

import pytest
from ai.abstention.service import AbstentionService


class TestAbstentionService:
    def test_confirm_field_action(self):
        service = AbstentionService()
        record = service.confirm_field(
            prescription_id="RX-001",
            field_id="medicine_name",
            original_value="Augmentin 625 Duo",
            reason="Confirmed against original document.",
        )
        assert record.verification_status == "confirmed"
        assert record.verifier_action == "confirm"
        assert record.original_value == "Augmentin 625 Duo"
        assert record.verified_value == "Augmentin 625 Duo"

        state = service.get_verification_state("RX-001")
        assert state is not None
        assert "medicine_name" in state.records
        assert len(state.audit_trail) == 1

    def test_correct_field_action_preserves_original(self):
        service = AbstentionService()
        record = service.correct_field(
            prescription_id="RX-002",
            field_id="medicine_name",
            corrected_value="Amoxicillin 500mg",
            original_value="Amoxcillin 500mg",
            reason="Corrected minor spelling error in transcription.",
        )
        assert record.verification_status == "corrected"
        assert record.verifier_action == "correct"
        assert record.original_value == "Amoxcillin 500mg"
        assert record.verified_value == "Amoxicillin 500mg"

        # State audit verification
        state = service.get_verification_state("RX-002")
        assert state is not None
        assert state.records["medicine_name"].verified_value == "Amoxicillin 500mg"
        assert state.records["medicine_name"].original_value == "Amoxcillin 500mg"

    def test_mark_unreadable_action(self):
        service = AbstentionService()
        record = service.mark_field_unreadable(
            prescription_id="RX-003",
            field_id="duration",
            original_value="???",
            reason="Handwriting stroke is illegible.",
        )
        assert record.verification_status == "unreadable"
        assert record.verifier_action == "mark_unreadable"
        assert record.verified_value is None

    def test_empty_correction_raises_error(self):
        service = AbstentionService()
        with pytest.raises(ValueError, match="Corrected value cannot be empty"):
            service.correct_field(
                prescription_id="RX-004",
                field_id="dosage",
                corrected_value="   ",
            )

    def test_chronological_audit_trail_multiple_edits(self):
        service = AbstentionService()
        # Step 1: Initial correction
        rec1 = service.correct_field(
            prescription_id="RX-AUDIT",
            field_id="dosage",
            corrected_value="500 mg",
            original_value="50 mg",
            reason="Initial correction",
        )
        # Step 2: Second clarification edit
        rec2 = service.correct_field(
            prescription_id="RX-AUDIT",
            field_id="dosage",
            corrected_value="625 mg",
            original_value="50 mg",
            reason="Re-inspected under high magnification",
        )
        state = service.get_verification_state("RX-AUDIT")
        assert state is not None
        assert len(state.audit_trail) == 2
        assert state.audit_trail[0].verified_value == "500 mg"
        assert state.audit_trail[1].verified_value == "625 mg"
        # Current active record reflects the latest determination
        assert state.records["dosage"].verified_value == "625 mg"
        assert state.records["dosage"].original_value == "50 mg"

    def test_verification_state_transitions(self):
        service = AbstentionService()
        state = service.get_or_create_verification_state(
            prescription_id="RX-TRANS",
            pending_fields=["medicine_name", "dosage"],
        )
        assert state.overall_verification_status == "pending"

        # Verify field 1 -> in_progress
        service.confirm_field("RX-TRANS", "medicine_name", original_value="Paracetamol")
        state = service.get_verification_state("RX-TRANS")
        assert state.overall_verification_status == "in_progress"

        # Verify field 2 -> completed
        service.confirm_field("RX-TRANS", "dosage", original_value="500 mg")
        state = service.get_verification_state("RX-TRANS")
        assert state.overall_verification_status == "completed"
