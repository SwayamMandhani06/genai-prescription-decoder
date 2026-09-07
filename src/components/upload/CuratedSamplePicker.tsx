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
      <div className="flex items-center justify-between text-xs">
        <span className="text-theme-secondary font-medium flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
          <span>Or evaluate with curated test scripts:</span>
        </span>
        <span className="text-[11px] text-theme-muted">Sample Prescriptions</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {MOCK_PRESCRIPTION_SAMPLES.map((sample) => {
          const isSelected = selectedSampleId === sample.id;

          return (
            <button
              key={sample.id}
              onClick={() => onSelectSample(sample.id)}
              className={`p-3 rounded-xl text-left border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-teal-50 dark:bg-teal-950/40 border-teal-500 shadow-xs'
                  : 'bg-surface border-theme hover:border-theme-hover shadow-xs'
              }`}
            >
              <div className="flex items-center justify-between gap-1.5 mb-1.5">
                <span className="text-xs font-semibold text-theme-primary">
                  {sample.id === 'rx-sample-1'
                    ? 'Sample 1: Standard'
                    : sample.id === 'rx-sample-2'
                    ? 'Sample 2: LASA Pair'
                    : 'Sample 3: Ambiguous'}
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

              <div className="text-xs text-theme-secondary font-medium truncate">
                {sample.medications.map((m) => m.brandName).join(', ')}
              </div>

              <div className="text-[11px] text-theme-muted mt-1">
                {sample.doctorSpecialty}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
