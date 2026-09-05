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
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>CONFIDENT · High Confidence</span>
          </div>
        );
      case 'uncertain':
        return (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>UNCERTAIN · Needs Verification</span>
          </div>
        );
      case 'flagged':
        return (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-red-500/20 text-red-300 border border-red-500/40">
            <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
            <span>FLAGGED · Do Not Rely on Interpretation</span>
          </div>
        );
    }
  };

  const getBorderAndBgStyle = () => {
    if (field.status === 'flagged') {
      return 'bg-red-950/20 border-red-500/40 hover:border-red-500/60 shadow-lg shadow-red-950/20';
    }
    if (field.status === 'uncertain') {
      return 'bg-amber-950/20 border-amber-500/40 hover:border-amber-500/60 shadow-lg shadow-amber-950/15';
    }
    if (isActive) {
      return 'bg-cyan-950/30 border-cyan-400 shadow-lg shadow-cyan-950/30';
    }
    return 'bg-[#0B0F19] border-white/[0.08] hover:border-cyan-500/30';
  };

  const confidencePercent = Math.round(field.confidence * 100);

  return (
    <div
      onMouseEnter={() => onHover && onHover(field.boundingBox, field.fieldName)}
      onMouseLeave={() => onLeave && onLeave()}
      className={`p-4 rounded-xl border transition-all duration-200 space-y-3 cursor-pointer ${getBorderAndBgStyle()}`}
    >
      {/* Top Header: Field Name, Status Badge, and Confidence Score */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="space-y-0.5">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
            {field.fieldName}
          </span>
          <div className="text-base sm:text-lg font-bold text-white font-mono tracking-tight">
            {field.value}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {getStatusBadge()}
          <div className="text-right font-mono">
            <span
              className={`text-xs font-bold ${
                field.status === 'confident'
                  ? 'text-emerald-400'
                  : field.status === 'uncertain'
                  ? 'text-amber-400'
                  : 'text-red-400'
              }`}
            >
              {confidencePercent}%
            </span>
            <span className="text-[10px] text-slate-500 block uppercase">CALIBRATED</span>
          </div>
        </div>
      </div>

      {/* Visual Confidence Meter Bar */}
      <div className="space-y-1">
        <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-white/5 flex">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              field.status === 'confident'
                ? 'bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_8px_#34d399]'
                : field.status === 'uncertain'
                ? 'bg-gradient-to-r from-amber-500 to-yellow-400 shadow-[0_0_8px_#fbbf24]'
                : 'bg-gradient-to-r from-red-600 to-red-400 shadow-[0_0_8px_#f87171]'
            }`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Technical Explanation & Clinical Rationale */}
      <div className="text-xs text-slate-300 font-sans leading-relaxed">
        {field.explanation}
      </div>

      {/* Special First-Class Uncertainty & Verification Instructions */}
      {field.status === 'uncertain' && (
        <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-500/30 space-y-1.5 text-xs text-amber-200 animate-in fade-in">
          <div className="flex items-center gap-1.5 font-bold font-mono text-amber-300">
            <Info className="w-3.5 h-3.5 text-amber-400" />
            <span>AMBIGUITY REASON &amp; VERIFICATION INSTRUCTION</span>
          </div>
          {field.uncertaintyReason && (
            <p className="font-sans text-[11px] text-amber-200/90">
              <strong className="text-amber-300">Observation:</strong> {field.uncertaintyReason}
            </p>
          )}
          {field.interpretedCandidate && (
            <p className="font-mono text-[11px] text-amber-300">
              <strong>Interpreted Candidate:</strong> {field.interpretedCandidate}
            </p>
          )}
          {field.verificationInstruction && (
            <p className="font-sans text-[11px] text-amber-100 bg-amber-900/30 p-1.5 rounded border border-amber-500/20">
              <strong className="text-white">Action Required:</strong>{' '}
              {field.verificationInstruction}
            </p>
          )}
        </div>
      )}

      {/* Special Prominent Flagged / Selective Abstention Notice */}
      {field.status === 'flagged' && (
        <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 space-y-1.5 text-xs text-red-200 animate-in fade-in">
          <div className="flex items-center gap-1.5 font-bold font-mono text-red-300">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>SELECTIVE ABSTENTION PROTOCOL ACTIVATED</span>
          </div>
          {field.uncertaintyReason && (
            <p className="font-sans text-[11px] text-red-200/90">
              <strong className="text-red-300">Hazard Analysis:</strong> {field.uncertaintyReason}
            </p>
          )}
          {field.verificationInstruction && (
            <p className="font-sans text-[11px] text-red-100 bg-red-900/40 p-2 rounded border border-red-500/30 leading-relaxed font-semibold">
              {field.verificationInstruction}
            </p>
          )}
        </div>
      )}

      {/* Card Footer: Physical Stroke Attribution & Bounding Box Coordinates */}
      <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[10px] font-mono text-slate-500">
        <div className="flex items-center gap-1 text-slate-400">
          <FileSearch className="w-3 h-3 text-cyan-400" />
          <span>Source: {field.source}</span>
        </div>
        <div className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300">
          <span>Highlight On Script</span>
          <ExternalLink className="w-2.5 h-2.5" />
        </div>
      </div>
    </div>
  );
};
