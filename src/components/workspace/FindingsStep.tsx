import React, { useState } from 'react';
import {
  ResultsDemoStateId,
  BoundingBox,
  PrescriptionAnalysisResult,
  ExtractedFieldItem,
} from '../../types/prescription.types';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import { RESULTS_DEMO_STATES } from '../../data/resultsDemoStates';
import { OriginalScriptViewer } from '../results/OriginalScriptViewer';
import { DemoStateSwitcher } from '../results/DemoStateSwitcher';
import { LasaSafetyCard } from '../results/LasaSafetyCard';
import { MedicineValidationSection } from '../results/MedicineValidationSection';
import { MultilingualExplanationCard } from '../results/MultilingualExplanationCard';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  Printer,
  UploadCloud,
  CheckCircle2,
  FileSearch,
} from 'lucide-react';

export interface FindingsStepProps {
  uploadedData: UploadedPrescriptionFile | null;
  initialResult?: PrescriptionAnalysisResult | null;
  rotation?: number;
  onNewPrescription: () => void;
}

export const FindingsStep: React.FC<FindingsStepProps> = ({
  uploadedData,
  initialResult,
  onNewPrescription,
}) => {
  // Determine state based on initialResult or sample ID
  const determineInitialState = (): ResultsDemoStateId => {
    if (initialResult) {
      if (initialResult.overallStatus === 'ABSTAINED') return 'state-abstained';
      if (initialResult.overallStatus === 'SAFETY_ALERT') return 'state-lasa';
      if (initialResult.overallStatus === 'SELECTIVE_ABSTAIN') return 'state-flagged';
      if (initialResult.overallStatus === 'NEEDS_VERIFICATION') return 'state-uncertain';
      if (initialResult.overallStatus === 'VERIFIED') return 'state-confident';
    }
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

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Screen Header - Clean, obvious primary action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-theme">
        <div className="space-y-1.5">
          <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold tracking-tight text-theme-primary leading-[1.05]">
            Prescription Findings
          </h1>
          <p className="text-base sm:text-lg text-theme-secondary">
            Accession <span className="font-mono text-theme-primary font-semibold">{currentState.accessionId}</span> &middot; Patient: <span className="text-theme-primary font-medium">{currentState.patientName}</span> ({currentState.patientAgeGender})
          </p>
        </div>

        {/* Actions Toolbar */}
        <div className="flex items-center gap-3">
          <button
            onClick={handlePrint}
            className="text-sm font-semibold text-theme-secondary hover:text-theme-primary transition-colors flex items-center gap-2 cursor-pointer py-2.5 px-3.5"
          >
            <Printer className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>Print</span>
          </button>

          <button
            onClick={onNewPrescription}
            className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer shadow-sm"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Analyze another</span>
          </button>
        </div>
      </div>

      {/* Scenario Demo Switcher */}
      <DemoStateSwitcher
        activeStateId={activeStateId}
        onSelectState={(id) => {
          setActiveStateId(id);
          setHoveredBox(null);
          setHoveredLabel(undefined);
        }}
      />

      {/* Safety Reminder Note - Generous secondary typography */}
      <div className="flex items-start gap-3 text-sm sm:text-base text-theme-secondary leading-relaxed">
        <ShieldCheck className="w-5 h-5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
        <p>
          <strong className="text-theme-primary font-medium">Assistive tool note: </strong>
          The original physician&rsquo;s signed prescription is the permanent legal reference. Always confirm ambiguous handwriting with a pharmacist before dispensing.
        </p>
      </div>

      {/* Primary 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Original Prescription (5 cols Sticky on Desktop) */}
        <div className="lg:col-span-5 space-y-3.5 lg:sticky lg:top-20">
          <div className="flex items-center justify-between px-0.5">
            <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
              Original prescription
            </h2>
            <span className="text-theme-muted text-xs sm:text-sm">Hover fields to locate ink</span>
          </div>

          <OriginalScriptViewer
            scriptKey={currentState.rawScriptKey}
            previewUrl={uploadedData?.source === 'user_upload' ? uploadedData.previewUrl : undefined}
            activeBoundingBox={hoveredBox}
            highlightLabel={hoveredLabel}
            accessionId={currentState.accessionId}
          />
        </div>

        {/* Right: Interpreted Medication, Formulary Evidence & Explanation (7 cols) */}
        <div className="lg:col-span-7 space-y-8">
          {/* Explicit Clinical Abstention Notice (When Model Halts on Ambiguity/Illegibility) */}
          {(currentState.overallStatus === 'ABSTAINED' || currentState.id === 'state-abstained') && (
            <div className="rounded-2xl border-2 border-red-300 dark:border-red-800 bg-red-50/70 dark:bg-red-950/30 p-5 sm:p-6 space-y-4 shadow-sm animate-in fade-in">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 flex items-center justify-center shrink-0">
                  <ShieldAlert className="w-5 h-5 text-red-700 dark:text-red-400" />
                </div>
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-red-950 dark:text-red-100">
                    Clinical Engine Abstention Activated
                  </h3>
                  <p className="text-xs sm:text-sm text-red-800 dark:text-red-300">
                    Epistemic uncertainty exceeds diagnostic safety limits. Automated inference halted.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1 text-xs">
                <div className="p-3.5 rounded-xl bg-surface border border-theme space-y-1">
                  <strong className="text-theme-primary block font-semibold">WHAT happened:</strong>
                  <span className="text-theme-secondary">
                    {currentState.abstentionGuidance?.whatHappened ||
                      'The system halted decoding because handwriting is severely degraded.'}
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-surface border border-theme space-y-1">
                  <strong className="text-theme-primary block font-semibold">WHY it halted:</strong>
                  <span className="text-theme-secondary">
                    {currentState.abstentionGuidance?.why ||
                      'Excessive ink smear, paper crease, or ambiguous stroke ligatures.'}
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-surface border border-theme space-y-1">
                  <strong className="text-amber-900 dark:text-amber-300 block font-semibold">WHAT to do:</strong>
                  <span className="text-theme-secondary">
                    {currentState.abstentionGuidance?.whatToDo ||
                      'Pharmacist must inspect physical prescription paper. Do not dispense without prescriber confirmation.'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Look-Alike Sound-Alike (LASA) Collision Warning Card (When Active) */}
          {currentState.lasaDetail && currentState.lasaDetail.hasWarning && (
            <LasaSafetyCard lasaDetail={currentState.lasaDetail} />
          )}

          {/* Interpreted Medications List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between px-0.5">
              <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
                Interpreted medication ({currentState.fields.length} items)
              </h2>
              <span className="text-theme-muted text-xs sm:text-sm">Formulary matched</span>
            </div>

            <div className="space-y-4">
              {currentState.fields.map((field: ExtractedFieldItem) => {
                const isFieldHovered = hoveredLabel === field.fieldName;
                const isUncertain = field.status !== 'confident';
                const confidencePercent = Math.round(field.confidence * 100);

                return (
                  <div
                    key={field.fieldKey}
                    onMouseEnter={() => {
                      setHoveredBox(field.boundingBox || null);
                      setHoveredLabel(field.fieldName);
                    }}
                    onMouseLeave={() => {
                      setHoveredBox(null);
                      setHoveredLabel(undefined);
                    }}
                    className={`rounded-2xl p-5 border transition-all ${
                      isFieldHovered
                        ? 'border-teal-500 shadow-md bg-surface ring-1 ring-teal-500/20'
                        : field.status === 'abstained' || field.status === 'flagged'
                        ? 'border-red-200 dark:border-red-900/60 bg-surface shadow-xs'
                        : field.status === 'uncertain'
                        ? 'border-amber-200 dark:border-amber-900/60 bg-surface shadow-xs'
                        : 'border-theme bg-surface shadow-xs'
                    }`}
                  >
                    {/* Header: Field Name, Extracted Value, and Semantic Status */}
                    <div className="flex flex-wrap items-start justify-between gap-3 mb-2.5">
                      <div className="space-y-0.5">
                        <span className="text-xs text-theme-muted block font-medium">
                          {field.fieldName}
                        </span>
                        <h3 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
                          {field.value}
                        </h3>
                        {field.interpretedCandidate && (
                          <div className="text-xs sm:text-sm text-teal-700 dark:text-teal-400 font-medium">
                            Candidate: {field.interpretedCandidate}
                          </div>
                        )}
                      </div>

                      {/* Status indicator badge */}
                      <div className="flex items-center gap-3">
                        {field.status === 'confident' && (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-xs font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                            <span>Grounded ({confidencePercent}%)</span>
                          </span>
                        )}

                        {field.status === 'uncertain' && (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-xs font-semibold">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                            <span>Needs verification ({confidencePercent}%)</span>
                          </span>
                        )}

                        {field.status === 'flagged' && (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800 text-xs font-semibold">
                            <AlertTriangle className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
                            <span>Safety alert ({confidencePercent}%)</span>
                          </span>
                        )}

                        {field.status === 'abstained' && (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-100 dark:bg-red-950/60 text-red-900 dark:text-red-200 border border-red-300 dark:border-red-800 text-xs font-semibold">
                            <ShieldAlert className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
                            <span>Abstained ({confidencePercent}%)</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Explanation */}
                    <p className="text-sm sm:text-base text-theme-secondary leading-relaxed pt-1">
                      {field.explanation}
                    </p>

                    {/* Uncertainty Warning Box */}
                    {isUncertain && (
                      <div className="mt-3.5 p-3.5 rounded-xl bg-amber-50/80 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 space-y-1.5 text-xs">
                        <div className="flex items-center gap-2 text-amber-900 dark:text-amber-300 font-semibold">
                          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                          <span>Attention: Ambiguous handwriting</span>
                        </div>
                        <p className="text-amber-800 dark:text-amber-300 leading-relaxed">
                          <strong>Observation: </strong>
                          {field.uncertaintyReason ||
                            'The handwriting does not provide enough visual evidence to confidently interpret this field.'}
                        </p>
                        <p className="font-semibold text-amber-950 dark:text-amber-200 pt-0.5">
                          <strong>Required action: </strong>
                          {field.verificationInstruction ||
                            'Compare with original prescription / consult healthcare professional.'}
                        </p>
                      </div>
                    )}

                    {/* Source link */}
                    <div className="pt-3 mt-3 border-t border-theme flex items-center justify-between text-xs text-theme-muted">
                      <div className="flex items-center gap-1.5">
                        <FileSearch className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                        <span>Source: {field.source}</span>
                      </div>
                      <span className="text-teal-700 dark:text-teal-400 font-medium">
                        Hover to inspect stroke
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Formulary Evidence Grounding Section */}
          <MedicineValidationSection evidence={currentState.validationEvidence} />

          {/* Multilingual Patient Posology Explanation */}
          <MultilingualExplanationCard multilingual={currentState.multilingual} />
        </div>
      </div>
    </div>
  );
};
