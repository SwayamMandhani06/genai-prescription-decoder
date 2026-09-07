import React from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  FileCheck2,
  Lock,
} from 'lucide-react';

export const SafetyPhilosophySection: React.FC = () => {
  return (
    <section id="safety" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Lead */}
        <div className="max-w-3xl mb-14 sm:mb-18 space-y-4">
          <div className="text-sm font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" />
            <span>Epistemic Uncertainty &amp; Patient Safety</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-[2.5rem] font-bold tracking-tight text-theme-primary leading-[1.08]">
            The system should know when it does not know.
          </h2>

          <p className="text-lg sm:text-xl text-theme-secondary leading-[1.65]">
            In medical artificial intelligence, false confidence is dangerous. When physician handwriting is legible, AURA-Rx resolves the regimen. When ink is degraded or ambiguous, the system intentionally abstains from guessing and requests human verification.
          </p>
        </div>

        {/* Visually Distinctive Conceptual Comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
          {/* Case 1: Clear Handwriting -> Interpretation */}
          <div className="p-7 sm:p-9 rounded-3xl bg-surface shadow-elevated-card border border-theme flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs sm:text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                  Example 1 &middot; Legible handwriting
                </span>
                <span className="inline-flex items-center gap-1 text-xs sm:text-sm font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Interpretation verified</span>
                </span>
              </div>

              {/* Sample Ink */}
              <div className="p-4 rounded-xl prescription-paper border border-amber-900/15 dark:border-white/15">
                <div className="text-xs text-slate-600 mb-1 font-medium">
                  Legible physician script
                </div>
                <div className="font-serif italic text-xl sm:text-2xl text-blue-900 font-bold py-1">
                  ℞ Pan 40 &mdash; 1 tab OD (AC) x 5 days
                </div>
              </div>

              {/* System Analysis */}
              <div className="space-y-2.5 text-sm">
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Handwriting clarity</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">High legibility</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Confidence</span>
                  <span className="font-semibold text-theme-primary">94% (Illustrative demo score)</span>
                </div>
                <div className="flex items-center justify-between py-1 text-theme-secondary">
                  <span>Formulary match</span>
                  <span className="font-bold text-theme-primary">Matched: Pantoprazole 40mg</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface-subtle border border-theme text-sm text-theme-secondary leading-[1.6]">
                <strong className="text-theme-primary font-medium">System Outcome:</strong> High certainty achieved. Dosage, meal relation (before breakfast), and duration resolved cleanly.
              </div>
            </div>

            <div className="text-xs text-theme-muted pt-2 border-t border-theme flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>Resolved with verified clinical evidence</span>
            </div>
          </div>

          {/* Case 2: Ambiguous Handwriting -> Flagged for Verification */}
          <div className="p-7 sm:p-9 rounded-3xl bg-surface shadow-elevated-card border border-theme flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs sm:text-sm font-semibold text-amber-700 dark:text-amber-400">
                  Example 2 &middot; Ambiguous handwriting
                </span>
                <span className="inline-flex items-center gap-1 text-xs sm:text-sm font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Selective abstention</span>
                </span>
              </div>

              {/* Sample Ink */}
              <div className="p-4 rounded-xl prescription-paper border border-amber-900/15 dark:border-white/15">
                <div className="text-xs text-slate-600 mb-1 font-medium">
                  Hurried cursive scrawl with ambiguous letters
                </div>
                <div className="font-serif italic text-xl sm:text-2xl text-blue-900 font-bold py-1">
                  ℞ Hydr... 25mg &mdash; 1 tab HS
                </div>
              </div>

              {/* System Analysis */}
              <div className="space-y-2.5 text-sm">
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Handwriting clarity</span>
                  <span className="font-semibold text-amber-600 dark:text-amber-400">Ambiguous cursive loop</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Confidence</span>
                  <span className="font-semibold text-amber-600 dark:text-amber-400">Low confidence threshold</span>
                </div>
                <div className="flex items-center justify-between py-1 text-theme-secondary">
                  <span>Sound-alike conflict</span>
                  <span className="font-bold text-amber-800 dark:text-amber-300">hydrOXYzine vs hydrALAzine</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-sm text-amber-900 dark:text-amber-300 leading-[1.6]">
                <strong>System Outcome:</strong> Abstention triggered. Rather than guessing between an antihistamine and a vasodilator, the system flags the script for pharmacist verification.
              </div>
            </div>

            <div className="text-xs text-theme-muted pt-2 border-t border-theme flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
              <span>Safety barrier active &mdash; protects patient from dispensing errors</span>
            </div>
          </div>
        </div>

        {/* Ground Truth Reassurance */}
        <div className="mt-10 p-5 rounded-2xl bg-surface-subtle border border-theme flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-surface border border-theme flex items-center justify-center text-teal-700 dark:text-teal-300 shrink-0 shadow-xs">
              <FileCheck2 className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-base sm:text-lg font-bold text-theme-primary">
                The original prescription is always preserved.
              </h4>
              <p className="text-sm text-theme-secondary">
                AURA-Rx never obscures the doctor&rsquo;s physical ink. Every interpretation links back to spatial pixel coordinates.
              </p>
            </div>
          </div>

          <div className="text-xs sm:text-sm text-theme-muted shrink-0 font-medium">
            Assistive clinical tool
          </div>
        </div>
      </div>
    </section>
  );
};
