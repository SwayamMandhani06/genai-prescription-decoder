import React, { useState } from 'react';
import { ExtractedFieldItem, BoundingBox } from '../../types/prescription.types';
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
  const getStatusBadge = () => {
    switch (field.status) {
      case 'confident':
        return (
          <div className="inline-flex items-center gap-1.5 text-xs sm:text-sm text-theme-muted font-medium">
            <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>Grounded</span>
          </div>
        );
      case 'uncertain':
        return (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs sm:text-sm font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span>Needs verification</span>
          </div>
        );
      case 'flagged':
        return (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs sm:text-sm font-semibold bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800">
            <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
            <span>Flagged for review</span>
          </div>
        );
    }
  };

  const getBorderAndBgStyle = () => {
    if (field.status === 'flagged') {
      return 'bg-red-50/50 dark:bg-red-950/20 border-red-200 dark:border-red-800';
    }
    if (field.status === 'uncertain') {
      return 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800';
    }
    if (isActive) {
      return 'bg-teal-50/60 dark:bg-teal-950/30 border-teal-500 dark:border-teal-500 shadow-sm ring-1 ring-teal-500/20';
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
            {field.value}
          </h3>
        </div>

        <div className="flex items-center gap-3.5">
          {getStatusBadge()}
          <div className="text-right">
            {field.calibrationStatus === 'calibrated' && field.calibratedConfidence !== null && field.calibratedConfidence !== undefined ? (
              <>
                <span
                  title="Calibrated confidence estimate grounded in empirical validation distribution"
                  className="text-sm font-bold font-mono text-teal-700 dark:text-teal-400"
                >
                  {Math.round(field.calibratedConfidence * 100)}%
                </span>
                <span className="text-[11px] text-teal-600 dark:text-teal-400 block font-medium">
                  Calibrated Confidence
                </span>
              </>
            ) : (
              <>
                <span
                  title="Estimated extraction confidence score (raw model signal — not a calibrated probability)"
                  className={`text-sm font-bold font-mono ${
                    field.status === 'confident'
                      ? 'text-emerald-700 dark:text-emerald-400'
                      : field.status === 'uncertain'
                      ? 'text-amber-700 dark:text-amber-400'
                      : 'text-red-700 dark:text-red-400'
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
              field.status === 'confident'
                ? 'bg-emerald-500'
                : field.status === 'uncertain'
                ? 'bg-amber-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

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
                    ? 'bg-teal-100 text-teal-800 dark:bg-teal-900/50 dark:text-teal-200'
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
            <div className="p-2.5 rounded-lg bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 text-xs text-teal-900 dark:text-teal-200 leading-relaxed">
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
                  className="flex-1 px-3 py-1.5 rounded-lg text-sm border border-theme bg-surface text-theme-primary focus:outline-none focus:ring-1 focus:ring-teal-500"
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
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-teal-600 text-white hover:bg-teal-700 transition-colors"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface-subtle text-theme-secondary hover:bg-theme-muted transition-colors"
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
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 ${
                  verificationStatus === 'confirmed'
                    ? 'bg-teal-600 text-white'
                    : 'bg-surface-subtle text-theme-primary hover:bg-teal-50 dark:hover:bg-teal-950/40 border border-theme'
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
          <FileSearch className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
          <span>Source: {field.source}</span>
        </div>
        <div className="flex items-center gap-1.5 text-teal-700 dark:text-teal-400 hover:underline font-medium">
          <span>Highlight On Script</span>
          <ExternalLink className="w-3 h-3" />
        </div>
      </div>
    </div>
  );
};
