"""
Dataset and Experimental Infrastructure Module (Phase 3)
Provides dataset manifest management, ground truth schemas, deterministic normalizers,
group-aware splitting with leakage prevention, and data validation suites.
"""

from .schema import (
    GroundTruthAnnotation,
    MedicationEntityAnnotation,
    DerivedAnnotation,
    AnnotationTier,
    AmbiguityLevel,
    PrescriptionDocumentRecord,
)
from .manifest import DatasetManifest, DatasetSourceEntry, ProvenanceRecord
from .normalization import (
    normalize_text,
    normalize_dosage,
    normalize_frequency,
    ClinicalNormalizer,
)
from .splitter import GroupAwareSplitter, DatasetSplitResult, detect_split_leakage
from .validator import DatasetValidator, ValidationReport, ImageHeuristics
from .config import ExperimentConfig, DatasetVersionInfo

__all__ = [
    "GroundTruthAnnotation",
    "MedicationEntityAnnotation",
    "DerivedAnnotation",
    "AnnotationTier",
    "AmbiguityLevel",
    "PrescriptionDocumentRecord",
    "DatasetManifest",
    "DatasetSourceEntry",
    "ProvenanceRecord",
    "normalize_text",
    "normalize_dosage",
    "normalize_frequency",
    "ClinicalNormalizer",
    "GroupAwareSplitter",
    "DatasetSplitResult",
    "detect_split_leakage",
    "DatasetValidator",
    "ValidationReport",
    "ImageHeuristics",
    "ExperimentConfig",
    "DatasetVersionInfo",
]
