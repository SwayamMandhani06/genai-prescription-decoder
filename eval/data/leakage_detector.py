"""
Data Leakage Detector (Section 51).
Verifies strict partition isolation across train, calibration, and test splits:
- Zero document ID overlap
- Zero patient group ID overlap (group-aware isolation)
- Zero image SHA-256 duplicate content leakage
"""

from typing import Any, Dict, List, Set
from eval.data.dataset_loader import EvaluationDatasetLoader


class LeakageAuditReport:
    def __init__(self):
        self.passed: bool = True
        self.doc_id_overlap: List[str] = []
        self.group_id_overlap: List[str] = []
        self.image_hash_overlap: List[str] = []
        self.details: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "doc_id_overlap": self.doc_id_overlap,
            "group_id_overlap": self.group_id_overlap,
            "image_hash_overlap": self.image_hash_overlap,
            "details": self.details
        }


class DataLeakageDetector:
    def __init__(self, loader: EvaluationDatasetLoader):
        self.loader = loader

    def audit_splits(self) -> LeakageAuditReport:
        report = LeakageAuditReport()
        
        splits = ["train", "val", "test"]
        doc_sets: Dict[str, Set[str]] = {}
        group_sets: Dict[str, Set[str]] = {}
        hash_sets: Dict[str, Set[str]] = {}

        for sp in splits:
            samples = self.loader.get_split_samples(sp)
            doc_sets[sp] = {s.document_id for s in samples}
            group_sets[sp] = {s.patient_group_id for s in samples if s.patient_group_id}
            hash_sets[sp] = {s.image_sha256 for s in samples if s.image_sha256}

        # 1. Document ID overlap
        for i in range(len(splits)):
            for j in range(i + 1, len(splits)):
                s1, s2 = splits[i], splits[j]
                overlap = doc_sets[s1].intersection(doc_sets[s2])
                if overlap:
                    report.passed = False
                    report.doc_id_overlap.extend([f"{doc}:{s1}<->{s2}" for doc in overlap])

        # 2. Patient Group ID overlap
        for i in range(len(splits)):
            for j in range(i + 1, len(splits)):
                s1, s2 = splits[i], splits[j]
                overlap = group_sets[s1].intersection(group_sets[s2])
                if overlap:
                    report.passed = False
                    report.group_id_overlap.extend([f"{grp}:{s1}<->{s2}" for grp in overlap])

        # 3. Image SHA-256 hash overlap
        for i in range(len(splits)):
            for j in range(i + 1, len(splits)):
                s1, s2 = splits[i], splits[j]
                overlap = hash_sets[s1].intersection(hash_sets[s2])
                if overlap:
                    report.passed = False
                    report.image_hash_overlap.extend([f"{h[:10]}:{s1}<->{s2}" for h in overlap])

        report.details = {
            "train_docs": list(doc_sets["train"]),
            "val_docs": list(doc_sets["val"]),
            "test_docs": list(doc_sets["test"]),
            "train_groups": list(group_sets["train"]),
            "val_groups": list(group_sets["val"]),
            "test_groups": list(group_sets["test"]),
        }
        return report
