"""
Phase 10: LASA (Look-Alike / Sound-Alike) Medicine Conflict Detection Layer.
Adheres strictly to PLAN.md:
- Identifies potential medicine name confusion via lexical and phonetic similarity
- Curates ISMP Tall Man Lettering pairs
- Safety-oriented: flags conflicts for Phase 9 verification, does NOT resolve them
- Medicine identity only — dosage/strength similarity is out of scope
- Deterministic, reproducible, and auditable
"""

from ai.lasa.config import LasaConfig, get_default_lasa_config, TALL_MAN_PAIRS
from ai.lasa.schemas import (
    LasaSimilarityDetail,
    MedicineLasaResult,
    PrescriptionLasaDetection,
    LasaDetectionProvenance,
)
from ai.lasa.similarity import (
    orthographic_similarity,
    phonetic_similarity,
    metaphone_exact_match,
    combined_similarity,
    compute_metaphone,
    lookup_tall_man_pair,
)
from ai.lasa.detector import (
    screen_medicine,
    detect_prescription_lasa,
)
from ai.lasa.service import LasaDetectionService, get_lasa_detection_service

__all__ = [
    "LasaConfig",
    "get_default_lasa_config",
    "TALL_MAN_PAIRS",
    "LasaSimilarityDetail",
    "MedicineLasaResult",
    "PrescriptionLasaDetection",
    "LasaDetectionProvenance",
    "orthographic_similarity",
    "phonetic_similarity",
    "metaphone_exact_match",
    "combined_similarity",
    "compute_metaphone",
    "lookup_tall_man_pair",
    "screen_medicine",
    "detect_prescription_lasa",
    "LasaDetectionService",
    "get_lasa_detection_service",
]
