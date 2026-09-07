import React from 'react';
import { ResultsDemoStateId } from '../../types/prescription.types';
import { Layers, ShieldAlert, CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';

export interface DemoStateSwitcherProps {
  activeStateId: ResultsDemoStateId;
  onSelectState: (stateId: ResultsDemoStateId) => void;
}

export const DemoStateSwitcher: React.FC<DemoStateSwitcherProps> = ({
  activeStateId,
  onSelectState,
}) => {
  const states: Array<{
    id: ResultsDemoStateId;
    label: string;
    icon: typeof CheckCircle2;
    tag: string;
    variant: 'emerald' | 'amber' | 'coral' | 'red';
  }> = [
    {
      id: 'state-confident',
      label: '1. Confident',
      icon: CheckCircle2,
      tag: 'Augmentin 625 Duo · 96%',
      variant: 'emerald',
    },
    {
      id: 'state-uncertain',
      label: '2. Uncertain',
      icon: AlertCircle,
      tag: 'Pan 40 · Ambiguity',
      variant: 'amber',
    },
    {
      id: 'state-lasa',
      label: '3. LASA Alert',
      icon: AlertTriangle,
      tag: 'Metformin Collision',
      variant: 'coral',
    },
    {
      id: 'state-flagged',
      label: '4. Abstention',
      icon: ShieldAlert,
      tag: 'Selective Abstention',
      variant: 'red',
    },
  ];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs py-2 border-b border-theme">
      <div className="flex items-center gap-2 text-theme-secondary font-medium">
        <Layers className="w-4 h-4 text-teal-600 dark:text-teal-400" />
        <span className="font-semibold text-theme-primary">Demo scenarios:</span>
        <span className="text-theme-muted hidden md:inline text-xs">
          Inspect safety responses
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {states.map((st) => {
          const isSelected = activeStateId === st.id;
          const StateIcon = st.icon;

          return (
            <button
              key={st.id}
              onClick={() => onSelectState(st.id)}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 text-xs ${
                isSelected
                  ? 'bg-teal-600 text-white font-semibold shadow-xs'
                  : 'text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle'
              }`}
              title={st.tag}
            >
              <StateIcon className="w-3.5 h-3.5" />
              <span>{st.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
