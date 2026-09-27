"""
Reproducible Group-Aware Dataset Splitting and Leakage Prevention (Phase 3)
Guarantees patient-level and source-level isolation across train/validation/test partitions.
"""

import json
import random
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Set, Tuple, Optional, Any
from pydantic import BaseModel, Field, model_validator

from .schema import PrescriptionDocumentRecord


class DatasetSplitResult(BaseModel):
    """Container for reproducible dataset partition splits."""
    split_version: str = Field(default="1.0.0", description="Semantic version of split protocol")
    seed: int = Field(default=42, description="Random seed used for deterministic partition assignment")
    ratios: Dict[str, float] = Field(
        default_factory=lambda: {"train": 0.70, "val": 0.15, "test": 0.15},
        description="Target partition proportions"
    )
    train_ids: List[str] = Field(default_factory=list, description="Document IDs allocated to train partition")
    val_ids: List[str] = Field(default_factory=list, description="Document IDs allocated to validation partition")
    test_ids: List[str] = Field(default_factory=list, description="Document IDs allocated to test partition")
    total_count: int = Field(default=0, description="Total number of partitioned documents")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Generation timestamp"
    )
    checksum: Optional[str] = Field(None, description="Cryptographic SHA-256 fingerprint of the split assignment")

    @model_validator(mode="after")
    def compute_checksum_and_validate(self) -> "DatasetSplitResult":
        # Check for disjoint partitions
        s_train = set(self.train_ids)
        s_val = set(self.val_ids)
        s_test = set(self.test_ids)

        overlap_tv = s_train.intersection(s_val)
        overlap_tt = s_train.intersection(s_test)
        overlap_vt = s_val.intersection(s_test)

        if overlap_tv or overlap_tt or overlap_vt:
            raise ValueError(
                f"Split contains overlapping document IDs: "
                f"train-val={overlap_tv}, train-test={overlap_tt}, val-test={overlap_vt}"
            )

        self.total_count = len(self.train_ids) + len(self.val_ids) + len(self.test_ids)
        
        # Calculate fingerprint
        payload = json.dumps(
            {
                "split_version": self.split_version,
                "seed": self.seed,
                "train_ids": sorted(self.train_ids),
                "val_ids": sorted(self.val_ids),
                "test_ids": sorted(self.test_ids),
            },
            sort_keys=True
        )
        self.checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return self


def detect_split_leakage(
    split: DatasetSplitResult,
    records: List[PrescriptionDocumentRecord]
) -> Dict[str, Any]:
    """
    Performs rigorous static audit for data leakage across train, val, and test partitions:
    1. Group-level leakage (verifies no patient_group_id is distributed across partitions)
    2. Image hash leakage (verifies no identical image SHA-256 hash appears across partitions)
    """
    record_map: Dict[str, PrescriptionDocumentRecord] = {r.document_id: r for r in records}

    # Map partition -> set of group IDs and set of image hashes
    partition_groups: Dict[str, Set[str]] = {"train": set(), "val": set(), "test": set()}
    partition_hashes: Dict[str, Set[str]] = {"train": set(), "val": set(), "test": set()}

    for split_name, id_list in [
        ("train", split.train_ids),
        ("val", split.val_ids),
        ("test", split.test_ids),
    ]:
        for doc_id in id_list:
            if doc_id in record_map:
                rec = record_map[doc_id]
                partition_groups[split_name].add(rec.patient_group_id)
                partition_hashes[split_name].add(rec.ground_truth.image_sha256)

    # Calculate intersections
    leaked_groups = {
        "train_val": list(partition_groups["train"].intersection(partition_groups["val"])),
        "train_test": list(partition_groups["train"].intersection(partition_groups["test"])),
        "val_test": list(partition_groups["val"].intersection(partition_groups["test"])),
    }

    leaked_hashes = {
        "train_val": list(partition_hashes["train"].intersection(partition_hashes["val"])),
        "train_test": list(partition_hashes["train"].intersection(partition_hashes["test"])),
        "val_test": list(partition_hashes["val"].intersection(partition_hashes["test"])),
    }

    has_group_leakage = any(len(v) > 0 for v in leaked_groups.values())
    has_hash_leakage = any(len(v) > 0 for v in leaked_hashes.values())
    is_leak_free = (not has_group_leakage) and (not has_hash_leakage)

    return {
        "is_leak_free": is_leak_free,
        "has_group_leakage": has_group_leakage,
        "has_hash_leakage": has_hash_leakage,
        "leaked_groups": leaked_groups,
        "leaked_hashes": leaked_hashes,
        "partition_sizes": {
            "train": len(split.train_ids),
            "val": len(split.val_ids),
            "test": len(split.test_ids),
        },
    }


