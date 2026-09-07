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
    <div className="rounded-2xl border border-theme bg-surface p-5 sm:p-6 space-y-5 shadow-xs transition-colors">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-theme pb-4">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-teal-600 dark:text-teal-400" />
          <div>
            <h3 className="text-sm font-bold text-theme-primary tracking-tight">
              Clinical Formulary &amp; Grounding Evidence
            </h3>
            <p className="text-xs text-theme-secondary">
              Cross-verified with CDSCO India &amp; US NLM RxNorm Formularies
            </p>
          </div>
        </div>

        <div
          className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 ${
            isApproved
              ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
              : 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
          }`}
        >
          {isApproved ? (
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
          )}
          <span>{evidence.statusBadgeText}</span>
        </div>
      </div>

      {/* Grid: Extracted Candidate vs Matched Formulary Medicine */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-3.5 rounded-xl bg-surface-subtle border border-theme space-y-1">
          <span className="text-[11px] text-theme-muted uppercase tracking-wider block font-medium">
            Extracted Vision Candidate:
          </span>
          <div className="text-sm font-bold text-teal-700 dark:text-teal-300">
            {evidence.extractedCandidate}
          </div>
          <span className="text-xs text-theme-secondary block">
            Extracted directly from handwritten cursive strokes.
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-surface-subtle border border-theme space-y-1">
          <span className="text-[11px] text-theme-muted uppercase tracking-wider block font-medium">
            Verified Formulary Entity:
          </span>
          <div className="text-sm font-bold text-emerald-700 dark:text-emerald-300">
            {evidence.matchedMedicine}
          </div>
          <span className="text-xs text-theme-secondary block">
            Active Molecule: <strong className="text-theme-primary">{evidence.genericSalt}</strong>
          </span>
        </div>
      </div>

      {/* Clinical Reference Metadata Badges */}
      <div className="p-4 rounded-xl bg-surface-subtle border border-theme grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <div className="space-y-0.5">
          <span className="text-[10px] text-theme-muted uppercase font-medium block">CDSCO Schedule</span>
          <span className="text-theme-primary font-semibold font-mono">{evidence.cdscoSchedule}</span>
        </div>
        <div className="space-y-0.5">
          <span className="text-[10px] text-theme-muted uppercase font-medium block">RxNorm Concept</span>
          <div className="flex items-center gap-1.5 text-sky-700 dark:text-sky-400 font-bold font-mono">
            <span>RxCUI: {evidence.rxNormCui}</span>
            <ExternalLink className="w-3 h-3" />
          </div>
        </div>
        <div className="space-y-0.5">
          <span className="text-[10px] text-theme-muted uppercase font-medium block">Therapeutic Class</span>
          <span className="text-theme-secondary text-xs leading-tight block">
            {evidence.therapeuticClass}
          </span>
        </div>
      </div>

      {/* Indications & Evidence Source */}
      <div className="space-y-1 text-xs">
        <div className="text-theme-secondary">
          <strong className="text-theme-primary">Standard Indications:</strong>{' '}
          {evidence.standardIndications}
        </div>
        <div className="text-[11px] text-theme-muted">
          Source: {evidence.evidenceSource}
        </div>
      </div>

      {/* Alternative Candidates */}
      {evidence.alternativeCandidates && evidence.alternativeCandidates.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-theme">
          <div className="flex items-center justify-between text-xs text-theme-secondary">
            <span className="font-semibold flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              Bioequivalent Formulations Evaluated
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {evidence.alternativeCandidates.map((alt, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-surface border border-theme space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-theme-primary">{alt.name}</span>
                  <span className="text-[11px] font-mono text-teal-700 dark:text-teal-400 font-semibold">
                    {Math.round(alt.similarityScore * 100)}% Match
                  </span>
                </div>
                <div className="text-[11px] text-theme-secondary">{alt.generic}</div>
                <div className="text-[10px] text-theme-muted">{alt.notes}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statutory Primacy Reminder */}
      <div className="p-3 rounded-xl bg-teal-50/70 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 flex items-start gap-2.5 text-xs text-teal-900 dark:text-teal-200 leading-relaxed">
        <FileCheck2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-teal-950 dark:text-teal-100 uppercase text-[11px] block">
            Original Prescription Primacy:
          </strong>
          Pharmacopeial cross-referencing is assistive. The prescriber&rsquo;s signed
          prescription remains the primary legal reference for dispensing.
        </div>
      </div>
    </div>
  );
};
