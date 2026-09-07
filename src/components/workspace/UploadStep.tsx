import React, { useState, useRef } from 'react';
import { UploadedPrescriptionFile } from '../../types/navigation.types';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../../data/sampleHandwrittenSvg';
import { computeImageHeuristics, validatePrescriptionFile } from '../../utils/imageHeuristics';
import {
  UploadCloud,
  RotateCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  FileCheck2,
  Sun,
  Camera,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export interface UploadStepProps {
  uploadedData: UploadedPrescriptionFile | null;
  onSetUploadedData: (data: UploadedPrescriptionFile | null) => void;
  rotation: number;
  onSetRotation: (rotation: number) => void;
  zoom: number;
  onSetZoom: (zoom: number) => void;
  onContinueToReview: () => void;
}

export const UploadStep: React.FC<UploadStepProps> = ({
  uploadedData,
  onSetUploadedData,
  rotation,
  onSetRotation,
  zoom,
  onSetZoom,
  onContinueToReview,
}) => {
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const processFile = (file: File) => {
    setErrorMsg(null);
    const validation = validatePrescriptionFile(file);
    if (!validation.isValid) {
      setErrorMsg(validation.error || 'Invalid file format.');
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const metrics = computeImageHeuristics(
        img.naturalWidth || 1800,
        img.naturalHeight || 2400,
        file.size,
        file.type
      );
      onSetUploadedData({
        file,
        previewUrl,
        fileName: file.name,
        source: 'user_upload',
        metrics,
      });
      onSetRotation(0);
      onSetZoom(100);
    };
    img.onerror = () => {
      const metrics = computeImageHeuristics(1800, 2400, file.size, file.type);
      onSetUploadedData({
        file,
        previewUrl,
        fileName: file.name,
        source: 'user_upload',
        metrics,
      });
      onSetRotation(0);
      onSetZoom(100);
    };
    img.src = previewUrl;
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleSelectCuratedSample = (sampleId: string) => {
    setErrorMsg(null);
    const canvas = SAMPLE_PRESCRIPTION_CANVASES[sampleId] || SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];
    const previewUrl =
      sampleId === 'rx-sample-2'
        ? '/assets/sample-lasa.svg'
        : sampleId === 'rx-sample-3'
        ? '/assets/sample-flagged.svg'
        : '/assets/sample-standard.svg';

    const metrics = computeImageHeuristics(2480, 3508, 1024 * 1024 * 1.8, 'image/svg+xml');

    onSetUploadedData({
      file: null,
      previewUrl,
      fileName: `${canvas.accessionId}.svg`,
      source: 'curated_sample',
      sampleId,
      metrics,
    });
    onSetRotation(0);
    onSetZoom(100);
  };

  const handleRotate = () => {
    onSetRotation((rotation + 90) % 360);
  };

  const handleZoomIn = () => {
    onSetZoom(Math.min(zoom + 20, 200));
  };

  const handleZoomOut = () => {
    onSetZoom(Math.max(zoom - 20, 60));
  };

  const handleResetZoom = () => {
    onSetZoom(100);
    onSetRotation(0);
  };

  const curatedSamples = [
    {
      id: 'rx-sample-1',
      title: 'Standard Outpatient Script',
      subtitle: 'Augmentin 625 Duo · Pan 40 · Dolo 650',
      difficulty: 'High Legibility',
    },
    {
      id: 'rx-sample-2',
      title: 'Cardiometabolic Script (LASA)',
      subtitle: 'Metformin 500mg (Sound-alike risk)',
      difficulty: 'LASA Risk Alert',
    },
    {
      id: 'rx-sample-3',
      title: 'Pediatric Script (Ambiguity)',
      subtitle: 'Prednisolone decimal ligature ambiguity',
      difficulty: 'Selective Abstention',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Step Header */}
      <div className="max-w-2xl space-y-2">
        <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-theme-primary">
          Mount a prescription.
        </h1>
        <p className="text-sm sm:text-base text-theme-secondary leading-relaxed">
          Upload a prescription document or select an authentic clinic sample to begin interpretation.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Document Workspace Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left / Central: Large Document Preview Area (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative rounded-3xl border-2 transition-all overflow-hidden flex flex-col items-center justify-center min-h-[460px] p-6 sm:p-10 ${
              isDragging
                ? 'border-teal-500 bg-teal-50/20 dark:bg-teal-950/30'
                : 'border-dashed border-theme bg-surface/40'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/jpeg,image/png,image/webp,image/svg+xml"
              className="hidden"
            />

            {uploadedData ? (
              /* Mounted Document Visualization */
              <div className="w-full flex flex-col items-center space-y-6">
                {/* Document Canvas Frame with Transform (Rotate & Zoom) */}
                <div className="w-full max-w-xl overflow-hidden rounded-2xl flex items-center justify-center p-2">
                  <div
                    style={{
                      transform: `rotate(${rotation}deg) scale(${zoom / 100})`,
                      transition: 'transform 0.25s ease-out',
                    }}
                    className="max-w-md w-full shadow-md rounded-2xl prescription-paper p-6 border border-theme origin-center"
                  >
                    {uploadedData.source === 'curated_sample' ? (
                      /* Curated Sample SVG Preview */
                      <div className="space-y-4 text-slate-900 dark:text-slate-100">
                        <div className="border-b border-slate-300 dark:border-slate-700 pb-2 flex justify-between items-start text-xs">
                          <div>
                            <div className="font-semibold text-teal-800 dark:text-teal-400 text-[11px]">
                              Example Outpatient Clinic (Demo)
                            </div>
                            <div className="font-bold text-slate-800 dark:text-slate-200 text-xs">
                              Example Prescriber, M.D.
                            </div>
                          </div>
                          <span className="text-[11px] text-slate-500 dark:text-slate-400">
                            {uploadedData.fileName}
                          </span>
                        </div>

                        <div className="text-xl font-serif italic font-bold">℞</div>

                        {/* Handwriting Lines - Clean presentation without artificial Line 01/02 tags */}
                        <div className="space-y-3.5 py-2">
                          <div className="border-b border-slate-200 dark:border-slate-800 pb-2">
                            <div className="font-serif italic text-base text-blue-900 dark:text-sky-300 font-bold">
                              Augm 625 Duo &mdash; 1-0-1 (PC) x 5d
                            </div>
                          </div>
                          <div className="border-b border-slate-200 dark:border-slate-800 pb-2">
                            <div className="font-serif italic text-base text-blue-900 dark:text-sky-300 font-bold">
                              Pan 40 &mdash; 1 tab OD (AC) x 5d
                            </div>
                          </div>
                          <div>
                            <div className="font-serif italic text-base text-blue-900 dark:text-sky-300 font-bold">
                              Dolo 650 &mdash; SOS for fever
                            </div>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-slate-300 dark:border-slate-700 flex justify-between text-[10px] text-slate-500">
                          <span>Patient: Demo Patient (34M)</span>
                          <span>Prescriber Signature Attached</span>
                        </div>
                      </div>
                    ) : (
                      /* User Uploaded Image Preview */
                      <img
                        src={uploadedData.previewUrl}
                        alt="Prescription Document"
                        className="w-full max-h-[380px] object-contain rounded-lg shadow-xs"
                      />
                    )}
                  </div>
                </div>

                {/* Floating Document Actions Toolbar */}
                <div className="flex flex-wrap items-center justify-center gap-2 p-2 rounded-2xl bg-surface border border-theme shadow-md">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-1.5 rounded-xl bg-surface-subtle hover:bg-surface border border-theme text-xs font-semibold text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer"
                    title="Replace Document"
                  >
                    <UploadCloud className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                    <span>Replace</span>
                  </button>

                  <div className="w-px h-5 bg-border-subtle" />

                  <button
                    onClick={handleRotate}
                    className="px-3 py-1.5 rounded-xl bg-surface-subtle hover:bg-surface border border-theme text-xs font-semibold text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer"
                    title="Rotate 90 degrees clockwise"
                  >
                    <RotateCw className="w-3.5 h-3.5" />
                    <span>Rotate ({rotation}&deg;)</span>
                  </button>

                  <div className="w-px h-5 bg-border-subtle" />

                  <button
                    onClick={handleZoomOut}
                    className="p-2 rounded-xl bg-surface-subtle hover:bg-surface border border-theme text-theme-secondary hover:text-theme-primary transition-all cursor-pointer"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-3.5 h-3.5" />
                  </button>

                  <span className="font-mono text-xs text-theme-secondary px-1 min-w-[45px] text-center">
                    {zoom}%
                  </span>

                  <button
                    onClick={handleZoomIn}
                    className="p-2 rounded-xl bg-surface-subtle hover:bg-surface border border-theme text-theme-secondary hover:text-theme-primary transition-all cursor-pointer"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={handleResetZoom}
                    className="p-2 rounded-xl bg-surface-subtle hover:bg-surface border border-theme text-theme-muted hover:text-theme-primary transition-all cursor-pointer"
                    title="Reset Zoom and Rotation"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ) : (
              /* Empty State: Dropzone & Upload Action */
              <div className="space-y-5 text-center max-w-md">
                <div className="w-16 h-16 rounded-3xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 flex items-center justify-center text-teal-700 dark:text-teal-300 mx-auto shadow-xs">
                  <UploadCloud className="w-8 h-8" />
                </div>

                <div className="space-y-1">
                  <h3 className="text-lg font-bold text-theme-primary">
                    Drop your prescription image here
                  </h3>
                  <p className="text-xs text-theme-secondary">
                    Supports JPEG, PNG, WEBP, or scanned SVG (up to 15MB)
                  </p>
                </div>

                <div className="pt-2 flex justify-center">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold transition-all inline-flex items-center gap-2 cursor-pointer shadow-sm"
                  >
                    <Camera className="w-4 h-4" />
                    <span>Choose a prescription file</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Proceed Action Bar - Clean layout flow without card wrapper */}
          {uploadedData && (
            <div className="flex items-center justify-between pt-2">
              <div className="text-xs text-theme-secondary">
                <span className="font-semibold text-theme-primary">Mounted:</span> {uploadedData.fileName}
              </div>

              <button
                onClick={onContinueToReview}
                className="px-7 py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold transition-all inline-flex items-center gap-2 cursor-pointer shadow-sm group"
              >
                <span>Continue to Review</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Curated Samples & Guidance (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Curated Samples */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-theme-secondary flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              <span>Or choose a clinical sample:</span>
            </h3>

            <div className="space-y-2">
              {curatedSamples.map((sample) => (
                <button
                  key={sample.id}
                  onClick={() => handleSelectCuratedSample(sample.id)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                    uploadedData?.sampleId === sample.id
                      ? 'bg-surface border-teal-500 shadow-sm'
                      : 'bg-surface-subtle/70 hover:bg-surface border-theme'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-theme-primary">{sample.title}</span>
                    <span className="text-[11px] text-teal-700 dark:text-teal-400 font-medium">
                      {sample.difficulty}
                    </span>
                  </div>
                  <p className="text-[11px] text-theme-secondary">{sample.subtitle}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Document Quality Guidance - Quiet inline checklist without card wrapper */}
          <div className="space-y-3 pt-4 border-t border-theme">
            <h3 className="text-xs font-semibold text-theme-secondary flex items-center gap-1.5">
              <FileCheck2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              <span>Document quality guidelines</span>
            </h3>

            <div className="space-y-2.5 text-xs text-theme-secondary">
              <div className="flex items-start gap-2">
                <Sun className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-theme-primary font-medium">Even lighting:</strong> Minimal shadow over cursive handwriting.
                </p>
              </div>

              <div className="flex items-start gap-2">
                <RotateCw className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-theme-primary font-medium">Upright orientation:</strong> Rotate so physician header is at top.
                </p>
              </div>

              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                <p>
                  <strong className="text-theme-primary font-medium">Sharp focus:</strong> Avoid motion blur for clear stroke tracing.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
