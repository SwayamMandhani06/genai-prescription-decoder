import {
  PrescriptionAnalyzeResponseDto,
  ExtractedEntityDto,
  ValidationEvidenceDto,
  LasaScreeningDto,
  MultilingualPosologyDto,
} from '../../types/api.types';
import {
  ResultsDemoState,
  ExtractedFieldItem,
  ValidationEvidence,
  LasaSafetyDetail,
  MultilingualExplanationContent,
  PrescriptionAnalysisResult,
  MedicineCandidate,
} from '../../types/prescription.types';

/**
 * Maps ExtractedEntityDto (API contract) to ExtractedFieldItem (UI presentation)
 */
export function mapEntityDtoToFieldItem(dto: ExtractedEntityDto): ExtractedFieldItem {
  const statusLabel =
    dto.status === 'confident'
      ? 'CONFIDENT · High confidence'
      : dto.status === 'uncertain'
      ? 'UNCERTAIN · Needs verification'
      : 'FLAGGED · Do not rely on this interpretation';

  // Map backend field keys to UI domain field keys
  const fieldKeyMap: Record<string, ExtractedFieldItem['fieldKey']> = {
    medicine_name: 'medicineName',
    dosage: 'dosage',
    frequency: 'frequency',
    duration: 'duration',
    abbreviation: 'abbreviation',
  };

  return {
    fieldKey: fieldKeyMap[dto.field_key] || 'medicineName',
    fieldName: dto.field_label,
    value: dto.normalized_value || dto.raw_value,
    confidence: dto.confidence,
    status: dto.status,
    statusLabel,
    explanation: dto.explanation,
    source: dto.stroke_source,
    boundingBox: dto.bounding_box,
    uncertaintyReason: dto.uncertainty_reason || undefined,
    verificationInstruction: dto.verification_instruction || undefined,
    interpretedCandidate: dto.interpreted_candidate || undefined,
  };
}

/**
 * Maps ValidationEvidenceDto (API contract) to ValidationEvidence (UI presentation)
 */
export function mapValidationEvidenceDtoToDomain(dto: ValidationEvidenceDto): ValidationEvidence {
  const statusMap: Record<string, ValidationEvidence['validationStatus']> = {
    cdsco_approved: 'CDSCO_APPROVED',
    rxnorm_grounded: 'RXNORM_GROUNDED',
    formulary_match: 'FORMULARY_MATCH',
    unverified: 'UNVERIFIED',
  };

  return {
    extractedCandidate: dto.candidate_name,
    matchedMedicine: dto.matched_entity_name,
    genericSalt: dto.generic_salt,
    validationStatus: statusMap[dto.validation_status] || 'FORMULARY_MATCH',
    statusBadgeText: dto.status_badge_text,
    rxNormCui: dto.rxnorm_cui,
    cdscoSchedule: dto.cdsco_schedule,
    therapeuticClass: dto.therapeutic_class,
    standardIndications: dto.indications,
    evidenceSource: dto.evidence_source,
    referenceUrl: dto.reference_url || undefined,
    alternativeCandidates: (dto.alternatives || []).map((alt) => ({
      name: alt.name,
      generic: alt.generic,
      similarityScore: alt.similarity_score,
      notes: alt.notes,
    })),
  };
}

/**
 * Maps LasaScreeningDto (API contract) to LasaSafetyDetail (UI presentation)
 */
export function mapLasaScreeningDtoToDomain(dto: LasaScreeningDto): LasaSafetyDetail {
  return {
    hasWarning: dto.has_warning,
    prescribedCandidate: dto.prescribed_candidate,
    confusedWithDrug: dto.confusable_counterpart,
    tallManPrescribed: dto.tall_man_prescribed,
    tallManConfused: dto.tall_man_confused,
    similarityType: dto.similarity_type,
    levenshteinScore: dto.similarity_score,
    metaphoneMatch: dto.metaphone_match,
    clinicalRiskSummary: dto.clinical_risk_summary,
    mandatedAction: dto.mandated_action,
  };
}

/**
 * Maps MultilingualPosologyDto (API contract) to MultilingualExplanationContent (UI presentation)
 */
export function mapMultilingualPosologyDtoToDomain(
  dto: MultilingualPosologyDto
): {
  en: MultilingualExplanationContent;
  hi: MultilingualExplanationContent;
  mr: MultilingualExplanationContent;
} {
  const mapPack = (pack: typeof dto.en): MultilingualExplanationContent => ({
    summary: pack.summary,
    instructions: pack.patient_instructions,
    timing: (pack.daily_schedule || []).map((s) => ({
      slot: s.time_slot,
      icon: s.icon_key,
      dose: s.dosage_label,
      foodNote: s.food_instruction,
    })),
    precautions: pack.precautions || [],
  });

  return {
    en: mapPack(dto.en),
    hi: mapPack(dto.hi),
    mr: mapPack(dto.mr),
  };
}

