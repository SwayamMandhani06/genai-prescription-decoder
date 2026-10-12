import React, { useState } from 'react';
import {
  Camera,
  FileSearch,
  ShieldCheck,
  Languages,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  FileText,
  Database,
  Eye,
  Lock,
} from 'lucide-react';

interface StageDetail {
  num: string;
  id: string;
  title: string;
  kicker: string;
  tagline: string;
  icon: React.ElementType;
  inputs: string[];
  mechanics: {
    title: string;
    description: string;
  }[];
  outputs: string[];
  guardrail: string;
}

const STAGES: StageDetail[] = [
  {
    num: '01',
    id: 'upload',
    title: 'Upload',
    kicker: 'Intake & Quality Triage',
    tagline: 'High-resolution document capture with automated optical quality validation.',
    icon: Camera,
    inputs: [
      'Original clinical photograph or scanned document (JPEG, PNG, WebP)',
      'Spatial metadata and orientation headers',
    ],
    mechanics: [
      {
        title: 'Stroke Contrast Screening',
        description:
          'Evaluates paper-to-ink luminance differential to prevent unreadable faint ballpoint or faded thermal ink from entering the pipeline.',
      },
      {
        title: 'Optical Blur & Motion Detection',
        description:
          'Applies Laplacian variance heuristics to assess focal sharpness before model inference, prompting for re-capture if illegible.',
      },
      {
        title: 'Perspective Normalization',
        description:
          'Corrects document skew while preserving original spatial coordinate anchors for downstream legal verification.',
      },
    ],
    outputs: [
      'Quality-screened prescription canvas',
      'Original pixel coordinate reference map',
      'Audit accession record',
    ],
    guardrail:
      'If physical image quality falls below readability thresholds, the system flags the issue before model inference rather than guessing.',
  },
  {
    num: '02',
    id: 'understand',
    title: 'Understand',
    kicker: 'Multimodal Stroke Dissection',
    tagline: 'Isolating cursive pen strokes into structured medication name, strength, frequency, and duration slots.',
    icon: FileSearch,
    inputs: [
      'Quality-verified prescription canvas',
      'Spatial bounding proposals',
    ],
    mechanics: [
      {
        title: 'Cursive Stroke Tokenization',
        description:
          'Disentangles hurried outpatient script into localized token proposals, distinguishing brand trade names from strength suffixes.',
      },
      {
        title: 'Clinical Shorthand Parsing',
        description:
          'Decodes classical Indian outpatient sig codes: 1-0-1 (morning/night), PC (post cibum / after meals), AC (ante cibum / before meals), and SOS / PRN.',
      },
      {
        title: 'Epistemic Confidence Scoring',
        description:
          'Computes field-level probability scores. Every character sequence is assigned a confidence metric to drive selective abstention.',
      },
    ],
    outputs: [
      'Structured drug candidates (Name, Form, Strength)',
      'Posology frequency & condition slots',
      'Field-level confidence matrix',
    ],
    guardrail:
      'Does not hallucinate unwritten medication slots. Ambiguous strokes receive low confidence scores and are explicitly flagged.',
  },
  {
    num: '03',
    id: 'verify',
    title: 'Verify',
    kicker: 'Formulary & LASA Safety Barrier',
    tagline: 'Cross-referencing candidates with CDSCO and RxNorm databases with active selective abstention.',
    icon: ShieldCheck,
    inputs: [
      'Extracted drug candidates',
      'Field confidence scores',
      'Prescribed posology slots',
    ],
    mechanics: [
      {
        title: 'Ontological Database Grounding',
        description:
          'Maps proposed brand and generic entities against CDSCO National List of Essential Medicines and US NLM RxNorm concept identifiers.',
      },
      {
        title: 'Look-Alike Sound-Alike (LASA) Screening',
        description:
          'Evaluates phonetic and orthographic similarity against high-risk conflict dictionaries (e.g., hydrOXYzine vs hydrALAzine), applying ISMP Tall Man lettering.',
      },
      {
        title: 'Selective Abstention Boundary',
        description:
          'When confidence falls below the clinical safety threshold or an unresolved conflict exists, the system intentionally abstains and demands pharmacist verification.',
      },
    ],
    outputs: [
      'Grounding reference badges (RxNorm / CDSCO)',
      'Tall Man safety warnings for LASA pairs',
      'Human verification status triggers',
    ],
    guardrail:
      'Never presents an unverified candidate as confirmed. Ambiguous strokes are protected by the selective abstention safety barrier.',
  },
  {
    num: '04',
    id: 'explain',
    title: 'Explain',
    kicker: 'Controlled Multilingual Posology',
    tagline: 'Converting abbreviated clinical regimens into clear, patient-friendly guidance in English, Hindi, and Marathi.',
    icon: Languages,
    inputs: [
      'Verified medication candidates',
      'Validated meal and frequency parameters',
      'Original signed prescription canvas',
    ],
    mechanics: [
      {
        title: 'Deterministic Posology Translation',
        description:
          'Translates Latin abbreviations (e.g., 1-0-1 PC) into unambiguous patient instructions using verified medical vocabularies.',
      },
      {
        title: 'Native Devanagari Typography',
        description:
          'Renders clear instructions in Hindi and Marathi with accurate vernacular phrasing for meal relationships and course completion.',
      },
      {
        title: 'Side-by-Side Dual Reference',
        description:
          'Keeps the original doctor’s handwriting alongside the patient explanation so patients, caregivers, and pharmacists can verify every point.',
      },
    ],
    outputs: [
      'Plain-language patient guidance (EN, HI, MR)',
      'Scheduled intake timeline (Morning, Noon, Night)',
      'Dual-pane audit-ready export',
    ],
    guardrail:
      'Assistive guidance only. The original signed prescription remains the primary legal medical document.',
  },
];

