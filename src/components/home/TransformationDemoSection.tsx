import React, { useState } from 'react';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import { CheckCircle2, AlertTriangle, ArrowRight, CornerDownRight } from 'lucide-react';

export const TransformationDemoSection: React.FC = () => {
  const [selectedDemoIdx, setSelectedDemoIdx] = useState<number>(0);

  const canvasData = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];

  const demoItems = [
    {
      id: 'demo-1',
      strokeIdx: 0,
      label: 'Standard Antibiotic',
      doctorInk: 'Augmentin 625 Duo (1-0-1 x 5d PC)',
      brand: 'Augmentin 625 Duo Tablet',
      generic: 'Amoxicillin (500mg) + Clavulanic Acid (125mg)',
      dosage: '625 mg',
      frequency: 'Twice daily (Morning & Night)',
      mealRelation: 'After meals (PC)',
      duration: '5 days',
      confidence: 96,
      status: 'verified' as const,
      formularyRef: 'CDSCO Approved · RxNorm #213169',
      explanation: 'Complete all 5 days of antibacterial therapy as prescribed.',
    },
    {
      id: 'demo-2',
      strokeIdx: 1,
      label: 'Gastroprotective Proton-Pump Inhibitor',
      doctorInk: 'Pan 40 (1-0-0 x 5d AC)',
      brand: 'Pan 40 Tablet',
      generic: 'Pantoprazole Sodium 40mg',
      dosage: '40 mg',
      frequency: 'Once daily (Morning only)',
      mealRelation: '30 minutes before breakfast (AC)',
      duration: '5 days',
      confidence: 94,
      status: 'verified' as const,
      formularyRef: 'CDSCO Approved · RxNorm #284635',
      explanation: 'Take with water before breakfast to protect the stomach lining.',
    },
    {
      id: 'demo-3',
      strokeIdx: 2,
      label: 'Ambiguous Frequency Shorthand',
      doctorInk: 'Dolo 650 (SOS / PRN for fever)',
      brand: 'Dolo 650 Tablet',
      generic: 'Paracetamol 650mg',
      dosage: '650 mg',
      frequency: 'As needed (SOS / PRN)',
      mealRelation: 'When fever exceeds 100°F',
      duration: '3 days max',
      confidence: 68,
      status: 'ambiguous' as const,
      formularyRef: 'CDSCO Approved · RxNorm #161',
      explanation: 'Ambiguous cursive terminal loop: interpreted as SOS, requires pharmacist confirmation.',
    },
  ];

  const activeItem = demoItems[selectedDemoIdx];
  const activeStroke = canvasData.strokes[activeItem.strokeIdx];

  return (
    <section id="transformation" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="max-w-2xl mb-12 sm:mb-16 space-y-3">
          <div className="text-xs font-semibold text-teal-700 dark:text-teal-400">
            Transformation
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-theme-primary">
            See what changes.
          </h2>
          <p className="text-base text-theme-secondary leading-relaxed">
            From handwritten ink on clinical paper to verified medication slots and patient instructions.
          </p>

          {/* Interactive Prescription Line Selectors */}
          <div className="flex flex-wrap items-center gap-2 pt-2">
            {demoItems.map((item, idx) => (
              <button
                key={item.id}
                onClick={() => setSelectedDemoIdx(idx)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                  selectedDemoIdx === idx
                    ? 'bg-teal-600 text-white shadow-xs font-semibold'
                    : 'bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary hover:text-theme-primary'
                }`}
              >
                Line {idx + 1}: {item.brand}
              </button>
            ))}
          </div>
        </div>

        {/* Side-by-Side Transformation Stage */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left: Original Handwritten Ink (5 cols) */}
          <div className="lg:col-span-5 p-6 rounded-2xl prescription-paper border border-theme flex flex-col justify-between space-y-6 shadow-xs">
            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Original handwriting
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Doctor penmanship stroke
              </h3>
            </div>

            {/* Handwritten Ink Stroke Visualizer */}
            <div className="p-5 rounded-xl bg-white/70 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 space-y-3">
              <div className="text-slate-800 dark:text-slate-200 font-serif italic text-xl font-black">
                ℞
              </div>

              <div className="py-2">
                <svg
                  viewBox="0 0 650 35"
                  className="w-full h-10 overflow-visible"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d={activeStroke.svgPath}
                    fill="none"
                    stroke="currentColor"
                    className="text-blue-900 dark:text-sky-400 stroke-[2.8]"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>

              <div className="text-xs text-slate-500 dark:text-slate-400">
                {activeStroke.label}
              </div>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Hurried outpatient penmanship, cursive slant, and classical clinical shorthands are preserved as the legal record.
            </p>
          </div>

          {/* Arrow / Bridge Indicator (Desktop Only) */}
          <div className="hidden lg:flex lg:col-span-1 items-center justify-center">
            <div className="w-10 h-10 rounded-full bg-surface border border-theme flex items-center justify-center text-theme-muted shadow-xs">
              <ArrowRight className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            </div>
          </div>

          {/* Right: Structured Interpretation & Grounded Evidence (6 cols) */}
          <div className="lg:col-span-6 p-6 sm:p-7 rounded-2xl bg-surface border border-theme flex flex-col justify-between space-y-6 shadow-xs">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-xs text-teal-700 dark:text-teal-400">
                  Interpreted medication
                </span>
                {activeItem.status === 'ambiguous' ? (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 px-2.5 py-0.5 rounded-md border border-amber-200 dark:border-amber-800">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Requires verification</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span>Verified match</span>
                  </span>
                )}
              </div>

              <div>
                <h3 className="text-xl font-bold text-theme-primary">
                  {activeItem.brand}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  {activeItem.generic}
                </p>
              </div>
            </div>

            {/* Extracted Slots - Typographic layout without card-in-a-card rectangles */}
            <div className="space-y-3 py-1 border-y border-theme text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-theme-muted block text-[11px] mb-0.5">Dosage</span>
                  <span className="text-base font-bold text-theme-primary">{activeItem.dosage}</span>
                </div>
                <div>
                  <span className="text-theme-muted block text-[11px] mb-0.5">Duration</span>
                  <span className="text-base font-bold text-theme-primary">{activeItem.duration}</span>
                </div>
              </div>
              <div>
                <span className="text-theme-muted block text-[11px] mb-0.5">Schedule &amp; instructions</span>
                <span className="text-sm font-semibold text-theme-primary">
                  {activeItem.frequency} &middot; {activeItem.mealRelation}
                </span>
              </div>
            </div>

            {/* Explanation & Formulary Reference */}
            <div className="space-y-2 text-xs">
              <div className="text-theme-secondary leading-relaxed">
                <strong className="text-theme-primary font-medium">Patient guidance: </strong>
                {activeItem.explanation}
              </div>

              <div className="flex items-center justify-between text-[11px] text-theme-muted pt-1">
                <div className="flex items-center gap-1">
                  <CornerDownRight className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                  <span>{activeItem.formularyRef}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
