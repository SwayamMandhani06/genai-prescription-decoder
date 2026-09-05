import {
  PrescriptionSample,
  PrescriptionAnalysisResult,
  ResultsDemoState,
} from '../types/prescription.types';
import { LasaWarning } from '../types/safety.types';
import { LanguageCode, MultilingualExplanationPackage } from '../types/explanation.types';
import {
  ProcessingStage,
  ProcessingStageId,
  LiveToken,
  ProcessingSpeedMode,
  PipelineProgressEvent,
} from '../types/pipeline.types';
import { MOCK_PRESCRIPTION_SAMPLES } from '../data/mockPrescriptions';
import { CLINICAL_LASA_CATALOG } from '../data/lasaCatalog';
import { MULTILINGUAL_EXPLANATIONS } from '../data/multilingualCatalog';
import { getPrescriptionApiClient } from './api/prescriptionApiClient';
import {
  mapApiResponseToResultsState,
  mapApiResponseToAnalysisResult,
} from './mappers/prescriptionMapper';
import { ApiError } from './api/apiErrors';

export interface AnalysisOptions {
  confidenceThreshold?: number; // e.g. 0.65
  enableLasaDetection?: boolean;
  targetLanguage?: LanguageCode;
  speedMode?: ProcessingSpeedMode;
  mockScenario?:
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

export const PIPELINE_STAGE_DEFINITIONS: Omit<
  ProcessingStage,
  'state' | 'progressPercent' | 'telemetryLogs'
>[] = [
  {
    id: 'image_received',
    stepNumber: 1,
    label: 'Image Received & Optical Intake',
    tagline: 'Sensor Stream Verification',
    description: 'Verifying image bit-depth, bi-tonal contrast ratio, and optical sensor calibration.',
  },
  {
    id: 'image_processing',
    stepNumber: 2,
    label: 'Image Normalization & Deskew',
    tagline: 'Preprocessing & Filtering',
    description: 'Compensating for document skew, paper texture noise, and segmenting doctor letterheads.',
  },
  {
    id: 'handwriting_interpretation',
    stepNumber: 3,
    label: 'Handwriting Interpretation',
    tagline: 'Cursive Stroke Tokenization',
    description: 'Multi-head cross-attention recognizing cursive ligatures, loops, and clinical shorthand.',
  },
  {
    id: 'structured_extraction',
    stepNumber: 4,
    label: 'Structured Entity Extraction',
    tagline: 'Biomedical NER Parsing',
    description: 'Parsing token streams into Medicine Name, Dosage, Frequency, and Duration fields.',
  },
  {
    id: 'medicine_validation',
    stepNumber: 5,
    label: 'Medicine Validation & Grounding',
    tagline: 'Pharmacopeia Knowledge Graph',
    description: 'Cross-referencing entities against CDSCO India Schedule H and US NLM RxNorm formularies.',
  },
  {
    id: 'safety_analysis',
    stepNumber: 6,
    label: 'Safety Analysis & Uncertainty',
    tagline: 'Entropy Calibration & LASA Alert',
    description: 'Calculating Monte Carlo epistemic entropy and screening Look-Alike Sound-Alike collision risks.',
  },
  {
    id: 'explanation_synthesis',
    stepNumber: 7,
    label: 'Explanation & Posology Synthesis',
    tagline: 'Multilingual Natural Language Generation',
    description: 'Synthesizing verified clinical posology into accessible English, Hindi, and Marathi instructions.',
  },
];

export interface IPrescriptionService {
  getSamplePrescriptions(): Promise<PrescriptionSample[]>;
  getSampleById(sampleId: string): Promise<PrescriptionSample | null>;
  analyze(input: File | string, options?: AnalysisOptions): Promise<ResultsDemoState>;
  analyzePrescription(input: File | string, options?: AnalysisOptions): Promise<PrescriptionAnalysisResult>;
  analyzePrescriptionWithStream(
    input: File | string,
    options: AnalysisOptions,
    onProgress: (event: PipelineProgressEvent) => void
  ): Promise<PrescriptionAnalysisResult>;
  getLasaWarnings(): Promise<LasaWarning[]>;
  getExplanation(
    sampleId: string,
    language?: LanguageCode
  ): Promise<MultilingualExplanationPackage | null>;
  evaluateAbstention(
    entropy: number,
    threshold?: number
  ): { willAbstain: boolean; riskLevel: 'SAFE' | 'BORDERLINE' | 'CRITICAL_ABSTAIN' };
}

class PrescriptionService implements IPrescriptionService {
  private simulateDelay(ms: number = 400): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async getSamplePrescriptions(): Promise<PrescriptionSample[]> {
    await this.simulateDelay(100);
    return [...MOCK_PRESCRIPTION_SAMPLES];
  }

