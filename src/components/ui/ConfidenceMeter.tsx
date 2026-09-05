import React from 'react';
import { cn } from '../../utils/cn';
import { ConfidenceLevel } from '../../types/prescription.types';
import { ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react';

export interface ConfidenceMeterProps {
  score: number; // 0.0 to 1.0
  level?: ConfidenceLevel;
  showLabel?: boolean;
  compact?: boolean;
  className?: string;
  threshold?: number; // e.g. 0.65
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  score,
  level,
  showLabel = true,
  compact = false,
  className,
  threshold = 0.65,
}) => {
  const percentage = Math.round(score * 100);

  // Derive status if not explicitly passed
  const effectiveLevel: ConfidenceLevel =
    level ||
    (percentage >= 85
      ? 'HIGH_CONFIDENCE'
      : percentage >= threshold * 100
      ? 'BORDERLINE'
      : 'ABSTAIN_FLAGGED');

  const statusConfig = {
    HIGH_CONFIDENCE: {
      label: 'Verified High Confidence',
      barColor: 'bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.5)]',
      textColor: 'text-emerald-400',
      badgeBg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
      icon: ShieldCheck,
    },
    BORDERLINE: {
      label: 'Clinical Review Recommended',
      barColor: 'bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.5)]',
      textColor: 'text-amber-400',
      badgeBg: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
      icon: AlertTriangle,
    },
    ABSTAIN_FLAGGED: {
      label: 'Abstention Triggered (Overdose Risk)',
      barColor: 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.6)]',
      textColor: 'text-red-400',
      badgeBg: 'bg-red-500/15 border-red-500/30 text-red-300',
      icon: ShieldAlert,
    },
  };

  const current = statusConfig[effectiveLevel];
  const IconComponent = current.icon;

  if (compact) {
    return (
      <div className={cn('inline-flex items-center gap-1.5 font-mono text-xs', className)}>
        <span className={cn('w-2 h-2 rounded-full', current.barColor)} />
        <span className={cn('font-semibold', current.textColor)}>{percentage}%</span>
        {effectiveLevel === 'ABSTAIN_FLAGGED' && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-sans uppercase tracking-wider">
            Abstained
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={cn('space-y-1.5', className)}>
      {showLabel && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400 flex items-center gap-1.5 font-medium">
            <IconComponent className={cn('w-3.5 h-3.5', current.textColor)} />
            <span>{current.label}</span>
          </span>
          <div className="flex items-center gap-2">
            <span className="text-slate-500 font-mono text-[10px]">
              Threshold: {Math.round(threshold * 100)}%
            </span>
            <span className={cn('font-mono font-bold text-sm', current.textColor)}>
              {percentage}%
            </span>
          </div>
        </div>
      )}

      {/* Progress Bar Container with Threshold Tick */}
      <div className="relative w-full h-2 rounded-full bg-slate-800/80 overflow-hidden border border-white/5">
        {/* Fill */}
        <div
          className={cn('h-full rounded-full transition-all duration-500 ease-out', current.barColor)}
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        />
        {/* Calibrated Threshold Marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white/40 z-10 pointer-events-none"
          style={{ left: `${threshold * 100}%` }}
          title={`Selective Abstention Gate: ${threshold * 100}%`}
        />
      </div>
    </div>
  );
};
