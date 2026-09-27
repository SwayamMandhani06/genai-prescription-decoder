"""
Hierarchical Deterministic Reference Retriever for Phase 7 RAG.
Adheres strictly to Section 7 of PLAN.md:
Retrieval Hierarchy:
1. Exact normalized name match
2. Exact brand / alias match
3. Exact ingredient match
4. Controlled normalized token overlap
5. Controlled lexical similarity (threshold >= 0.75)
No unconstrained fuzzy guessing or opaque vector retrieval.
"""

from typing import List, Dict, Set, Optional, Tuple
import difflib
from .schemas import RetrievalCandidate, MedicineReferenceRecord
from .normalization import normalize_medicine_name, extract_tokens, token_set
from .index import MedicineReferenceIndex
from .config import RAGConfig, get_rag_config


class HierarchicalRetriever:
    """
    Executes staged deterministic candidate retrieval against MedicineReferenceIndex.
    """

    def __init__(self, index: MedicineReferenceIndex, config: Optional[RAGConfig] = None):
        self.index = index
        self.config = config or get_rag_config()

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievalCandidate]:
        """
        Executes hierarchical retrieval for a medicine candidate query.
        Returns ordered, deduplicated, traceable candidates.
        """
        k = top_k if top_k is not None else self.config.top_k
        if not query or not query.strip():
            return []

        norm_query = normalize_medicine_name(query)
        q_tokens = token_set(query)

        # Dictionary mapping reference_id -> (score, method, evidence, record)
        candidate_map: Dict[str, Tuple[float, str, str, MedicineReferenceRecord]] = {}

        def register_match(record: MedicineReferenceRecord, score: float, method: str, evidence: str):
            ref_id = record.reference_id
            if ref_id not in candidate_map or score > candidate_map[ref_id][0]:
                candidate_map[ref_id] = (score, method, evidence, record)

        # ----------------------------------------------------------------------
        # Stage 1: Exact Normalized Canonical Name Match
        # ----------------------------------------------------------------------
        exact_name_records = self.index.lookup_exact_name(norm_query)
        for rec in exact_name_records:
            register_match(
                record=rec,
                score=1.0,
                method="exact_normalized_name",
                evidence=f"Exact match on canonical reference formulation '{rec.medicine_name}'"
            )

        # ----------------------------------------------------------------------
        # Stage 2: Exact Brand Match
        # ----------------------------------------------------------------------
        exact_brand_records = self.index.lookup_brand(norm_query)
        for rec in exact_brand_records:
            register_match(
                record=rec,
                score=0.99,
                method="exact_alias",
                evidence=f"Exact match on reference proprietary brand '{rec.brand_name}' ({rec.medicine_name})"
            )

        # ----------------------------------------------------------------------
        # Stage 3: Exact Alias Match
        # ----------------------------------------------------------------------
        exact_alias_records = self.index.lookup_alias(norm_query)
        for rec in exact_alias_records:
            register_match(
                record=rec,
                score=0.98,
                method="exact_alias",
                evidence=f"Exact match on reference alias/synonym for '{rec.medicine_name}'"
            )

        # ----------------------------------------------------------------------
        # Stage 4: Exact Ingredient Match
        # ----------------------------------------------------------------------
        exact_ing_records = self.index.lookup_ingredient(norm_query)
        for rec in exact_ing_records:
            register_match(
                record=rec,
                score=0.95,
                method="exact_ingredient",
                evidence=f"Exact match on active pharmaceutical ingredient '{norm_query}' in '{rec.medicine_name}'"
            )

        # ----------------------------------------------------------------------
        # Stage 5: Controlled Normalized Token Overlap
        # ----------------------------------------------------------------------
        if q_tokens:
            token_candidates = self.index.lookup_by_tokens(q_tokens)
            for rec in token_candidates:
                rec_tokens = (
                    token_set(rec.medicine_name)
                    | (token_set(rec.brand_name) if rec.brand_name else set())
                    | set().union(*(token_set(a) for a in rec.aliases))
                )
                intersection = q_tokens & rec_tokens
                if not intersection:
                    continue

                jaccard = len(intersection) / len(q_tokens | rec_tokens)
                containment = len(intersection) / len(q_tokens)
                weighted_score = (0.5 * jaccard) + (0.5 * containment)

                if weighted_score >= 0.70:
                    bounded_score = min(0.92, round(weighted_score, 3))
                    matched_words = ", ".join(sorted(intersection))
                    register_match(
                        record=rec,
                        score=bounded_score,
                        method="token_overlap",
                        evidence=f"Controlled token overlap ({matched_words}) with formulation '{rec.medicine_name}'"
                    )

        # ----------------------------------------------------------------------
        # Stage 6: Controlled Lexical Similarity
        # Evaluated against candidate pool or all records if pool is small
        # ----------------------------------------------------------------------
        eval_records = self.index.all_records
        for rec in eval_records:
            # Check ratio against normalized medicine name
            rec_norm = rec.normalized_name or normalize_medicine_name(rec.medicine_name)
            name_ratio = difflib.SequenceMatcher(None, norm_query, rec_norm).ratio()
            
            # Check ratio against brand if present
            brand_ratio = 0.0
            if rec.brand_name:
                brand_ratio = difflib.SequenceMatcher(
                    None, norm_query, normalize_medicine_name(rec.brand_name)
                ).ratio()

            # Check ratio against aliases
            alias_ratio = 0.0
            for a in rec.aliases:
                ar = difflib.SequenceMatcher(None, norm_query, normalize_medicine_name(a)).ratio()
                if ar > alias_ratio:
                    alias_ratio = ar

            best_ratio = max(name_ratio, brand_ratio, alias_ratio)
            if best_ratio >= self.config.min_similarity_threshold:
                bounded_ratio = min(0.94, round(best_ratio, 3))
                register_match(
                    record=rec,
                    score=bounded_ratio,
                    method="lexical_similarity",
                    evidence=(
                        f"Controlled lexical similarity ({bounded_ratio:.2f}) with "
                        f"reference '{rec.medicine_name}'"
                    )
                )

        # ----------------------------------------------------------------------
        # Sort and Format Top-K Candidates
        # Deterministic order: descending score, then ascending reference_id
        # ----------------------------------------------------------------------
        sorted_items = sorted(
            candidate_map.values(),
            key=lambda x: (-x[0], x[3].reference_id)
        )

        candidates: List[RetrievalCandidate] = []
        for rank, (score, method, evidence, record) in enumerate(sorted_items[:k], start=1):
            candidates.append(
                RetrievalCandidate(
                    reference_id=record.reference_id,
                    source=record.source,
                    medicine_name=record.medicine_name,
                    generic_name=record.generic_name,
                    brand_name=record.brand_name,
                    strength=record.strength,
                    dosage_form=record.dosage_form,
                    ingredients=record.ingredients,
                    aliases=record.aliases,
                    rxnorm_cui=record.rxnorm_cui,
                    cdsco_schedule=record.cdsco_schedule,
                    atc_code=record.atc_code,
                    therapeutic_class=record.therapeutic_class,
                    indications=record.indications,
                    match_method=method,  # type: ignore
                    score=score,
                    rank=rank,
                    evidence=evidence,
                    provenance=record.provenance,
                )
            )

        return candidates
