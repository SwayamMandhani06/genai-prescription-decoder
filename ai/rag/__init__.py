"""
Phase 7: Evidence-Grounded Retrieval-Augmented Generation / Reference Medicine Validation Package.
Adheres strictly to PLAN.md Section 16 (RAG-based Medicine Validation).
"""

from .config import RAGConfig, get_rag_config
from .schemas import (
    MedicineReferenceRecord,
    RetrievalCandidate,
    MedicineValidationResult,
    ValidationDecisionProvenance,
    SourceProvenance,
)
from .sources import (
    CDSCO_SOURCE_ID,
    RXNORM_SOURCE_ID,
    AUTHORITATIVE_SOURCES,
    SOURCE_JUSTIFICATIONS,
    get_source_provenance,
)
from .normalization import (
    NORMALIZATION_VERSION,
    normalize_medicine_name,
    separate_raw_and_normalized,
    extract_tokens,
    token_set,
)
from .ingestion import ReferenceIngestor, IngestionReport
from .index import MedicineReferenceIndex
from .retriever import HierarchicalRetriever
from .validator import MedicineValidator
from .service import MedicineValidationService, get_medicine_validation_service
from .provenance import create_provenance_record, verify_provenance_integrity

__all__ = [
    "RAGConfig",
    "get_rag_config",
    "MedicineReferenceRecord",
    "RetrievalCandidate",
    "MedicineValidationResult",
    "ValidationDecisionProvenance",
    "SourceProvenance",
    "CDSCO_SOURCE_ID",
    "RXNORM_SOURCE_ID",
    "AUTHORITATIVE_SOURCES",
    "SOURCE_JUSTIFICATIONS",
    "get_source_provenance",
    "NORMALIZATION_VERSION",
    "normalize_medicine_name",
    "separate_raw_and_normalized",
    "extract_tokens",
    "token_set",
    "ReferenceIngestor",
    "IngestionReport",
    "MedicineReferenceIndex",
    "HierarchicalRetriever",
    "MedicineValidator",
    "MedicineValidationService",
    "get_medicine_validation_service",
    "create_provenance_record",
    "verify_provenance_integrity",
]
