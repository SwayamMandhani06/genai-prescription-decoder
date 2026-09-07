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
import {
  ShieldCheck,
  AlertTriangle,
  AlertCircle,
  Printer,
  UploadCloud,
  CheckCircle2,
  Languages,
  Clock,
  Utensils,
  ExternalLink,
} from 'lucide-react';

export interface FindingsStepProps {
  uploadedData: UploadedPrescriptionFile | null;
  initialResult?: PrescriptionAnalysisResult | null;
  rotation?: number;
  onNewPrescription: () => void;
}

export const FindingsStep: React.FC<FindingsStepProps> = ({
  uploadedData,
  onNewPrescription,
}) => {
  // Determine state based on sample ID
  const determineInitialState = (): ResultsDemoStateId => {
    if (uploadedData?.sampleId === 'rx-sample-2') return 'state-lasa';
    if (uploadedData?.sampleId === 'rx-sample-3') return 'state-flagged';
    return 'state-confident';
  };

  const [activeStateId, setActiveStateId] = useState<ResultsDemoStateId>(determineInitialState);
  const [hoveredBox, setHoveredBox] = useState<BoundingBox | null>(null);
  const [hoveredLabel, setHoveredLabel] = useState<string | undefined>(undefined);
  const [activeLang, setActiveLang] = useState<'en' | 'hi' | 'mr'>('en');

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
            previewUrl={uploadedData?.previewUrl}
            activeBoundingBox={hoveredBox}
            highlightLabel={hoveredLabel}
            accessionId={currentState.accessionId}
          />
        </div>

        {/* Right: Interpreted Medication, Formulary Evidence & Explanation (7 cols) */}
        <div className="lg:col-span-7 space-y-8">
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
                        ? 'border-teal-500 shadow-md bg-surface'
                        : 'border-theme bg-surface shadow-xs'
                    }`}
                  >
                    {/* Header: Medicine Name & Quiet Status */}
                    <div className="flex items-start justify-between gap-3 mb-2.5">
                      <div>
                        <span className="text-xs text-theme-muted block mb-1 font-medium">
                          {field.fieldName}
                        </span>
                        <h3 className="text-2xl sm:text-3xl font-bold text-theme-primary tracking-tight">
                          {field.value}
                        </h3>
                        {field.interpretedCandidate && (
                          <div className="text-xs sm:text-sm text-teal-700 dark:text-teal-400 font-medium mt-1">
                            Candidate: {field.interpretedCandidate}
                          </div>
                        )}
                      </div>

                      {/* Status indicator: Quiet when confident, prominent when alert needed */}
                      <div>
                        {field.status === 'confident' && (
                          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>Verified</span>
                          </span>
                        )}

                        {field.status === 'uncertain' && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800 text-xs font-semibold">
                            <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                            <span>Verification needed</span>
                          </span>
                        )}

                        {field.status === 'flagged' && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-red-100 dark:bg-red-950/60 text-red-900 dark:text-red-200 border border-red-300 dark:border-red-800 text-xs font-semibold">
                            <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
                            <span>Safety alert</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Regimen Summary - Generous 16-18px body scale */}
                    <p className="text-base sm:text-lg text-theme-secondary leading-relaxed pt-1.5">
                      {field.explanation}
                    </p>

                    {/* Uncertainty Warning Box - High contrast only when attention is required */}
                    {isUncertain && (
                      <div className="mt-3.5 p-3.5 rounded-xl bg-amber-50/80 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 space-y-1.5">
                        <div className="flex items-center gap-2 text-amber-900 dark:text-amber-300 font-semibold text-xs">
                          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                          <span>Attention: Ambiguous handwriting</span>
                        </div>
                        <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                          {field.uncertaintyReason ||
                            'The handwriting does not provide enough visual evidence to confidently interpret this field.'}
                        </p>
                        <p className="text-xs font-semibold text-amber-900 dark:text-amber-200 pt-0.5">
                          {field.verificationInstruction ||
                            'Action: Compare with original prescription / consult healthcare professional.'}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Formulary Evidence - Clean, quiet grouping without heavy boxed card */}
          <div className="space-y-4 pt-6 border-t border-theme">
            <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
              Formulary verification
            </h2>

            <div className="p-5 rounded-2xl bg-surface border border-theme space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-theme-primary text-base sm:text-lg">
                  {currentState.validationEvidence.matchedMedicine}
                </span>
                <span className="font-mono text-xs sm:text-sm text-teal-700 dark:text-teal-400 font-semibold">
                  RxNorm #{currentState.validationEvidence.rxNormCui}
                </span>
              </div>
              <p className="text-sm sm:text-base text-theme-secondary leading-relaxed">
                Generic: {currentState.validationEvidence.genericSalt} &middot; {currentState.validationEvidence.cdscoSchedule}
              </p>
              <div className="text-xs sm:text-sm text-theme-muted pt-1 flex items-center gap-1.5">
                <ExternalLink className="w-3.5 h-3.5" />
                <span>CDSCO National List of Essential Medicines &middot; Official clinical cross-reference</span>
              </div>
            </div>
          </div>

          {/* Multilingual Patient Explanation */}
          <div className="space-y-4 pt-6 border-t border-theme">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <Languages className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
                  Patient explanation
                </h2>
              </div>

              {/* Language Switcher Tabs */}
              <div className="inline-flex p-1 rounded-xl bg-surface-subtle border border-theme">
                {(['en', 'hi', 'mr'] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setActiveLang(lang)}
                    className={`px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all cursor-pointer ${
                      activeLang === lang
                        ? 'bg-teal-600 text-white font-semibold shadow-xs'
                        : 'text-theme-secondary hover:text-theme-primary'
                    }`}
                  >
                    {lang === 'en' ? 'English' : lang === 'hi' ? 'हिन्दी' : 'मराठी'}
                  </button>
                ))}
              </div>
            </div>

            {/* Explanation Content - Spacious editorial typography with elevated depth */}
            <div className="p-6 sm:p-8 rounded-3xl bg-surface shadow-elevated-card border border-theme space-y-5">
              <div className="space-y-2">
                <div className="text-xs sm:text-sm font-semibold text-teal-700 dark:text-teal-400 flex items-center gap-1.5">
                  <Clock className="w-4 h-4" />
                  <span>Dosing schedule &amp; instructions</span>
                </div>
                <p className="text-lg sm:text-xl font-medium text-theme-primary leading-[1.6]">
                  {currentState.multilingual[activeLang].instructions}
                </p>
              </div>

              <div className="flex items-start gap-3 text-sm sm:text-base text-theme-secondary pt-4 border-t border-theme leading-relaxed">
                <Utensils className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-theme-primary font-medium">Dietary guidance: </strong>
                  <span>{currentState.multilingual[activeLang].summary}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
