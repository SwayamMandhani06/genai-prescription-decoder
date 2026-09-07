import React from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import {
  ArrowLeft,
  ArrowRight,
  RotateCw,
  CheckCircle2,
  ShieldCheck,
  Languages,
  FileCheck2,
} from 'lucide-react';

export interface ReviewStepProps {
  uploadedData: UploadedPrescriptionFile | null;
  rotation: number;
  onSetRotation: (rotation: number) => void;
  onBackToUpload: () => void;
  onStartAnalysis: () => void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  uploadedData,
  rotation,
  onSetRotation,
  onBackToUpload,
  onStartAnalysis,
}) => {
  const handleRotate = () => {
    onSetRotation((rotation + 90) % 360);
  };

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Step Header */}
      <div className="max-w-2xl space-y-2">
        <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-theme-primary">
          Review the prescription.
        </h1>
        <p className="text-sm sm:text-base text-theme-secondary leading-relaxed">
          Confirm document orientation and clarity before running the clinical interpretation engine.
        </p>
      </div>

      {/* Main Review Cockpit (Focused on the Prescription) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Document Focus Area (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-3xl border border-theme bg-surface/40 p-6 sm:p-8 flex flex-col items-center justify-center min-h-[440px]">
            <div
              style={{
                transform: `rotate(${rotation}deg)`,
                transition: 'transform 0.25s ease-out',
              }}
              className="max-w-md w-full shadow-md rounded-2xl prescription-paper p-6 border border-theme origin-center"
            >
              {/* Prescription Document Display */}
              <div className="space-y-4 text-slate-900 dark:text-slate-100">
                <div className="border-b border-slate-300 dark:border-slate-700 pb-2 flex justify-between items-start text-xs">
                  <div>
                    <div className="font-semibold text-teal-800 dark:text-teal-400 text-[11px]">
                      Example Clinical Practice
                    </div>
                    <div className="font-bold text-slate-800 dark:text-slate-200 text-xs">
                      Example Prescriber, M.D.
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400">
                    {uploadedData?.fileName || 'prescription.svg'}
                  </span>
                </div>

                <div className="text-xl font-serif italic font-bold">℞</div>

                {/* Handwriting Lines */}
                <div className="space-y-3.5 py-2">
                  <div className="border-b border-slate-200 dark:border-slate-800 pb-2">
                    <div className="font-serif italic text-base text-blue-900 dark:text-sky-300 font-bold">
                      Augm 625 Duo &mdash; 1-0-1 (PC) x 5d
                    </div>
                  </div>
                  <div className="border-b border-slate-200 dark:border-slate-800 pb-2">
                    <div className="font-serif italic text-base text-blue-900 dark:text-sky-300 font-bold">
                      Pan 40 &mdash; 1 tab OD (AC) x 5d
                    </div>
                  </div>
                  <div>
                    <div className="font-serif italic text-base text-blue-900 dark:text-sky-300 font-bold">
                      Dolo 650 &mdash; SOS for fever
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-300 dark:border-slate-700 flex justify-between text-[10px] text-slate-500">
                  <span>Patient: Demo Patient (34M)</span>
                  <span>Prescriber Signature Attached</span>
                </div>
              </div>
            </div>

            {/* Rotation Adjustment */}
            <div className="mt-4 flex items-center gap-2">
              <button
                onClick={handleRotate}
                className="px-3.5 py-1.5 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-xs font-semibold text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Adjust rotation ({rotation}&deg;)</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right: Actions & Pre-Flight Verification (5 cols) */}
        <div className="lg:col-span-5 space-y-6 pt-2">
          {/* Primary & Secondary Actions - Free from container card */}
          <div className="space-y-3">
            <button
              onClick={onStartAnalysis}
              className="w-full py-4 px-6 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-sm cursor-pointer group"
            >
              <FileCheck2 className="w-5 h-5" />
              <span>Start Analysis</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              onClick={onBackToUpload}
              className="w-full py-2.5 px-4 text-xs font-semibold text-theme-secondary hover:text-theme-primary transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Upload</span>
            </button>
          </div>

          {/* Pre-Flight Checklist - Unboxed, quiet typographic grouping */}
          <div className="space-y-3 pt-6 border-t border-theme">
            <h3 className="text-xs font-semibold text-theme-secondary">
              Pre-analysis checklist
            </h3>

            <div className="space-y-2.5 text-xs text-theme-secondary">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-theme-primary font-medium">Document mounted:</strong>{' '}
                  {uploadedData?.fileName || 'Prescription Script'}
                </p>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-theme-primary font-medium">Formularies:</strong> CDSCO National List &amp; US NLM RxNorm linked
                </p>
              </div>

              <div className="flex items-start gap-2.5">
                <Languages className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-theme-primary font-medium">Languages:</strong> English, हिन्दी, मराठी
                </p>
              </div>

              <div className="flex items-start gap-2.5">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-theme-primary font-medium">Safety barrier:</strong> Ambiguous cursive will be flagged for review
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
