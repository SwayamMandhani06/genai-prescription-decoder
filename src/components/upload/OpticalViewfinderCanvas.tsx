import React, { useRef, useState } from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import {
  Camera,
  UploadCloud,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Trash2,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';
import { Button } from '../ui/Button';

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
    <div className="w-full relative rounded-2xl overflow-hidden border border-theme bg-surface shadow-xs transition-colors">
      {/* Top Viewfinder Control Bar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-surface-subtle border-b border-theme text-xs gap-2">
        <div className="flex items-center gap-2">
          <FileCheck2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          <span className="font-semibold text-theme-primary">
            {uploadedData ? 'Prescription Document Mounted' : 'Prescription Viewfinder'}
          </span>
          {uploadedData && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface border border-theme text-theme-secondary">
              {`${uploadedData.metrics.width}×${uploadedData.metrics.height}px`}
            </span>
          )}
        </div>

        {/* Viewfinder Controls when image is loaded */}
        {uploadedData && (
          <div className="flex items-center gap-1">
            <button
              onClick={zoomOut}
              className="p-1 text-theme-secondary hover:text-theme-primary rounded hover:bg-surface transition-colors cursor-pointer"
              title="Zoom out"
              aria-label="Zoom out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-[11px] text-theme-secondary px-1 font-mono min-w-[45px] text-center">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              onClick={zoomIn}
              className="p-1 text-theme-secondary hover:text-theme-primary rounded hover:bg-surface transition-colors cursor-pointer"
              title="Zoom in"
              aria-label="Zoom in"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={resetZoom}
              className="p-1 text-theme-secondary hover:text-theme-primary rounded hover:bg-surface transition-colors ml-1 cursor-pointer"
              title="Reset optical scale"
              aria-label="Reset zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onRemoveFile}
              className="p-1 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 rounded hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors ml-2 cursor-pointer"
              title="Remove document"
              aria-label="Remove document"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Main Optical Canvas Stage */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative min-h-[420px] sm:min-h-[480px] flex items-center justify-center p-6 sm:p-8 transition-all overflow-hidden ${
          isDragging
            ? 'bg-teal-50/50 dark:bg-teal-950/20 border-2 border-teal-500'
            : 'bg-canvas'
        }`}
      >
        {/* Subtle Framing Reticles */}
        <div className="absolute top-4 left-4 w-5 h-5 border-t border-l border-theme pointer-events-none" />
        <div className="absolute top-4 right-4 w-5 h-5 border-t border-r border-theme pointer-events-none" />
        <div className="absolute bottom-4 left-4 w-5 h-5 border-b border-l border-theme pointer-events-none" />
        <div className="absolute bottom-4 right-4 w-5 h-5 border-b border-r border-theme pointer-events-none" />

        {/* State A: Document Loaded & Mounted */}
        {uploadedData ? (
          <div className="relative max-w-full max-h-[520px] overflow-auto flex items-center justify-center z-10 select-none">
            {/* Document Image Surface */}
            <div
              className="transition-transform duration-200 ease-out origin-center rounded-xl border border-theme shadow-md overflow-hidden bg-white relative"
              style={{ transform: `scale(${zoomLevel})` }}
            >
              {isAnalyzing && (
                <div className="absolute inset-0 bg-teal-500/10 pointer-events-none z-20 flex items-center justify-center">
                  <div className="h-0.5 w-full bg-teal-500 shadow-sm animate-pulse" />
                </div>
              )}
              <img
                src={uploadedData.previewUrl}
                alt="Prescription document preview"
                className="max-h-[480px] w-auto object-contain block pointer-events-none"
              />
            </div>
          </div>
        ) : (
          /* State B: Empty Optical Focal Zone ("Bring the prescription into focus") */
          <div className="text-center max-w-md mx-auto space-y-4 z-10 py-6">
            <div className="w-14 h-14 rounded-2xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 flex items-center justify-center mx-auto text-teal-700 dark:text-teal-300">
              <UploadCloud className="w-7 h-7" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-lg sm:text-xl font-bold text-theme-primary tracking-tight">
                Bring the prescription into focus.
              </h3>
              <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed">
                Drag and drop your physician&rsquo;s handwritten script here, or select an image scan from your device.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                size="md"
                onClick={() => fileInputRef.current?.click()}
                leftIcon={<UploadCloud className="w-4 h-4" />}
              >
                Select from Device
              </Button>

              <Button
                variant="secondary"
                size="md"
                onClick={() => cameraInputRef.current?.click()}
                leftIcon={<Camera className="w-4 h-4 text-theme-muted" />}
              >
                Use Camera
              </Button>
            </div>

            {/* Supported Formats */}
            <div className="pt-4 border-t border-theme flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-xs text-theme-muted">
              <span>JPEG, PNG, WEBP, PDF</span>
              <span>·</span>
              <span>Max 15 MB</span>
              <span>·</span>
              <span>&ge; 300 DPI recommended</span>
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
        <div className="p-3 bg-red-50 dark:bg-red-950/40 border-t border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};
