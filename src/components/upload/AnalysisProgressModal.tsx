import React, { useEffect, useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  CheckCircle2,
  Database,
  ShieldAlert,
  Layers,
  ArrowRight,
  FileCheck2,
} from 'lucide-react';
import { PrescriptionAnalysisResult } from '../../types/prescription.types';

export interface AnalysisProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisResult: PrescriptionAnalysisResult | null;
  onViewResults: (result: PrescriptionAnalysisResult) => void;
}

export const AnalysisProgressModal: React.FC<AnalysisProgressModalProps> = ({
  isOpen,
  onClose,
  analysisResult,
  onViewResults,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(0);

  const steps = [
    {
      label: 'Optical Normalization & Layout Segments',
      desc: 'Compensating for document skew, paper grain, and clinical letterhead watermark.',
      icon: Layers,
    },
    {
      label: 'BioClinical NER & Posology Tokenization',
      desc: 'Segmenting cursive handwritten ligatures into Brand, Dosage Strength, and Frequency.',
      icon: FileCheck2,
    },
    {
      label: 'CDSCO & RxNorm Pharmacopeia Grounding',
      desc: 'Matching extracted drug entities against 45,000+ approved clinical monographs.',
      icon: Database,
    },
    {
      label: 'Uncertainty Calibration & LASA Screening',
      desc: 'Measuring token predictive entropy; verifying Look-Alike Sound-Alike collision risk.',
      icon: ShieldAlert,
    },
  ];

  // Animate through steps when open
  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(0);
      return;
    }

    const t1 = setTimeout(() => setCurrentStep(1), 300);
    const t2 = setTimeout(() => setCurrentStep(2), 650);
    const t3 = setTimeout(() => setCurrentStep(3), 1000);
    const t4 = setTimeout(() => setCurrentStep(4), 1350);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const isComplete = currentStep >= 4 && analysisResult !== null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={isComplete ? onClose : () => {}}
      title="Multimodal Diagnostic Pipeline"
      subtitle="Executing Swin-Doc layout transformer, CDSCO ontology grounding, and selective prediction gate."
      maxWidth="xl"
    >
      <div className="space-y-6 py-2">
        {/* Progress Bar Container */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400">
              {isComplete ? 'INFERENCE COMPLETE' : 'INFERENCE IN PROGRESS...'}
            </span>
            <span className="text-cyan-400 font-bold">
              {Math.min(100, Math.round((currentStep / 4) * 100))}%
            </span>
          </div>

          <div className="w-full h-2 rounded-full bg-slate-950 border border-white/10 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 transition-all duration-300 ease-out"
              style={{ width: `${Math.min(100, (currentStep / 4) * 100)}%` }}
            />
          </div>
        </div>

        {/* Steps List */}
        <div className="space-y-3 font-mono text-xs">
          {steps.map((step, idx) => {
            const isStepActive = currentStep === idx;
            const isStepDone = currentStep > idx;
            const StepIcon = step.icon;

            return (
              <div
                key={step.label}
                className={`p-3 rounded-lg border transition-all flex items-start gap-3 ${
                  isStepDone
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : isStepActive
                    ? 'bg-cyan-950/30 border-cyan-500/50 shadow-sm'
                    : 'bg-black/20 border-white/[0.04] opacity-50'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isStepDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isStepActive ? (
                    <StepIcon className="w-4 h-4 text-cyan-400 animate-pulse" />
                  ) : (
                    <StepIcon className="w-4 h-4 text-slate-500" />
                  )}
                </div>

                <div className="space-y-0.5 flex-1">
                  <div className="flex items-center justify-between">
                    <span
                      className={`font-bold ${
                        isStepDone
                          ? 'text-emerald-300'
                          : isStepActive
                          ? 'text-cyan-300'
                          : 'text-slate-400'
                      }`}
                    >
                      {step.label}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {isStepDone ? 'DONE' : isStepActive ? 'PROCESSING' : 'QUEUED'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Outcome Summary when Complete */}
        {isComplete && analysisResult && (
          <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-3 animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="text-sm font-bold text-white font-mono">
                  Prescription Analysis Complete
                </span>
              </div>
              <Badge variant="emerald" size="xs">
                {analysisResult.processingTimeMs} ms latency
              </Badge>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center font-mono text-xs">
              <div className="p-2 rounded bg-black/50 border border-white/5">
                <span className="text-[10px] text-slate-400 block">DETECTED</span>
                <span className="text-base font-bold text-white">
                  {analysisResult.summary.totalDetected} Drugs
                </span>
              </div>
              <div className="p-2 rounded bg-black/50 border border-white/5">
                <span className="text-[10px] text-slate-400 block">ABSTENTIONS</span>
                <span
                  className={`text-base font-bold ${
                    analysisResult.summary.abstentionsCount > 0
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {analysisResult.summary.abstentionsCount} Flagged
                </span>
              </div>
              <div className="p-2 rounded bg-black/50 border border-white/5">
                <span className="text-[10px] text-slate-400 block">LASA RISK</span>
                <span
                  className={`text-base font-bold ${
                    analysisResult.summary.lasaRiskCount > 0 ? 'text-red-400' : 'text-emerald-400'
                  }`}
                >
                  {analysisResult.summary.lasaRiskCount} Alerts
                </span>
              </div>
            </div>

            <Button
              variant="primary"
              size="md"
              className="w-full mt-2"
              onClick={() => onViewResults(analysisResult)}
              rightIcon={<ArrowRight className="w-4 h-4 text-slate-950" />}
            >
              Open Diagnostic Review Console
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
};
