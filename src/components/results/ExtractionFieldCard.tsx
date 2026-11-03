import React, { useState } from 'react';
import { ExtractedFieldItem, BoundingBox, EpistemicStatus } from '../../types/prescription.types';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  FileSearch,
  ExternalLink,
  ShieldAlert,
  Info,
  Check,
  Edit3,
  HelpCircle,
} from 'lucide-react';

export interface ExtractionFieldCardProps {
  field: ExtractedFieldItem;
  isActive?: boolean;
  onHover?: (box?: BoundingBox, label?: string) => void;
  onLeave?: () => void;
}

export const ExtractionFieldCard: React.FC<ExtractionFieldCardProps> = ({
  field,
  isActive = false,
  onHover,
  onLeave,
}) => {
  const [verificationStatus, setVerificationStatus] = useState<'pending' | 'confirmed' | 'corrected' | 'unreadable'>(
    field.verificationStatus || 'pending'
  );
  const [verifiedValue, setVerifiedValue] = useState<string | null>(
    field.verifiedValue !== undefined ? field.verifiedValue : field.value
  );
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(field.value);

  const resolveEpistemicStatus = (): EpistemicStatus => {
    if (field.epistemicStatus) return field.epistemicStatus;
    const val = (field.value || '').trim();
    if (val === 'ILLEGIBLE' || val.includes('[?]') || val.toLowerCase().includes('illegible')) {
      return 'ILLEGIBLE';
    }
    if (!val || val === 'MISSING' || val === 'NOT_SPECIFIED' || val.toLowerCase().includes('not written')) {
      return 'MISSING_ON_RX';
    }
    if (field.status === 'flagged' || field.status === 'abstained') {
      return 'AMBIGUOUS';
    }
    if (field.status === 'uncertain') {
      return 'UNVERIFIED';
    }
    return 'EXTRACTED';
  };

  const epistemic = resolveEpistemicStatus();

  const getStatusBadge = () => {
    switch (epistemic) {
      case 'MISSING_ON_RX':
        return (
          <div
            data-testid="badge-missing-on-rx"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs sm:text-sm font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700"
            title="Prescriber did not write or specify this field on the prescription pad."
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
            <span>Not written on prescription</span>
          </div>
        );

      case 'ILLEGIBLE':
        return (
          <div
            data-testid="badge-illegible"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs sm:text-sm font-semibold bg-rose-50 dark:bg-rose-950/50 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
            title="Handwriting strokes are present on pad but illegible or collapsed. Clinical safety rules strictly forbid guessing."
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
            <span>Handwriting unclear — do not guess</span>
          </div>
        );

      case 'AMBIGUOUS':
        return (
          <div
            data-testid="badge-ambiguous"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs sm:text-sm font-semibold bg-orange-50 dark:bg-orange-950/40 text-orange-800 dark:text-orange-300 border border-orange-300 dark:border-orange-800"
            title="Multiple conflicting or ambiguous posology interpretations detected."
          >
            <AlertCircle className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
            <span>Ambiguous interpretation</span>
          </div>
        );

      case 'UNVERIFIED':
        return (
          <div
            data-testid="badge-unverified"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs sm:text-sm font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800"
            title="Extraction confidence below verification threshold. Pharmacist confirmation required."
          >
            <Info className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            <span>Pharmacist Verification Required</span>
          </div>
        );

      case 'EXTRACTED':
      default:
        return (
          <div
            data-testid="badge-extracted"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs sm:text-sm font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800"
            title="Visually grounded extraction with confident evidence support."
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Grounded · Extracted</span>
          </div>
        );
    }
  };

  const getBorderAndBgStyle = () => {
    if (epistemic === 'ILLEGIBLE') {
      return 'bg-rose-50/40 dark:bg-rose-950/20 border-rose-300 dark:border-rose-800 shadow-xs';
    }
    if (epistemic === 'MISSING_ON_RX') {
      return 'bg-slate-50/50 dark:bg-slate-900/20 border-slate-300 dark:border-slate-800 shadow-xs';
    }
    if (epistemic === 'AMBIGUOUS' || field.status === 'flagged') {
      return 'bg-orange-50/40 dark:bg-orange-950/20 border-orange-300 dark:border-orange-800 shadow-xs';
    }
    if (epistemic === 'UNVERIFIED' || field.status === 'uncertain') {
      return 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-800 shadow-xs';
    }
    if (isActive) {
      return 'bg-[#EAF2FF]/50 dark:bg-[#155EEF]/20 border-[#155EEF] dark:border-[#4B8BFF] shadow-sm ring-1 ring-[#155EEF]/30';
    }
    return 'bg-surface border-theme hover:border-theme-hover shadow-xs';
  };

  const confidencePercent = Math.round(field.confidence * 100);

  return (
    <div
      onMouseEnter={() => onHover && onHover(field.boundingBox, field.fieldName)}
      onMouseLeave={() => onLeave && onLeave()}
      className={`p-5 sm:p-6 rounded-2xl border transition-all duration-200 space-y-4 cursor-pointer ${getBorderAndBgStyle()}`}
    >
      {/* Top Header: Field Name, Status Badge, and Confidence Score */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <span className="text-xs sm:text-sm text-theme-muted font-medium block">
            {field.fieldName}
          </span>
          <h3 className="text-xl sm:text-2xl lg:text-[1.65rem] font-bold text-theme-primary tracking-tight leading-snug">
            {epistemic === 'MISSING_ON_RX' ? (
              <span className="text-slate-500 dark:text-slate-400 italic font-normal text-lg sm:text-xl">
                Not written on prescription
              </span>
            ) : epistemic === 'ILLEGIBLE' ? (
              <span className="text-rose-700 dark:text-rose-300 font-mono flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0" />
                <span>[Illegible Handwriting]</span>
              </span>
            ) : (
              field.value
            )}
          </h3>
        </div>

        <div className="flex items-center gap-3.5">
          {getStatusBadge()}
          <div className="text-right">
            {field.calibrationStatus === 'calibrated' && field.calibratedConfidence !== null && field.calibratedConfidence !== undefined ? (
              <>
                <span
                  title="Calibrated confidence estimate grounded in empirical validation distribution"
                  className="text-sm font-bold font-mono text-[#155EEF] dark:text-[#4B8BFF]"
                >
                  {Math.round(field.calibratedConfidence * 100)}%
                </span>
                <span className="text-[11px] text-[#155EEF] dark:text-[#4B8BFF] block font-medium">
                  Calibrated Confidence
                </span>
              </>
            ) : (
              <>
                <span
                  title="Estimated extraction confidence score (raw model signal — not a calibrated probability)"
                  className={`text-sm font-bold font-mono ${
                    epistemic === 'EXTRACTED'
                      ? 'text-emerald-700 dark:text-emerald-400'
                      : epistemic === 'MISSING_ON_RX'
                      ? 'text-slate-600 dark:text-slate-400'
                      : epistemic === 'ILLEGIBLE'
                      ? 'text-rose-700 dark:text-rose-400'
                      : epistemic === 'AMBIGUOUS'
                      ? 'text-orange-700 dark:text-orange-400'
                      : 'text-amber-700 dark:text-amber-400'
                  }`}
                >
                  {confidencePercent}%
                </span>
                <span className="text-[11px] text-theme-muted block font-medium">
                  {field.calibrationStatus === 'insufficient_data'
                    ? 'Raw Signal (Uncalibrated)'
                    : 'Estimated Confidence'}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Visual Confidence Meter Bar */}
      <div className="space-y-1">
        <div className="w-full h-1.5 bg-surface-subtle rounded-full overflow-hidden border border-theme flex">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              epistemic === 'EXTRACTED'
                ? 'bg-emerald-500'
                : epistemic === 'MISSING_ON_RX'
                ? 'bg-slate-400'
                : epistemic === 'ILLEGIBLE'
                ? 'bg-rose-500'
                : epistemic === 'AMBIGUOUS'
                ? 'bg-orange-500'
                : 'bg-amber-500'
            }`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Explicit Epistemic Callout: Missing on Rx vs Illegible */}
      {epistemic === 'MISSING_ON_RX' && (
        <div className="p-3.5 rounded-xl bg-slate-100/70 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800 text-xs sm:text-sm text-slate-700 dark:text-slate-300 flex items-start gap-2.5">
          <HelpCircle className="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <strong className="font-semibold block text-slate-900 dark:text-slate-100">
              Not Written on Prescription Pad
            </strong>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              The prescribing physician omitted this field (no ink strokes present on pad for this posology attribute). Clinical safety guidelines prohibit guessing or inserting default dosages.
            </p>
          </div>
        </div>
      )}

      {epistemic === 'ILLEGIBLE' && (
        <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-xs sm:text-sm text-rose-900 dark:text-rose-200 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <strong className="font-semibold block text-rose-950 dark:text-rose-100">
              Handwriting Unclear — Do Not Guess
            </strong>
            <p className="text-xs text-rose-800/90 dark:text-rose-200/90 leading-relaxed">
              Handwriting stroke is visually detected, but ink ligature is collapsed or severely degraded. To protect patient safety, automated AI interpretation has been halted for this field. Contact prescriber for clarification.
            </p>
          </div>
        </div>
      )}

      {/* Explanation & Rationale */}
      <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
        {field.explanation}
      </p>

      {/* Uncertainty & Verification Instructions */}
      {field.status === 'uncertain' && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 space-y-2 text-xs sm:text-sm text-amber-900 dark:text-amber-200">
          <div className="flex items-center gap-2 font-semibold text-amber-800 dark:text-amber-300">
            <Info className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span>Ambiguity &amp; Verification Guidance</span>
          </div>
          {field.uncertaintyReason && (
            <p className="text-xs sm:text-sm text-amber-800/90 dark:text-amber-200/90 leading-relaxed">
              <strong>Observation:</strong> {field.uncertaintyReason}
            </p>
          )}
          {field.verificationInstruction && (
            <p className="text-xs sm:text-sm text-amber-900 dark:text-amber-100 bg-amber-100/60 dark:bg-amber-900/30 p-2.5 rounded-lg border border-amber-300 dark:border-amber-800 leading-relaxed">
              <strong>Action Required:</strong> {field.verificationInstruction}
            </p>
          )}
        </div>
      )}

      {/* Flagged / Selective Abstention Notice */}
      {field.status === 'flagged' && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 space-y-2 text-xs sm:text-sm text-red-900 dark:text-red-200">
          <div className="flex items-center gap-2 font-semibold text-red-800 dark:text-red-300">
            <ShieldAlert className="w-4 h-4 text-red-600 dark:text-red-400" />
            <span>Selective Abstention Activated</span>
          </div>
          {field.uncertaintyReason && (
            <p className="text-xs sm:text-sm text-red-800/90 dark:text-red-200/90 leading-relaxed">
              <strong>Hazard Analysis:</strong> {field.uncertaintyReason}
            </p>
          )}
          {field.verificationInstruction && (
            <p className="text-xs sm:text-sm text-red-900 dark:text-red-100 bg-red-100/60 dark:bg-red-900/40 p-2.5 rounded-lg border border-red-300 dark:border-red-800 leading-relaxed font-semibold">
              {field.verificationInstruction}
            </p>
          )}
        </div>
      )}

      {/* Phase 9 Human Verification Section */}
      {(field.requiresHumanVerification || field.abstentionDecision === 'abstained' || field.status === 'uncertain' || field.status === 'flagged') && (
        <div className="pt-3 border-t border-theme/60 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-amber-800 dark:text-amber-300">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Requires Human Verification</span>
            </div>
            {verificationStatus !== 'pending' && (
              <span
                className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  verificationStatus === 'confirmed'
                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                    : verificationStatus === 'corrected'
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200'
                    : 'bg-zinc-200 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200'
                }`}
              >
                Audit State: {verificationStatus.toUpperCase()}
              </span>
            )}
          </div>

          {/* Reason codes */}
          {field.abstentionReasons && field.abstentionReasons.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {field.abstentionReasons.map((reason, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-md text-[11px] font-mono font-medium bg-surface-subtle border border-theme text-theme-secondary"
                >
                  {reason}
                </span>
              ))}
            </div>
          )}

          {/* Dosage Invariant Notice */}
          {field.fieldKey === 'dosage' && (
            <div className="p-2.5 rounded-lg bg-[#EAF2FF]/60 dark:bg-[#155EEF]/20 border border-[#155EEF]/30 text-xs text-[#102A43] dark:text-[#EAF2FF] leading-relaxed">
              <strong>IMPORTANT:</strong> The system has NOT changed the observed dosage. Reference data matches never alter prescribed dosage.
            </div>
          )}

          {/* Verified value display if corrected */}
          {verificationStatus === 'corrected' && verifiedValue && (
            <div className="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 text-xs text-blue-900 dark:text-blue-200 leading-relaxed">
              <strong>Verified Transcription:</strong> <span className="font-semibold underline">{verifiedValue}</span> (Original: <em>{field.value}</em>)
            </div>
          )}

          {/* Verified value display if unreadable */}
          {verificationStatus === 'unreadable' && (
            <div className="p-2.5 rounded-lg bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-800 dark:text-zinc-300 leading-relaxed">
              <strong>Marked Unreadable:</strong> Handwriting stroke could not be clinically transcribed. No autonomous guess was substituted.
            </div>
          )}

          {/* Verification Actions */}
          {isEditing ? (
            <div className="space-y-2 pt-1">
              <label className="text-xs font-medium text-theme-secondary block">
                Enter Verified Transcription:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-lg text-sm border border-theme bg-surface text-theme-primary focus:outline-none focus:ring-1 focus:ring-[#155EEF]"
                  placeholder="Corrected clinical text..."
                />
                <button
                  type="button"
                  onClick={() => {
                    if (editValue.trim()) {
                      setVerifiedValue(editValue.trim());
                      setVerificationStatus('corrected');
                      setIsEditing(false);
                    }
                  }}
                  className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#155EEF] text-white hover:bg-[#1249C7] transition-colors cursor-pointer"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-surface-subtle text-theme-secondary hover:bg-theme-muted transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <button
                type="button"
                onClick={() => {
                  setVerifiedValue(field.value);
                  setVerificationStatus('confirmed');
                }}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors flex items-center gap-1 cursor-pointer ${
                  verificationStatus === 'confirmed'
                    ? 'bg-[#155EEF] text-white'
                    : 'bg-surface-subtle text-theme-primary hover:bg-[#EAF2FF]/50 dark:hover:bg-[#155EEF]/20 border border-theme'
                }`}
              >
                <Check className="w-3.5 h-3.5" />
                <span>Confirm</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditValue(verifiedValue || field.value);
                  setIsEditing(true);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 ${
                  verificationStatus === 'corrected'
                    ? 'bg-blue-600 text-white'
                    : 'bg-surface-subtle text-theme-primary hover:bg-blue-50 dark:hover:bg-blue-950/40 border border-theme'
                }`}
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Correct</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setVerifiedValue(null);
                  setVerificationStatus('unreadable');
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 ${
                  verificationStatus === 'unreadable'
                    ? 'bg-zinc-700 text-white'
                    : 'bg-surface-subtle text-theme-primary hover:bg-zinc-100 dark:hover:bg-zinc-800 border border-theme'
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Mark Unreadable</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Card Footer */}
      <div className="pt-3 border-t border-theme flex items-center justify-between text-xs text-theme-muted">
        <div className="flex items-center gap-1.5">
          <FileSearch className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
          <span>Source: {field.source}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[#155EEF] dark:text-[#4B8BFF] hover:underline font-medium">
          <span>Highlight On Script</span>
          <ExternalLink className="w-3 h-3" />
        </div>
      </div>
    </div>
  );
};
