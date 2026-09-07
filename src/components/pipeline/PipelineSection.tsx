import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import {
  FileImage,
  Tag,
  Database,
  ShieldAlert,
  Languages,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';

export const PipelineSection: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(0);

  const steps = [
    {
      step: '01',
      title: 'Multimodal Document Intake',
      subtitle: 'Spatial Layout & Ink Stroke Tokenization',
      icon: FileImage,
      badge: 'Vision Transformer',
      summary:
        'Analyzes high-resolution prescription images (JPEG/PNG/PDF), corrects skew, isolates doctor letterhead watermarks, and extracts localized handwriting bounding polygons.',
      technicalDetails: [
        'Swin-Transformer Document Backbone with feature pyramid networks',
        'Polygon line extraction handling dense cursive and multi-angled margins',
        'Noise removal for paper bleed-through and stamp occlusions',
      ],
      inputOutput: {
        input: 'Raw camera scan or digital PDF (200-400 DPI)',
        output: 'Normalized spatial polygon segment coordinates & stroke tensor',
      },
    },
    {
      step: '02',
      title: 'Semantic Clinical Tokenization',
      subtitle: 'Entity Parsing & Shorthand Decoding',
      icon: Tag,
      badge: 'BioClinical NER',
      summary:
        'Parses cursive sequences into distinct clinical entity slots: Brand Name, Generic Formulation, Dosage Strength, Route, Frequency (1-0-1, SOS), and Duration.',
      technicalDetails: [
        'Designed for regional outpatient clinical handwriting patterns and common prescribing conventions',
        'Disentangles Latin shorthand abbreviations (PC, AC, OD, BD, TDS, QID, HS)',
        'Extracts conditional dosage instructions (e.g. SOS for fever > 100°F)',
      ],
      inputOutput: {
        input: 'Handwritten stroke coordinates & image patch tokens',
        output: 'Structured entity candidates [Drug, Dosage, Frequency, Duration]',
      },
    },
    {
      step: '03',
      title: 'Ontology Knowledge Grounding',
      subtitle: 'CDSCO & RxNorm Pharmacopeia Verification',
      icon: Database,
      badge: 'Knowledge Graph',
      summary:
        'Every extracted drug candidate is queried against trusted pharmacological databases (CDSCO, FDA RxNorm, WHO Essential Medicines). Non-existent formulations are strictly rejected.',
      technicalDetails: [
        'Fast phonetic & edit-distance candidate retrieval across 45,000+ formulations',
        'Validates drug-salt bioequivalence and standard marketed strengths',
        'Maps candidate to standardized RxNorm CUI and WHO ATC anatomical class',
      ],
      inputOutput: {
        input: 'Unvalidated entity candidate strings',
        output: 'Verified pharmacopeial record with generic salts and ATC code',
      },
    },
    {
      step: '04',
      title: 'Calibrated Selective Abstention',
      subtitle: 'Entropy Thresholding & Selective Abstention Gate',
      icon: ShieldAlert,
      badge: 'Uncertainty Quantification',
      summary:
        'When handwritten ink is degraded or ambiguous (e.g. 1.0mg vs 10mg), the system quantifies predictive entropy. If entropy exceeds safe limits, the model deliberately abstains rather than emitting an ungrounded guess.',
      technicalDetails: [
        'Monte Carlo Dropout & Softmax temperature scaling for uncertainty calibration',
        'Selective classification with cost-sensitive penalty on dosage errors',
        'Mandatory pharmacist review escalation for all abstained tokens',
      ],
      inputOutput: {
        input: 'Token posterior distribution & character entropy scores',
        output: 'Pass verification OR Selective Abstention flag with human referral',
      },
    },
    {
      step: '05',
      title: 'Vernacular Patient Posology',
      subtitle: 'Multilingual Schedule Synthesis (EN / HI / MR)',
      icon: Languages,
      badge: 'NLG & Translation',
      summary:
        'Converts complex prescription jargon into an intuitive, low-literacy patient posology schedule with meal associations, warnings, and audio explanations in English, Hindi, and Marathi.',
      technicalDetails: [
        'Culturally grounded vernacular terminology (e.g. भोजन के बाद, उपाशीपोटी)',
        'Visual timeline breakdown (Morning, Afternoon, Evening, Night)',
        'Storage precautions and missed-dose protocols tailored to the medication',
      ],
      inputOutput: {
        input: 'Verified clinical medication record',
        output: 'Localized patient explanation cards with daily schedule & audio',
      },
    },
  ];

  const current = steps[activeStep];
  const Icon = current.icon;

  return (
    <section id="pipeline" className="py-20 bg-canvas border-t border-theme relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <Badge variant="cyan" size="sm" dot>
            Architectural Workflow
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-theme-primary tracking-tight">
            From Raw Cursive Ink to Verified Understanding
          </h2>
          <p className="text-sm sm:text-base text-theme-secondary">
            A 5-stage multimodal architecture designed to curb ungrounded generation, enforce clinical ontology grounding, and abstain when handwriting is ambiguous.
          </p>
        </div>

        {/* Horizontal Pipeline Steps Navigation */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-10">
          {steps.map((step, idx) => {
            const StepIcon = step.icon;
            const isSelected = activeStep === idx;

            return (
              <button
                key={step.step}
                onClick={() => setActiveStep(idx)}
                className={`p-4 rounded-xl text-left border transition-all cursor-pointer flex flex-col justify-between ${
                  isSelected
                    ? 'bg-sky-50 dark:bg-sky-950/30 border-sky-400 dark:border-sky-700 shadow-xs'
                    : 'bg-surface border-theme hover:bg-surface-subtle'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-theme-muted">{step.step}</span>
                  <StepIcon
                    className={`w-4 h-4 ${isSelected ? 'text-teal-600 dark:text-cyan-400' : 'text-theme-muted'}`}
                  />
                </div>
                <div>
                  <h3
                    className={`text-xs font-bold font-mono tracking-tight line-clamp-1 ${
                      isSelected ? 'text-teal-800 dark:text-cyan-300' : 'text-theme-primary'
                    }`}
                  >
                    {step.title}
                  </h3>
                  <span className="text-[10px] text-theme-muted line-clamp-1 mt-0.5">
                    {step.badge}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Deep Dive Card for Selected Stage */}
        <Card variant="glass" padding="lg" className="border-theme relative overflow-hidden shadow-xs">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Description Column */}
            <div className="lg:col-span-7 space-y-5">
              <div className="flex flex-wrap items-center gap-2.5">
                <Badge variant="cyan" size="sm">
                  Stage {current.step} of 05
                </Badge>
                <Badge variant="slate" size="sm">
                  {current.badge}
                </Badge>
              </div>

              <div>
                <h3 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight flex items-center gap-2.5">
                  <Icon className="w-6 h-6 text-teal-600 dark:text-cyan-400" />
                  <span>{current.title}</span>
                </h3>
                <p className="text-xs sm:text-sm font-mono text-teal-700 dark:text-cyan-400/90 mt-1">
                  {current.subtitle}
                </p>
              </div>

              <p className="text-sm text-theme-secondary leading-relaxed">{current.summary}</p>

              {/* Technical Specifications */}
              <div className="space-y-2 pt-2">
                <div className="text-xs font-mono font-semibold uppercase tracking-wider text-theme-muted">
                  Engine Architecture &amp; Algorithmic Principles:
                </div>
                <ul className="space-y-2">
                  {current.technicalDetails.map((detail, dIdx) => (
                    <li key={dIdx} className="flex items-start gap-2.5 text-xs text-theme-secondary">
                      <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                      <span>{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Right I/O Flow Visualizer */}
            <div className="lg:col-span-5 space-y-4">
              <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-3 font-mono text-xs">
                <div className="text-theme-secondary flex items-center justify-between border-b border-theme pb-2">
                  <span className="text-[11px] font-semibold text-teal-700 dark:text-cyan-400">DATA FLOW CONTRACT</span>
                  <span className="text-[10px] text-theme-muted">STAGE {current.step}</span>
                </div>

                <div className="space-y-1.5">
                  <div className="text-[11px] text-theme-muted uppercase tracking-wider">Inputs:</div>
                  <div className="p-2.5 rounded bg-surface border border-theme text-theme-primary text-[11px] break-words">
                    {current.inputOutput.input}
                  </div>
                </div>

                <div className="flex justify-center my-1">
                  <ArrowRight className="w-4 h-4 text-teal-600 dark:text-cyan-400 rotate-90 lg:rotate-0" />
                </div>

                <div className="space-y-1.5">
                  <div className="text-[11px] text-theme-muted uppercase tracking-wider">Outputs:</div>
                  <div className="p-2.5 rounded bg-sky-50/70 dark:bg-sky-950/30 border border-sky-200 dark:border-sky-800 text-sky-900 dark:text-sky-300 text-[11px] break-words">
                    {current.inputOutput.output}
                  </div>
                </div>
              </div>

              {/* Navigation controls */}
              <div className="flex items-center justify-between pt-2">
                <button
                  disabled={activeStep === 0}
                  onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
                  className="px-3 py-1.5 text-xs font-mono text-theme-secondary hover:text-theme-primary disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                >
                  &larr; Previous Stage
                </button>
                <button
                  disabled={activeStep === steps.length - 1}
                  onClick={() => setActiveStep(Math.min(steps.length - 1, activeStep + 1))}
                  className="px-4 py-1.5 text-xs font-mono font-semibold bg-surface hover:bg-surface-subtle text-theme-primary rounded-lg border border-theme disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1.5 shadow-xs"
                >
                  <span>Next Stage</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
};
