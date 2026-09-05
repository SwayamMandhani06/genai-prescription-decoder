import React, { useState } from 'react';
import { MOCK_PRESCRIPTION_SAMPLES } from '../../data/mockPrescriptions';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import { MULTILINGUAL_EXPLANATIONS } from '../../data/multilingualCatalog';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { ConfidenceMeter } from '../ui/ConfidenceMeter';
import { Modal } from '../ui/Modal';
import { MedicineCandidate } from '../../types/prescription.types';
import { LanguageCode } from '../../types/explanation.types';
import {
  Sparkles,
  AlertTriangle,
  ExternalLink,
  Languages,
  FileCheck2,
  Crosshair,
} from 'lucide-react';

export const InteractiveAnalyzer: React.FC = () => {
  const [selectedSampleId, setSelectedSampleId] = useState<string>('rx-sample-1');
  const [hoveredMedicineId, setHoveredMedicineId] = useState<string | null>(null);
  const [selectedMedicineForModal, setSelectedMedicineForModal] = useState<MedicineCandidate | null>(null);
  const [activeLanguage, setActiveLanguage] = useState<LanguageCode>('en');

  const currentSample =
    MOCK_PRESCRIPTION_SAMPLES.find((s) => s.id === selectedSampleId) ||
    MOCK_PRESCRIPTION_SAMPLES[0];
  const canvasData =
    SAMPLE_PRESCRIPTION_CANVASES[selectedSampleId] ||
    SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];
  const languageExplanation = MULTILINGUAL_EXPLANATIONS[selectedSampleId]?.[activeLanguage];

  return (
    <section id="analyzer" className="py-20 bg-[#07090E] border-b border-white/[0.06] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
          <Badge variant="cyan" size="sm" dot>
            Clinical Inspection Console
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight font-sans">
            Simulated Prescription Diagnostic Console
          </h2>
          <p className="text-sm sm:text-base text-slate-300 font-sans">
            Inspect real-world outpatient clinical prescriptions. Compare the physical paper artifact with synchronized bounding polygons, ontology validation records, and vernacular schedules.
          </p>
        </div>

        {/* Prescription Sample Selector (Segmented Bar) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
          {MOCK_PRESCRIPTION_SAMPLES.map((sample) => {
            const isSelected = sample.id === selectedSampleId;

            return (
              <button
                key={sample.id}
                onClick={() => {
                  setSelectedSampleId(sample.id);
                  setHoveredMedicineId(null);
                }}
                className={`p-3.5 rounded-lg text-left border transition-all cursor-pointer flex flex-col justify-between ${
                  isSelected
                    ? 'bg-[#121826] border-cyan-500/60 shadow-lg'
                    : 'bg-[#0B0E17] border-white/[0.06] hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-xs font-mono font-bold text-cyan-400">
                    {sample.id === 'rx-sample-1'
                      ? 'SAMPLE A: MULTI-DRUG'
                      : sample.id === 'rx-sample-2'
                      ? 'SAMPLE B: LASA RISK'
                      : 'SAMPLE C: SELECTIVE ABSTENTION'}
                  </span>
                  <Badge
                    variant={
                      sample.difficultyScore === 'Clear'
                        ? 'emerald'
                        : sample.difficultyScore === 'Moderate Cursive'
                        ? 'amber'
                        : 'coral'
                    }
                    size="xs"
                  >
                    {sample.difficultyScore}
                  </Badge>
                </div>
                <h3 className="text-xs sm:text-sm font-bold text-slate-100 line-clamp-1 mb-0.5">
                  {sample.title}
                </h3>
                <p className="text-[11px] text-slate-400 line-clamp-2">
                  {sample.chiefComplaint}
                </p>
              </button>
            );
          })}
        </div>

        {/* Top Control Bar: Patient Context & Vernacular Switcher */}
        <div className="p-3.5 rounded-lg bg-[#0E131F] border border-white/[0.08] mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-500/30">
              <FileCheck2 className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-mono font-bold text-white">
                {currentSample.patientProfile} · {currentSample.doctorSpecialty}
              </div>
              <div className="text-[11px] text-slate-400 font-sans">
                Diagnosis Context: {currentSample.chiefComplaint}
              </div>
            </div>
          </div>

          {/* Vernacular Language Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
              <Languages className="w-3.5 h-3.5 text-cyan-400" />
              <span>Vernacular Posology:</span>
            </span>
            <div className="flex items-center bg-[#07090E] p-0.5 rounded border border-white/10">
              {(['en', 'hi', 'mr'] as LanguageCode[]).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setActiveLanguage(lang)}
                  className={`px-3 py-1 text-xs font-mono rounded transition-all cursor-pointer ${
                    activeLanguage === lang
                      ? 'bg-cyan-950 text-cyan-300 font-bold border border-cyan-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {lang === 'en' ? 'English' : lang === 'hi' ? 'हिन्दी' : 'मराठी'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Dual Pane Layout: Authentic Paper Artifact vs Structured AI Inspection */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Pane: Authentic Physical Paper Prescription Slip */}
          <div className="lg:col-span-6 rounded-lg overflow-hidden border border-slate-700/60 shadow-xl bg-slate-900">
            {/* Window Telemetry Strip */}
            <div className="bg-[#0D121D] px-4 py-2 border-b border-white/[0.08] flex items-center justify-between text-[11px] font-mono">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold">
                <Crosshair className="w-3.5 h-3.5" />
                <span>SPATIAL GROUND TRUTH · {canvasData.accessionId}</span>
              </div>
              <span className="text-slate-400 text-[10px]">HOVER TO TRACE INK</span>
            </div>

            {/* Physical Paper Document */}
            <div className="clinical-paper p-5 sm:p-6 text-slate-900 min-h-[480px] flex flex-col justify-between select-none">
              {/* Physician Letterhead */}
              <div className="border-b-2 border-slate-400/40 pb-3 mb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-sm tracking-tight text-slate-900 font-sans">
                      {canvasData.doctorHeader.name}
                    </h3>
                    <p className="text-[10px] text-slate-600 font-sans">
                      {canvasData.doctorHeader.qualifications}
                    </p>
                    <p className="text-[9px] font-mono text-slate-500 mt-0.5">
                      {canvasData.doctorHeader.clinicAddress} · Tel: {canvasData.doctorHeader.phone}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-700 border border-slate-300 block mb-1">
                      {canvasData.doctorHeader.regNo}
                    </span>
                    <div className="text-[9px] font-mono text-slate-500">
                      Date: {canvasData.patientInfo.date}
                    </div>
                  </div>
                </div>

                {/* Patient Vitals */}
                <div className="mt-2 pt-1.5 border-t border-dashed border-slate-300 flex justify-between text-[10px] font-mono text-slate-700">
                  <span>
                    <strong>Patient:</strong> {canvasData.patientInfo.name} ({canvasData.patientInfo.ageGender})
                  </span>
                  <span>
                    <strong>Vitals:</strong> {canvasData.patientInfo.vitals}
                  </span>
                </div>
              </div>

              {/* Rx Symbol */}
              <div className="text-slate-800 font-serif italic text-2xl font-black mb-1">
                ℞
              </div>

              {/* Handwriting strokes with precision crosshairs on hover */}
              <div className="space-y-4 my-auto relative">
                {canvasData.strokes.map((stroke) => {
                  const isHovered = hoveredMedicineId === stroke.medicineId;

                  return (
                    <div
                      key={stroke.id}
                      onMouseEnter={() => setHoveredMedicineId(stroke.medicineId)}
                      onMouseLeave={() => setHoveredMedicineId(null)}
                      className={`relative p-2 rounded transition-all cursor-pointer ${
                        isHovered
                          ? 'bg-cyan-500/15 ring-2 ring-cyan-600 shadow-md'
                          : 'hover:bg-slate-200/40'
                      }`}
                    >
                      {/* Precise Coordinate Overlay */}
                      {isHovered && (
                        <div className="absolute -top-3 left-2 flex items-center gap-1.5 z-30">
                          <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-900 text-cyan-300 border border-cyan-500/40 shadow-sm">
                            TARGET INK POLYGON
                          </span>
                          <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-300">
                            {stroke.pixelCoords}
                          </span>
                        </div>
                      )}

                      {/* SVG Stroke */}
                      <svg
                        viewBox="0 0 650 35"
                        className="w-full h-8 overflow-visible"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d={stroke.svgPath}
                          fill="none"
                          stroke={stroke.inkColor}
                          strokeWidth={isHovered ? '3.4' : '2.4'}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="transition-all duration-150"
                        />
                      </svg>

                      <div className="mt-0.5 text-[10px] font-mono text-slate-700 flex justify-between">
                        <span className="font-semibold">{stroke.label}</span>
                        {isHovered && (
                          <span className="text-cyan-800 font-bold">Synchronized Active Focus</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Physical Document Footer: Signature & Clinic Stamp */}
              <div className="border-t border-slate-300/80 pt-2 mt-2 flex justify-between items-end text-[9px] font-mono text-slate-600">
                <div className="space-y-0.5">
                  <div className="inline-block px-2 py-0.5 rounded border border-slate-400/60 bg-slate-100 font-bold text-[8px] text-slate-700">
                    {canvasData.clinicStampText}
                  </div>
                  <div>Primary Reference: Doctor Physical Slip</div>
                </div>

                <div className="text-right">
                  <svg viewBox="400 340 200 45" className="w-28 h-7 inline-block opacity-80">
                    <path
                      d={canvasData.doctorSignaturePath}
                      fill="none"
                      stroke="#1E3A8A"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="border-t border-slate-400 w-28 text-center text-[8px] text-slate-600">
                    Physician Signature
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Pane: Extracted & Grounded Clinical Entities */}
          <div className="lg:col-span-6 space-y-3.5">
            <div className="flex items-center justify-between text-xs font-mono px-1">
              <span className="text-slate-300 font-bold flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>EXTRACTED & GROUNDED ENTITIES ({currentSample.medications.length})</span>
              </span>
              <span className="text-slate-500 text-[10px]">CLICK FOR MONOGRAPH</span>
            </div>

            {/* Medication Cards */}
            <div className="space-y-3">
              {currentSample.medications.map((med) => {
                const isHovered = hoveredMedicineId === med.id;
                const localized = languageExplanation?.medications.find(
                  (m) => m.medicineId === med.id
                );

                return (
                  <Card
                    key={med.id}
                    variant={isHovered ? 'cyan' : 'glass'}
                    padding="md"
                    className={`transition-all cursor-pointer border rounded-lg ${
                      isHovered
                        ? 'border-cyan-400 bg-cyan-950/30'
                        : med.confidenceLevel === 'ABSTAIN_FLAGGED'
                        ? 'border-red-500/40 bg-red-950/15'
                        : med.confidenceLevel === 'BORDERLINE'
                        ? 'border-amber-500/40 bg-amber-950/15'
                        : 'border-white/[0.08] bg-[#0E121B]'
                    }`}
                    onMouseEnter={() => setHoveredMedicineId(med.id)}
                    onMouseLeave={() => setHoveredMedicineId(null)}
                    onClick={() => setSelectedMedicineForModal(med)}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-base font-bold text-white tracking-tight font-sans">
                            {med.brandName}
                          </h4>
                          <Badge
                            variant={
                              med.confidenceLevel === 'HIGH_CONFIDENCE'
                                ? 'emerald'
                                : med.confidenceLevel === 'BORDERLINE'
                                ? 'amber'
                                : 'coral'
                            }
                            size="xs"
                          >
                            {med.form}
                          </Badge>
                        </div>
                        <p className="text-xs font-mono text-slate-300 mt-0.5">
                          {med.genericName}
                        </p>
                      </div>

                      <div className="text-right shrink-0">
                        <ConfidenceMeter score={med.confidenceScore} compact />
                      </div>
                    </div>

                    {/* Vernacular posology translation */}
                    {localized && (
                      <div className="my-2 p-2.5 rounded bg-black/40 border border-white/5 space-y-1">
                        <div className="flex items-center justify-between text-xs font-bold text-cyan-300 font-mono">
                          <span>{localized.localizedName}</span>
                          <span className="text-[10px] text-slate-400 uppercase">
                            {activeLanguage === 'en' ? 'Posology' : 'डोस वेळापत्रक'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-200 font-sans">
                          {localized.dosageSummary} · {localized.foodInstruction}
                        </p>
                      </div>
                    )}

                    {/* Abstention alert notice if flagged */}
                    {med.abstentionReason && (
                      <div className="mt-2 p-2.5 rounded bg-red-500/10 border border-red-500/30 text-xs text-red-300 space-y-1">
                        <div className="font-bold flex items-center gap-1.5 text-red-400 font-mono">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Selective Prediction Gate: Model Abstained</span>
                        </div>
                        <p className="text-[11px] text-red-200/90 leading-relaxed font-sans">
                          {med.abstentionReason}
                        </p>
                      </div>
                    )}

                    {/* Footer tags */}
                    <div className="mt-2.5 pt-2 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-400">
                      <div className="flex items-center gap-2">
                        {med.rxNormCui && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                            RxNorm: {med.rxNormCui}
                          </span>
                        )}
                        {med.cdscoApproved && (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                            CDSCO Verified
                          </span>
                        )}
                      </div>
                      <span className="text-cyan-400 hover:underline flex items-center gap-1 text-[10px]">
                        <span>View Clinical Monograph</span>
                        <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </Card>
                );
              })}
            </div>

            {/* Overall Advice Box */}
            {languageExplanation && (
              <div className="p-4 rounded-lg bg-[#0E131F] border border-white/[0.08] text-xs text-slate-300 space-y-1.5">
                <span className="font-mono font-bold text-cyan-400 uppercase text-[11px] block">
                  Patient Guidance ({languageExplanation.nativeLabel}):
                </span>
                <p className="leading-relaxed font-sans">{languageExplanation.overallPatientAdvice}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Monograph Detail Modal */}
      {selectedMedicineForModal && (
        <Modal
          isOpen={Boolean(selectedMedicineForModal)}
          onClose={() => setSelectedMedicineForModal(null)}
          title={selectedMedicineForModal.brandName}
          subtitle={selectedMedicineForModal.genericName}
          maxWidth="2xl"
        >
          <div className="space-y-4 text-xs sm:text-sm font-sans">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs">
              <div className="p-2.5 rounded bg-slate-900 border border-white/5">
                <span className="text-slate-500 block text-[10px]">DOSAGE STRENGTH</span>
                <span className="text-white font-bold">{selectedMedicineForModal.dosage}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-white/5">
                <span className="text-slate-500 block text-[10px]">FREQUENCY</span>
                <span className="text-cyan-400 font-bold">{selectedMedicineForModal.frequency}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-white/5">
                <span className="text-slate-500 block text-[10px]">DURATION</span>
                <span className="text-slate-200">{selectedMedicineForModal.duration}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-white/5">
                <span className="text-slate-500 block text-[10px]">CALIBRATED CONFIDENCE</span>
                <span className="text-emerald-400 font-bold">
                  {Math.round(selectedMedicineForModal.confidenceScore * 100)}%
                </span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-slate-400 font-mono text-xs uppercase tracking-wider">
                Clinical Indication & Purpose:
              </span>
              <p className="text-slate-200 leading-relaxed">
                {selectedMedicineForModal.indication}
              </p>
            </div>

            <div className="p-3.5 rounded bg-cyan-950/20 border border-cyan-500/20 space-y-1.5 font-mono text-xs">
              <div className="text-cyan-400 font-bold">ONTOLOGY VERIFICATION RECORD</div>
              <div className="flex justify-between text-slate-300">
                <span>RxNorm Concept Unique Identifier (CUI):</span>
                <span className="text-white">{selectedMedicineForModal.rxNormCui || 'N/A'}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>WHO Anatomical Therapeutic Chemical (ATC):</span>
                <span className="text-white">{selectedMedicineForModal.atcCode || 'J01CR02'}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>CDSCO India Regulatory Approval:</span>
                <span className="text-emerald-400">
                  {selectedMedicineForModal.cdscoApproved ? 'Verified Marketed Formulation' : 'Unverified'}
                </span>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </section>
  );
};
