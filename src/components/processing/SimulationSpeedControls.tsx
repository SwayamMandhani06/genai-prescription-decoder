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
      desc: 'Tests 504 timeout recovery',
      icon: Bug,
    },
  ];

  return (
    <div className="p-3.5 rounded-2xl bg-surface border border-theme flex flex-col sm:flex-row items-center justify-between gap-3 text-xs shadow-xs">
      <div className="flex items-center gap-2 text-theme-primary font-medium">
        <Gauge className="w-4 h-4 text-teal-600 dark:text-teal-400" />
        <span>Simulation Speed:</span>
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
              className={`px-3 py-1.5 rounded-xl transition-all cursor-pointer flex items-center gap-1.5 text-xs disabled:opacity-40 disabled:cursor-not-allowed ${
                isSelected
                  ? m.id === 'simulate_error'
                    ? 'bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-300 border border-red-300 dark:border-red-800 font-semibold'
                    : 'bg-teal-50 dark:bg-teal-950/40 text-teal-800 dark:text-teal-300 border border-teal-300 dark:border-teal-800 font-semibold'
                  : 'bg-surface-subtle text-theme-secondary hover:text-theme-primary border border-theme'
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
