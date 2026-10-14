import React, { useState } from 'react';
import { BoundingBox } from '../../types/prescription.types';
import { apiConfig } from '../../services/api/apiConfig';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  RotateCcw,
  Eye,
  FileCheck,
} from 'lucide-react';

export interface OriginalScriptViewerProps {
  scriptKey?: string;
  previewUrl?: string;
  activeBoundingBox?: BoundingBox | null;
  highlightLabel?: string;
  accessionId: string;
}

export const OriginalScriptViewer: React.FC<OriginalScriptViewerProps> = ({
  scriptKey: _scriptKey,
  previewUrl,
  activeBoundingBox,
  highlightLabel,
  accessionId,
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const handleZoomIn = () => setZoomLevel((z) => Math.min(z + 20, 220));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(z - 20, 70));
  const handleResetZoom = () => setZoomLevel(100);

  const resolvedPreviewUrl = previewUrl
    ? previewUrl.startsWith('http') || previewUrl.startsWith('data:') || previewUrl.startsWith('blob:') || previewUrl.startsWith('/samples') || previewUrl.startsWith('/assets')
      ? previewUrl
      : `${apiConfig.baseUrl}${previewUrl}`
    : undefined;

  const hasGroundedBox = Boolean(
    activeBoundingBox &&
      activeBoundingBox.width > 0 &&
      activeBoundingBox.height > 0 &&
      (activeBoundingBox.x > 0 || activeBoundingBox.y > 0)
  );

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
          <Eye className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
          <span className="font-semibold text-theme-primary">
            Original script · <span className="font-mono text-xs">{accessionId}</span>
          </span>
          <span className="hidden sm:inline text-theme-muted">|</span>
          <span className="hidden sm:inline text-theme-secondary text-xs">
            Visual reference
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
            className="p-1.5 rounded-lg bg-[#EAF2FF] dark:bg-[#155EEF]/20 border border-[#155EEF]/30 text-[#155EEF] dark:text-[#4B8BFF] hover:bg-[#EAF2FF]/80 cursor-pointer ml-1"
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
          {resolvedPreviewUrl ? (
            <div className="relative rounded-xl border border-theme shadow-md overflow-hidden bg-white">
              <img
                src={resolvedPreviewUrl}
                alt="Original handwritten prescription"
                className="max-h-[500px] w-auto object-contain block"
              />
              {hasGroundedBox && activeBoundingBox && (
                <div
                  className="absolute border-2 border-[#155EEF] bg-[#155EEF]/15 rounded-md pointer-events-none transition-all duration-200 ring-2 ring-[#155EEF]/40"
                  style={{
                    top: `${activeBoundingBox.y}%`,
                    left: `${activeBoundingBox.x}%`,
                    width: `${activeBoundingBox.width}%`,
                    height: `${activeBoundingBox.height}%`,
                  }}
                >
                  <span className="absolute -top-4 left-1 px-1.5 py-0.2 bg-surface text-[9px] font-medium text-[#155EEF] dark:text-[#4B8BFF] rounded border border-theme shadow-xs">
                    {highlightLabel || 'Verified Region'}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-theme-muted flex flex-col items-center justify-center space-y-3 rounded-2xl border border-theme bg-surface">
              <FileCheck className="w-12 h-12 text-theme-muted opacity-40" />
              <p className="text-sm font-semibold text-theme-primary">Prescription Document Viewer</p>
              <p className="text-xs text-theme-secondary max-w-xs">
                Original prescription image will be displayed here for clinical review.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Notice Strip */}
      <div className="px-4 py-2 bg-surface-subtle border-t border-theme flex items-center justify-between text-xs text-theme-muted">
        <div className="flex items-center gap-1.5">
          <FileCheck className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
          <span>Original physician document preserved as primary legal record</span>
        </div>
      </div>
    </div>
  );
};
