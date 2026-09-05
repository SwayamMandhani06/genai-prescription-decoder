import React, { useState } from 'react';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import { BoundingBox } from '../../types/prescription.types';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  RotateCcw,
  Eye,
  FileCheck,
  Crosshair,
} from 'lucide-react';

export interface OriginalScriptViewerProps {
  scriptKey: string;
  previewUrl?: string;
  activeBoundingBox?: BoundingBox | null;
  highlightLabel?: string;
  accessionId: string;
}

export const OriginalScriptViewer: React.FC<OriginalScriptViewerProps> = ({
  scriptKey,
  previewUrl,
  activeBoundingBox,
  highlightLabel,
  accessionId,
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const canvas = SAMPLE_PRESCRIPTION_CANVASES[scriptKey] || SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];

  const handleZoomIn = () => setZoomLevel((z) => Math.min(220, z + 20));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(70, z - 20));
  const handleResetZoom = () => setZoomLevel(100);

  return (
    <div
      className={`rounded-xl border border-white/10 bg-[#0B0E17] shadow-2xl flex flex-col transition-all duration-200 ${
        isFullscreen
          ? 'fixed inset-4 z-50 bg-[#07090F]/95 backdrop-blur-2xl flex flex-col p-4 border-cyan-500/40 shadow-[0_0_50px_rgba(0,0,0,0.8)]'
          : 'relative w-full'
      }`}
    >
      {/* Workstation Header Bar */}
      <div className="flex flex-wrap items-center justify-between px-3.5 py-2.5 bg-[#0F1420] border-b border-white/[0.08] text-xs font-mono">
        <div className="flex items-center gap-2 text-cyan-400">
          <Eye className="w-4 h-4 text-cyan-400" />
          <span className="font-bold text-white tracking-wider">
            ORIGINAL SCRIPT · {accessionId}
          </span>
          <span className="hidden sm:inline text-slate-500">|</span>
          <span className="hidden sm:inline text-emerald-400 text-[11px] font-semibold">
            GROUND TRUTH REFERENCE
          </span>
        </div>

        {/* Optical Controls (Zoom, Fit, Fullscreen) */}
        <div className="flex items-center gap-1">
          <span className="text-[11px] text-slate-400 font-mono mr-2">{zoomLevel}%</span>
          <button
            onClick={handleZoomOut}
            disabled={zoomLevel <= 70}
            aria-label="Zoom Out"
            className="p-1.5 rounded bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white disabled:opacity-40 cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleResetZoom}
            aria-label="Reset Zoom"
            className="p-1.5 rounded bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white cursor-pointer"
            title="Reset Zoom (100%)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomIn}
            disabled={zoomLevel >= 220}
            aria-label="Zoom In"
            className="p-1.5 rounded bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 hover:text-white disabled:opacity-40 cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            aria-label={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            className="p-1.5 rounded bg-cyan-950/60 border border-cyan-500/40 text-cyan-300 hover:text-white cursor-pointer ml-1"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen View'}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Main Inspection Canvas */}
      <div
        className={`relative overflow-auto bg-[#07090F] p-4 sm:p-6 flex items-center justify-center select-none ${
          isFullscreen ? 'flex-1 min-h-0' : 'min-h-[460px] sm:min-h-[540px]'
        }`}
      >
        {/* Reticles */}
        <div className="absolute top-3 left-3 w-4 h-4 border-t border-l border-cyan-500/40 pointer-events-none" />
        <div className="absolute top-3 right-3 w-4 h-4 border-t border-r border-cyan-500/40 pointer-events-none" />
        <div className="absolute bottom-3 left-3 w-4 h-4 border-b border-l border-cyan-500/40 pointer-events-none" />
        <div className="absolute bottom-3 right-3 w-4 h-4 border-b border-r border-cyan-500/40 pointer-events-none" />

        {/* Prescription Surface */}
        <div
          className="transition-transform duration-200 ease-out origin-center relative max-w-full"
          style={{ transform: `scale(${zoomLevel / 100})` }}
        >
          {previewUrl ? (
            <div className="relative rounded border border-slate-700/60 shadow-2xl overflow-hidden bg-white">
              <img
                src={previewUrl}
                alt="Original handwritten prescription"
                className="max-h-[500px] w-auto object-contain block"
              />
              {/* Active synchronized bounding box */}
              {activeBoundingBox && (
                <div
                  className="absolute border-2 border-cyan-400 bg-cyan-500/20 rounded pointer-events-none transition-all duration-200 animate-pulse shadow-[0_0_12px_#38bdf8]"
                  style={{
                    top: `${activeBoundingBox.y}%`,
                    left: `${activeBoundingBox.x}%`,
                    width: `${activeBoundingBox.width}%`,
                    height: `${activeBoundingBox.height}%`,
                  }}
                >
                  <span className="absolute -top-4 left-1 px-1.5 py-0.2 bg-slate-900 text-[8px] font-mono text-cyan-300 rounded border border-cyan-500/40">
                    {highlightLabel || 'ACTIVE_ENTITY'}
                  </span>
                </div>
              )}
            </div>
          ) : (
            /* Curated Clinical Script Canvas */
            <div className="clinical-paper p-5 sm:p-7 text-slate-900 w-[580px] max-w-full rounded-md shadow-2xl relative border border-slate-300">
              {/* Clinic Letterhead */}
              <div className="border-b-2 border-slate-400 pb-2 mb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-sm text-slate-950 tracking-tight font-sans">
                      {canvas.doctorHeader.name}
                    </h3>
                    <p className="text-[11px] text-slate-700">{canvas.doctorHeader.qualifications}</p>
                    <p className="text-[10px] text-slate-500 font-mono">{canvas.doctorHeader.regNo}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[11px] text-cyan-900 tracking-wide">
                      {canvas.doctorHeader.clinicName}
                    </p>
                    <p className="text-[10px] text-slate-600">{canvas.doctorHeader.clinicAddress}</p>
                    <p className="text-[10px] text-slate-500 font-mono">{canvas.doctorHeader.phone}</p>
                  </div>
                </div>
              </div>

              {/* Patient Profile Bar */}
              <div className="bg-slate-100/90 rounded px-2.5 py-1.5 mb-4 border border-slate-200 flex justify-between items-center text-[11px] font-sans">
                <div>
                  <span className="text-slate-500 mr-1">Patient:</span>
                  <strong className="text-slate-900">{canvas.patientInfo.name}</strong>
                  <span className="text-slate-400 mx-1.5">|</span>
                  <span className="text-slate-700">{canvas.patientInfo.ageGender}</span>
                </div>
                <div>
                  <span className="text-slate-500 mr-1">Date:</span>
                  <strong className="text-slate-800 font-mono">{canvas.patientInfo.date}</strong>
                </div>
              </div>

              {/* Rx Symbol */}
              <div className="text-2xl font-serif italic font-bold text-slate-900 mb-2">℞</div>

              {/* Ruled lines with SVG Cursive Ink Strokes */}
              <div className="space-y-4 relative py-2 min-h-[220px]">
                {/* Horizontal guide lines */}
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-30">
                  <div className="border-b border-cyan-400/40 w-full h-8" />
                  <div className="border-b border-cyan-400/40 w-full h-8" />
                  <div className="border-b border-cyan-400/40 w-full h-8" />
                  <div className="border-b border-cyan-400/40 w-full h-8" />
                </div>

                {/* SVG Stroke paths */}
                <svg
                  viewBox="0 0 600 240"
                  className="w-full h-44 pointer-events-none overflow-visible"
                >
                  {canvas.strokes.map((stroke) => (
                    <g key={stroke.id}>
                      <path
                        d={stroke.svgPath}
                        fill="none"
                        stroke={stroke.inkColor}
                        strokeWidth="3.2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="drop-shadow-sm"
                      />
                    </g>
                  ))}
                </svg>

                {/* Dynamic Coordinate Highlight Box */}
                {activeBoundingBox && (
                  <div
                    className="absolute border-2 border-cyan-500 bg-cyan-500/15 rounded pointer-events-none transition-all duration-200 animate-pulse shadow-[0_0_14px_rgba(14,165,233,0.5)]"
                    style={{
                      top: `${activeBoundingBox.y}%`,
                      left: `${activeBoundingBox.x}%`,
                      width: `${activeBoundingBox.width}%`,
                      height: `${activeBoundingBox.height}%`,
                    }}
                  >
                    <div className="absolute -top-4 left-1 px-1.5 py-0.2 bg-slate-900 text-[8px] font-mono text-cyan-300 rounded border border-cyan-500/40 flex items-center gap-1 shadow">
                      <Crosshair className="w-2.5 h-2.5" />
                      <span>{highlightLabel || 'ENTITY_STROKE'}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Prescriber Signature & Clinic Stamp */}
              <div className="mt-5 pt-3 border-t border-slate-300 flex justify-between items-end text-[10px] text-slate-600 font-sans">
                <div className="border border-slate-300 rounded px-2 py-1 bg-white/70 font-mono text-[9px] text-slate-700">
                  {canvas.clinicStampText}
                </div>
                <div className="text-right">
                  <svg viewBox="0 0 200 60" className="w-32 h-10 inline-block">
                    <path
                      d={canvas.doctorSignaturePath}
                      fill="none"
                      stroke="#1E3A8A"
                      strokeWidth="2.4"
                      strokeLinecap="round"
                    />
                  </svg>
                  <p className="text-[9px] text-slate-500 font-mono">Prescriber Digital Signature</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Sensor Telemetry Strip */}
      <div className="px-3.5 py-2 bg-[#0D121D] border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-1.5">
          <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>ORIGINAL SCRIPT PRESERVED AS LEGAL GROUND TRUTH</span>
        </div>
        <span className="text-slate-500 hidden sm:inline">300 DPI · FLATBED RAW STREAM</span>
      </div>
    </div>
  );
};
