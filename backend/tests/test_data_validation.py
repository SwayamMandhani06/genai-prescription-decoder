"""
Unit and Integration Tests for Dataset Validation Suite (Phase 3)
"""

import json
from pathlib import Path
from PIL import Image
import pytest

from backend.app.dataset.schema import (
    PrescriptionDocumentRecord,
    GroundTruthAnnotation,
    AnnotationTier
)
from backend.app.dataset.validator import (
    DatasetValidator,
    IssueSeverity,
    ValidationReport
)


def test_validator_detects_missing_image_file(tmp_path: Path):
    """Verifies that non-existent image paths produce FILE_NOT_FOUND error."""
    missing_path = tmp_path / "non_existent.png"
    heuristics, issues = DatasetValidator.validate_image_file(missing_path)
    assert heuristics is None
    assert any(i.code == "FILE_NOT_FOUND" and i.severity == IssueSeverity.ERROR for i in issues)


def test_validator_detects_corrupted_image(tmp_path: Path):
    """Verifies that corrupted image files produce CORRUPTED_IMAGE error."""
    corrupted_path = tmp_path / "corrupted.png"
    # Write garbage bytes with PNG extension
    with open(corrupted_path, "wb") as f:
        f.write(b"not a valid png header at all")

    heuristics, issues = DatasetValidator.validate_image_file(corrupted_path)
    assert heuristics is not None
    assert heuristics.is_corrupted is True
    assert any(i.code == "CORRUPTED_IMAGE" and i.severity == IssueSeverity.ERROR for i in issues)


def test_validator_detects_checksum_mismatch(tmp_path: Path):
    """Verifies that mismatched image_sha256 in ground truth triggers IMAGE_CHECKSUM_MISMATCH."""
    # Create valid 1x1 image
    img_path = tmp_path / "valid.png"
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    img.save(img_path)

    rec = PrescriptionDocumentRecord(
        document_id="DOC-TEST-MISMATCH",
        patient_group_id="GRP-1",
        ground_truth=GroundTruthAnnotation(
            tier=AnnotationTier.GROUND_TRUTH,
            document_id="DOC-TEST-MISMATCH",
            image_rel_path="valid.png",
            image_sha256="0" * 64,  # Intentionally fake SHA-256
            patient_deidentified=True,
            source_dataset_id="test",
            medications=[]
        )
    )

    report = DatasetValidator.audit_collection([rec], base_data_dir=tmp_path)
    assert report.is_valid is False
    assert any(i.code == "IMAGE_CHECKSUM_MISMATCH" for i in report.issues)


def test_validator_detects_duplicate_image_hashes(tmp_path: Path):
    """Verifies that duplicate image hashes across distinct documents are flagged."""
    img_path = tmp_path / "shared.png"
    img = Image.new("RGB", (200, 200), color=(200, 200, 200))
    img.save(img_path)

    heuristics, _ = DatasetValidator.validate_image_file(img_path)
    true_hash = heuristics.sha256

    rec1 = PrescriptionDocumentRecord(
        document_id="DOC-DUP-1",
        patient_group_id="GRP-1",
        ground_truth=GroundTruthAnnotation(
            tier=AnnotationTier.GROUND_TRUTH,
            document_id="DOC-DUP-1",
            image_rel_path="shared.png",
            image_sha256=true_hash,
            patient_deidentified=True,
            source_dataset_id="test",
            medications=[]
        )
    )
    rec2 = PrescriptionDocumentRecord(
        document_id="DOC-DUP-2",
        patient_group_id="GRP-2",
        ground_truth=GroundTruthAnnotation(
            tier=AnnotationTier.GROUND_TRUTH,
            document_id="DOC-DUP-2",
            image_rel_path="shared.png",
            image_sha256=true_hash,
            patient_deidentified=True,
            source_dataset_id="test",
            medications=[]
        )
    )

    report = DatasetValidator.audit_collection([rec1, rec2], base_data_dir=tmp_path)
    assert true_hash in report.duplicate_image_hashes
    assert len(report.duplicate_image_hashes[true_hash]) == 2
    assert any(i.code == "DUPLICATE_IMAGE_HASH" for i in report.issues)


def test_canonical_dataset_passes_full_audit():
    """Verifies that the canonical dataset in data/ passes the complete validation audit."""
    base_data_dir = Path("data")
    ann_path = base_data_dir / "annotations" / "sample_annotations.json"
    splits_path = base_data_dir / "splits" / "sample_splits.json"

    with open(ann_path, "r", encoding="utf-8") as f:
        raw_recs = json.load(f)
    records = [PrescriptionDocumentRecord.model_validate(r) for r in raw_recs]

    from backend.app.dataset.splitter import DatasetSplitResult
    with open(splits_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    split = DatasetSplitResult.model_validate(split_data)

    report = DatasetValidator.audit_collection(records, base_data_dir, split=split)
    assert report.is_valid is True
    assert report.error_count == 0
    assert report.valid_records_count == 7
    assert len(report.image_heuristics) == 7
    for doc_id, heur in report.image_heuristics.items():
        assert heur.is_corrupted is False
        assert heur.width >= 150
        assert heur.height >= 150
