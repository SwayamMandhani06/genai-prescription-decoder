import React, { useRef, useState } from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import {
  Camera,
  UploadCloud,
  Crosshair,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export interface OpticalViewfinderCanvasProps {
  uploadedData: UploadedPrescriptionFile | null;
  onFileSelect: (file: File) => void;
  onRemoveFile: () => void;
  isAnalyzing?: boolean;
  errorMessage?: string | null;
}

export const OpticalViewfinderCanvas: React.FC<OpticalViewfinderCanvasProps> = ({
  uploadedData,
  onFileSelect,
  onRemoveFile,
  isAnalyzing = false,
  errorMessage = null,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      onFileSelect(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  const resetZoom = () => setZoomLevel(1);
  const zoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.25, 2.5));
  const zoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.25, 0.75));

  return (
    <div className="w-full relative rounded-xl overflow-hidden border border-white/10 bg-[#0B0E17] shadow-2xl">
      {/* Top Viewfinder Telemetry Header */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-[#0F1420] border-b border-white/[0.08] text-xs font-mono gap-2">
        <div className="flex items-center gap-2.5 text-cyan-400">
          <Crosshair className="w-3.5 h-3.5" />
          <span className="font-semibold text-white tracking-wider">
            {uploadedData ? 'OPTICAL STAGE: INTAKE ACTIVE' : 'OPTICAL STAGE: AWAITING DOCUMENT'}
          </span>
          {uploadedData && (
            <Badge variant="cyan" size="xs">
              {`${uploadedData.metrics.width}×${uploadedData.metrics.height}px`}
            </Badge>
          )}
        </div>

        {/* Viewfinder Controls when image is loaded */}
        {uploadedData && (
          <div className="flex items-center gap-1">
            <button
              onClick={zoomOut}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-white/5 transition-colors"
              title="Zoom out"
              aria-label="Zoom out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] text-slate-400 px-1 font-mono min-w-[45px] text-center">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              onClick={zoomIn}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-white/5 transition-colors"
              title="Zoom in"
              aria-label="Zoom in"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={resetZoom}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-white/5 transition-colors ml-1"
              title="Reset optical focal scale"
              aria-label="Reset zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onRemoveFile}
              className="p-1 text-red-400 hover:text-red-300 rounded hover:bg-red-500/10 transition-colors ml-2"
              title="Remove document"
              aria-label="Remove document"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Main Optical Canvas Stage */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative min-h-[440px] sm:min-h-[500px] flex items-center justify-center p-6 sm:p-8 transition-all overflow-hidden ${
          isDragging
            ? 'bg-cyan-950/20 border-2 border-cyan-400 ring-4 ring-cyan-500/20'
            : 'bg-[#080A12]'
        }`}
      >
        {/* Optical Alignment Reticles (Corner L-Brackets) */}
        <div className="absolute top-4 left-4 w-6 h-6 border-t-2 border-l-2 border-cyan-500/60 pointer-events-none" />
        <div className="absolute top-4 right-4 w-6 h-6 border-t-2 border-r-2 border-cyan-500/60 pointer-events-none" />
        <div className="absolute bottom-4 left-4 w-6 h-6 border-b-2 border-l-2 border-cyan-500/60 pointer-events-none" />
        <div className="absolute bottom-4 right-4 w-6 h-6 border-b-2 border-r-2 border-cyan-500/60 pointer-events-none" />

        {/* Center Optical Crosshair (Subtle watermark) */}
        {!uploadedData && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
            <div className="w-16 h-16 border border-dashed border-cyan-400 rounded-full flex items-center justify-center">
              <div className="w-2 h-2 bg-cyan-400 rounded-full" />
            </div>
            <div className="absolute w-32 h-[1px] bg-cyan-400/40" />
            <div className="absolute h-32 w-[1px] bg-cyan-400/40" />
          </div>
        )}

        {/* State A: Document Loaded & Mounted */}
        {uploadedData ? (
          <div className="relative max-w-full max-h-[560px] overflow-auto flex items-center justify-center z-10 select-none">
            {/* HUD Scanning Line during analysis */}
            {isAnalyzing && (
              <div className="absolute left-0 right-0 h-0.5 bg-cyan-400 shadow-[0_0_12px_#38bdf8] pointer-events-none animate-hud-scanline z-30 opacity-90" />
            )}

            {/* Document Image Surface */}
            <div
              className="transition-transform duration-200 ease-out origin-center rounded border border-slate-700/60 shadow-2xl overflow-hidden bg-white"
              style={{ transform: `scale(${zoomLevel})` }}
            >
              <img
                src={uploadedData.previewUrl}
                alt="Prescription document preview"
                className="max-h-[500px] w-auto object-contain block pointer-events-none"
              />
            </div>
          </div>
        ) : (
          /* State B: Empty Optical Focal Zone ("Bring the prescription into focus") */
          <div className="text-center max-w-md mx-auto space-y-5 z-10 py-6">
            <div className="w-16 h-16 rounded-2xl bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-center mx-auto text-cyan-400 shadow-inner">
              <UploadCloud className="w-8 h-8 animate-pulse" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg sm:text-xl font-bold text-white font-sans tracking-tight">
                Bring the prescription into focus.
              </h3>
              <p className="text-xs sm:text-sm text-slate-300 font-sans leading-relaxed">
                Drag and drop your physician&rsquo;s handwritten script onto the optical focal stage, or select an image scan from your device.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                size="md"
                onClick={() => fileInputRef.current?.click()}
                leftIcon={<UploadCloud className="w-4 h-4 text-slate-950" />}
              >
                Select from Device
              </Button>

              <Button
                variant="secondary"
                size="md"
                onClick={() => cameraInputRef.current?.click()}
                leftIcon={<Camera className="w-4 h-4 text-slate-300" />}
              >
                Scan with Camera
              </Button>
            </div>

            {/* Supported Formats & Technical Specs */}
            <div className="pt-4 border-t border-white/5 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[11px] font-mono text-slate-400">
              <span>Formats: JPEG, PNG, WEBP, TIFF, PDF</span>
              <span>·</span>
              <span>Max: 15 MB</span>
              <span>·</span>
              <span>Recommended: &ge; 300 DPI</span>
            </div>
          </div>
        )}

        {/* Hidden File Input for Device Browsing */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/tiff,application/pdf"
          className="hidden"
          onChange={handleFileChange}
          aria-label="Upload prescription file"
        />

        {/* Hidden Camera Input with environment capture for mobile */}
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleFileChange}
          aria-label="Capture prescription photo"
        />
      </div>

      {/* Error Message Strip */}
      {errorMessage && (
        <div className="p-3 bg-red-950/50 border-t border-red-500/40 text-red-200 text-xs font-mono flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};
