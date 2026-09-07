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
      className={`rounded-2xl border border-theme bg-surface shadow-xs flex flex-col transition-all duration-200 ${
        isFullscreen
          ? 'fixed inset-4 z-50 bg-surface/95 backdrop-blur-md flex flex-col p-4 border-theme shadow-2xl'
          : 'relative w-full'
      }`}
    >
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-surface-subtle border-b border-theme text-xs">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          <span className="font-semibold text-theme-primary">
            Original script · <span className="font-mono text-xs">{accessionId}</span>
          </span>
          <span className="hidden sm:inline text-theme-muted">|</span>
          <span className="hidden sm:inline text-theme-secondary text-xs">
            Doctor reference
          </span>
        </div>

        {/* Optical Controls */}
        <div className="flex items-center gap-1">
          <span className="text-xs text-theme-muted font-mono mr-2">{zoomLevel}%</span>
          <button
            onClick={handleZoomOut}
            disabled={zoomLevel <= 70}
            aria-label="Zoom Out"
            className="p-1 rounded-lg bg-surface border border-theme text-theme-secondary hover:text-theme-primary disabled:opacity-40 cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleResetZoom}
            aria-label="Reset Zoom"
            className="p-1 rounded-lg bg-surface border border-theme text-theme-secondary hover:text-theme-primary cursor-pointer"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomIn}
            disabled={zoomLevel >= 220}
            aria-label="Zoom In"
            className="p-1 rounded-lg bg-surface border border-theme text-theme-secondary hover:text-theme-primary disabled:opacity-40 cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            aria-label={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            className="p-1 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-300 dark:border-teal-700 text-teal-700 dark:text-teal-300 hover:text-teal-800 cursor-pointer ml-1"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen View'}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Main Inspection Canvas */}
      <div
        className={`relative overflow-auto bg-canvas p-4 sm:p-6 flex items-center justify-center select-none ${
          isFullscreen ? 'flex-1 min-h-0' : 'min-h-[460px] sm:min-h-[520px]'
        }`}
      >
        {/* Subtle Framing Reticles */}
        <div className="absolute top-3 left-3 w-4 h-4 border-t border-l border-theme pointer-events-none" />
        <div className="absolute top-3 right-3 w-4 h-4 border-t border-r border-theme pointer-events-none" />
        <div className="absolute bottom-3 left-3 w-4 h-4 border-b border-l border-theme pointer-events-none" />
        <div className="absolute bottom-3 right-3 w-4 h-4 border-b border-r border-theme pointer-events-none" />

        {/* Prescription Surface */}
        <div
          className="transition-transform duration-200 ease-out origin-center relative max-w-full"
          style={{ transform: `scale(${zoomLevel / 100})` }}
        >
          {previewUrl ? (
            <div className="relative rounded-xl border border-theme shadow-md overflow-hidden bg-white">
              <img
                src={previewUrl}
                alt="Original handwritten prescription"
                className="max-h-[500px] w-auto object-contain block"
              />
              {activeBoundingBox && (
                <div
                  className="absolute border-2 border-sky-500 bg-sky-500/10 rounded-md pointer-events-none transition-all duration-200 ring-2 ring-sky-500/40"
                  style={{
                    top: `${activeBoundingBox.y}%`,
                    left: `${activeBoundingBox.x}%`,
                    width: `${activeBoundingBox.width}%`,
                    height: `${activeBoundingBox.height}%`,
                  }}
                >
                  <span className="absolute -top-4 left-1 px-1.5 py-0.2 bg-surface text-[9px] font-medium text-teal-700 dark:text-teal-300 rounded border border-theme shadow-xs">
                    {highlightLabel || 'Active Stroke'}
                  </span>
                </div>
              )}
            </div>
          ) : (
            /* Curated Clinical Script Canvas */
            <div className="prescription-paper shadow-paper p-6 sm:p-8 text-slate-900 w-[580px] max-w-full rounded-2xl relative border border-amber-900/15 dark:border-white/15">
              {/* Clinic Letterhead */}
              <div className="border-b border-slate-300 pb-2 mb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-sm text-slate-950 tracking-tight font-sans">
                      {canvas.doctorHeader.name}
                    </h3>
                    <p className="text-[11px] text-slate-600">{canvas.doctorHeader.qualifications}</p>
                    <p className="text-[10px] text-slate-500 font-mono">{canvas.doctorHeader.regNo}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[11px] text-teal-800 tracking-wide">
                      {canvas.doctorHeader.clinicName}
                    </p>
                    <p className="text-[10px] text-slate-600">{canvas.doctorHeader.clinicAddress}</p>
                    <p className="text-[10px] text-slate-500 font-mono">{canvas.doctorHeader.phone}</p>
                  </div>
                </div>
              </div>

              {/* Patient Profile Bar */}
              <div className="bg-amber-900/5 rounded-lg px-3 py-1.5 mb-4 border border-amber-900/10 flex justify-between items-center text-xs font-sans text-slate-800">
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
              <div className="space-y-4 relative py-2 min-h-[200px]">
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
                        className="drop-shadow-xs"
                      />
                    </g>
                  ))}
                </svg>

                {/* Dynamic Coordinate Highlight Box */}
                {activeBoundingBox && (
                  <div
                    className="absolute border-2 border-teal-600 bg-teal-500/15 rounded-md pointer-events-none transition-all duration-200 ring-2 ring-teal-500/30"
                    style={{
                      top: `${activeBoundingBox.y}%`,
                      left: `${activeBoundingBox.x}%`,
                      width: `${activeBoundingBox.width}%`,
                      height: `${activeBoundingBox.height}%`,
                    }}
                  >
                    <div className="absolute -top-4 left-1 px-1.5 py-0.2 bg-surface text-[9px] font-medium text-teal-700 dark:text-teal-300 rounded border border-theme flex items-center gap-1 shadow-xs">
                      <Crosshair className="w-2.5 h-2.5" />
                      <span>{highlightLabel || 'Recognized Line'}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Prescriber Signature & Stamp */}
              <div className="mt-4 pt-3 border-t border-slate-300 flex justify-between items-end text-xs text-slate-600">
                <div className="border border-red-300/80 rounded px-2 py-1 bg-red-50/70 font-mono text-[10px] text-red-900 font-semibold">
                  {canvas.clinicStampText}
                </div>
                <div className="text-right">
                  <svg viewBox="0 0 200 60" className="w-28 h-8 inline-block">
                    <path
                      d={canvas.doctorSignaturePath}
                      fill="none"
                      stroke="#1E3A8A"
                      strokeWidth="2.4"
                      strokeLinecap="round"
                    />
                  </svg>
                  <p className="text-[10px] text-slate-500 font-mono">Physician Signature</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Notice Strip */}
      <div className="px-4 py-2 bg-surface-subtle border-t border-theme flex items-center justify-between text-xs text-theme-muted">
        <div className="flex items-center gap-1.5">
          <FileCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
          <span>Original physician document preserved as primary legal record</span>
        </div>
      </div>
    </div>
  );
};