export const HowItWorksSection: React.FC = () => {
  const [activeStageIdx, setActiveStageIdx] = useState<number>(0);
  const activeStage = STAGES[activeStageIdx];
  const ActiveIcon = activeStage.icon;

  return (
    <section id="how-it-works" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mb-14 sm:mb-18 space-y-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#7C5A8B] dark:text-[#F472B6]">
            05 // Clinical Pipeline Architecture
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-[2.5rem] font-bold tracking-tight text-theme-primary leading-[1.08]">
            How DawaAI processes your prescription.
          </h2>
          <p className="text-lg sm:text-xl text-theme-secondary leading-[1.65]">
            An integrated four-stage pipeline: Upload &rarr; Understand &rarr; Verify &rarr; Explain. Inspect each stage to see the underlying vision algorithms, clinical databases, and safety boundaries.
          </p>
        </div>

        {/* Integrated Process Rail Navigation */}
        <div className="relative mb-10">
          {/* Subtle rail connecting line for desktop */}
          <div
            className="hidden lg:block absolute top-7 left-12 right-12 h-0.5 bg-theme pointer-events-none"
            aria-hidden="true"
          />

          <div
            role="tablist"
            aria-label="Clinical processing stages"
            className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4"
          >
            {STAGES.map((stage, idx) => {
              const Icon = stage.icon;
              const isActive = activeStageIdx === idx;
              const isPast = activeStageIdx > idx;

              return (
                <button
                  key={stage.id}
                  role="tab"
                  id={`tab-${stage.id}`}
                  aria-selected={isActive}
                  aria-controls={`panel-${stage.id}`}
                  onClick={() => setActiveStageIdx(idx)}
                  className={`group relative text-left p-4 sm:p-5 rounded-2xl border transition-all cursor-pointer ${
                    isActive
                      ? 'bg-surface border-[#4A2E4D] dark:border-[#F472B6] shadow-md ring-1 ring-[#4A2E4D]/20 dark:ring-[#F472B6]/30'
                      : isPast
                      ? 'bg-surface/70 border-theme hover:border-theme-hover text-theme-secondary'
                      : 'bg-surface-subtle/50 border-theme hover:border-theme-hover text-theme-muted'
                  }`}
                >
                  {/* Top indicator: Number & Icon */}
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className={`font-mono text-xs font-bold px-2 py-0.5 rounded-md ${
                        isActive
                          ? 'bg-[#4A2E4D] dark:bg-[#F472B6] text-white dark:text-[#2E2233]'
                          : isPast
                          ? 'bg-surface text-theme-secondary border border-theme'
                          : 'bg-surface-subtle text-theme-muted'
                      }`}
                    >
                      Stage {stage.num}
                    </span>
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${
                        isActive
                          ? 'bg-[#FFD6DA]/70 dark:bg-[#4A2E4D]/80 text-[#4A2E4D] dark:text-[#F472B6]'
                          : 'bg-surface text-theme-muted group-hover:text-theme-primary'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>

                  {/* Stage Title & Short Kicker */}
                  <div className="text-base sm:text-lg font-bold text-theme-primary">
                    {stage.title}
                  </div>
                  <div className="text-xs text-theme-muted mt-0.5 line-clamp-1">
                    {stage.kicker}
                  </div>

                  {/* Active bottom accent bar */}
                  {isActive && (
                    <div className="absolute -bottom-[1px] left-6 right-6 h-[2px] bg-[#4A2E4D] dark:bg-[#F472B6] rounded-full" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Detailed Stage Inspector (Active Pane) */}
        <div
          role="tabpanel"
          id={`panel-${activeStage.id}`}
          aria-labelledby={`tab-${activeStage.id}`}
          className="rounded-3xl bg-surface border border-theme p-6 sm:p-9 lg:p-10 shadow-elevated-card transition-all"
        >
          {/* Header Row: Stage Identity & Navigation */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-theme">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#7C5A8B] dark:text-[#F472B6]">
                <ActiveIcon className="w-4 h-4" />
                <span>Stage {activeStage.num} &middot; {activeStage.kicker}</span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-bold text-theme-primary tracking-tight">
                {activeStage.title}
              </h3>
              <p className="text-sm sm:text-base text-theme-secondary">
                {activeStage.tagline}
              </p>
            </div>

            {/* Stage Selector Steppers */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setActiveStageIdx((prev) => Math.max(0, prev - 1))}
                disabled={activeStageIdx === 0}
                aria-label="Previous pipeline stage"
                className="p-2.5 rounded-xl border border-theme bg-surface hover:bg-surface-subtle disabled:opacity-40 disabled:cursor-not-allowed text-theme-secondary hover:text-theme-primary transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <span className="text-xs font-mono text-theme-muted px-2">
                {activeStageIdx + 1} / {STAGES.length}
              </span>
              <button
                onClick={() => setActiveStageIdx((prev) => Math.min(STAGES.length - 1, prev + 1))}
                disabled={activeStageIdx === STAGES.length - 1}
                aria-label="Next pipeline stage"
                className="p-2.5 rounded-xl border border-theme bg-surface hover:bg-surface-subtle disabled:opacity-40 disabled:cursor-not-allowed text-theme-secondary hover:text-theme-primary transition-colors cursor-pointer"
              >
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Deep-Dive Grid: Mechanics, Inputs & Outputs */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 pt-8 items-start">
            {/* Mechanics Column (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              <div className="text-xs font-bold uppercase tracking-wider text-theme-muted">
                Processing Mechanics
              </div>

              <div className="space-y-4">
                {activeStage.mechanics.map((mech, i) => (
                  <div
                    key={i}
                    className="p-4 sm:p-5 rounded-2xl bg-surface-subtle/70 border border-theme space-y-1.5"
                  >
                    <div className="text-sm font-bold text-theme-primary flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-[#FFD6DA]/60 dark:bg-[#4A2E4D] text-[#4A2E4D] dark:text-[#FFD6DA] text-xs font-mono font-bold flex items-center justify-center shrink-0">
                        {i + 1}
                      </span>
                      <span>{mech.title}</span>
                    </div>
                    <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed pl-7">
                      {mech.description}
                    </p>
                  </div>
                ))}
              </div>

              {/* Guardrail Box */}
              <div className="p-4 rounded-2xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/60 flex items-start gap-3">
                <Lock className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <div className="space-y-0.5 text-xs">
                  <div className="font-bold text-amber-900 dark:text-amber-300">
                    Clinical Boundary &amp; Safety Guardrail
                  </div>
                  <p className="text-amber-800 dark:text-amber-400 leading-relaxed">
                    {activeStage.guardrail}
                  </p>
                </div>
              </div>
            </div>

            {/* Inputs & Outputs Column (5 cols) */}
            <div className="lg:col-span-5 space-y-6">
              {/* Inputs */}
              <div className="space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-theme-muted flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Stage Inputs</span>
                </div>
                <div className="space-y-2">
                  {activeStage.inputs.map((inp, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-surface border border-theme text-xs text-theme-secondary flex items-start gap-2"
                    >
                      <Eye className="w-3.5 h-3.5 text-[#7C5A8B] dark:text-[#F472B6] shrink-0 mt-0.5" />
                      <span>{inp}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Outputs */}
              <div className="space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-theme-muted flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5" />
                  <span>Verifiable Stage Outputs</span>
                </div>
                <div className="space-y-2">
                  {activeStage.outputs.map((out, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-surface border border-theme text-xs font-medium text-theme-primary flex items-start gap-2"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                      <span>{out}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

