export type ConfidenceLevel = 'HIGH_CONFIDENCE' | 'BORDERLINE' | 'ABSTAIN_FLAGGED';

export interface BoundingBox {
  x: number; // percentage 0 - 100
  y: number; // percentage 0 - 100
  width: number; // percentage
  height: number; // percentage
  inkStrokeIds?: string[];
}

export type MedicationForm = 'Tablet' | 'Capsule' | 'Syrup' | 'Injection' | 'Inhaler' | 'Drops' | 'Ointment';

export type FoodTiming = 'before_meal' | 'after_meal' | 'with_meal' | 'empty_stomach' | 'at_bedtime';

export interface MedicineCandidate {
  id: string;
  brandName: string;
  genericName: string;
  dosage: string;
  form: MedicationForm;
  frequency: string; // e.g. "1-0-1" or "0-1-0"
  frequencyExplanation: string; // e.g. "Twice daily (Morning & Night)"
  timing: FoodTiming;
  duration: string; // e.g. "5 days"
  indication: string; // e.g. "Acute bacterial bronchitis / Respiratory tract infection"
  confidenceScore: number; // 0.0 - 1.0 (e.g. 0.94)
  confidenceLevel: ConfidenceLevel;
  abstentionReason?: string; // Populated when model abstains
  boundingBox: BoundingBox;
  rxNormCui?: string;
  cdscoApproved: boolean;
  atcCode?: string;
}

export interface PrescriptionSample {
  id: string;
  title: string;
  doctorSpecialty: string;
  clinicType: string;
  patientProfile: string;
  chiefComplaint: string;
  clinicalNote: string;
  difficultyScore: 'Clear' | 'Moderate Cursive' | 'Severe Ambiguity';
  medications: MedicineCandidate[];
  rawSvgInkKey: string;
}

export interface PrescriptionAnalysisResult {
  id: string;
  timestamp: string;
  processingTimeMs: number;
  documentConfidence: number;
  qualityMetrics: {
    resolutionDpi: number;
    inkContrastRatio: number;
    skewAngleDegrees: number;
    illegibilityFraction: number;
  };
  extractedMedications: MedicineCandidate[];
  summary: {
    totalDetected: number;
    highConfidenceCount: number;
    abstentionsCount: number;
    lasaRiskCount: number;
  };
}

export type FieldConfidenceStatus = 'confident' | 'uncertain' | 'flagged';

export interface ExtractedFieldItem {
  fieldKey: 'medicineName' | 'dosage' | 'frequency' | 'duration' | 'abbreviation' | 'route';
  fieldName: string;
  value: string;
  confidence: number; // 0.0 - 1.0 (e.g. 0.94)
  status: FieldConfidenceStatus;
  statusLabel: string; // e.g. "CONFIDENT · High confidence", "UNCERTAIN · Needs verification", "FLAGGED · Do not rely on this interpretation"
  explanation: string;
  source: string; // e.g. "Prescription Line 01 · Pen Stroke #1"
  boundingBox?: BoundingBox;
  uncertaintyReason?: string;
  verificationInstruction?: string;
  interpretedCandidate?: string;
}

export interface ValidationEvidence {
  extractedCandidate: string;
  matchedMedicine: string;
  genericSalt: string;
  validationStatus: 'CDSCO_APPROVED' | 'RXNORM_GROUNDED' | 'FORMULARY_MATCH' | 'UNVERIFIED';
  statusBadgeText: string;
  rxNormCui: string;
  cdscoSchedule: string;
  therapeuticClass: string;
  standardIndications: string;
  evidenceSource: string;
  referenceUrl?: string;
  alternativeCandidates: Array<{
    name: string;
    generic: string;
    similarityScore: number;
    notes: string;
  }>;
}

export interface LasaSafetyDetail {
  hasWarning: boolean;
  prescribedCandidate: string;
  confusedWithDrug: string;
  tallManPrescribed: string;
  tallManConfused: string;
  similarityType: 'Orthographic & Phonetic' | 'Orthographic' | 'Phonetic';
  levenshteinScore: number;
  metaphoneMatch: boolean;
  clinicalRiskSummary: string;
  mandatedAction: string;
}

export type ResultsDemoStateId =
  | 'state-confident'
  | 'state-uncertain'
  | 'state-lasa'
  | 'state-flagged';

export interface PosologyTimingSlot {
  slot: string;
  icon: string;
  dose: string;
  foodNote: string;
}

export interface MultilingualExplanationContent {
  summary: string;
  instructions: string;
  timing: PosologyTimingSlot[];
  precautions: string[];
}

export interface ResultsDemoState {
  id: ResultsDemoStateId;
  tabLabel: string;
  scenarioTitle: string;
  scenarioSubtitle: string;
  accessionId: string;
  difficultyTag: 'Clear Handwriting' | 'Moderate Cursive' | 'LASA Similarity' | 'Severe Ambiguity';
  rawScriptKey: string;
  patientName: string;
  patientAgeGender: string;
  doctorName: string;
  clinicName: string;
  overallStatus: 'VERIFIED' | 'NEEDS_VERIFICATION' | 'SAFETY_ALERT' | 'SELECTIVE_ABSTAIN';
  documentConfidence: number;
  fields: ExtractedFieldItem[];
  validationEvidence: ValidationEvidence;
  lasaDetail?: LasaSafetyDetail;
  multilingual: {
    en: MultilingualExplanationContent;
    hi: MultilingualExplanationContent;
    mr: MultilingualExplanationContent;
  };
}

