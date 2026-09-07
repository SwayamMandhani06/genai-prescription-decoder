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
      label: 'Document Focus & Ingestion',
      desc: 'Compensating for document skew, paper grain, and doctor letterhead context.',
      icon: Layers,
    },
    {
      label: 'Handwriting Parsing & Posology',
      desc: 'Segmenting cursive handwritten strokes into medicine name, dosage, and frequency.',
      icon: FileCheck2,
    },
    {
      label: 'Formulary Verification (CDSCO & RxNorm)',
      desc: 'Matching candidate entities against official approved pharmaceutical references.',
      icon: Database,
    },
    {
      label: 'Uncertainty Calibration & Safety',
      desc: 'Evaluating entropy; checking Look-Alike Sound-Alike confusion risks.',
      icon: ShieldAlert,
    },
  ];

  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(0);
      return;
    }

    const t1 = setTimeout(() => setCurrentStep(1), 400);
    const t2 = setTimeout(() => setCurrentStep(2), 1000);
    const t3 = setTimeout(() => setCurrentStep(3), 1600);
    const t4 = setTimeout(() => setCurrentStep(4), 2200);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [isOpen]);

  const isComplete = currentStep >= 4 && analysisResult !== null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Processing Prescription"
      subtitle="Multimodal vision pipeline analyzing handwritten script"
      maxWidth="lg"
    >
      <div className="space-y-6">
        {/* Step Progress List */}
        <div className="space-y-3">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isFinished = currentStep > idx;
            const isCurrent = currentStep === idx;

            return (
              <div
                key={step.label}
                className={`p-3.5 rounded-xl border transition-all flex items-start gap-3.5 ${
                  isFinished
                    ? 'bg-teal-50/60 dark:bg-teal-950/20 border-teal-200 dark:border-teal-800 text-theme-primary'
                    : isCurrent
                    ? 'bg-teal-50/60 dark:bg-teal-950/25 border-teal-400 dark:border-teal-600 text-theme-primary ring-2 ring-teal-500/20'
                    : 'bg-surface-subtle border-theme text-theme-muted opacity-60'
                }`}
              >
                <div className="shrink-0 mt-0.5">
                  {isFinished ? (
                    <CheckCircle2 className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                  ) : isCurrent ? (
                    <div className="w-5 h-5 rounded-full border-2 border-teal-600 border-t-transparent animate-spin" />
                  ) : (
                    <Icon className="w-5 h-5 text-theme-muted" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-theme-primary">
                      {step.label}
                    </span>
                    {isFinished && (
                      <span className="text-[10px] font-medium text-teal-700 dark:text-teal-300 uppercase">
                        Verified
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-theme-secondary mt-0.5 leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Completion Callout */}
        {isComplete && analysisResult && (
          <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-3 animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span className="text-xs font-bold text-theme-primary">
                  Analysis Complete
                </span>
              </div>
              <Badge variant="emerald" size="xs">
                {analysisResult.extractedMedications.length} Medicines Identified
              </Badge>
            </div>

            <p className="text-xs text-theme-secondary leading-relaxed">
              Prescription interpretation complete. Medicine candidates grounded in official formularies with plain-language explanations.
            </p>

            <Button
              variant="primary"
              size="md"
              onClick={() => onViewResults(analysisResult)}
              className="w-full"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              View Prescription Findings
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
};
