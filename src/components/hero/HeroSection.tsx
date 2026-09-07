import React, { useState, useEffect } from 'react';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import {
  UploadCloud,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Search,
  Check,
} from 'lucide-react';

export interface HeroSectionProps {
  onOpenUpload?: () => void;
  onScrollToHowItWorks?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onOpenUpload,
  onScrollToHowItWorks,
}) => {
  const canvasData = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];

  // Current active prescription line (0: Augmentin, 1: Pan 40, 2: Dolo 650)
  const [activeLineIdx, setActiveLineIdx] = useState<number>(0);

  // Transformation phase for the current line:
  // 0 = Raw Handwriting
  // 1 = Scanning pass
  // 2 = Structured posology emerging
  // 3 = Evidence verification locked in
  const [stage, setStage] = useState<0 | 1 | 2 | 3>(3);
  const [isAutoPlaying, setIsAutoPlaying] = useState<boolean>(true);

  // Auto-play animation cycle
  useEffect(() => {
    if (!isAutoPlaying) return;

    // Progression within each line:
    // 0ms: stage 0 (Handwriting)
    // 700ms: stage 1 (Scan pass)
    // 1600ms: stage 2 (Structured fields emerge)
    // 2500ms: stage 3 (Verified with evidence)
    // 5500ms: advance to next line
    const t0 = setTimeout(() => setStage(0), 100);
    const t1 = setTimeout(() => setStage(1), 700);
    const t2 = setTimeout(() => setStage(2), 1600);
    const t3 = setTimeout(() => setStage(3), 2500);
    const tNext = setTimeout(() => {
      setActiveLineIdx((prev) => (prev + 1) % 3);
    }, 6000);

    return () => {
      clearTimeout(t0);
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(tNext);
    };
  }, [activeLineIdx, isAutoPlaying]);

  const prescriptionLines = [
    {
      strokeIdx: 0,
      label: 'Line 01 · Antibiotic',
      doctorInkText: 'Augmentin 625 Duo (1-0-1 x 5d PC)',
      medicine: 'Augmentin 625 Duo',
      generic: 'Amoxicillin (500mg) + Clavulanate (125mg)',
      posology: '1 tablet twice daily · after meals · 5 days',
      confidence: 96,
      status: 'verified' as const,
      evidence: 'Grounded in CDSCO & RxNorm #213169',
      isUncertain: false,
    },
    {
      strokeIdx: 1,
      label: 'Line 02 · Gastroprotective',
      doctorInkText: 'Pan 40 (1-0-0 x 5d AC)',
      medicine: 'Pan 40',
      generic: 'Pantoprazole Sodium 40mg',
      posology: '1 tablet once daily · before breakfast · 5 days',
      confidence: 94,
      status: 'verified' as const,
      evidence: 'Grounded in CDSCO & RxNorm #284635',
      isUncertain: false,
    },
    {
      strokeIdx: 2,
      label: 'Line 03 · Ambiguous Shorthand',
      doctorInkText: 'Dolo 650 (SOS / PRN for fever)',
      medicine: 'Dolo 650',
      generic: 'Paracetamol 650mg',
      posology: 'Take as needed for fever > 100°F (SOS)',
      confidence: 68,
      status: 'ambiguous' as const,
      evidence: 'CDSCO & RxNorm #161 · Flagged for pharmacist verification',
      isUncertain: true,
    },
  ];

  const currentLine = prescriptionLines[activeLineIdx];
  const activeStroke = canvasData.strokes[currentLine.strokeIdx];

  return (
    <section className="relative pt-24 pb-16 sm:pt-32 sm:pb-24 overflow-hidden border-b border-theme bg-canvas">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Asymmetric Editorial Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
          {/* Left Column: Direct Editorial Headline + CTA (5 cols) */}
          <div className="lg:col-span-5 space-y-6 text-left">
            {/* Direct Context Indicator */}
            <div className="text-xs font-semibold text-teal-700 dark:text-teal-400 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 dark:bg-teal-400" />
              <span>Assistive Prescription Understanding</span>
            </div>

            {/* Direct, Honest Headline */}
            <div className="space-y-1">
              <h1 className="text-3xl sm:text-5xl lg:text-[3.25rem] font-extrabold tracking-tight text-theme-primary leading-[1.12]">
                Some prescriptions are clear.
              </h1>
              <h1 className="text-3xl sm:text-5xl lg:text-[3.25rem] font-extrabold tracking-tight text-teal-700 dark:text-teal-400 leading-[1.12]">
                Some are not.
              </h1>
            </div>

            {/* Concise Subcopy */}
            <p className="text-base sm:text-lg text-theme-secondary leading-relaxed max-w-lg">
              AURA-Rx turns difficult physician handwriting into structured, explainable prescription information &mdash; while explicitly showing you when the system is uncertain.
            </p>

            {/* Actions: Primary CTA visually dominant */}
            <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5">
              {onOpenUpload && (
                <button
                  onClick={onOpenUpload}
                  className="px-7 py-4 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-sm cursor-pointer group"
                >
                  <UploadCloud className="w-5 h-5" />
                  <span>Analyze a prescription</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </button>
              )}

              {onScrollToHowItWorks && (
                <button
                  onClick={onScrollToHowItWorks}
                  className="px-5 py-4 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary hover:text-theme-primary text-sm font-medium transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                >
                  <span>Explore how it works</span>
                </button>
              )}
            </div>

            {/* Trust Signals */}
            <div className="pt-4 border-t border-theme space-y-2 text-xs text-theme-muted">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                <span>Original doctor prescription preserved as primary legal record</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                <span>Verified against CDSCO India &amp; US NLM RxNorm formularies</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                <span>Flags ambiguous handwriting for verification instead of guessing</span>
              </div>
            </div>
          </div>

          {/* Right Column: Prescription as the Central Hero Object (7 cols) */}
          <div className="lg:col-span-7">
            {/* The Physical Prescription Stationery Document */}
            <div className="prescription-paper rounded-2xl p-5 sm:p-7 text-slate-900 dark:text-slate-100 shadow-sm border border-theme relative overflow-hidden transition-all">
              {/* Doctor Letterhead Header */}
              <div className="border-b border-slate-300 dark:border-slate-700 pb-3 mb-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-xs font-semibold text-teal-800 dark:text-teal-400">
                      {canvasData.doctorHeader.clinicName}
                    </div>
                    <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                      {canvasData.doctorHeader.name}
                    </h3>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400">
                      {canvasData.doctorHeader.qualifications} · {canvasData.doctorHeader.clinicAddress}
                    </p>
                  </div>
                  <div className="text-right text-[11px] text-slate-600 dark:text-slate-400">
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      {canvasData.doctorHeader.regNo}
                    </span>
                    <div className="text-[10px] mt-1">Date: {canvasData.patientInfo.date}</div>
                  </div>
                </div>

                <div className="mt-2.5 pt-2 border-t border-dashed border-slate-300 dark:border-slate-700 flex justify-between text-[11px] text-slate-700 dark:text-slate-300">
                  <span>
                    <strong>Patient:</strong> {canvasData.patientInfo.name} ({canvasData.patientInfo.ageGender})
                  </span>
                  <span>
                    <strong>Vitals:</strong> {canvasData.patientInfo.vitals}
                  </span>
                </div>
              </div>

              {/* Rx Symbol + Interactive Line Selectors */}
              <div className="flex items-center justify-between mb-3">
                <div className="text-slate-800 dark:text-slate-200 font-serif italic text-2xl font-black">
                  ℞
                </div>

                {/* Step / Line Selector Pills */}
                <div className="flex items-center gap-1.5">
                  {prescriptionLines.map((line, idx) => (
                    <button
                      key={line.label}
                      onClick={() => {
                        setActiveLineIdx(idx);
                        setIsAutoPlaying(false);
                        setStage(3);
                      }}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
                        activeLineIdx === idx
                          ? 'bg-teal-700 text-white shadow-xs'
                          : 'bg-white/80 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 border border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      {idx === 2 ? 'Ambiguous Example' : `Line 0${idx + 1}`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Live Transformation Focus Stage */}
              <div className="p-4 rounded-xl bg-white/90 dark:bg-slate-900/80 border border-slate-300 dark:border-slate-700 space-y-4">
                {/* 1. Raw Handwriting Display with Scanning Overlay */}
                <div className="relative rounded-lg p-3 bg-slate-50/70 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-800 overflow-hidden">
                  <div className="flex items-center justify-between text-[11px] mb-1.5 text-slate-500 dark:text-slate-400">
                    <span className="font-semibold text-theme-primary">
                      Doctor handwriting stroke
                    </span>
                    <span className="text-[10px] text-slate-400">Original pen ink</span>
                  </div>

                  {/* SVG Cursive Ink Stroke */}
                  <div className="relative py-1">
                    <svg
                      viewBox="0 0 650 35"
                      className="w-full h-8 overflow-visible"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d={activeStroke.svgPath}
                        fill="none"
                        stroke="currentColor"
                        className="text-blue-800 dark:text-sky-400 stroke-[2.8]"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>

                    {/* Subtle Animated Scanning Sweep (Stage 1) */}
                    {(stage === 1 || stage === 2) && (
                      <div className="absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-transparent via-teal-500/20 to-transparent pointer-events-none animate-pulse" />
                    )}
                  </div>
                </div>

                {/* 2. Transformation Pipeline Stages Flow (Visual Steps) */}
                <div className="flex items-center justify-between text-xs px-1 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 pb-2">
                  <div
                    className={`flex items-center gap-1 transition-colors ${
                      stage >= 0 ? 'text-teal-700 dark:text-teal-400 font-semibold' : ''
                    }`}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    <span>Ink detected</span>
                  </div>
                  <span>&rarr;</span>
                  <div
                    className={`flex items-center gap-1 transition-colors ${
                      stage >= 1 ? 'text-teal-700 dark:text-teal-400 font-semibold' : ''
                    }`}
                  >
                    <Search className="w-3 h-3" />
                    <span>Scanning</span>
                  </div>
                  <span>&rarr;</span>
                  <div
                    className={`flex items-center gap-1 transition-colors ${
                      stage >= 2 ? 'text-teal-700 dark:text-teal-400 font-semibold' : ''
                    }`}
                  >
                    <Check className="w-3 h-3" />
                    <span>Structured posology</span>
                  </div>
                  <span>&rarr;</span>
                  <div
                    className={`flex items-center gap-1 transition-colors ${
                      stage >= 3 ? 'text-teal-700 dark:text-teal-400 font-semibold' : ''
                    }`}
                  >
                    <ShieldCheck className="w-3 h-3" />
                    <span>Evidence grounded</span>
                  </div>
                </div>

                {/* 3. Structured Posology Emerging (Stage 2 & 3) */}
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-xs font-semibold text-teal-800 dark:text-teal-400">
                        Interpreted medicine
                      </div>
                      <div className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100">
                        {currentLine.medicine}
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400">
                        {currentLine.generic}
                      </div>
                    </div>

                    {/* Confidence & Verification Status Badge */}
                    {stage >= 3 && (
                      <div className="shrink-0 text-right">
                        {currentLine.status === 'ambiguous' ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Verification flagged</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-900 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Formulary verified</span>
                          </span>
                        )}
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                          Demo match: {currentLine.confidence}%
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Posology Schedule */}
                  <div className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200">
                    <span className="font-semibold text-slate-900 dark:text-slate-100">Dosage Regimen: </span>
                    {currentLine.posology}
                  </div>

                  {/* Grounded Evidence Marker */}
                  {stage >= 3 && (
                    <div className="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1.5 pt-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-teal-700 dark:text-teal-400 shrink-0" />
                      <span>{currentLine.evidence}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Physician Signature & Legal Note */}
              <div className="mt-4 pt-3 border-t border-slate-300 dark:border-slate-700 flex justify-between items-end text-[10px] text-slate-600 dark:text-slate-400">
                <div className="border border-slate-300 dark:border-slate-700 rounded px-2 py-0.5 bg-white/70 dark:bg-slate-800/80 font-mono text-[9px] text-slate-700 dark:text-slate-300">
                  {canvasData.clinicStampText}
                </div>
                <div className="text-right">
                  <svg viewBox="0 0 200 60" className="w-20 h-6 inline-block">
                    <path
                      d={canvasData.doctorSignaturePath}
                      fill="none"
                      stroke="#1E3A8A"
                      strokeWidth="2.2"
                      strokeLinecap="round"
                      className="dark:stroke-sky-400"
                    />
                  </svg>
                  <p className="text-[9px] text-slate-500 dark:text-slate-400 font-mono">Prescriber Signature</p>
                </div>
              </div>
            </div>

            {/* Calm Caption */}
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-theme-muted px-1">
              <span>Interactive preview &middot; Click lines above to test ambiguity handling</span>
              <span>Prescription stays permanent reference</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