/**
 * Maps complete PrescriptionAnalyzeResponseDto to ResultsDemoState (used by ResultsPage)
 */
export function mapApiResponseToResultsState(
  response: PrescriptionAnalyzeResponseDto
): ResultsDemoState {
  const { data } = response;

  const idMap: Record<string, ResultsDemoState['id']> = {
    'RX-PUN-3412-A': 'state-confident',
    'RX-MUM-8921-B': 'state-uncertain',
    'RX-CHN-5510-C': 'state-lasa',
    'RX-NGP-1104-D': 'state-flagged',
  };

  const stateId = idMap[data.accession_id] || 'state-confident';

  return {
    id: stateId,
    tabLabel: data.scenario_title,
    scenarioTitle: data.scenario_title,
    scenarioSubtitle: data.scenario_subtitle,
    accessionId: data.accession_id,
    difficultyTag: data.difficulty_tag,
    rawScriptKey: data.script_sample_key,
    patientName: data.patient_info.name,
    patientAgeGender: data.patient_info.age_gender,
    doctorName: data.prescriber_info.name,
    clinicName: data.prescriber_info.clinic_name,
    overallStatus: data.overall_status,
    documentConfidence: data.document_confidence,
    fields: data.extracted_entities.map(mapEntityDtoToFieldItem),
    validationEvidence: mapValidationEvidenceDtoToDomain(data.validation_evidence),
    lasaDetail: mapLasaScreeningDtoToDomain(data.lasa_screening),
    multilingual: mapMultilingualPosologyDtoToDomain(data.posology_explanation),
  };
}

/**
 * Maps complete PrescriptionAnalyzeResponseDto to PrescriptionAnalysisResult (used by legacy analyzer)
 */
export function mapApiResponseToAnalysisResult(
  response: PrescriptionAnalyzeResponseDto
): PrescriptionAnalysisResult {
  const { meta, document_telemetry, data } = response;

  const primaryMedName =
    data.extracted_entities.find((e) => e.field_key === 'medicine_name')?.normalized_value ||
    'Unknown Medicine';
  const dosage =
    data.extracted_entities.find((e) => e.field_key === 'dosage')?.normalized_value || 'N/A';
  const frequency =
    data.extracted_entities.find((e) => e.field_key === 'frequency')?.normalized_value || '1-0-1';
  const duration =
    data.extracted_entities.find((e) => e.field_key === 'duration')?.normalized_value || '5 days';

  const medCandidate: MedicineCandidate = {
    id: `med-${data.accession_id}`,
    brandName: primaryMedName,
    genericName: data.validation_evidence.generic_salt,
    dosage,
    form: 'Tablet',
    frequency,
    frequencyExplanation: data.posology_explanation.en.summary,
    timing: 'after_meal',
    duration,
    indication: data.validation_evidence.indications,
    confidenceScore: data.document_confidence,
    confidenceLevel:
      data.document_confidence >= 0.85
        ? 'HIGH_CONFIDENCE'
        : data.document_confidence >= 0.65
        ? 'BORDERLINE'
        : 'ABSTAIN_FLAGGED',
    boundingBox: data.extracted_entities[0]?.bounding_box || { x: 12, y: 30, width: 78, height: 14 },
    rxNormCui: data.validation_evidence.rxnorm_cui,
    cdscoApproved: data.validation_evidence.validation_status === 'cdsco_approved',
    atcCode: data.validation_evidence.atc_code,
  };

  return {
    id: meta.request_id,
    timestamp: meta.timestamp,
    processingTimeMs: meta.processing_time_ms,
    documentConfidence: data.document_confidence,
    qualityMetrics: {
      resolutionDpi: document_telemetry.estimated_dpi,
      inkContrastRatio: document_telemetry.contrast_ratio,
      skewAngleDegrees: document_telemetry.skew_angle_deg,
      illegibilityFraction: document_telemetry.illegibility_score,
    },
    extractedMedications: [medCandidate],
    summary: {
      totalDetected: 1,
      highConfidenceCount: data.overall_status === 'VERIFIED' ? 1 : 0,
      abstentionsCount: data.overall_status === 'SELECTIVE_ABSTAIN' ? 1 : 0,
      lasaRiskCount: data.lasa_screening.has_warning ? 1 : 0,
    },
  };
}
