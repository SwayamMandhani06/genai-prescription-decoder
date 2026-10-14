"""
Evidence-Grounded Medicine Validation Decision Engine for Phase 7 RAG.
Adheres strictly to Sections 1, 2, 11, 12, 13, and 14 of PLAN.md and Research Integrity Standards:
- Strictly answers: 'Does this visually extracted candidate correspond to a known medicine in authoritative references?'
- Defines 'validated' precisely as: Reference correspondence established according to configured retrieval/validation rules.
  (Does not claim clinical safety, medical correctness, or therapeutic appropriateness).
- Separates medicine identity validation from formulation/dosage compatibility.
- Never modifies or infers prescription candidates or dosage observations.
- Escalates formulation/dosage mismatches to mandatory human review.
"""

from typing import List, Optional, Tuple, Dict, Any, Literal
from .schemas import (
    RetrievalCandidate,
    MedicineValidationResult,
    ValidationDecisionProvenance,
)
from .normalization import separate_raw_and_normalized, token_set
from .config import RAGConfig, get_rag_config
from .sources import CDSCO_SOURCE_ID, RXNORM_SOURCE_ID


import re


def parse_strength_value_unit(strength_str: str) -> Tuple[Optional[float], Optional[str]]:
    """Extracts numeric magnitude and unit from a dosage string (e.g., '500 mg' -> (500.0, 'mg'))."""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z%]+)", strength_str)
    if match:
        try:
            return float(match.group(1)), match.group(2).lower()
        except ValueError:
            return None, None
    return None, None


def evaluate_formulation_consistency(
    observed_dosage: Optional[str],
    reference_strength: Optional[str],
) -> Tuple[Literal["consistent", "mismatch", "not_evaluated"], Optional[str]]:
    """
    Evaluates compatibility between prescription observed dosage and reference strength.
    Detects critical unit confusion (e.g., mg vs mcg) and 10x decimal errors (e.g., 5000 mg vs 500 mg).
    Never mutates, alters, or infers posology.
    """
    if not observed_dosage or not observed_dosage.strip():
        return "not_evaluated", None
    if not reference_strength or not reference_strength.strip():
        return "not_evaluated", None

    obs_val, obs_unit = parse_strength_value_unit(observed_dosage)
    ref_val, ref_unit = parse_strength_value_unit(reference_strength)

    # 1. Critical Clinical Safety Bounds (FMEA-01 / HIGH-04)
    if obs_val is not None and ref_val is not None and obs_unit and ref_unit:
        # Unit confusion hazard: mg prescribed instead of microgram (1000x overdose)
        if obs_unit in ("mg", "g") and ref_unit in ("mcg", "ug", "microgram", "micrograms"):
            return (
                "mismatch",
                f"CRITICAL_DOSAGE_OUT_OF_RANGE: Unit mismatch hazard detected (Observed '{observed_dosage}' vs Reference '{reference_strength}'). Prescribing milligrams instead of micrograms presents severe overdose risk."
            )
        # Decimal shift / 10x overdose hazard: observed value is 5x or more of manufactured strength
        if obs_unit == ref_unit and obs_val >= (4.5 * ref_val):
            return (
                "mismatch",
                f"CRITICAL_DOSAGE_OUT_OF_RANGE: Extreme dosage magnitude detected (Observed '{observed_dosage}' vs Reference '{reference_strength}'). Potential decimal point misread or overdose hazard."
            )
        # Exact numerical & unit match
        if obs_unit == ref_unit and abs(obs_val - ref_val) < 1e-4:
            return "consistent", f"Observed dosage '{observed_dosage}' matches reference strength '{reference_strength}' exactly."

    obs_toks = token_set(observed_dosage)
    ref_toks = token_set(reference_strength)

    if obs_toks and (obs_toks == ref_toks or obs_toks.issubset(ref_toks) or ref_toks.issubset(obs_toks)):
        return "consistent", f"Observed dosage '{observed_dosage}' is consistent with reference strength '{reference_strength}'."

    return "mismatch", f"Observed dosage '{observed_dosage}' differs from reference strength '{reference_strength}'."



