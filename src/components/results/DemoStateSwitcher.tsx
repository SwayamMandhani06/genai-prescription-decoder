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
      label: '1. Fully Confident',
      icon: CheckCircle2,
      tag: 'Augmentin 625 Duo · 96% Match',
      variant: 'emerald',
    },
    {
      id: 'state-uncertain',
      label: '2. Uncertain Fields',
      icon: AlertCircle,
      tag: 'Pan 40 · SOS Frequency Ambiguity',
      variant: 'amber',
    },
    {
      id: 'state-lasa',
      label: '3. LASA Warning',
      icon: AlertTriangle,
      tag: 'Metformin vs Metronidazole (82%)',
      variant: 'coral',
    },
    {
      id: 'state-flagged',
      label: '4. Multiple Flagged',
      icon: ShieldAlert,
      tag: 'Prednisolone · Selective Abstention',
      variant: 'red',
    },
  ];

  return (
    <div className="p-3.5 rounded-xl bg-[#0B0F19] border border-white/10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-3 text-xs font-mono shadow-xl">
      <div className="flex items-center gap-2 text-slate-300">
        <Layers className="w-4 h-4 text-cyan-400" />
        <span className="font-bold text-white uppercase tracking-wider">
          ACADEMIC EVALUATION SCENARIOS:
        </span>
        <span className="text-slate-500 hidden sm:inline">|</span>
        <span className="text-slate-400 hidden sm:inline text-[11px]">
          Inspect 4 Critical Clinical Edge Cases
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 w-full lg:w-auto">
        {states.map((st) => {
          const isSelected = activeStateId === st.id;
          const StateIcon = st.icon;

          return (
            <button
              key={st.id}
              onClick={() => onSelectState(st.id)}
              className={`px-3 py-2 rounded-lg transition-all cursor-pointer flex flex-col items-start gap-0.5 text-left border ${
                isSelected
                  ? st.variant === 'emerald'
                    ? 'bg-emerald-950/60 border-emerald-500 text-emerald-300 font-bold shadow-md shadow-emerald-950/40'
                    : st.variant === 'amber'
                    ? 'bg-amber-950/60 border-amber-500 text-amber-300 font-bold shadow-md shadow-amber-950/40'
                    : st.variant === 'coral'
                    ? 'bg-red-950/60 border-red-500 text-red-300 font-bold shadow-md shadow-red-950/40'
                    : 'bg-red-950/80 border-red-400 text-red-200 font-bold shadow-md shadow-red-950/50'
                  : 'bg-black/40 border-white/5 text-slate-400 hover:text-slate-200 hover:bg-black/60'
              }`}
            >
              <div className="flex items-center gap-1.5 w-full">
                <StateIcon className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{st.label}</span>
              </div>
              <span className="text-[10px] text-slate-500 truncate w-full hidden sm:block">
                {st.tag}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
