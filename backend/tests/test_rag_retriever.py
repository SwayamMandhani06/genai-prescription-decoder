"""
Unit tests for Phase 7 Hierarchical Retriever and Index.
Adheres to Section 7 of PLAN.md:
Retrieval Hierarchy:
1. Exact normalized name
2. Exact brand / alias
3. Exact ingredient
4. Controlled token overlap
5. Controlled lexical similarity (>= 0.75)
"""

import pytest
from pathlib import Path
from ai.rag.ingestion import ReferenceIngestor
from ai.rag.index import MedicineReferenceIndex
from ai.rag.retriever import HierarchicalRetriever
from ai.rag.config import RAGConfig


@pytest.fixture(scope="module")
def initialized_retriever():
    ingestor = ReferenceIngestor(base_dir=Path("."))
    records, _ = ingestor.ingest_all(verify_checksums=False)
    index = MedicineReferenceIndex()
    index.build(records)
    config = RAGConfig(top_k=5, min_similarity_threshold=0.75)
    return HierarchicalRetriever(index=index, config=config)


class TestRAGRetriever:
    def test_empty_query_returns_empty_list(self, initialized_retriever):
        assert initialized_retriever.retrieve("") == []
        assert initialized_retriever.retrieve("   ") == []

    def test_exact_name_match(self, initialized_retriever):
        candidates = initialized_retriever.retrieve("Augmentin 625 Duo")
        assert len(candidates) >= 1
        top = candidates[0]
        assert top.medicine_name == "Augmentin 625 Duo"
        assert top.score == 1.0
        assert top.match_method == "exact_normalized_name"
        assert top.rank == 1

    def test_exact_normalized_match_with_whitespace_and_casing(self, initialized_retriever):
        candidates = initialized_retriever.retrieve("  aUgMeNtIn   625  duo  ")
        assert len(candidates) >= 1
        top = candidates[0]
        assert top.medicine_name == "Augmentin 625 Duo"
        assert top.score == 1.0

    def test_exact_brand_match(self, initialized_retriever):
        candidates = initialized_retriever.retrieve("Dolo")
        assert len(candidates) >= 1
        top = candidates[0]
        assert "Paracetamol" in top.medicine_name or top.brand_name == "Dolo"
        assert top.score >= 0.98
        assert top.match_method == "exact_alias"


    def test_exact_alias_match(self, initialized_retriever):
        candidates = initialized_retriever.retrieve("Clavam 625")
        assert len(candidates) >= 1
        top = candidates[0]
        assert top.medicine_name == "Augmentin 625 Duo"
        assert top.score == 0.98
        assert top.match_method == "exact_alias"

    def test_exact_ingredient_match(self, initialized_retriever):
        candidates = initialized_retriever.retrieve("Azithromycin")
        assert len(candidates) >= 1
        assert any(c.generic_name == "Azithromycin" or "Azithromycin" in c.ingredients for c in candidates)
        assert candidates[0].score >= 0.95

    def test_controlled_lexical_similarity_match(self, initialized_retriever):
        # Slightly misspelled / partial variation "Augmentn 625"
        candidates = initialized_retriever.retrieve("Augmentn 625")
        assert len(candidates) >= 1
        assert candidates[0].medicine_name == "Augmentin 625 Duo"
        assert candidates[0].score >= 0.75
        assert candidates[0].match_method in ("lexical_similarity", "token_overlap")

    def test_subthreshold_query_rejection(self, initialized_retriever):
        # Completely arbitrary random string must produce NO candidates
        candidates = initialized_retriever.retrieve("ZzzQqqXxx123RandomChemical")
        assert len(candidates) == 0

    def test_top_k_limiting(self, initialized_retriever):
        candidates = initialized_retriever.retrieve("Amoxicillin", top_k=2)
        assert len(candidates) <= 2
