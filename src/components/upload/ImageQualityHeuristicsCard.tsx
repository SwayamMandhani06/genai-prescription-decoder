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
      <Card variant="glass" padding="md" className="border-white/[0.08] bg-[#0E121B] rounded-xl text-center p-6 space-y-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-white/5 flex items-center justify-center mx-auto text-slate-400">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-slate-200 font-sans">
            Optical Heuristics Awaiting Document
          </h4>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            When a prescription is mounted in the viewfinder, real-time spatial resolution, contrast ratio, and legibility estimates will appear here.
          </p>
        </div>
      </Card>
    );
  }

  const isOptimal = metrics.qualityStatus === 'OPTIMAL';
  const isAcceptable = metrics.qualityStatus === 'ACCEPTABLE';

  return (
    <Card
      variant="glass"
      padding="md"
      className={`border rounded-xl bg-[#0E121B] space-y-4 ${
        isOptimal
          ? 'border-emerald-500/30'
          : isAcceptable
          ? 'border-amber-500/30'
          : 'border-red-500/40'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-cyan-400" />
          <h4 className="text-sm font-bold text-white font-sans">
            Optical Pre-Screening Heuristics
          </h4>
        </div>
        <Badge
          variant={isOptimal ? 'emerald' : isAcceptable ? 'amber' : 'coral'}
          size="xs"
          dot
        >
          {isOptimal ? 'READY FOR INFERENCE' : isAcceptable ? 'ACCEPTABLE CLARITY' : 'DEGRADED QUALITY'}
        </Badge>
      </div>

      {/* Grid of Heuristics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs">
        <div className="p-2.5 rounded bg-black/40 border border-white/5">
          <span className="text-[10px] text-slate-400 uppercase block">Resolution</span>
          <span className="text-white font-bold">
            {metrics.width} × {metrics.height}
          </span>
          <span className="text-[9px] text-slate-500 block mt-0.5">{metrics.fileSizeFormatted}</span>
        </div>

        <div className="p-2.5 rounded bg-black/40 border border-white/5">
          <span className="text-[10px] text-slate-400 uppercase block">Optical DPI</span>
          <span className="text-cyan-300 font-bold">~{metrics.estimatedDpi} DPI</span>
          <span className="text-[9px] text-slate-500 block mt-0.5">{metrics.orientation}</span>
        </div>

        <div className="p-2.5 rounded bg-black/40 border border-white/5">
          <span className="text-[10px] text-slate-400 uppercase block">Readability Index</span>
          <span className="text-emerald-400 font-bold">{metrics.readabilityScore} / 100</span>
          <span className="text-[9px] text-slate-500 block mt-0.5">Estimated Ink Score</span>
        </div>

        <div className="p-2.5 rounded bg-black/40 border border-white/5">
          <span className="text-[10px] text-slate-400 uppercase block">Contrast Score</span>
          <span className="text-slate-200 font-bold">{metrics.contrastScore}</span>
          <span className="text-[9px] text-slate-500 block mt-0.5">Bi-tonal Edge Density</span>
        </div>
      </div>

      {/* Status Message Callout */}
      <div
        className={`p-3 rounded text-xs font-sans flex items-start gap-2.5 ${
          isOptimal
            ? 'bg-emerald-950/30 border border-emerald-500/20 text-emerald-200'
            : isAcceptable
            ? 'bg-amber-950/30 border border-amber-500/20 text-amber-200'
            : 'bg-red-950/30 border border-red-500/30 text-red-200'
        }`}
      >
        {isOptimal ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        )}
        <p className="leading-relaxed text-[11px] sm:text-xs">{metrics.statusMessage}</p>
      </div>

      {/* Academic / Clinical Disclaimer */}
      <div className="pt-2 border-t border-white/5 flex items-start gap-1.5 text-[10px] text-slate-500 font-sans">
        <Info className="w-3 h-3 text-slate-500 shrink-0 mt-0.5" />
        <span>
          Client-side optical pre-screening heuristic indicator. Evaluates edge sharpness and pixel density before multimodal tokenization; does not constitute clinical diagnostic validation.
        </span>
      </div>
    </Card>
  );
};
