import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { ConfidenceMeter } from '../ui/ConfidenceMeter';
import {
  ShieldAlert,
  Sliders,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

export const UncertaintyAbstentionSection: React.FC = () => {
  const [threshold, setThreshold] = useState<number>(0.65);

  const testTokens = [
    {
      id: 'tok-1',
      field: 'Amoxicillin 500mg',
      rawInkDesc: 'Clear baseline stroke with full character ascenders',
      calibratedScore: 0.94,
    },
    {
      id: 'tok-2',
      field: 'Pantoprazole 40mg',
      rawInkDesc: 'Standard clinical cursive with minor trailing ligature',
      calibratedScore: 0.82,
    },
    {
      id: 'tok-3',
      field: 'Prednisolone [1.0mg vs 10mg]',
      rawInkDesc: 'Degraded decimal point with ambiguous pen lift (decimal ligature ambiguity)',
      calibratedScore: 0.58,
    },
    {
      id: 'tok-4',
      field: 'Clopidogrel 75mg [Smudged]',
      rawInkDesc: 'Ink smear over prefix stroke ("Clo-" vs "Flu-")',
      calibratedScore: 0.44,
    },
  ];

  return (
    <section id="uncertainty" className="py-20 bg-canvas border-t border-theme relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-14 space-y-3">
          <Badge variant="amber" size="sm" dot>
            Safety Engineering
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-theme-primary tracking-tight">
            The System Knows When It Is Uncertain
          </h2>
          <p className="text-sm sm:text-base text-theme-secondary">
            In medicine, guessing is dangerous. When clinical cursive strokes are ambiguous, AURA-Rx activates calibrated selective prediction: deliberately refusing to transcribe rather than guessing on ambiguous medication strength.
          </p>
        </div>

        {/* The Core Distinction: Naive LLM vs Calibrated Abstention */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {/* Card 1: Naive Generative AI Hazard */}
          <Card variant="coral" padding="lg">
            <div className="flex items-start gap-3.5 mb-4">
              <div className="p-2.5 rounded-lg bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 border border-red-300 dark:border-red-500/30 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-theme-primary">
                  The Conventional Generative AI Hazard
                </h3>
                <p className="text-xs text-red-800 dark:text-red-300 font-mono mt-0.5">
                  Overconfident Guessing Under Ambiguity
                </p>
              </div>
            </div>
            <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed mb-4">
              Standard large vision-language models are trained with next-token prediction objectives that force a generated answer even when visual ink is illegible. When encountering an ambiguous cursive stroke like <code className="text-red-700 dark:text-red-300 font-mono font-semibold">1.0 mg vs 10 mg</code>, an uncalibrated LLM will predict a token without communicating uncertainty, risking dosage errors.
            </p>
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/30 text-xs font-mono text-red-900 dark:text-red-300">
              ❌ Baseline Hazard: Forced generation on unreadable strokes without uncertainty calibration
            </div>
          </Card>

          {/* Card 2: AURA-Rx Calibrated Abstention */}
          <Card variant="cyan" padding="lg">
            <div className="flex items-start gap-3.5 mb-4">
              <div className="p-2.5 rounded-lg bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-500/30 shrink-0">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-theme-primary">
                  AURA-Rx Selective Prediction Gate
                </h3>
                <p className="text-xs text-emerald-800 dark:text-emerald-300 font-mono mt-0.5">
                  Cost-Sensitive Abstention &amp; Escalation
                </p>
              </div>
            </div>
            <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed mb-4">
              Our architecture measures predictive token entropy. If visual ambiguity exceeds the calibrated clinical safety threshold, the system abstains from autonomous decoding and immediately flags the prescription for human clinician or pharmacist verification.
            </p>
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/30 text-xs font-mono text-emerald-900 dark:text-emerald-300">
              ✅ Selective Policy: Flags uncertain strokes for verification rather than outputting guesses
            </div>
          </Card>
        </div>

        {/* Interactive Calibrated Threshold Simulator */}
        <Card variant="glass" padding="lg" className="border-theme">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pb-6 border-b border-theme mb-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <h3 className="text-lg font-bold text-theme-primary">
                  Interactive Calibrated Threshold Gate (Illustrative Simulator)
                </h3>
              </div>
              <p className="text-xs text-theme-secondary">
                Adjust the clinical confidence threshold below to observe how the model dynamically triggers abstention flags on borderline tokens.
              </p>
            </div>

            {/* Threshold Slider */}
            <div className="flex items-center gap-4 bg-surface-subtle p-3 rounded-xl border border-theme w-full lg:w-auto">
              <span className="text-xs font-mono text-theme-secondary whitespace-nowrap">
                Gate Threshold:
              </span>
              <input
                type="range"
                min="0.50"
                max="0.90"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-40 sm:w-48 accent-teal-600 dark:accent-cyan-400 cursor-pointer"
                aria-label="Selective Abstention Gate Threshold"
              />
              <span className="text-sm font-mono font-bold text-teal-700 dark:text-cyan-400 w-12 text-right">
                {Math.round(threshold * 100)}%
              </span>
            </div>
          </div>

          {/* Token Simulation Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {testTokens.map((tok) => {
              const willAbstain = tok.calibratedScore < threshold;

              return (
                <div
                  key={tok.id}
                  className={`p-4 rounded-xl border transition-all ${
                    willAbstain
                      ? 'bg-red-50/60 dark:bg-red-950/20 border-red-300 dark:border-red-500/40'
                      : 'bg-surface border-theme'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h4 className="text-sm font-bold text-theme-primary font-mono">{tok.field}</h4>
                      <p className="text-[11px] text-theme-muted mt-0.5">{tok.rawInkDesc}</p>
                    </div>
                    <Badge variant={willAbstain ? 'coral' : 'emerald'} size="xs" dot>
                      {willAbstain ? 'ABSTAINED' : 'ACCEPTED'}
                    </Badge>
                  </div>

                  <ConfidenceMeter
                    score={tok.calibratedScore}
                    threshold={threshold}
                    className="mt-3"
                  />

                  {willAbstain ? (
                    <div className="mt-3 p-2 rounded-lg bg-red-50 dark:bg-red-500/10 text-[11px] font-mono text-red-800 dark:text-red-300 border border-red-200 dark:border-red-500/20 flex items-center gap-1.5">
                      <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-red-600 dark:text-red-400" />
                      <span>Action: Mandatory Pharmacist Physical Script Confirmation</span>
                    </div>
                  ) : (
                    <div className="mt-3 p-2 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-[11px] font-mono text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/20 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                      <span>Action: Passed Clinical Gate → Forwarded to Explanation Engine</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </section>
  );
};
