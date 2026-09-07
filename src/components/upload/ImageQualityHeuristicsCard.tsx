import React from 'react';
import { ImageQualityMetrics } from '../../types/navigation.types';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Info,
} from 'lucide-react';

export interface ImageQualityHeuristicsCardProps {
  metrics: ImageQualityMetrics | null;
}

export const ImageQualityHeuristicsCard: React.FC<ImageQualityHeuristicsCardProps> = ({
  metrics,
}) => {
  if (!metrics) {
    return (
      <Card variant="subtle" padding="md" className="text-center p-6 space-y-3">
        <div className="w-10 h-10 rounded-xl bg-surface border border-theme flex items-center justify-center mx-auto text-theme-muted">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-theme-primary">
            Image Quality Heuristics
          </h4>
          <p className="text-xs text-theme-secondary mt-1 max-w-sm mx-auto">
            When a prescription is mounted, real-time spatial resolution, contrast ratio, and legibility estimates will appear here.
          </p>
        </div>
      </Card>
    );
  }

  const isOptimal = metrics.qualityStatus === 'OPTIMAL';
  const isAcceptable = metrics.qualityStatus === 'ACCEPTABLE';

  return (
    <Card
      variant="elevated"
      padding="md"
      className="space-y-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-theme pb-3">
        <div className="flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          <h4 className="text-sm font-bold text-theme-primary">
            Image Clarity Assessment
          </h4>
        </div>
        <Badge
          variant={isOptimal ? 'emerald' : isAcceptable ? 'amber' : 'coral'}
          size="xs"
          dot
        >
          {isOptimal ? 'Clear Document' : isAcceptable ? 'Acceptable Clarity' : 'Degraded Quality'}
        </Badge>
      </div>

      {/* Grid of Heuristics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
        <div className="p-2.5 rounded-lg bg-surface-subtle border border-theme">
          <span className="text-[10px] text-theme-muted uppercase font-medium block">Resolution</span>
          <span className="text-theme-primary font-bold font-mono">
            {metrics.width} × {metrics.height}
          </span>
          <span className="text-[10px] text-theme-muted block mt-0.5">{metrics.fileSizeFormatted}</span>
        </div>

        <div className="p-2.5 rounded-lg bg-surface-subtle border border-theme">
          <span className="text-[10px] text-theme-muted uppercase font-medium block">Density</span>
          <span className="text-theme-primary font-bold font-mono">~{metrics.estimatedDpi} DPI</span>
          <span className="text-[10px] text-theme-muted block mt-0.5">{metrics.orientation}</span>
        </div>

        <div className="p-2.5 rounded-lg bg-surface-subtle border border-theme">
          <span className="text-[10px] text-theme-muted uppercase font-medium block">Readability</span>
          <span className="text-emerald-700 dark:text-emerald-400 font-bold font-mono">{metrics.readabilityScore} / 100</span>
          <span className="text-[10px] text-theme-muted block mt-0.5">Ink Legibility</span>
        </div>

        <div className="p-2.5 rounded-lg bg-surface-subtle border border-theme">
          <span className="text-[10px] text-theme-muted uppercase font-medium block">Contrast</span>
          <span className="text-theme-primary font-bold">{metrics.contrastScore}</span>
          <span className="text-[10px] text-theme-muted block mt-0.5">Edge Clarity</span>
        </div>
      </div>

      {/* Status Message Callout */}
      <div
        className={`p-3 rounded-lg text-xs flex items-start gap-2.5 ${
          isOptimal
            ? 'bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200'
            : isAcceptable
            ? 'bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200'
            : 'bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-900 dark:text-red-200'
        }`}
      >
        {isOptimal ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        )}
        <p className="leading-relaxed text-xs">{metrics.statusMessage}</p>
      </div>

      {/* Disclaimer */}
      <div className="pt-2 border-t border-theme flex items-start gap-1.5 text-[11px] text-theme-muted">
        <Info className="w-3.5 h-3.5 text-theme-muted shrink-0 mt-0.5" />
        <span>
          Pre-screening assesses edge sharpness and pixel density before multimodal interpretation; does not constitute clinical diagnostic advice.
        </span>
      </div>
    </Card>
  );
};
