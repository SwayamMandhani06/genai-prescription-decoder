export type ProcessingStageId =
  | 'image_received'
  | 'image_processing'
  | 'handwriting_interpretation'
  | 'structured_extraction'
  | 'medicine_validation'
  | 'safety_analysis'
  | 'explanation_synthesis';

export type ProcessingStageState = 'pending' | 'active' | 'completed' | 'failed';

export interface ProcessingStage {
  id: ProcessingStageId;
  stepNumber: number;
  label: string;
  tagline: string;
  description: string;
  state: ProcessingStageState;
  progressPercent: number; // 0 - 100
  telemetryLogs: string[];
}

export type TokenType =
  | 'DOCUMENT_PRECHECK'
  | 'SEGMENT_POLYGON'
  | 'CURSIVE_LIGATURE'
  | 'BRAND_NAME'
  | 'GENERIC_SALT'
  | 'DOSAGE_STRENGTH'
  | 'POSOLOGY_FREQ'
  | 'RXNORM_ONTOLOGY'
  | 'CDSCO_APPROVAL'
  | 'CALIBRATED_ENTROPY'
  | 'LASA_SCREENING'
  | 'VERNACULAR_SCHEDULE';

export interface LiveToken {
  id: string;
  type: TokenType;
  label: string;
  value: string;
  confidence: number;
  stageId: ProcessingStageId;
  timestampMs: number;
}

export type ProcessingSpeedMode = 'fast' | 'normal' | 'thorough' | 'simulate_error';

export interface PipelineProgressEvent {
  currentStageId: ProcessingStageId;
  overallPercent: number;
  stages: ProcessingStage[];
  liveTokens: LiveToken[];
  currentLogMessage: string;
  activeModelHead: string;
  elapsedTimeMs: number;
  isCompleted: boolean;
  hasError: boolean;
  errorMessage?: string;
}
