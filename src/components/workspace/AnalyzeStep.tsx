import React, { useState, useEffect } from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import { PrescriptionAnalysisResult } from '../../types/prescription.types';
import { prescriptionService } from '../../services/prescriptionService';
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
  onAnalysisCompleted: (result: PrescriptionAnalysisResult) => void;
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
  const [isDone, setIsDone] = useState<boolean>(false);
  const [resultData, setResultData] = useState<PrescriptionAnalysisResult | null>(null);
  const [errorState, setErrorState] = useState<{
    title: string;
    message: string;
    code?: string;
  } | null>(null);
  const [retryTrigger, setRetryTrigger] = useState<number>(0);

  useEffect(() => {
    setErrorState(null);
    setIsDone(false);
    setProgressPercent(15);
    setActiveStageIdx(0);

    let currentIdx = 0;

    // Advance through the 5 human-readable stages smoothly
    const stageInterval = setInterval(() => {
      currentIdx += 1;
      if (currentIdx < humanStages.length) {
        setActiveStageIdx(currentIdx);
        setProgressPercent(Math.round(((currentIdx + 1) / humanStages.length) * 90));
      } else {
        clearInterval(stageInterval);
      }
    }, 1000);

    // Call service to get typed analysis result
    const sampleKey = uploadedData?.sampleId || 'rx-sample-1';
    const payload = uploadedData?.file || sampleKey;

    prescriptionService
      .analyzePrescription(payload, { confidenceThreshold: 0.65 })
      .then((res) => {
        setResultData(res);
        setActiveStageIdx(humanStages.length - 1);
        setProgressPercent(100);
        setIsDone(true);
      })
      .catch((err) => {
        clearInterval(stageInterval);
        setErrorState({
          title: 'Prescription Interpretation Gateway Notice',
          message:
            err?.message ||
            'The clinical interpretation gateway could not complete the request. Please inspect image clarity or verify network connectivity.',
          code: err?.code || 'PIPELINE_ERROR',
        });
      });

    return () => clearInterval(stageInterval);
  }, [uploadedData, retryTrigger]);

  const handleProceed = () => {
    if (resultData) {
      onAnalysisCompleted(resultData);
    }
  };

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Step Header */}
      <div className="max-w-3xl space-y-2.5">
        <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold tracking-tight text-theme-primary leading-[1.05]">
          Analyzing the prescription.
        </h1>
        <p className="text-lg sm:text-xl text-theme-secondary leading-[1.65]">
          Interpreting cursive handwriting, verifying medicine entities against official formularies, and screening for ambiguity.
        </p>
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
                  className="absolute inset-x-0 h-12 bg-gradient-to-b from-teal-500/10 via-teal-500/25 to-transparent pointer-events-none border-b-2 border-teal-500/50"
                />
              )}

              {/* Prescription Document Display */}
              {uploadedData?.source === 'user_upload' && uploadedData.previewUrl ? (
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
                          <div className="font-semibold text-teal-900 text-[11px]">
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
            <div className="mt-5 flex items-center gap-2 text-xs text-theme-secondary">
              {errorState ? (
                <>
                  <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                  <span className="font-semibold text-amber-800 dark:text-amber-300">
                    Analysis interrupted &middot; Diagnostic check required
                  </span>
                </>
              ) : !isDone ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-teal-500 animate-ping" />
                  <span>Processing handwriting trajectories...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span className="font-semibold text-emerald-800 dark:text-emerald-300">
                    Interpretation complete &middot; Ready for findings
                  </span>
                </>
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
                <p>1. Check that the prescription document has adequate contrast and lighting.</p>
                <p>2. Retry analysis to reconnect to the clinical grounding engine.</p>
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                <button
                  onClick={() => setRetryTrigger((r) => r + 1)}
                  className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
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
                  <span className="font-semibold text-teal-700 dark:text-teal-400">
                    {progressPercent}%
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-surface-subtle overflow-hidden border border-theme">
                  <div
                    style={{ width: `${progressPercent}%`, transition: 'width 0.4s ease-out' }}
                    className="h-full bg-teal-600 rounded-full"
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
                          <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                        ) : isCurrent ? (
                          <span className="w-4 h-4 flex items-center justify-center">
                            <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
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
                              ? 'font-bold text-teal-700 dark:text-teal-300'
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
                    className="w-full py-4 px-6 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-sm cursor-pointer group"
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
