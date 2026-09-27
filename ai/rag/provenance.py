"""
Validation Decision Provenance and Audit Verification for Phase 7 RAG.
Adheres to Section 18 of PLAN.md:
Ensures every validation outcome is fully auditable, reproducible, and verifiable.
"""

from typing import List, Optional
from datetime import datetime, timezone
from .schemas import ValidationDecisionProvenance, MedicineValidationResult
from .config import RAGConfig


def create_provenance_record(
    query_raw: str,
    query_normalized: str,
    retrieval_method: str,
    matched_count: int,
    validation_rule: str,
    source_authorities: List[str],
    config: RAGConfig,
    timestamp: Optional[str] = None,
) -> ValidationDecisionProvenance:
    """
    Creates an immutable provenance audit record for a validation decision.
    """
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    return ValidationDecisionProvenance(
        retrieval_method=retrieval_method,
        query_raw=query_raw,
        query_normalized=query_normalized,
        normalization_version=config.normalization_version,
        index_version=config.index_version,
        config_hash=config.compute_config_hash(),
        matched_count=matched_count,
        timestamp=ts,
        validation_rule=validation_rule,
        source_authorities=source_authorities,
    )


def verify_provenance_integrity(result: MedicineValidationResult, active_config: RAGConfig) -> bool:
    """
    Verifies that the validation result's provenance matches active configuration expectations.
    """
    prov = result.provenance
    if prov.config_hash != active_config.compute_config_hash():
        return False
    if prov.normalization_version != active_config.normalization_version:
        return False
    if prov.index_version != active_config.index_version:
        return False
    return True
