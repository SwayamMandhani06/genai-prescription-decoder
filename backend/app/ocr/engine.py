"""
Phase 5: Tesseract OCR Engine Adapter
Encapsulates conventional OCR baseline execution.
Detects actual engine binary versions and available languages at runtime.
Preserves raw OCR output immutability and never fabricates confidence scores.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Tuple
from PIL import Image

from ..schemas.error import ErrorCode
from ..services.pipeline_interface import PipelineProcessingError
from .config import OCRBaselineConfig, find_default_tesseract_cmd
from .schemas import BoundingBox, OCREngineMetadata, OCRLine, OCRToken

logger = logging.getLogger("aura_rx.ocr.engine")

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    PYTESSERACT_AVAILABLE = False


class TesseractEngine:
    """
    Interface wrapper around conventional Tesseract OCR binary.
    Guarantees runtime traceability, deterministic configuration, and safe subprocess execution.
    """
    def __init__(self, config: Optional[OCRBaselineConfig] = None):
        self.config = config or OCRBaselineConfig()
        self._tesseract_cmd: Optional[str] = self.config.tesseract_cmd or find_default_tesseract_cmd()
        self._version_cache: Optional[str] = None
        self._languages_cache: Optional[List[str]] = None

        if PYTESSERACT_AVAILABLE and self._tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd

    def get_binary_path(self) -> Optional[str]:
        """Returns the active resolved path to the tesseract executable."""
        return self._tesseract_cmd

    def is_available(self) -> bool:
        """Verifies whether pytesseract is installed and the tesseract binary is runnable."""
        if not PYTESSERACT_AVAILABLE or not self._tesseract_cmd:
            return False
        if not os.path.isfile(self._tesseract_cmd):
            return False
        try:
            self.get_version()
            return True
        except Exception:
            return False

    def get_version(self) -> str:
        """
        Retrieves actual installed Tesseract binary version at runtime.
        DO NOT FABRICATE.
        """
        if self._version_cache:
            return self._version_cache

        if not PYTESSERACT_AVAILABLE:
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="pytesseract package is not installed in the active environment.",
                stage="ocr_baseline_init",
                retryable=False,
            )

        if not self._tesseract_cmd or not os.path.isfile(self._tesseract_cmd):
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=f"Tesseract binary not found at '{self._tesseract_cmd}'.",
                stage="ocr_baseline_init",
                retryable=False,
            )

        try:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
            raw_ver = str(pytesseract.get_tesseract_version())
            self._version_cache = raw_ver.strip()
            return self._version_cache
        except Exception as e:
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=f"Failed to query Tesseract binary version: {str(e)}",
                stage="ocr_baseline_init",
                retryable=False,
            )

    def get_available_languages(self) -> List[str]:
        """Queries the engine for installed tessdata language models."""
        if self._languages_cache:
            return self._languages_cache

        if not self.is_available():
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="Tesseract engine is not available to query languages.",
                stage="ocr_baseline_init",
                retryable=False,
            )

        try:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
            langs = pytesseract.get_languages()
            self._languages_cache = langs
            return langs
        except Exception as e:
            logger.warning("Could not list Tesseract languages: %s", e)
            return ["eng"]

    def validate_configuration(self, config: Optional[OCRBaselineConfig] = None) -> None:
        """Ensures the requested language and runtime parameters are valid for the engine."""
        cfg = config or self.config
        version = self.get_version()
        if not version:
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="Tesseract version could not be detected.",
                stage="ocr_configuration_validation",
            )

        available_langs = self.get_available_languages()
        if cfg.language not in available_langs:
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=f"Requested OCR language '{cfg.language}' is not installed in tessdata. Available: {available_langs}",
                stage="ocr_configuration_validation",
                details={"available_languages": available_langs, "requested": cfg.language},
            )

    def build_metadata(self, config: Optional[OCRBaselineConfig] = None) -> OCREngineMetadata:
        """Constructs audit-traceable engine metadata structure."""
        cfg = config or self.config
        version = self.get_version()
        return OCREngineMetadata(
            name="tesseract",
            version=version,
            language=cfg.language,
            configuration_id=cfg.configuration_id,
            configuration_hash=cfg.compute_config_hash(),
            psm=cfg.psm,
            oem=cfg.oem,
            tessdata_path=os.path.dirname(self._tesseract_cmd) if self._tesseract_cmd else None,
        )

    def execute(
        self,
        pil_image: Image.Image,
        config: Optional[OCRBaselineConfig] = None,
    ) -> Tuple[str, List[OCRToken], List[OCRLine], float]:
        """
        Executes OCR extraction on a PIL Image.
        Returns:
            (raw_text, tokens, lines, duration_seconds)
        Preserves raw text immutability and extracts token bounding boxes and genuine confidence scores.
        """
        cfg = config or self.config
        self.validate_configuration(cfg)

        if not isinstance(pil_image, Image.Image):
            raise PipelineProcessingError(
                code=ErrorCode.INVALID_REQUEST,
                message="OCR input must be a valid PIL Image instance.",
                stage="ocr_input_validation",
            )

        if pil_image.width == 0 or pil_image.height == 0:
            raise PipelineProcessingError(
                code=ErrorCode.INVALID_REQUEST,
                message="OCR input image has zero width or height.",
                stage="ocr_input_validation",
            )

        custom_flags = f"--psm {cfg.psm} --oem {cfg.oem}"
        timeout = cfg.timeout_seconds

        start_time = time.perf_counter()

        try:
            # 1. Execute raw text extraction
            raw_text = pytesseract.image_to_string(
                pil_image,
                lang=cfg.language,
                config=custom_flags,
                timeout=timeout,
            )
        except (pytesseract.TesseractTimeoutError, TimeoutError):
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message=f"OCR execution timed out after {timeout} seconds.",
                stage="ocr_inference",
                retryable=True,
            )
        except pytesseract.TesseractError as te:
            # Mask low-level system traces while providing safe explanation
            clean_msg = str(te).split("\n")[0]
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message=f"Tesseract OCR engine failure: {clean_msg}",
                stage="ocr_inference",
                retryable=False,
            )
        except Exception as e:
            raise PipelineProcessingError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Unexpected error during OCR execution: {str(e)}",
                stage="ocr_inference",
                retryable=False,
            )

        # 2. Execute spatial token extraction
        tokens: List[OCRToken] = []
        lines_map: Dict[int, List[OCRToken]] = {}

        try:
            data = pytesseract.image_to_data(
                pil_image,
                lang=cfg.language,
                config=custom_flags,
                output_type=pytesseract.Output.DICT,
                timeout=timeout,
            )

            n_boxes = len(data.get("text", []))
            for i in range(n_boxes):
                token_text = data["text"][i]
                if not token_text or not token_text.strip():
                    continue

                raw_conf = data["conf"][i]
                try:
                    conf_val = float(raw_conf)
                    # Tesseract assigns -1 when confidence is unavailable
                    confidence = conf_val if (conf_val >= 0.0) else None
                except (ValueError, TypeError):
                    confidence = None

                x = int(data["left"][i])
                y = int(data["top"][i])
                w = int(data["width"][i])
                h = int(data["height"][i])

                line_num = int(data["line_num"][i]) if "line_num" in data else None
                block_num = int(data["block_num"][i]) if "block_num" in data else None
                par_num = int(data["par_num"][i]) if "par_num" in data else None
                word_num = int(data["word_num"][i]) if "word_num" in data else None

                tok = OCRToken(
                    text=token_text,
                    confidence=confidence,
                    bbox=BoundingBox(x=x, y=y, width=w, height=h),
                    line_num=line_num,
                    block_num=block_num,
                    par_num=par_num,
                    word_num=word_num,
                )
                tokens.append(tok)

                if line_num is not None:
                    if line_num not in lines_map:
                        lines_map[line_num] = []
                    lines_map[line_num].append(tok)

        except Exception as e:
            logger.warning("Token spatial data extraction failed; continuing with raw text: %s", e)

        # Build lines structure
        lines: List[OCRLine] = []
        for line_num in sorted(lines_map.keys()):
            line_tokens = lines_map[line_num]
            line_text = " ".join([t.text for t in line_tokens])
            if line_tokens:
                min_x = min(t.bbox.x for t in line_tokens)
                min_y = min(t.bbox.y for t in line_tokens)
                max_x = max(t.bbox.x + t.bbox.width for t in line_tokens)
                max_y = max(t.bbox.y + t.bbox.height for t in line_tokens)
                line_bbox = BoundingBox(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)
            else:
                line_bbox = None

            lines.append(OCRLine(line_num=line_num, text=line_text, tokens=line_tokens, bbox=line_bbox))

        duration_seconds = round(time.perf_counter() - start_time, 4)
        return raw_text, tokens, lines, duration_seconds
