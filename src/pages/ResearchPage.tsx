import React from 'react';
import { BENCHMARK_METRICS, DATASET_EVALUATION_SUMMARY } from '../data/benchmarkData';
import { ThemeSwitcher } from '../components/layout/ThemeSwitcher';
import {
  ArrowLeft,
  FileText,
  BarChart3,
  ShieldCheck,
  Activity,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

export interface ResearchPageProps {
  onBackToHome: () => void;
  onOpenUpload?: () => void;
}

const LASA_ERROR_ANALYSIS_PAIRS = [
  {
    id: 'lasa-1',
    pair: 'Metformin 500mg ↔ Metronidazole 400mg',
    clinicalRisk: 'Antidiabetic vs Nitroimidazole Antibacterial; distinct dosing and severe hypoglycemia risk.',
    metricDistance: 'Levenshtein: 68% | Phonetic: 84%',
    preventionStatus: 'TALL MAN Enforced',
  },
  {
    id: 'lasa-2',
    pair: 'Prednisolone 5mg ↔ Prednisone 5mg',
    clinicalRisk: 'Hepatic conversion required for Prednisone; avoid in hepatic impairment.',
    metricDistance: 'Levenshtein: 91% | Phonetic: 95%',
    preventionStatus: 'Entity Disambiguated',
  },
  {
    id: 'lasa-3',
    pair: 'Clonazepam 0.5mg ↔ Lorazepam 1mg',
    clinicalRisk: 'Benzodiazepines with differing half-lives and potency; risk of excess sedation.',
    metricDistance: 'Levenshtein: 73% | Phonetic: 79%',
    preventionStatus: 'TALL MAN Enforced',
  },
];

export const ResearchPage: React.FC<ResearchPageProps> = ({ onBackToHome, onOpenUpload }) => {
  return (
    <div className="min-h-screen bg-canvas text-theme-primary flex flex-col font-sans transition-colors">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-theme py-3 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToHome}
              className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface border border-theme text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Overview</span>
            </button>

            <span className="text-theme-muted hidden sm:inline">|</span>

            <div className="hidden sm:flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-theme-primary">
                AURA-Rx
              </span>
              <span className="text-xs text-theme-muted">
                / Research Methodology &amp; Evaluation
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ThemeSwitcher />
            {onOpenUpload && (
              <button
                onClick={onOpenUpload}
                className="px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium transition-all cursor-pointer shadow-xs"
              >
                Analyze a Prescription
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12 space-y-14">
        {/* Research Title & Abstract */}
        <section className="space-y-5">
          <div className="text-xs sm:text-sm font-semibold text-teal-700 dark:text-teal-400 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span>Academic Capstone Research Prototype</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold tracking-tight text-theme-primary leading-[1.05]">
            Quantitative Evaluation &amp; Safety Architecture
          </h1>

          <p className="text-lg sm:text-xl text-theme-secondary leading-relaxed max-w-3xl">
            This research prototype investigates whether grounded multimodal vision-language architectures, coupled with ontology retrieval and calibrated epistemic abstention, can reduce clinical misinterpretation in handwritten prescription processing.
          </p>

          {/* Research Transparency & Protocol Banner */}
          <div className="p-5 sm:p-6 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-theme-primary space-y-2.5">
            <div className="flex items-center gap-2 text-amber-700 dark:text-amber-300 font-bold text-base">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <span>Research Transparency &amp; Evaluation Protocol Notice</span>
            </div>
            <p className="text-sm text-theme-secondary leading-relaxed">
              AURA-Rx is an academic research prototype. The metrics, performance comparisons, and dataset profiles presented below outline the <strong>planned evaluation framework and design target criteria</strong> for the research pipeline. Empirical benchmark numbers will be published upon completion of formal institutional ethics review and multi-center clinical validation trials. Values labeled as <em>Simulated</em> or <em>Design Target</em> are illustrative engineering references and must not be cited as finalized clinical validation results.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3">
            <div className="p-5 rounded-2xl bg-surface border border-theme space-y-1">
              <div className="text-xs font-semibold uppercase tracking-wider text-theme-muted">Evaluation protocol</div>
              <div className="text-2xl font-bold text-theme-primary mt-1">1,200 Scripts (Target)</div>
              <div className="text-xs sm:text-sm text-theme-secondary leading-relaxed mt-1">Proposed multi-center study protocol; synthetic/demo data currently used</div>
            </div>
            <div className="p-5 rounded-2xl bg-surface border border-theme space-y-1">
              <div className="text-xs font-semibold uppercase tracking-wider text-theme-muted">Baseline framework</div>
              <div className="text-2xl font-bold text-theme-primary mt-1">OCR vs VLM vs Grounded</div>
              <div className="text-xs sm:text-sm text-theme-secondary leading-relaxed mt-1">Evaluation criteria comparing OCR, general VLMs, and grounded pipeline</div>
            </div>
            <div className="p-5 rounded-2xl bg-surface border border-theme space-y-1">
              <div className="text-xs font-semibold uppercase tracking-wider text-theme-muted">Safety policy</div>
              <div className="text-2xl font-bold text-theme-primary mt-1">Selective Abstention</div>
              <div className="text-xs sm:text-sm text-theme-secondary leading-relaxed mt-1">Flags ambiguous handwriting for clinician review rather than guessing</div>
            </div>
          </div>
        </section>

        {/* 1. Quantitative Benchmark Comparison Table */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-teal-600 dark:text-teal-400" />
            <h2 className="text-2xl sm:text-3xl lg:text-[2.25rem] font-bold text-theme-primary tracking-tight leading-[1.1]">
              Comparative Benchmark Protocol (Illustrative Targets)
            </h2>
          </div>
          <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
            Target performance criteria across character error rates, entity extraction (medicine, dosage, frequency), formulary grounding, and uncertainty calibration.
          </p>

          <div className="rounded-2xl border border-theme overflow-x-auto bg-surface shadow-xs">
            <table className="w-full text-left text-sm sm:text-base">
              <thead className="bg-surface-subtle text-xs sm:text-sm font-semibold text-theme-muted border-b border-theme">
                <tr>
                  <th className="py-4 px-4 sm:px-6">Evaluation Metric</th>
                  <th className="py-4 px-4 text-theme-secondary">Conventional OCR (Simulated Baseline)</th>
                  <th className="py-4 px-4 text-theme-secondary">Zero-Shot VLM (Simulated Baseline)</th>
                  <th className="py-4 px-4 text-teal-700 dark:text-teal-300 font-bold bg-teal-50/50 dark:bg-teal-950/20">
                    AURA-Rx (Design Target)
                  </th>
                  <th className="py-4 px-4 sm:px-6 text-emerald-600 dark:text-emerald-400">Target Objective</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme text-theme-secondary">
                {BENCHMARK_METRICS.map((metric) => (
                  <tr key={metric.id} className="hover:bg-surface-subtle/50 transition-colors">
                    <td className="py-4 px-4 sm:px-6">
                      <div className="font-bold text-theme-primary text-sm sm:text-base">{metric.metric}</div>
                      <div className="text-xs sm:text-sm text-theme-muted mt-0.5">{metric.definition}</div>
                    </td>
                    <td className="py-4 px-4 text-xs sm:text-sm font-mono">{metric.traditionalOcr}</td>
                    <td className="py-4 px-4 text-xs sm:text-sm font-mono">{metric.generalVlm}</td>
                    <td className="py-4 px-4 text-xs sm:text-sm font-mono font-bold text-teal-700 dark:text-teal-300 bg-teal-50/50 dark:bg-teal-950/20">
                      {metric.auraRxModel}
                    </td>
                    <td className="py-4 px-4 sm:px-6 text-xs sm:text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                      {metric.improvement}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 2. Uncertainty & Selective Abstention Methodology */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-amber-600 dark:text-amber-400" />
            <h2 className="text-2xl sm:text-3xl lg:text-[2.25rem] font-bold text-theme-primary tracking-tight leading-[1.1]">
              Epistemic Calibration &amp; Selective Abstention
            </h2>
          </div>
          <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
            In clinical decision support, making a confident error is catastrophic. AURA-Rx computes posterior token entropy across handwriting interpretations. When epistemic uncertainty crosses the calibrated decision threshold (&tau; = 0.65), the system explicitly flags the field for human clinician verification rather than emitting an unverified candidate.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-6 rounded-2xl bg-surface border border-theme space-y-2.5">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-base sm:text-lg">
                <CheckCircle2 className="w-5 h-5" />
                <span>High Certainty State (&tau; &lt; 0.35)</span>
              </div>
              <p className="text-sm text-theme-secondary leading-relaxed">
                Clear legibility with multiple concordant visual tokens and unambiguous pharmacopeia match (e.g. &ldquo;Amoxicillin 500mg&rdquo;). Candidate displayed with evidence citations and green confidence indicator.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-surface border border-theme space-y-2.5">
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-bold text-base sm:text-lg">
                <AlertTriangle className="w-5 h-5" />
                <span>Flagged Selective Abstention (&tau; &ge; 0.65)</span>
              </div>
              <p className="text-sm text-theme-secondary leading-relaxed">
                Degraded ink, occlusions, or contradictory stroke trajectories. System yields an explicit verification warning (&ldquo;Requires Pharmacist Verification&rdquo;) and highlights the original stroke coordinate.
              </p>
            </div>
          </div>
        </section>

        {/* 3. Look-Alike Sound-Alike (LASA) Safety */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-6 h-6 text-teal-600 dark:text-teal-400" />
            <h2 className="text-2xl sm:text-3xl lg:text-[2.25rem] font-bold text-theme-primary tracking-tight leading-[1.1]">
              Phonological &amp; Orthographic LASA Differentiation
            </h2>
          </div>
          <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
            Drug confusion constitutes up to 25% of all medication dispensing errors. The pipeline cross-references recognized tokens against known ISMP and CDSCO confusion catalogs, applying TALL MAN lettering to visually emphasize distinct orthographic stems.
          </p>

          <div className="rounded-2xl border border-theme bg-surface divide-y divide-theme shadow-xs">
            {LASA_ERROR_ANALYSIS_PAIRS.map((pair) => (
              <div key={pair.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="text-sm sm:text-base font-mono font-bold text-theme-primary tracking-wide">
                    {pair.pair}
                  </div>
                  <div className="text-xs sm:text-sm text-theme-secondary leading-relaxed">
                    {pair.clinicalRisk}
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-surface-subtle text-theme-muted border border-theme">
                    {pair.metricDistance}
                  </span>
                  <span className="text-xs sm:text-sm font-semibold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 px-3 py-1 rounded-lg border border-amber-200 dark:border-amber-800">
                    {pair.preventionStatus}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 4. Dataset Characteristics */}
        <section className="space-y-4">
          <h2 className="text-2xl sm:text-3xl lg:text-[2.25rem] font-bold text-theme-primary tracking-tight leading-[1.1]">
            Evaluation Datasets (Planned &amp; Reference Framework)
          </h2>
          <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
            The dataset specifications below outline the prospective multi-center collection protocol and reference open-access benchmark corpus established for pipeline evaluation.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {DATASET_EVALUATION_SUMMARY.map((ds) => (
              <div key={ds.name} className="p-5 sm:p-6 rounded-2xl bg-surface border border-theme space-y-2.5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-theme-primary">{ds.name}</h3>
                    {ds.statusTag && (
                      <span className="inline-block mt-1 text-xs font-medium px-2.5 py-0.5 rounded-full bg-surface-subtle border border-theme text-theme-muted">
                        {ds.statusTag}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-surface-subtle border border-theme text-theme-secondary shrink-0 font-medium">
                    {ds.sampleCount}
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed">{ds.origin}</p>
                <div className="text-xs text-theme-muted pt-2 border-t border-theme">
                  Styles: {ds.handwritingStyles}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 5. Scope and Safety Declaration */}
        <section className="p-6 sm:p-8 rounded-3xl bg-surface-subtle border border-theme space-y-3">
          <h3 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
            Academic Scope &amp; Assistive Nature
          </h3>
          <p className="text-sm sm:text-base text-theme-secondary leading-relaxed">
            AURA-Rx is developed as an academic research prototype. It is explicitly designed as an assistive document understanding tool to help patients and healthcare staff read ambiguous handwriting. It does not replace registered pharmacists or physicians, does not diagnose medical conditions, and does not alter prescribed medications.
          </p>
        </section>
      </main>
    </div>
  );
};
