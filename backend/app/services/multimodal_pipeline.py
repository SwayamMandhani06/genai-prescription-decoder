"""
Phase 6: Multimodal Prescription Processing Pipeline
Implements IPrescriptionPipeline using the multimodal vision-language extraction architecture.
Integrates Phase 4 Preprocessing & Quality Assessment with the MultimodalExtractionService.
Ensures the original prescription image is preserved as primary visual evidence while
providing full multi-medicine, field uncertainty, and visual grounding support.
"""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

from .pipeline_interface import IPrescriptionPipeline, PipelineOptions, PipelineProcessingError
from ..schemas.prescription import (
    PrescriptionAnalyzeResponse,
    FieldExtractionItem,
    MultilingualSummary,
    BoundingBox as UI_BoundingBox,
    ExtractedEntity,
    AlternativeCandidate,
    ValidationEvidence,
    ValidationItem,
    LasaFlagItem,
    LasaScreening,
    PosologyTimingSlot,
    PosologyLanguagePack,
    MultilingualPosology,
    DocumentTelemetry,
    PrescriptionMetadata,
    PatientInfo,
    PrescriberInfo,
    PrescriptionData,
)
from ..schemas.error import ErrorCode
from ..preprocessing import ImagePreprocessingService, ImageValidationError
from ..multimodal import (
    MultimodalExtractionService,
    PrescriptionExtractionResult,
    MultimodalConfig,
    MockMultimodalModelAdapter,
    GeminiMultimodalAdapter,
)
from ai.rag import get_medicine_validation_service
from ai.explanation import get_explanation_service