class GroupAwareSplitter:
    """
    Deterministic group-aware dataset partitioner.
    Clusters documents by patient_group_id and assigns entire clusters to partitions,
    ensuring zero leakage between training, validation, and test datasets.
    """

    def __init__(
        self,
        seed: int = 42,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ):
        if not (0.99 <= train_ratio + val_ratio + test_ratio <= 1.01):
            raise ValueError(f"Partition ratios must sum to 1.0, got {train_ratio + val_ratio + test_ratio}")
        self.seed = seed
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

    def split(self, records: List[PrescriptionDocumentRecord]) -> DatasetSplitResult:
        """Splits records into deterministic train/val/test partitions by group."""
        if not records:
            return DatasetSplitResult(
                seed=self.seed,
                ratios={"train": self.train_ratio, "val": self.val_ratio, "test": self.test_ratio},
            )

        # 1. Group document IDs by patient_group_id
        groups: Dict[str, List[str]] = {}
        for r in records:
            groups.setdefault(r.patient_group_id, []).append(r.document_id)

        # 2. Sort groups canonically before shuffling to guarantee cross-platform determinism
        sorted_group_keys = sorted(groups.keys())
        rng = random.Random(self.seed)
        rng.shuffle(sorted_group_keys)

        total_docs = len(records)
        target_train_count = int(total_docs * self.train_ratio)
        target_val_count = int(total_docs * self.val_ratio)

        train_groups: List[str] = []
        val_groups: List[str] = []
        test_groups: List[str] = []

        current_train_count = 0
        current_val_count = 0

        # If there are at least 3 groups, guarantee that val and test each receive at least one group
        if len(sorted_group_keys) >= 3:
            alloc_keys = sorted_group_keys[:-2]
            for group_id in alloc_keys:
                cnt = len(groups[group_id])
                if current_train_count + cnt <= target_train_count or not train_groups:
                    train_groups.append(group_id)
                    current_train_count += cnt
                elif current_val_count + cnt <= target_val_count or not val_groups:
                    val_groups.append(group_id)
                    current_val_count += cnt
                else:
                    test_groups.append(group_id)
            val_groups.append(sorted_group_keys[-2])
            test_groups.append(sorted_group_keys[-1])
        else:
            for idx, group_id in enumerate(sorted_group_keys):
                if idx == 0:
                    train_groups.append(group_id)
                elif idx == 1:
                    val_groups.append(group_id)
                else:
                    test_groups.append(group_id)

        train_ids: List[str] = []
        val_ids: List[str] = []
        test_ids: List[str] = []

        for g in train_groups:
            train_ids.extend(groups[g])
        for g in val_groups:
            val_ids.extend(groups[g])
        for g in test_groups:
            test_ids.extend(groups[g])

        return DatasetSplitResult(
            seed=self.seed,
            ratios={"train": self.train_ratio, "val": self.val_ratio, "test": self.test_ratio},
            train_ids=sorted(train_ids),
            val_ids=sorted(val_ids),
            test_ids=sorted(test_ids),
        )
