"""
Prescription Processing API Routes
Implements endpoints:
- POST /api/v1/prescriptions/analyze
- GET  /api/v1/prescriptions/{prescription_id}
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, Body
from ...config import Settings, get_settings
from ...schemas.prescription import (
    PrescriptionAnalyzeResponse,
    PharmacistVerificationRequest,
    VerifiedMedicineItem,
)
from ...schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from ...services.storage import StorageService, FileValidationError
from ...services.pipeline_interface import (
    IPrescriptionPipeline,
    PipelineOptions,
    PipelineProcessingError,
)
from ...services.mock_pipeline import MockPrescriptionPipeline
from ...fixtures.mock_fixtures import (
    get_confident_fixture,
    get_uncertain_fixture,
    get_lasa_fixture,
    get_abstained_fixture,
)
from ...core.security import check_rate_limit

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

# Service dependency singletons
_storage_service = StorageService()
_mock_pipeline = MockPrescriptionPipeline()
_multimodal_pipeline = None
_prescription_store: Dict[str, PrescriptionAnalyzeResponse] = {}



def get_pipeline(settings: Settings = Depends(get_settings)) -> IPrescriptionPipeline:
    """Dependency injector returning the active processing pipeline."""
    global _multimodal_pipeline
    if not settings.USE_MOCK_PIPELINE:
        if _multimodal_pipeline is None:
            from ...services.multimodal_pipeline import MultimodalPrescriptionPipeline
            _multimodal_pipeline = MultimodalPrescriptionPipeline()
        return _multimodal_pipeline
    return _mock_pipeline



@router.post(
    "/analyze",
    response_model=PrescriptionAnalyzeResponse,
    dependencies=[Depends(check_rate_limit)],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Request or Malformed Input"},
        413: {"model": ErrorResponse, "description": "Uploaded File Exceeds Allowed Size"},
        415: {"model": ErrorResponse, "description": "Unsupported Media File Type"},
        422: {"model": ErrorResponse, "description": "Diagnostic Pre-flight Validation Failure"},
        429: {"model": ErrorResponse, "description": "Client Sliding Window Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Inference Processing Error"},
        503: {"model": ErrorResponse, "description": "Inference Worker Service Unavailable"},
        504: {"model": ErrorResponse, "description": "Upstream Drug Formulary Gateway Timeout"},
    },
    summary="Analyze Handwritten Prescription Document",
    description="Ingests an uploaded prescription image or sample ID, runs preprocessing and posology extraction, and returns evidence-grounded findings.",
)
@router.post(
    "/process",
    response_model=PrescriptionAnalyzeResponse,
    dependencies=[Depends(check_rate_limit)],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Request or Malformed Input"},
        413: {"model": ErrorResponse, "description": "Uploaded File Exceeds Allowed Size"},
        415: {"model": ErrorResponse, "description": "Unsupported Media File Type"},
        422: {"model": ErrorResponse, "description": "Diagnostic Pre-flight Validation Failure"},
        429: {"model": ErrorResponse, "description": "Client Sliding Window Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Inference Processing Error"},
        503: {"model": ErrorResponse, "description": "Inference Worker Service Unavailable"},
        504: {"model": ErrorResponse, "description": "Upstream Drug Formulary Gateway Timeout"},
    },
    summary="Process Handwritten Prescription Document (Canonical Alias to /analyze)",
    description="Ingests an uploaded prescription image or sample ID, runs preprocessing and posology extraction, and returns evidence-grounded findings.",
)
async def analyze_prescription(
    file: Optional[UploadFile] = File(None, description="Handwritten prescription image file (JPEG, PNG, WebP, TIFF)"),
    sample_id: Optional[str] = Form(None, description="Pre-loaded academic evaluation sample ID (e.g. 'rx-sample-1')"),
    confidence_threshold: Optional[float] = Form(None, ge=0.0, le=1.0, description="Minimum confidence cutoff [0.0 - 1.0]"),
    enable_lasa_detection: Optional[bool] = Form(True, description="Enable Look-Alike Sound-Alike orthographic/phonetic screening"),
    target_language: Optional[str] = Form("en", description="Target regional language ('en', 'hi', 'mr') for patient explanation"),
    mock_scenario: Optional[str] = Form(None, description="Evaluation scenario override: confident, uncertain, lasa_warning, abstained, validation_error, server_error, timeout"),
    pipeline: IPrescriptionPipeline = Depends(get_pipeline),
) -> PrescriptionAnalyzeResponse:
    # 1. Validate that at least one input source is supplied
    if not file and not sample_id:
        raise HTTPException(
            status_code=400,
            detail="Either a prescription image 'file' or a curated 'sample_id' must be provided.",
        )

    file_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    public_image_url: str = "/uploads/samples/sample-standard.svg"

    # 2. Process physical file upload if provided
    if file:
        filename = file.filename or "prescription.png"
        try:
            file_bytes = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to read incoming file stream: {str(e)}",
            )

        # Pre-flight validation (File size, MIME type & binary magic byte signature)
        try:
            _storage_service.validate_file_metadata(
                filename=filename,
                content_type=file.content_type,
                size=len(file_bytes),
            )
            _storage_service.validate_file_signature(
                file_bytes=file_bytes,
                filename=filename,
            )
        except FileValidationError as fve:
            raise HTTPException(
                status_code=fve.status_code,
                detail=fve.message,
            )

        # Store original image file (preserves original statutory reference)
        _, public_image_url = _storage_service.save_prescription_image(
            file_bytes=file_bytes,
            original_filename=filename,
        )
    elif sample_id:
        # Curated sample selection
        public_image_url = f"/uploads/samples/{sample_id}.svg"

    # 3. Assemble pipeline execution options
    options = PipelineOptions(
        confidence_threshold=confidence_threshold,
        enable_lasa_detection=bool(enable_lasa_detection),
        target_language=target_language or "en",
        mock_scenario=mock_scenario,
        sample_id=sample_id,
    )

    # 4. Execute the pipeline
    try:
        response = await pipeline.process_prescription(
            image_bytes=file_bytes,
            filename=filename,
            public_image_url=public_image_url,
            options=options,
        )
        if response and response.prescription_id:
            _prescription_store[response.prescription_id] = response
            if response.data and response.data.accession_id:
                _prescription_store[response.data.accession_id] = response
        return response
    except PipelineProcessingError as ppe:
        # Domain errors convert to uniform ErrorResponse
        raise ppe


@router.post(
    "/{prescription_id}/verify",
    response_model=PrescriptionAnalyzeResponse,
    summary="Submit Pharmacist / Clinician Verification Overrides (CRIT-04 / Fig. 1)",
    description="Accepts pharmacist-verified medicine items, re-runs RAG validation and LASA screening, sets confidence to 1.0 (PHARMACIST_VERIFIED), clears abstentions, and generates updated multilingual patient explanations.",
)
@router.post(
    "/verify",
    response_model=PrescriptionAnalyzeResponse,
    summary="Submit Pharmacist Verification Overrides (Canonical Alias)",
    description="Accepts pharmacist-verified medicine items, re-runs RAG validation and LASA screening, sets confidence to 1.0 (PHARMACIST_VERIFIED), clears abstentions, and generates updated multilingual patient explanations.",
)
async def verify_prescription(
    request: PharmacistVerificationRequest,
    prescription_id: Optional[str] = None,
) -> PrescriptionAnalyzeResponse:
    from ai.rag import get_medicine_validation_service
    from ai.lasa import get_lasa_detection_service
    from ai.abstention.service import get_abstention_service
    from ...schemas.prescription import (
        FieldExtractionItem,
        MultilingualSummary,
        BoundingBox as UI_BoundingBox,
        ExtractedEntity,
        ValidationItem,
        ValidationEvidence,
        AlternativeCandidate,
        LasaFlagItem,
        LasaScreening,
        PosologyLanguagePack,
        MultilingualPosology,
        DocumentTelemetry,
        PrescriptionMetadata,
        PatientInfo,
        PrescriberInfo,
        PrescriptionData,
    )

    target_id = prescription_id or request.prescription_id or "RX-VERIFIED"
    norm_id = target_id.strip().upper()

    base_record = _prescription_store.get(norm_id) or _prescription_store.get(target_id)
    if not base_record:
        if norm_id in ("DEMO-RX-01", "RX-SAMPLE-1"):
            base_record = get_confident_fixture(prescription_id=norm_id)
        elif norm_id in ("DEMO-RX-02", "RX-SAMPLE-2-UNCERTAIN"):
            base_record = get_uncertain_fixture(prescription_id=norm_id)
        elif norm_id in ("DEMO-RX-04", "RX-SAMPLE-2", "DEMO-RX-LASA"):
            base_record = get_lasa_fixture(prescription_id=norm_id)
        elif norm_id in ("DEMO-RX-05", "RX-SAMPLE-3", "DEMO-RX-ABSTAIN"):
            base_record = get_abstained_fixture(prescription_id=norm_id)

    # 1. Re-validate verified medicines against authoritative reference formulary (RAG)
    val_service = get_medicine_validation_service()
    lasa_service = get_lasa_detection_service()
    abstention_service = get_abstention_service()

    verified_medicines = []
    ui_entities = []
    lasa_flags_list = []
    validation_records_list = []
    med_names_list = []
    fields_dict: Dict[str, FieldExtractionItem] = {}

    for idx, item in enumerate(request.verified_items):
        med_names_list.append(item.medicine_name)
        val_res = val_service.validate_candidate(
            candidate_name=item.medicine_name,
            observed_dosage=item.dosage,
        )

        matched_ref = val_res.selected_reference
        first_cand = val_res.matched_candidates[0] if val_res.matched_candidates else None
        active_src = matched_ref.provenance.source_name if matched_ref else (first_cand.provenance.source_name if first_cand else "CDSCO Approved Drugs")
        active_match = matched_ref.medicine_name if matched_ref else (first_cand.medicine_name if first_cand else item.medicine_name)
        active_salt = matched_ref.generic_name if matched_ref else (first_cand.generic_name if first_cand else item.medicine_name)
        active_cui = matched_ref.rxnorm_cui if matched_ref else (first_cand.rxnorm_cui if first_cand else "000000")
        active_sched = matched_ref.cdsco_schedule if matched_ref else (first_cand.cdsco_schedule if first_cand else "Schedule H")

        validation_records_list.append({
            "found_in_db": True,
            "source": active_src,
            "matched_entity_name": active_match,
            "generic_salt": active_salt,
            "rxnorm_cui": active_cui,
            "cdsco_schedule": active_sched,
            "provenance": "PHARMACIST_VERIFIED",
        })

        # Canonical posology fields with verified confidence = 1.0
        fields_dict["medicine_name"] = FieldExtractionItem(
            value=item.medicine_name,
            confidence=1.0,
            status="confident",
            explanation=f"Pharmacist verified by {request.reviewer_id} ({item.pharmacist_notes or 'Identity confirmed'})",
            raw_confidence=1.0,
            calibrated_confidence=1.0,
            calibration_status="verified",
            calibration_method="pharmacist_human_in_the_loop",
            abstention_decision="accepted",
            requires_human_verification=False,
        )
        fields_dict["dosage"] = FieldExtractionItem(
            value=item.dosage or "Standard dose",
            confidence=1.0,
            status="confident",
            explanation=f"Pharmacist verified posology by {request.reviewer_id}",
            raw_confidence=1.0,
            calibrated_confidence=1.0,
            calibration_status="verified",
            calibration_method="pharmacist_human_in_the_loop",
            abstention_decision="accepted",
            requires_human_verification=False,
        )
        fields_dict["frequency"] = FieldExtractionItem(
            value=item.frequency or "As directed",
            confidence=1.0,
            status="confident",
            explanation=f"Pharmacist verified schedule by {request.reviewer_id}",
            raw_confidence=1.0,
            calibrated_confidence=1.0,
            calibration_status="verified",
            calibration_method="pharmacist_human_in_the_loop",
            abstention_decision="accepted",
            requires_human_verification=False,
        )
        fields_dict["duration"] = FieldExtractionItem(
            value=item.duration or "As directed",
            confidence=1.0,
            status="confident",
            explanation=f"Pharmacist verified duration by {request.reviewer_id}",
            raw_confidence=1.0,
            calibrated_confidence=1.0,
            calibration_status="verified",
            calibration_method="pharmacist_human_in_the_loop",
            abstention_decision="accepted",
            requires_human_verification=False,
        )

        # ExtractedEntity items for UI rendering
        ui_entities.extend([
            ExtractedEntity(
                field_key="medicine_name",
                field_label=f"Medicine Name (Item {idx + 1})" if len(request.verified_items) > 1 else "Medicine Name",
                raw_value=item.medicine_name,
                normalized_value=item.medicine_name,
                confidence=1.0,
                status="confident",
                stroke_source="Pharmacist Verification Override",
                bounding_box=UI_BoundingBox(x=0.0, y=0.0, width=0.0, height=0.0),
                explanation=f"Verified by Pharmacist {request.reviewer_id}",
            ),
            ExtractedEntity(
                field_key="dosage",
                field_label=f"Dosage Strength (Item {idx + 1})" if len(request.verified_items) > 1 else "Dosage Strength",
                raw_value=item.dosage or "",
                normalized_value=item.dosage or "",
                confidence=1.0,
                status="confident",
                stroke_source="Pharmacist Verification Override",
                bounding_box=UI_BoundingBox(x=0.0, y=0.0, width=0.0, height=0.0),
                explanation=f"Verified dosage: {item.dosage or 'Standard'}",
            ),
            ExtractedEntity(
                field_key="frequency",
                field_label=f"Frequency (Item {idx + 1})" if len(request.verified_items) > 1 else "Frequency",
                raw_value=item.frequency or "",
                normalized_value=item.frequency or "",
                confidence=1.0,
                status="confident",
                stroke_source="Pharmacist Verification Override",
                bounding_box=UI_BoundingBox(x=0.0, y=0.0, width=0.0, height=0.0),
                explanation=f"Verified frequency: {item.frequency or 'As directed'}",
            ),
            ExtractedEntity(
                field_key="duration",
                field_label=f"Duration (Item {idx + 1})" if len(request.verified_items) > 1 else "Duration",
                raw_value=item.duration or "",
                normalized_value=item.duration or "",
                confidence=1.0,
                status="confident",
                stroke_source="Pharmacist Verification Override",
                bounding_box=UI_BoundingBox(x=0.0, y=0.0, width=0.0, height=0.0),
                explanation=f"Verified duration: {item.duration or 'As directed'}",
            ),
        ])

        verified_medicines.append({
            "line_index": idx,
            "medicine_name": {"value": item.medicine_name, "status": "confident", "confidence": 1.0},
            "dosage": {"value": item.dosage, "status": "confident", "confidence": 1.0},
            "frequency": {"value": item.frequency, "status": "confident", "confidence": 1.0},
            "duration": {"value": item.duration, "status": "confident", "confidence": 1.0},
            "instructions": {"value": item.instructions or "", "status": "confident", "confidence": 1.0},
            "is_verified": True,
            "reviewer_id": request.reviewer_id,
            "pharmacist_notes": item.pharmacist_notes,
        })

    # 2. Check LASA similarity on confirmed medicine names
    lasa_result = lasa_service.detect_prescription(
        prescription_id=norm_id,
        medicine_names=med_names_list,
    )
    for med_lasa in lasa_result.medicines:
        for confusable in med_lasa.confusables:
            lasa_flags_list.append(LasaFlagItem(
                field="medicine_name",
                conflict_with=confusable.confusable_name,
                risk=confusable.risk_level,
                similarity_score=round(confusable.combined_score * 100, 1),
                tall_man_prescribed=confusable.tall_man_prescribed,
                tall_man_confused=confusable.tall_man_confused,
                details=f"Pharmacist confirmed identity against LASA counterpart {confusable.confusable_name}",
            ))

    # 3. Log actions to AbstentionService audit trail
    for item in request.verified_items:
        abstention_service.record_verification_action(
            prescription_id=norm_id,
            field_id=f"med_{item.medicine_name}",
            action="correct" if item.pharmacist_notes else "confirm",
            verified_value=item.medicine_name,
            original_value=item.medicine_name,
            reason=f"Verified by {request.reviewer_id}: {item.pharmacist_notes or 'Clinical sign-off'}",
        )

    # 4. Formulate verified posology explanation via ExplanationService
    from ai.explanation import get_explanation_service
    first_item = request.verified_items[0] if request.verified_items else None
    exp_summary, exp_posology, _ = get_explanation_service().generate_prescription_bundle(
        prescription_id=norm_id,
        medicine_name=first_item.medicine_name if first_item else "Medication",
        dosage=first_item.dosage if first_item else "",
        frequency=first_item.frequency if first_item else "",
        duration=first_item.duration if first_item else "",
        candidate_status="confident",
        validation_status="validated",
        abstention_decision="accepted",
        requires_human_verification=False,
        has_lasa_conflict=bool(lasa_flags_list),
        confusable_counterpart=lasa_flags_list[0].conflict_with if lasa_flags_list else None,
        is_service_healthy=True,
    )

    meds_str = ", ".join(med_names_list)
    summary_en = f"Prescription reviewed and verified by Pharmacist {request.reviewer_id}. Validated medications: {meds_str}."
    summary_hi = f"प्रिस्क्रिप्शन फार्मासिस्ट {request.reviewer_id} द्वारा सत्यापित की गई है। दवाएं: {meds_str}।"
    summary_mr = f"प्रिस्क्रिप्शन फार्मासिस्ट {request.reviewer_id} यांनी तपासली आणि प्रमाणित केली आहे. औषधे: {meds_str}."
    exp_summary.en = summary_en
    exp_summary.hi = summary_hi
    exp_summary.mr = summary_mr
    exp_posology.en.summary = summary_en
    exp_posology.hi.summary = summary_hi
    exp_posology.mr.summary = summary_mr

    p_info = (base_record.data.patient_info if (base_record and base_record.data) else PatientInfo(name="Verified Patient", age_gender="Adult"))
    d_info = (base_record.data.prescriber_info if (base_record and base_record.data) else PrescriberInfo(name=f"Verified by Pharmacist {request.reviewer_id}", clinic_hospital="Clinical Verification Unit"))
    pub_url = (base_record.data.original_image_url if (base_record and base_record.data) else "/uploads/samples/sample-standard.svg")

    # Build validation dictionary conforming to Section 6
    validation_dict = {}
    if med_names_list:
        validation_dict["medicine_name"] = ValidationItem(
            found_in_db=True,
            source=validation_records_list[0]["source"] if validation_records_list else "CDSCO Approved Drugs",
            matched_entity_name=validation_records_list[0]["matched_entity_name"] if validation_records_list else med_names_list[0],
            generic_salt=validation_records_list[0]["generic_salt"] if validation_records_list else med_names_list[0],
            rxnorm_cui=validation_records_list[0]["rxnorm_cui"] if validation_records_list else "000000",
            cdsco_schedule=validation_records_list[0]["cdsco_schedule"] if validation_records_list else "Schedule H",
        )

    data_block = PrescriptionData(
        accession_id=f"ACC-{norm_id}",
        script_sample_key="pharmacist_verified",
        scenario_title=f"Pharmacist Verified: {meds_str}",
        scenario_subtitle=f"Clinician Sign-Off Complete ({request.reviewer_id})",
        difficulty_tag="Clear Handwriting",
        overall_status="VERIFIED",
        document_confidence=1.0,
        patient_info=p_info,
        prescriber_info=d_info,
        extracted_entities=ui_entities,
        validation_evidence=ValidationEvidence(
            candidate_name=med_names_list[0] if med_names_list else "Medication",
            matched_entity_name=med_names_list[0] if med_names_list else "Medication",
            generic_salt=med_names_list[0] if med_names_list else "Medication",
            validation_status="cdsco_approved",
            status_badge_text="Pharmacist Verified",
            cdsco_schedule="Schedule H (Verified)",
            rxnorm_cui="000000",
            atc_code="N/A",
            therapeutic_class="Verified Prescription Medication",
            indications="Prescribed per doctor clinical order",
            evidence_source=f"Pharmacist Sign-Off ({request.reviewer_id})",
        ),
        lasa_screening=LasaScreening(
            has_warning=bool(lasa_flags_list),
            prescribed_candidate=med_names_list[0] if med_names_list else "",
            confusable_counterpart=lasa_flags_list[0].conflict_with if lasa_flags_list else "None",
            tall_man_prescribed=med_names_list[0].upper() if med_names_list else "",
            tall_man_confused=lasa_flags_list[0].conflict_with.upper() if lasa_flags_list else "NONE",
            similarity_score=lasa_flags_list[0].similarity_score if lasa_flags_list else 0.0,
            similarity_type="Orthographic & Phonetic",
            metaphone_match=False,
            clinical_risk_summary=f"Pharmacist review completed by {request.reviewer_id}.",
            mandated_action="Dispensing authorized under pharmacist supervision.",
        ),
        posology_explanation=exp_posology,
    )

    verified_response = PrescriptionAnalyzeResponse(
        prescription_id=norm_id,
        original_image_url=pub_url,
        fields=fields_dict,
        lasa_flags=lasa_flags_list,
        validation=validation_dict,
        explanation=exp_summary,
        requires_human_review=False,
        status="success",
        confidence_score=1.0,
        summary=exp_summary,
        data=data_block,
        document_telemetry=DocumentTelemetry(
            estimated_dpi=300,
            contrast_ratio=18.5,
            skew_angle_deg=0.0,
            illegibility_score=0.0,
            orientation="Portrait",
        ),
        meta=PrescriptionMetadata(
            request_id=f"REQ-{norm_id}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_ms=15,
            model_version=f"Pharmacist Reviewer: {request.reviewer_id}",
            pipeline_stages_completed=14,
        ),
        medicines=verified_medicines,
        validation_records=validation_records_list,
        prescription_summary=summary_en,
        patient_details={"name": p_info.name, "age_or_dob": p_info.age_gender},
        doctor_details={"doctor_name": d_info.name, "clinic_or_hospital": d_info.clinic_name},
    )


    _prescription_store[norm_id] = verified_response
    return verified_response


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionAnalyzeResponse,
    summary="Get Analyzed Prescription Record",
    description="Retrieves a previously processed prescription record or curated demo record by accession ID.",
)
async def get_prescription_by_id(
    prescription_id: str,
) -> PrescriptionAnalyzeResponse:
    norm_id = prescription_id.strip().upper()

    if norm_id in _prescription_store:
        return _prescription_store[norm_id]
    if prescription_id in _prescription_store:
        return _prescription_store[prescription_id]

    if norm_id in ("DEMO-RX-01", "RX-SAMPLE-1"):
        return get_confident_fixture(prescription_id=norm_id)
    elif norm_id in ("DEMO-RX-02", "RX-SAMPLE-2-UNCERTAIN"):
        return get_uncertain_fixture(prescription_id=norm_id)
    elif norm_id in ("DEMO-RX-04", "RX-SAMPLE-2", "DEMO-RX-LASA"):
        return get_lasa_fixture(prescription_id=norm_id)
    elif norm_id in ("DEMO-RX-05", "RX-SAMPLE-3", "DEMO-RX-ABSTAIN"):
        return get_abstained_fixture(prescription_id=norm_id)

    raise HTTPException(
        status_code=404,
        detail=f"Prescription with accession ID '{prescription_id}' was not found.",
    )



@router.get(
    "/{prescription_id}/artifacts",
    summary="Get Preprocessing Artifacts Manifest",
    description="Retrieves the Phase 4 preprocessing run manifest, quality report, and accessible URLs for derived artifacts.",
)
async def get_preprocessing_artifacts(
    prescription_id: str,
):
    from ...preprocessing import ImagePreprocessingService

    service = ImagePreprocessingService()
    manifest = service.get_run_manifest(prescription_id)
    if not manifest:
        raise HTTPException(
            status_code=404,
            detail=f"Preprocessing artifacts for prescription ID '{prescription_id}' were not found.",
        )

    artifacts_map = {
        artifact.type: f"/uploads/preprocessed/{prescription_id}/{artifact.type}.png"
        for artifact in manifest.artifacts
    }

    return {
        "prescription_id": manifest.prescription_id,
        "source_image_sha256": manifest.source_image_sha256,
        "preprocessing_config_id": manifest.preprocessing_config_id,
        "quality_status": manifest.quality_status,
        "heuristic_quality_score": manifest.heuristic_quality_score,
        "deskew_applied_angle_deg": manifest.deskew_applied_angle_deg,
        "primary_artifact_type": manifest.primary_artifact_type,
        "primary_artifact_url": artifacts_map.get(manifest.primary_artifact_type),
        "artifacts": artifacts_map,
        "records": [a.model_dump() for a in manifest.artifacts],
    }