  async getSampleById(sampleId: string): Promise<PrescriptionSample | null> {
    await this.simulateDelay(80);
    const found = MOCK_PRESCRIPTION_SAMPLES.find((s) => s.id === sampleId);
    return found ? { ...found } : null;
  }

  /**
   * Primary high-level endpoint: Analyzes prescription and returns fully mapped ResultsDemoState
   */
  async analyze(input: File | string, options: AnalysisOptions = {}): Promise<ResultsDemoState> {
    const client = getPrescriptionApiClient();
    const responseDto = await client.analyzePrescription(input, {
      confidence_threshold: options.confidenceThreshold,
      enable_lasa_detection: options.enableLasaDetection,
      target_language: options.targetLanguage,
      mock_scenario: options.mockScenario,
    });
    return mapApiResponseToResultsState(responseDto);
  }

  /**
   * Traditional endpoint: Analyzes prescription and returns legacy PrescriptionAnalysisResult
   */
  async analyzePrescription(
    input: File | string,
    options: AnalysisOptions = {}
  ): Promise<PrescriptionAnalysisResult> {
    const client = getPrescriptionApiClient();
    const responseDto = await client.analyzePrescription(input, {
      confidence_threshold: options.confidenceThreshold,
      enable_lasa_detection: options.enableLasaDetection,
      target_language: options.targetLanguage,
      mock_scenario: options.mockScenario,
    });
    return mapApiResponseToAnalysisResult(responseDto);
  }

