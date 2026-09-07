import React from 'react';
import {
  ProcessingStage,
  ProcessingStageId,
  LiveToken,
} from '../../types/pipeline.types';
import {
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  FileCheck2,
  ShieldAlert,
  Sparkles,
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
  currentStageId: _currentStageId,
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
    <div className="space-y-4">
      {/* Top Diagnostics Strip */}
      <div className="p-3.5 rounded-xl bg-surface border border-theme flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-theme-primary">
          <Activity className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          <span className="text-theme-muted font-medium">Pipeline Focus:</span>
          <span className="font-semibold">{activeModelHead}</span>
        </div>
        <div className="flex items-center gap-3 text-theme-secondary text-xs">
          <span>Elapsed: <strong className="font-mono text-theme-primary">{(elapsedTimeMs / 1000).toFixed(1)}s</strong></span>
          <span>·</span>
          <span>Tokens: <strong className="font-mono text-teal-700 dark:text-teal-400">{liveTokens.length}</strong></span>
        </div>
      </div>

      {/* Vertical Pipeline Nodes List */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-theme-secondary px-1">
          Processing Steps (7 Stages):
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
                className={`p-3 rounded-xl border transition-all flex items-start gap-3 ${
                  isActive
                    ? 'bg-teal-50/60 dark:bg-teal-950/30 border-teal-400 dark:border-teal-700 shadow-xs'
                    : isCompleted
                    ? 'bg-surface border-theme text-theme-primary'
                    : isFailed
                    ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
                    : 'bg-surface-subtle border-theme text-theme-muted opacity-60'
                }`}
              >
                {/* Node Status Icon */}
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  ) : isActive ? (
                    <StageIcon className="w-4 h-4 text-teal-600 dark:text-teal-400 animate-pulse" />
                  ) : isFailed ? (
                    <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                  ) : (
                    <StageIcon className="w-4 h-4 text-theme-muted" />
                  )}
                </div>

                {/* Node Content */}
                <div className="flex-1 min-w-0 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] text-theme-muted font-bold">
                        0{stage.stepNumber}
                      </span>
                      <h4
                        className={`text-xs font-semibold tracking-tight ${
                          isActive
                            ? 'text-teal-800 dark:text-teal-300'
                            : isCompleted
                            ? 'text-theme-primary'
                            : 'text-theme-secondary'
                        }`}
                      >
                        {stage.label}
                      </h4>
                    </div>

                    <span className="text-[11px] font-medium">
                      {isCompleted ? (
                        <span className="text-teal-700 dark:text-teal-400">Complete</span>
                      ) : isActive ? (
                        <span className="text-teal-700 dark:text-teal-400">In Progress</span>
                      ) : isFailed ? (
                        <span className="text-red-700 dark:text-red-400">Failed</span>
                      ) : (
                        <span className="text-theme-muted">Pending</span>
                      )}
                    </span>
                  </div>

                  <p className="text-[11px] text-theme-secondary leading-relaxed">
                    {stage.description}
                  </p>

                  {/* Active Progress Bar */}
                  {isActive && (
                    <div className="w-full h-1 bg-surface-subtle rounded-full overflow-hidden mt-2 border border-theme">
                      <div className="h-full bg-teal-600 w-3/4 rounded-full" />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
