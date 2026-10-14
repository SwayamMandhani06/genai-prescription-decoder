import React, { useState, useEffect, useRef } from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import { PrescriptionAnalysisResult, ResultsDemoState } from '../../types/prescription.types';
import { prescriptionService } from '../../services/prescriptionService';
import { apiConfig } from '../../services/api/apiConfig';
import { ApiTimeoutError } from '../../services/api/apiErrors';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import {
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  RotateCcw,
  AlertCircle,
  AlertTriangle,
} from 'lucide-react';

export interface AnalyzeStepProps {
  uploadedData: UploadedPrescriptionFile | null;
  rotation: number;
  onAnalysisCompleted: (result: PrescriptionAnalysisResult, demoState?: ResultsDemoState) => void;
  onBackToReview?: () => void;
}

export const AnalyzeStep: React.FC<AnalyzeStepProps> = ({
  uploadedData,
  rotation,
  onAnalysisCompleted,
  onBackToReview,
}) => {
  // 5 Human-readable stages specified by prompt:
  const humanStages = [
    { id: 'reading', label: 'Reading the prescription', desc: 'Isolating doctor penmanship and paper structure.' },
    { id: 'identifying', label: 'Identifying written fields', desc: 'Separating drug name, strength, frequency, and duration.' },
    { id: 'checking', label: 'Checking medicine candidates', desc: 'Cross-referencing CDSCO and RxNorm pharmacopeias.' },
    { id: 'assessing', label: 'Assessing uncertainty', desc: 'Screening for Look-Alike Sound-Alike risks and low-confidence ink.' },
    { id: 'preparing', label: 'Preparing explanation', desc: 'Translating posology into plain English, Hindi, and Marathi.' },
  ];

  const [activeStageIdx, setActiveStageIdx] = useState<number>(0);
  const [progressPercent, setProgressPercent] = useState<number>(15);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [isDone, setIsDone] = useState<boolean>(false);
  const [resultData, setResultData] = useState<PrescriptionAnalysisResult | null>(null);
  const [demoState, setDemoState] = useState<ResultsDemoState | null>(null);
  const [errorState, setErrorState] = useState<{
    title: string;
    message: string;
    code?: string;
    isTimeout?: boolean;
    isOverloaded?: boolean;
  } | null>(null);
  const [retryTrigger, setRetryTrigger] = useState<number>(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!uploadedData) return;

    // Abort any existing in-flight request before starting a new run
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setErrorState(null);
    setIsDone(false);
    setProgressPercent(15);
    setActiveStageIdx(0);
    setElapsedSeconds(0);

    const startTime = Date.now();

    // Advance stages and progress smoothly across realistic multimodal analysis duration
    const timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setElapsedSeconds(elapsed);

      if (elapsed < 4) {
        setActiveStageIdx(0);
        setProgressPercent(Math.min(25, Math.round(15 + elapsed * 2.5)));
      } else if (elapsed < 12) {
        setActiveStageIdx(1);
        setProgressPercent(Math.min(48, Math.round(26 + (elapsed - 4) * 2.8)));
      } else if (elapsed < 24) {
        setActiveStageIdx(2);
        setProgressPercent(Math.min(70, Math.round(50 + (elapsed - 12) * 1.7)));
      } else if (elapsed < 38) {
        setActiveStageIdx(3);
        setProgressPercent(Math.min(85, Math.round(71 + (elapsed - 24) * 1.0)));
      } else {
        setActiveStageIdx(4);
        // Asymptotically approach 94% until the real response arrives
        setProgressPercent(Math.min(94, Math.round(86 + (elapsed - 38) * 0.4)));
      }
    }, 1000);

    // Call service to get typed analysis result and UI domain state
    const sampleKey = uploadedData?.sampleId || 'rx-sample-1';
    const payload = uploadedData?.file || sampleKey;

    prescriptionService
      .analyzeWithFullState(payload, {
        confidenceThreshold: 0.65,
        signal: controller.signal,
      })
      .then(({ result, demoState: fullState }) => {
        if (controller.signal.aborted) return;
        clearInterval(timer);
        setResultData(result);
        setDemoState(fullState);
        setActiveStageIdx(humanStages.length - 1);
        setProgressPercent(100);
        setIsDone(true);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        clearInterval(timer);

        const isTimeout =
          err instanceof ApiTimeoutError ||
          err?.statusCode === 504 ||
          (typeof err?.message === 'string' &&
            (err.message.toLowerCase().includes('timed out') ||
              err.message.toLowerCase().includes('timeout') ||
              err.message.includes('504')));

        const isOverloaded =
          err?.statusCode === 503 ||
          (typeof err?.message === 'string' &&
            (err.message.includes('503') ||
              err.message.toLowerCase().includes('high demand') ||
              err.message.toLowerCase().includes('temporarily unavailable')));

        const isDocumentRejected =
          err?.statusCode === 422 ||
          err?.code === 'DOCUMENT_NOT_PRESCRIPTION' ||
          err?.code === 'IMAGE_QUALITY_INSUFFICIENT' ||
          (typeof err?.message === 'string' &&
            (err.message.toLowerCase().includes('not appear to be a medical prescription') ||
              err.message.toLowerCase().includes('not a medical prescription') ||
              err.message.toLowerCase().includes('landscape') ||
              err.message.toLowerCase().includes('receipt') ||
              err.message.toLowerCase().includes('blank') ||
              err.message.toLowerCase().includes('packaging') ||
              err.message.toLowerCase().includes('portrait') ||
              err.message.toLowerCase().includes('selfie') ||
              err.message.toLowerCase().includes('food') ||
              err.message.toLowerCase().includes('animal')));

        if (isDocumentRejected) {
          setErrorState({
            title: 'Image Rejected: Not a Medical Prescription',
            message:
              err?.message ||
              'The uploaded image was inspected by the clinical vision pipeline and rejected because it does not appear to be an authentic doctor prescription. To protect medical safety, no medications were extracted.',
            code: 'DOCUMENT_REJECTED_422',
            isRejected: true,
          } as any);
        } else if (isTimeout) {
          setErrorState({
            title: 'Prescription Analysis Timed Out (Gateway 504)',
            message:
              'The live Gemini multimodal vision model took longer than the configured 60-second limit to decode the handwriting. This can occur during temporary upstream demand spikes or for complex cursive scripts. The original document has been preserved.',
            code: 'GATEWAY_TIMEOUT_504',
            isTimeout: true,
          });
        } else if (isOverloaded) {
          setErrorState({
            title: 'Multimodal AI Model Under High Demand (503)',
            message:
              'Google Gemini is currently experiencing temporary high demand spikes. Your prescription document has been securely kept in memory. Please click Retry Analysis to reconnect.',
            code: 'MODEL_UNAVAILABLE_503',
            isOverloaded: true,
          });
        } else {
          setErrorState({
            title: 'Prescription Interpretation Gateway Notice',
            message:
              err?.message ||
              'The clinical interpretation gateway could not complete the request. Please inspect image clarity or verify network connectivity.',
            code: err?.code || 'PIPELINE_ERROR',
          });
        }
      });

    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [uploadedData, retryTrigger]);

  const handleRetry = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setErrorState(null);
    setRetryTrigger((r) => r + 1);
  };

  const handleProceed = () => {
    if (resultData) {
      onAnalysisCompleted(resultData, demoState || undefined);
    }
  };

  if (!uploadedData) {
    return (
      <div className="max-w-4xl mx-auto w-full px-4 py-12 text-center space-y-4">
        <h2 className="text-2xl font-bold text-theme-primary">No Prescription Mounted</h2>
        <p className="text-theme-secondary text-sm">Please select or upload a prescription file to analyze.</p>
        <button
          onClick={onBackToReview}
          className="px-5 py-2.5 rounded-xl bg-primary text-primary-contrast font-medium text-sm cursor-pointer"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="max-w-3xl space-y-2.5">
          <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold tracking-tight text-theme-primary leading-[1.05]">
            Analyzing the prescription.
          </h1>
          <p className="text-lg sm:text-xl text-theme-secondary leading-[1.65]">
            Interpreting cursive handwriting, verifying medicine entities against official formularies, and screening for ambiguity.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium border border-theme bg-surface shrink-0 self-start sm:self-auto shadow-xs">
          <span className={`w-2.5 h-2.5 rounded-full ${apiConfig.useMock ? 'bg-[#155EEF]' : 'bg-emerald-500 animate-pulse'}`} />
          <span className="text-theme-secondary">
            {apiConfig.useMock ? 'Demonstration Mock Mode' : 'Live FastAPI Backend (Port 8001)'}
          </span>
        </div>
      </div>

      {/* Main Analysis Cockpit */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Document Scan Visual (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="relative rounded-3xl border border-theme bg-surface/40 p-6 sm:p-8 flex flex-col items-center justify-center min-h-[460px] overflow-hidden">
            {/* The Document Canvas */}
            <div
              style={{
                transform: `rotate(${rotation}deg)`,
                transition: 'transform 0.25s ease-out',
              }}
              className="max-w-md w-full prescription-paper shadow-paper rounded-2xl p-6 sm:p-7 border border-theme relative overflow-hidden"
            >
              {/* Subtle Scanning Beam Passing Over Document */}
              {!isDone && (
                <div
                  style={{
                    top: `${(activeStageIdx + 1) * 18}%`,
                    transition: 'top 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}
                  className="absolute inset-x-0 h-12 bg-gradient-to-b from-[#155EEF]/10 via-[#155EEF]/25 to-transparent pointer-events-none border-b-2 border-[#155EEF]/70 shadow-[0_4px_12px_rgba(21,94,239,0.3)]"
                />
              )}

              {/* Prescription Document Display */}
              {uploadedData?.previewUrl ? (
                <div className="flex flex-col items-center">
                  <img
                    src={uploadedData.previewUrl}
                    alt="Prescription Document Under Analysis"
                    className="w-full max-h-[380px] object-contain rounded-lg shadow-xs"
                  />
                  <div className="pt-2 text-[10px] text-slate-600 font-mono text-center">
                    {uploadedData.fileName}
                  </div>
                </div>
              ) : (
                (() => {
                  const activeCanvas =
                    SAMPLE_PRESCRIPTION_CANVASES[uploadedData?.sampleId || 'rx-sample-1'] ||
                    SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];
                  return (
                    <div className="space-y-4 text-slate-900">
                      <div className="border-b border-slate-300 pb-2 flex justify-between items-start text-xs">
                        <div>
                          <div className="font-semibold text-[#102A43] text-[11px]">
                            {activeCanvas.doctorHeader.clinicName}
                          </div>
                          <div className="font-bold text-slate-900 text-xs">
                            {activeCanvas.doctorHeader.name}
                          </div>
                        </div>
                        <span className="text-[11px] text-slate-600 font-mono">
                          {activeCanvas.accessionId}
                        </span>
                      </div>

                      <div className="text-xl font-serif italic font-bold text-slate-900">℞</div>

                      {/* Handwriting Lines */}
                      <div className="space-y-3 py-1.5">
                        {activeCanvas.strokes.map((stroke) => (
                          <div key={stroke.id} className="border-b border-slate-200 pb-2">
                            <div
                              className="font-serif italic text-sm sm:text-base font-bold leading-relaxed"
                              style={{ color: stroke.inkColor }}
                            >
                              {stroke.label}
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="pt-2 border-t border-slate-300 flex justify-between items-center text-[10px] text-slate-600">
                        <span>Patient: {activeCanvas.patientInfo.name} ({activeCanvas.patientInfo.ageGender})</span>
                        <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-200/80">
                          {activeCanvas.clinicStampText}
                        </span>
                      </div>
                    </div>
                  );
                })()
              )}
            </div>

            {/* Reassuring Status Indicator */}
            <div className="mt-5 flex items-center justify-between w-full max-w-md text-xs text-theme-secondary px-2">
              <div className="flex items-center gap-2">
                {errorState ? (
                  <>
                    <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                    <span className="font-semibold text-amber-800 dark:text-amber-300">
                      {errorState.isTimeout
                        ? 'Gateway timeout (504) · Retry available'
                        : errorState.isOverloaded
                        ? 'High demand spike (503) · Retry available'
                        : 'Analysis interrupted · Diagnostic check required'}
                    </span>
                  </>
                ) : !isDone ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-[#155EEF] animate-ping shrink-0" />
                    <span className="truncate">
                      {elapsedSeconds < 10
                        ? 'Scanning handwriting ink trajectories...'
                        : elapsedSeconds < 25
                        ? 'Deciphering cursive script with multimodal vision AI...'
                        : elapsedSeconds < 40
                        ? 'Grounding medicines against CDSCO & RxNorm...'
                        : 'Synthesizing verified posology explanation...'}
                    </span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    <span className="font-semibold text-emerald-800 dark:text-emerald-300">
                      Interpretation complete &middot; Ready for findings
                    </span>
                  </>
                )}
              </div>

              {!errorState && !isDone && (
                <span className="text-[11px] font-mono text-theme-muted shrink-0 ml-2">
                  {elapsedSeconds}s / 60s
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: 5 Stages as Typographic Flow (5 cols) */}
        <div className="lg:col-span-5 space-y-6 pt-2">
          {errorState ? (
            /* Explicit Failure / Error State with Guided Recovery */
            <div className="p-6 rounded-2xl bg-amber-50/80 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 space-y-4 animate-in fade-in">
              <div className="flex items-center gap-3 text-amber-900 dark:text-amber-200">
                <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0" />
                <h3 className="font-bold text-base sm:text-lg">{errorState.title}</h3>
              </div>

              <p className="text-sm text-amber-900 dark:text-amber-200 leading-relaxed">
                {errorState.message}
              </p>

              <div className="p-3 rounded-lg bg-surface/70 border border-theme text-xs text-theme-secondary space-y-1">
                <strong className="text-theme-primary block">Recommended next steps:</strong>
                {(errorState as any).isRejected ? (
                  <>
                    <p>1. Ensure you are uploading an authentic doctor prescription pad, clinic Rx slip, or hospital discharge order.</p>
                    <p>2. Do not upload commercial receipts, personal photos, landscape scenes, or medication packaging without a prescription.</p>
                    <p>3. Click &ldquo;Back to Review&rdquo; or re-upload a clear photograph of an authentic medical prescription.</p>
                  </>
                ) : errorState.isTimeout ? (
                  <>
                    <p>1. Click &ldquo;Retry Analysis&rdquo; below to send a fresh request to the multimodal inference worker.</p>
                    <p>2. If handwriting is heavily smudged or faint, click &ldquo;Back to Review&rdquo; to adjust contrast or rotation.</p>
                  </>
                ) : errorState.isOverloaded ? (
                  <>
                    <p>1. Google Gemini experienced a brief demand spike; waiting a moment and clicking &ldquo;Retry Analysis&rdquo; usually succeeds.</p>
                    <p>2. Your prescription image remains loaded in your browser session.</p>
                  </>
                ) : (
                  <>
                    <p>1. Check that the prescription document has adequate contrast and lighting.</p>
                    <p>2. Retry analysis to reconnect to the clinical grounding engine.</p>
                  </>
                )}
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                <button
                  onClick={handleRetry}
                  className="w-full sm:w-auto px-6 py-2.5 rounded-full bg-gradient-to-r from-[#155EEF] to-[#2E90FA] hover:from-[#1249C7] hover:to-[#155EEF] text-white text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs hover:shadow-sm"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Retry Analysis</span>
                </button>

                {onBackToReview && (
                  <button
                    onClick={onBackToReview}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary hover:text-theme-primary text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back to Review</span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <>
              {/* Progress Indicator */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-theme-secondary">
                    Progress
                  </span>
                  <span className="font-semibold text-[#155EEF] dark:text-[#4B8BFF]">
                    {progressPercent}%
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-surface-subtle overflow-hidden border border-theme">
                  <div
                    style={{ width: `${progressPercent}%`, transition: 'width 0.4s ease-out' }}
                    className="h-full bg-gradient-to-r from-[#155EEF] to-[#2E90FA] rounded-full"
                  />
                </div>
              </div>

              {/* Continuous Typographic Stage List */}
              <div className="space-y-4 pt-2">
                {humanStages.map((stage, idx) => {
                  const isCurrent = idx === activeStageIdx && !isDone;
                  const isPassed = idx < activeStageIdx || isDone;

                  return (
                    <div
                      key={stage.id}
                      className={`flex items-start gap-3 transition-opacity ${
                        isCurrent
                          ? 'opacity-100'
                          : isPassed
                          ? 'opacity-90'
                          : 'opacity-40'
                      }`}
                    >
                      <div className="mt-0.5 shrink-0">
                        {isPassed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        ) : isCurrent ? (
                          <span className="w-4 h-4 flex items-center justify-center">
                            <span className="w-2 h-2 rounded-full bg-[#155EEF] animate-pulse" />
                          </span>
                        ) : (
                          <span className="w-4 h-4 flex items-center justify-center text-[11px] text-theme-muted">
                            {idx + 1}
                          </span>
                        )}
                      </div>

                      <div className="space-y-0.5">
                        <h4
                          className={`text-base sm:text-lg ${
                            isCurrent
                              ? 'font-bold text-[#155EEF] dark:text-[#4B8BFF]'
                              : isPassed
                              ? 'font-bold text-theme-primary'
                              : 'font-medium text-theme-secondary'
                          }`}
                        >
                          {stage.label}
                        </h4>
                        <p className="text-sm text-theme-secondary leading-[1.6]">
                          {stage.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Primary Action Button */}
              {isDone && (
                <div className="pt-4 border-t border-theme animate-in fade-in duration-300">
                  <button
                    onClick={handleProceed}
                    className="w-full py-4 px-6 rounded-full bg-gradient-to-r from-[#155EEF] to-[#2E90FA] hover:from-[#1249C7] hover:to-[#155EEF] text-white text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0 cursor-pointer group"
                  >
                    <ShieldCheck className="w-5 h-5" />
                    <span>View Findings &amp; Interpretation</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              )}

              {/* Quiet Formulary Reassurance */}
              <p className="text-xs sm:text-sm text-theme-muted pt-2 leading-[1.6]">
                Grounded against CDSCO National Essential Medicines and US NLM RxNorm formularies.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