  /**
   * Streaming telemetry pipeline orchestrator:
   * Executes 7 transparent sequential stages, streams progress events, and grounds against the API client.
   */
  async analyzePrescriptionWithStream(
    input: File | string,
    options: AnalysisOptions = {},
    onProgress: (event: PipelineProgressEvent) => void
  ): Promise<PrescriptionAnalysisResult> {
    const speedMode = options.speedMode || 'normal';

    // Stage delay profiles in milliseconds
    const delays: Record<ProcessingSpeedMode, number> = {
      fast: 160,
      normal: 360,
      thorough: 720,
      simulate_error: 360,
    };
    const stepDelay = delays[speedMode];

    // Initialize 7 stages in pending state
    const stages: ProcessingStage[] = PIPELINE_STAGE_DEFINITIONS.map((def) => ({
      ...def,
      state: 'pending',
      progressPercent: 0,
      telemetryLogs: [],
    }));

    const liveTokens: LiveToken[] = [];
    const startTime = Date.now();

    const stageTokenGenerators: Record<ProcessingStageId, LiveToken[]> = {
      image_received: [
        {
          id: 'tok-1',
          type: 'DOCUMENT_PRECHECK',
          label: 'OPTICAL_STREAM',
          value: 'Bi-tonal Scan · 300 DPI Verified',
          confidence: 0.99,
          stageId: 'image_received',
          timestampMs: 120,
        },
      ],
      image_processing: [
        {
          id: 'tok-2',
          type: 'SEGMENT_POLYGON',
          label: 'DESKEW_AXIS',
          value: '0.4° Compensated · Margins Segmented',
          confidence: 0.98,
          stageId: 'image_processing',
          timestampMs: 380,
        },
      ],
      handwriting_interpretation: [
        {
          id: 'tok-3',
          type: 'CURSIVE_LIGATURE',
          label: 'LIGATURE_DECODE',
          value: 'Cross-Attention: Amox / Clav Cursive Token',
          confidence: 0.95,
          stageId: 'handwriting_interpretation',
          timestampMs: 820,
        },
      ],
      structured_extraction: [
        {
          id: 'tok-4',
          type: 'BRAND_NAME',
          label: 'MEDICINE_NAME',
          value: 'Augmentin 625 Duo Tablet',
          confidence: 0.96,
          stageId: 'structured_extraction',
          timestampMs: 1150,
        },
        {
          id: 'tok-5',
          type: 'POSOLOGY_FREQ',
          label: 'POSOLOGY_CODE',
          value: '1-0-1 PC (Morning & Night, Post Cibum)',
          confidence: 0.94,
          stageId: 'structured_extraction',
          timestampMs: 1320,
        },
      ],
      medicine_validation: [
        {
          id: 'tok-6',
          type: 'CDSCO_APPROVAL',
          label: 'CDSCO_FORMULARY',
          value: 'Approved Indian Schedule H Drug Combination',
          confidence: 0.99,
          stageId: 'medicine_validation',
          timestampMs: 1550,
        },
        {
          id: 'tok-7',
          type: 'RXNORM_ONTOLOGY',
          label: 'RXNORM_CUI',
          value: 'RxCUI: 213169 (Amoxicillin/Clavulanate)',
          confidence: 0.97,
          stageId: 'medicine_validation',
          timestampMs: 1680,
        },
      ],
      safety_analysis: [
        {
          id: 'tok-8',
          type: 'CALIBRATED_ENTROPY',
          label: 'CALIBRATED_GATE',
          value: 'Low Epistemic Entropy (0.14) → PASS_VERIFIED',
          confidence: 0.94,
          stageId: 'safety_analysis',
          timestampMs: 2050,
        },
        {
          id: 'tok-9',
          type: 'LASA_SCREENING',
          label: 'LASA_COLLISION',
          value: 'Clean (No Critical Look-Alike Confusions Detected)',
          confidence: 0.99,
          stageId: 'safety_analysis',
          timestampMs: 2200,
        },
      ],
      explanation_synthesis: [
        {
          id: 'tok-10',
          type: 'VERNACULAR_SCHEDULE',
          label: 'MULTILINGUAL_NLG',
          value: 'Synthesized: English · हिन्दी · मराठी Posology Cards',
          confidence: 0.98,
          stageId: 'explanation_synthesis',
          timestampMs: 2500,
        },
      ],
    };

    // Iterate through all 7 stages sequentially
    for (let i = 0; i < stages.length; i++) {
      const stage = stages[i];

      // Simulate failure if explicitly requested on stage 5
      if (speedMode === 'simulate_error' && i === 4) {
        stage.state = 'failed';
        stage.progressPercent = 45;
        stage.telemetryLogs.push('CDSCO Formulary Gateway Timeout (504)');

        onProgress({
          currentStageId: stage.id,
          overallPercent: Math.round(((i + 0.4) / stages.length) * 100),
          stages: [...stages],
          liveTokens: [...liveTokens],
          currentLogMessage: 'CDSCO Formulary Gateway connection timed out after 400ms.',
          activeModelHead: 'Ontology Graph Ingestion Head',
          elapsedTimeMs: Date.now() - startTime,
          isCompleted: false,
          hasError: true,
          errorMessage: 'CDSCO Pharmacopeia Gateway Timeout (504). Please retry or enable offline formulary cache.',
        });

        throw new ApiError('CDSCO Pharmacopeia Gateway Timeout (504)', 504);
      }

      // Mark stage as active
      stage.state = 'active';
      stage.progressPercent = 35;
      stage.telemetryLogs.push(`Activated ${stage.label}`);

      onProgress({
        currentStageId: stage.id,
        overallPercent: Math.round(((i + 0.3) / stages.length) * 100),
        stages: [...stages],
        liveTokens: [...liveTokens],
        currentLogMessage: `Executing ${stage.label}...`,
        activeModelHead: stage.tagline,
        elapsedTimeMs: Date.now() - startTime,
        isCompleted: false,
        hasError: false,
      });

      await this.simulateDelay(stepDelay);

      // Append generated tokens for this stage
      const newTokens = stageTokenGenerators[stage.id] || [];
      liveTokens.push(...newTokens);

      // Mark stage as completed
      stage.state = 'completed';
      stage.progressPercent = 100;
      stage.telemetryLogs.push(`Completed ${stage.label}`);

      onProgress({
        currentStageId: stage.id,
        overallPercent: Math.round(((i + 1) / stages.length) * 100),
        stages: [...stages],
        liveTokens: [...liveTokens],
        currentLogMessage: `Finished ${stage.label}`,
        activeModelHead: stage.tagline,
        elapsedTimeMs: Date.now() - startTime,
        isCompleted: i === stages.length - 1,
        hasError: false,
      });
    }

    // Call API client to retrieve the structured final result
    const client = getPrescriptionApiClient();
    const responseDto = await client.analyzePrescription(input, {
      confidence_threshold: options.confidenceThreshold,
      enable_lasa_detection: options.enableLasaDetection,
      target_language: options.targetLanguage,
      mock_scenario: options.mockScenario,
    });

    return mapApiResponseToAnalysisResult(responseDto);
  }

  async getLasaWarnings(): Promise<LasaWarning[]> {
    await this.simulateDelay(80);
    return [...CLINICAL_LASA_CATALOG];
  }

  async getExplanation(
    sampleId: string,
    language: LanguageCode = 'en'
  ): Promise<MultilingualExplanationPackage | null> {
    await this.simulateDelay(80);
    const samplePackage = MULTILINGUAL_EXPLANATIONS[sampleId];
    if (!samplePackage) return null;
    return samplePackage[language] || samplePackage.en;
  }

  evaluateAbstention(
    entropy: number,
    threshold: number = 0.65
  ): { willAbstain: boolean; riskLevel: 'SAFE' | 'BORDERLINE' | 'CRITICAL_ABSTAIN' } {
    if (entropy >= threshold) {
      return { willAbstain: true, riskLevel: 'CRITICAL_ABSTAIN' };
    }
    if (entropy >= threshold - 0.15) {
      return { willAbstain: false, riskLevel: 'BORDERLINE' };
    }
    return { willAbstain: false, riskLevel: 'SAFE' };
  }
}

export const prescriptionService = new PrescriptionService();
