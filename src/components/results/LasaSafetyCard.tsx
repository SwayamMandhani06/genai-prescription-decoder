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
    <div className="rounded-2xl border border-amber-300 dark:border-amber-800/80 bg-amber-50/40 dark:bg-amber-950/20 p-5 sm:p-6 space-y-4 shadow-xs transition-colors">
      {/* Alert Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-amber-200 dark:border-amber-800/60 pb-3.5">
        <div className="flex items-center gap-3 text-amber-900 dark:text-amber-200">
          <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/50 border border-amber-300 dark:border-amber-700 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-4 h-4 text-amber-700 dark:text-amber-400" />
          </div>
          <div>
            <h3 className="text-lg sm:text-xl font-bold tracking-tight text-amber-950 dark:text-amber-100">
              Look-Alike Sound-Alike (LASA) Conflict Notice
            </h3>
            <p className="text-xs sm:text-sm text-amber-800 dark:text-amber-300">
              High phonetic and orthographic similarity detected against clinical formularies
            </p>
          </div>
        </div>

        <div className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 dark:bg-amber-900/60 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-700 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
          <span>{lasaDetail.levenshteinScore}% Similarity Index ({lasaDetail.similarityType})</span>
        </div>
      </div>

      {/* TALL MAN Lettering Comparison Box */}
      <div className="p-4 sm:p-5 rounded-xl bg-surface border border-theme space-y-3">
        <div className="flex items-center justify-between text-xs text-theme-muted font-medium">
          <span>ISMP TALL MAN LETTERING DIFFERENTIATION:</span>
          <span className="text-amber-700 dark:text-amber-400 font-semibold">Formulary Collision Screened</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 items-stretch">
          <div className="p-3.5 rounded-lg bg-surface-subtle border border-theme space-y-1">
            <span className="text-xs text-theme-muted uppercase font-medium block">
              Interpreted Candidate:
            </span>
            <div className="text-lg sm:text-xl font-mono font-bold text-teal-800 dark:text-teal-300">
              {lasaDetail.tallManPrescribed}
            </div>
            <span className="text-xs text-theme-secondary block leading-relaxed">
              Prescribed oral biguanide for glycaemic control.
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-amber-50/70 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-amber-800 dark:text-amber-300 uppercase font-medium">
                Confusable Counterpart:
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-200 dark:bg-amber-900/60 text-amber-950 dark:text-amber-100 font-bold">
                SIMILARITY CONFLICT
              </span>
            </div>
            <div className="text-lg sm:text-xl font-mono font-bold text-amber-900 dark:text-amber-200">
              {lasaDetail.tallManConfused}
            </div>
            <span className="text-xs text-amber-800/90 dark:text-amber-300/90 block leading-relaxed">
              Distinct therapeutic class; separate dosing and clinical indications.
            </span>
          </div>
        </div>
      </div>

      {/* Clinical Risk Summary */}
      <div className="text-xs sm:text-sm text-theme-secondary leading-relaxed bg-surface/60 p-3 rounded-lg border border-theme">
        <strong className="text-theme-primary">Clinical Observation:</strong> {lasaDetail.clinicalRiskSummary}
      </div>

      {/* Pharmacist Action Safeguard */}
      <div className="p-3.5 rounded-xl bg-amber-100/60 dark:bg-amber-950/50 border border-amber-300 dark:border-amber-800 flex items-start gap-2.5 text-xs sm:text-sm text-amber-950 dark:text-amber-100 leading-relaxed font-medium">
        <UserCheck className="w-4 h-4 text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
        <div>
          <strong className="font-semibold text-amber-950 dark:text-amber-100">Verification Safeguard: </strong>
          <span>{lasaDetail.mandatedAction}</span>
        </div>
      </div>
    </div>
  );
};
