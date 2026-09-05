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
        'Fine-tuned on Indian outpatient clinical prescription corpora (IndoRx-1200)',
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
      subtitle: 'Entropy Thresholding & Anti-Hallucination Gate',
      icon: ShieldAlert,
      badge: 'Uncertainty Quantification',
      summary:
        'When handwritten ink is degraded or ambiguous (e.g. 1.0mg vs 10mg), the system quantifies predictive entropy. If entropy exceeds safe limits, the model deliberately abstains rather than hallucinating.',
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
    <section id="pipeline" className="py-20 bg-[#080C16] border-t border-white/[0.08] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <Badge variant="cyan" size="sm" dot>
            Architectural Workflow
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            From Raw Cursive Ink to Verified Understanding
          </h2>
          <p className="text-sm sm:text-base text-slate-300">
            A 5-stage multimodal architecture designed to eliminate hallucinations, enforce clinical ontology grounding, and abstain when handwriting is ambiguous.
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
                    ? 'bg-cyan-950/40 border-cyan-500/60 shadow-[0_0_20px_rgba(14,165,233,0.2)]'
                    : 'bg-slate-900/50 border-white/[0.06] hover:border-white/20 hover:bg-slate-900/80'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-slate-500">{step.step}</span>
                  <StepIcon
                    className={`w-4 h-4 ${isSelected ? 'text-cyan-400' : 'text-slate-400'}`}
                  />
                </div>
                <div>
                  <h3
                    className={`text-xs font-bold font-mono tracking-tight line-clamp-1 ${
                      isSelected ? 'text-cyan-300' : 'text-slate-200'
                    }`}
                  >
                    {step.title}
                  </h3>
                  <span className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">
                    {step.badge}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Deep Dive Card for Selected Stage */}
        <Card variant="glass" padding="lg" className="border-cyan-500/25 relative overflow-hidden">
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
                <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
                  <Icon className="w-6 h-6 text-cyan-400" />
                  <span>{current.title}</span>
                </h3>
                <p className="text-xs sm:text-sm font-mono text-cyan-400/80 mt-1">
                  {current.subtitle}
                </p>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">{current.summary}</p>

              {/* Technical Specifications */}
              <div className="space-y-2 pt-2">
                <div className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
                  Engine Architecture & Algorithmic Principles:
                </div>
                <ul className="space-y-2">
                  {current.technicalDetails.map((detail, dIdx) => (
                    <li key={dIdx} className="flex items-start gap-2.5 text-xs text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                      <span>{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Right I/O Flow Visualizer */}
            <div className="lg:col-span-5 space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/80 border border-white/10 space-y-3 font-mono text-xs">
                <div className="text-slate-400 flex items-center justify-between border-b border-white/10 pb-2">
                  <span className="text-[11px] font-semibold text-cyan-400">DATA FLOW CONTRACT</span>
                  <span className="text-[10px] text-slate-500">STAGE {current.step}</span>
                </div>

                <div className="space-y-1.5">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Inputs:</div>
                  <div className="p-2.5 rounded bg-black/50 border border-white/5 text-slate-300 text-[11px] break-words">
                    {current.inputOutput.input}
                  </div>
                </div>

                <div className="flex justify-center my-1">
                  <ArrowRight className="w-4 h-4 text-cyan-400 rotate-90 lg:rotate-0" />
                </div>

                <div className="space-y-1.5">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider">Outputs:</div>
                  <div className="p-2.5 rounded bg-cyan-950/30 border border-cyan-500/20 text-cyan-300 text-[11px] break-words">
                    {current.inputOutput.output}
                  </div>
                </div>
              </div>

              {/* Navigation controls */}
              <div className="flex items-center justify-between pt-2">
                <button
                  disabled={activeStep === 0}
                  onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
                  className="px-3 py-1.5 text-xs font-mono text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                >
                  ← Previous Stage
                </button>
                <button
                  disabled={activeStep === steps.length - 1}
                  onClick={() => setActiveStep(Math.min(steps.length - 1, activeStep + 1))}
                  className="px-4 py-1.5 text-xs font-mono font-semibold bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 rounded-lg border border-cyan-500/30 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1.5"
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
