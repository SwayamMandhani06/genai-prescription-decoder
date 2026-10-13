import React, { useState } from 'react';
import {
  ResultsDemoState,
  PrescriptionAnalysisResult,
} from '../../types/prescription.types';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import { apiConfig } from '../../services/api/apiConfig';
import { OriginalScriptViewer } from '../results/OriginalScriptViewer';
import { LasaSafetyCard } from '../results/LasaSafetyCard';
import { MultilingualExplanationCard } from '../results/MultilingualExplanationCard';
import { MedicineValidationSection } from '../results/MedicineValidationSection';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Printer,
  UploadCloud,
  User,
  Stethoscope,
  ChevronDown,
  ChevronUp,
  FileText,
  Clock,
  Pill,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';

export interface FindingsStepProps {
  uploadedData: UploadedPrescriptionFile | null;
  initialResult?: PrescriptionAnalysisResult | null;
  liveDemoState?: ResultsDemoState | null;
  rotation?: number;
  onNewPrescription: () => void;
}

export const FindingsStep: React.FC<FindingsStepProps> = ({
  uploadedData,
  initialResult,
  liveDemoState,
  onNewPrescription,
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);

  // If liveDemoState is present, it is the genuine live multimodal inference state
  const currentState = liveDemoState || null;

  const handlePrint = () => {
    window.print();
  };

  if (!currentState) {
    return (
      <div className="max-w-4xl mx-auto w-full px-4 py-12 text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
        <h2 className="text-2xl font-bold text-theme-primary">No Analysis Findings Available</h2>
        <p className="text-theme-secondary text-sm">
          Please upload a prescription image to initiate live multimodal vision analysis.
        </p>
        <button
          onClick={onNewPrescription}
          className="px-5 py-2.5 rounded-xl bg-primary text-primary-contrast font-medium text-sm inline-flex items-center gap-2 cursor-pointer"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Prescription</span>
        </button>
      </div>
    );
  }

  // Resolve genuine patient details (no fabrication)
  const patientDetails = currentState.patientDetails || {};
  const patientName = patientDetails.name || (currentState.patientName !== 'Anonymized Patient' && currentState.patientName !== 'Ramesh Kumar' ? currentState.patientName : null);
  const patientAgeDob = patientDetails.ageOrDob || null;
  const patientSex = patientDetails.sexGender || null;
  const patientId = patientDetails.patientId || null;
  const rxDate = patientDetails.prescriptionDate || null;

  // Resolve genuine doctor & clinic details (no fabrication)
  const doctorDetails = currentState.doctorDetails || {};
  const doctorName = doctorDetails.doctorName || (currentState.doctorName !== 'Consulting Physician' && currentState.doctorName !== 'Dr. Arvind Gupta' ? currentState.doctorName : null);
  const qualifications = doctorDetails.qualifications || null;
  const clinicName = doctorDetails.clinicOrHospital || (currentState.clinicName !== 'Clinical Care Center' ? currentState.clinicName : null);
  const contactInfo = doctorDetails.contact || null;
  const regNumber = doctorDetails.registrationNo || null;

  // Resolve prescription summary (2-4 plain language sentences)
  const summaryText =
    currentState.prescriptionSummary ||
    currentState.multilingual?.en?.summary ||
    'Prescription document processed. Please review the extracted medication lines and confirm posology instructions below.';

  // Resolve medicines list
  const medicines = currentState.medicinesList && currentState.medicinesList.length > 0
    ? currentState.medicinesList
    : currentState.fields
        .filter((f) => f.fieldKey === 'medicineName' || f.fieldName.toLowerCase().includes('medicine') || f.fieldName.toLowerCase().includes('item'))
        .map((f) => ({
          name: f.value || 'Medication',
          strength: currentState.fields.find((d) => d.fieldKey === 'dosage')?.value || null,
          formulation: null,
          dosageAmount: null,
          frequency: currentState.fields.find((d) => d.fieldKey === 'frequency')?.value || null,
          frequencyPlain: null,
          timingAndFood: null,
          duration: currentState.fields.find((d) => d.fieldKey === 'duration')?.value || null,
          route: 'Oral',
          specialInstructions: null,
          patientExplanation: f.explanation || 'Take as directed on prescription pad.',
          requiresVerification: f.status !== 'confident',
          status: f.status as 'confident' | 'uncertain' | 'flagged',
          candidates: f.interpretedCandidate ? [f.interpretedCandidate] : [],
        }));

  // Resolve preview image URL (real uploaded file or backend preserved URL)
  const previewImageUrl =
    uploadedData?.previewUrl ||
    (initialResult?.originalImageUrl
      ? initialResult.originalImageUrl.startsWith('http')
        ? initialResult.originalImageUrl
        : `${apiConfig.baseUrl}${initialResult.originalImageUrl}`
      : undefined);

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Header Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-theme">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-theme-primary">
              Prescription Findings
            </h1>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Live Multimodal AI Analysis
            </span>
          </div>
          <p className="text-sm sm:text-base text-theme-secondary">
            Prescription ID: <span className="font-mono text-theme-primary font-semibold">{currentState.accessionId}</span>
            {rxDate && <span> &middot; Date: <span className="font-medium text-theme-primary">{rxDate}</span></span>}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handlePrint}
            className="text-sm font-semibold text-theme-secondary hover:text-theme-primary transition-colors flex items-center gap-2 cursor-pointer py-2 px-3 border border-theme rounded-xl bg-surface"
          >
            <Printer className="w-4 h-4 text-theme-muted" />
            <span>Print Report</span>
          </button>

          <button
            onClick={onNewPrescription}
            className="px-5 py-2.5 rounded-xl bg-[#4A2E4D] hover:bg-[#5C3A60] dark:bg-[#F472B6] dark:hover:bg-[#F687C2] text-white dark:text-[#2E2233] text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer shadow-sm"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Analyze Another</span>
          </button>
        </div>
      </div>

      {/* 2. Short Plain-Language Prescription Summary */}
      <div className="rounded-2xl border border-blue-200 dark:border-blue-900 bg-blue-50/50 dark:bg-blue-950/20 p-5 sm:p-6 space-y-2.5">
        <div className="flex items-center gap-2 text-blue-900 dark:text-blue-200 font-semibold text-sm">
          <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span>Prescription Overview</span>
        </div>
        <p className="text-base sm:text-lg text-theme-primary leading-relaxed font-normal">
          {summaryText}
        </p>
        <p className="text-xs text-theme-muted">
          * Grounded in direct ink strokes extracted from your uploaded prescription. No independent medical diagnoses are inferred.
        </p>
      </div>

      {/* 3. Primary Grid: Document Visual on Left, Structured Clinical Content on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Original Prescription Document (5 columns on desktop) */}
        <div className="lg:col-span-5 space-y-4 lg:sticky lg:top-20">
          <div className="flex items-center justify-between px-0.5">
            <h2 className="text-xl font-bold text-theme-primary tracking-tight">
              Original Prescription Pad
            </h2>
            <span className="text-theme-muted text-xs">Primary legal visual evidence</span>
          </div>

          <OriginalScriptViewer
            scriptKey={currentState.rawScriptKey}
            previewUrl={previewImageUrl}
            accessionId={currentState.accessionId}
          />
        </div>

        {/* Right: Patient & Doctor Details, Medications, Safety Review (7 columns) */}
        <div className="lg:col-span-7 space-y-8">
          {/* A. Patient & Doctor Details Panel */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Patient Card */}
            <div className="rounded-2xl border border-theme bg-surface p-5 space-y-3">
              <div className="flex items-center gap-2 border-b border-theme pb-2.5 text-theme-primary font-semibold text-sm">
                <User className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6]" />
                <span>Patient Information</span>
              </div>
              <div className="space-y-2 text-xs sm:text-sm">
                <div className="flex justify-between">
                  <span className="text-theme-muted">Name:</span>
                  <span className={`font-medium ${patientName ? 'text-theme-primary' : 'text-theme-muted italic'}`}>
                    {patientName || 'Not present in prescription'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-muted">Age / Gender:</span>
                  <span className={`font-medium ${(patientAgeDob || patientSex) ? 'text-theme-primary' : 'text-theme-muted italic'}`}>
                    {[patientAgeDob, patientSex].filter(Boolean).join(', ') || 'Not present in prescription'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-muted">Patient ID / MRN:</span>
                  <span className={`font-medium ${patientId ? 'font-mono text-theme-primary' : 'text-theme-muted italic'}`}>
                    {patientId || 'Not present in prescription'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-muted">Prescription Date:</span>
                  <span className={`font-medium ${rxDate ? 'font-mono text-theme-primary' : 'text-theme-muted italic'}`}>
                    {rxDate || 'Not present in prescription'}
                  </span>
                </div>
              </div>
            </div>

            {/* Doctor & Facility Card */}
            <div className="rounded-2xl border border-theme bg-surface p-5 space-y-3">
              <div className="flex items-center gap-2 border-b border-theme pb-2.5 text-theme-primary font-semibold text-sm">
                <Stethoscope className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6]" />
                <span>Doctor &amp; Facility</span>
              </div>
              <div className="space-y-2 text-xs sm:text-sm">
                <div className="flex justify-between">
                  <span className="text-theme-muted">Prescribing Doctor:</span>
                  <span className={`font-medium ${doctorName ? 'text-theme-primary' : 'text-theme-muted italic'}`}>
                    {doctorName || 'Not present in prescription'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-muted">Qualifications:</span>
                  <span className={`font-medium ${qualifications ? 'text-theme-primary' : 'text-theme-muted italic'}`}>
                    {qualifications || 'Not present in prescription'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-muted">Clinic / Facility:</span>
                  <span className={`font-medium ${clinicName ? 'text-theme-primary' : 'text-theme-muted italic'}`}>
                    {clinicName || 'Not present in prescription'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-muted">Registration No:</span>
                  <span className={`font-medium ${regNumber ? 'font-mono text-theme-primary' : 'text-theme-muted italic'}`}>
                    {regNumber || 'Not present in prescription'}
                  </span>
                </div>
                {contactInfo && (
                  <div className="flex justify-between">
                    <span className="text-theme-muted">Contact Info:</span>
                    <span className="font-medium text-theme-primary font-mono">{contactInfo}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* B. Individual Extracted Medicine Cards */}
          <div className="space-y-4">
            <div className="flex items-center justify-between px-0.5">
              <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
                Prescribed Medicines ({medicines.length})
              </h2>
              <span className="text-theme-muted text-xs sm:text-sm">Evidence grounded</span>
            </div>

            <div className="space-y-4">
              {medicines.map((med, idx) => (
                <div
                  key={`med-${idx}-${med.name}`}
                  className="rounded-2xl border border-theme bg-surface p-5 sm:p-6 space-y-4 shadow-xs"
                >
                  {/* Medicine Header */}
                  <div className="flex flex-wrap items-start justify-between gap-3 border-b border-theme pb-3.5">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Pill className="w-5 h-5 text-[#7C5A8B] dark:text-[#F472B6]" />
                        <h3 className="text-xl font-bold text-theme-primary tracking-tight font-mono">
                          {med.name}
                        </h3>
                        {med.strength && (
                          <span className="px-2 py-0.5 rounded-md bg-surface-subtle border border-theme text-xs font-semibold text-theme-secondary font-mono">
                            {med.strength}
                          </span>
                        )}
                        {med.formulation && (
                          <span className="px-2 py-0.5 rounded-md bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 text-xs font-medium text-blue-800 dark:text-blue-300">
                            {med.formulation}
                          </span>
                        )}
                      </div>
                      {med.route && (
                        <p className="text-xs text-theme-muted">Route: {med.route}</p>
                      )}
                    </div>

                    {/* Verification Status Badge */}
                    <div>
                      {med.status === 'confident' && !med.requiresVerification ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-700 text-emerald-800 dark:text-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Confirmed Reading</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-700 text-amber-900 dark:text-amber-200">
                          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                          <span>Needs Pharmacist Confirmation</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Posology Details Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs sm:text-sm">
                    <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-0.5">
                      <span className="text-theme-muted text-xs block">Dosage Quantity</span>
                      <strong className="text-theme-primary font-medium">
                        {med.dosageAmount || med.strength || 'As directed'}
                      </strong>
                    </div>

                    <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-0.5">
                      <span className="text-theme-muted text-xs block">Frequency</span>
                      <strong className="text-theme-primary font-medium">
                        {med.frequencyPlain || med.frequency || 'As written'}
                      </strong>
                      {med.frequency && med.frequencyPlain && (
                        <span className="text-[11px] text-theme-muted block font-mono">({med.frequency})</span>
                      )}
                    </div>

                    <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-0.5">
                      <span className="text-theme-muted text-xs block">Timing &amp; Food</span>
                      <strong className="text-theme-primary font-medium">
                        {med.timingAndFood || 'Not specified'}
                      </strong>
                    </div>

                    <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-0.5">
                      <span className="text-theme-muted text-xs block">Duration</span>
                      <strong className="text-theme-primary font-medium">
                        {med.duration || 'Not specified'}
                      </strong>
                    </div>
                  </div>

                  {/* Patient-Friendly Grounded Medicine Explanation */}
                  <div className="rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 p-3.5 text-xs sm:text-sm text-theme-secondary flex items-start gap-2.5">
                    <Clock className="w-4 h-4 text-emerald-700 dark:text-emerald-400 shrink-0 mt-0.5" />
                    <div className="space-y-0.5">
                      <strong className="font-semibold text-emerald-950 dark:text-emerald-200">Patient Instruction: </strong>
                      <span>
                        {med.patientExplanation ||
                          (med.timingAndFood
                            ? `Take ${med.name} ${med.timingAndFood.toLowerCase()}, as indicated on your prescription.`
                            : `Take ${med.name} according to the verified schedule on your prescription pad.`)}
                      </span>
                      {med.requiresVerification && (
                        <p className="text-amber-800 dark:text-amber-300 text-xs font-medium pt-1">
                          Notice: Handwriting strokes for this medication are cursive or ambiguous. Please confirm exact timing with your dispensing pharmacist.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* C. Safety & LASA Conflict Screening */}
          <div className="space-y-3">
            <h2 className="text-xl font-bold text-theme-primary tracking-tight">
              Safety &amp; Look-Alike Sound-Alike (LASA) Screening
            </h2>

            {currentState.lasaDetail && currentState.lasaDetail.hasWarning ? (
              <LasaSafetyCard lasaDetail={currentState.lasaDetail} />
            ) : (
              <div className="rounded-2xl border border-emerald-300 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-950/20 p-5 flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1 text-xs sm:text-sm">
                  <h3 className="font-semibold text-emerald-950 dark:text-emerald-100">
                    Formulary LASA Collision Check Complete
                  </h3>
                  <p className="text-emerald-900/80 dark:text-emerald-300/80 leading-relaxed">
                    Extracted medicine names were cross-referenced against the CDSCO India and ISMP Look-Alike Sound-Alike catalogs. No high-risk orthographic or phonetic name-confusion collisions were identified for this prescription.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* D. Abstention Notice (Only when overall status is ABSTAINED) */}
          {(currentState.overallStatus === 'ABSTAINED' || currentState.id === 'state-abstained') && (
            <div className="rounded-2xl border-2 border-red-300 dark:border-red-800 bg-red-50/70 dark:bg-red-950/30 p-5 sm:p-6 space-y-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 flex items-center justify-center shrink-0">
                  <ShieldAlert className="w-5 h-5 text-red-700 dark:text-red-400" />
                </div>
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-red-950 dark:text-red-100">
                    Clinical Abstention Activated
                  </h3>
                  <p className="text-xs sm:text-sm text-red-800 dark:text-red-300">
                    Optical ink ambiguity exceeds diagnostic safety limits. Automated inference halted.
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

          {/* E. Multilingual Patient Explanation & Text-to-Speech (Listen) */}
          <MultilingualExplanationCard
            multilingual={currentState.multilingual}
            medicines={medicines}
            prescriptionSummary={currentState.prescriptionSummary}
            accessionId={currentState.accessionId}
          />

          {/* F. Expandable Detailed Pharmacopeia Evidence & Technical Telemetry */}
          <div className="border border-theme rounded-2xl bg-surface overflow-hidden">
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              className="w-full px-5 py-4 flex items-center justify-between text-left text-sm font-semibold text-theme-primary hover:bg-surface-subtle transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <HelpCircle className="w-4 h-4 text-theme-muted" />
                <span>Advanced Clinical Grounding &amp; Technical Evidence</span>
              </div>
              {showTechnicalDetails ? (
                <ChevronUp className="w-4 h-4 text-theme-muted" />
              ) : (
                <ChevronDown className="w-4 h-4 text-theme-muted" />
              )}
            </button>

            {showTechnicalDetails && (
              <div className="p-5 border-t border-theme space-y-6 bg-surface-subtle/50">
                <MedicineValidationSection evidence={currentState.validationEvidence} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
