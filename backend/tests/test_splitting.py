"""
Unit Tests for Reproducible Group-Aware Splitting and Leakage Detection (Phase 3)
"""

import json
from pathlib import Path
import pytest

from backend.app.dataset.schema import (
    PrescriptionDocumentRecord,
    GroundTruthAnnotation,
    AnnotationTier
)
from backend.app.dataset.splitter import (
    GroupAwareSplitter,
    DatasetSplitResult,
    detect_split_leakage
)


@pytest.fixture
def dummy_grouped_records():
    """Generates dummy records with explicit multi-document patient groups."""
    records = []
    # Patient 1 has 3 documents (e.g. multiple pages of one prescription)
    for i in range(1, 4):
        records.append(PrescriptionDocumentRecord(
            document_id=f"DOC-P1-{i}",
            patient_group_id="GROUP-PATIENT-1",
            ground_truth=GroundTruthAnnotation(
                tier=AnnotationTier.GROUND_TRUTH,
                document_id=f"DOC-P1-{i}",
                image_rel_path="samples/test.png",
                image_sha256="1" * 64,
                patient_deidentified=True,
                source_dataset_id="test-source",
                medications=[]
            )
        ))
    # Patient 2 has 2 documents
    for i in range(1, 3):
        records.append(PrescriptionDocumentRecord(
            document_id=f"DOC-P2-{i}",
            patient_group_id="GROUP-PATIENT-2",
            ground_truth=GroundTruthAnnotation(
                tier=AnnotationTier.GROUND_TRUTH,
                document_id=f"DOC-P2-{i}",
                image_rel_path="samples/test.png",
                image_sha256="2" * 64,
                patient_deidentified=True,
                source_dataset_id="test-source",
                medications=[]
            )
        ))
    # Patient 3 has 2 documents
    for i in range(1, 3):
        records.append(PrescriptionDocumentRecord(
            document_id=f"DOC-P3-{i}",
            patient_group_id="GROUP-PATIENT-3",
            ground_truth=GroundTruthAnnotation(
                tier=AnnotationTier.GROUND_TRUTH,
                document_id=f"DOC-P3-{i}",
                image_rel_path="samples/test.png",
                image_sha256="3" * 64,
                patient_deidentified=True,
                source_dataset_id="test-source",
                medications=[]
            )
        ))
    # Patient 4 has 1 document
    records.append(PrescriptionDocumentRecord(
        document_id="DOC-P4-1",
        patient_group_id="GROUP-PATIENT-4",
        ground_truth=GroundTruthAnnotation(
            tier=AnnotationTier.GROUND_TRUTH,
            document_id="DOC-P4-1",
            image_rel_path="samples/test.png",
            image_sha256="4" * 64,
            patient_deidentified=True,
            source_dataset_id="test-source",
            medications=[]
        )
    ))
    return records


def test_splitter_reproducibility(dummy_grouped_records):
    """Verifies that running splitter twice with seed=42 yields identical partitions and checksums."""
    splitter_a = GroupAwareSplitter(seed=42)
    split_a = splitter_a.split(dummy_grouped_records)

    splitter_b = GroupAwareSplitter(seed=42)
    split_b = splitter_b.split(dummy_grouped_records)

    assert split_a.train_ids == split_b.train_ids
    assert split_a.val_ids == split_b.val_ids
    assert split_a.test_ids == split_b.test_ids
    assert split_a.checksum == split_b.checksum


def test_group_aware_isolation_prevents_patient_leakage(dummy_grouped_records):
    """Verifies that all documents for a given patient group are confined to a single partition."""
    splitter = GroupAwareSplitter(seed=42)
    split = splitter.split(dummy_grouped_records)

    audit = detect_split_leakage(split, dummy_grouped_records)
    assert audit["is_leak_free"] is True
    assert audit["has_group_leakage"] is False
    assert audit["has_hash_leakage"] is False

    # Check Patient 1's documents (DOC-P1-1, DOC-P1-2, DOC-P1-3)
    p1_docs = {"DOC-P1-1", "DOC-P1-2", "DOC-P1-3"}
    # Must all be in train, all in val, or all in test
    in_train = p1_docs.issubset(set(split.train_ids))
    in_val = p1_docs.issubset(set(split.val_ids))
    in_test = p1_docs.issubset(set(split.test_ids))
    assert in_train or in_val or in_test, "Patient 1 documents were fragmented across partitions!"


def test_leakage_detector_catches_deliberate_group_leakage(dummy_grouped_records):
    """Verifies that artificially distributing documents from GROUP-PATIENT-1 across train and test triggers an alarm."""
    leaked_split = DatasetSplitResult(
        seed=42,
        train_ids=["DOC-P1-1", "DOC-P1-2"],
        val_ids=["DOC-P2-1"],
        test_ids=["DOC-P1-3", "DOC-P3-1"]  # DOC-P1-3 is in test while DOC-P1-1/2 are in train!
    )
    audit = detect_split_leakage(leaked_split, dummy_grouped_records)
    assert audit["is_leak_free"] is False
    assert audit["has_group_leakage"] is True
    assert "GROUP-PATIENT-1" in audit["leaked_groups"]["train_test"]


def test_canonical_sample_splits_file_is_leak_free():
    """Verifies that the committed sample_splits.json is 100% leak-free against sample_annotations.json."""
    splits_p = Path("data/splits/sample_splits.json")
    ann_p = Path("data/annotations/sample_annotations.json")
    assert splits_p.exists()
    assert ann_p.exists()

    with open(splits_p, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    split = DatasetSplitResult.model_validate(split_data)

    with open(ann_p, "r", encoding="utf-8") as f:
        raw_recs = json.load(f)
    records = [PrescriptionDocumentRecord.model_validate(r) for r in raw_recs]

    audit = detect_split_leakage(split, records)
    assert audit["is_leak_free"] is True
    assert audit["has_group_leakage"] is False
    assert audit["has_hash_leakage"] is False
