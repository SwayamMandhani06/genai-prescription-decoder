import React from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import { ProcessingStageId } from '../../types/pipeline.types';
import { FileText } from 'lucide-react';

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
    <div className="w-full rounded-2xl overflow-hidden border border-theme bg-surface shadow-xs flex flex-col transition-colors">
      {/* Top Workstation Bar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-surface-subtle border-b border-theme text-xs">
        <div className="flex items-center gap-2 text-theme-primary">
          <FileText className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          <span className="font-semibold">
            {uploadedData?.fileName || 'Prescription Document'}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-theme-secondary">
          <span>Processing Stage</span>
          <span className="text-theme-muted">·</span>
          <span className="text-teal-700 dark:text-teal-400 font-bold font-mono">{overallPercent}%</span>
        </div>
      </div>

      {/* Main Document Inspection Canvas with Calm Scan Indicator */}
      <div className="relative min-h-[440px] sm:min-h-[500px] bg-canvas p-4 sm:p-6 flex items-center justify-center overflow-hidden select-none">
        {/* Subtle Framing Reticles */}
        <div className="absolute top-3 left-3 w-4 h-4 border-t border-l border-theme pointer-events-none" />
        <div className="absolute top-3 right-3 w-4 h-4 border-t border-r border-theme pointer-events-none" />
        <div className="absolute bottom-3 left-3 w-4 h-4 border-b border-l border-theme pointer-events-none" />
        <div className="absolute bottom-3 right-3 w-4 h-4 border-b border-r border-theme pointer-events-none" />

        {/* Dynamic Scanning Line */}
        <div
          className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-teal-500 to-transparent pointer-events-none z-30 transition-all duration-300 ease-out opacity-80"
          style={{ top: currentScanY }}
        >
          <div className="absolute right-4 -top-3 text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface border border-theme text-teal-700 dark:text-teal-300 shadow-xs">
            Scanning
          </div>
        </div>

        {/* Prescription Paper Display */}
        <div className="relative max-w-full max-h-[460px] overflow-hidden rounded-xl border border-theme shadow-sm bg-white">
          <img
            src={uploadedData?.previewUrl || '/assets/sample-standard.svg'}
            alt="Scanning prescription document"
            className="max-h-[440px] w-auto object-contain block opacity-95"
          />
        </div>
      </div>
    </div>
  );
};