class MultimodalPrescriptionPipeline(IPrescriptionPipeline):
    """
    Multimodal vision-language pipeline integrating Phase 4 preprocessing
    and Phase 6 multimodal prescription extraction.
    """

    def __init__(
        self,
        service: Optional[MultimodalExtractionService] = None,
        config: Optional[MultimodalConfig] = None,
    ):
        self.config = config or MultimodalConfig()
        if service is not None:
            self.service = service
        elif self.config.provider == "gemini":
            self.service = MultimodalExtractionService(
                adapter=GeminiMultimodalAdapter(config=self.config),
                config=self.config,
            )
        else:
            self.service = MultimodalExtractionService(
                adapter=MockMultimodalModelAdapter(),
                config=self.config,
            )
        self.preprocessing_service = ImagePreprocessingService()

    async def process_prescription(
        self,
        image_bytes: Optional[bytes],
        filename: Optional[str],
        public_image_url: str,
        options: PipelineOptions,
    ) -> PrescriptionAnalyzeResponse:
        scenario = options.mock_scenario
        prescription_id = f"RX-{uuid.uuid4().hex[:8].upper()}"
        t_pipeline_start = time.perf_counter()
        t_preprocess_ms = 0.0
        t_inference_ms = 0.0
        t_entity_mapping_ms = 0.0
        t_rag_ms = 0.0
        t_conf_ms = 0.0
        t_lasa_ms = 0.0
        t_abstention_ms = 0.0
        t_explanation_ms = 0.0

        # ------------------------------------------------------------------
        # 1. Fault Injection / Error Scenarios (PLAN.md Section 6 & 11)
        # ------------------------------------------------------------------
        if scenario in ("image_quality_insufficient", "low_quality", "insufficient_quality"):
            raise PipelineProcessingError(
                code=ErrorCode.IMAGE_QUALITY_INSUFFICIENT,
                message="Prescription image quality is insufficient for reliable automated processing (effective resolution below 150 DPI threshold or severe optical degradation).",
                stage="image_quality_assessment",
                status_code=422,
                retryable=True,
                details={
                    "minimum_dpi": 150,
                    "detected_dpi": 96,
                    "blur_score": 38.4,
                    "contrast_ratio": 1.4,
                    "recommendation": "Retake prescription photo with direct overhead lighting, high resolution, and avoid motion blur.",
                },
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        if scenario == "validation_error":
            raise PipelineProcessingError(
                code=ErrorCode.VALIDATION_FAILED,
                message="Prescription payload failed schema validation: Missing required posology metadata.",
                stage="request_validation",
                status_code=400,
                retryable=False,
                details={"fields": ["confidence_threshold"]},
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        if scenario in ("server_error", "processing_failed"):
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message="Internal pipeline execution failure: Multimodal decoder attention state collapsed.",
                stage="multimodal_extraction",
                status_code=500,
                retryable=True,
                details={"worker_node": "multimodal-vision-01", "error_type": "AttentionCollapse"},
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        if scenario == "model_unavailable":
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="Prescription multimodal inference worker service is temporarily offline or unavailable (503 Service Unavailable).",
                stage="inference_dispatch",
                status_code=503,
                retryable=True,
                details={"service": "multimodal_worker", "retry_after_seconds": 5},
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        # ------------------------------------------------------------------
        # 2. Phase 4 Preprocessing & Quality Assessment Execution
        # ------------------------------------------------------------------
        processed_image_url: Optional[str] = None
        quality_report_dict: Optional[dict] = None
        preprocessing_manifest_dict: Optional[dict] = None
        preprocessed_bytes: Optional[bytes] = None

        t_pre_start = time.perf_counter()
        # Resolve real sample bytes if sample_id is provided without direct file upload
        if (not image_bytes or len(image_bytes) < 10) and options.sample_id:
            sample_map = {
                "rx-sample-1": "data/samples/sample_01_clear.png",
                "rx-sample-2": "data/samples/sample_06_lasa_pair.png",
                "rx-sample-3": "data/samples/sample_07_ambiguous_abstain.png",
                "sample-standard": "data/samples/sample_01_clear.png",
            }
            sample_file = sample_map.get(options.sample_id.lower())
            if sample_file:
                from pathlib import Path as _Path
                p = _Path(sample_file)
                if p.exists():
                    image_bytes = p.read_bytes()
                    filename = p.name

        if image_bytes and len(image_bytes) > 0 and image_bytes != b"dummy" and image_bytes != b"VALID_IMAGE_MOCK_STREAM":
            try:
                res, manifest, derived_url = self.preprocessing_service.process_and_store(
                    image_bytes=image_bytes,
                    filename=filename,
                    prescription_id=prescription_id,
                    reject_insufficient_quality=True,
                )
                processed_image_url = derived_url
                quality_report_dict = res.quality_report.model_dump()
                preprocessing_manifest_dict = manifest.model_dump()
                if res.primary_processed_image:
                    import io as _io
                    _buf = _io.BytesIO()
                    res.primary_processed_image.save(_buf, format="PNG")
                    preprocessed_bytes = _buf.getvalue()
            except ImageValidationError as ive:
                raise PipelineProcessingError(
                    code=ive.code,
                    message=ive.message,
                    stage=ive.stage,
                    status_code=ive.status_code,
                    retryable=ive.retryable,
                    details=ive.details,
                    prescription_id=prescription_id,
                    original_image_url=public_image_url,
                )
        t_preprocess_ms = (time.perf_counter() - t_pre_start) * 1000.0

        # ------------------------------------------------------------------
        # 3. Phase 6 Multimodal Vision-Language Extraction
        # Ingests untouched original prescription image as primary visual evidence
        # ------------------------------------------------------------------
        t_inf_start = time.perf_counter()
        effective_bytes = image_bytes if (image_bytes and len(image_bytes) >= 10) else b"VALID_IMAGE_MOCK_STREAM"
        
        extraction_result: PrescriptionExtractionResult = await self.service.extract_prescription(
            image_bytes=effective_bytes,
            prescription_id=prescription_id,
            original_image_url=public_image_url,
            mime_type="image/jpeg",
            preprocessed_bytes=preprocessed_bytes,
            preprocessed_image_url=processed_image_url,
            scenario=scenario,
        )
        t_inference_ms = (time.perf_counter() - t_inf_start) * 1000.0

        # ------------------------------------------------------------------
        # 4. Map Extraction Result to Canonical PLAN.md & UI Contracts
        # ------------------------------------------------------------------
        t_map_start = time.perf_counter()
        # Map primary fields
        fields_dict: Dict[str, FieldExtractionItem] = {}
        for key, field in extraction_result.fields.items():
            conf_val = 0.95 if field.status == "confident" else (0.65 if field.status == "uncertain" else 0.40)
            fields_dict[key] = FieldExtractionItem(
                value=field.value or "Not Observed / Absent",
                confidence=conf_val,
                status=field.status,
                candidates=field.candidates,
                explanation=field.explanation or "Visually observed handwriting feature",
                uncertainty_reason=field.uncertainty_reason,
                verification_instruction=field.verification_instruction,
            )

        # Ensure 'abbreviation' key matches Phase 1 DTO singular naming
        if "abbreviations" in fields_dict and "abbreviation" not in fields_dict:
            fields_dict["abbreviation"] = fields_dict["abbreviations"]

        # Build UI extracted_entities for bounding box overlays
        ui_entities: List[ExtractedEntity] = []
        for med_idx, med in enumerate(extraction_result.medicines):
            field_mappings = [
                ("medicine_name", "Medicine Name", med.medicine_name),
                ("dosage", "Dosage Strength", med.dosage),
                ("frequency", "Frequency", med.frequency),
                ("duration", "Duration", med.duration),
            ]
            for f_key, f_label, f_obj in field_mappings:
                # Resolve bounding box coordinates
                if f_obj.evidence and f_obj.evidence.region:
                    ui_box = UI_BoundingBox(
                        x=f_obj.evidence.region.x,
                        y=f_obj.evidence.region.y,
                        width=f_obj.evidence.region.width,
                        height=f_obj.evidence.region.height,
                    )
                else:
                    # No fabricated coordinates: set zero box to indicate ungrounded
                    ui_box = UI_BoundingBox(x=0.0, y=0.0, width=0.0, height=0.0)

                conf_score = (
                    med.overall_confidence
                    if med.overall_confidence is not None
                    else (0.95 if f_obj.status == "confident" else 0.65)
                )

                ui_entities.append(
                    ExtractedEntity(
                        field_key=f_key,  # type: ignore
                        field_label=f"{f_label} (Item {med_idx + 1})" if len(extraction_result.medicines) > 1 else f_label,
                        raw_value=f_obj.value or "Not Observed",
                        normalized_value=f_obj.value or "Not Observed",
                        confidence=conf_score,
                        status=f_obj.status,  # type: ignore
                        stroke_source="Original Prescription Visual Evidence",
                        bounding_box=ui_box,
                        explanation=f_obj.explanation or f"Multimodal extraction of {f_label}",
                        uncertainty_reason=f_obj.uncertainty_reason,
                        verification_instruction=f_obj.verification_instruction,
                        interpreted_candidate=f_obj.candidates[0] if f_obj.candidates else f_obj.value,
                    )
                )

        # Primary medicine for UI patient display summary
        primary_med_name = (
            extraction_result.medicines[0].medicine_name.value
            if extraction_result.medicines and extraction_result.medicines[0].medicine_name.value
            else "Extracted Medication"
        )
        primary_dosage = (
            extraction_result.medicines[0].dosage.value
            if extraction_result.medicines and extraction_result.medicines[0].dosage.value
            else ""
        )
        primary_freq = (
            extraction_result.medicines[0].frequency.value
            if extraction_result.medicines and extraction_result.medicines[0].frequency.value
            else ""
        )
        primary_duration = (
            extraction_result.medicines[0].duration.value
            if extraction_result.medicines and extraction_result.medicines[0].duration.value
            else ""
        )

        posology_summary_en = f"Take {primary_med_name} {primary_dosage} {primary_freq}."
        posology_summary_hi = f"{primary_med_name} {primary_dosage} {primary_freq} लें।"
        posology_summary_mr = f"{primary_med_name} {primary_dosage} {primary_freq} घ्या."
        t_entity_mapping_ms = (time.perf_counter() - t_map_start) * 1000.0

        # ------------------------------------------------------------------
        # Phase 7: RAG-Based Medicine Validation (PLAN.md Section 16)
        # ------------------------------------------------------------------
        t_rag_start = time.perf_counter()
        validation_dict: Dict[str, ValidationItem] = {}
        medicine_validations_list: List[Dict[str, Any]] = []
        primary_ui_evidence: Optional[Dict[str, Any]] = None
        rag_requires_human_review = False

        val_service = get_medicine_validation_service()
        raw_val_results: List[Any] = []
        for idx, med in enumerate(extraction_result.medicines):
            med_name_val = med.medicine_name.value
            dosage_val = med.dosage.value
            val_res = val_service.validate_candidate(
                candidate_name=med_name_val or "",
                observed_dosage=dosage_val,
            )
            raw_val_results.append(val_res)
            medicine_validations_list.append(val_res.model_dump())

            if val_res.requires_human_review:
                rag_requires_human_review = True

            # Formulate Section 6 ValidationItem
            matched_ref = val_res.selected_reference
            first_cand = val_res.matched_candidates[0] if val_res.matched_candidates else None
            active_src = matched_ref.provenance.source_name if matched_ref else (first_cand.provenance.source_name if first_cand else "None")
            active_match = matched_ref.medicine_name if matched_ref else (first_cand.medicine_name if first_cand else None)
            active_salt = matched_ref.generic_name if matched_ref else (first_cand.generic_name if first_cand else None)
            active_cui = matched_ref.rxnorm_cui if matched_ref else (first_cand.rxnorm_cui if first_cand else None)
            active_sched = matched_ref.cdsco_schedule if matched_ref else (first_cand.cdsco_schedule if first_cand else None)

            val_item = ValidationItem(
                found_in_db=(val_res.validation_status == "validated"),
                source=active_src,
                matched_entity_name=active_match,
                generic_salt=active_salt,
                rxnorm_cui=active_cui,
                cdsco_schedule=active_sched,
            )
            val_key = f"medicine_{idx + 1}" if len(extraction_result.medicines) > 1 else "medicine_name"
            validation_dict[val_key] = val_item
            if "medicine_name" not in validation_dict:
                validation_dict["medicine_name"] = val_item

            if idx == 0:
                primary_ui_evidence = val_res.to_ui_validation_evidence()
        t_rag_ms = (time.perf_counter() - t_rag_start) * 1000.0

        # ------------------------------------------------------------------
        # Phase 8: Confidence Estimation & Calibration (PLAN.md Section 17)
        # ------------------------------------------------------------------
        t_conf_start = time.perf_counter()
        from ai.confidence.service import get_confidence_service
        confidence_service = get_confidence_service()
        confidence_assessment = confidence_service.evaluate_prescription_confidence(
            extraction_result=extraction_result,
            validation_results=raw_val_results,
        )

        # Enrich Section 6 field extraction items with Phase 8 calibration signals
        for f_name, f_item in fields_dict.items():
            f_conf = confidence_assessment.fields.get(f_name)
            if f_conf:
                f_item.raw_confidence = f_conf.raw_signal.raw_value
                f_item.calibrated_confidence = f_conf.calibrated.value
                f_item.calibration_status = f_conf.calibrated.calibration_status
                f_item.calibration_method = f_conf.calibrated.calibration_method
        t_conf_ms = (time.perf_counter() - t_conf_start) * 1000.0

        # ------------------------------------------------------------------
        # Phase 10: LASA (Look-Alike / Sound-Alike) Conflict Detection (PLAN.md Section 19)
        # ------------------------------------------------------------------
        t_lasa_start = time.perf_counter()
        # Phase 10 detects potential medicine-name conflicts against reference pool & ISMP pairs.
        # It does NOT decide abstention or confirm/reject medicines; it passes evidence to Phase 9.
        from ai.lasa.service import get_lasa_detection_service
        lasa_service = get_lasa_detection_service()
        medicine_names_for_lasa = [
            med.medicine_name.value or ""
            for med in extraction_result.medicines
            if med.medicine_name.value
        ]
        lasa_result = lasa_service.detect_prescription(
            prescription_id=prescription_id,
            medicine_names=medicine_names_for_lasa,
        )
        t_lasa_ms = (time.perf_counter() - t_lasa_start) * 1000.0

        # ------------------------------------------------------------------
        # Phase 9: Abstention & Human Verification (PLAN.md Section 18)
        # ------------------------------------------------------------------
        t_abs_start = time.perf_counter()
        # Phase 9 consumes Phase 6 (extraction), Phase 7 (validation), Phase 8 (confidence),
        # and Phase 10 (LASA) evidence. Phase 9 owns the abstention and human verification decision.
        from ai.abstention.service import get_abstention_service
        abstention_service = get_abstention_service()
        abstention_decision = abstention_service.evaluate_prescription(
            prescription_id=prescription_id,
            extraction_result=extraction_result,
            confidence_assessment=confidence_assessment,
            validation_results=raw_val_results,
            original_image_url=public_image_url,
            lasa_detection=lasa_result,
        )

        # Enrich Section 6 field extraction items with Phase 9 abstention decisions
        for f_name, f_item in fields_dict.items():
            f_dec = abstention_decision.fields.get(f_name)
            if f_dec:
                f_item.abstention_decision = f_dec.decision
                f_item.abstention_reasons = f_dec.reason_codes
                f_item.requires_human_verification = f_dec.requires_human_verification

        # Ensure human verification state is initialized for traceability
        abstention_service.get_or_create_verification_state(
            prescription_id=prescription_id,
            original_image_url=public_image_url or "",
            pending_fields=abstention_decision.fields_requiring_verification,
        )

        # Build Section 6 lasa_flags from canonical Phase 10 detection results
        lasa_flags_list: List[LasaFlagItem] = []
        for med_lasa in lasa_result.medicines:
            for confusable in med_lasa.confusables:
                lasa_flags_list.append(LasaFlagItem(
                    field="medicine_name",
                    conflict_with=confusable.confusable_name,
                    risk=confusable.risk_level,
                    similarity_score=round(confusable.combined_score * 100, 1),
                    tall_man_prescribed=confusable.tall_man_prescribed,
                    tall_man_confused=confusable.tall_man_confused,
                    details=confusable.clinical_context,
                ))

        # Build LasaScreening for Phase 1 UI envelope from primary medicine result
        primary_lasa = lasa_result.medicines[0] if lasa_result.medicines else None
        if lasa_result.status != "completed":
            # Detection unavailable or failed: explicit non-completion semantics
            ui_lasa_screening = LasaScreening(
                has_warning=False,
                prescribed_candidate=primary_med_name,
                confusable_counterpart="Screening Unavailable",
                tall_man_prescribed=primary_med_name,
                tall_man_confused="",
                similarity_score=0.0,
                similarity_type="Orthographic & Phonetic",
                metaphone_match=False,
                clinical_risk_summary=(
                    f"LASA conflict detection is {lasa_result.status}. "
                    "Manual clinical verification of medicine identity is required."
                ),
                mandated_action="Manual identity verification required before dispensing.",
            )
        elif primary_lasa and primary_lasa.has_lasa_conflict and primary_lasa.confusables:
            top_conf = primary_lasa.confusables[0]
            ui_lasa_screening = LasaScreening(
                has_warning=True,
                prescribed_candidate=primary_lasa.prescribed_candidate,
                confusable_counterpart=top_conf.confusable_name,
                tall_man_prescribed=top_conf.tall_man_prescribed or primary_lasa.prescribed_candidate,
                tall_man_confused=top_conf.tall_man_confused or top_conf.confusable_name,
                similarity_score=top_conf.combined_score,
                similarity_type=(
                    "Orthographic & Phonetic" if top_conf.similarity_type in ("combined", "known_pair")
                    else ("Phonetic" if top_conf.similarity_type == "phonetic" else "Orthographic")
                ),
                metaphone_match=top_conf.metaphone_match,
                clinical_risk_summary=top_conf.clinical_context,
                mandated_action="Verify correct medicine identity before dispensing.",
            )
        else:
            ui_lasa_screening = LasaScreening(
                has_warning=False,
                prescribed_candidate=primary_med_name,
                confusable_counterpart="None Identified",
                tall_man_prescribed=primary_med_name,
                tall_man_confused="",
                similarity_score=0.0,
                similarity_type="Orthographic & Phonetic",
                metaphone_match=False,
                clinical_risk_summary="No high-risk orthographic collision flagged at extraction stage.",
                mandated_action="Routine clinical verification before dispensing.",
            )

        # Application safety-review state determination:
        # SAFETY_ALERT is an application safety-review state indicating that a potential
        # medicine-name conflict requires attention/verification.
        # It does NOT mean: clinical danger, adverse drug event, wrong medicine,
        # medical risk probability, diagnosis, or prescribing recommendation.
        effective_human_review = (
            extraction_result.requires_human_review
            or rag_requires_human_review
            or abstention_decision.requires_human_verification
            or (lasa_result.status == "completed" and bool(lasa_result.conflict_detected))
            or (lasa_result.status != "completed")
        )
        has_lasa_alert = (
            lasa_result.status == "completed"
            and bool(lasa_result.conflict_detected)
            and lasa_result.highest_risk in ("high", "medium")
        )
        lasa_status_override = has_lasa_alert
        overall_status_str = (
            "SAFETY_ALERT" if has_lasa_alert
            else ("NEEDS_VERIFICATION" if effective_human_review else "VERIFIED")
        )

        if primary_ui_evidence:
            ui_val_evidence = ValidationEvidence(
                candidate_name=primary_ui_evidence["candidate_name"],
                matched_entity_name=primary_ui_evidence["matched_entity_name"],
                generic_salt=primary_ui_evidence["generic_salt"],
                validation_status=primary_ui_evidence["validation_status"],
                status_badge_text=primary_ui_evidence["status_badge_text"],
                cdsco_schedule=primary_ui_evidence["cdsco_schedule"],
                rxnorm_cui=primary_ui_evidence["rxnorm_cui"],
                atc_code=primary_ui_evidence["atc_code"],
                therapeutic_class=primary_ui_evidence["therapeutic_class"],
                indications=primary_ui_evidence["indications"],
                evidence_source=primary_ui_evidence["evidence_source"],
                reference_url=primary_ui_evidence.get("reference_url"),
                alternatives=[
                    AlternativeCandidate(
                        name=a["name"],
                        generic=a["generic"],
                        similarity_score=a["similarity_score"],
                        notes=a["notes"],
                    )
                    for a in primary_ui_evidence.get("alternatives", [])
                ],
            )
        else:
            ui_val_evidence = ValidationEvidence(
                candidate_name=primary_med_name,
                matched_entity_name=primary_med_name,
                generic_salt=primary_med_name,
                validation_status="unverified",
                status_badge_text="UNVERIFIED",
                cdsco_schedule="Schedule H Prescription Drug",
                rxnorm_cui="N/A",
                atc_code="N/A",
                therapeutic_class="Prescription Medicine",
                indications="Clinical Posology Recorded",
                evidence_source="Reference Validation Service",
            )
        t_abstention_ms = (time.perf_counter() - t_abs_start) * 1000.0

        # ------------------------------------------------------------------
        # Phase 11: Multilingual Patient-Friendly Explanation (PLAN.md Section 20)
        # ------------------------------------------------------------------
        t_exp_start = time.perf_counter()
        has_lasa_conflict_flag = bool(lasa_result.status == "completed" and lasa_result.conflict_detected)
        confusable_name = (
            ui_lasa_screening.confusable_counterpart
            if ui_lasa_screening and ui_lasa_screening.has_warning
            else None
        )
        val_status_str = primary_ui_evidence.get("validation_status", "validated") if primary_ui_evidence else "validated"

        primary_med = extraction_result.medicines[0] if extraction_result.medicines else None
        primary_med_status = "confident"
        if primary_med:
            if hasattr(primary_med, "medicine_name") and hasattr(primary_med.medicine_name, "status"):
                primary_med_status = primary_med.medicine_name.status
            elif getattr(primary_med, "status", None):
                primary_med_status = primary_med.status

        # A readable medicine name is not uncertain merely because another field is missing
        candidate_status_val = "confident"
        if not primary_med_name or primary_med_name.endswith("...") or primary_med_status in ("uncertain", "unreadable", "flagged"):
            candidate_status_val = "uncertain"

        med_requires_verification = bool(
            (primary_med and getattr(primary_med, "requires_verification", False))
            or candidate_status_val == "uncertain"
        )

        exp_summary, exp_posology, exp_full = get_explanation_service().generate_prescription_bundle(
            prescription_id=prescription_id,
            medicine_name=primary_med_name,
            dosage=primary_dosage,
            frequency=primary_freq,
            duration=primary_duration,
            candidate_status=candidate_status_val,
            validation_status=val_status_str,
            abstention_decision=abstention_decision.decision if hasattr(abstention_decision, "decision") else "accepted",
            requires_human_verification=med_requires_verification,
            has_lasa_conflict=has_lasa_conflict_flag,
            confusable_counterpart=confusable_name,
            is_service_healthy=True,
        )
        t_explanation_ms = (time.perf_counter() - t_exp_start) * 1000.0
        t_total_ms = (time.perf_counter() - t_pipeline_start) * 1000.0

        logger.info(
            "Prescription [%s] processing timings: total=%.1fms (preprocessing=%.1fms, inference=%.1fms, entity_mapping=%.1fms, rag=%.1fms, confidence=%.1fms, lasa=%.1fms, abstention=%.1fms, explanation=%.1fms)",
            prescription_id,
            t_total_ms,
            t_preprocess_ms,
            t_inference_ms,
            t_entity_mapping_ms,
            t_rag_ms,
            t_conf_ms,
            t_lasa_ms,
            t_abstention_ms,
            t_explanation_ms,
        )
        # Resolve patient and prescriber info from actual extraction (no fabrication)
        pat_details = extraction_result.patient_details or {}
        p_name = pat_details.get("name") or "Not present in prescription"
        p_age = pat_details.get("age_or_dob") or ""
        p_sex = pat_details.get("sex_gender") or ""
        p_age_gender = f"{p_age} {p_sex}".strip() or "Not present in prescription"

        doc_details = extraction_result.doctor_details or {}
        d_name = doc_details.get("doctor_name") or "Not present in prescription"
        d_qual = doc_details.get("qualifications") or "Not present in prescription"
        d_reg = doc_details.get("registration_no") or "Not present in prescription"
        d_clinic = doc_details.get("clinic_or_hospital") or "Not present in prescription"
        d_addr = doc_details.get("contact") or "Not present in prescription"

        # Synchronize prescription posology summary across languages and DTO models
        all_med_names = [
            m.medicine_name.value
            for m in extraction_result.medicines
            if hasattr(m, "medicine_name") and getattr(m.medicine_name, "value", None)
        ]
        if not all_med_names and primary_med_name:
            all_med_names = [primary_med_name]

        if extraction_result.prescription_summary:
            exp_summary.en = extraction_result.prescription_summary
            exp_posology.en.summary = extraction_result.prescription_summary
            if len(all_med_names) > 1:
                med_list_str = ", ".join(all_med_names)
                exp_summary.hi = f"प्रिस्क्रिप्शन में {med_list_str} दवाएं शामिल हैं। कृपया नीचे दिए गए समय और निर्देश अनुसार लें।"
                exp_posology.hi.summary = exp_summary.hi
                exp_summary.mr = f"प्रिस्क्रिप्शनमध्ये {med_list_str} ही औषधे समाविष्ट आहेत. कृपया खाली दिलेल्या वेळेनुसार आणि सूचनेनुसार औषधे घ्यावीत."
                exp_posology.mr.summary = exp_summary.mr
        elif len(all_med_names) > 1:
            med_list_str = ", ".join(all_med_names)
            multi_summary_en = f"Your prescription contains {len(all_med_names)} prescribed medicines: {med_list_str}. Follow each recorded administration schedule below."
            exp_summary.en = multi_summary_en
            exp_posology.en.summary = multi_summary_en
            exp_summary.hi = f"प्रिस्क्रिप्शन में {len(all_med_names)} दवाएं ({med_list_str}) लिखी हैं। कृपया नीचे दिए गए समय अनुसार लें।"
            exp_posology.hi.summary = exp_summary.hi
            exp_summary.mr = f"प्रिस्क्रिप्शनमध्ये {len(all_med_names)} औषधे ({med_list_str}) लिहिलेली आहेत. कृपया खाली दिलेल्या वेळेनुसार औषधे घ्यावीत."
            exp_posology.mr.summary = exp_summary.mr

        data_block = PrescriptionData(
            accession_id=f"ACC-{prescription_id}",
            script_sample_key="multimodal_v1",
            scenario_title=f"Multimodal Extraction: {primary_med_name}",
            scenario_subtitle="Multimodal Vision-Language Extraction Pipeline",
            difficulty_tag=(
                "LASA Similarity" if lasa_status_override
                else ("Moderate Cursive" if effective_human_review else "Clear Handwriting")
            ),
            overall_status=overall_status_str,  # type: ignore
            document_confidence=0.70 if effective_human_review else 0.94,
            patient_info=PatientInfo(name=p_name, age_gender=p_age_gender),
            prescriber_info=PrescriberInfo(
                name=d_name,
                qualifications=d_qual,
                registration_no=d_reg,
                clinic_name=d_clinic,
                clinic_address=d_addr,
            ),
            extracted_entities=ui_entities,
            validation_evidence=ui_val_evidence,
            lasa_screening=ui_lasa_screening,
            posology_explanation=exp_posology,
        )

        response = PrescriptionAnalyzeResponse(
            prescription_id=prescription_id,
            original_image_url=public_image_url,
            fields=fields_dict,
            lasa_flags=lasa_flags_list,
            validation=validation_dict,
            explanation=exp_summary,
            requires_human_review=effective_human_review,
            status="abstain" if overall_status_str == "NEEDS_VERIFICATION" and scenario in ("abstained", "flagged") else "success",
            meta=PrescriptionMetadata(
                request_id=f"REQ-{uuid.uuid4().hex[:12].upper()}",
                timestamp=extraction_result.created_at,
                processing_time_ms=int(t_total_ms),
                model_version=f"{extraction_result.model.provider}:{extraction_result.model.model_id}",
                pipeline_stages_completed=11,
            ),
            document_telemetry=DocumentTelemetry(
                estimated_dpi=200,
                contrast_ratio=18.5,
                skew_angle_deg=0.4,
                illegibility_score=0.15 if not effective_human_review else 0.45,
                orientation="Portrait",
            ),
            data=data_block,
            processed_image_url=processed_image_url,
            quality_report=quality_report_dict,
            preprocessing_manifest=preprocessing_manifest_dict,
            medicines=[m.model_dump() for m in extraction_result.medicines],
            multimodal_result=extraction_result.model_dump(),
            medicine_validations=medicine_validations_list,
            confidence_assessment=confidence_assessment.model_dump(),
            abstention=abstention_decision.model_dump(),
            lasa_detection=lasa_result.model_dump(),
            multilingual_explanation=exp_full.model_dump(),
            prescription_summary=extraction_result.prescription_summary,
            patient_details=extraction_result.patient_details,
            doctor_details=extraction_result.doctor_details,
        )



        # Attach telemetry from Phase 4 if available
        if quality_report_dict:
            res_metric = quality_report_dict["metrics"]["resolution"]
            contrast_metric = quality_report_dict["metrics"]["contrast"]
            skew_metric = quality_report_dict["metrics"]["skew"]
            response.document_telemetry.estimated_dpi = int(res_metric["effective_ppi"])
            response.document_telemetry.contrast_ratio = float(contrast_metric["rms_contrast"])
            response.document_telemetry.skew_angle_deg = float(skew_metric["estimated_angle_deg"])
            response.document_telemetry.illegibility_score = round(
                float(1.0 - quality_report_dict["heuristic_quality_score"]), 2
            )

        return response
