import React from 'react';
import { MOCK_PRESCRIPTION_SAMPLES } from '../../data/mockPrescriptions';
import { Badge } from '../ui/Badge';
import { Sparkles } from 'lucide-react';

export interface CuratedSamplePickerProps {
  onSelectSample: (sampleId: string) => void;
  selectedSampleId?: string;
}

export const CuratedSamplePicker: React.FC<CuratedSamplePickerProps> = ({
  onSelectSample,
  selectedSampleId,
}) => {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Or Quick-Load Curated Clinical Test Scripts:</span>
        </span>
        <span className="text-[11px] text-slate-500">1-Click Evaluation Mode</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {MOCK_PRESCRIPTION_SAMPLES.map((sample) => {
          const isSelected = selectedSampleId === sample.id;

          return (
            <button
              key={sample.id}
              onClick={() => onSelectSample(sample.id)}
              className={`p-3 rounded-lg text-left border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-cyan-950/40 border-cyan-500/60 shadow-sm'
                  : 'bg-[#0E131F] border-white/[0.06] hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between gap-1.5 mb-1">
                <span className="text-[10px] font-mono font-bold text-cyan-400">
                  {sample.id === 'rx-sample-1'
                    ? 'SAMPLE A'
                    : sample.id === 'rx-sample-2'
                    ? 'SAMPLE B'
                    : 'SAMPLE C'}
                </span>
                <Badge
                  variant={
                    sample.difficultyScore === 'Clear'
                      ? 'emerald'
                      : sample.difficultyScore === 'Moderate Cursive'
                      ? 'amber'
                      : 'coral'
                  }
                  size="xs"
                >
                  {sample.difficultyScore}
                </Badge>
              </div>

              <h4 className="text-xs font-bold text-slate-200 line-clamp-1 mb-0.5 font-sans">
                {sample.title}
              </h4>
              <p className="text-[10px] text-slate-400 line-clamp-1 font-sans">
                {sample.doctorSpecialty}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
};
