import React, { useState } from 'react';
import { SAMPLE_PRESCRIPTION_CANVASES, HandwrittenStrokeLine } from '../../data/sampleHandwrittenSvg';
import {
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ShieldCheck,
  Eye,
} from 'lucide-react';

interface ResolvedMedicineItem {
  id: string;
  name: string;
  genericName: string;
  dosage: string;
  frequency: string;
  duration: string;
  evidenceSource: string;
  confidence: number;
  status: 'verified' | 'flagged' | 'warning';
  annotationNote: string;
}

const RESOLVED_ITEMS: Record<string, ResolvedMedicineItem> = {
  'stroke-1': {
    id: 'stroke-1',
    name: 'Amoxicillin Trihydrate',
    genericName: 'Amoxicillin 500mg Capsule',
    dosage: '500 mg',
    frequency: '1 capsule three times daily (TDS, after meals)',
    duration: '5 days',
    evidenceSource: 'CDSCO & RxNorm #213169',
    confidence: 0.96,
    status: 'verified',
    annotationNote: 'Visual match with standard antibiotherapy posology.',
  },
  'stroke-2': {
    id: 'stroke-2',
    name: 'Pantoprazole Gastro-Resistant',
    genericName: 'Pantoprazole Sodium 40mg Tablet',
    dosage: '40 mg',
    frequency: '1 tablet once daily before breakfast (OD, AC)',
    duration: '10 days',
    evidenceSource: 'CDSCO & RxNorm #284635',
    confidence: 0.94,
    status: 'verified',
    annotationNote: 'Grounded against gastroprotective proton-pump inhibitor catalog.',
  },
  'stroke-3': {
    id: 'stroke-3',
    name: 'Paracetamol (Acetaminophen)',
    genericName: 'Paracetamol 650mg Tablet',
    dosage: '650 mg',
    frequency: 'As needed for fever > 100°F (SOS)',
    duration: '3 days max',
    evidenceSource: 'CDSCO & RxNorm #161',
    confidence: 0.68,
    status: 'warning',
    annotationNote: 'Ambiguous cursive terminal loop: interpreted as SOS, requires pharmacist confirmation.',
  },
};

