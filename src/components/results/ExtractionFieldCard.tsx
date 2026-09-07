import React from 'react';
import { ExtractedFieldItem, BoundingBox } from '../../types/prescription.types';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  FileSearch,
  ExternalLink,
  ShieldAlert,
  Info,
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
            <span
              title="Illustrative demo confidence score for prototype testing"
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
            <span className="text-xs text-theme-muted block font-medium">Demo Score</span>
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
