import React from 'react';
import { ProcessingSpeedMode } from '../../types/pipeline.types';
import { Gauge, Zap, Clock, Bug } from 'lucide-react';

export interface SimulationSpeedControlsProps {
  currentMode: ProcessingSpeedMode;
  onModeChange: (mode: ProcessingSpeedMode) => void;
  disabled?: boolean;
}

export const SimulationSpeedControls: React.FC<SimulationSpeedControlsProps> = ({
  currentMode,
  onModeChange,
  disabled = false,
}) => {
  const modes = [
    {
      id: 'fast' as ProcessingSpeedMode,
      label: 'Fast (~1.4s)',
      desc: 'Rapid inference pass',
      icon: Zap,
    },
    {
      id: 'normal' as ProcessingSpeedMode,
      label: 'Standard (~3.2s)',
      desc: 'Balanced clinical pipeline',
      icon: Gauge,
    },
    {
      id: 'thorough' as ProcessingSpeedMode,
      label: 'Thorough (~6.0s)',
      desc: 'Deep inspection pass',
      icon: Clock,
    },
    {
      id: 'simulate_error' as ProcessingSpeedMode,
      label: 'Simulate Error',
      desc: 'Tests 504 gateway timeout',
      icon: Bug,
    },
  ];

  return (
    <div className="p-3.5 rounded-lg bg-[#0E131F] border border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono">
      <div className="flex items-center gap-2 text-slate-300">
        <Gauge className="w-4 h-4 text-cyan-400" />
        <span className="font-bold">INFERENCE SPEED SIMULATOR:</span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
        {modes.map((m) => {
          const isSelected = currentMode === m.id;
          const ModeIcon = m.icon;

          return (
            <button
              key={m.id}
              disabled={disabled}
              onClick={() => onModeChange(m.id)}
              className={`px-3 py-1.5 rounded transition-all cursor-pointer flex items-center gap-1.5 text-[11px] disabled:opacity-40 disabled:cursor-not-allowed ${
                isSelected
                  ? m.id === 'simulate_error'
                    ? 'bg-red-950 text-red-300 border border-red-500/50 font-bold shadow-sm'
                    : 'bg-cyan-950 text-cyan-300 border border-cyan-500/50 font-bold shadow-sm'
                  : 'bg-black/40 text-slate-400 hover:text-white border border-white/5'
              }`}
              title={m.desc}
            >
              <ModeIcon className="w-3.5 h-3.5" />
              <span>{m.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
