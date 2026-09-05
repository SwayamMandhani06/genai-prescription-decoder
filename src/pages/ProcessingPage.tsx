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
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  ArrowLeft,
  ArrowRight,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  FileSearch,
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
  // Speed simulation profile: default normal (~3.2s)
  const [speedMode, setSpeedMode] = useState<ProcessingSpeedMode>('normal');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Telemetry stream state
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
    'Initializing optical intake sensor & bit-depth verification...'
  );
  const [activeModelHead, setActiveModelHead] = useState<string>(
    'Spatial Attention Pre-Screening'
  );
  const [elapsedTimeMs, setElapsedTimeMs] = useState<number>(0);
  const [finalResult, setFinalResult] = useState<PrescriptionAnalysisResult | null>(null);

  // Keep track of active run iteration to cancel stale async promises
  const runIterationRef = useRef<number>(0);

  // Narrative descriptions mapping for executive display
  const narrativeHeadlines: Record<ProcessingStageId, { title: string; narrative: string }> = {
    image_received: {
      title: 'Image Received & Optical Calibration',
      narrative: 'Validating pixel density, bi-tonal contrast ratio, and sensor orientation before inference.',
    },
    image_processing: {
      title: 'Normalization & Document Deskew',
      narrative: 'Compensating for perspective distortion, paper fold noise, and segmenting doctor letterhead.',
    },
    handwriting_interpretation: {
      title: 'Interpreting Physician Handwriting',
      narrative: 'Tokenizing cursive ligature sequences and extracting doctor pen strokes with cross-attention.',
    },
    structured_extraction: {
      title: 'Extracting Prescription Fields',
      narrative: 'Mapping recognized handwriting tokens into Brand Name, Salt Formulation, Dosage, and Posology.',
    },
    medicine_validation: {
      title: 'Formulary & Ontology Grounding',
      narrative: 'Verifying drug entity against CDSCO National Formulary and US NLM RxNorm knowledge graphs.',
    },
    safety_analysis: {
      title: 'Calibrated Uncertainty & LASA Screening',
      narrative: 'Computing epistemic entropy confidence score and cross-referencing Look-Alike Sound-Alike risks.',
    },
    explanation_synthesis: {
      title: 'Synthesizing Multilingual Explanation',
      narrative: 'Compiling verified clinical posology into accessible English, Hindi, and Marathi instructions.',
    },
  };

  const currentStageDef = stages.find((s) => s.id === currentStageId) || stages[0];
  const activeNarrative = narrativeHeadlines[currentStageId] || narrativeHeadlines.image_received;

  // Function to start or re-run the pipeline
  const runPipeline = useCallback(
    async (mode: ProcessingSpeedMode) => {
      const currentIteration = ++runIterationRef.current;

      setIsRunning(true);
      setIsCompleted(false);
      setHasError(false);
      setErrorMessage(null);
      setLiveTokens([]);
      setElapsedTimeMs(0);
      setOverallPercent(5);
      setCurrentStageId('image_received');

      // Reset stages to pending
      setStages(
        PIPELINE_STAGE_DEFINITIONS.map((def) => ({
          ...def,
          state: 'pending',
          progressPercent: 0,
          telemetryLogs: [],
        }))
      );

      const input = uploadedData?.file || uploadedData?.sampleId || 'rx-sample-1';

      try {
        const result = await prescriptionService.analyzePrescriptionWithStream(
          input,
          {
            speedMode: mode,
            confidenceThreshold: 0.65,
            enableLasaDetection: true,
            targetLanguage: 'en',
          },
          (event: PipelineProgressEvent) => {
            // Guard against stale asynchronous runs
            if (currentIteration !== runIterationRef.current) return;

            setCurrentStageId(event.currentStageId);
            setOverallPercent(event.overallPercent);
            setStages(event.stages);
            setLiveTokens(event.liveTokens);
            setCurrentLogMessage(event.currentLogMessage);
            setActiveModelHead(event.activeModelHead);
            setElapsedTimeMs(event.elapsedTimeMs);

            if (event.hasError) {
              setHasError(true);
              setErrorMessage(event.errorMessage || 'Pipeline inference encountered an error.');
            }
          }
        );

        if (currentIteration === runIterationRef.current) {
          setFinalResult(result);
          setIsCompleted(true);
          setIsRunning(false);
        }
      } catch (err: unknown) {
        if (currentIteration === runIterationRef.current) {
          setHasError(true);
          setIsRunning(false);
          const errorMsg =
            err instanceof Error
              ? err.message
              : 'Formulary gateway timed out during ontology grounding.';
          setErrorMessage(errorMsg);
        }
      }
    },
    [uploadedData]
  );

  // Auto-start pipeline on mount
  useEffect(() => {
    runPipeline(speedMode);

    return () => {
      // Invalidate running operations on unmount
      runIterationRef.current += 1;
    };
  }, [runPipeline, speedMode]);

  const handleSpeedModeChange = (newMode: ProcessingSpeedMode) => {
    setSpeedMode(newMode);
  };

  const handleRerun = () => {
    runPipeline(speedMode);
  };

  const handleProceedToFindings = () => {
    if (finalResult) {
      onComplete(finalResult);
    }
  };

  return (
    <div className="min-h-screen bg-[#07090E] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/25 selection:text-cyan-200">
      {/* Screen Reader Assistive Live Status */}
      <div role="status" aria-live="polite" className="sr-only">
        {hasError
          ? `Pipeline error: ${errorMessage}`
          : isCompleted
          ? `Pipeline completed. Prescription analysis verified. Ready to review findings.`
          : `Stage ${currentStageDef.stepNumber} of 7: ${currentStageDef.label}. ${activeNarrative.narrative}. Overall progress: ${overallPercent}%.`}
      </div>

      {/* Top Clinical Workstation Header */}
      <header className="sticky top-0 z-40 bg-[#0A0D15]/95 backdrop-blur-xl border-b border-white/[0.08] py-3 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToUpload}
              className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 hover:border-white/20 text-xs font-mono text-slate-300 hover:text-white transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Intake</span>
            </button>

            <span className="text-slate-700 hidden sm:inline">|</span>

            <div className="hidden sm:flex items-center gap-2">
              <span className="font-extrabold text-sm tracking-tight text-white font-mono">
                AURA<span className="text-cyan-400">-Rx</span>
              </span>
              <span className="text-xs text-slate-400 font-mono">
                / Multimodal Pipeline Telemetry
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {hasError ? (
              <Badge variant="coral" size="sm">
                <AlertTriangle className="w-3 h-3 inline mr-1 text-red-400" />
                Pipeline Halted (504)
              </Badge>
            ) : isCompleted ? (
              <Badge variant="emerald" size="sm">
                <ShieldCheck className="w-3 h-3 inline mr-1 text-emerald-400" />
                Analysis Verified (7/7)
              </Badge>
            ) : (
              <Badge variant="cyan" size="sm">
                <Cpu className="w-3 h-3 inline mr-1 text-cyan-400 animate-spin" />
                Node 0{currentStageDef.stepNumber}/07 Active
              </Badge>
            )}

            <div className="hidden md:flex items-center gap-2 text-xs font-mono text-slate-400 bg-black/40 px-3 py-1 rounded border border-white/5">
              <span>PROGRESS:</span>
              <span className="text-cyan-400 font-bold">{overallPercent}%</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Analysis Cockpit */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
        {/* Executive Narrative & Transparency Header */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-mono">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse motion-reduce:animate-none" />
                <span className="font-semibold uppercase tracking-wider">
                  Stage 0{currentStageDef.stepNumber}: {currentStageDef.label}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-sans transition-all duration-300">
                {activeNarrative.title}
              </h1>
            </div>

            {/* Quick Actions (Rerun / Complete) */}
            <div className="flex items-center gap-2.5">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRerun}
                disabled={isRunning}
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
              >
                Rerun Pipeline
              </Button>

              {isCompleted && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleProceedToFindings}
                  rightIcon={<ArrowRight className="w-4 h-4 text-slate-950" />}
                  className="shadow-lg shadow-cyan-500/20 animate-in fade-in"
                >
                  View Diagnostic Results
                </Button>
              )}
            </div>
          </div>

          <p className="text-sm text-slate-300 font-sans max-w-3xl leading-relaxed">
            {activeNarrative.narrative}
          </p>

          {/* Micro Telemetry Bar */}
          <div className="text-xs font-mono text-cyan-400/90 flex items-center gap-2">
            <span className="text-slate-500">&gt;</span>
            <span className="truncate">{currentLogMessage}</span>
          </div>
        </div>

        {/* Speed Profile Selector Controls */}
        <SimulationSpeedControls
          currentMode={speedMode}
          onModeChange={handleSpeedModeChange}
          disabled={isRunning}
        />

        {/* Error Simulation Banner if Pipeline Fails */}
        {hasError && (
          <div className="p-4 sm:p-5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-white font-mono">
                  Inference Halted: CDSCO Pharmacopeia Gateway Timeout (504)
                </h4>
                <p className="text-xs text-red-300/90 font-sans leading-relaxed">
                  {errorMessage || 'The simulated CDSCO formulary gateway timed out after 400ms.'}
                  To proceed, select Standard or Fast profile and retry the analysis pass.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSpeedMode('normal');
                  runPipeline('normal');
                }}
                className="w-full sm:w-auto text-xs"
              >
                Switch to Standard &amp; Retry
              </Button>
            </div>
          </div>
        )}

        {/* Completion Milestone Banner */}
        {isCompleted && !hasError && (
          <div className="p-4 sm:p-5 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-white font-mono">
                  Prescription Interpretation Complete &amp; Formularies Grounded
                </h4>
                <p className="text-xs text-emerald-300/90 font-sans leading-relaxed">
                  Verified against CDSCO India Schedule H and US NLM RxNorm. Calibrated uncertainty is safe (entropy &lt; 0.65 threshold). Multilingual posology synthesized in English, हिन्दी, and मराठी.
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={handleProceedToFindings}
              rightIcon={<ArrowRight className="w-4 h-4 text-slate-950" />}
              className="w-full sm:w-auto shadow-lg shadow-emerald-500/20 shrink-0"
            >
              Examine Structured Findings
            </Button>
          </div>
        )}

        {/* 2-Column Clinical Cockpit */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Live Document Scanner (7 cols on lg) */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between px-1 text-xs font-mono">
              <span className="text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <FileSearch className="w-3.5 h-3.5 text-cyan-400" />
                Optical Document Stage &amp; Active Scanhead
              </span>
              <span className="text-slate-500">
                RESOLUTION: {uploadedData?.metrics.width || 2100} &times;{' '}
                {uploadedData?.metrics.height || 2800} PX
              </span>
            </div>

            <LiveDocumentScanner
              uploadedData={uploadedData}
              currentStageId={currentStageId}
              overallPercent={overallPercent}
            />

            {/* Document Quality Telemetry Strip */}
            <div className="p-3 rounded-lg bg-[#0A0E18] border border-white/[0.06] grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">ORIENTATION</span>
                <span className="text-slate-200 font-bold">
                  {uploadedData?.metrics.orientation || 'Portrait'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">READABILITY</span>
                <span className="text-emerald-400 font-bold">
                  {uploadedData?.metrics.readabilityScore || 92}/100
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">CONTRAST</span>
                <span className="text-cyan-300 font-bold">
                  {uploadedData?.metrics.contrastScore || 'High'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block uppercase">EST. DPI</span>
                <span className="text-slate-300 font-bold">
                  {uploadedData?.metrics.estimatedDpi || 300} DPI
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Pipeline Stages Telemetry & Live Recognized Tokens (5 cols on lg) */}
          <div className="lg:col-span-5 space-y-4">
            <PipelineStagesTelemetry
              stages={stages}
              currentStageId={currentStageId}
              liveTokens={liveTokens}
              elapsedTimeMs={elapsedTimeMs}
              activeModelHead={activeModelHead}
            />
          </div>
        </div>

        {/* Bottom Educational / Architectural Transparency Callout */}
        <div className="p-4 rounded-xl bg-[#090D17] border border-white/[0.08] flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs font-sans text-slate-400">
          <div className="space-y-1">
            <span className="font-mono text-cyan-400 font-bold tracking-wide block">
              RESEARCH ARCHITECTURE NOTE · WHY 7 STAGES?
            </span>
            <p className="leading-relaxed text-slate-300">
              Unlike generic chatbot LLMs that guess illegible doctor shorthand directly from raw pixels, AURA-Rx decomposes prescription decoding into an audited sequential graph: isolating cursive ligatures, validating candidates against CDSCO formularies, and calibrating epistemic entropy to explicitly abstain on dangerous ambiguities.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};
