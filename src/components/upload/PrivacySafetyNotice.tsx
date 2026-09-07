import React from 'react';
import { Card } from '../ui/Card';
import { ShieldCheck, Lock, AlertTriangle } from 'lucide-react';

export const PrivacySafetyNotice: React.FC = () => {
  return (
    <Card variant="subtle" padding="md" className="rounded-2xl space-y-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-theme-primary uppercase tracking-wider">
        <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />
        <span>Privacy & Clinical Safety Principles</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-theme-secondary">
        <div className="p-3 rounded-xl bg-surface border border-theme space-y-1">
          <div className="flex items-center gap-1.5 font-semibold text-theme-primary text-xs">
            <Lock className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
            <span>Session Memory Isolation</span>
          </div>
          <p className="text-[11px] text-theme-secondary leading-relaxed">
            Uploaded prescription scans are processed locally in session memory. Images are not retained or used for public training.
          </p>
        </div>

        <div className="p-3 rounded-xl bg-surface border border-theme space-y-1">
          <div className="flex items-center gap-1.5 font-semibold text-theme-primary text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
            <span>Prescriber Ground Truth</span>
          </div>
          <p className="text-[11px] text-theme-secondary leading-relaxed">
            The physician&rsquo;s signed physical prescription remains the legal anchor. The AI provides assistive interpretation.
          </p>
        </div>

        <div className="p-3 rounded-xl bg-surface border border-theme space-y-1">
          <div className="flex items-center gap-1.5 font-semibold text-theme-primary text-xs">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            <span>Mandatory Verification</span>
          </div>
          <p className="text-[11px] text-theme-secondary leading-relaxed">
            Whenever ink ambiguity exceeds safety thresholds, the system flags the field for pharmacist verification rather than guessing.
          </p>
        </div>
      </div>
    </Card>
  );
};
