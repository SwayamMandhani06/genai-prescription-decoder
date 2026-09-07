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
import { ThemeSwitcher } from '../components/layout/ThemeSwitcher';
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
            <ShieldCheck className="w-3.5 h-3.5 inline mr-1" />
            Verified &amp; Grounded
          </Badge>
        );
      case 'NEEDS_VERIFICATION':
        return (
          <Badge variant="amber" size="sm">
            <AlertCircle className="w-3.5 h-3.5 inline mr-1" />
            Requires Verification
          </Badge>
        );
      case 'SAFETY_ALERT':
        return (
          <Badge variant="coral" size="sm">
            <AlertTriangle className="w-3.5 h-3.5 inline mr-1" />
            LASA Ambiguity Detected
          </Badge>
        );
      case 'SELECTIVE_ABSTAIN':
        return (
          <Badge variant="coral" size="sm">
            <ShieldAlert className="w-3.5 h-3.5 inline mr-1" />
            Selective Abstention Active
          </Badge>
        );
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-theme-primary flex flex-col font-sans transition-colors">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-theme py-3 px-4 sm:px-8 print:hidden">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToUpload}
              className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface border border-theme text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Intake</span>
            </button>

            <span className="text-theme-muted hidden sm:inline">|</span>

            <div className="hidden sm:flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-theme-primary">
                AURA-Rx
              </span>
              <span className="text-xs text-theme-muted">
                / Prescription Findings
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {getStatusBadge()}

            {onRerunPipeline && (
              <button
                onClick={onRerunPipeline}
                className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface border border-theme text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all hidden md:flex items-center gap-1.5 cursor-pointer"
                title="Rerun Pipeline"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Rerun</span>
              </button>
            )}

            <button
              onClick={handlePrint}
              aria-label="Print Prescription Summary"
              className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface border border-theme text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all hidden sm:flex items-center gap-1.5 cursor-pointer"
              title="Print Prescription Summary"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print</span>
            </button>

            <ThemeSwitcher />

            <button
              onClick={onBackToHome}
              className="px-3 py-1.5 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-300 dark:border-teal-700 text-teal-800 dark:text-teal-300 text-xs font-medium transition-all cursor-pointer"
            >
              Overview
            </button>
          </div>
        </div>
      </header>

      {/* Main Results Body */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Scenario Switcher Bar */}
        <DemoStateSwitcher
          activeStateId={activeStateId}
          onSelectState={(id) => {
            setActiveStateId(id);
            setHoveredBox(null);
            setHoveredLabel(undefined);
          }}
        />

        {/* Prescription Metadata */}
        <div className="p-6 sm:p-7 rounded-3xl bg-surface border border-theme flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xs">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs sm:text-sm font-medium">
              <Stethoscope className="w-4 h-4" />
              <span>Accession: <strong className="font-mono">{currentState.accessionId}</strong></span>
              <span className="text-teal-400">|</span>
              <span>{currentState.difficultyTag}</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold text-theme-primary tracking-tight leading-[1.05]">
              {currentState.scenarioTitle}
            </h1>

            <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">{currentState.scenarioSubtitle}</p>
          </div>

          {/* Patient Profile Readout */}
          <div className="p-4 rounded-2xl bg-surface-subtle border border-theme space-y-1.5 text-sm sm:text-base w-full md:w-auto shrink-0">
            <div>
              <span className="text-theme-muted mr-2">Patient:</span>
              <strong className="text-theme-primary">{currentState.patientName}</strong>{' '}
              <span className="text-theme-secondary">({currentState.patientAgeGender})</span>
            </div>
            <div>
              <span className="text-theme-muted mr-2">Physician:</span>
              <span className="text-teal-700 dark:text-teal-300 font-medium">{currentState.doctorName}</span>
            </div>
          </div>
        </div>

        {/* Statutory Assistive Tool Disclaimer Banner */}
        <div className="p-4 sm:p-5 rounded-2xl bg-surface-subtle border border-theme flex items-start gap-3.5 text-sm sm:text-base text-theme-secondary leading-relaxed">
          <Info className="w-5 h-5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-theme-primary uppercase text-xs sm:text-sm font-semibold block mb-1">
              Assistive Prescription Interpretation Notice:
            </strong>
            This system is an assistive prescription-understanding tool. It does not diagnose
            conditions, prescribe medicines, or modify prescribed dosages. Uncertain information
            must be verified against the original prescription and with a licensed healthcare
            professional.
          </div>
        </div>

        {/* 2-Column Responsive Layout */}
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
            <div className="space-y-4">
              <div className="flex items-center justify-between px-1">
                <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                  <span>Interpreted Posology ({currentState.fields.length} Fields)</span>
                </h2>
                <span className="text-xs sm:text-sm text-theme-muted">
                  Hover to locate on script
                </span>
              </div>

              <div className="space-y-4">
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

        {/* Verification Checklist */}
        <div className="pt-6 border-t border-theme space-y-4">
          <div className="p-5 sm:p-6 rounded-2xl bg-surface border border-theme space-y-4 shadow-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">Verification Checklist</h2>
              </div>
              <span className="text-xs sm:text-sm text-theme-muted font-medium">Pharmacist Oversight</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-theme-primary text-sm sm:text-base">
                  <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                  <span>1. Script Validation</span>
                </div>
                <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed">
                  Confirm physician signature, date, and state registration number.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-theme-primary text-sm sm:text-base">
                  <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                  <span>2. Molecule &amp; Strength</span>
                </div>
                <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed">
                  Verify dosage strength matches patient age, weight, and renal profile.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-theme-primary text-sm sm:text-base">
                  <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                  <span>3. Drug Interaction</span>
                </div>
                <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed">
                  Screen against co-prescribed molecules for potential drug-drug interactions or contraindications.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-theme-primary text-sm sm:text-base">
                  <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                  <span>4. Patient Posology</span>
                </div>
                <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed">
                  Counsel patient or caregiver on meal timing in their preferred regional language.
                </p>
              </div>
            </div>
          </div>

          {/* Bottom Workflow Action Ribbon */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-surface-subtle border border-theme">
            <div className="flex items-center gap-3">
              <button
                onClick={onBackToUpload}
                className="px-4 py-2.5 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-sm font-semibold text-theme-primary transition-all flex items-center gap-2 cursor-pointer shadow-xs"
              >
                <UploadCloud className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span>Upload Another Prescription</span>
              </button>

              <button
                onClick={handlePrint}
                className="px-4 py-2.5 rounded-xl bg-surface hover:bg-surface-subtle border border-theme text-sm font-semibold text-theme-primary transition-all flex items-center gap-2 cursor-pointer shadow-xs"
              >
                <Printer className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span>Print Findings</span>
              </button>
            </div>

            <button
              onClick={onBackToHome}
              className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer shadow-xs"
            >
              <span>Return to Workspace Overview</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};
