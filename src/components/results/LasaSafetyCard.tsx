import React from 'react';
import { LasaSafetyDetail } from '../../types/prescription.types';
import { ShieldAlert, AlertTriangle, UserCheck } from 'lucide-react';

export interface LasaSafetyCardProps {
  lasaDetail?: LasaSafetyDetail;
}

export const LasaSafetyCard: React.FC<LasaSafetyCardProps> = ({ lasaDetail }) => {
  if (!lasaDetail || !lasaDetail.hasWarning) {
    return null;
  }

  return (
    <div className="rounded-3xl border border-red-200 dark:border-red-800 bg-red-50/60 dark:bg-red-950/20 p-6 sm:p-7 space-y-5 shadow-xs animate-in fade-in transition-colors">
      {/* Alert Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-red-200 dark:border-red-800/60 pb-4">
        <div className="flex items-center gap-3 text-red-700 dark:text-red-400">
          <ShieldAlert className="w-6 h-6 text-red-600 dark:text-red-400 shrink-0" />
          <div>
            <h3 className="text-xl sm:text-2xl font-bold text-red-900 dark:text-red-200 tracking-tight">
              Look-Alike Sound-Alike (LASA) Confusion Alert
            </h3>
            <p className="text-sm sm:text-base text-red-700 dark:text-red-300/80">
              High Phonetic &amp; Orthographic Similarity Detected in Formularies
            </p>
          </div>
        </div>

        <div className="px-3.5 py-1.5 rounded-full text-xs sm:text-sm font-semibold bg-red-100 dark:bg-red-950/50 text-red-800 dark:text-red-300 border border-red-300 dark:border-red-700 flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
          <span>{lasaDetail.levenshteinScore}% Similarity Index</span>
        </div>
      </div>

      {/* TALL MAN Lettering Comparison Box */}
      <div className="p-5 rounded-2xl bg-surface border border-red-200 dark:border-red-800/60 space-y-4">
        <div className="flex items-center justify-between text-xs sm:text-sm text-theme-muted font-medium">
          <span>ISMP TALL MAN LETTERING DIFFERENTIATION:</span>
          <span className="text-red-600 dark:text-red-400 font-semibold">Confusion Risk</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
          <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-1.5">
            <span className="text-xs sm:text-sm text-theme-muted uppercase font-medium block">
              Interpreted Candidate:
            </span>
            <div className="text-xl sm:text-2xl font-mono font-bold text-teal-800 dark:text-teal-300">
              {lasaDetail.tallManPrescribed}
            </div>
            <span className="text-xs sm:text-sm text-theme-secondary block leading-relaxed">
              Biguanide oral hypoglycemic for diabetes.
            </span>
          </div>

          <div className="p-4 rounded-xl bg-red-50/70 dark:bg-red-950/40 border border-red-300 dark:border-red-800 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs sm:text-sm text-red-800 dark:text-red-300 uppercase font-medium">
                Confusable Counterpart:
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-red-200/70 dark:bg-red-900/60 text-red-900 dark:text-red-200 font-bold">
                HIGH DANGER
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-mono font-bold text-red-700 dark:text-red-300">
              {lasaDetail.tallManConfused}
            </div>
            <span className="text-xs sm:text-sm text-red-800 dark:text-red-300/80 block leading-relaxed">
              Sulfonylurea antidiabetic; distinct dosing and potency.
            </span>
          </div>
        </div>
      </div>

      {/* Clinical Risk Summary */}
      <div className="text-sm sm:text-base text-red-900 dark:text-red-200 leading-relaxed">
        <strong>Adverse Risk Note:</strong> {lasaDetail.clinicalRiskSummary}
      </div>

      {/* Pharmacist Action Notice */}
      <div className="p-4 rounded-xl bg-red-100/70 dark:bg-red-900/30 border border-red-300 dark:border-red-700 flex items-start gap-3 text-sm sm:text-base text-red-950 dark:text-red-100 font-semibold leading-relaxed">
        <UserCheck className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
        <div>
          <span>Dispensing Safeguard:</span> {lasaDetail.mandatedAction}
        </div>
      </div>
    </div>
  );
};
