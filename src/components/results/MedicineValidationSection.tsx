import React from 'react';
import { ValidationEvidence } from '../../types/prescription.types';
import {
  Database,
  FileCheck2,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';

export interface MedicineValidationSectionProps {
  evidence: ValidationEvidence;
}

export const MedicineValidationSection: React.FC<MedicineValidationSectionProps> = ({
  evidence,
}) => {
  const isApproved =
    evidence.validationStatus === 'CDSCO_APPROVED' ||
    evidence.validationStatus === 'RXNORM_GROUNDED';

  return (
    <div className="rounded-xl border border-white/10 bg-[#0A0E1A] p-5 sm:p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="text-sm font-bold text-white font-mono tracking-tight uppercase">
              Pharmacopeial Validation &amp; Grounding Evidence
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              CDSCO India Schedule H &amp; US NLM RxNorm Formulary Cross-Verification
            </p>
          </div>
        </div>

        <div
          className={`px-3 py-1 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 ${
            isApproved
              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
              : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
          }`}
        >
          {isApproved ? (
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span>{evidence.statusBadgeText}</span>
        </div>
      </div>

      {/* Grid: Extracted Candidate vs Matched Formulary Medicine */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
            Extracted Vision-Language Candidate:
          </span>
          <div className="text-sm font-bold text-cyan-300 font-mono">
            {evidence.extractedCandidate}
          </div>
          <span className="text-[11px] text-slate-400 font-sans block">
            Tokenized directly from handwritten physician ligatures.
          </span>
        </div>

        <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
            Verified Knowledge Graph Entity:
          </span>
          <div className="text-sm font-bold text-emerald-300 font-mono">
            {evidence.matchedMedicine}
          </div>
          <span className="text-[11px] text-slate-400 font-sans block">
            Active Salt: <strong className="text-slate-200">{evidence.genericSalt}</strong>
          </span>
        </div>
      </div>

      {/* Clinical Reference Metadata Badges */}
      <div className="p-4 rounded-lg bg-[#070A12] border border-white/[0.06] grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
        <div className="space-y-1">
          <span className="text-[10px] text-slate-500 uppercase block">CDSCO CLASSIFICATION</span>
          <span className="text-slate-200 font-semibold">{evidence.cdscoSchedule}</span>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] text-slate-500 uppercase block">RXNORM CONCEPT (CUI)</span>
          <div className="flex items-center gap-1.5 text-cyan-400 font-bold">
            <span>RxCUI: {evidence.rxNormCui}</span>
            <ExternalLink className="w-3 h-3 text-cyan-500" />
          </div>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] text-slate-500 uppercase block">THERAPEUTIC CLASS</span>
          <span className="text-slate-300 font-sans text-[11px] leading-tight block">
            {evidence.therapeuticClass}
          </span>
        </div>
      </div>

      {/* Indications & Evidence Source */}
      <div className="space-y-1.5 text-xs">
        <div className="text-slate-400 font-sans">
          <strong className="text-slate-200 font-mono">Standard Indications:</strong>{' '}
          {evidence.standardIndications}
        </div>
        <div className="text-[11px] font-mono text-slate-500">
          Source: {evidence.evidenceSource}
        </div>
      </div>

      {/* Alternative Candidates / Formulations */}
      {evidence.alternativeCandidates && evidence.alternativeCandidates.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-white/[0.06]">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="uppercase tracking-wider flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
              Alternative Bioequivalent Candidates Evaluated
            </span>
            <span className="text-[10px] text-slate-500">EDIT DISTANCE &amp; FORMULARY SIMILARITY</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {evidence.alternativeCandidates.map((alt, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded bg-black/30 border border-white/5 space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200 font-mono">{alt.name}</span>
                  <span className="text-[10px] font-mono text-cyan-400 font-semibold">
                    {Math.round(alt.similarityScore * 100)}% Match
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 font-sans">{alt.generic}</div>
                <div className="text-[10px] text-slate-500 font-sans">{alt.notes}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statutory Primacy Reminder */}
      <div className="p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/20 flex items-start gap-2.5 text-xs text-cyan-200 font-sans leading-relaxed">
        <FileCheck2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-white font-mono uppercase text-[11px] block">
            Original Prescription Primacy Rule:
          </strong>
          Pharmacopeial cross-referencing is assistive. The prescriber&rsquo;s original signed
          prescription remains the primary legal reference for dispensing.
        </div>
      </div>
    </div>
  );
};
