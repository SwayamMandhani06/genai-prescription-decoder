import React, { useState, useEffect, useRef, useCallback } from 'react';
import { UploadedPrescriptionFile } from '../types/navigation.types';
import {
  ProcessingStage,
  ProcessingStageId,
  LiveToken,
  ProcessingSpeedMode,
  PipelineProgressEvent,
} from '../types/pipeline.types';
import { PrescriptionAnalysisResult } from '../types/prescription.types';
import {
  prescriptionService,
  PIPELINE_STAGE_DEFINITIONS,
} from '../services/prescriptionService';
import { LiveDocumentScanner } from '../components/processing/LiveDocumentScanner';
import { PipelineStagesTelemetry } from '../components/processing/PipelineStagesTelemetry';
import { SimulationSpeedControls } from '../components/processing/SimulationSpeedControls';
import { ThemeSwitcher } from '../components/layout/ThemeSwitcher';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  ArrowLeft,
  ArrowRight,
  RotateCcw,
  AlertTriangle,
  ShieldCheck,
  Cpu,
} from 'lucide-react';

export interface ProcessingPageProps {
  uploadedData: UploadedPrescriptionFile | null;
  onBackToUpload: () => void;
  onComplete: (result: PrescriptionAnalysisResult) => void;
}

export const ProcessingPage: React.FC<ProcessingPageProps> = ({
  uploadedData,
  onBackToUpload,
  onComplete,
}) => {
  const [speedMode, setSpeedMode] = useState<ProcessingSpeedMode>('normal');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [currentStageId, setCurrentStageId] = useState<ProcessingStageId>('image_received');
  const [overallPercent, setOverallPercent] = useState<number>(5);
  const [stages, setStages] = useState<ProcessingStage[]>(() =>
    PIPELINE_STAGE_DEFINITIONS.map((def) => ({
      ...def,
      state: 'pending',
      progressPercent: 0,
      telemetryLogs: [],
    }))
  );
  const [liveTokens, setLiveTokens] = useState<LiveToken[]>([]);
  const [currentLogMessage, setCurrentLogMessage] = useState<string>(
    'Verifying document resolution and contrast...'
  );
  const [activeModelHead, setActiveModelHead] = useState<string>(
    'Document Spatial Alignment'
  );
  const [elapsedTimeMs, setElapsedTimeMs] = useState<number>(0);
  const [finalResult, setFinalResult] = useState<PrescriptionAnalysisResult | null>(null);

  const runIterationRef = useRef<number>(0);

  const narrativeHeadlines: Record<ProcessingStageId, { title: string; narrative: string }> = {
    image_received: {
      title: 'Prescription Image Loaded',
      narrative:
        'Validating document orientation, resolution, and edge contrast before passing to the multimodal vision architecture.',
    },
    image_processing: {
      title: 'Compensating Document Surface',
      narrative:
        'Removing paper shadows, background grid artifacts, and letterhead stamps to isolate doctor ink strokes.',
    },
    handwriting_interpretation: {
      title: 'Interpreting Cursive Handwriting',
      narrative:
        'Multimodal vision-language models trace ink trajectory paths and translate clinical shorthand.',
    },
    structured_extraction: {
      title: 'Extracting Prescription Fields',
      narrative:
        'Mapping recognized handwriting tokens into posology slots: medicine, dosage strength, frequency, and duration.',
    },
    medicine_validation: {
      title: 'Verifying with Clinical Formularies',
      narrative:
        'Matching extracted candidates against official CDSCO and RxNorm pharmacopeia catalogs.',
    },
    safety_analysis: {
      title: 'Safety Checks & Epistemic Calibration',
      narrative:
        'Screening for Look-Alike Sound-Alike risks and evaluating uncertainty to flag ambiguity.',
    },
    explanation_synthesis: {
      title: 'Preparing Plain-Language Explanations',
      narrative:
        'Formulating patient-friendly instructions with schedules and precautions in English, Hindi, and Marathi.',
    },
  };

  const startPipelineExecution = useCallback(() => {
    runIterationRef.current += 1;
    const iterationId = runIterationRef.current;

    setIsRunning(true);
    setIsCompleted(false);
    setHasError(false);
    setErrorMessage(null);
    setFinalResult(null);
    setLiveTokens([]);
    setOverallPercent(5);
    setCurrentStageId('image_received');

    setStages(
      PIPELINE_STAGE_DEFINITIONS.map((def) => ({
        ...def,
        state: 'pending',
        progressPercent: 0,
        telemetryLogs: [],
      }))
    );

    const startTime = Date.now();
    const timerInterval = setInterval(() => {
      setElapsedTimeMs(Date.now() - startTime);
    }, 100);

    const sampleKey = uploadedData?.sampleId || 'rx-sample-1';
    const payload = uploadedData?.file || sampleKey;

    const subscription = prescriptionService.analyzePrescriptionWithStream(
      payload,
      { speedMode },
      (event: PipelineProgressEvent) => {
        if (iterationId !== runIterationRef.current) return;

        setCurrentStageId(event.currentStageId);
        setOverallPercent(event.overallPercent);
        setCurrentLogMessage(event.currentLogMessage);
        setActiveModelHead(event.activeModelHead);
        setStages(event.stages);
        setLiveTokens(event.liveTokens);
      }
    );

    subscription
      .then((result: PrescriptionAnalysisResult) => {
        if (iterationId !== runIterationRef.current) return;

        clearInterval(timerInterval);
        setIsRunning(false);
        setIsCompleted(true);
        setOverallPercent(100);
        setFinalResult(result);

        setStages((prev) =>
          prev.map((s) => ({
            ...s,
            state: 'completed',
            progressPercent: 100,
          }))
        );
      })
      .catch((err: Error) => {
        if (iterationId !== runIterationRef.current) return;

        clearInterval(timerInterval);
        setIsRunning(false);
        setHasError(true);
        setErrorMessage(err.message || 'Pipeline analysis execution failed.');

        setStages((prev) =>
          prev.map((s) => {
            if (s.id === currentStageId) {
              return { ...s, state: 'failed' };
            }
            return s;
          })
        );
      });

    return () => {
      clearInterval(timerInterval);
    };
  }, [speedMode, uploadedData, currentStageId]);

  useEffect(() => {
    const cancel = startPipelineExecution();
    return () => {
      if (cancel) cancel();
    };
  }, [speedMode]);

  const handleRerun = () => {
    startPipelineExecution();
  };

  const handleProceedToFindings = () => {
    if (finalResult) {
      onComplete(finalResult);
    }
  };

  const currentStageDef =
    PIPELINE_STAGE_DEFINITIONS.find((d) => d.id === currentStageId) ||
    PIPELINE_STAGE_DEFINITIONS[0];
  const activeNarrative = narrativeHeadlines[currentStageId] || narrativeHeadlines.image_received;

  return (
    <div className="min-h-screen bg-canvas text-theme-primary flex flex-col font-sans transition-colors">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-theme py-3 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToUpload}
              className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface border border-theme text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Intake</span>
            </button>

            <span className="text-theme-muted hidden sm:inline">|</span>

            <div className="hidden sm:flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-theme-primary">
                AURA-Rx
              </span>
              <span className="text-xs text-theme-muted">
                / Processing Workflow
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ThemeSwitcher />

            {hasError ? (
              <Badge variant="coral" size="sm">
                <AlertTriangle className="w-3 h-3 inline mr-1" />
                Error (504)
              </Badge>
            ) : isCompleted ? (
              <Badge variant="emerald" size="sm">
                <ShieldCheck className="w-3 h-3 inline mr-1" />
                Analysis Complete
              </Badge>
            ) : (
              <Badge variant="cyan" size="sm">
                <Cpu className="w-3 h-3 inline mr-1 animate-spin" />
                Stage 0{currentStageDef.stepNumber}/07 Active
              </Badge>
            )}

            <div className="hidden md:flex items-center gap-1.5 text-xs text-theme-secondary bg-surface-subtle px-3 py-1 rounded-lg border border-theme">
              <span>Progress:</span>
              <span className="text-teal-700 dark:text-teal-400 font-bold font-mono">{overallPercent}%</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Analysis Stage */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
        {hasError && errorMessage && (
          <div className="p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 text-xs rounded-xl flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
        {/* Narrative Header */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
                <span>
                  Stage 0{currentStageDef.stepNumber}: {currentStageDef.label}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-theme-primary tracking-tight">
                {activeNarrative.title}
              </h1>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2.5">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRerun}
                disabled={isRunning}
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
              >
                Rerun
              </Button>

              {isCompleted && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleProceedToFindings}
                  rightIcon={<ArrowRight className="w-4 h-4 text-white" />}
                >
                  View Prescription Findings
                </Button>
              )}
            </div>
          </div>

          <p className="text-sm text-theme-secondary max-w-3xl leading-relaxed">
            {activeNarrative.narrative}
          </p>

          <div className="text-xs text-theme-muted flex items-center gap-2">
            <span>&gt;</span>
            <span className="truncate">{currentLogMessage}</span>
          </div>
        </div>

        {/* 2-Column Processing Cockpit */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Live Document Scanner */}
          <div className="lg:col-span-7">
            <LiveDocumentScanner
              uploadedData={uploadedData}
              currentStageId={currentStageId}
              overallPercent={overallPercent}
            />
          </div>

          {/* Right Column: Pipeline Stages & Telemetry */}
          <div className="lg:col-span-5 space-y-4">
            <PipelineStagesTelemetry
              stages={stages}
              currentStageId={currentStageId}
              liveTokens={liveTokens}
              elapsedTimeMs={elapsedTimeMs}
              activeModelHead={activeModelHead}
            />

            {/* Simulation Speed Simulator */}
            <SimulationSpeedControls
              currentMode={speedMode}
              onModeChange={setSpeedMode}
              disabled={isRunning}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
