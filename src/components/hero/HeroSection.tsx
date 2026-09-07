import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Clock,
} from 'lucide-react';

export interface HeroSectionProps {
  onOpenUpload?: () => void;
  onScrollToHowItWorks?: () => void;
}

export type ScanPhase =
  | 'idle'           // Phase 1: Document visible with subtle ambient breathing & shadow
  | 'scan_line1'     // Phase 2: Refined optical scan line moves top-to-bottom toward Line 1
  | 'detect_line1'   // Phase 3: Ink becomes emphasized, small focus region appears
  | 'interpret_line1'// Phase 4 & 5: Connector line grows, interpretation panel reveals (High confidence)
  | 'scan_line2'     // Phase 6a: Scan line sweeps smoothly down to Line 2
  | 'detect_line2'   // Phase 6b: Focus bounds ambiguous cursive ligature in amber
  | 'interpret_line2'// Phase 6c: Connector grows, reveals "Needs verification" (Selective Abstention)
  | 'reset';         // Phase 7: Smoothly returns to idle

export interface PrescriptionLineItem {
  id: string;
  lineNum: number;
  label: string;
  shortTitle: string;
  strokeIdx: number;
  doctorInkText: string;
  interpretedName: string;
  genericFormula: string;
  posologyDetail: string;
  duration: string;
  confidenceScore: number;
  statusType: 'high_confidence' | 'needs_verification';
  statusLabel: string;
  evidenceCitation: string;
  isAmbiguous: boolean;
  abstentionReason?: string;
  scanTopPercent: string;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onOpenUpload,
  onScrollToHowItWorks,
}) => {
  const canvasData = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];

  // Fictional clinical prescription lines illustrating clear recognition vs. transparent uncertainty
  const prescriptionLines: PrescriptionLineItem[] = [
    {
      id: 'line-1',
      lineNum: 1,
      label: 'Line 01',
      shortTitle: 'Augmentin 625',
      strokeIdx: 0,
      doctorInkText: 'Tab. Augmentin 625 Duo  1 - 0 - 1 x 5d  (P.C.)',
      interpretedName: 'Amoxicillin + Clavulanate',
      genericFormula: '500 mg + 125 mg',
      posologyDetail: 'Twice daily (1 - 0 - 1) · Strictly after meals (P.C.)',
      duration: '5 days course',
      confidenceScore: 96,
      statusType: 'high_confidence',
      statusLabel: 'High confidence · Demo',
      evidenceCitation: 'Grounded: CDSCO & US NLM RxNorm #213169',
      isAmbiguous: false,
      scanTopPercent: '38%',
    },
    {
      id: 'line-2',
      lineNum: 2,
      label: 'Line 02 (Ambiguous)',
      shortTitle: 'Pan 40 (Ambiguity)',
      strokeIdx: 1,
      doctorInkText: 'Cap. Pan 40mg  1 - 0 - 0 x 5d  (A.C. 30m before food)',
      interpretedName: 'Pantoprazole Sodium',
      genericFormula: 'Possible dosage · 40 mg Gastro-Resistant',
      posologyDetail: 'Candidate: Once daily (OD) · 30m before food (A.C.)',
      duration: '5 days course',
      confidenceScore: 61,
      statusType: 'needs_verification',
      statusLabel: 'Needs verification',
      evidenceCitation: 'Selective Abstention · Pharmacist review mandated',
      isAmbiguous: true,
      abstentionReason:
        'Terminal cursive stroke is morphologically ambiguous between OD and BD. The system refrains from autonomous confirmation and flags for pharmacist review.',
      scanTopPercent: '56%',
    },
    {
      id: 'line-3',
      lineNum: 3,
      label: 'Line 03',
      shortTitle: 'Dolo 650',
      strokeIdx: 2,
      doctorInkText: 'Tab. Dolo 650mg  1 - 0 - 1  S.O.S. (if fever > 100°F)',
      interpretedName: 'Paracetamol (Acetaminophen)',
      genericFormula: '650 mg Tablet (Dolo 650)',
      posologyDetail: 'As needed (S.O.S.) when fever rises > 100°F · Max 3/day',
      duration: 'Max 3 days as needed',
      confidenceScore: 94,
      statusType: 'high_confidence',
      statusLabel: 'High confidence · Demo',
      evidenceCitation: 'Grounded: CDSCO & US NLM RxNorm #161',
      isAmbiguous: false,
      scanTopPercent: '74%',
    },
  ];

  // State management
  const [phase, setPhase] = useState<ScanPhase>('idle');
  const [selectedLineIdx, setSelectedLineIdx] = useState<number>(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState<boolean>(true);
  const [isUserInteracting, setIsUserInteracting] = useState<boolean>(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);

  // Geometric measurement refs for the physical connector line
  const stageGridRef = useRef<HTMLDivElement | null>(null);
  const lineAnchorRefs = [
    useRef<HTMLDivElement | null>(null),
    useRef<HTMLDivElement | null>(null),
    useRef<HTMLDivElement | null>(null),
  ];
  const panelAnchorRef = useRef<HTMLDivElement | null>(null);
  const [connectorLine, setConnectorLine] = useState<{
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  } | null>(null);

  const resumeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Check for prefers-reduced-motion
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      setPrefersReducedMotion(mediaQuery.matches);

      const handleMotionChange = (e: MediaQueryListEvent) => {
        setPrefersReducedMotion(e.matches);
      };

      mediaQuery.addEventListener('change', handleMotionChange);
      return () => mediaQuery.removeEventListener('change', handleMotionChange);
    }
  }, []);

  // Determine active line index
  const activeLineIdx = isUserInteracting ? selectedLineIdx : phase.includes('line2') ? 1 : 0;
  const currentLine = prescriptionLines[activeLineIdx];

  // Measure connector line positions whenever active line or phase changes
  const measureConnector = useCallback(() => {
    if (!stageGridRef.current) return;
    const stageRect = stageGridRef.current.getBoundingClientRect();
    const anchorEl = lineAnchorRefs[activeLineIdx]?.current;
    const panelEl = panelAnchorRef.current;

    if (anchorEl && panelEl) {
      const aRect = anchorEl.getBoundingClientRect();
      const pRect = panelEl.getBoundingClientRect();
      setConnectorLine({
        x1: aRect.left + aRect.width / 2 - stageRect.left,
        y1: aRect.top + aRect.height / 2 - stageRect.top,
        x2: pRect.left + pRect.width / 2 - stageRect.left,
        y2: pRect.top + pRect.height / 2 - stageRect.top,
      });
    }
  }, [activeLineIdx]);

  useEffect(() => {
    measureConnector();
    window.addEventListener('resize', measureConnector);
    return () => window.removeEventListener('resize', measureConnector);
  }, [measureConnector, phase]);

  // Full 7-Phase Story Loop (~11.4 seconds total sequence)
  useEffect(() => {
    if (!isAutoPlaying || isUserInteracting || prefersReducedMotion) {
      return;
    }

    // Phase 1: IDLE (0s - 1.2s)
    const t0 = setTimeout(() => {
      setPhase('idle');
      setSelectedLineIdx(0);
    }, 0);

    // Phase 2: SCAN (1.2s - 2.4s) - subtle physical scan line glides top to bottom
    const t1 = setTimeout(() => {
      setPhase('scan_line1');
    }, 1200);

    // Phase 3: DETECT (2.4s - 3.5s) - ink emphasizes, focus region bounds Line 1
    const t2 = setTimeout(() => {
      setPhase('detect_line1');
    }, 2400);

    // Phase 4 & 5: INTERPRET & CONFIDENCE (3.5s - 6.4s) - connector grows, panel reveals High Confidence demo
    const t3 = setTimeout(() => {
      setPhase('interpret_line1');
    }, 3500);

    // Phase 6a: SECOND FIELD SCAN (6.4s - 7.4s) - scan line moves to Line 2
    const t4 = setTimeout(() => {
      setPhase('scan_line2');
      setSelectedLineIdx(1);
    }, 6400);

    // Phase 6b: DETECT AMBIGUITY (7.4s - 8.4s) - amber bounding box on ambiguous cursive stroke
    const t5 = setTimeout(() => {
      setPhase('detect_line2');
    }, 7400);

    // Phase 6c: INTERPRET UNCERTAINTY (8.4s - 10.5s) - reveals "Needs verification" & Selective Abstention
    const t6 = setTimeout(() => {
      setPhase('interpret_line2');
    }, 8400);

    // Phase 7: RESET (10.5s - 11.4s) - smoothly dissolve highlights and return to idle
    const t7 = setTimeout(() => {
      setPhase('reset');
    }, 10500);

    // Loop cycle completion
    const loopTimer = setTimeout(() => {
      setPhase('idle');
      setSelectedLineIdx(0);
    }, 11400);

    return () => {
      clearTimeout(t0);
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearTimeout(t5);
      clearTimeout(t6);
      clearTimeout(t7);
      clearTimeout(loopTimer);
    };
  }, [isAutoPlaying, isUserInteracting, prefersReducedMotion]);

  // Handle direct user interaction (click/tap or hover)
  const handleUserSelectLine = (index: number) => {
    setSelectedLineIdx(index);
    setIsUserInteracting(true);
    setPhase(index === 1 ? 'interpret_line2' : 'interpret_line1');

    if (resumeTimeoutRef.current) {
      clearTimeout(resumeTimeoutRef.current);
    }
  };

  // Resume automated loop after user moves away
  const handleMouseLeaveStage = () => {
    if (prefersReducedMotion) return;

    if (resumeTimeoutRef.current) clearTimeout(resumeTimeoutRef.current);
    resumeTimeoutRef.current = setTimeout(() => {
      setIsUserInteracting(false);
      setPhase('idle');
    }, 4500);
  };

  // Visual highlight flags
  const isLine1Highlighted =
    (phase === 'detect_line1' || phase === 'interpret_line1') && activeLineIdx === 0;
  const isLine2Highlighted =
    (phase === 'detect_line2' || phase === 'interpret_line2') && activeLineIdx === 1;
  const isLine3Highlighted = isUserInteracting && activeLineIdx === 2;

  // Scan bar visibility and position
  const isScanBarVisible =
    !isUserInteracting &&
    !prefersReducedMotion &&
    (phase === 'scan_line1' ||
      phase === 'detect_line1' ||
      phase === 'scan_line2' ||
      phase === 'detect_line2');

  const scanBarTopPercent =
    phase === 'scan_line1' || phase === 'detect_line1'
      ? '38%'
      : phase === 'scan_line2' || phase === 'detect_line2'
      ? '56%'
      : '16%';

  // Interpretation panel visibility
  const isInterpretationVisible =
    isUserInteracting ||
    phase === 'interpret_line1' ||
    phase === 'scan_line2' ||
    phase === 'detect_line2' ||
    phase === 'interpret_line2' ||
    prefersReducedMotion;

  // Connector line visibility
  const isConnectorVisible =
    (isUserInteracting ||
      phase === 'interpret_line1' ||
      phase === 'interpret_line2' ||
      prefersReducedMotion) &&
    connectorLine !== null;

  return (
    <section className="relative pt-16 pb-16 sm:pt-24 sm:pb-24 overflow-hidden bg-canvas border-b border-theme">
      {/* Subtle Environmental Depth: Gentle ambient illumination & faint ruling grid */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.25] dark:opacity-[0.12]"
        style={{
          backgroundImage: 'radial-gradient(rgba(13, 148, 136, 0.20) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
        aria-hidden="true"
      />
      <div
        className="absolute top-0 right-1/4 w-[600px] h-[400px] pointer-events-none opacity-30 dark:opacity-20"
        style={{
          background:
            'radial-gradient(ellipse at 50% 30%, rgba(13, 148, 136, 0.22) 0%, transparent 70%)',
        }}
        aria-hidden="true"
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          {/* ========================================================= */}
          {/* LEFT: Balanced Headline, Subcopy, CTA & Trust Line         */}
          {/* Preserved without modifying typography scale or navigation */}
          {/* ========================================================= */}
          <div className="lg:col-span-5 space-y-6 text-left order-1">
            {/* Eyebrow (14-15px) */}
            <div className="inline-flex items-center gap-2 text-sm font-semibold text-teal-800 dark:text-teal-300">
              <span className="w-2 h-2 rounded-full bg-teal-600 dark:bg-teal-400" />
              <span>Assistive prescription understanding</span>
            </div>

            {/* Headline: Responsive 56-72px desktop / 42-50px mobile */}
            <div className="space-y-1">
              <h1 className="text-[clamp(2.5rem,4.2vw,4.25rem)] font-extrabold tracking-[-0.035em] text-theme-primary leading-[1.04]">
                Some prescriptions are clear.<br />
                <span className="text-teal-700 dark:text-teal-400">Some are not.</span>
              </h1>
            </div>

            {/* Supporting Copy (18-20px subhead, 16px body) */}
            <div className="space-y-2.5 max-w-lg">
              <p className="text-lg sm:text-xl font-medium text-theme-primary leading-snug">
                Understand difficult handwriting &mdash; and see when the system isn&rsquo;t sure.
              </p>
              <p className="text-sm sm:text-base text-theme-secondary leading-relaxed">
                Transcribes physician cursive into structured medication posology, cross-referenced with standard formularies &mdash; with transparent selective abstention when strokes are ambiguous.
              </p>
            </div>

            {/* Desktop Actions (Hidden on mobile; mobile displays CTA after document) */}
            <div className="hidden sm:flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5 pt-2">
              {onOpenUpload && (
                <button
                  onClick={onOpenUpload}
                  className="px-7 py-3.5 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-md hover:shadow-lg cursor-pointer group"
                >
                  <span>Analyze a prescription</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              )}

              {onScrollToHowItWorks && (
                <button
                  onClick={onScrollToHowItWorks}
                  className="px-5 py-3.5 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary hover:text-theme-primary text-base font-medium transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                >
                  <span>How it works</span>
                </button>
              )}
            </div>

            {/* Concise Trust Line */}
            <div className="hidden sm:flex items-center gap-2 pt-1 text-xs sm:text-sm text-theme-muted">
              <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
              <span>Original prescription remains the primary reference.</span>
            </div>
          </div>

          {/* ========================================================= */}
          {/* RIGHT: Signature Scanning & Interpretation Experience      */}
          {/* Fully Rebuilt: Authentic Paper, Refined Scan, Precise Line */}
          {/* ========================================================= */}
          <div
            className="lg:col-span-7 order-2 space-y-3"
            onMouseLeave={handleMouseLeaveStage}
          >
            {/* Top Interactive Mode Ribbon */}
            <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
              <div className="text-xs font-semibold text-theme-secondary flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    phase === 'interpret_line2' || (isUserInteracting && activeLineIdx === 1)
                      ? 'bg-amber-600 animate-pulse'
                      : 'bg-teal-600 animate-pulse'
                  }`}
                />
                <span>
                  {phase === 'idle'
                    ? 'Prescription Document Ready'
                    : phase.includes('scan')
                    ? 'Optical reader scanning strokes...'
                    : phase.includes('detect')
                    ? 'Handwritten line detected'
                    : phase === 'interpret_line2'
                    ? 'Selective abstention: Uncertainty flagged'
                    : 'Field interpreted'}
                </span>
              </div>

              {/* Direct Line Selection Controls */}
              <div className="flex items-center gap-1.5">
                {prescriptionLines.map((line, idx) => {
                  const isActive = activeLineIdx === idx;
                  return (
                    <button
                      key={line.id}
                      onClick={() => handleUserSelectLine(idx)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                        isActive
                          ? line.isAmbiguous
                            ? 'bg-amber-600 text-white font-semibold shadow-xs'
                            : 'bg-teal-700 text-white font-semibold shadow-xs'
                          : 'bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary hover:text-theme-primary'
                      }`}
                      title={`Inspect ${line.shortTitle}`}
                    >
                      {line.shortTitle}
                    </button>
                  );
                })}

                <button
                  onClick={() => setIsAutoPlaying(!isAutoPlaying)}
                  className="p-1.5 rounded-lg bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary cursor-pointer shadow-xs transition-colors ml-1"
                  title={isAutoPlaying ? 'Pause automated cycle' : 'Resume automated cycle'}
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

            {/* Document Stage Frame Container */}
            <div className="relative rounded-3xl p-4 sm:p-5 lg:p-6 bg-surface-subtle/60 border border-theme shadow-elevated-card">
              <div
                ref={stageGridRef}
                className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-stretch relative"
              >
                {/* ------------------------------------------------------- */}
                {/* PRECISE SVG CONNECTOR LINE (Phase 4: Grows from detect) */}
                {/* Physical vector bridge between paper line & card panel  */}
                {/* ------------------------------------------------------- */}
                {isConnectorVisible && connectorLine && (
                  <svg
                    className="hidden xl:block absolute inset-0 w-full h-full pointer-events-none z-30 overflow-visible"
                    aria-hidden="true"
                  >
                    <defs>
                      <linearGradient id="connectorGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop
                          offset="0%"
                          stopColor={currentLine.isAmbiguous ? '#D97706' : '#0D9488'}
                          stopOpacity="0.85"
                        />
                        <stop
                          offset="100%"
                          stopColor={currentLine.isAmbiguous ? '#B45309' : '#0F766E'}
                          stopOpacity="0.95"
                        />
                      </linearGradient>
                    </defs>

                    {/* Animated connector path: Smooth cubic Bézier curve */}
                    {(() => {
                      const { x1, y1, x2, y2 } = connectorLine;
                      const deltaX = Math.max(20, (x2 - x1) * 0.45);
                      const dPath = `M ${x1} ${y1} C ${x1 + deltaX} ${y1}, ${x2 - deltaX} ${y2}, ${x2} ${y2}`;

                      return (
                        <motion.path
                          key={`connector-${currentLine.id}`}
                          d={dPath}
                          fill="none"
                          stroke="url(#connectorGradient)"
                          strokeWidth="2"
                          strokeLinecap="round"
                          initial={prefersReducedMotion ? { pathLength: 1, opacity: 1 } : { pathLength: 0, opacity: 0 }}
                          animate={{ pathLength: 1, opacity: 1 }}
                          transition={{ duration: 0.35, ease: 'easeOut' }}
                        />
                      );
                    })()}

                    {/* Origin Anchor Node */}
                    <circle
                      cx={connectorLine.x1}
                      cy={connectorLine.y1}
                      r="3.5"
                      fill={currentLine.isAmbiguous ? '#D97706' : '#0D9488'}
                      stroke="#FFFFFF"
                      strokeWidth="1.5"
                    />

                    {/* Destination Anchor Node */}
                    <circle
                      cx={connectorLine.x2}
                      cy={connectorLine.y2}
                      r="3.5"
                      fill={currentLine.isAmbiguous ? '#D97706' : '#0D9488'}
                      stroke="#FFFFFF"
                      strokeWidth="1.5"
                    />
                  </svg>
                )}

                {/* ------------------------------------------------------- */}
                {/* 1. Authentic Physical Prescription Document Sheet       */}
                {/* Physical paper texture, printed structure & real ink    */}
                {/* ------------------------------------------------------- */}
                <motion.div
                  className="xl:col-span-7 relative rounded-2xl p-5 sm:p-6 text-slate-800 shadow-paper overflow-hidden select-none"
                  style={{
                    backgroundColor: 'var(--paper-bg, #FCFAF6)',
                  }}
                  animate={
                    prefersReducedMotion
                      ? {}
                      : {
                          y: phase === 'idle' ? [0, -2, 0] : 0,
                        }
                  }
                  transition={{
                    duration: 5.5,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }}
                >
                  {/* Subtle Physical Document Imperfections: Faint Crease & Watermark */}
                  <div
                    className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-slate-400/20 to-transparent pointer-events-none"
                    aria-hidden="true"
                  />
                  <div
                    className="absolute inset-0 pointer-events-none opacity-[0.035]"
                    style={{
                      backgroundImage:
                        'linear-gradient(rgba(15, 23, 42, 0.4) 1px, transparent 1px)',
                      backgroundSize: '100% 36px',
                    }}
                    aria-hidden="true"
                  />

                  {/* Phase 2: Refined Physical Optical Scan Line (No sci-fi glow) */}
                  <AnimatePresence>
                    {isScanBarVisible && (
                      <motion.div
                        key={`optical-scan-${phase}`}
                        initial={{ opacity: 0, top: '14%' }}
                        animate={{
                          opacity: [0, 0.85, 0.85, 0.3],
                          top: scanBarTopPercent,
                        }}
                        exit={{ opacity: 0 }}
                        transition={{
                          duration: 1.05,
                          ease: [0.25, 1, 0.5, 1],
                        }}
                        className="absolute inset-x-0 h-7 -translate-y-1/2 pointer-events-none z-20 bg-gradient-to-b from-teal-700/0 via-teal-700/10 to-teal-700/20 border-b-2 border-teal-700/70 dark:border-teal-400/70 shadow-[0_1px_4px_rgba(13,148,136,0.12)]"
                      />
                    )}
                  </AnimatePresence>

                  {/* Printed Document Structure: Fictional Clinic Header */}
                  <div className="border-b border-slate-300 pb-2.5 mb-2.5 flex justify-between items-start text-xs">
                    <div>
                      <div className="text-[10px] font-bold tracking-wider uppercase text-teal-900 font-mono">
                        {canvasData.doctorHeader.clinicName}
                      </div>
                      <div className="text-xs sm:text-sm font-bold text-slate-900 tracking-tight">
                        {canvasData.doctorHeader.name}
                      </div>
                      <div className="text-[10px] text-slate-600">
                        Reg. #{canvasData.doctorHeader.regNo} &bull; Outpatient Dept.
                      </div>
                    </div>

                    <div className="text-right text-[10px] text-slate-600 font-mono">
                      <div>Date: {canvasData.patientInfo.date}</div>
                      <div className="font-semibold text-slate-800">
                        Pt: {canvasData.patientInfo.name}
                      </div>
                    </div>
                  </div>

                  {/* Traditional Printed Rx Symbol & Pre-printed Ruled Table Header */}
                  <div className="flex items-center justify-between py-1 border-b border-slate-200 text-[10px] text-slate-500 font-medium">
                    <div className="flex items-center gap-3">
                      <span className="text-[#1E3A8A] font-serif italic text-2xl sm:text-3xl font-black select-none leading-none">
                        ℞
                      </span>
                      <span className="uppercase tracking-wider font-semibold text-[9px] text-slate-400">
                        Medication &amp; Dosage Instructions
                      </span>
                    </div>
                    <span className="text-[9px] text-slate-400 italic">
                      Tap or hover line to inspect
                    </span>
                  </div>

                  {/* Handwritten Medicine Lines (Authentic Cursive SVG Ink) */}
                  <div className="space-y-2 pt-2 relative">
                    {prescriptionLines.map((line, idx) => {
                      const isLineActive = activeLineIdx === idx;
                      const isHighlighted =
                        (idx === 0 && (isLine1Highlighted || (isUserInteracting && isLineActive))) ||
                        (idx === 1 && (isLine2Highlighted || (isUserInteracting && isLineActive))) ||
                        (idx === 2 && isLine3Highlighted);

                      const stroke = canvasData.strokes[line.strokeIdx];

                      return (
                        <div
                          key={line.id}
                          onMouseEnter={() => handleUserSelectLine(idx)}
                          onClick={() => handleUserSelectLine(idx)}
                          className={`p-2.5 rounded-xl transition-all duration-200 cursor-pointer relative ${
                            isHighlighted
                              ? line.isAmbiguous
                                ? 'bg-amber-500/10 border border-amber-600/50 ring-1 ring-amber-600/20'
                                : 'bg-teal-600/10 border border-teal-700/50 ring-1 ring-teal-700/20'
                              : 'bg-transparent border border-transparent hover:bg-slate-200/40'
                          }`}
                        >
                          {/* Field metadata label */}
                          <div className="flex items-center justify-between text-[10px] mb-0.5 text-slate-600">
                            <span className="font-semibold text-[10px] text-slate-700">
                              {line.label}
                            </span>
                            {isHighlighted && (
                              <span
                                className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                                  line.isAmbiguous
                                    ? 'bg-amber-100 text-amber-900 border border-amber-300'
                                    : 'bg-teal-100 text-teal-900 border border-teal-300'
                                }`}
                              >
                                {line.isAmbiguous ? 'Needs Verification' : 'Detected'}
                              </span>
                            )}
                          </div>

                          {/* SVG Cursive Ink Stroke Path (Phase 3: Ink becomes slightly emphasized) */}
                          <div className="py-0.5 overflow-hidden">
                            <svg
                              viewBox="0 0 650 35"
                              className="w-full h-7 overflow-visible"
                              xmlns="http://www.w3.org/2000/svg"
                            >
                              <path
                                d={stroke.svgPath}
                                fill="none"
                                stroke={
                                  isHighlighted
                                    ? line.isAmbiguous
                                      ? '#92400E' // Rich amber ink
                                      : '#1E3A8A' // Deep Prussian blue ink
                                    : '#334155'
                                }
                                strokeWidth={isHighlighted ? '3.4' : '2.8'}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="transition-all duration-200"
                              />
                            </svg>
                          </div>

                          {/* Pre-printed dosage / frequency mark indicator */}
                          <div className="text-[9px] font-mono text-slate-500 flex items-center justify-between pt-0.5">
                            <span>{line.doctorInkText}</span>
                          </div>

                          {/* Anchor Node for Connector Line */}
                          <div
                            ref={lineAnchorRefs[idx]}
                            className={`hidden xl:block absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 bg-white shadow-xs z-30 transition-transform ${
                              isHighlighted
                                ? line.isAmbiguous
                                  ? 'border-amber-600 ring-2 ring-amber-400/30'
                                  : 'border-teal-600 ring-2 ring-teal-400/30'
                                : 'opacity-0'
                            }`}
                          />
                        </div>
                      );
                    })}
                  </div>

                  {/* Document Imperfections: Clinic Stamp & Doctor Signature */}
                  <div className="pt-2.5 mt-2.5 border-t border-slate-300 flex justify-between items-end text-[10px] text-slate-600">
                    <div className="border border-red-400/80 rounded px-2 py-0.5 bg-red-50/80 font-mono text-[9px] text-red-900 font-semibold rotate-[-1.5deg] shadow-xs">
                      {canvasData.clinicStampText}
                    </div>

                    <div className="text-right">
                      <svg viewBox="0 0 200 50" className="w-20 h-5 inline-block">
                        <path
                          d={canvasData.doctorSignaturePath}
                          fill="none"
                          stroke="#1E3A8A"
                          strokeWidth="2.2"
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="text-[9px] text-slate-500 font-mono">
                        Prescriber Verification
                      </div>
                    </div>
                  </div>
                </motion.div>

                {/* ------------------------------------------------------- */}
                {/* 2. Structured Interpretation Panel (Phases 4, 5, 6)     */}
                {/* Editorial typography, confidence pill & abstention card */}
                {/* ------------------------------------------------------- */}
                <div className="xl:col-span-5 flex flex-col justify-between rounded-2xl bg-surface p-5 sm:p-6 border border-theme shadow-md relative overflow-hidden transition-all">
                  {/* Receiving Connector Anchor Point */}
                  <div
                    ref={panelAnchorRef}
                    className={`hidden xl:block absolute -left-1.5 top-8 w-3 h-3 rounded-full border-2 bg-white shadow-xs z-30 ${
                      currentLine.isAmbiguous
                        ? 'border-amber-600 ring-2 ring-amber-400/30'
                        : 'border-teal-600 ring-2 ring-teal-400/30'
                    }`}
                  />

                  {/* Panel Top Strip: Title & Phase 5 Confidence */}
                  <div className="flex items-center justify-between border-b border-theme pb-3 mb-3 text-xs">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-theme-muted">
                      Line 0{currentLine.lineNum} Interpretation
                    </span>

                    {/* Phase 5: Confidence Indicator (Clear Demo vs. Needs Verification) */}
                    <AnimatePresence mode="wait">
                      {isInterpretationVisible ? (
                        <motion.div
                          key={`status-${currentLine.id}`}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          transition={{ duration: 0.2 }}
                        >
                          {currentLine.statusType === 'needs_verification' ? (
                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-950/70 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                              <span>{currentLine.statusLabel}</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-100 dark:bg-emerald-950/70 text-emerald-900 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-800">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                              <span>{currentLine.statusLabel}</span>
                            </span>
                          )}
                        </motion.div>
                      ) : (
                        <span className="text-[11px] text-theme-muted italic">
                          Awaiting scan...
                        </span>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Phase 4: Interpreted Medicine Entity & Dosage */}
                  <div className="space-y-3.5 flex-1">
                    <AnimatePresence mode="wait">
                      {isInterpretationVisible ? (
                        <motion.div
                          key={`entity-${currentLine.id}`}
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -6 }}
                          transition={{ duration: 0.25 }}
                          className="space-y-1"
                        >
                          <div className="text-[11px] font-semibold text-teal-700 dark:text-teal-400 uppercase tracking-wider">
                            Interpreted Medicine
                          </div>
                          <h3 className="text-xl sm:text-2xl font-extrabold text-theme-primary tracking-tight leading-tight">
                            {currentLine.interpretedName}
                          </h3>
                          <p className="text-xs sm:text-sm text-theme-secondary font-medium">
                            {currentLine.genericFormula}
                          </p>
                        </motion.div>
                      ) : (
                        <div className="py-8 text-center text-xs text-theme-muted italic">
                          Illuminating handwritten cursive stroke...
                        </div>
                      )}
                    </AnimatePresence>

                    {/* Regimen Posology Breakdown */}
                    <AnimatePresence mode="wait">
                      {isInterpretationVisible && (
                        <motion.div
                          key={`posology-${currentLine.id}`}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.2 }}
                          className="p-3.5 rounded-xl bg-surface-subtle/80 border border-theme space-y-1.5 text-xs"
                        >
                          <div className="font-semibold text-theme-primary flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                            <span>Prescribed Posology:</span>
                          </div>
                          <p className="text-theme-secondary leading-relaxed">
                            {currentLine.posologyDetail}
                          </p>
                          <p className="text-theme-muted text-[11px]">
                            Duration: {currentLine.duration}
                          </p>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Phase 6: Uncertainty & Selective Abstention Notice */}
                    {/* Explicitly demonstrates that the system does NOT blindly guess */}
                    {currentLine.isAmbiguous && isInterpretationVisible && (
                      <motion.div
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-1"
                      >
                        <div className="font-semibold flex items-center gap-1.5 text-[11px]">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                          <span>Selective Abstention Active:</span>
                        </div>
                        <p className="leading-relaxed text-[11px] text-amber-800 dark:text-amber-300">
                          {currentLine.abstentionReason}
                        </p>
                      </motion.div>
                    )}
                  </div>

                  {/* Standard Formulary Grounding & Confidence Citation */}
                  <div className="pt-3.5 mt-3 border-t border-theme flex items-center justify-between text-[11px] text-theme-muted">
                    <div className="flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                      <span>{currentLine.evidenceCitation}</span>
                    </div>

                    <div className="font-mono text-teal-700 dark:text-teal-400 font-semibold">
                      {currentLine.confidenceScore}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Mobile View CTA Fallback */}
            <div className="sm:hidden pt-3 space-y-2.5">
              {onOpenUpload && (
                <button
                  onClick={onOpenUpload}
                  className="w-full py-3.5 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base font-semibold transition-all flex items-center justify-center gap-2 shadow-md cursor-pointer"
                >
                  <UploadCloud className="w-5 h-5" />
                  <span>Analyze a prescription</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}

              {onScrollToHowItWorks && (
                <button
                  onClick={onScrollToHowItWorks}
                  className="w-full py-3 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary text-sm font-medium transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                >
                  <span>How it works</span>
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

