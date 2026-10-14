import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  FileCheck2,
  Lock,
} from 'lucide-react';

export const SafetyPhilosophySection: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="safety" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Lead */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="max-w-3xl mb-14 sm:mb-18 space-y-4"
        >
          <div className="text-sm font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" />
            <span>Epistemic Uncertainty &amp; Patient Safety</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-[2.85rem] font-extrabold tracking-tight text-theme-primary leading-[1.08]">
            The system should know when it does not know.
          </h2>

          <p className="text-lg sm:text-xl text-theme-secondary leading-[1.65]">
            In medical artificial intelligence, false confidence is dangerous. When physician handwriting is legible, DawaAI resolves the regimen. When ink is degraded or ambiguous, the system intentionally abstains from guessing and requests human verification.
          </p>
        </motion.div>

        {/* Visually Distinctive Conceptual Comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
          {/* Case 1: Clear Handwriting -> Interpretation */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.55, ease: 'easeOut' }}
            className="p-7 sm:p-9 rounded-3xl bg-surface card-border-interactive shadow-elevated-card flex flex-col justify-between space-y-6"
          >
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

              {/* Sample Ink Preview Asset */}
              <div className="rounded-xl overflow-hidden border border-theme bg-white shadow-xs p-1">
                <img
                  src="/samples/clear-prescription-sample.png"
                  alt="Clear prescription sample: Cap. Pan 40mg 1-0-0 x 5d (A.C. 30m before food)"
                  className="w-full h-44 sm:h-48 object-cover object-center block bg-white rounded-lg"
                  loading="lazy"
                />
              </div>

              {/* System Analysis */}
              <div className="space-y-2.5 text-sm">
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Prescription text</span>
                  <span className="font-semibold text-theme-primary font-mono text-xs">Cap. Pan 40mg 1-0-0 x 5d (A.C. 30m before food)</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Handwriting clarity</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">High legibility</span>
                </div>
                <div className="flex items-center justify-between py-1 text-theme-secondary">
                  <span>Formulary match</span>
                  <span className="font-bold text-theme-primary">Matched: Pantoprazole 40mg (Pan 40)</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface-subtle border border-theme text-sm text-theme-secondary leading-[1.6]">
                <strong className="text-theme-primary font-medium">System Outcome:</strong> High certainty achieved. Dosage (40mg), frequency (once daily morning), meal relation (30m before food), and duration (5 days) resolved cleanly.
              </div>
            </div>

            <div className="text-xs text-theme-muted pt-2 border-t border-theme flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>Resolved with verified clinical evidence</span>
            </div>
          </motion.div>

          {/* Case 2: Ambiguous Handwriting -> Flagged for Verification */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.55, delay: shouldReduceMotion ? 0 : 0.1, ease: 'easeOut' }}
            className="p-7 sm:p-9 rounded-3xl bg-surface card-border-interactive shadow-elevated-card flex flex-col justify-between space-y-6"
          >
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

              {/* Sample Ink Preview Asset */}
              <div className="rounded-xl overflow-hidden border border-theme bg-white shadow-xs p-1">
                <img
                  src="/samples/ambiguous-prescription-sample.png"
                  alt="Ambiguous prescription sample: Tab. Cetcip 10mg 0-0-1 (H.S.) with ink artifacts"
                  className="w-full h-44 sm:h-48 object-cover object-center block bg-white rounded-lg"
                  loading="lazy"
                />
              </div>

              {/* System Analysis */}
              <div className="space-y-2.5 text-sm">
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Prescription text</span>
                  <span className="font-semibold text-amber-800 dark:text-amber-300 font-mono text-xs">Tab. Cetcip 10mg 0-0-1 (H.S.)</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-theme text-theme-secondary">
                  <span>Handwriting clarity</span>
                  <span className="font-semibold text-amber-600 dark:text-amber-400">Degraded ink &amp; smudged characters</span>
                </div>
                <div className="flex items-center justify-between py-1 text-theme-secondary">
                  <span>Unresolved field</span>
                  <span className="font-bold text-amber-800 dark:text-amber-300">Requires human verification</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-sm text-amber-900 dark:text-amber-300 leading-[1.6]">
                <strong>System Outcome:</strong> Selective abstention triggered. The system abstains from guessing ambiguous cursive characters or damaged ink and clearly indicates the need for professional pharmacist verification.
              </div>
            </div>

            <div className="text-xs text-theme-muted pt-2 border-t border-theme flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
              <span>Safety barrier active &mdash; protects patient from dispensing errors</span>
            </div>
          </motion.div>
        </div>

        {/* Ground Truth Reassurance */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.5, delay: shouldReduceMotion ? 0 : 0.08, ease: 'easeOut' }}
          className="mt-10 p-5 rounded-2xl bg-surface-subtle card-border-subtle flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-surface border border-theme flex items-center justify-center text-[#155EEF] dark:text-[#4B8BFF] shrink-0 shadow-xs">
              <FileCheck2 className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-base sm:text-lg font-bold text-theme-primary">
                The original prescription is always preserved.
              </h4>
              <p className="text-sm text-theme-secondary">
                DawaAI never obscures the doctor&rsquo;s physical ink. Every interpretation links back to spatial pixel coordinates.
              </p>
            </div>
          </div>

          <div className="text-xs sm:text-sm text-theme-muted shrink-0 font-medium">
            Assistive clinical tool
          </div>
        </motion.div>
      </div>
    </section>
  );
};
