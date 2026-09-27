"""
Phase 7 Medicine Validation Service Facade.
Coordinates ingestion, indexing, hierarchical retrieval, deterministic validation,
and auditable provenance generation.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import RAGConfig, get_rag_config
from .schemas import MedicineValidationResult
from .ingestion import ReferenceIngestor, IngestionReport
from .index import MedicineReferenceIndex
from .retriever import HierarchicalRetriever
from .validator import MedicineValidator

logger = logging.getLogger("aura_rx.rag.service")


class MedicineValidationService:
    """
    Unified Phase 7 Medicine Validation Service.
    Answers: 'Does this visually extracted candidate correspond to a known medicine in authoritative references?'
    """

    def __init__(self, config: Optional[RAGConfig] = None, project_root: Optional[Path] = None):
        self.config = config or get_rag_config()
        self.project_root = project_root or Path.cwd()
        self.ingestor = ReferenceIngestor(base_dir=self.project_root)
        self.index = MedicineReferenceIndex(index_version=self.config.index_version)
        self.retriever = HierarchicalRetriever(index=self.index, config=self.config)
        self.validator = MedicineValidator(config=self.config)
        self.ingestion_report: Optional[IngestionReport] = None
        self._is_initialized = False

        if self.config.enabled:
            self.initialize()

    def initialize(self) -> None:
        """
        Loads reference datasets, verifies checksums, and constructs the deterministic index.
        """
        try:
            records, report = self.ingestor.ingest_all(
                manifest_rel_path=self.config.manifest_path,
                verify_checksums=True
            )
            self.index.build(records)
            self.ingestion_report = report
            self._is_initialized = True
            logger.info(
                "MedicineValidationService initialized successfully with %d authoritative records",
                len(records)
            )
        except Exception as e:
            logger.error("Failed to initialize MedicineValidationService: %s", str(e), exc_info=True)
            self._is_initialized = False

    def validate_candidate(
        self,
        candidate_name: str,
        observed_dosage: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> MedicineValidationResult:
        """
        Validates a single visually extracted medicine candidate against authoritative references.
        Guarantees that observed_dosage is preserved and never mutated.
        """
        if not self._is_initialized:
            self.initialize()

        k = top_k if top_k is not None else self.config.top_k
        retrieved_candidates = self.retriever.retrieve(query=candidate_name, top_k=k)
        result = self.validator.validate(
            candidate_name=candidate_name,
            retrieved_candidates=retrieved_candidates,
            observed_dosage=observed_dosage,
        )
        return result

    def validate_batch(self, items: List[Dict[str, Any]]) -> List[MedicineValidationResult]:
        """
        Validates a batch of medicine candidate dictionaries.
        Each dict may have 'medicine_name' (or 'candidate_name') and optional 'dosage'.
        """
        results: List[MedicineValidationResult] = []
        for item in items:
            name = item.get("medicine_name") or item.get("candidate_name") or ""
            dosage = item.get("dosage")
            top_k = item.get("top_k")
            results.append(self.validate_candidate(name, observed_dosage=dosage, top_k=top_k))
        return results

    def get_service_status(self) -> Dict[str, Any]:
        """
        Reports operational telemetry and index audit metrics.
        """
        return {
            "initialized": self._is_initialized,
            "config_hash": self.config.compute_config_hash(),
            "config": self.config.model_dump(),
            "index_stats": self.index.stats(),
            "ingestion_report": self.ingestion_report.to_dict() if self.ingestion_report else None,
        }


_singleton_service: Optional[MedicineValidationService] = None


def get_medicine_validation_service() -> MedicineValidationService:
    """Returns singleton instance of MedicineValidationService."""
    global _singleton_service
    if _singleton_service is None:
        _singleton_service = MedicineValidationService()
    return _singleton_service
