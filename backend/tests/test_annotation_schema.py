"""
Unit Tests for Annotation Schemas, Tier Boundaries, and Ground Truth Integrity (Phase 3)
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.app.dataset.schema import (
    GroundTruthAnnotation,
    MedicationEntityAnnotation,
    DerivedAnnotation,
    AnnotationTier,
    AmbiguityLevel,
    BoundingBox,
    PrescriptionDocumentRecord
)


def test_annotation_tiers_are_strictly_enforced():
    """Verifies that GroundTruthAnnotation strictly requires tier='ground_truth'."""
    gt = GroundTruthAnnotation(
        document_id="TEST-001",
        image_rel_path="samples/test.png",
        image_sha256="a" * 64,
        patient_deidentified=True,
        source_dataset_id="test-source",
        medications=[]
    )
    assert gt.tier == AnnotationTier.GROUND_TRUTH

    # Attempting to assign model_prediction to a GroundTruthAnnotation must fail
    with pytest.raises(ValidationError):
        GroundTruthAnnotation(
            tier=AnnotationTier.MODEL_PREDICTION,  # Invalid for ground truth
            document_id="TEST-002",
            image_rel_path="samples/test.png",
            image_sha256="a" * 64,
            patient_deidentified=True,
            source_dataset_id="test-source",
            medications=[]
        )


def test_privacy_enforcement_rejects_unverified_pii():
    """Verifies that patient_deidentified=False triggers validation error."""
    with pytest.raises(ValidationError) as exc_info:
        GroundTruthAnnotation(
            document_id="TEST-003",
            image_rel_path="samples/test.png",
            image_sha256="a" * 64,
            patient_deidentified=False,  # Uncertified PII risk
            source_dataset_id="test-source",
            medications=[]
        )
    assert "patient_deidentified" in str(exc_info.value)


def test_bounding_box_boundary_validation():
    """Verifies that bounding boxes outside [0.0 - 1.0] are rejected."""
    # Valid box
    box = BoundingBox(x=0.1, y=0.2, width=0.5, height=0.3)
    assert box.x == 0.1

    # Overflows right edge (x + width > 1.0)
    with pytest.raises(ValidationError):
        BoundingBox(x=0.7, y=0.2, width=0.4, height=0.2)

    # Negative coordinates
    with pytest.raises(ValidationError):
        BoundingBox(x=-0.1, y=0.2, width=0.5, height=0.2)


def test_sample_annotations_file_conforms_to_schema():
    """Verifies that all records in sample_annotations.json load cleanly and validate."""
    ann_path = Path("data/annotations/sample_annotations.json")
    assert ann_path.exists()

    with open(ann_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 7, "Must contain exactly 7 curated evaluation sample records"

    for raw_rec in data:
        rec = PrescriptionDocumentRecord.model_validate(raw_rec)
        assert rec.document_id.startswith("DOC-RX-")
        assert rec.patient_group_id.startswith("PATIENT-GRP-")
        assert rec.ground_truth.patient_deidentified is True
        assert len(rec.ground_truth.image_sha256) == 64
        assert len(rec.ground_truth.medications) >= 1
        for med in rec.ground_truth.medications:
            assert med.item_index >= 1
            assert len(med.raw_text) > 0
            assert med.ambiguity_level in [
                AmbiguityLevel.NONE,
                AmbiguityLevel.MINOR,
                AmbiguityLevel.SEVERE_ILLEGIBLE
            ]
