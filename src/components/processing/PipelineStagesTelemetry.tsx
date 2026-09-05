import React from 'react';
import {
  ProcessingStage,
  ProcessingStageId,
  LiveToken,
} from '../../types/pipeline.types';
import { Card } from '../ui/Card';
import {
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  FileCheck2,
  ShieldAlert,
  Sparkles,
  Terminal,
  Activity,
  Cpu,
} from 'lucide-react';

export interface PipelineStagesTelemetryProps {
  stages: ProcessingStage[];
  currentStageId: ProcessingStageId;
  liveTokens: LiveToken[];
  elapsedTimeMs: number;
  activeModelHead: string;
}

export const PipelineStagesTelemetry: React.FC<PipelineStagesTelemetryProps> = ({
  stages,
  currentStageId,
  liveTokens,
  elapsedTimeMs,
  activeModelHead,
}) => {
  const getStageIcon = (id: ProcessingStageId) => {
    switch (id) {
      case 'image_received':
        return Layers;
      case 'image_processing':
        return Activity;
      case 'handwriting_interpretation':
        return Cpu;
      case 'structured_extraction':
        return FileCheck2;
      case 'medicine_validation':
        return Database;
      case 'safety_analysis':
        return ShieldAlert;
      case 'explanation_synthesis':
        return Sparkles;
      default:
        return Activity;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Diagnostics HUD Strip */}
      <div className="p-3.5 rounded-lg bg-[#0E131F] border border-white/[0.08] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span className="text-slate-400">ACTIVE COGNITIVE HEAD:</span>
          <span className="text-cyan-300 font-bold">{activeModelHead}</span>
        </div>
        <div className="flex items-center gap-3 text-slate-400">
          <span className="hidden sm:inline">STAGE: <strong className="text-cyan-300 uppercase">{currentStageId.replace(/_/g, ' ')}</strong></span>
          <span>ELAPSED: <strong className="text-white">{(elapsedTimeMs / 1000).toFixed(2)}s</strong></span>
          <span>TOKENS: <strong className="text-emerald-400">{liveTokens.length}</strong></span>
        </div>
      </div>

      {/* Vertical Pipeline Nodes Grid */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-xs font-mono px-1">
          <span className="text-slate-400 uppercase tracking-wider">
            Sequential Cognitive Pipeline (7 Nodes):
          </span>
          <span className="text-[10px] text-slate-500">REAL-TIME INFERENCE STREAM</span>
        </div>

        <div className="space-y-2">
          {stages.map((stage) => {
            const isCompleted = stage.state === 'completed';
            const isActive = stage.state === 'active';
            const isFailed = stage.state === 'failed';
            const StageIcon = getStageIcon(stage.id);

            return (
              <div
                key={stage.id}
                className={`p-3 rounded-lg border transition-all flex items-start gap-3 ${
                  isActive
                    ? 'bg-cyan-950/30 border-cyan-500/60 shadow-lg'
                    : isCompleted
                    ? 'bg-[#0A0E18] border-emerald-500/20 text-slate-300'
                    : isFailed
                    ? 'bg-red-950/30 border-red-500/50'
                    : 'bg-[#080B12] border-white/[0.04] opacity-50'
                }`}
              >
                {/* Node Status Icon */}
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isActive ? (
                    <StageIcon className="w-4 h-4 text-cyan-400 animate-pulse" />
                  ) : isFailed ? (
                    <AlertCircle className="w-4 h-4 text-red-400" />
                  ) : (
                    <StageIcon className="w-4 h-4 text-slate-600" />
                  )}
                </div>

                {/* Node Content */}
                <div className="flex-1 min-w-0 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-slate-500 font-bold">
                        0{stage.stepNumber}
                      </span>
                      <h4
                        className={`text-xs font-bold font-mono tracking-tight ${
                          isActive
                            ? 'text-cyan-300'
                            : isCompleted
                            ? 'text-slate-200'
                            : 'text-slate-400'
                        }`}
                      >
                        {stage.label}
                      </h4>
                    </div>

                    <span className="text-[9px] font-mono uppercase tracking-wider">
                      {isCompleted ? (
                        <span className="text-emerald-400 font-semibold">Verified</span>
                      ) : isActive ? (
                        <span className="text-cyan-400 font-semibold animate-pulse">Running</span>
                      ) : isFailed ? (
                        <span className="text-red-400 font-semibold">Failed</span>
                      ) : (
                        <span className="text-slate-600">Pending</span>
                      )}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                    {stage.description}
                  </p>

                  {/* Active Progress Bar */}
                  {isActive && (
                    <div className="w-full h-1 bg-slate-900 rounded-full overflow-hidden mt-1.5 border border-white/5">
                      <div className="h-full bg-cyan-400 animate-pulse w-3/4 rounded-full" />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Extracted Token Stream Terminal */}
      <Card variant="glass" padding="md" className="border-white/[0.08] bg-[#070A12] rounded-lg space-y-2">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-cyan-400">
            <Terminal className="w-3.5 h-3.5" />
            <span className="font-bold">LIVE RECOGNIZED TOKEN STREAM</span>
          </div>
          <span className="text-[10px] text-slate-500">AUTO-SCROLLING</span>
        </div>

        <div className="max-h-48 overflow-y-auto space-y-1.5 font-mono text-xs pr-1">
          {liveTokens.length === 0 ? (
            <div className="text-[11px] text-slate-600 py-3 text-center">
              Awaiting token classification heads...
            </div>
          ) : (
            liveTokens.map((token) => (
              <div
                key={token.id}
                className="p-2 rounded bg-black/40 border border-white/5 flex items-start justify-between gap-2 text-[11px] animate-in fade-in duration-150"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-cyan-400 font-bold">[{token.label}]:</span>
                  <span className="text-slate-200">{token.value}</span>
                </div>
                <span className="text-[10px] text-emerald-400 shrink-0">
                  {Math.round(token.confidence * 100)}%
                </span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};
