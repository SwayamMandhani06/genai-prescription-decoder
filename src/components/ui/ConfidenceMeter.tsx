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
      label: 'Formulary Grounded (High Confidence)',
      barColor: 'bg-emerald-600 dark:bg-emerald-400',
      textColor: 'text-emerald-700 dark:text-emerald-300',
      badgeBg: 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300',
      icon: ShieldCheck,
    },
    BORDERLINE: {
      label: 'Needs Verification (Borderline)',
      barColor: 'bg-amber-500 dark:bg-amber-400',
      textColor: 'text-amber-800 dark:text-amber-300',
      badgeBg: 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-300',
      icon: AlertTriangle,
    },
    ABSTAIN_FLAGGED: {
      label: 'Selective Abstention Activated',
      barColor: 'bg-red-600 dark:bg-red-500',
      textColor: 'text-red-700 dark:text-red-300',
      badgeBg: 'bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-800 text-red-800 dark:text-red-300',
      icon: ShieldAlert,
    },
  };

  const current = statusConfig[effectiveLevel];
  const IconComponent = current.icon;

  if (compact) {
    return (
      <div className={cn('inline-flex items-center gap-1.5 font-mono text-xs', className)}>
        <span className={cn('w-2 h-2 rounded-full', current.barColor)} aria-hidden="true" />
        <span className={cn('font-semibold', current.textColor)}>{percentage}%</span>
        {effectiveLevel === 'ABSTAIN_FLAGGED' && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 font-sans uppercase tracking-wider">
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
          <span className="text-theme-secondary flex items-center gap-1.5 font-medium">
            <IconComponent className={cn('w-3.5 h-3.5 shrink-0', current.textColor)} aria-hidden="true" />
            <span>{current.label}</span>
          </span>
          <div className="flex items-center gap-2">
            <span className="text-theme-muted font-mono text-[10px]">
              Threshold: {Math.round(threshold * 100)}%
            </span>
            <span className={cn('font-mono font-bold text-sm', current.textColor)}>
              {percentage}%
            </span>
          </div>
        </div>
      )}

      {/* Progress Bar Container with Threshold Tick */}
      <div className="relative w-full h-2 rounded-full bg-surface-subtle overflow-hidden border border-theme">
        {/* Fill */}
        <div
          className={cn('h-full rounded-full transition-all duration-300 ease-out', current.barColor)}
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        />
        {/* Calibrated Threshold Marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-stone-400 dark:bg-slate-400 z-10 pointer-events-none"
          style={{ left: `${threshold * 100}%` }}
          title={`Selective Abstention Gate: ${threshold * 100}%`}
        />
      </div>
    </div>
  );
};
