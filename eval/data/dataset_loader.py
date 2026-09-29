"""
Evaluation Dataset Loader (Section 6 & 7).
Provides structured access to evaluation datasets, ground-truth annotations, and splits.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class EvaluationSample:
    def __init__(self, raw_record: Dict[str, Any], root_dir: Path):
        self.document_id: str = raw_record.get("document_id", "")
        self.patient_group_id: str = raw_record.get("patient_group_id", "")
        self.ground_truth: Dict[str, Any] = raw_record.get("ground_truth", {})
        self.derived_annotations: List[Dict[str, Any]] = raw_record.get("derived_annotations", [])
        self.metadata: Dict[str, Any] = raw_record.get("metadata", {})
        
        self.image_rel_path: str = self.ground_truth.get("image_rel_path", "")
        self.image_path: Path = root_dir / "data" / self.image_rel_path if self.image_rel_path else Path("")
        self.image_sha256: str = self.ground_truth.get("image_sha256", "")
        
        self.medications: List[Dict[str, Any]] = self.ground_truth.get("medications", [])
        self.field_count: int = len(self.medications) * 4  # med_name, dosage, freq, duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "patient_group_id": self.patient_group_id,
            "image_rel_path": self.image_rel_path,
            "image_sha256": self.image_sha256,
            "medication_count": len(self.medications),
            "medications": self.medications,
            "metadata": self.metadata
        }


class EvaluationDatasetLoader:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = root_dir
            
        self.annotations_path = self.root_dir / "data" / "annotations" / "sample_annotations.json"
        self.splits_path = self.root_dir / "data" / "splits" / "sample_splits.json"
        
        self._samples: Dict[str, EvaluationSample] = {}
        self._splits: Dict[str, List[str]] = {}
        self._load_data()

    def _load_data(self) -> None:
        if self.annotations_path.exists():
            with open(self.annotations_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    sample = EvaluationSample(item, self.root_dir)
                    self._samples[sample.document_id] = sample

        if self.splits_path.exists():
            with open(self.splits_path, "r", encoding="utf-8") as f:
                splits_data = json.load(f)
                self._splits = {
                    "train": splits_data.get("train_ids", []),
                    "val": splits_data.get("val_ids", []),
                    "test": splits_data.get("test_ids", [])
                }

    def get_all_samples(self) -> List[EvaluationSample]:
        return list(self._samples.values())

    def get_sample(self, document_id: str) -> Optional[EvaluationSample]:
        return self._samples.get(document_id)

    def get_split_samples(self, split: str) -> List[EvaluationSample]:
        doc_ids = self._splits.get(split, [])
        return [self._samples[doc_id] for doc_id in doc_ids if doc_id in self._samples]

    def get_split_counts(self) -> Dict[str, int]:
        return {
            "total_documents": len(self._samples),
            "total_medications": sum(len(s.medications) for s in self._samples.values()),
            "total_fields": sum(s.field_count for s in self._samples.values()),
            "train_documents": len(self.get_split_samples("train")),
            "val_documents": len(self.get_split_samples("val")),
            "test_documents": len(self.get_split_samples("test"))
        }
