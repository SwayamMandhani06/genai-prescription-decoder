import React from 'react';
import { BENCHMARK_METRICS, DATASET_EVALUATION_SUMMARY } from '../../data/benchmarkData';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { BarChart3, Database } from 'lucide-react';

export const ResearchBenchmarkSection: React.FC = () => {
  return (
    <section id="benchmarks" className="py-20 bg-[#080C16] border-t border-white/[0.08] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-14 space-y-3">
          <Badge variant="cyan" size="sm" dot>
            Capstone Research & Evaluation
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Rigorous Quantitative Evaluation
          </h2>
          <p className="text-sm sm:text-base text-slate-300">
            Evaluated on real-world outpatient clinical scripts across Indian hospital centers. Tested against traditional OCR baselines and general vision-language models.
          </p>
        </div>

        {/* Benchmark Metrics Comparison Table */}
        <Card variant="glass" padding="none" className="border-white/[0.12] mb-12 overflow-x-auto">
          <div className="p-5 sm:p-6 border-b border-white/[0.08] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              <h3 className="text-base sm:text-lg font-bold text-white">
                Model Performance Benchmark (IndoRx-1200 Test Set)
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
              Double-Blind Clinical Validation
            </span>
          </div>

          <table className="w-full text-left text-xs sm:text-sm font-sans">
            <thead className="bg-slate-950/80 font-mono text-[11px] text-slate-400 border-b border-white/[0.08] uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4 sm:px-6">Evaluation Metric</th>
                <th className="py-3.5 px-4">Traditional OCR (Tesseract 5.3)</th>
                <th className="py-3.5 px-4">Zero-Shot VLM (General)</th>
                <th className="py-3.5 px-4 text-cyan-300 font-bold bg-cyan-950/20">
                  AURA-Rx (Proposed Grounded Pipeline)
                </th>
                <th className="py-3.5 px-4 sm:px-6 text-emerald-400">Improvement Margin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06] text-slate-200">
              {BENCHMARK_METRICS.map((metric) => (
                <tr key={metric.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-4 px-4 sm:px-6">
                    <div className="font-bold text-white">{metric.metric}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{metric.definition}</div>
                  </td>
                  <td className="py-4 px-4 font-mono text-slate-400">{metric.traditionalOcr}</td>
                  <td className="py-4 px-4 font-mono text-slate-400">{metric.generalVlm}</td>
                  <td className="py-4 px-4 font-mono font-bold text-cyan-300 bg-cyan-950/20">
                    {metric.auraRxModel}
                  </td>
                  <td className="py-4 px-4 sm:px-6 font-mono text-xs text-emerald-400 font-semibold">
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
            <Card key={ds.name} variant="subtle" padding="md" className="border-white/[0.08]">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <h4 className="text-sm font-bold text-white font-mono">{ds.name}</h4>
                </div>
                <Badge variant="cyan" size="xs">
                  {ds.sampleCount} Annotated Prescriptions
                </Badge>
              </div>

              <div className="space-y-2 text-xs text-slate-300">
                <div>
                  <strong className="text-slate-400 font-mono text-[11px] uppercase block">
                    Geographic & Clinical Origin:
                  </strong>
                  <span>{ds.origin}</span>
                </div>
                <div>
                  <strong className="text-slate-400 font-mono text-[11px] uppercase block">
                    Handwriting Variability:
                  </strong>
                  <span>{ds.handwritingStyles}</span>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {ds.doctorSpecialties.map((spec) => (
                    <span
                      key={spec}
                      className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-300 border border-white/5"
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
