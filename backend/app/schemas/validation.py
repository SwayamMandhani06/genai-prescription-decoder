"""
API Schemas for Phase 7 RAG Medicine Validation Endpoint.
Conforms to PLAN.md Section 16 and Section 19.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ai.rag.schemas import MedicineValidationResult, RetrievalCandidate, ValidationDecisionProvenance


class MedicineValidationRequest(BaseModel):
    """
    Request model for validating an extracted medicine candidate against authoritative references.
    """
    candidate_name: str = Field(
        ...,
        description="Visually extracted medicine candidate text from Phase 6 or manual review",
        examples=["Augmentin 625 Duo", "Amox..."]
    )
    observed_dosage: Optional[str] = Field(
        None,
        description="Visually observed dosage from prescription (strictly preserved, never modified)",
        examples=["500 mg", "625 mg"]
    )
    top_k: Optional[int] = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of authoritative reference candidates to retrieve"
    )
    prescription_id: Optional[str] = Field(
        None,
        description="Optional tracking ID of the source prescription document"
    )


class MedicineValidationResponse(BaseModel):
    """
    Response model containing complete validation decision, retrieved candidates, and provenance.
    """
    status: str = Field("success", description="API response execution status")
    prescription_id: Optional[str] = Field(None, description="Tracking ID of the source prescription document")
    validation_result: MedicineValidationResult = Field(
        ...,
        description="Phase 7 structured medicine validation result"
    )
    ui_evidence: Dict[str, Any] = Field(
        ...,
        description="Formatted evidence dictionary compatible with Phase 1 frontend ValidationEvidence schema"
    )


class MedicineBatchValidationRequest(BaseModel):
    """
    Request model for batch-validating multiple extracted medicine candidates.
    """
    items: List[MedicineValidationRequest] = Field(
        ...,
        description="List of medicine candidate extraction items to validate"
    )


class MedicineBatchValidationResponse(BaseModel):
    """
    Response model for batch medicine validation.
    """
    status: str = Field("success", description="API response execution status")
    total_processed: int = Field(..., description="Number of items evaluated")
    results: List[MedicineValidationResponse] = Field(
        ...,
        description="Individual validation response items"
    )
