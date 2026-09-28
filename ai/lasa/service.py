"""
Phase 10: LASA Detection Service.
Provides singleton dependency injection for LASA conflict detection.
Integrates with the RAG index to obtain reference medicine records.
"""

import threading
from typing import List, Optional

from ai.rag import get_medicine_validation_service
from ai.rag.schemas import MedicineReferenceRecord
from ai.lasa.config import LasaConfig, get_default_lasa_config
from ai.lasa.schemas import PrescriptionLasaDetection, MedicineLasaResult
from ai.lasa.detector import detect_prescription_lasa, screen_medicine


class LasaDetectionService:
    """
    Service coordinating LASA conflict detection over extracted prescription medicines.
    Thread-safe singleton with configurable policy.
    """

    def __init__(self, config: Optional[LasaConfig] = None):
        self._config = config or get_default_lasa_config()
        self._lock = threading.Lock()

    @property
    def config(self) -> LasaConfig:
        return self._config

    def set_config(self, config: LasaConfig) -> None:
        with self._lock:
            self._config = config

    def _get_reference_records(self) -> Optional[List[MedicineReferenceRecord]]:
        """
        Obtains the full reference medicine record pool from the RAG index.
        Uses the existing RAG service's index to avoid duplicating data.
        Returns None if the reference index is inaccessible.
        """
        try:
            val_service = get_medicine_validation_service()
            return val_service.retriever.index.all_records
        except Exception:
            return None

    def detect_prescription(
        self,
        prescription_id: str,
        medicine_names: List[str],
        reference_records: Optional[List[MedicineReferenceRecord]] = None,
    ) -> PrescriptionLasaDetection:
        """
        Runs LASA detection for all medicines in a prescription.

        Args:
            prescription_id: Prescription tracking identifier
            medicine_names: List of extracted medicine names
            reference_records: Optional override of reference records
                             (uses RAG index if None)

        Returns:
            PrescriptionLasaDetection with all screening results
        """
        refs = reference_records if reference_records is not None else self._get_reference_records()
        return detect_prescription_lasa(
            prescription_id=prescription_id,
            medicine_names=medicine_names,
            reference_records=refs,
            config=self._config,
        )

    def screen_single_medicine(
        self,
        candidate_name: str,
        item_index: int = 1,
        reference_records: Optional[List[MedicineReferenceRecord]] = None,
    ) -> MedicineLasaResult:
        """
        Screens a single medicine name for LASA conflicts.

        Args:
            candidate_name: Extracted medicine name
            item_index: 1-based line item index
            reference_records: Optional override (uses RAG index if None)

        Returns:
            MedicineLasaResult for the single candidate
        """
        refs = reference_records if reference_records is not None else self._get_reference_records()
        return screen_medicine(
            candidate_name=candidate_name,
            item_index=item_index,
            reference_records=refs,
            config=self._config,
        )


# Singleton instance
_service_instance: Optional[LasaDetectionService] = None
_service_lock = threading.Lock()


def get_lasa_detection_service() -> LasaDetectionService:
    """Dependency injector for LasaDetectionService."""
    global _service_instance
    with _service_lock:
        if _service_instance is None:
            _service_instance = LasaDetectionService()
        return _service_instance
