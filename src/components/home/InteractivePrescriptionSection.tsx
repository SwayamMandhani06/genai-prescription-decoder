import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  CheckCircle2,
  AlertTriangle,
  Play,
  Pause,
  ShieldCheck,
  FileText,
  Clock,
  Calendar,
  Pill,
} from 'lucide-react';

export interface BoundingBoxPercent {
  left: number;   // percent 0-100
  top: number;    // percent 0-100
  width: number;  // percent 0-100
  height: number; // percent 0-100
  scanTop: number; // percent 0-100 for scanning line center
}

export interface PrescriptionLineItem {
  id: string;
  lineNum: number;
  label: string;
  shortTitle: string;
  doctorInkText: string;
  interpretedName: string;
  tradeBrand: string;
  genericFormula: string;
  posologyDetail: string;
  scheduleTiming: string;
  duration: string;
  statusType: 'high_confidence' | 'needs_verification';
  statusLabel: string;
  evidenceCitation: string;
  isAmbiguous: boolean;
  abstentionReason?: string;
  patientGuidance: string;
  box: BoundingBoxPercent;
}

export const DEMO_PRESCRIPTION_LINES: PrescriptionLineItem[] = [
  {
    id: 'line-1',
    lineNum: 1,
    label: 'Line 01',
    shortTitle: 'Augmentin 625 Duo',
    doctorInkText: 'Tab. Augmentin 625 Duo 1 - 0 - 1 x 5d (P.C.)',
    interpretedName: 'Amoxicillin + Potassium Clavulanate',
    tradeBrand: 'Augmentin 625 Duo',
    genericFormula: '500 mg + 125 mg Tablet · Oral',
    posologyDetail: 'Twice daily (1 - 0 - 1) · Strictly after meals (P.C.)',
    scheduleTiming: 'Morning (9:00 AM) & Night (9:00 PM)',
    duration: '5 days course',
    statusType: 'high_confidence',
    statusLabel: 'Ontology Grounded · Confirmed',
    evidenceCitation: 'CDSCO Schedule H1 · US NLM RxNorm #213169',
    isAmbiguous: false,
    patientGuidance:
      'Take one tablet in the morning and one at night strictly after food. Complete the full 5-day course as prescribed to prevent antimicrobial resistance.',
    box: {
      left: 7.0,
      top: 32.0,
      width: 81.0,
      height: 9.8,
      scanTop: 36.9,
    },
  },
  {
    id: 'line-2',
    lineNum: 2,
    label: 'Line 02',
    shortTitle: 'Pan 40mg',
    doctorInkText: 'Cap. Pan 40mg 1 - 0 - 0 x 5d (A.C. 30m before breakfast)',
    interpretedName: 'Pantoprazole Sodium',
    tradeBrand: 'Pan 40',
    genericFormula: '40 mg Gastro-Resistant Capsule · Oral',
    posologyDetail: 'Once daily (1 - 0 - 0) · 30m before breakfast (A.C.)',
    scheduleTiming: 'Morning (8:30 AM before breakfast)',
    duration: '5 days course',
    statusType: 'needs_verification',
    statusLabel: 'Verification Recommended · Flagged',
    evidenceCitation: 'Selective Abstention · Pharmacist review required',
    isAmbiguous: true,
    abstentionReason:
      'Pre-meal timing (A.C. 30m before breakfast) is confirmed. Terminal shorthand frequency is flagged for routine pharmacist dispensing verification rather than autonomous confirmation.',
    patientGuidance:
      'Take one capsule once daily in the morning on an empty stomach, at least 30 minutes before breakfast. Swallow whole with water; do not crush or chew.',
    box: {
      left: 7.0,
      top: 42.5,
      width: 88.0,
      height: 9.8,
      scanTop: 47.4,
    },
  },
  {
    id: 'line-3',
    lineNum: 3,
    label: 'Line 03',
    shortTitle: 'Dolo 650mg',
    doctorInkText: 'Tab. Dolo 650mg 1 - 0 - 1 S.O.S. (if fever > 100°F)',
    interpretedName: 'Paracetamol (Acetaminophen)',
    tradeBrand: 'Dolo 650',
    genericFormula: '650 mg Fast-Release Tablet · Oral',
    posologyDetail: 'As needed (SOS) for fever or body ache · Min 6h gap',
    scheduleTiming: 'Up to 3 times daily as needed (TDS / SOS)',
    duration: 'As needed (max 3 days)',
    statusType: 'high_confidence',
    statusLabel: 'Ontology Grounded · Confirmed',
    evidenceCitation: 'CDSCO Approved · US NLM RxNorm #161',
    isAmbiguous: false,
    patientGuidance:
      'Take only when fever (above 100°F) or body ache occurs. Maintain at least 6 hours between tablets. Do not exceed 4 tablets in 24 hours.',
    box: {
      left: 6.5,
      top: 53.0,
      width: 81.0,
      height: 9.8,
      scanTop: 57.9,
    },
  },
  {
    id: 'line-4',
    lineNum: 4,
    label: 'Line 04',
    shortTitle: 'Cetcip 10mg',
    doctorInkText: 'Tab. Cetcip 10mg 0 - 0 - 1 (H.S. at bedtime)',
    interpretedName: 'Cetirizine Hydrochloride',
    tradeBrand: 'Cetcip 10',
    genericFormula: '10 mg Film-Coated Tablet · Oral',
    posologyDetail: 'Once at night before sleep (0 - 0 - 1) · Bedtime (H.S.)',
    scheduleTiming: 'Night (10:00 PM / Bedtime)',
    duration: '5 days course',
    statusType: 'high_confidence',
    statusLabel: 'Ontology Grounded · Confirmed',
    evidenceCitation: 'CDSCO Approved · US NLM RxNorm #20610',
    isAmbiguous: false,
    patientGuidance:
      'Take one tablet at night before sleeping. May cause mild drowsiness; avoid driving, cycling, or operating machinery after taking.',
    box: {
      left: 6.5,
      top: 63.5,
      width: 76.0,
      height: 9.8,
      scanTop: 68.4,
    },
  },
];

