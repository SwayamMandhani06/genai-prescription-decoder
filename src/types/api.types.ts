/**
 * Backend API Contract DTOs
 * Matches FastAPI Pydantic schemas for endpoint POST /api/v1/prescriptions/analyze
 * Kept intentionally separate from UI presentation models to ensure zero business coupling.
 */

export interface BoundingBoxDto {
  x: number; // percentage 0 - 100
  y: number;
  width: number;
  height: number;
}

export type EntityFieldKeyDto =
  | 'medicine_name'
  | 'dosage'
  | 'frequency'
  | 'duration'
  | 'abbreviation';

export type EntityStatusDto = 'confident' | 'uncertain' | 'flagged';

export interface ExtractedEntityDto {
  field_key: EntityFieldKeyDto;
  field_label: string;
  raw_value: string;
  normalized_value: string;
  confidence: number; // 0.0 - 1.0
  status: EntityStatusDto;
  stroke_source: string;
  bounding_box: BoundingBoxDto;
  explanation: string;
  uncertainty_reason?: string | null;
  verification_instruction?: string | null;
  interpreted_candidate?: string | null;
}

export interface AlternativeCandidateDto {
  name: string;
  generic: string;
  similarity_score: number;
  notes: string;
}

export interface ValidationEvidenceDto {
  candidate_name: string;
  matched_entity_name: string;
  generic_salt: string;
  validation_status: 'cdsco_approved' | 'rxnorm_grounded' | 'formulary_match' | 'unverified';
  status_badge_text: string;
  cdsco_schedule: string;
  rxnorm_cui: string;
  atc_code: string;
  therapeutic_class: string;
  indications: string;
  evidence_source: string;
  reference_url?: string | null;
  alternatives: AlternativeCandidateDto[];
}

export interface LasaScreeningDto {
  has_warning: boolean;
  prescribed_candidate: string;
  confusable_counterpart: string;
  tall_man_prescribed: string;
  tall_man_confused: string;
  similarity_score: number; // percentage 0 - 100
  similarity_type: 'Orthographic & Phonetic' | 'Orthographic' | 'Phonetic';
  metaphone_match: boolean;
  clinical_risk_summary: string;
  mandated_action: string;
}

export interface PosologyTimingSlotDto {
  time_slot: string;
  icon_key: string;
  dosage_label: string;
  food_instruction: string;
}

export interface PosologyLanguagePackDto {
  summary: string;
  patient_instructions: string;
  daily_schedule: PosologyTimingSlotDto[];
  precautions: string[];
}

export interface MultilingualPosologyDto {
  en: PosologyLanguagePackDto;
  hi: PosologyLanguagePackDto;
  mr: PosologyLanguagePackDto;
}

export interface DocumentTelemetryDto {
  estimated_dpi: number;
  contrast_ratio: number;
  skew_angle_deg: number;
  illegibility_score: number;
  orientation: 'Portrait' | 'Landscape';
}

export interface PrescriptionMetadataDto {
  request_id: string;
  timestamp: string;
  processing_time_ms: number;
  model_version: string;
  pipeline_stages_completed: number;
}

export interface PatientInfoDto {
  name: string;
  age_gender: string;
}

export interface PrescriberInfoDto {
  name: string;
  qualifications: string;
  registration_no: string;
  clinic_name: string;
  clinic_address: string;
}

export interface PrescriptionDataDto {
  accession_id: string;
  script_sample_key: string;
  scenario_title: string;
  scenario_subtitle: string;
  difficulty_tag: 'Clear Handwriting' | 'Moderate Cursive' | 'LASA Similarity' | 'Severe Ambiguity';
  overall_status: 'VERIFIED' | 'NEEDS_VERIFICATION' | 'SAFETY_ALERT' | 'SELECTIVE_ABSTAIN';
  document_confidence: number;
  patient_info: PatientInfoDto;
  prescriber_info: PrescriberInfoDto;
  extracted_entities: ExtractedEntityDto[];
  validation_evidence: ValidationEvidenceDto;
  lasa_screening: LasaScreeningDto;
  posology_explanation: MultilingualPosologyDto;
}

export interface PrescriptionAnalyzeResponseDto {
  status: 'success' | 'abstain' | 'error';
  meta: PrescriptionMetadataDto;
  document_telemetry: DocumentTelemetryDto;
  data: PrescriptionDataDto;
}

export interface FastApiValidationErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface FastApiHttpErrorDto {
  detail: string | FastApiValidationErrorDetail[];
  error_code?: string;
  request_id?: string;
}

export interface PrescriptionAnalyzeOptionsDto {
  confidence_threshold?: number;
  enable_lasa_detection?: boolean;
  target_language?: 'en' | 'hi' | 'mr';
  mock_scenario?:
    | 'confident'
    | 'uncertain'
    | 'flagged'
    | 'lasa_warning'
    | 'validation_error'
    | 'server_error'
    | 'timeout'
    | 'malformed'
    | 'empty';
}

/**
 * Result envelope pattern for safe functional handling
 */
export type ApiResult<T, E = FastApiHttpErrorDto> =
  | { ok: true; data: T }
  | { ok: false; error: E; statusCode: number };
