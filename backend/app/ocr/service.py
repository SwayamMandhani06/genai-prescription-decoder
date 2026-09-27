"""
Phase 5: OCR/HTR Baseline Service
Orchestrates preprocessing artifact consumption, conventional OCR inference,
and immutable result generation. Maintains clean isolation from multimodal extraction.
"""

import hashlib
import io
import uuid
from typing import Dict, List, Optional, Union
from PIL import Image

from ..preprocessing import PrescriptionPreprocessingPipeline, PreprocessingConfig, PreprocessingResult
from ..schemas.error import ErrorCode
from ..services.pipeline_interface import PipelineProcessingError
from .config import OCRBaselineConfig
from .engine import TesseractEngine
from .metrics import evaluate_ocr_hypothesis, normalize_eval_text
from .schemas import (
    EvaluationMetrics,
    NormalizedOCRRepresentation,
    OCRRunResult,
)


class OCRBaselineService:
    """
    Research baseline service for conventional OCR/HTR evaluation.
    Accepts raw prescription images, executes Phase 4 preprocessing, and produces
    structured immutable OCR records for comparative benchmarking.
    """
    def __init__(
        self,
        ocr_config: Optional[OCRBaselineConfig] = None,
        preprocessing_config: Optional[PreprocessingConfig] = None,
    ):
        self.ocr_config = ocr_config or OCRBaselineConfig()
        self.preprocessing_pipeline = PrescriptionPreprocessingPipeline(config=preprocessing_config)
        self.engine = TesseractEngine(config=self.ocr_config)

    def run_ocr(
        self,
        image_input: Union[bytes, Image.Image],
        filename: Optional[str] = None,
        prescription_id: Optional[str] = None,
        preprocessing_variant: Optional[str] = None,
        config_override: Optional[OCRBaselineConfig] = None,
    ) -> OCRRunResult:
        """
        Executes the conventional OCR baseline.
        Consumes Phase 4 derived representations without modifying original image.
        """
        cfg = config_override or self.ocr_config
        target_variant = preprocessing_variant or cfg.preprocessing_variant

        # 1. Resolve image bytes and source SHA-256
        if isinstance(image_input, bytes):
            source_bytes = image_input
            source_sha256 = hashlib.sha256(source_bytes).hexdigest()
            # Run Phase 4 preprocessing
            prep_result: PreprocessingResult = self.preprocessing_pipeline.process(
                image_bytes=source_bytes,
                filename=filename,
            )
            derived_map = prep_result.derived_images
            primary_pil = prep_result.primary_processed_image

            # Select target variant
            if target_variant == "original":
                target_pil = Image.open(io.BytesIO(source_bytes)).convert("RGB")
            elif target_variant in derived_map:
                target_pil = derived_map[target_variant]
            elif target_variant == "primary":
                target_pil = primary_pil
            else:
                # Fallback to primary processed image if variant not found (e.g. deskewed when skew ~ 0)
                target_pil = primary_pil

        elif isinstance(image_input, Image.Image):
            target_pil = image_input
            buf = io.BytesIO()
            target_pil.save(buf, format="PNG")
            source_bytes = buf.getvalue()
            source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        else:
            raise PipelineProcessingError(
                code=ErrorCode.INVALID_REQUEST,
                message="Unsupported image input type; expected bytes or PIL.Image.Image.",
                stage="ocr_baseline_service",
            )

        # 2. Compute hash of preprocessed artifact fed to engine
        artifact_buf = io.BytesIO()
        target_pil.save(artifact_buf, format="PNG")
        artifact_sha256 = hashlib.sha256(artifact_buf.getvalue()).hexdigest()

        # 3. Execute OCR engine
        raw_text, tokens, lines, duration_seconds = self.engine.execute(
            pil_image=target_pil,
            config=cfg,
        )

        raw_text_sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        engine_metadata = self.engine.build_metadata(config=cfg)

        # 4. Status determination (empty output is partial/empty, never fabricated)
        if raw_text.strip():
            status = "completed"
        else:
            status = "partial"

        ocr_run_id = f"ocr-run-{uuid.uuid4().hex[:12]}"

        return OCRRunResult(
            ocr_run_id=ocr_run_id,
            prescription_id=prescription_id,
            source_image_sha256=source_sha256,
            preprocessing_artifact=target_variant,
            preprocessing_artifact_sha256=artifact_sha256,
            engine=engine_metadata,
            raw_text=raw_text,
            raw_text_sha256=raw_text_sha256,
            tokens=tokens,
            lines=lines,
            processing_status=status,
            duration_seconds=duration_seconds,
        )

    def run_variant_comparison(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
        prescription_id: Optional[str] = None,
        variants: Optional[List[str]] = None,
    ) -> Dict[str, OCRRunResult]:
        """
        Executes the OCR baseline across multiple Phase 4 preprocessing variants:
        - original
        - grayscale
        - enhanced (nominal baseline)
        - deskewed (if available)
        - thresholded (Sauvola)
        Enables empirical investigation of preprocessing impact on handwriting recognition.
        """
        source_sha256 = hashlib.sha256(image_bytes).hexdigest()

        # Run preprocessing once
        prep_result = self.preprocessing_pipeline.process(
            image_bytes=image_bytes,
            filename=filename,
        )

        available_variants: Dict[str, Image.Image] = {
            "original": Image.open(io.BytesIO(image_bytes)).convert("RGB"),
            **prep_result.derived_images,
        }

        requested = variants or ["original", "grayscale", "enhanced", "deskewed", "thresholded"]
        results: Dict[str, OCRRunResult] = {}

        for var_name in requested:
            if var_name not in available_variants:
                continue
            pil_img = available_variants[var_name]

            # Buffer hash
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            art_sha256 = hashlib.sha256(buf.getvalue()).hexdigest()

            # Execute
            raw_text, tokens, lines, duration = self.engine.execute(
                pil_image=pil_img,
                config=self.ocr_config,
            )

            status = "completed" if raw_text.strip() else "partial"
            run_id = f"ocr-comp-{var_name}-{uuid.uuid4().hex[:8]}"

            results[var_name] = OCRRunResult(
                ocr_run_id=run_id,
                prescription_id=prescription_id,
                source_image_sha256=source_sha256,
                preprocessing_artifact=var_name,
                preprocessing_artifact_sha256=art_sha256,
                engine=self.engine.build_metadata(),
                raw_text=raw_text,
                raw_text_sha256=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
                tokens=tokens,
                lines=lines,
                processing_status=status,
                duration_seconds=duration,
            )

        return results

    def create_normalized_representation(
        self,
        run_result: OCRRunResult,
    ) -> NormalizedOCRRepresentation:
        """
        Produces a separate normalized representation for evaluation.
        STRICTLY preserves the immutable raw text in run_result.
        """
        norm_text = normalize_eval_text(run_result.raw_text)
        return NormalizedOCRRepresentation(
            ocr_run_id=run_result.ocr_run_id,
            raw_text=run_result.raw_text,
            normalized_text=norm_text,
            normalization_rules=["NFKC", "lowercase", "collapse_spaces"],
            tokens=norm_text.split() if norm_text else [],
        )

    def evaluate_run(
        self,
        run_result: OCRRunResult,
        ground_truth_text: Optional[str] = None,
        ground_truth_entities: Optional[Dict[str, List[str]]] = None,
    ) -> EvaluationMetrics:
        """
        Calculates CER, WER, and entity-level metrics against ground truth.
        """
        return evaluate_ocr_hypothesis(
            reference_text=ground_truth_text,
            hypothesis_text=run_result.raw_text,
            ground_truth_entities=ground_truth_entities,
        )
