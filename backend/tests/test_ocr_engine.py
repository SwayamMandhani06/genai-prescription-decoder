"""
Phase 5 Test Suite: OCR Engine Adapter
Tests Tesseract binary discovery, runtime version query, language inventory,
deterministic configuration hashing, and failure path handling.
"""

import pytest
from PIL import Image

from backend.app.ocr.config import OCRBaselineConfig, find_default_tesseract_cmd
from backend.app.ocr.engine import TesseractEngine
from backend.app.schemas.error import ErrorCode
from backend.app.services.pipeline_interface import PipelineProcessingError


class TestTesseractEngineDiscovery:
    """Verifies physical binary discovery and runtime version detection."""

    def test_engine_binary_found(self):
        cmd = find_default_tesseract_cmd()
        assert cmd is not None, "Tesseract executable should be resolved on the system."

    def test_engine_is_available(self):
        engine = TesseractEngine()
        assert engine.is_available() is True

    def test_engine_version_not_fabricated(self):
        engine = TesseractEngine()
        version = engine.get_version()
        assert isinstance(version, str)
        assert len(version) > 0
        # Ubuntu/Debian/Windows standard versions are 5.x
        assert version.startswith("5."), f"Unexpected engine version: {version}"

    def test_engine_available_languages(self):
        engine = TesseractEngine()
        langs = engine.get_available_languages()
        assert isinstance(langs, list)
        assert "eng" in langs, "English ('eng') language model must be available."


class TestTesseractConfiguration:
    """Verifies configuration validation and cryptographic hashing."""

    def test_configuration_hash_reproducibility(self):
        cfg1 = OCRBaselineConfig(psm=6, oem=1, preprocessing_variant="enhanced")
        cfg2 = OCRBaselineConfig(psm=6, oem=1, preprocessing_variant="enhanced")
        assert cfg1.compute_config_hash() == cfg2.compute_config_hash()

    def test_configuration_hash_changes_with_parameters(self):
        cfg1 = OCRBaselineConfig(psm=6)
        cfg2 = OCRBaselineConfig(psm=3)
        assert cfg1.compute_config_hash() != cfg2.compute_config_hash()

    def test_engine_metadata_structure(self):
        engine = TesseractEngine()
        meta = engine.build_metadata()
        assert meta.name == "tesseract"
        assert meta.version == engine.get_version()
        assert meta.language == "eng"
        assert meta.configuration_id == "ocr_tesseract_baseline_v1"
        assert len(meta.configuration_hash) == 64


class TestTesseractEngineFailurePaths:
    """Verifies graceful error handling and mapping to project error contracts."""

    def test_missing_binary_raises_model_unavailable(self):
        cfg = OCRBaselineConfig(tesseract_cmd="/nonexistent/path/to/tesseract.exe")
        engine = TesseractEngine(config=cfg)
        with pytest.raises(PipelineProcessingError) as exc_info:
            engine.get_version()
        assert exc_info.value.code == ErrorCode.MODEL_UNAVAILABLE

    def test_unsupported_language_raises_model_unavailable(self):
        cfg = OCRBaselineConfig(language="xyz_nonexistent_lang_999")
        engine = TesseractEngine(config=cfg)
        with pytest.raises(PipelineProcessingError) as exc_info:
            engine.validate_configuration(cfg)
        assert exc_info.value.code == ErrorCode.MODEL_UNAVAILABLE

    def test_zero_dimension_image_raises_invalid_request(self):
        engine = TesseractEngine()
        zero_img = Image.new("RGB", (0, 0))
        with pytest.raises(PipelineProcessingError) as exc_info:
            engine.execute(zero_img)
        assert exc_info.value.code == ErrorCode.INVALID_REQUEST

    def test_invalid_input_type_raises_invalid_request(self):
        engine = TesseractEngine()
        with pytest.raises(PipelineProcessingError) as exc_info:
            engine.execute("not_an_image")  # type: ignore
        assert exc_info.value.code == ErrorCode.INVALID_REQUEST
