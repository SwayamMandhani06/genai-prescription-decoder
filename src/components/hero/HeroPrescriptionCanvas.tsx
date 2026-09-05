import React, { useState } from 'react';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import { Badge } from '../ui/Badge';
import { ConfidenceMeter } from '../ui/ConfidenceMeter';
import {
  CheckCircle2,
  ArrowRight,
  Crosshair,
} from 'lucide-react';

export type HeroTransformationStage = 0 | 1 | 2 | 3 | 4;

export interface HeroPrescriptionCanvasProps {
  currentStage: HeroTransformationStage;
  onSelectStage: (stage: HeroTransformationStage) => void;
}

export const HeroPrescriptionCanvas: React.FC<HeroPrescriptionCanvasProps> = ({
  currentStage,
  onSelectStage,
}) => {
  const canvasData = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];
  const [activeHighlight, setActiveHighlight] = useState<string | null>('stroke-1');

  const stages = [
    { index: 0 as HeroTransformationStage, label: '01. Physician Script', tag: 'Cursive Paper' },
    { index: 1 as HeroTransformationStage, label: '02. Bounding HUD', tag: 'Entity Bounding' },
    { index: 2 as HeroTransformationStage, label: '03. Formularies', tag: 'CDSCO / RxNorm' },
    { index: 3 as HeroTransformationStage, label: '04. Calibrated Safety', tag: 'Entropy Gate' },
    { index: 4 as HeroTransformationStage, label: '05. Vernacular Guide', tag: 'EN · HI · MR' },
  ];

  return (
    <div className="w-full rounded-xl overflow-hidden border border-white/10 bg-[#0A0D15] shadow-2xl">
      {/* Medical Workstation Control Bar (No macOS dots, real telemetry) */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-[#0F1420] border-b border-white/[0.08] gap-3 text-xs font-mono">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-cyan-400">
            <Crosshair className="w-3.5 h-3.5 animate-pulse" />
            <span className="font-semibold text-white tracking-wider">
              {canvasData.accessionId}
            </span>
          </div>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-slate-400 hidden sm:inline">
            OPTICAL INTAKE: 300 DPI · FLATBED SENSOR
          </span>
        </div>

        {/* Stage Progression Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto max-w-full pb-1 sm:pb-0">
          {stages.map((stg) => (
            <button
              key={stg.index}
              onClick={() => onSelectStage(stg.index)}
              className={`px-3 py-1 text-xs rounded font-mono transition-all cursor-pointer whitespace-nowrap ${
                currentStage === stg.index
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
              }`}
            >
              {stg.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Workstation Workspace */}
      <div className="p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 bg-[#080B12]">
        {/* Left: Authentic Physical Prescription Paper Artifact with HUD Overlay */}
        <div className="lg:col-span-7 flex flex-col justify-between relative rounded-lg overflow-hidden border border-slate-700/50 shadow-xl">
          {/* Authentic Clinical Paper Sheet */}
          <div className="clinical-paper p-5 sm:p-6 text-slate-900 relative min-h-[460px] flex flex-col justify-between select-none">
            {/* HUD Scanning Line across physical paper */}
            {currentStage > 0 && (
              <div className="absolute left-0 right-0 h-0.5 bg-cyan-600 shadow-[0_0_8px_rgba(2,132,199,0.8)] pointer-events-none animate-hud-scanline z-30 opacity-70" />
            )}

            {/* Top Physician Letterhead */}
            <div className="border-b-2 border-slate-400/40 pb-3 mb-3">
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

              {/* Patient Vitals Strip */}
              <div className="mt-2.5 pt-2 border-t border-dashed border-slate-300 flex flex-wrap justify-between text-[10px] font-mono text-slate-700">
                <span>
                  <strong>Patient:</strong> {canvasData.patientInfo.name} ({canvasData.patientInfo.ageGender})
                </span>
                <span>
                  <strong>Vitals:</strong> {canvasData.patientInfo.vitals}
                </span>
              </div>
            </div>

            {/* Classical Rx Symbol */}
            <div className="text-slate-800 font-serif italic text-2xl font-black mb-1">
              ℞
            </div>

            {/* Doctor Cursive Handwriting Strokes with Surgical HUD Bounding Boxes */}
            <div className="space-y-4 my-auto relative z-20">
              {canvasData.strokes.map((stroke, idx) => {
                const isSelected = activeHighlight === stroke.id;

                return (
                  <div
                    key={stroke.id}
                    onClick={() => setActiveHighlight(stroke.id)}
                    onMouseEnter={() => setActiveHighlight(stroke.id)}
                    className={`relative p-2.5 rounded transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-cyan-500/10 ring-2 ring-cyan-600/70'
                        : currentStage >= 1
                        ? 'bg-slate-200/40 ring-1 ring-slate-400/50 hover:ring-cyan-500/40'
                        : ''
                    }`}
                  >
                    {/* HUD Bounding Coordinates Tag (Stage 1+) */}
                    {currentStage >= 1 && (
                      <div className="absolute -top-3 left-2 flex items-center gap-1.5 z-30">
                        <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-900 text-cyan-300 border border-cyan-500/40 shadow-sm">
                          {idx === 0 ? 'ENT: ANTIBACTERIAL' : idx === 1 ? 'ENT: PPI_GASTRO' : 'ENT: ANTIPYRETIC'}
                        </span>
                        <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-300 hidden sm:inline">
                          {stroke.pixelCoords}
                        </span>
                      </div>
                    )}

                    {/* Authentic Blue Ballpoint Ink Cursive SVG */}
                    <div className="py-1">
                      <svg
                        viewBox="0 0 650 35"
                        className="w-full h-8 overflow-visible"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d={stroke.svgPath}
                          fill="none"
                          stroke={stroke.inkColor}
                          strokeWidth={isSelected ? '3.2' : '2.4'}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="transition-all duration-200"
                        />
                      </svg>
                    </div>

                    {/* Transcribed Translation Ribbon (Stage 2+) */}
                    {currentStage >= 2 && (
                      <div className="mt-1 pt-1 border-t border-slate-300/60 flex items-center justify-between text-[10px] font-mono text-slate-800">
                        <span className="font-semibold">{stroke.label}</span>
                        <span className="text-cyan-800 font-bold">
                          {idx === 0 ? 'RxNorm: 213169' : idx === 1 ? 'RxNorm: 284635' : 'RxNorm: 161'}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Bottom Footer on Physical Slip: Doctor Signature & Clinic Stamp */}
            <div className="border-t border-slate-300/80 pt-2 mt-3 flex justify-between items-end text-[9px] font-mono text-slate-600">
              <div className="space-y-0.5">
                <div className="inline-block px-2 py-0.5 rounded border border-slate-400/60 bg-slate-100 font-bold text-[8px] text-slate-700">
                  {canvasData.clinicStampText}
                </div>
                <div>Ground Truth: Signed Prescriber Copy</div>
              </div>

              {/* Doctor Signature SVG */}
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

        {/* Right: Diagnostic Clinical Intelligence Telemetry Panel */}
        <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
          {/* Stage 0: Physical Document Ingestion */}
          {currentStage === 0 && (
            <div className="h-full flex flex-col justify-between p-5 rounded-lg bg-[#0F1420] border border-white/[0.08] space-y-4">
              <div>
                <Badge variant="cyan" size="xs" dot className="mb-2">
                  Telemetry Layer 01: Optical Intake
                </Badge>
                <h4 className="text-base font-bold text-white tracking-tight font-sans">
                  Authentic Clinical Handwriting Ingestion
                </h4>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
                  The system ingests high-resolution flatbed or mobile scans of standard doctor prescription pads. Physical ink variations, cursive baseline slant, and clinical shorthand are preserved verbatim as the legal primary source.
                </p>
              </div>

              <div className="p-3.5 rounded bg-black/40 border border-white/5 space-y-2 font-mono text-xs text-slate-400">
                <div className="flex justify-between text-[11px]">
                  <span>Sensor Stream:</span>
                  <span className="text-cyan-300 font-semibold">Flatbed Bi-tonal Optical</span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span>Physical Paper Medium:</span>
                  <span className="text-slate-200">Standard Outpatient Rx Pad</span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span>Ink Pigment Analysis:</span>
                  <span className="text-emerald-400 font-semibold">Ballpoint Blue (Solvent Base)</span>
                </div>
              </div>

              <button
                onClick={() => onSelectStage(1)}
                className="w-full py-2.5 px-4 rounded bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 text-xs font-mono font-semibold flex items-center justify-center gap-2 border border-cyan-500/40 transition-all cursor-pointer"
              >
                <span>Run Bounding Box Localization</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Stage 1: Spatial Bounding & Entity Extraction */}
          {currentStage === 1 && (
            <div className="h-full flex flex-col justify-between p-5 rounded-lg bg-[#0F1420] border border-white/[0.08] space-y-4">
              <div>
                <Badge variant="teal" size="xs" dot className="mb-2">
                  Telemetry Layer 02: Spatial Bounding
                </Badge>
                <h4 className="text-base font-bold text-white tracking-tight font-sans">
                  Bounding Polygon Segmentation
                </h4>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
                  Vision Transformer heads isolate medication lines, classifying tokens into entity categories: Drug Name, Dosage Strength, Frequency shorthand, and Food Relations.
                </p>
              </div>

              <div className="space-y-2 font-mono text-xs">
                <div className="p-2.5 rounded bg-black/40 border border-white/5 flex justify-between">
                  <span className="text-slate-400">Entity 1:</span>
                  <span className="text-cyan-300 font-bold">Augmentin 625 Duo [Oral Tab]</span>
                </div>
                <div className="p-2.5 rounded bg-black/40 border border-white/5 flex justify-between">
                  <span className="text-slate-400">Posology Shorthand:</span>
                  <span className="text-slate-200">1-0-1 (Twice Daily) PC</span>
                </div>
                <div className="p-2.5 rounded bg-black/40 border border-white/5 flex justify-between">
                  <span className="text-slate-400">Polygon Precision:</span>
                  <span className="text-emerald-400 font-semibold">98.2% IoU</span>
                </div>
              </div>

              <button
                onClick={() => onSelectStage(2)}
                className="w-full py-2.5 px-4 rounded bg-teal-950/60 hover:bg-teal-900/60 text-teal-300 text-xs font-mono font-semibold flex items-center justify-center gap-2 border border-teal-500/40 transition-all cursor-pointer"
              >
                <span>Validate Against Pharmacopeias</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Stage 2: Ontology Grounding */}
          {currentStage === 2 && (
            <div className="h-full flex flex-col justify-between p-5 rounded-lg bg-[#0F1420] border border-white/[0.08] space-y-4">
              <div>
                <Badge variant="emerald" size="xs" dot className="mb-2">
                  Telemetry Layer 03: Ontology Linking
                </Badge>
                <h4 className="text-base font-bold text-white tracking-tight font-sans">
                  CDSCO & RxNorm Pharmacopeia Verification
                </h4>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
                  Extracted text candidates are validated against approved Indian CDSCO formulations and US NLM RxNorm concepts. Disallowed or hallucinated salts are rejected.
                </p>
              </div>

              <div className="p-3.5 rounded bg-emerald-950/20 border border-emerald-500/30 space-y-2 text-xs font-mono">
                <div className="flex items-center gap-2 text-emerald-400 font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approved Drug Salt Combination</span>
                </div>
                <div className="text-slate-300 text-[11px]">
                  Amoxicillin (500mg) + Clavulanic Acid (125mg)
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 pt-1 border-t border-emerald-500/20">
                  <span>RxNorm CUI: 213169</span>
                  <span>ATC: J01CR02</span>
                </div>
              </div>

              <button
                onClick={() => onSelectStage(3)}
                className="w-full py-2.5 px-4 rounded bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 text-xs font-mono font-semibold flex items-center justify-center gap-2 border border-emerald-500/40 transition-all cursor-pointer"
              >
                <span>Check Selective Uncertainty Gate</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Stage 3: Calibrated Uncertainty */}
          {currentStage === 3 && (
            <div className="h-full flex flex-col justify-between p-5 rounded-lg bg-[#0F1420] border border-white/[0.08] space-y-4">
              <div>
                <Badge variant="amber" size="xs" dot className="mb-2">
                  Telemetry Layer 04: Calibrated Safety Gate
                </Badge>
                <h4 className="text-base font-bold text-white tracking-tight font-sans">
                  Entropy Measurement & Abstention Gate
                </h4>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
                  The model evaluates token predictive entropy. If ink degradation introduces ambiguity, the system abstains from autonomous guessing and flags mandatory human review.
                </p>
              </div>

              <div className="space-y-2">
                <div className="p-3 rounded bg-black/40 border border-white/5 space-y-1 font-mono text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Calibrated Confidence:</span>
                    <span className="text-emerald-400 font-bold">94.2% (Passed)</span>
                  </div>
                  <ConfidenceMeter score={0.942} showLabel={false} threshold={0.65} />
                </div>
                <div className="p-2.5 rounded bg-black/40 border border-white/5 text-[11px] font-mono text-slate-300 flex justify-between">
                  <span>LASA Orthographic Overlap:</span>
                  <span className="text-emerald-400">None (Safe margin)</span>
                </div>
              </div>

              <button
                onClick={() => onSelectStage(4)}
                className="w-full py-2.5 px-4 rounded bg-amber-950/60 hover:bg-amber-900/60 text-amber-300 text-xs font-mono font-semibold flex items-center justify-center gap-2 border border-amber-500/40 transition-all cursor-pointer"
              >
                <span>View Patient Vernacular Guidance</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Stage 4: Vernacular Explanation */}
          {currentStage === 4 && (
            <div className="h-full flex flex-col justify-between p-5 rounded-lg bg-[#0F1420] border border-white/[0.08] space-y-4">
              <div>
                <Badge variant="cyan" size="xs" dot className="mb-2">
                  Telemetry Layer 05: Vernacular Posology
                </Badge>
                <h4 className="text-base font-bold text-white tracking-tight font-sans">
                  Accessible Patient Posology
                </h4>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
                  Clinical Latin abbreviations (&ldquo;1-0-1 PC&rdquo;) are synthesized into clear, meal-correlated instructions in English, Hindi, or Marathi.
                </p>
              </div>

              <div className="p-3.5 rounded bg-cyan-950/20 border border-cyan-500/30 space-y-1.5 text-xs font-mono">
                <div className="text-cyan-300 font-bold">मराठी / हिन्दी / English Guide</div>
                <div className="text-slate-300 text-[11px]">
                  ☀️ <strong>सकाळी:</strong> १ गोळी (नाश्त्यानंतर २० मिनिटांनी)
                </div>
                <div className="text-slate-300 text-[11px]">
                  🌙 <strong>रात्री:</strong> १ गोळी (जेवणानंतर) · ५ दिवस पूर्ण करा
                </div>
              </div>

              <button
                onClick={() => onSelectStage(0)}
                className="w-full py-2.5 px-4 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold flex items-center justify-center gap-2 border border-white/10 transition-all cursor-pointer"
              >
                <span>Reset Workflow Inspection</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
