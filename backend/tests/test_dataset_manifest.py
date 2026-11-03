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
    assert len(reloaded.files) == len(manifest.files)


def test_manifest_files_exist_and_match_magic_bytes():
    """
    Verifies that every file in dataset_manifest.json exists on disk,
    and its initial magic bytes match its declared extension and MIME type.
    """
    import hashlib
    from backend.app.dataset.manifest import MAGIC_BYTES_BY_EXTENSION, MIME_TYPE_BY_EXTENSION

    manifest_path = Path("data/manifests/dataset_manifest.json")
    manifest = load_manifest(manifest_path)

    assert len(manifest.files) >= 15, "Manifest must inventory verified sample files"

    for file_entry in manifest.files:
        p = Path(file_entry.file_path)
        assert p.exists(), f"File declared in manifest does not exist: {file_entry.file_path}"
        assert p.is_file(), f"Path is not a regular file: {file_entry.file_path}"

        ext = p.suffix.lower()
        assert ext in MAGIC_BYTES_BY_EXTENSION, f"Unsupported file extension {ext} for {file_entry.file_path}"
        expected_mime = MIME_TYPE_BY_EXTENSION[ext]
        assert file_entry.mime_type == expected_mime, (
            f"MIME type mismatch for {file_entry.file_path}: "
            f"expected {expected_mime}, got {file_entry.mime_type}"
        )

        content = p.read_bytes()
        expected_magic = MAGIC_BYTES_BY_EXTENSION[ext]
        assert content.startswith(expected_magic), (
            f"Magic byte mismatch for {file_entry.file_path} ({ext}): "
            f"file header {content[:8].hex()} does not match expected {expected_magic.hex()}"
        )
        assert len(content) == file_entry.size_bytes, f"Size mismatch for {file_entry.file_path}"


def test_manifest_files_have_unique_sha256_hashes():
    """
    Verifies that every file in dataset_manifest.json has a unique SHA-256 hash
    and matches its actual on-disk cryptographic digest.
    """
    import hashlib

    manifest_path = Path("data/manifests/dataset_manifest.json")
    manifest = load_manifest(manifest_path)

    seen_hashes = {}
    for file_entry in manifest.files:
        p = Path(file_entry.file_path)
        actual_sha = hashlib.sha256(p.read_bytes()).hexdigest()

        assert actual_sha == file_entry.sha256, (
            f"SHA-256 mismatch for {file_entry.file_path}: "
            f"manifest says {file_entry.sha256}, on disk is {actual_sha}"
        )

        assert actual_sha not in seen_hashes, (
            f"Duplicate SHA-256 detected: {actual_sha} shared by "
            f"'{file_entry.file_path}' and '{seen_hashes[actual_sha]}'"
        )
        seen_hashes[actual_sha] = file_entry.file_path


def test_clear_prescription_sample_deduplicated_in_manifest():
    """
    Verifies that clear-prescription-sample.png is inventoried and
    clear-prescription-sample.jpg is excluded to avoid duplicated image payloads.
    """
    manifest_path = Path("data/manifests/dataset_manifest.json")
    manifest = load_manifest(manifest_path)

    paths = [f.file_path.replace("\\", "/") for f in manifest.files]
    assert "data/samples/clear-prescription-sample.png" in paths
    assert "data/samples/clear-prescription-sample.jpg" not in paths


def test_cardiology_and_clinic_pad_format_and_hash_distinction():
    """
    Verifies that cardiology-clinic-slip and handwritten-clinic-pad png vs jpg
    entries have distinct magic bytes and non-identical SHA-256 hashes.
    """
    import hashlib

    manifest_path = Path("data/manifests/dataset_manifest.json")
    manifest = load_manifest(manifest_path)

    cardio_png = manifest.get_file_by_path("data/samples/cardiology-clinic-slip.png")
    cardio_jpg = manifest.get_file_by_path("data/samples/cardiology-clinic-slip.jpg")
    assert cardio_png is not None and cardio_jpg is not None
    assert cardio_png.sha256 != cardio_jpg.sha256, "Cardiology slip PNG and JPG must not have identical hashes"
    assert cardio_png.mime_type == "image/png"
    assert cardio_jpg.mime_type == "image/jpeg"

    pad_png = manifest.get_file_by_path("data/samples/handwritten-clinic-pad.png")
    pad_jpg = manifest.get_file_by_path("data/samples/handwritten-clinic-pad.jpg")
    assert pad_png is not None and pad_jpg is not None
    assert pad_png.sha256 != pad_jpg.sha256, "Clinic pad PNG and JPG must not have identical hashes"
    assert pad_png.mime_type == "image/png"
    assert pad_jpg.mime_type == "image/jpeg"
