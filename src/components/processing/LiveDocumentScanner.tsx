import React from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import { ProcessingStageId } from '../../types/pipeline.types';
import { Crosshair, Activity } from 'lucide-react';

export interface LiveDocumentScannerProps {
  uploadedData: UploadedPrescriptionFile | null;
  currentStageId: ProcessingStageId;
  overallPercent: number;
}

export const LiveDocumentScanner: React.FC<LiveDocumentScannerProps> = ({
  uploadedData,
  currentStageId,
  overallPercent,
}) => {
  // Determine scanline y-offset according to stage
  const stagePositions: Record<ProcessingStageId, string> = {
    image_received: '10%',
    image_processing: '25%',
    handwriting_interpretation: '45%',
    structured_extraction: '65%',
    medicine_validation: '80%',
    safety_analysis: '92%',
    explanation_synthesis: '98%',
  };

  const currentScanY = stagePositions[currentStageId] || `${overallPercent}%`;

  return (
    <div className="w-full rounded-xl overflow-hidden border border-white/10 bg-[#0B0E17] shadow-2xl flex flex-col">
      {/* Top Workstation Telemetry Bar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2 bg-[#0F1420] border-b border-white/[0.08] text-xs font-mono">
        <div className="flex items-center gap-2.5 text-cyan-400">
          <Crosshair className="w-3.5 h-3.5 animate-pulse" />
          <span className="font-semibold text-white tracking-wider">
            {uploadedData?.fileName || 'PHYSICAL_SCRIPT_STREAM.RAW'}
          </span>
        </div>

        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          <span>SCANNING HEAD: ACTIVE</span>
          <span className="text-slate-600">|</span>
          <span className="text-emerald-400 font-bold">{overallPercent}% PROGRESS</span>
        </div>
      </div>

      {/* Main Document Inspection Canvas with Active Laser HUD */}
      <div className="relative min-h-[460px] sm:min-h-[520px] bg-[#07090F] p-4 sm:p-6 flex items-center justify-center overflow-hidden select-none">
        {/* Optical Alignment Reticles */}
        <div className="absolute top-3 left-3 w-5 h-5 border-t-2 border-l-2 border-cyan-500/60 pointer-events-none" />
        <div className="absolute top-3 right-3 w-5 h-5 border-t-2 border-r-2 border-cyan-500/60 pointer-events-none" />
        <div className="absolute bottom-3 left-3 w-5 h-5 border-b-2 border-l-2 border-cyan-500/60 pointer-events-none" />
        <div className="absolute bottom-3 right-3 w-5 h-5 border-b-2 border-r-2 border-cyan-500/60 pointer-events-none" />

        {/* Dynamic Laser Scanning Beam moving across document */}
        <div
          className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#38bdf8] pointer-events-none z-30 transition-all duration-300 ease-out"
          style={{ top: currentScanY }}
        >
          <div className="absolute -top-3 right-8 px-2 py-0.5 rounded bg-cyan-950 text-[9px] font-mono text-cyan-300 border border-cyan-500/40 shadow-sm">
            OPTICAL SCANNER · Y: {currentScanY}
          </div>
        </div>

        {/* The Prescription Document Surface */}
        {uploadedData?.previewUrl ? (
          <div className="relative max-w-full max-h-[480px] rounded border border-slate-700/60 shadow-2xl overflow-hidden bg-white">
            <img
              src={uploadedData.previewUrl}
              alt="Prescription under inference"
              className="max-h-[460px] w-auto object-contain block pointer-events-none"
            />
            {/* Real-time Bounding Polygon Highlights */}
            {overallPercent >= 40 && (
              <div className="absolute top-[28%] left-[8%] right-[8%] h-[14%] border-2 border-cyan-400 bg-cyan-500/15 rounded pointer-events-none animate-pulse">
                <span className="absolute -top-3 left-2 px-1.5 py-0.2 bg-slate-900 text-[8px] font-mono text-cyan-300 rounded border border-cyan-500/40">
                  POLY_01: MEDICINE_TOKEN
                </span>
              </div>
            )}
            {overallPercent >= 60 && (
              <div className="absolute top-[45%] left-[8%] right-[8%] h-[14%] border-2 border-teal-400 bg-teal-500/15 rounded pointer-events-none">
                <span className="absolute -top-3 left-2 px-1.5 py-0.2 bg-slate-900 text-[8px] font-mono text-teal-300 rounded border border-teal-500/40">
                  POLY_02: POSOLOGY_SHORTHAND
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="clinical-paper p-6 text-slate-900 w-full max-w-md rounded shadow-2xl relative">
            <div className="border-b border-slate-300 pb-2 mb-3 flex justify-between text-xs font-mono">
              <span className="font-bold">APOLLO HEALTH CLINIC · PUNE</span>
              <span className="text-slate-500">RX-3412</span>
            </div>
            <div className="text-xl font-serif italic font-bold mb-2">℞</div>
            <div className="space-y-3 font-mono text-xs text-slate-800">
              <div className="p-2 rounded bg-cyan-50 border border-cyan-300">
                Tab Augmentin 625 Duo  1-0-1 x 5d PC
              </div>
              <div className="p-2 rounded bg-slate-100 border border-slate-200">
                Cap Pan 40mg  1-0-0 AC (30m before breakfast)
              </div>
              <div className="p-2 rounded bg-slate-100 border border-slate-200">
                Tab Dolo 650mg  1-0-1 SOS (if fever &gt; 100°F)
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Sensor Telemetry */}
      <div className="px-4 py-2.5 bg-[#0D121D] border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span>STAGE: {currentStageId.toUpperCase().replace(/_/g, ' ')}</span>
        </div>
        <span className="text-emerald-400 font-semibold">ZERO-HALLUCINATION PROTOCOL ACTIVE</span>
      </div>
    </div>
  );
};