export const InteractivePrescriptionSection: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();
  const [activeLineIndex, setActiveLineIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const intervalRef = useRef<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const imgFrameRef = useRef<HTMLDivElement>(null);
  const rightCardRef = useRef<HTMLDivElement>(null);
  const [connectorCoords, setConnectorCoords] = useState<{
    startX: number;
    startY: number;
    endX: number;
    endY: number;
  } | null>(null);

  const activeLine = DEMO_PRESCRIPTION_LINES[activeLineIndex];

  // Auto-advance loop when playing
  useEffect(() => {
    if (!isPlaying) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    intervalRef.current = window.setInterval(() => {
      setActiveLineIndex((prev) => (prev + 1) % DEMO_PRESCRIPTION_LINES.length);
    }, 4500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying]);

  const selectLine = (index: number) => {
    setActiveLineIndex(index);
    setIsPlaying(false);
  };

  // Recompute connector coordinates dynamically
  const updateConnector = useCallback(() => {
    if (typeof window === 'undefined') return;
    if (window.innerWidth < 1024) {
      setConnectorCoords(null);
      return;
    }

    if (!containerRef.current || !imgFrameRef.current || !rightCardRef.current) {
      return;
    }

    const containerRect = containerRef.current.getBoundingClientRect();
    const imgRect = imgFrameRef.current.getBoundingClientRect();
    const rightRect = rightCardRef.current.getBoundingClientRect();

    const box = activeLine.box;
    // Right edge of the active bounding box on the image
    const startX = imgRect.left - containerRect.left + (imgRect.width * (box.left + box.width)) / 100;
    // Center vertical of the active bounding box on the image
    const startY = imgRect.top - containerRect.top + (imgRect.height * (box.top + box.height / 2)) / 100;

    // Connect to left edge of right card, vertically aligning near the "Interpreted Medication" title
    const targetAnchor = rightCardRef.current.querySelector('[data-connector-anchor="true"]') as HTMLElement | null;
    let endY = rightRect.top - containerRect.top + 160;
    if (targetAnchor) {
      const anchorRect = targetAnchor.getBoundingClientRect();
      endY = anchorRect.top - containerRect.top + anchorRect.height / 2;
    }
    const endX = rightRect.left - containerRect.left;

    setConnectorCoords({ startX, startY, endX, endY });
  }, [activeLine]);

  useEffect(() => {
    updateConnector();
    window.addEventListener('resize', updateConnector);
    return () => window.removeEventListener('resize', updateConnector);
  }, [updateConnector]);

  // Recalculate slightly after render to catch image paint
  useEffect(() => {
    const timer = setTimeout(updateConnector, 120);
    return () => clearTimeout(timer);
  }, [activeLineIndex, updateConnector]);

  const connectorPath = connectorCoords
    ? `M ${connectorCoords.startX} ${connectorCoords.startY} C ${
        connectorCoords.startX + (connectorCoords.endX - connectorCoords.startX) * 0.45
      } ${connectorCoords.startY}, ${
        connectorCoords.startX + (connectorCoords.endX - connectorCoords.startX) * 0.55
      } ${connectorCoords.endY}, ${connectorCoords.endX} ${connectorCoords.endY}`
    : '';

  return (
    <section id="demo" className="py-20 sm:py-28 bg-canvas border-b border-theme relative overflow-hidden">
      {/* Subtle ambient clinical glow */}
      <div
        className="absolute top-1/3 -left-20 w-[550px] h-[550px] rounded-full pointer-events-none opacity-30 dark:opacity-10 blur-3xl"
        style={{
          background: 'radial-gradient(circle, rgba(21, 94, 239, 0.2) 0%, rgba(234, 242, 255, 0.1) 70%, transparent 100%)',
        }}
        aria-hidden="true"
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Lead — Scroll Triggered Entrance */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.55, ease: 'easeOut' }}
          className="max-w-3xl mb-12 sm:mb-16 space-y-4"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EAF2FF] dark:bg-[#16263D] border border-[#B2DDFF] dark:border-[rgba(255,255,255,0.12)] text-xs font-semibold text-[#155EEF] dark:text-[#84CAFF]">
            <FileText className="w-3.5 h-3.5" />
            <span>INTERACTIVE CLINICAL DEMO</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-[2.85rem] font-extrabold tracking-tight text-theme-primary leading-[1.08]">
            From handwriting to understanding.
          </h2>

          <p className="text-base sm:text-lg lg:text-xl text-theme-secondary leading-[1.65]">
            Explore how prescription text becomes structured information, with unclear details kept visible for professional review. Click any medicine line to see its instant clinical interpretation.
          </p>
        </motion.div>

        {/* Interactive Workspace Grid with Dynamic SVG Connector */}
        <div ref={containerRef} className="relative grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Dynamic SVG Connector Line (Desktop Only) */}
          {connectorCoords && (
            <svg
              className="hidden lg:block absolute inset-0 w-full h-full pointer-events-none z-30"
              aria-hidden="true"
            >
              <defs>
                <linearGradient id="demoConnectorGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#155EEF" stopOpacity="0.95" />
                  <stop offset="100%" stopColor="#4B8BFF" stopOpacity="0.95" />
                </linearGradient>
                <filter id="demoGlow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="2.5" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Glowing under-stroke */}
              <path
                d={connectorPath}
                fill="none"
                stroke="#155EEF"
                strokeWidth="5"
                strokeOpacity="0.25"
                filter="url(#demoGlow)"
              />

              {/* Main dashed precision connector */}
              <path
                d={connectorPath}
                fill="none"
                stroke="url(#demoConnectorGrad)"
                strokeWidth="2.2"
                strokeDasharray="6 4"
              />

              {/* Start anchor node on image */}
              <circle
                cx={connectorCoords.startX}
                cy={connectorCoords.startY}
                r="4.5"
                fill="#155EEF"
                stroke="#FFFFFF"
                strokeWidth="1.8"
              />

              {/* End anchor node on interpretation card */}
              <circle
                cx={connectorCoords.endX}
                cy={connectorCoords.endY}
                r="4.5"
                fill="#4B8BFF"
                stroke="#FFFFFF"
                strokeWidth="1.8"
              />
            </svg>
          )}

          {/* ========================================================= */}
          {/* LEFT: Authentic Prescription Document with Interactive Overlay */}
          {/* ========================================================= */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="lg:col-span-6 glass-panel card-border-interactive rounded-3xl p-5 sm:p-7 shadow-sm space-y-5"
          >
            {/* Document Header Bar */}
            <div className="flex items-center justify-between pb-3.5 border-b border-theme">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#155EEF] animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-wider text-theme-primary">
                  Prescription Canvas &middot; Scan Review
                </span>
              </div>

              {/* Play / Pause Step Animation */}
              <button
                type="button"
                onClick={() => setIsPlaying(!isPlaying)}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-theme bg-surface-subtle hover:bg-surface text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all cursor-pointer shadow-2xs"
                aria-label={isPlaying ? 'Pause auto-demonstration' : 'Resume auto-demonstration'}
              >
                {isPlaying ? (
                  <>
                    <Pause className="w-3 h-3 text-[#155EEF]" />
                    <span>Pause Demo</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 text-[#155EEF]" />
                    <span>Auto Step</span>
                  </>
                )}
              </button>
            </div>

            {/* Document Canvas Frame (Authentic Image with Overlay Coordinates) */}
            <div
              ref={imgFrameRef}
              className="relative rounded-2xl overflow-hidden box-dotted-frame bg-white shadow-inner select-none transition-all p-1.5"
            >
              {/* The Unhighlighted Source Fictional Prescription Image */}
              <img
                src="/samples/handwritten-clinic-pad.png"
                alt="Handwritten Clinic Prescription Pad demonstration written in doctor cursive ink"
                className="w-full h-auto block object-contain"
                loading="eager"
                onLoad={updateConnector}
              />

              {/* Coordinate Overlay Layer for 4 Medicine Entries */}
              <div className="absolute inset-0 pointer-events-none" aria-label="Interactive prescription medicine lines">
                {DEMO_PRESCRIPTION_LINES.map((line, idx) => {
                  const isSelected = activeLineIndex === idx;
                  const box = line.box;

                  return (
                    <div
                      key={line.id}
                      role="button"
                      tabIndex={0}
                      aria-pressed={isSelected}
                      aria-label={`Select ${line.shortTitle} (${line.label})`}
                      onClick={() => selectLine(idx)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          selectLine(idx);
                        }
                      }}
                      style={{
                        left: `${box.left}%`,
                        top: `${box.top}%`,
                        width: `${box.width}%`,
                        height: `${box.height}%`,
                      }}
                      className={`absolute rounded-xl transition-all cursor-pointer pointer-events-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#155EEF] focus-visible:ring-offset-2 ${
                        isSelected
                          ? line.isAmbiguous
                            ? 'bg-amber-500/15 border-2 border-amber-500 shadow-[0_0_14px_rgba(245,158,11,0.35)] ring-1 ring-amber-500/30'
                            : 'bg-[#155EEF]/14 border-2 border-[#155EEF] shadow-[0_0_16px_rgba(21,94,239,0.35)] ring-1 ring-[#155EEF]/30'
                          : 'border border-transparent hover:border-[#155EEF]/40 hover:bg-[#155EEF]/6'
                      }`}
                    >
                      {/* Interactive Focus Badge Tag on Active Box */}
                      {isSelected && (
                        <span
                          className={`absolute -top-2.5 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white shadow-xs ${
                            line.isAmbiguous ? 'bg-amber-600' : 'bg-[#155EEF]'
                          }`}
                        >
                          {line.label} &middot; {line.isAmbiguous ? 'Flagged' : 'Active'}
                        </span>
                      )}
                    </div>
                  );
                })}

                {/* Simulated Optical Blue Scan Sweep Line */}
                <motion.div
                  className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#155EEF] dark:via-[#4B8BFF] to-transparent pointer-events-none shadow-[0_0_10px_rgba(21,94,239,0.9)]"
                  style={{ top: `${activeLine.box.scanTop}%` }}
                  transition={{ duration: 0.35, ease: 'easeOut' }}
                />
              </div>

              {/* Fictional Disclaimer Footer Banner */}
              <div className="absolute bottom-0 left-0 right-0 py-1.5 px-3 bg-white/90 dark:bg-[#101E30]/90 backdrop-blur-xs border-t border-slate-200 dark:border-white/10 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400">
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  Fictional Demonstration Document
                </span>
                <span>Original Document Remains Primary Authority</span>
              </div>
            </div>

            {/* Line Selection Buttons with Direct Sync */}
            <div className="flex flex-wrap gap-2 pt-1" role="tablist" aria-label="Prescription medicine lines">
              {DEMO_PRESCRIPTION_LINES.map((line, idx) => {
                const isSelected = activeLineIndex === idx;
                return (
                  <button
                    key={line.id}
                    type="button"
                    role="tab"
                    id={`btn-${line.id}`}
                    aria-selected={isSelected}
                    onClick={() => selectLine(idx)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#155EEF] ${
                      isSelected
                        ? line.isAmbiguous
                          ? 'bg-amber-600 text-white shadow-xs ring-1 ring-amber-700/50'
                          : 'bg-[#155EEF] text-white shadow-xs ring-1 ring-[#155EEF]/50'
                        : 'bg-surface-subtle border border-theme hover:border-theme-hover text-theme-secondary hover:text-theme-primary'
                    }`}
                  >
                    <span className="font-mono text-[11px] opacity-80">{line.label}</span>
                    <span>{line.shortTitle}</span>
                  </button>
                );
              })}
            </div>
          </motion.div>

          {/* ========================================================= */}
          {/* RIGHT: Structured Interpretation Panel (Staggered Scroll)  */}
          {/* ========================================================= */}
          <motion.div
            ref={rightCardRef}
            initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.6, delay: shouldReduceMotion ? 0 : 0.1, ease: 'easeOut' }}
            className="lg:col-span-6 glass-panel card-border-interactive rounded-3xl p-5 sm:p-7 shadow-sm space-y-6"
          >
            {/* Header: Line Status Badge */}
            <div className="flex items-center justify-between pb-3.5 border-b border-theme">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-theme-primary">
                  {activeLine.label} &middot; Clinical Interpretation
                </span>
              </div>

              <div
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
                  activeLine.isAmbiguous
                    ? 'bg-amber-500/10 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-700/60'
                    : 'bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-700/60'
                }`}
              >
                {activeLine.isAmbiguous ? (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Selective Abstention Active</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Ontology Grounded</span>
                  </>
                )}
              </div>
            </div>

            {/* Doctor Ink Transcription (Exact Match to Prompt) */}
            <div data-connector-anchor="true" className="space-y-1.5">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-theme-muted">
                Original Doctor Handwriting Transcription
              </div>
              <div className="p-3.5 rounded-xl box-dotted-pattern font-mono text-xs sm:text-sm text-theme-primary">
                {activeLine.doctorInkText}
              </div>
            </div>

            {/* Resolved Entity Details */}
            <div className="space-y-3.5">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-theme-muted">
                Interpreted Medication &amp; Formulation
              </div>

              <div className="p-4 rounded-2xl box-dotted-pattern space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1 sm:gap-2">
                  <div className="flex items-center gap-2">
                    <Pill className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF] shrink-0" />
                    <h3 className="text-lg sm:text-xl font-bold text-theme-primary">
                      {activeLine.tradeBrand}
                    </h3>
                  </div>
                  <span className="text-xs font-medium text-theme-muted">
                    {activeLine.genericFormula}
                  </span>
                </div>

                <div className="text-xs text-theme-secondary font-medium">
                  Generic Entity: <strong className="text-theme-primary">{activeLine.interpretedName}</strong>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs pt-2.5 border-t border-theme/60 text-theme-secondary">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-theme-muted shrink-0" />
                    <span>
                      <strong className="text-theme-primary">Posology:</strong> {activeLine.posologyDetail}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-theme-muted shrink-0" />
                    <span>
                      <strong className="text-theme-primary">Duration:</strong> {activeLine.duration}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Selective Abstention Caution Banner (for Ambiguous Line) */}
            {activeLine.isAmbiguous && activeLine.abstentionReason && (
              <div className="p-4 rounded-2xl bg-amber-50/70 dark:bg-amber-950/20 border-2 border-dashed border-amber-300 dark:border-amber-700/60 text-xs text-amber-900 dark:text-amber-200 space-y-1.5">
                <div className="font-bold flex items-center gap-1.5 text-amber-800 dark:text-amber-300">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Uncertainty Safeguard: Abstaining from Autonomous Decision</span>
                </div>
                <p className="leading-relaxed">
                  {activeLine.abstentionReason}
                </p>
              </div>
            )}

            {/* Plain-Language Patient Explanation */}
            <div className="space-y-1.5">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-theme-muted">
                Patient-Friendly Guidance
              </div>
              <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed p-3.5 rounded-xl box-dotted-pattern">
                {activeLine.patientGuidance}
              </p>
            </div>

            {/* Grounding Citation Footer */}
            <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-theme-muted border-t border-theme">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
                <span>{activeLine.evidenceCitation}</span>
              </div>
              <span className="text-[10px]">Fictional Reference Demo</span>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
