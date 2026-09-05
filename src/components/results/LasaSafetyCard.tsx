import React from 'react';
import { LasaSafetyDetail } from '../../types/prescription.types';
import { ShieldAlert, AlertTriangle, ArrowRightLeft, UserCheck } from 'lucide-react';

export interface LasaSafetyCardProps {
  lasaDetail?: LasaSafetyDetail;
}

export const LasaSafetyCard: React.FC<LasaSafetyCardProps> = ({ lasaDetail }) => {
  if (!lasaDetail || !lasaDetail.hasWarning) {
    return null;
  }

  return (
    <div className="rounded-xl border border-red-500/40 bg-red-950/20 p-5 sm:p-6 space-y-4 shadow-xl shadow-red-950/20 animate-in fade-in">
      {/* Alert Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-red-500/20 pb-3">
        <div className="flex items-center gap-2.5 text-red-400">
          <ShieldAlert className="w-5 h-5 text-red-400 animate-pulse" />
          <div>
            <h3 className="text-sm font-bold text-white font-mono tracking-tight uppercase">
              Look-Alike Sound-Alike (LASA) Ambiguity Alert
            </h3>
            <p className="text-xs text-red-300/80 font-sans">
              High Phonetic &amp; Orthographic Similarity Detected in Formularies
            </p>
          </div>
        </div>

        <div className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-red-500/20 text-red-300 border border-red-500/40 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
          <span>{lasaDetail.levenshteinScore}% Similarity Index</span>
        </div>
      </div>

      {/* TALL MAN Lettering Comparison Box */}
      <div className="p-4 rounded-lg bg-black/60 border border-red-500/20 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400">
          <span>FDA / ISMP TALL MAN LETTERING DIFFERENTIATION:</span>
          <span className="text-[10px] text-red-400">ORTHOGRAPHIC COLLISION</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
          <div className="p-3 rounded bg-slate-900/80 border border-white/10 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase">
              Interpreted Prescription Candidate:
            </span>
            <div className="text-lg font-mono font-extrabold text-cyan-300">
              {lasaDetail.tallManPrescribed}
            </div>
            <span className="text-[11px] text-slate-400 font-sans block">
              Biguanide oral hypoglycemic for diabetes mellitus.
            </span>
          </div>

          <div className="p-3 rounded bg-red-950/40 border border-red-500/30 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-red-300 uppercase">
                High-Risk Confusable Counterpart:
              </span>
              <ArrowRightLeft className="w-3 h-3 text-red-400" />
            </div>
            <div className="text-lg font-mono font-extrabold text-red-300">
              {lasaDetail.tallManConfused}
            </div>
            <span className="text-[11px] text-slate-300 font-sans block">
              Nitroimidazole antimicrobial agent for infections.
            </span>
          </div>
        </div>
      </div>

      {/* Clinical Risk Summary */}
      <div className="text-xs text-red-200/90 font-sans leading-relaxed space-y-1.5">
        <p>
          <strong className="text-white font-mono uppercase text-[11px]">Clinical Hazard: </strong>
          {lasaDetail.clinicalRiskSummary}
        </p>
      </div>

      {/* Mandatory Non-Prescriptive Statement */}
      <div className="p-3.5 rounded-lg bg-red-900/30 border border-red-500/40 flex items-start gap-2.5 text-xs text-red-100 font-sans leading-relaxed">
        <UserCheck className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-white font-mono uppercase text-[11px] block">
            Mandated Dispensing Verification:
          </strong>
          <p>{lasaDetail.mandatedAction}</p>
        </div>
      </div>
    </div>
  );
};
