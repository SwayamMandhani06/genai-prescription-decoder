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
    <div className="rounded-2xl border border-red-200 dark:border-red-800 bg-red-50/60 dark:bg-red-950/20 p-5 sm:p-6 space-y-4 shadow-xs animate-in fade-in transition-colors">
      {/* Alert Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-red-200 dark:border-red-800/60 pb-3">
        <div className="flex items-center gap-2.5 text-red-700 dark:text-red-400">
          <ShieldAlert className="w-5 h-5 text-red-600 dark:text-red-400" />
          <div>
            <h3 className="text-sm font-bold text-red-900 dark:text-red-200 tracking-tight">
              Look-Alike Sound-Alike (LASA) Confusion Alert
            </h3>
            <p className="text-xs text-red-700 dark:text-red-300/80">
              High Phonetic &amp; Orthographic Similarity Detected in Formularies
            </p>
          </div>
        </div>

        <div className="px-3 py-1 rounded-full text-xs font-semibold bg-red-100 dark:bg-red-950/50 text-red-800 dark:text-red-300 border border-red-300 dark:border-red-700 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
          <span>{lasaDetail.levenshteinScore}% Similarity Index</span>
        </div>
      </div>

      {/* TALL MAN Lettering Comparison Box */}
      <div className="p-4 rounded-xl bg-surface border border-red-200 dark:border-red-800/60 space-y-3">
        <div className="flex items-center justify-between text-xs text-theme-muted font-medium">
          <span>ISMP TALL MAN LETTERING DIFFERENTIATION:</span>
          <span className="text-red-600 dark:text-red-400 font-semibold">Confusion Risk</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
          <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-1">
            <span className="text-[11px] text-theme-muted uppercase font-medium">
              Interpreted Candidate:
            </span>
            <div className="text-lg font-mono font-bold text-teal-800 dark:text-teal-300">
              {lasaDetail.tallManPrescribed}
            </div>
            <span className="text-xs text-theme-secondary block">
              Biguanide oral hypoglycemic for diabetes.
            </span>
          </div>

          <div className="p-3 rounded-xl bg-red-50/70 dark:bg-red-950/40 border border-red-300 dark:border-red-800 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-red-800 dark:text-red-300 uppercase font-medium">
                Confusable Counterpart:
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-200/70 dark:bg-red-900/60 text-red-900 dark:text-red-200 font-bold">
                HIGH DANGER
              </span>
            </div>
            <div className="text-lg font-mono font-bold text-red-700 dark:text-red-300">
              {lasaDetail.tallManConfused}
            </div>
            <span className="text-xs text-red-800 dark:text-red-300/80 block">
              Sulfonylurea antidiabetic; distinct dosing and potency.
            </span>
          </div>
        </div>
      </div>

      {/* Clinical Risk Summary */}
      <div className="text-xs text-red-900 dark:text-red-200 leading-relaxed">
        <strong>Adverse Risk Note:</strong> {lasaDetail.clinicalRiskSummary}
      </div>

      {/* Pharmacist Action Notice */}
      <div className="p-3 rounded-xl bg-red-100/70 dark:bg-red-900/30 border border-red-300 dark:border-red-700 flex items-start gap-2.5 text-xs text-red-950 dark:text-red-100 font-semibold">
        <UserCheck className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
        <div>
          <span>Dispensing Safeguard:</span> {lasaDetail.mandatedAction}
        </div>
      </div>
    </div>
  );
};
