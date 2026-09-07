import React from 'react';
import { BENCHMARK_METRICS, DATASET_EVALUATION_SUMMARY } from '../../data/benchmarkData';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { BarChart3, Database } from 'lucide-react';

export const ResearchBenchmarkSection: React.FC = () => {
  return (
    <section id="benchmarks" className="py-20 bg-canvas border-t border-theme relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-14 space-y-3">
          <Badge variant="cyan" size="sm" dot>
            Capstone Research & Evaluation
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-theme-primary tracking-tight">
            Rigorous Quantitative Evaluation
          </h2>
          <p className="text-sm sm:text-base text-theme-secondary">
            Evaluated on real-world outpatient clinical scripts across Indian hospital centers. Tested against traditional OCR baselines and general vision-language models.
          </p>
        </div>

        {/* Benchmark Metrics Comparison Table */}
        <Card variant="glass" padding="none" className="border-theme mb-12 overflow-x-auto shadow-xs">
          <div className="p-5 sm:p-6 border-b border-theme flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-teal-600 dark:text-cyan-400" />
              <h3 className="text-base sm:text-lg font-bold text-theme-primary">
                Model Performance Benchmark (IndoRx-1200 Test Set)
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-300 dark:border-emerald-500/20 font-semibold">
              Double-Blind Clinical Validation
            </span>
          </div>

          <table className="w-full text-left text-xs sm:text-sm font-sans">
            <thead className="bg-surface-subtle font-mono text-[11px] text-theme-secondary border-b border-theme uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4 sm:px-6 font-semibold">Evaluation Metric</th>
                <th className="py-3.5 px-4 font-semibold">Traditional OCR (Tesseract 5.3)</th>
                <th className="py-3.5 px-4 font-semibold">Zero-Shot VLM (General)</th>
                <th className="py-3.5 px-4 text-teal-800 dark:text-cyan-300 font-bold bg-teal-50/60 dark:bg-cyan-950/20">
                  AURA-Rx (Proposed Grounded Pipeline)
                </th>
                <th className="py-3.5 px-4 sm:px-6 text-emerald-700 dark:text-emerald-400 font-semibold">Improvement Margin</th>
              </tr>
            </thead>
            <tbody className="divide-y border-theme text-theme-secondary">
              {BENCHMARK_METRICS.map((metric) => (
                <tr key={metric.id} className="hover:bg-surface-subtle/50 transition-colors">
                  <td className="py-4 px-4 sm:px-6">
                    <div className="font-bold text-theme-primary">{metric.metric}</div>
                    <div className="text-[11px] text-theme-muted mt-0.5">{metric.definition}</div>
                  </td>
                  <td className="py-4 px-4 font-mono text-theme-secondary">{metric.traditionalOcr}</td>
                  <td className="py-4 px-4 font-mono text-theme-secondary">{metric.generalVlm}</td>
                  <td className="py-4 px-4 font-mono font-bold text-teal-900 dark:text-cyan-300 bg-teal-50/40 dark:bg-cyan-950/20">
                    {metric.auraRxModel}
                  </td>
                  <td className="py-4 px-4 sm:px-6 font-mono text-xs text-emerald-700 dark:text-emerald-400 font-semibold">
                    {metric.improvement}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* Dataset Breakdown Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {DATASET_EVALUATION_SUMMARY.map((ds) => (
            <Card key={ds.name} variant="subtle" padding="md" className="border-theme">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-teal-600 dark:text-cyan-400" />
                  <h4 className="text-sm font-bold text-theme-primary font-mono">{ds.name}</h4>
                </div>
                <Badge variant="cyan" size="xs">
                  {ds.sampleCount} Annotated Prescriptions
                </Badge>
              </div>

              <div className="space-y-2 text-xs text-theme-secondary">
                <div>
                  <strong className="text-theme-muted font-mono text-[11px] uppercase block">
                    Geographic & Clinical Origin:
                  </strong>
                  <span>{ds.origin}</span>
                </div>
                <div>
                  <strong className="text-theme-muted font-mono text-[11px] uppercase block">
                    Handwriting Variability:
                  </strong>
                  <span>{ds.handwritingStyles}</span>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {ds.doctorSpecialties.map((spec) => (
                    <span
                      key={spec}
                      className="px-2 py-0.5 rounded bg-surface border border-theme text-[10px] font-mono text-theme-secondary"
                    >
                      {spec}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};