class MedicineValidator:
    """
    Evaluates retrieved reference evidence against extracted prescription candidate.
    Applies conservative clinical validation policy separating identity from formulation.
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()

    def validate(
        self,
        candidate_name: str,
        retrieved_candidates: List[RetrievalCandidate],
        observed_dosage: Optional[str] = None,
        timestamp_iso: str = "2026-09-27T00:00:00Z",
    ) -> MedicineValidationResult:
        """
        Executes deterministic validation logic.
        """
        raw_candidate, norm_candidate = separate_raw_and_normalized(candidate_name)
        cfg_hash = self.config.compute_config_hash()

        # ----------------------------------------------------------------------
        # Case 1: Empty or Missing Candidate
        # ----------------------------------------------------------------------
        if not raw_candidate or not raw_candidate.strip():
            provenance = ValidationDecisionProvenance(
                retrieval_method="none",
                query_raw=raw_candidate,
                query_normalized=norm_candidate,
                normalization_version=self.config.normalization_version,
                index_version=self.config.index_version,
                config_hash=cfg_hash,
                matched_count=0,
                timestamp=timestamp_iso,
                validation_rule="EMPTY_CANDIDATE_REJECTION",
                source_authorities=[CDSCO_SOURCE_ID, RXNORM_SOURCE_ID],
            )
            return MedicineValidationResult(
                input_candidate=raw_candidate,
                normalized_candidate=norm_candidate,
                validation_status="not_validated",
                medicine_identity_status="not_validated",
                matched_candidates=[],
                selected_reference=None,
                evidence="No medicine name candidate was extracted from visual evidence.",
                retrieval_metadata={"error": "empty_query"},
                requires_human_review=True,
                dosage_observation_preserved=True,
                observed_dosage=observed_dosage,
                reference_strength=None,
                formulation_consistency="not_evaluated",
                brand_generic_relationship=None,
                provenance=provenance,
            )

        # ----------------------------------------------------------------------
        # Case 2: Zero Retrieved Candidates
        # ----------------------------------------------------------------------
        if not retrieved_candidates:
            provenance = ValidationDecisionProvenance(
                retrieval_method="hierarchical_exhausted",
                query_raw=raw_candidate,
                query_normalized=norm_candidate,
                normalization_version=self.config.normalization_version,
                index_version=self.config.index_version,
                config_hash=cfg_hash,
                matched_count=0,
                timestamp=timestamp_iso,
                validation_rule="NO_REFERENCE_MATCH_FOUND",
                source_authorities=[CDSCO_SOURCE_ID, RXNORM_SOURCE_ID],
            )
            return MedicineValidationResult(
                input_candidate=raw_candidate,
                normalized_candidate=norm_candidate,
                validation_status="not_validated",
                medicine_identity_status="not_validated",
                matched_candidates=[],
                selected_reference=None,
                evidence=(
                    f"Candidate '{raw_candidate}' has no corresponding approved formulation "
                    f"in queried authoritative references (CDSCO / RxNorm subsets)."
                ),
                retrieval_metadata={"matched_count": 0, "threshold": self.config.min_similarity_threshold},
                requires_human_review=True,
                dosage_observation_preserved=True,
                observed_dosage=observed_dosage,
                reference_strength=None,
                formulation_consistency="not_evaluated",
                brand_generic_relationship=None,
                provenance=provenance,
            )

        top_cand = retrieved_candidates[0]
        has_competitor = len(retrieved_candidates) > 1
        second_cand = retrieved_candidates[1] if has_competitor else None

        # Check for ambiguity: multiple candidates with close scores
        is_ambiguous = (
            has_competitor
            and second_cand is not None
            and (top_cand.score - second_cand.score) <= self.config.ambiguity_margin
        )

        # ----------------------------------------------------------------------
        # Case 3: Multiple Plausible Candidates with Ambiguous Proximity
        # ----------------------------------------------------------------------
        if is_ambiguous:
            competing_names = ", ".join(f"'{c.medicine_name}' ({c.score:.2f})" for c in retrieved_candidates[:3])
            provenance = ValidationDecisionProvenance(
                retrieval_method=top_cand.match_method,
                query_raw=raw_candidate,
                query_normalized=norm_candidate,
                normalization_version=self.config.normalization_version,
                index_version=self.config.index_version,
                config_hash=cfg_hash,
                matched_count=len(retrieved_candidates),
                timestamp=timestamp_iso,
                validation_rule="MULTI_CANDIDATE_AMBIGUITY_GATE",
                source_authorities=[CDSCO_SOURCE_ID, RXNORM_SOURCE_ID],
            )
            consistency, _ = evaluate_formulation_consistency(observed_dosage, top_cand.strength)
            return MedicineValidationResult(
                input_candidate=raw_candidate,
                normalized_candidate=norm_candidate,
                validation_status="uncertain",
                medicine_identity_status="uncertain",
                matched_candidates=retrieved_candidates,
                selected_reference=None,  # Do NOT pick one arbitrarily!
                evidence=(
                    f"Prescription candidate '{raw_candidate}' matches multiple plausible formulations "
                    f"with near-equal relevance: {competing_names}. Preserving uncertainty for clinician disambiguation."
                ),
                retrieval_metadata={
                    "top_score": top_cand.score,
                    "second_score": second_cand.score if second_cand else None,
                    "margin": self.config.ambiguity_margin,
                },
                requires_human_review=True,
                dosage_observation_preserved=True,
                observed_dosage=observed_dosage,
                reference_strength=top_cand.strength,
                formulation_consistency=consistency,
                brand_generic_relationship={
                    "brand_name": top_cand.brand_name,
                    "generic_name": top_cand.generic_name,
                    "active_ingredients": top_cand.ingredients,
                } if (top_cand.brand_name or top_cand.generic_name) else None,
                provenance=provenance,
            )

        # ----------------------------------------------------------------------
        # Case 4: High-Confidence Autonomous Match (Score >= threshold)
        # ----------------------------------------------------------------------
        if top_cand.score >= self.config.validation_score_threshold:
            provenance = ValidationDecisionProvenance(
                retrieval_method=top_cand.match_method,
                query_raw=raw_candidate,
                query_normalized=norm_candidate,
                normalization_version=self.config.normalization_version,
                index_version=self.config.index_version,
                config_hash=cfg_hash,
                matched_count=len(retrieved_candidates),
                timestamp=timestamp_iso,
                validation_rule="HIGH_CONFIDENCE_FORMULARY_VALIDATED",
                source_authorities=[CDSCO_SOURCE_ID, RXNORM_SOURCE_ID],
            )
            brand_generic = {
                "brand_name": top_cand.brand_name,
                "generic_name": top_cand.generic_name,
                "active_ingredients": top_cand.ingredients,
            }

            # Evaluate formulation consistency separately
            consistency, consistency_note = evaluate_formulation_consistency(observed_dosage, top_cand.strength)
            is_mismatch = (consistency == "mismatch")

            # SAFETY INVARIANT: If formulation mismatch exists, human review is MANDATORY!
            needs_review = is_mismatch

            evidence_text = (
                f"Prescription observation '{raw_candidate}' corresponds to authorized formulary "
                f"record '{top_cand.medicine_name}' via {top_cand.match_method} (Score: {top_cand.score:.2f}, "
                f"Source: {top_cand.source})."
            )
            if is_mismatch:
                evidence_text += (
                    f" NOTE: Formulation strength mismatch detected (observed '{observed_dosage}' "
                    f"vs reference strength '{top_cand.strength}'). Observed posology is preserved without "
                    f"alteration and mandates clinical review."
                )

            return MedicineValidationResult(
                input_candidate=raw_candidate,
                normalized_candidate=norm_candidate,
                validation_status="validated",
                medicine_identity_status="validated",
                matched_candidates=retrieved_candidates,
                selected_reference=top_cand,
                evidence=evidence_text,
                retrieval_metadata={
                    "dominant_method": top_cand.match_method,
                    "matched_score": top_cand.score,
                    "reference_id": top_cand.reference_id,
                },
                requires_human_review=needs_review,
                dosage_observation_preserved=True,
                observed_dosage=observed_dosage,
                reference_strength=top_cand.strength,
                formulation_consistency=consistency,
                brand_generic_relationship=brand_generic,
                provenance=provenance,
            )

        # ----------------------------------------------------------------------
        # Case 5: Moderate Lexical Similarity but Insufficient for Autonomous Validation
        # ----------------------------------------------------------------------
        if top_cand.score >= self.config.min_similarity_threshold:
            provenance = ValidationDecisionProvenance(
                retrieval_method=top_cand.match_method,
                query_raw=raw_candidate,
                query_normalized=norm_candidate,
                normalization_version=self.config.normalization_version,
                index_version=self.config.index_version,
                config_hash=cfg_hash,
                matched_count=len(retrieved_candidates),
                timestamp=timestamp_iso,
                validation_rule="LEXICAL_SIMILARITY_UNCERTAIN_GATE",
                source_authorities=[CDSCO_SOURCE_ID, RXNORM_SOURCE_ID],
            )
            consistency, _ = evaluate_formulation_consistency(observed_dosage, top_cand.strength)
            return MedicineValidationResult(
                input_candidate=raw_candidate,
                normalized_candidate=norm_candidate,
                validation_status="uncertain",
                medicine_identity_status="uncertain",
                matched_candidates=retrieved_candidates,
                selected_reference=None,
                evidence=(
                    f"Candidate '{raw_candidate}' demonstrates lexical similarity ({top_cand.score:.2f}) "
                    f"to reference '{top_cand.medicine_name}' via {top_cand.match_method}. "
                    f"Visual evidence is insufficient to autonomously confirm drug identity."
                ),
                retrieval_metadata={
                    "top_score": top_cand.score,
                    "threshold_required": self.config.validation_score_threshold,
                },
                requires_human_review=True,
                dosage_observation_preserved=True,
                observed_dosage=observed_dosage,
                reference_strength=top_cand.strength,
                formulation_consistency=consistency,
                brand_generic_relationship={
                    "brand_name": top_cand.brand_name,
                    "generic_name": top_cand.generic_name,
                    "active_ingredients": top_cand.ingredients,
                },
                provenance=provenance,
            )

        # ----------------------------------------------------------------------
        # Case 6: Sub-threshold fallback
        # ----------------------------------------------------------------------
        provenance = ValidationDecisionProvenance(
            retrieval_method=top_cand.match_method,
            query_raw=raw_candidate,
            query_normalized=norm_candidate,
            normalization_version=self.config.normalization_version,
            index_version=self.config.index_version,
            config_hash=cfg_hash,
            matched_count=len(retrieved_candidates),
            timestamp=timestamp_iso,
            validation_rule="SUBTHRESHOLD_MATCH_REJECTED",
            source_authorities=[CDSCO_SOURCE_ID, RXNORM_SOURCE_ID],
        )
        return MedicineValidationResult(
            input_candidate=raw_candidate,
            normalized_candidate=norm_candidate,
            validation_status="not_validated",
            medicine_identity_status="not_validated",
            matched_candidates=[],
            selected_reference=None,
            evidence=f"No reference formulation achieved the minimum confidence threshold ({self.config.min_similarity_threshold}).",
            retrieval_metadata={"best_score": top_cand.score},
            requires_human_review=True,
            dosage_observation_preserved=True,
            observed_dosage=observed_dosage,
            reference_strength=None,
            formulation_consistency="not_evaluated",
            brand_generic_relationship=None,
            provenance=provenance,
        )
