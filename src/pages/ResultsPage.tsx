import React, { useState } from 'react';
import {
  ResultsDemoStateId,
  BoundingBox,
  PrescriptionAnalysisResult,
} from '../types/prescription.types';
import { UploadedPrescriptionFile } from '../types/navigation.types';
import { RESULTS_DEMO_STATES } from '../data/resultsDemoStates';
import { OriginalScriptViewer } from '../components/results/OriginalScriptViewer';
import { ExtractionFieldCard } from '../components/results/ExtractionFieldCard';
import { MedicineValidationSection } from '../components/results/MedicineValidationSection';
import { LasaSafetyCard } from '../components/results/LasaSafetyCard';
import { MultilingualExplanationCard } from '../components/results/MultilingualExplanationCard';
import { DemoStateSwitcher } from '../components/results/DemoStateSwitcher';
import { Badge } from '../components/ui/Badge';
import {
  ArrowLeft,
  Printer,
  ShieldCheck,
  AlertCircle,
  ShieldAlert,
  AlertTriangle,
  FileSpreadsheet,
  Stethoscope,
  Info,
  RotateCcw,
  UploadCloud,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';

export interface ResultsPageProps {
  initialResult?: PrescriptionAnalysisResult | null;
  uploadedData?: UploadedPrescriptionFile | null;
  onBackToHome: () => void;
  onBackToUpload: () => void;
  onRerunPipeline?: () => void;
}

export const ResultsPage: React.FC<ResultsPageProps> = ({
  uploadedData,
  onBackToHome,
  onBackToUpload,
  onRerunPipeline,
}) => {
  // Initialize state based on uploaded sample if available or default to state-confident
  const determineInitialState = (): ResultsDemoStateId => {
    if (uploadedData?.sampleId === 'rx-sample-2') return 'state-lasa';
    if (uploadedData?.sampleId === 'rx-sample-3') return 'state-flagged';
    return 'state-confident';
  };

  const [activeStateId, setActiveStateId] = useState<ResultsDemoStateId>(determineInitialState);
  const [hoveredBox, setHoveredBox] = useState<BoundingBox | null>(null);
  const [hoveredLabel, setHoveredLabel] = useState<string | undefined>(undefined);

  const currentState = RESULTS_DEMO_STATES[activeStateId] || RESULTS_DEMO_STATES['state-confident'];

  const handlePrint = () => {
    window.print();
  };

  const getStatusBadge = () => {
    switch (currentState.overallStatus) {
      case 'VERIFIED':
        return (
          <Badge variant="emerald" size="sm">
            <ShieldCheck className="w-3.5 h-3.5 inline mr-1 text-emerald-400" />
            All Fields Grounded &amp; Verified
          </Badge>
        );
      case 'NEEDS_VERIFICATION':
        return (
          <Badge variant="amber" size="sm">
            <AlertCircle className="w-3.5 h-3.5 inline mr-1 text-amber-400" />
            1 Field Requires Verification
          </Badge>
        );
      case 'SAFETY_ALERT':
        return (
          <Badge variant="coral" size="sm">
            <AlertTriangle className="w-3.5 h-3.5 inline mr-1 text-red-400" />
            LASA Safety Conflict Flagged
          </Badge>
        );
      case 'SELECTIVE_ABSTAIN':
        return (
          <Badge variant="coral" size="sm">
            <ShieldAlert className="w-3.5 h-3.5 inline mr-1 text-red-400" />
            Selective Abstention Protocol Active
          </Badge>
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#07090E] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/25 selection:text-cyan-200">
      {/* Top Clinical Workstation Header */}
      <header className="sticky top-0 z-40 bg-[#0A0D15]/95 backdrop-blur-xl border-b border-white/[0.08] py-3 px-4 sm:px-8 print:hidden">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToUpload}
              className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 hover:border-white/20 text-xs font-mono text-slate-300 hover:text-white transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Intake Console</span>
            </button>

            <span className="text-slate-700 hidden sm:inline">|</span>

            <div className="hidden sm:flex items-center gap-2">
              <span className="font-extrabold text-sm tracking-tight text-white font-mono">
                AURA<span className="text-cyan-400">-Rx</span>
              </span>
              <span className="text-xs text-slate-400 font-mono">
                / Clinical Diagnostic Findings
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {getStatusBadge()}

            {onRerunPipeline && (
              <button
                onClick={onRerunPipeline}
                className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 hover:border-white/20 text-xs font-mono text-cyan-300 hover:text-white transition-all hidden md:flex items-center gap-1.5 cursor-pointer"
                title="Rerun Animated Pipeline"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Rerun Pipeline</span>
              </button>
            )}

            <button
              onClick={handlePrint}
              aria-label="Print Clinical Monograph"
              className="px-3 py-1.5 rounded-lg bg-black/40 border border-white/10 hover:border-white/20 text-xs font-mono text-slate-300 hover:text-white transition-all hidden sm:flex items-center gap-1.5 cursor-pointer"
              title="Print Clinical Monograph"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print Summary</span>
            </button>

            <button
              onClick={onBackToHome}
              className="px-3 py-1.5 rounded-lg bg-cyan-950/60 border border-cyan-500/30 hover:border-cyan-400 text-xs font-mono text-cyan-300 hover:text-white transition-all cursor-pointer"
            >
              Overview
            </button>
          </div>
        </div>
      </header>

      {/* Main Results Body */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Scenario Demo Switcher Bar */}
        <DemoStateSwitcher
          activeStateId={activeStateId}
          onSelectState={(id) => {
            setActiveStateId(id);
            setHoveredBox(null);
            setHoveredLabel(undefined);
          }}
        />

        {/* Executive Header & Prescriber Metadata */}
        <div className="p-5 rounded-xl bg-[#090D18] border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-mono">
              <Stethoscope className="w-3.5 h-3.5 text-cyan-400" />
              <span>Accession: {currentState.accessionId}</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-300">{currentState.difficultyTag}</span>
            </div>

            <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight font-sans">
              {currentState.scenarioTitle}
            </h1>

            <p className="text-xs text-slate-400 font-sans">{currentState.scenarioSubtitle}</p>
          </div>

          {/* Patient Profile Readout */}
          <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1 text-xs font-mono w-full md:w-auto">
            <div>
              <span className="text-slate-500 mr-2">PATIENT:</span>
              <strong className="text-slate-200">{currentState.patientName}</strong>{' '}
              <span className="text-slate-400">({currentState.patientAgeGender})</span>
            </div>
            <div>
              <span className="text-slate-500 mr-2">PRESCRIBER:</span>
              <span className="text-cyan-300">{currentState.doctorName}</span>
            </div>
          </div>
        </div>

        {/* Statutory Assistive Tool Disclaimer Banner (Approved Phrasing) */}
        <div className="p-3.5 rounded-xl bg-[#080B14] border border-white/[0.08] flex items-start gap-3 text-xs text-slate-300 font-sans leading-relaxed">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-white font-mono uppercase text-[11px] block">
              Assistive Tool Statutory Notice:
            </strong>
            This system is an assistive prescription-understanding tool. It does not diagnose
            conditions, prescribe medicines, or modify prescribed dosages. Uncertain information
            must be verified against the original prescription and with an appropriate healthcare
            professional.
          </div>
        </div>

        {/* Responsive Layout Composition:
            Desktop: 2-column layout (5 cols left: Original Script Viewer; 7 cols right: Interpretation & Findings)
            Mobile: Natural sequential order (Original Script -> Interpretation -> Warnings -> Evidence -> Multilingual)
        */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Interactive Original Script Viewer (5 cols) */}
          <div className="lg:col-span-5 space-y-4 lg:sticky lg:top-20">
            <OriginalScriptViewer
              scriptKey={currentState.rawScriptKey}
              previewUrl={uploadedData?.previewUrl}
              activeBoundingBox={hoveredBox}
              highlightLabel={hoveredLabel}
              accessionId={currentState.accessionId}
            />
          </div>

          {/* Right Column: Structured Interpretation, Safety & Evidence (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* 1. Extraction Fields Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between px-1 text-xs font-mono">
                <span className="text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
                  Interpreted Prescription Entities ({currentState.fields.length} Fields)
                </span>
                <span className="text-[10px] text-slate-500">
                  HOVER TO LOCATE STROKE ON SCRIPT
                </span>
              </div>

              <div className="space-y-3">
                {currentState.fields.map((field) => (
                  <ExtractionFieldCard
                    key={field.fieldKey}
                    field={field}
                    isActive={hoveredLabel === field.fieldName}
                    onHover={(box, label) => {
                      setHoveredBox(box || null);
                      setHoveredLabel(label);
                    }}
                    onLeave={() => {
                      setHoveredBox(null);
                      setHoveredLabel(undefined);
                    }}
                  />
                ))}
              </div>
            </div>

            {/* 2. LASA Safety Alert (Conditionally Rendered) */}
            {currentState.lasaDetail && currentState.lasaDetail.hasWarning && (
              <LasaSafetyCard lasaDetail={currentState.lasaDetail} />
            )}

            {/* 3. Pharmacopeial Validation & Evidence */}
            <MedicineValidationSection evidence={currentState.validationEvidence} />

            {/* 4. Multilingual Patient Explanation */}
            <MultilingualExplanationCard multilingual={currentState.multilingual} />
          </div>
        </div>

        {/* Clinical Verification & Actionable Next Steps */}
        <div className="pt-4 border-t border-white/[0.08] space-y-4">
          {/* Verification Protocol Checklist */}
          <div className="p-4 sm:p-5 rounded-xl bg-[#0B0F1A] border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono text-cyan-300 font-bold uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Mandatory Dispensing Verification Checklist (Pharmacy Act Protocol)</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500">HUMAN-IN-THE-LOOP</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-sans">
              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-slate-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>1. Script Validation</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Confirm physical doctor signature, date, and state registration number.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-slate-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>2. Posology Concordance</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Verify dosage frequency and meal timing against patient profile.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-slate-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>3. LASA &amp; Allergy Review</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Review Look-Alike Sound-Alike collision risk and cross-allergies.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-slate-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>4. Vernacular Counseling</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Counsel patient or caregiver in their preferred language (EN/HI/MR).
                </p>
              </div>
            </div>
          </div>

          {/* Actionable Next Steps Bar */}
          <div className="p-4 sm:p-5 rounded-xl bg-[#090D17] border border-cyan-500/20 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="space-y-0.5 text-center sm:text-left">
              <h4 className="text-sm font-bold text-white font-sans">
                Next Clinical Workflow Step
              </h4>
              <p className="text-xs text-slate-400 font-sans">
                Scan another physician prescription script or return to the overview dashboard.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
              <button
                onClick={onBackToUpload}
                className="flex-1 sm:flex-none px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs font-mono transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
              >
                <UploadCloud className="w-4 h-4 text-slate-950" />
                <span>Upload New Script</span>
              </button>

              {onRerunPipeline && (
                <button
                  onClick={onRerunPipeline}
                  className="flex-1 sm:flex-none px-3.5 py-2 rounded-lg bg-slate-900 border border-white/10 hover:border-white/20 text-xs font-mono text-cyan-300 hover:text-white transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Rerun Pipeline</span>
                </button>
              )}

              <button
                onClick={onBackToHome}
                className="flex-1 sm:flex-none px-3.5 py-2 rounded-lg bg-black/40 border border-white/10 hover:border-white/20 text-xs font-mono text-slate-400 hover:text-white transition-all cursor-pointer flex items-center justify-center gap-1.5"
              >
                <span>Academic Overview</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
