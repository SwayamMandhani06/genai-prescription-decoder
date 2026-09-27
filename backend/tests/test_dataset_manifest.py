"""
Unit and Integration Tests for Dataset Manifest, Licensing, and Provenance (Phase 3)
"""

import json
from pathlib import Path
import pytest
from backend.app.dataset.manifest import (
    DatasetManifest,
    DatasetSourceEntry,
    ProvenanceRecord,
    SourceVerificationStatus,
    load_manifest,
    save_manifest
)


def test_manifest_schema_and_integrity():
    """Verifies that the canonical dataset_manifest.json conforms strictly to the Pydantic schema."""
    manifest_path = Path("data/manifests/dataset_manifest.json")
    assert manifest_path.exists(), "Manifest file data/manifests/dataset_manifest.json must exist"

    manifest = load_manifest(manifest_path)
    assert manifest.manifest_version == "1.0.0"
    assert len(manifest.sources) >= 5, "Manifest must inventory at least 5 distinct sources"
    assert manifest.local_sample_count == 7, "Manifest must accurately state 7 local evaluation samples"
    assert manifest.checksum is not None, "Manifest must compute and store a valid checksum"
    assert manifest.compute_hash() == manifest.checksum, "Manifest checksum must match re-computed hash"


def test_all_sources_have_provenance_and_licensing():
    """Verifies that every inventoried dataset has verified provenance, citation, and license."""
    manifest_path = Path("data/manifests/dataset_manifest.json")
    manifest = load_manifest(manifest_path)

    for source in manifest.sources:
        assert len(source.dataset_id) >= 3
        assert len(source.name) >= 3
        assert source.description
        assert source.relevance
        assert source.verification_status in [
            SourceVerificationStatus.VERIFIED_PUBLIC,
            SourceVerificationStatus.VERIFIED_REGULATORY,
            SourceVerificationStatus.CANDIDATE_UNVERIFIED
        ]
        # Provenance verification
        prov = source.provenance
        assert prov.source_url.startswith("http") or prov.source_url.startswith("local://")
        assert len(prov.provider_organization) > 3
        assert len(prov.license) > 2
        assert prov.license_category is not None
        assert len(prov.permitted_usage) > 5
        assert len(prov.attribution_requirements) > 3
        assert len(prov.citation) > 5


def test_unverified_sources_are_explicitly_flagged():
    """Verifies that candidate sources without verified provenance are explicitly marked candidate_unverified."""
    manifest_path = Path("data/manifests/dataset_manifest.json")
    manifest = load_manifest(manifest_path)

    unverified = [s for s in manifest.sources if s.verification_status == SourceVerificationStatus.CANDIDATE_UNVERIFIED]
    assert len(unverified) >= 1, "Must contain at least 1 explicitly flagged unverified candidate"
    for s in unverified:
        assert "unverified" in s.provenance.license.lower() or "pending" in s.provenance.license.lower()


def test_manifest_serialization_and_hash_stability(tmp_path: Path):
    """Verifies that saving and reloading a manifest maintains exact checksum stability."""
    manifest_path = Path("data/manifests/dataset_manifest.json")
    manifest = load_manifest(manifest_path)

    temp_file = tmp_path / "manifest_test.json"
    save_manifest(manifest, temp_file)

    reloaded = load_manifest(temp_file)
    assert reloaded.checksum == manifest.checksum
    assert len(reloaded.sources) == len(manifest.sources)
