"""
Deterministic In-Memory Medicine Reference Index for Phase 7 RAG.
Provides structured, multi-key access (exact name, brand, aliases, ingredients, tokens).
Avoids opaque vector indexes while delivering fast, reproducible retrieval.
"""

from typing import List, Dict, Set, Optional, Any
from collections import defaultdict
from .schemas import MedicineReferenceRecord
from .normalization import normalize_medicine_name, extract_tokens, token_set


class MedicineReferenceIndex:
    """
    In-memory deterministic multi-key index for authoritative reference records.
    """

    def __init__(self, index_version: str = "v1.0-in-memory"):
        self.index_version = index_version
        self.records_by_id: Dict[str, MedicineReferenceRecord] = {}
        self.exact_name_index: Dict[str, List[MedicineReferenceRecord]] = defaultdict(list)
        self.brand_index: Dict[str, List[MedicineReferenceRecord]] = defaultdict(list)
        self.alias_index: Dict[str, List[MedicineReferenceRecord]] = defaultdict(list)
        self.ingredient_index: Dict[str, List[MedicineReferenceRecord]] = defaultdict(list)
        self.token_to_ref_ids: Dict[str, Set[str]] = defaultdict(set)
        self._all_records: List[MedicineReferenceRecord] = []

    def build(self, records: List[MedicineReferenceRecord]) -> None:
        """
        Builds all index lookup tables deterministically from a list of records.
        """
        self.clear()
        # Sort records by reference_id for deterministic indexing order
        sorted_records = sorted(records, key=lambda r: r.reference_id)
        self._all_records = sorted_records

        for record in sorted_records:
            ref_id = record.reference_id
            self.records_by_id[ref_id] = record

            # 1. Exact canonical name index
            norm_name = record.normalized_name or normalize_medicine_name(record.medicine_name)
            self.exact_name_index[norm_name].append(record)

            # 2. Brand name index
            if record.brand_name:
                norm_brand = normalize_medicine_name(record.brand_name)
                if norm_brand:
                    self.brand_index[norm_brand].append(record)

            # 3. Alias index
            for alias in record.aliases:
                norm_alias = normalize_medicine_name(alias)
                if norm_alias:
                    self.alias_index[norm_alias].append(record)

            # 4. Ingredient index
            for ingredient in record.ingredients:
                norm_ing = normalize_medicine_name(ingredient)
                if norm_ing:
                    self.ingredient_index[norm_ing].append(record)

            # 5. Token index (combining name, brand, aliases, ingredients)
            all_text_tokens = (
                token_set(record.medicine_name)
                | (token_set(record.brand_name) if record.brand_name else set())
                | set().union(*(token_set(a) for a in record.aliases))
                | set().union(*(token_set(i) for i in record.ingredients))
            )
            for token in all_text_tokens:
                self.token_to_ref_ids[token].add(ref_id)

    def clear(self) -> None:
        """Clears all indexed records."""
        self.records_by_id.clear()
        self.exact_name_index.clear()
        self.brand_index.clear()
        self.alias_index.clear()
        self.ingredient_index.clear()
        self.token_to_ref_ids.clear()
        self._all_records.clear()

    def get_by_id(self, reference_id: str) -> Optional[MedicineReferenceRecord]:
        return self.records_by_id.get(reference_id)

    def lookup_exact_name(self, normalized_name: str) -> List[MedicineReferenceRecord]:
        return self.exact_name_index.get(normalized_name, [])

    def lookup_brand(self, normalized_brand: str) -> List[MedicineReferenceRecord]:
        return self.brand_index.get(normalized_brand, [])

    def lookup_alias(self, normalized_alias: str) -> List[MedicineReferenceRecord]:
        return self.alias_index.get(normalized_alias, [])

    def lookup_ingredient(self, normalized_ingredient: str) -> List[MedicineReferenceRecord]:
        return self.ingredient_index.get(normalized_ingredient, [])

    def lookup_by_tokens(self, tokens: Set[str]) -> List[MedicineReferenceRecord]:
        """Returns records containing at least one of the queried tokens."""
        if not tokens:
            return []
        matched_ref_ids: Set[str] = set()
        for tok in tokens:
            matched_ref_ids.update(self.token_to_ref_ids.get(tok, set()))
        return [self.records_by_id[rid] for rid in sorted(matched_ref_ids)]

    @property
    def all_records(self) -> List[MedicineReferenceRecord]:
        return self._all_records

    def stats(self) -> Dict[str, Any]:
        return {
            "index_version": self.index_version,
            "total_records": len(self._all_records),
            "unique_exact_names": len(self.exact_name_index),
            "unique_brands": len(self.brand_index),
            "unique_aliases": len(self.alias_index),
            "unique_ingredients": len(self.ingredient_index),
            "unique_tokens": len(self.token_to_ref_ids),
        }
