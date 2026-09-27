"""
Phase 7 RAG Schemas: Authoritative Medicine Reference, Retrieval, and Validation Schemas.
Preserves strict separation between prescription evidence and reference evidence.
Enforces explicit separation between medicine identity correspondence and formulation/dosage compatibility.
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class SourceProvenance(BaseModel):
    """
    Cryptographic and institutional provenance metadata for authoritative medicine references.
    """
    source_id: str = Field(..., description="Unique source identifier (e.g. cdsco-approved-drugs, nlm-rxnorm)")
    source_name: str = Field(..., description="Full regulatory or institutional title of reference database")
    source_version: str = Field(..., description="Documented edition/release version (e.g. 2024.1, 2024-08)")
    license: str = Field(..., description="Formal legal license governing data utilization")
    license_category: str = Field(..., description="License classification (e.g. statutory_government_open_data)")
    retrieval_date: str = Field(..., description="ISO 8601 acquisition timestamp")
    citation: str = Field(..., description="Formal scholarly or regulatory citation")
    source_url: Optional[str] = Field(None, description="Official authoritative portal or repository URL")


class MedicineReferenceRecord(BaseModel):
    """
    Typed authoritative medicine record originating strictly from approved references.
    Never fabricated or modified by heuristic guesses.
    """
    reference_id: str = Field(..., description="Unique immutable reference ID (e.g. REF-CDSCO-001)")
    source: str = Field(..., description="Originating authority ID (e.g. cdsco-approved-drugs, nlm-rxnorm)")
    source_version: str = Field(..., description="Source release version")
    medicine_name: str = Field(..., description="Canonical reference brand or clinical formulation title")
    normalized_name: str = Field(..., description="Precomputed normalized string for exact indexing")
    generic_name: Optional[str] = Field(None, description="Active pharmaceutical ingredient or generic salt")
    brand_name: Optional[str] = Field(None, description="Proprietary commercial brand name if distinct")
    strength: Optional[str] = Field(None, description="Approved dosage strength (e.g. 500 mg, 625 mg)")
    dosage_form: Optional[str] = Field(None, description="Physical administration form (e.g. Tablet, Capsule)")
    ingredients: List[str] = Field(default_factory=list, description="Array of active chemical substances")
    aliases: List[str] = Field(default_factory=list, description="Known bioequivalent brands or spelling variants")
    rxnorm_cui: Optional[str] = Field(None, description="NLM RxNorm Concept Unique Identifier if mapped")
    cdsco_schedule: Optional[str] = Field(None, description="Indian CDSCO Schedule classification (e.g. Schedule H)")
    atc_code: Optional[str] = Field(None, description="WHO Anatomical Therapeutic Chemical code")
    therapeutic_class: Optional[str] = Field(None, description="Pharmacological/therapeutic class")
    indications: Optional[str] = Field(None, description="Approved clinical indications")
    provenance: SourceProvenance = Field(..., description="Audit provenance for the reference record")


class RetrievalCandidate(BaseModel):
    """
    Single candidate retrieved from reference data with matching audit metrics.
    Traceable back to its originating reference_id and source.
    """
    reference_id: str = Field(..., description="ID of the matched reference record")
    source: str = Field(..., description="Originating reference authority")
    medicine_name: str = Field(..., description="Canonical medicine formulation name from reference")
    generic_name: Optional[str] = Field(None, description="Active pharmaceutical salt")
    brand_name: Optional[str] = Field(None, description="Commercial brand name if documented")
    strength: Optional[str] = Field(None, description="Documented reference strength")
    dosage_form: Optional[str] = Field(None, description="Documented reference formulation form")
    ingredients: List[str] = Field(default_factory=list, description="Reference active ingredients")
    aliases: List[str] = Field(default_factory=list, description="Reference aliases")
    rxnorm_cui: Optional[str] = Field(None, description="RxNorm CUI")
    cdsco_schedule: Optional[str] = Field(None, description="CDSCO Schedule")
    atc_code: Optional[str] = Field(None, description="ATC classification")
    therapeutic_class: Optional[str] = Field(None, description="Therapeutic class")
    indications: Optional[str] = Field(None, description="Clinical indications")
    match_method: Literal[
        "exact_normalized_name",
        "exact_alias",
        "exact_ingredient",
        "token_overlap",
        "lexical_similarity"
    ] = Field(..., description="Retrieval mechanism through which match was established")
    score: float = Field(..., ge=0.0, le=1.0, description="Deterministic match relevance score [0.0 - 1.0]")
    rank: int = Field(1, ge=1, description="Rank position in retrieved candidate list")
    evidence: str = Field(..., description="Traceable rationale detailing why candidate matched")
    provenance: SourceProvenance = Field(..., description="Source provenance of retrieved candidate")


class ValidationDecisionProvenance(BaseModel):
    """
    Audit trail capturing the exact pipeline parameters and execution conditions.
    """
    retrieval_method: str = Field(..., description="Dominant retrieval method employed")
    query_raw: str = Field(..., description="Unmodified candidate string extracted by Phase 6")
    query_normalized: str = Field(..., description="Normalized query token used for retrieval")
    normalization_version: str = Field(..., description="Version of normalization algorithm")
    index_version: str = Field(..., description="Version of reference index")
    config_hash: str = Field(..., description="SHA-256 fingerprint of active RAG configuration")
    matched_count: int = Field(..., description="Total reference candidates retrieved")
    timestamp: str = Field(..., description="ISO 8601 validation timestamp")
    validation_rule: str = Field(..., description="Deterministic decision rule triggered")
    source_authorities: List[str] = Field(..., description="Authoritative reference catalogs queried")


class MedicineValidationResult(BaseModel):
    """
    Phase 7 Medicine Validation Output.
    Strictly answers: 'Does this visually extracted candidate correspond to a known medicine in authoritative reference data?'
    Never mutates extracted prescription observations or infers dosages.
    Separates medicine identity correspondence from formulation/dosage compatibility.
    """
    input_candidate: str = Field(..., description="Original raw prescription candidate text from Phase 6")
    normalized_candidate: str = Field(..., description="Normalized representation of the input candidate")
    validation_status: Literal["validated", "uncertain", "not_validated"] = Field(
        ...,
        description=(
            "Reference correspondence status: validated (reference correspondence established according to configured retrieval/validation rules), "
            "uncertain (multiple plausible candidates or ambiguous match), or not_validated (no correspondence established). "
            "Does not imply clinical safety, medical correctness, or therapeutic appropriateness."
        )
    )
    medicine_identity_status: Literal["validated", "uncertain", "not_validated"] = Field(
        ...,
        description="Explicit medicine identity correspondence status separate from formulation/dosage compatibility."
    )
    matched_candidates: List[RetrievalCandidate] = Field(
        default_factory=list,
        description="Top-k reference candidates meeting retrieval thresholds"
    )
    selected_reference: Optional[RetrievalCandidate] = Field(
        None,
        description="Selected canonical reference candidate if identity correspondence was established"
    )
    evidence: str = Field(..., description="Evidence supporting the validation decision")
    retrieval_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed retrieval parameters, scores, and timings"
    )
    requires_human_review: bool = Field(
        ...,
        description="True if ambiguity, lack of reference data, uncertain match, or formulation mismatch requires clinician review"
    )
    dosage_observation_preserved: bool = Field(
        True,
        description="Boolean asserting that the observed dosage was strictly preserved without alteration or inference"
    )
    observed_dosage: Optional[str] = Field(
        None,
        description="Unmodified dosage visually observed in Phase 6, explicitly preserved without modification"
    )
    reference_strength: Optional[str] = Field(
        None,
        description="Formulation dosage strength documented in authoritative reference record"
    )
    formulation_consistency: Literal["consistent", "mismatch", "not_evaluated", "unspecified"] = Field(
        "unspecified",
        description="Formulation compatibility assessment between observed dosage and reference strength"
    )
    brand_generic_relationship: Optional[Dict[str, Any]] = Field(
        None,
        description="Documented relationship between brand and generic salt from reference data"
    )
    provenance: ValidationDecisionProvenance = Field(
        ...,
        description="Full audit provenance for the validation decision"
    )

    def to_ui_validation_evidence(self) -> Dict[str, Any]:
        """
        Converts validation result to the ValidationEvidence dictionary format
        expected by the Phase 1 frontend envelope.
        """
        if self.selected_reference:
            ref = self.selected_reference
            status_map = {
                "cdsco-approved-drugs": "cdsco_approved",
                "nlm-rxnorm": "rxnorm_grounded",
            }
            val_status = status_map.get(ref.source, "formulary_match")
            badge = "CDSCO APPROVED" if ref.source == "cdsco-approved-drugs" else "RXNORM GROUNDED"
            
            # Formulation mismatch warning badge
            dosage_mismatch_warning = None
            if self.formulation_consistency == "mismatch":
                badge = "DOSAGE MISMATCH (REVIEW REQUIRED)"
                val_status = "unverified"
                dosage_mismatch_warning = f"Observed dosage '{self.observed_dosage}' differs from reference strength '{self.reference_strength}'"
            elif self.validation_status != "validated":
                badge = "NEEDS VERIFICATION"
                val_status = "unverified"

            evidence_src_prefix = ""
            if self.formulation_consistency == "mismatch":
                evidence_src_prefix = (
                    f"Formulation Mismatch: Observed '{self.observed_dosage}' vs Reference '{self.reference_strength}'. "
                )

            return {
                "candidate_name": self.input_candidate,
                "matched_entity_name": ref.medicine_name,
                "generic_salt": ref.generic_name or ref.medicine_name,
                "validation_status": val_status,
                "status_badge_text": badge,
                "cdsco_schedule": ref.cdsco_schedule or "Schedule H (Prescription Drug)",
                "rxnorm_cui": ref.rxnorm_cui or "N/A",
                "atc_code": ref.atc_code or "N/A",
                "therapeutic_class": ref.therapeutic_class or "Clinical Formulation",
                "indications": ref.indications or "Standard Clinical Indications",
                "evidence_source": evidence_src_prefix + ref.provenance.source_name,
                "reference_url": ref.provenance.source_url,
                "formulation_consistency": self.formulation_consistency,
                "observed_dosage": self.observed_dosage,
                "reference_strength": self.reference_strength,
                "dosage_mismatch_warning": dosage_mismatch_warning,
                "alternatives": [
                    {
                        "name": alt.medicine_name,
                        "generic": alt.generic_name or alt.medicine_name,
                        "similarity_score": alt.score,
                        "notes": f"Matched via {alt.match_method} (Source: {alt.source})"
                    }
                    for alt in self.matched_candidates[1:5]
                ]
            }

        # Fallback for unverified / not_validated / uncertain without selection
        top_alt = self.matched_candidates[0] if self.matched_candidates else None
        return {
            "candidate_name": self.input_candidate,
            "matched_entity_name": top_alt.medicine_name if top_alt else "Unverified Candidate",
            "generic_salt": (top_alt.generic_name if top_alt else None) or "Unverified Salt",
            "validation_status": "unverified",
            "status_badge_text": "UNVERIFIED CANDIDATE" if self.validation_status == "not_validated" else "AMBIGUOUS / UNCERTAIN",
            "cdsco_schedule": (top_alt.cdsco_schedule if top_alt else None) or "Verification Required",
            "rxnorm_cui": (top_alt.rxnorm_cui if top_alt else None) or "N/A",
            "atc_code": (top_alt.atc_code if top_alt else None) or "N/A",
            "therapeutic_class": (top_alt.therapeutic_class if top_alt else None) or "Unclassified Formulation",
            "indications": "Prescription observation not confirmed against reference formulary.",
            "evidence_source": self.evidence,
            "reference_url": None,
            "alternatives": [
                {
                    "name": alt.medicine_name,
                    "generic": alt.generic_name or alt.medicine_name,
                    "similarity_score": alt.score,
                    "notes": f"Plausible candidate via {alt.match_method}"
                }
                for alt in self.matched_candidates[:4]
            ]
        }