export const HeroPrescriptionCanvas: React.FC = () => {
  const canvasData = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];
  const [activeLineId, setActiveLineId] = useState<string>('stroke-1');
  const [isResolvedView, setIsResolvedView] = useState<boolean>(true);

  const activeResolved = RESOLVED_ITEMS[activeLineId] || RESOLVED_ITEMS['stroke-1'];

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Interactive Mode Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2 rounded-xl bg-surface border border-theme text-xs">
        <div className="flex items-center gap-2 text-theme-secondary">
          <Eye className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
          <span className="font-medium text-theme-primary">Interactive Document:</span>
          <span className="hidden sm:inline">Click any handwritten line to see it resolve into verified structure.</span>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-1 bg-surface-subtle p-1 rounded-lg border border-theme">
          <button
            type="button"
            onClick={() => setIsResolvedView(false)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
              !isResolvedView
                ? 'bg-surface text-theme-primary shadow-xs font-semibold'
                : 'text-theme-muted hover:text-theme-primary'
            }`}
          >
            Handwritten Ink
          </button>
          <button
            type="button"
            onClick={() => setIsResolvedView(true)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer flex items-center gap-1 ${
              isResolvedView
                ? 'bg-surface text-teal-700 dark:text-teal-300 shadow-xs font-semibold'
                : 'text-theme-muted hover:text-theme-primary'
            }`}
          >
            <Sparkles className="w-3 h-3 text-teal-600 dark:text-teal-400" />
            <span>Structured & Verified</span>
          </button>
        </div>
      </div>

      {/* Main Prescription Card (Paper Surface) */}
      <div className="prescription-paper rounded-2xl p-6 sm:p-8 text-slate-900 relative overflow-hidden transition-all duration-300 border border-amber-900/15 dark:border-white/15">
        {/* Doctor Header & Letterhead */}
        <div className="border-b border-slate-300 pb-4 mb-5">
          <div className="flex flex-col sm:flex-row justify-between items-start gap-2">
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-teal-900">
                {canvasData.doctorHeader.clinicName}
              </div>
              <h3 className="font-bold text-base tracking-tight text-slate-950">
                {canvasData.doctorHeader.name}
              </h3>
              <p className="text-xs text-slate-600">
                {canvasData.doctorHeader.qualifications} · {canvasData.doctorHeader.clinicAddress}
              </p>
            </div>
            <div className="sm:text-right text-xs text-slate-600 space-y-0.5">
              <span className="inline-block px-2 py-0.5 rounded bg-slate-200/80 text-slate-800 text-[11px] font-mono font-medium">
                {canvasData.doctorHeader.regNo}
              </span>
              <div className="text-[11px]">Date: {canvasData.patientInfo.date}</div>
            </div>
          </div>

          {/* Patient Details Strip */}
          <div className="mt-3 pt-2.5 border-t border-dashed border-slate-300 flex flex-wrap justify-between gap-2 text-xs text-slate-700">
            <span>
              <strong>Patient:</strong> {canvasData.patientInfo.name} ({canvasData.patientInfo.ageGender})
            </span>
            <span>
              <strong>Vitals:</strong> {canvasData.patientInfo.vitals}
            </span>
          </div>
        </div>

        {/* Prescription Body with Rx Mark */}
        <div className="space-y-4">
          <div className="text-slate-900 font-serif italic text-2xl font-black">
            ℞
          </div>

          {/* Cursive Medicine Lines with Interactive Hover & Resolution */}
          <div className="space-y-3">
            {canvasData.strokes.map((stroke: HandwrittenStrokeLine, idx: number) => {
              const isSelected = activeLineId === stroke.id;
              const resolved = RESOLVED_ITEMS[stroke.id];

              return (
                <div
                  key={stroke.id}
                  onClick={() => setActiveLineId(stroke.id)}
                  onMouseEnter={() => setActiveLineId(stroke.id)}
                  className={`group p-3.5 rounded-xl transition-all cursor-pointer border ${
                    isSelected
                      ? 'bg-teal-50/80 border-teal-600/50 shadow-xs'
                      : 'bg-black/[0.02] border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    {/* Left: Handwritten Cursive SVG stroke */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11px] font-mono text-slate-500 font-medium">
                          0{idx + 1}.
                        </span>
                        {isResolvedView && resolved && (
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm text-slate-950">
                              {resolved.name}
                            </span>
                            <span className="text-xs text-slate-600">
                              {resolved.dosage}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Doctor Blue Ballpoint Ink SVG */}
                      <div className="py-0.5">
                        <svg
                          viewBox="0 0 650 35"
                          className="w-full h-7 overflow-visible"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            d={stroke.svgPath}
                            fill="none"
                            stroke="currentColor"
                            className={`transition-all duration-200 ${
                              isSelected
                                ? 'text-blue-800 stroke-[2.8]'
                                : 'text-blue-900/85 stroke-[2.2]'
                            }`}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </div>

                      {/* When in resolved view, show dosage & schedule */}
                      {isResolvedView && resolved && (
                        <div className="text-xs text-slate-600 mt-1 flex flex-wrap items-center gap-3">
                          <span><strong>Schedule:</strong> {resolved.frequency}</span>
                          <span>·</span>
                          <span><strong>Duration:</strong> {resolved.duration}</span>
                        </div>
                      )}
                    </div>

                    {/* Right: Verification Status Badge */}
                    <div className="sm:text-right shrink-0">
                      {resolved?.status === 'warning' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-amber-100 text-amber-900 border border-amber-300">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                          <span>Verify Ambiguity</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-100 text-emerald-900 border border-emerald-300">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                          <span>Formulary Verified</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Details for the Active Item */}
        <div className="mt-5 pt-4 border-t border-slate-300">
          <div className="p-3.5 rounded-xl bg-amber-900/[0.04] border border-amber-900/10 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 text-xs">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-teal-700" />
                <span className="font-semibold text-slate-950">
                  {activeResolved.genericName}
                </span>
                <span className="text-[11px] text-slate-600">
                  ({activeResolved.evidenceSource})
                </span>
              </div>
              <p className="text-slate-600 text-[11px]">
                {activeResolved.annotationNote}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[11px] text-slate-600">
                Confidence:
              </span>
              <span className="font-mono text-xs font-bold text-teal-900 px-2 py-0.5 rounded bg-teal-100/70 border border-teal-300">
                {Math.round(activeResolved.confidence * 100)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
