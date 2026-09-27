"""
Phase 4 Safety Tests: Original Image Immutability & Traceability
Verifies the statutory invariant: original_image != preprocessed_image.
Proves that original file bytes, storage locations, and SHA-256 cryptographic hashes
are permanently preserved and NEVER overwritten by preprocessing.
"""

import hashlib
import io
import shutil
import tempfile
from pathlib import Path
import pytest
from PIL import Image, ImageDraw

from backend.app.preprocessing.artifacts import PreprocessingArtifactManager
from backend.app.preprocessing.config import PreprocessingConfig
from backend.app.preprocessing.pipeline import PrescriptionPreprocessingPipeline
from backend.app.preprocessing.service import ImagePreprocessingService


def _create_sample_rx_file(target_path: Path) -> str:
    """Creates a sample physical prescription file and returns its SHA-256 hash."""
    im = Image.new("RGB", (400, 500), color=(250, 250, 250))
    draw = ImageDraw.Draw(im)
    draw.text((20, 20), "Rx Original Pad Evidence", fill=(10, 10, 10))
    draw.line([(20, 45), (380, 45)], fill=(50, 50, 50), width=2)
    draw.text((20, 75), "Amoxicillin 500mg 1 cap TDS", fill=(20, 20, 100))
    im.save(target_path, format="PNG")
    with open(target_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class TestImmutabilityAndSafety:

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aura_immutability_test_"))
        self.runs_dir = self.temp_dir / "runs"
        self.public_dir = self.temp_dir / "public_preprocessed"
        self.service = ImagePreprocessingService(
            base_runs_dir=self.runs_dir,
            public_preprocessed_dir=self.public_dir,
        )

    def teardown_method(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_original_image_bytes_and_hash_remain_immutable(self):
        """Verifies that original physical image file bytes and hash are 100% unchanged after preprocessing."""
        rx_file = self.temp_dir / "original_rx_pad.png"
        original_hash = _create_sample_rx_file(rx_file)
        original_bytes = rx_file.read_bytes()

        # Run preprocessing and persistence
        res, manifest, pub_url = self.service.process_and_store(
            image_bytes=original_bytes,
            filename=rx_file.name,
            prescription_id="RX-IMMUTABLE-01",
            original_image_path=rx_file,
            reject_insufficient_quality=False,
        )

        # 1. Verify original file on disk is bit-for-bit identical
        assert rx_file.exists(), "Original prescription file was deleted or moved!"
        post_process_bytes = rx_file.read_bytes()
        post_process_hash = hashlib.sha256(post_process_bytes).hexdigest()

        assert post_process_hash == original_hash, "Original file hash changed during preprocessing!"
        assert post_process_bytes == original_bytes, "Original file bytes were mutated!"

        # 2. Verify preprocessed image is a separate derived artifact
        primary_artifact = self.runs_dir / "RX-IMMUTABLE-01" / f"{manifest.primary_artifact_type}.png"
        assert primary_artifact.exists()
        assert primary_artifact.resolve() != rx_file.resolve()

        # 3. Verify original_image != preprocessed_image
        with open(primary_artifact, "rb") as f:
            derived_bytes = f.read()
        assert derived_bytes != original_bytes, "Preprocessed image must be a derived representation, not identical copy!"

    def test_manifest_cryptographic_checksums_match_disk_files(self):
        """Verifies that every artifact listed in manifest.json exactly matches the SHA-256 of the file on disk."""
        rx_file = self.temp_dir / "rx_checksum_test.png"
        original_hash = _create_sample_rx_file(rx_file)
        original_bytes = rx_file.read_bytes()

        _, manifest, _ = self.service.process_and_store(
            image_bytes=original_bytes,
            filename=rx_file.name,
            prescription_id="RX-CHECKSUM-01",
            original_image_path=rx_file,
        )

        assert manifest.source_image_sha256 == original_hash

        for artifact in manifest.artifacts:
            disk_path = Path(artifact.relative_path)
            assert disk_path.exists(), f"Artifact {artifact.type} not found at {disk_path}"
            with open(disk_path, "rb") as f:
                disk_sha256 = hashlib.sha256(f.read()).hexdigest()
            assert disk_sha256 == artifact.sha256, f"Artifact {artifact.type} hash mismatch on disk!"

    def test_source_dataset_calibration_samples_never_mutated(self):
        """Verifies that data/samples/ files remain pristine and un-modified by any preprocessing pipeline run."""
        sample_path = Path("data/samples/sample_01_clear.png")
        if not sample_path.exists():
            pytest.skip("data/samples/sample_01_clear.png not found")

        initial_bytes = sample_path.read_bytes()
        initial_hash = hashlib.sha256(initial_bytes).hexdigest()

        # Run pipeline over the sample
        self.service.process_and_store(
            image_bytes=initial_bytes,
            filename=sample_path.name,
            prescription_id="SAMPLE-TEST-AUDIT",
            original_image_path=sample_path,
        )

        # Re-check sample file on disk
        after_bytes = sample_path.read_bytes()
        after_hash = hashlib.sha256(after_bytes).hexdigest()

        assert after_hash == initial_hash
        assert after_bytes == initial_bytes
