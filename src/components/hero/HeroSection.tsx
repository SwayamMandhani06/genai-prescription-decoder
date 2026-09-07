import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import {
  UploadCloud,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Play,
  Pause,
  ChevronRight,
} from 'lucide-react';

export interface HeroSectionProps {
  onOpenUpload?: () => void;
  onScrollToHowItWorks?: () => void;
}

export interface PrescriptionLineItem {
  id: string;
  lineNum: number;
  label: string;
  shortName: string;
  strokeIdx: number;
  doctorInkText: string;
  interpretedName: string;
  genericFormula: string;
  brandDetails: string;
  frequency: string;
  mealRelation: string;
  duration: string;
  confidenceScore: number;
  statusLabel: 'High confidence — demo' | 'Needs verification';
  statusType: 'high_confidence' | 'needs_verification';
  evidenceCitation: string;
  evidenceTag: string;
  clinicalRationale: string;
  isAmbiguous: boolean;
  abstentionReason?: string;
  scanTopPercent: string;
  verticalAnchorOffsetPx: number;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onOpenUpload,
  onScrollToHowItWorks,
}) => {
  const canvasData = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];

  // Three lines demonstrating clear resolution vs. uncertainty-aware selective abstention
  const prescriptionLines: PrescriptionLineItem[] = [
    {
      id: 'line-1',
      lineNum: 1,
      label: 'Line 1 · Antibiotic',
      shortName: 'Augmentin 625',
      strokeIdx: 0,
      doctorInkText: 'Tab. Augmentin 625 Duo  1 - 0 - 1 x 5d  (P.C.)',
      interpretedName: 'Amoxicillin + Clavulanate',
      genericFormula: 'Amoxicillin (500mg) + Clavulanic Acid (125mg)',
      brandDetails: 'Augmentin 625 Duo Tablet · 625 mg',
      frequency: 'Twice daily (Morning & Night)',
      mealRelation: 'Strictly after meals (P.C.)',
      duration: '5 days course',
      confidenceScore: 96,
      statusLabel: 'High confidence — demo',
      statusType: 'high_confidence',
      evidenceCitation: 'CDSCO India Formulary & US NLM RxNorm #213169',
      evidenceTag: 'RxNorm #213169',
      clinicalRationale: 'Character segmentation matches standard beta-lactam antibacterial regimen.',
      isAmbiguous: false,
      scanTopPercent: '34%',
      verticalAnchorOffsetPx: 175,
    },
    {
      id: 'line-2',
      lineNum: 2,
      label: 'Line 2 · Ambiguous Cursive',
      shortName: 'Dolo 650 (Ambiguous)',
      strokeIdx: 2,
      doctorInkText: 'Tab. Dolo 650mg  1 - 0 - 1  S.O.S. (if fever > 100°F)',
      interpretedName: 'Possible candidate: Paracetamol 650mg',
      genericFormula: 'Paracetamol (Acetaminophen) 650mg',
      brandDetails: 'Dolo 650 Tablet · 650 mg',
      frequency: 'Candidate: As needed (S.O.S. / PRN)',
      mealRelation: 'With water when fever rises > 100°F',
      duration: '3 days maximum',
      confidenceScore: 64,
      statusLabel: 'Needs verification',
      statusType: 'needs_verification',
      evidenceCitation: 'Selective Abstention · Flagged for pharmacist verification',
      evidenceTag: 'RxNorm #161 (Uncertain)',
      clinicalRationale: 'Selective Abstention: Terminal cursive shorthand loop is ambiguous between S.O.S. and daily schedule.',
      isAmbiguous: true,
      abstentionReason: 'Cursive terminal loop resembles both "S.O.S." and "1-0-1". To prevent medication error, the system refrains from autonomous confirmation and flags for pharmacist review.',
      scanTopPercent: '54%',
      verticalAnchorOffsetPx: 255,
    },
    {
      id: 'line-3',
      lineNum: 3,
      label: 'Line 3 · Gastroprotective',
      shortName: 'Pan 40',
      strokeIdx: 1,
      doctorInkText: 'Cap. Pan 40mg  1 - 0 - 0 x 5d  (A.C. 30m before food)',
      interpretedName: 'Pantoprazole Sodium 40mg',
      genericFormula: 'Pantoprazole Sodium 40mg Gastro-Resistant',
      brandDetails: 'Pan 40 Capsule · 40 mg',
      frequency: 'Once daily (Morning only)',
      mealRelation: '30 mins before breakfast (A.C.)',
      duration: '5 days co-prescribed course',
      confidenceScore: 94,
      statusLabel: 'High confidence — demo',
      statusType: 'high_confidence',
      evidenceCitation: 'CDSCO India Formulary & US NLM RxNorm #284635',
      evidenceTag: 'RxNorm #284635',
      clinicalRationale: 'Proton-pump inhibitor co-prescribed to mitigate gastric irritation from antibiotic.',
      isAmbiguous: false,
      scanTopPercent: '74%',
      verticalAnchorOffsetPx: 335,
    },
  ];

  // Active line index (0, 1, 2)
  const [activeLineIdx, setActiveLineIdx] = useState<number>(0);

  // Scanning animation sequence step:
  // 0: Document visible (0s)
  // 1: Scan line begins (1s)
  // 2: First prescription line highlighted (2s)
  // 3: Structured interpretation appears (3s)
  // 4: Confidence indicator appears (4s)
  // 5: Evidence indicator appears (5s)
  const [animationStep, setAnimationStep] = useState<number>(5);

  // Auto-play cycling status
  const [isAutoPlaying, setIsAutoPlaying] = useState<boolean>(true);
  const [isUserInteracting, setIsUserInteracting] = useState<boolean>(false);

  const resumeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Controlled scanning sequence clock
  useEffect(() => {
    if (!isAutoPlaying || isUserInteracting) return;

    // Reset to step 0 at start of line cycle
    setAnimationStep(0);

    const s1 = setTimeout(() => setAnimationStep(1), 1000);
    const s2 = setTimeout(() => setAnimationStep(2), 2000);
    const s3 = setTimeout(() => setAnimationStep(3), 3000);
    const s4 = setTimeout(() => setAnimationStep(4), 4000);
    const s5 = setTimeout(() => setAnimationStep(5), 5000);

    // Cycle to next line after full cycle
    const cycleTimer = setTimeout(() => {
      setActiveLineIdx((prev) => (prev + 1) % prescriptionLines.length);
    }, 7400);

    return () => {
      clearTimeout(s1);
      clearTimeout(s2);
      clearTimeout(s3);
      clearTimeout(s4);
      clearTimeout(s5);
      clearTimeout(cycleTimer);
    };
  }, [activeLineIdx, isAutoPlaying, isUserInteracting, prescriptionLines.length]);

  // Handle user hover/click on a specific line
  const handleSelectLine = (index: number) => {
    setActiveLineIdx(index);
    setAnimationStep(5); // Show full resolved state immediately on user inspection
    setIsUserInteracting(true);

    if (resumeTimeoutRef.current) {
      clearTimeout(resumeTimeoutRef.current);
    }
  };

  // Resume auto-cycling gently when user leaves interactive area
  const handleMouseLeaveStage = () => {
    if (resumeTimeoutRef.current) clearTimeout(resumeTimeoutRef.current);

    resumeTimeoutRef.current = setTimeout(() => {
      setIsUserInteracting(false);
    }, 4500);
  };

  const currentLine = prescriptionLines[activeLineIdx];

  return (
    <section className="relative pt-20 pb-20 sm:pt-28 sm:pb-28 overflow-hidden bg-canvas border-b border-theme">
      {/* Subtle Environmental Depth: Fine Blueprint Dot-Grid & Soft Radial Lighting (No sci-fi orbs) */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.35] dark:opacity-[0.18]"
        style={{
          backgroundImage: 'radial-gradient(rgba(13, 148, 136, 0.18) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
        aria-hidden="true"
      />
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 pointer-events-none opacity-40 dark:opacity-25"
        style={{
          background: 'radial-gradient(ellipse at 50% -10%, rgba(13, 148, 136, 0.22) 0%, transparent 70%)',
        }}
        aria-hidden="true"
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Asymmetric Two-Part Hero Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          {/* ========================================================= */}
          {/* LEFT: Large Editorial Headline, Subcopy, CTA & Trust Line  */}
          {/* ========================================================= */}
          <div className="lg:col-span-5 space-y-8 text-left order-1">
            {/* Subtle Eyebrow Tag */}
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-surface border border-theme text-xs font-semibold text-teal-800 dark:text-teal-300 shadow-xs">
              <span className="w-2 h-2 rounded-full bg-teal-600 dark:bg-teal-400 animate-pulse" />
              <span>Assistive Prescription Understanding</span>
            </div>

            {/* Editorial Headline */}
            <div className="space-y-1.5">
              <h1 className="text-[clamp(3rem,6vw,5rem)] font-extrabold tracking-[-0.038em] text-theme-primary leading-[0.98]">
                Some prescriptions are clear.
              </h1>
              <h1 className="text-[clamp(3rem,6vw,5rem)] font-extrabold tracking-[-0.038em] text-teal-700 dark:text-teal-400 leading-[0.98]">
                Some are not.
              </h1>
            </div>

            {/* Concise, Credible & Natural Copy */}
            <div className="space-y-3 max-w-xl">
              <p className="text-xl sm:text-2xl font-medium text-theme-primary leading-snug tracking-tight">
                Understand what the handwriting says &mdash; and see when the system isn't sure.
              </p>
              <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
                AURA-Rx transcribes physician cursive into structured medication posology, cross-referenced with standard formularies &mdash; with transparent selective abstention when strokes are ambiguous.
              </p>
            </div>

            {/* Desktop Action Buttons (Hidden on mobile; mobile displays CTA after document) */}
            <div className="hidden sm:flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
              {onOpenUpload && (
                <motion.button
                  whileHover={{ scale: 1.018, y: -1 }}
                  whileTap={{ scale: 0.985 }}
                  onClick={onOpenUpload}
                  className="px-8 py-4 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base sm:text-lg font-semibold transition-all flex items-center justify-center gap-3 shadow-md hover:shadow-lg cursor-pointer group"
                >
                  <UploadCloud className="w-5 h-5" />
                  <span>Analyze a prescription</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </motion.button>
              )}

              {onScrollToHowItWorks && (
                <button
                  onClick={onScrollToHowItWorks}
                  className="px-6 py-4 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary hover:text-theme-primary text-base font-medium transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                >
                  <span>See how it works</span>
                </button>
              )}
            </div>

            {/* Single Concise Supporting Trust Line (No badge sprawl) */}
            <div className="hidden sm:flex items-center gap-2.5 pt-2 text-sm text-theme-muted">
              <span className="w-2 h-2 rounded-full bg-teal-600 dark:bg-teal-400 shrink-0" />
              <span className="font-medium">Original prescription remains the primary reference.</span>
            </div>
          </div>

          {/* ========================================================= */}
          {/* RIGHT: Large Interactive Prescription Document Showcase  */}
          {/* ========================================================= */}
          <div
            className="lg:col-span-7 order-2 space-y-4"
            onMouseLeave={handleMouseLeaveStage}
          >
            {/* Interactive Mode Control Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-2 text-xs">
              {/* Process Stage Indicator */}
              <div className="flex items-center gap-2 text-theme-secondary font-medium">
                <span className="w-2 h-2 rounded-full bg-teal-600 dark:bg-teal-400" />
                <span className="font-semibold text-theme-primary">Reading Sequence:</span>
                <span className="text-theme-muted hidden sm:inline">
                  {animationStep === 0 && '01 Document Loaded'}
                  {animationStep === 1 && '02 Scanning Beam Active'}
                  {animationStep === 2 && '03 Stroke Highlighted'}
                  {animationStep === 3 && '04 Entity Interpreted'}
                  {animationStep === 4 && '05 Confidence Assessed'}
                  {animationStep >= 5 && '06 Formulary Grounded'}
                </span>
              </div>

              {/* Auto-Play Toggle & Line Jump Buttons */}
              <div className="flex items-center gap-1.5">
                {prescriptionLines.map((line, idx) => {
                  const isActive = activeLineIdx === idx;
                  return (
                    <button
                      key={line.id}
                      onClick={() => handleSelectLine(idx)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                        isActive
                          ? line.isAmbiguous
                            ? 'bg-amber-600 text-white font-semibold shadow-xs'
                            : 'bg-teal-700 text-white font-semibold shadow-xs'
                          : 'bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary'
                      }`}
                      title={`Inspect ${line.shortName}`}
                    >
                      {line.shortName}
                    </button>
                  );
                })}

                <button
                  onClick={() => setIsAutoPlaying(!isAutoPlaying)}
                  className="p-1.5 rounded-lg bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary cursor-pointer shadow-xs transition-colors ml-1"
                  title={isAutoPlaying ? 'Pause automatic scanning tour' : 'Resume automatic scanning tour'}
                  aria-label={isAutoPlaying ? 'Pause tour' : 'Play tour'}
                >
                  {isAutoPlaying ? (
                    <Pause className="w-3.5 h-3.5 text-theme-muted" />
                  ) : (
                    <Play className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                  )}
                </button>
              </div>
            </div>

            {/* ========================================================= */}
            {/* The Integrated Physical Document & Transformation Stage   */}
            {/* ========================================================= */}
            <div className="relative rounded-3xl p-4 sm:p-6 lg:p-7 bg-surface/70 border border-theme shadow-elevated-card backdrop-blur-sm">
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch relative">
                {/* ------------------------------------------------------- */}
                {/* 1. Authentic Physical Prescription Document Artifact     */}
                {/* Physical paper realism: remains paper-like in DARK theme! */}
                {/* ------------------------------------------------------- */}
                <div className="xl:col-span-7 relative rounded-2xl bg-[#FCFAF6] border border-[#E5DEC9] text-slate-900 shadow-[0_16px_45px_-12px_rgba(25,20,15,0.12),0_1px_3px_rgba(0,0,0,0.04)] dark:shadow-[0_24px_65px_-12px_rgba(0,0,0,0.75),0_0_0_1px_rgba(255,255,255,0.08)] overflow-hidden transition-all select-none">
                  {/* Subtle Ruled Stationery Background Lines */}
                  <div
                    className="absolute inset-0 pointer-events-none opacity-40"
                    style={{
                      backgroundImage: 'linear-gradient(to bottom, rgba(180, 168, 145, 0.28) 1px, transparent 1px)',
                      backgroundSize: '100% 28px',
                    }}
                    aria-hidden="true"
                  />

                  {/* Traveling Scan Beam (Active during step 1 & 2) */}
                  <AnimatePresence>
                    {animationStep >= 1 && (
                      <motion.div
                        key={`scan-beam-${activeLineIdx}`}
                        initial={{ opacity: 0, top: '20%' }}
                        animate={{
                          opacity: [0, 0.9, 0.9, 0.3],
                          top: currentLine.scanTopPercent,
                        }}
                        transition={{
                          duration: 1.2,
                          ease: [0.25, 1, 0.5, 1],
                        }}
                        className="absolute inset-x-0 h-10 -translate-y-1/2 pointer-events-none z-20 bg-gradient-to-b from-teal-600/0 via-teal-600/18 to-transparent border-b-2 border-teal-600/60 shadow-[0_4px_12px_rgba(13,148,136,0.15)]"
                      >
                        <div className="absolute right-3 top-1 px-2 py-0.5 rounded bg-white/95 border border-teal-600/30 text-[10px] font-mono font-semibold text-teal-900 shadow-xs flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-ping" />
                          <span>Optical Scan Active</span>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Paper Content Padding */}
                  <div className="p-5 sm:p-6 space-y-4 relative z-10">
                    {/* Clinical Letterhead (Clearly fictional / demo) */}
                    <div className="border-b border-[#E2D9C4] pb-3 flex justify-between items-start">
                      <div className="space-y-0.5">
                        <div className="text-[11px] font-bold tracking-wide uppercase text-teal-800">
                          {canvasData.doctorHeader.clinicName}
                        </div>
                        <h2 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
                          {canvasData.doctorHeader.name}
                        </h2>
                        <p className="text-[11px] text-slate-600">
                          {canvasData.doctorHeader.qualifications} &bull; {canvasData.doctorHeader.clinicAddress}
                        </p>
                      </div>
                      <div className="text-right space-y-1">
                        <span className="inline-block font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-[#ECE5D3] text-slate-800 border border-[#DCD3BE]">
                          {canvasData.doctorHeader.regNo}
                        </span>
                        <div className="text-[10px] text-slate-500 font-medium">
                          Date: {canvasData.patientInfo.date}
                        </div>
                      </div>
                    </div>

                    {/* Patient & Vitals Line */}
                    <div className="pb-2.5 border-b border-dashed border-[#E2D9C4] flex flex-wrap justify-between gap-2 text-[11px] text-slate-700">
                      <span>
                        <strong className="text-slate-900">Patient:</strong> {canvasData.patientInfo.name} ({canvasData.patientInfo.ageGender})
                      </span>
                      <span>
                        <strong className="text-slate-900">Vitals:</strong> {canvasData.patientInfo.vitals}
                      </span>
                    </div>

                    {/* ℞ Symbol Header */}
                    <div className="flex items-center justify-between pt-0.5">
                      <div className="text-[#1E3A8A] font-serif italic text-2xl sm:text-3xl font-black select-none">
                        ℞
                      </div>
                      <div className="text-[10px] font-medium text-slate-500 italic">
                        Tap or hover any line below to inspect resolution
                      </div>
                    </div>

                    {/* --------------------------------------------------- */}
                    {/* The 3 Handwritten Prescription Lines (Doctor Ink)   */}
                    {/* --------------------------------------------------- */}
                    <div className="space-y-2.5 pt-1">
                      {prescriptionLines.map((line, idx) => {
                        const isLineActive = activeLineIdx === idx;
                        const isLineHighlighted = isLineActive && animationStep >= 2;
                        const stroke = canvasData.strokes[line.strokeIdx];

                        return (
                          <div
                            key={line.id}
                            onMouseEnter={() => handleSelectLine(idx)}
                            onClick={() => handleSelectLine(idx)}
                            className={`p-3 rounded-xl transition-all duration-200 cursor-pointer relative ${
                              isLineHighlighted
                                ? line.isAmbiguous
                                  ? 'bg-amber-500/12 border border-amber-500/60 ring-1 ring-amber-500/40 shadow-xs'
                                  : 'bg-teal-500/12 border border-teal-600/60 ring-1 ring-teal-600/40 shadow-xs'
                                : 'bg-transparent border border-transparent hover:bg-slate-200/50'
                            }`}
                          >
                            {/* Line Metadata Label */}
                            <div className="flex items-center justify-between text-[11px] mb-1">
                              <span className="font-semibold text-slate-700">
                                {line.label}
                              </span>

                              {isLineHighlighted && (
                                <span
                                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                                    line.isAmbiguous
                                      ? 'bg-amber-100 text-amber-900 border border-amber-300'
                                      : 'bg-teal-100 text-teal-900 border border-teal-300'
                                  }`}
                                >
                                  {line.isAmbiguous ? 'Ambiguity Flagged' : 'Target In Focus'}
                                </span>
                              )}
                            </div>

                            {/* SVG Cursive Ink Stroke */}
                            <div className="py-0.5 overflow-hidden">
                              <svg
                                viewBox="0 0 650 35"
                                className="w-full h-8 overflow-visible"
                                xmlns="http://www.w3.org/2000/svg"
                              >
                                <path
                                  d={stroke.svgPath}
                                  fill="none"
                                  stroke={
                                    isLineHighlighted
                                      ? line.isAmbiguous
                                        ? '#92400E' // Rich amber ink
                                        : '#1E3A8A' // Deep royal fountain ink
                                      : '#334155' // Muted ink
                                  }
                                  strokeWidth={isLineHighlighted ? '3.4' : '2.8'}
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  className="transition-all duration-300"
                                />
                              </svg>
                            </div>

                            {/* Anchor Point Nub for Visual Transformation Connector */}
                            {isLineHighlighted && (
                              <div
                                className={`hidden xl:block absolute -right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full border-2 bg-white shadow-xs z-30 ${
                                  line.isAmbiguous
                                    ? 'border-amber-600 ring-2 ring-amber-400/30'
                                    : 'border-teal-600 ring-2 ring-teal-400/30'
                                }`}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Prescriber Signature & Rubber Stamp (Physical Realism) */}
                    <div className="pt-3 mt-2 border-t border-[#E2D9C4] flex justify-between items-end text-xs text-slate-600">
                      <div className="border border-[#DCD3BE] rounded px-2.5 py-1 bg-[#F5EFE1] font-mono text-[9px] text-[#991B1B] font-bold tracking-wider">
                        {canvasData.clinicStampText}
                      </div>

                      <div className="text-right space-y-0.5">
                        <svg viewBox="0 0 200 50" className="w-24 h-6 inline-block">
                          <path
                            d={canvasData.doctorSignaturePath}
                            fill="none"
                            stroke="#1E3A8A"
                            strokeWidth="2.2"
                            strokeLinecap="round"
                          />
                        </svg>
                        <p className="text-[9px] text-slate-500 font-mono">
                          Physician Signature On File
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* ------------------------------------------------------- */}
                {/* 2. Structured Interpretation Card (Digital Engine)       */}
                {/* Visual Transformation: Connected directly to handwriting */}
                {/* ------------------------------------------------------- */}
                <div className="xl:col-span-5 flex flex-col justify-between rounded-2xl bg-surface p-5 sm:p-6 border border-theme shadow-md relative overflow-hidden transition-all">
                  {/* Subtle Target Anchor Nub on Card Edge */}
                  {animationStep >= 2 && (
                    <div
                      className={`hidden xl:block absolute -left-2 top-8 w-3.5 h-3.5 rounded-full border-2 bg-white shadow-xs z-30 ${
                        currentLine.isAmbiguous
                          ? 'border-amber-600 ring-2 ring-amber-400/30'
                          : 'border-teal-600 ring-2 ring-teal-400/30'
                      }`}
                    />
                  )}

                  {/* Connector Lead Label (Clarifies the visual transformation) */}
                  <div className="flex items-center justify-between border-b border-theme pb-3 mb-4 text-xs">
                    <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-theme-muted text-[11px]">
                      <ChevronRight className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                      <span>Line {currentLine.lineNum} Interpretation</span>
                    </div>

                    {/* Step 4: Confidence Indicator */}
                    <AnimatePresence mode="wait">
                      {animationStep >= 4 ? (
                        <motion.div
                          key={`status-${currentLine.id}`}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9 }}
                          transition={{ duration: 0.25 }}
                        >
                          {currentLine.statusType === 'needs_verification' ? (
                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-950/70 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                              <span>Needs verification</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-100 dark:bg-emerald-950/70 text-emerald-900 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-800">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                              <span>High confidence &bull; demo</span>
                            </span>
                          )}
                        </motion.div>
                      ) : (
                        <div className="text-[11px] text-theme-muted font-medium italic animate-pulse">
                          Evaluating line...
                        </div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Step 3: Structured Medicine Entity Details */}
                  <div className="space-y-4 flex-1">
                    <AnimatePresence mode="wait">
                      {animationStep >= 3 ? (
                        <motion.div
                          key={`entity-${currentLine.id}`}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -8 }}
                          transition={{ duration: 0.3 }}
                          className="space-y-2"
                        >
                          <div className="text-xs font-semibold text-teal-700 dark:text-teal-400 uppercase tracking-wider">
                            Interpreted Entity
                          </div>
                          <h3 className="text-xl sm:text-2xl font-extrabold text-theme-primary tracking-tight leading-tight">
                            {currentLine.interpretedName}
                          </h3>
                          <p className="text-xs sm:text-sm text-theme-secondary font-medium">
                            {currentLine.genericFormula}
                          </p>
                          <div className="text-[11px] text-theme-muted font-mono">
                            {currentLine.brandDetails}
                          </div>
                        </motion.div>
                      ) : (
                        <div className="py-6 text-center text-sm text-theme-muted italic">
                          Scanning cursive ink stroke...
                        </div>
                      )}
                    </AnimatePresence>

                    {/* Regimen Posology Breakdown Grid */}
                    <AnimatePresence mode="wait">
                      {animationStep >= 3 && (
                        <motion.div
                          key={`slots-${currentLine.id}`}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.1, duration: 0.25 }}
                          className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1 text-xs"
                        >
                          <div className="p-2.5 rounded-xl bg-surface-subtle border border-theme">
                            <span className="text-theme-muted block text-[10px] font-medium uppercase tracking-wider">
                              Frequency
                            </span>
                            <span className="font-bold text-theme-primary text-xs leading-snug">
                              {currentLine.frequency}
                            </span>
                          </div>
                          <div className="p-2.5 rounded-xl bg-surface-subtle border border-theme">
                            <span className="text-theme-muted block text-[10px] font-medium uppercase tracking-wider">
                              Timing
                            </span>
                            <span className="font-bold text-theme-primary text-xs leading-snug">
                              {currentLine.mealRelation}
                            </span>
                          </div>
                          <div className="p-2.5 rounded-xl bg-surface-subtle border border-theme">
                            <span className="text-theme-muted block text-[10px] font-medium uppercase tracking-wider">
                              Duration
                            </span>
                            <span className="font-bold text-theme-primary text-xs leading-snug">
                              {currentLine.duration}
                            </span>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Uncertainty / Selective Abstention Notice (For Line 2) */}
                    {currentLine.isAmbiguous && animationStep >= 3 && (
                      <motion.div
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-1.5"
                      >
                        <div className="font-bold flex items-center gap-1.5">
                          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                          <span>Selective Abstention Rationale:</span>
                        </div>
                        <p className="leading-relaxed text-[11px]">
                          {currentLine.abstentionReason}
                        </p>
                      </motion.div>
                    )}
                  </div>

                  {/* Step 5: Evidence Grounding Indicator Footer */}
                  <div className="pt-4 mt-4 border-t border-theme flex flex-wrap items-center justify-between gap-2 text-xs">
                    <AnimatePresence mode="wait">
                      {animationStep >= 5 ? (
                        <motion.div
                          key={`evidence-${currentLine.id}`}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="flex items-center gap-2 text-theme-secondary text-[11px]"
                        >
                          <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                          <span>{currentLine.evidenceCitation}</span>
                        </motion.div>
                      ) : (
                        <div className="text-[11px] text-theme-muted italic">
                          Grounding against clinical formularies...
                        </div>
                      )}
                    </AnimatePresence>

                    <div className="font-mono text-[11px] text-theme-muted">
                      Demo Score: <strong className="text-theme-primary font-bold">{currentLine.confidenceScore}%</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ========================================================= */}
            {/* MOBILE ONLY: CTA Group & Trust Statement (Stacked Third)  */}
            {/* ========================================================= */}
            <div className="sm:hidden pt-4 space-y-3">
              {onOpenUpload && (
                <button
                  onClick={onOpenUpload}
                  className="w-full py-4 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-md cursor-pointer"
                >
                  <UploadCloud className="w-5 h-5" />
                  <span>Analyze a prescription</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}

              {onScrollToHowItWorks && (
                <button
                  onClick={onScrollToHowItWorks}
                  className="w-full py-3.5 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary text-sm font-medium transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                >
                  <span>See how it works</span>
                </button>
              )}

              <p className="text-xs text-center text-theme-muted pt-1">
                Original prescription remains the primary reference.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
