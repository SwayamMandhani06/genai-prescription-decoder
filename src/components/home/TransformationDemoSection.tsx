import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import {
  CheckCircle2,
  AlertTriangle,
  FileX2,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  CornerDownRight,
  Receipt,
  HelpCircle,
} from 'lucide-react';

export type DemoSampleType = 'standard' | 'ambiguous' | 'unrelated';

export interface DemoSampleItem {
  id: DemoSampleType;
  tabLabel: string;
  badgeLabel: string;
  badgeVariant: 'verified' | 'amber' | 'danger';
  headline: string;
  subheadline: string;
  documentType: 'prescription' | 'unrelated';
  // Prescription fields
  doctorInk?: string;
  svgPath?: string;
  brandName?: string;
  genericName?: string;
  dosage?: string;
  schedule?: string;
  duration?: string;
  formularyRef?: string;
  patientGuidance?: string;
  uncertaintyReason?: string;
  mandatedAction?: string;
  // Rejection fields for unrelated document
  rejectionCode?: string;
  rejectionTitle?: string;
  rejectionDetail?: string;
  safetyPolicy?: string;
}

export const TransformationDemoSection: React.FC = () => {
  const [selectedSample, setSelectedSample] = useState<DemoSampleType>('standard');
  const [isSwitching, setIsSwitching] = useState<boolean>(false);

  const canvasData = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];

  const samples: Record<DemoSampleType, DemoSampleItem> = {
    standard: {
      id: 'standard',
      tabLabel: '1. Standard Prescription',
      badgeLabel: 'Clear Handwriting · Grounded',
      badgeVariant: 'verified',
      headline: 'Standard Fictional Prescription',
      subheadline: 'Legible outpatient handwriting with grounded CDSCO & RxNorm ontology',
      documentType: 'prescription',
      doctorInk: 'Tab. Augmentin 625 Duo  1-0-1 x 5d  (P.C.)',
      svgPath: canvasData.strokes[0].svgPath,
      brandName: 'Augmentin 625 Duo Tablet',
      genericName: 'Amoxicillin (500mg) + Clavulanic Acid (125mg)',
      dosage: '625 mg',
      schedule: 'Twice daily (1-0-1: Morning & Night) · After meals (P.C.)',
      duration: '5 days course',
      formularyRef: 'CDSCO Approved · NLM RxNorm #213169',
      patientGuidance:
        'Complete the full 5-day antibacterial course as prescribed. Take strictly after meals to ensure optimal therapeutic absorption.',
    },
    ambiguous: {
      id: 'ambiguous',
      tabLabel: '2. Ambiguous Prescription',
      badgeLabel: 'Selective Abstention Active',
      badgeVariant: 'amber',
      headline: 'Ambiguous Cursive Prescription',
      subheadline: 'Morphological stroke ambiguity triggering calibrated safety abstention',
      documentType: 'prescription',
      doctorInk: 'Cap. Pan 40mg  1-0-0 x 5d  (A.C. 30m before breakfast)',
      svgPath: canvasData.strokes[1].svgPath,
      brandName: 'Pan 40 Gastro-Resistant Tablet',
      genericName: 'Pantoprazole Sodium (40mg)',
      dosage: '40 mg',
      schedule: 'Candidate: Once daily (OD) · 30m before breakfast (A.C.)',
      duration: '5 days course',
      formularyRef: 'CDSCO Approved · RxNorm #284635 (Human Verification Required)',
      uncertaintyReason:
        'Terminal cursive stroke is morphologically ambiguous between OD and BD. Automated confirmation is withheld.',
      mandatedAction:
        'Mandated Pharmacist Verification: Physical inspection of doctor note required before dispensing.',
      patientGuidance:
        'Take with water 30 minutes before breakfast. Do not self-increase frequency if dosage loop is unconfirmed by your pharmacist.',
    },
    unrelated: {
      id: 'unrelated',
      tabLabel: '3. Unrelated Image',
      badgeLabel: 'Document Rejection Active',
      badgeVariant: 'danger',
      headline: 'Non-Prescription Document Rejection',
      subheadline: 'Optical triage identifies non-medical input and halts analysis with zero hallucinations',
      documentType: 'unrelated',
      rejectionCode: 'DOCUMENT_LEVEL_ABSTENTION_422',
      rejectionTitle: 'Non-Prescription Document Detected',
      rejectionDetail:
        'The submitted image lacks clinical Rx symbology, prescriber credentials, patient demographic headers, and valid medication posology structure. Optical triage flagged retail invoice headers.',
      safetyPolicy:
        'Clinical Safety Guarantee: DawaAI refuses to invent plausible-sounding medicines for non-medical images. The system halts inference and issues a clear abstention notice.',
    },
  };

  const handleSelectSample = (sampleKey: DemoSampleType) => {
    if (sampleKey === selectedSample) return;
    setIsSwitching(true);
    setTimeout(() => {
      setSelectedSample(sampleKey);
      setIsSwitching(false);
    }, 150);
  };

  const active = samples[selectedSample];

  return (
    <section id="transformation" className="py-20 sm:py-28 bg-[#F7FAFD] dark:bg-[#0A1628] border-b border-theme relative overflow-hidden">
      {/* Background Soft Glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] pointer-events-none opacity-25 dark:opacity-10 blur-3xl"
        style={{
          background: 'radial-gradient(circle, rgba(21, 94, 239, 0.15) 0%, rgba(234, 242, 255, 0.1) 70%, transparent 100%)',
        }}
        aria-hidden="true"
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="max-w-3xl mb-10 sm:mb-14 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EAF2FF] dark:bg-[#163657] border border-[#B2DDFF] dark:border-[#1E446E] text-xs font-semibold text-[#155EEF] dark:text-[#84CAFF]">
            <span>Interactive Verification Demo</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-[2.65rem] font-bold tracking-tight text-[#102A43] dark:text-[#F7FAFD] leading-[1.08]">
            See what changes — and when DawaAI abstains.
          </h2>
          <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
            Test the pipeline across clear handwriting, ambiguous cursive script, and non-prescription documents to observe genuine validation and safe abstention in real time.
          </p>

          {/* Sample Selectors (Interactive Tabs) */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 pt-3">
            {(Object.keys(samples) as DemoSampleType[]).map((key) => {
              const item = samples[key];
              const isSelected = selectedSample === key;

              return (
                <button
                  key={key}
                  onClick={() => handleSelectSample(key)}
                  className={`px-4 sm:px-5 py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all duration-200 cursor-pointer flex items-center gap-2 shadow-xs hover:-translate-y-0.5 active:translate-y-0 ${
                    isSelected
                      ? 'bg-gradient-to-r from-[#155EEF] to-[#2E90FA] text-white shadow-sm'
                      : 'bg-surface hover:bg-surface-subtle border border-theme text-theme-secondary hover:text-theme-primary'
                  }`}
                  aria-pressed={isSelected}
                >
                  <span>{item.tabLabel}</span>
                  {item.badgeVariant === 'amber' && (
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                  )}
                  {item.badgeVariant === 'danger' && (
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                  )}
                  {item.badgeVariant === 'verified' && (
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Demonstration Watermark */}
          <div className="text-[11px] text-theme-muted pt-1 flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
            <span>Fictional ground truth demonstration data. Unrelated images trigger genuine rejection logic.</span>
          </div>
        </div>

        {/* Side-by-Side Synchronized Transformation Stage */}
        <AnimatePresence mode="wait">
          <motion.div
            key={active.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className={`grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8 items-stretch transition-all duration-150 ${
              isSwitching ? 'opacity-60 scale-[0.99]' : 'opacity-100 scale-100'
            }`}
          >
            {/* ------------------------------------------------------------- */}
            {/* LEFT PANE: Input Document Preview                              */}
            {/* ------------------------------------------------------------- */}
            <div className="lg:col-span-5 p-6 sm:p-8 rounded-3xl bg-surface border border-theme shadow-md flex flex-col justify-between space-y-6">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#155EEF] dark:text-[#4B8BFF] uppercase tracking-wider text-[11px]">
                    Input Document
                  </span>
                  <span className="text-[11px] font-mono text-theme-muted">
                    {active.documentType === 'prescription' ? 'Clinical Document Slip' : 'Non-Clinical Image'}
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-[#102A43] dark:text-[#F7FAFD] tracking-tight">
                  {active.headline}
                </h3>
                <p className="text-xs sm:text-sm text-theme-secondary">
                  {active.subheadline}
                </p>
              </div>

              {/* Document Rendering / Stroke Area */}
              {active.documentType === 'prescription' ? (
                <div className="p-5 rounded-2xl prescription-paper border border-[#CBD5E1] dark:border-white/10 space-y-3 shadow-paper">
                  <div className="flex items-center justify-between border-b border-slate-300 pb-2 text-[11px] text-slate-700 font-mono">
                    <span className="font-bold text-[#102A43]">EXAMPLE CLINICAL PRACTICE</span>
                    <span>Outpatient Slip</span>
                  </div>

                  <div className="py-2">
                    <div className="text-slate-900 font-serif italic text-2xl font-black mb-1 select-none">
                      ℞
                    </div>
                    <svg
                      viewBox="0 0 650 35"
                      className="w-full h-9 overflow-visible"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d={active.svgPath}
                        fill="none"
                        stroke={active.badgeVariant === 'amber' ? '#92400E' : '#155EEF'}
                        strokeWidth="3.2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>

                  <div className="text-[10px] text-slate-600 font-mono border-t border-slate-200 pt-1.5 flex justify-between">
                    <span>{active.doctorInk}</span>
                    <span className="font-semibold text-slate-800">Prescriber Verified</span>
                  </div>
                </div>
              ) : (
                /* Unrelated Image / Receipt Display */
                <div className="p-6 rounded-2xl bg-slate-100 dark:bg-slate-900/60 border border-slate-300 dark:border-slate-800 space-y-3 text-slate-700 dark:text-slate-300">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200">
                    <Receipt className="w-4 h-4 text-slate-500" />
                    <span>Non-Medical Image: Supermarket Grocery Receipt</span>
                  </div>

                  <div className="p-4 rounded-xl bg-white dark:bg-slate-950 border border-dashed border-slate-300 dark:border-slate-700 text-xs font-mono space-y-1.5 opacity-80">
                    <div className="text-center font-bold text-slate-900 dark:text-slate-100 pb-1 border-b border-slate-200 dark:border-slate-800">
                      METRO SUPERMARKET #402
                    </div>
                    <div className="flex justify-between">
                      <span>Organic Milk 1L</span>
                      <span>$3.49</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Wheat Bread 400g</span>
                      <span>$2.29</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Almonds Roasted</span>
                      <span>$5.99</span>
                    </div>
                    <div className="flex justify-between font-bold pt-1 border-t border-slate-200 dark:border-slate-800">
                      <span>TOTAL USD</span>
                      <span>$11.77</span>
                    </div>
                  </div>

                  <p className="text-xs text-theme-muted leading-relaxed">
                    Evaluated against optical triage heuristics. No prescriber credentials or medical posology recognized.
                  </p>
                </div>
              )}

              <div className="text-xs text-theme-muted">
                {active.documentType === 'prescription'
                  ? 'Original doctor ink preserved as the authoritative medical legal record.'
                  : 'Document type screening operates before clinical entity mapping.'}
              </div>
            </div>

            {/* Central Bridge Indicator (Desktop Only) */}
            <div className="hidden lg:flex lg:col-span-1 items-center justify-center">
              <div className="w-10 h-10 rounded-full bg-surface border border-theme flex items-center justify-center text-theme-muted shadow-xs">
                <ArrowRight className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
              </div>
            </div>

            {/* ------------------------------------------------------------- */}
            {/* RIGHT PANE: Extracted Findings or Rejection Panel             */}
            {/* ------------------------------------------------------------- */}
            <div className="lg:col-span-6 p-6 sm:p-8 rounded-3xl bg-surface border border-theme shadow-md flex flex-col justify-between space-y-6">
              <div className="space-y-3">
                {/* Status Ribbon */}
                <div className="flex items-center justify-between text-xs sm:text-sm">
                  <span className="font-semibold text-[#155EEF] dark:text-[#4B8BFF] text-xs uppercase tracking-wider">
                    {active.documentType === 'prescription' ? 'Interpreted Findings' : 'Optical Triage Verdict'}
                  </span>

                  {active.badgeVariant === 'verified' && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800 dark:text-emerald-200 bg-emerald-50 dark:bg-emerald-950/60 px-3 py-1 rounded-full border border-emerald-300 dark:border-emerald-800">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                      <span>{active.badgeLabel}</span>
                    </span>
                  )}

                  {active.badgeVariant === 'amber' && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/60 px-3 py-1 rounded-full border border-amber-300 dark:border-amber-800">
                      <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                      <span>{active.badgeLabel}</span>
                    </span>
                  )}

                  {active.badgeVariant === 'danger' && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-rose-800 dark:text-rose-200 bg-rose-50 dark:bg-rose-950/60 px-3 py-1 rounded-full border border-rose-300 dark:border-rose-800">
                      <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                      <span>{active.badgeLabel}</span>
                    </span>
                  )}
                </div>

                {/* Prescription Findings or Rejection Display */}
                {active.documentType === 'prescription' ? (
                  <>
                    <div>
                      <h3 className="text-2xl sm:text-3xl font-extrabold text-[#102A43] dark:text-[#F7FAFD] tracking-tight">
                        {active.brandName}
                      </h3>
                      <p className="text-sm sm:text-base text-theme-secondary mt-1">
                        {active.genericName}
                      </p>
                    </div>

                    {/* Extracted Slots */}
                    <div className="space-y-3 py-3 border-y border-theme text-xs sm:text-sm">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-theme-muted block text-xs mb-0.5 font-medium">
                            Dosage Strength
                          </span>
                          <span className="text-base sm:text-lg font-bold text-theme-primary">
                            {active.dosage}
                          </span>
                        </div>
                        <div>
                          <span className="text-theme-muted block text-xs mb-0.5 font-medium">
                            Prescribed Duration
                          </span>
                          <span className="text-base sm:text-lg font-bold text-theme-primary">
                            {active.duration}
                          </span>
                        </div>
                      </div>
                      <div>
                        <span className="text-theme-muted block text-xs mb-0.5 font-medium">
                          Schedule &amp; Administration
                        </span>
                        <span className="text-sm sm:text-base font-bold text-theme-primary">
                          {active.schedule}
                        </span>
                      </div>
                    </div>

                    {/* Uncertainty Notice for Ambiguous Sample */}
                    {active.uncertaintyReason && (
                      <div className="p-3.5 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-1">
                        <div className="font-semibold flex items-center gap-1.5 text-[11px]">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          <span>Uncertainty Notice:</span>
                        </div>
                        <p className="leading-relaxed text-[11px]">
                          {active.uncertaintyReason}
                        </p>
                        <p className="font-semibold text-[11px] text-amber-950 dark:text-amber-100 pt-0.5">
                          {active.mandatedAction}
                        </p>
                      </div>
                    )}

                    {/* Patient Guidance & Formulary Reference */}
                    <div className="space-y-2 text-xs sm:text-sm">
                      <div className="text-theme-secondary leading-relaxed">
                        <strong className="text-theme-primary font-semibold">Patient Guidance: </strong>
                        {active.patientGuidance}
                      </div>

                      <div className="flex items-center gap-1.5 text-xs text-theme-muted pt-1">
                        <CornerDownRight className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
                        <span>{active.formularyRef}</span>
                      </div>
                    </div>
                  </>
                ) : (
                  /* Rejection Details for Unrelated Image */
                  <div className="space-y-4 py-2">
                    <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 space-y-2">
                      <div className="flex items-center gap-2 text-rose-800 dark:text-rose-200 font-bold text-sm">
                        <FileX2 className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" />
                        <span>{active.rejectionTitle}</span>
                      </div>
                      <p className="text-xs text-rose-900/80 dark:text-rose-200/90 leading-relaxed">
                        {active.rejectionDetail}
                      </p>
                      <div className="font-mono text-[10px] text-rose-700 dark:text-rose-300 pt-1">
                        Status Code: {active.rejectionCode} &middot; Zero Entities Inferred
                      </div>
                    </div>

                    <div className="p-4 rounded-2xl bg-surface-subtle border border-theme space-y-1.5 text-xs text-theme-secondary">
                      <div className="font-semibold text-theme-primary flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
                        <span>Clinical Safety Guarantee:</span>
                      </div>
                      <p className="leading-relaxed text-[11px]">
                        {active.safetyPolicy}
                      </p>
                    </div>

                    <div className="text-xs text-theme-muted italic">
                      Live analyzer returns standard HTTP 422 Unprocessable Entity on non-prescription uploads.
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
};
