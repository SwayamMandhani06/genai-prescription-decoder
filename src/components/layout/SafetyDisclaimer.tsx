import React from 'react';
import { ShieldAlert, AlertCircle, CheckCircle2 } from 'lucide-react';

export const SafetyDisclaimer: React.FC = () => {
  return (
    <section className="py-12 bg-canvas border-y border-theme relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 rounded-2xl p-6 sm:p-8 backdrop-blur-md relative shadow-xs">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-amber-100 dark:bg-amber-500/15 border border-amber-300 dark:border-amber-500/30 text-amber-700 dark:text-amber-400 shrink-0">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-semibold uppercase tracking-widest text-amber-800 dark:text-amber-400">
                    Mandatory Clinical &amp; Safety Protocol
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-200/60 dark:bg-amber-500/20 text-amber-900 dark:text-amber-300 font-mono font-medium">
                    Academic Capstone Scope
                  </span>
                </div>
                <h3 className="text-base sm:text-lg font-bold text-theme-primary">
                  Explainable Decision Support &mdash; Not an Autonomous Prescriber
                </h3>
                <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed max-w-3xl">
                  AURA-Rx is designed strictly as an assistive medical intelligence tool to demystify complex handwritten prescription tokens for patients and healthcare workers. In compliance with statutory pharmaceutical guidelines, the <strong>physical handwritten prescription signed by a registered medical practitioner (RMP)</strong> remains the sole legal reference. Never alter medication regimens without direct consultation with a qualified physician or licensed clinical pharmacist.
                </p>
              </div>
            </div>

            <div className="shrink-0 flex flex-col sm:flex-row lg:flex-col gap-2.5 w-full lg:w-auto">
              <div className="flex items-center gap-2 text-xs text-emerald-800 dark:text-emerald-300 font-mono bg-surface px-3 py-2 rounded-lg border border-theme shadow-xs">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span>Calibrated Selective Abstention</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-teal-800 dark:text-cyan-300 font-mono bg-surface px-3 py-2 rounded-lg border border-theme shadow-xs">
                <AlertCircle className="w-4 h-4 shrink-0 text-teal-600 dark:text-cyan-400" />
                <span>Human-In-The-Loop Validation</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
