import React, { useState } from 'react';
import { OpticalViewfinderCanvas } from '../components/upload/OpticalViewfinderCanvas';
import { ImageQualityHeuristicsCard } from '../components/upload/ImageQualityHeuristicsCard';
import { PrivacySafetyNotice } from '../components/upload/PrivacySafetyNotice';
import { CuratedSamplePicker } from '../components/upload/CuratedSamplePicker';
import { AnalysisProgressModal } from '../components/upload/AnalysisProgressModal';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { UploadedPrescriptionFile } from '../types/navigation.types';
import { PrescriptionAnalysisResult } from '../types/prescription.types';
import {
  validatePrescriptionFile,
  computeImageHeuristics,
} from '../utils/imageHeuristics';
import { prescriptionService } from '../services/prescriptionService';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../data/sampleHandwrittenSvg';
import {
  ArrowLeft,
  ArrowRight,
  FileCheck2,
} from 'lucide-react';

export interface UploadPageProps {
  onBackToHome: () => void;
  onAnalysisSuccess?: (result: PrescriptionAnalysisResult) => void;
  onStartProcessing?: (data: UploadedPrescriptionFile) => void;
}

export const UploadPage: React.FC<UploadPageProps> = ({
  onBackToHome,
  onAnalysisSuccess,
  onStartProcessing,
}) => {
  const [uploadedData, setUploadedData] = useState<UploadedPrescriptionFile | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [showProgressModal, setShowProgressModal] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<PrescriptionAnalysisResult | null>(null);

  // Handle user uploaded file from drag-drop or file picker
  const handleFileSelect = (file: File) => {
    setErrorMessage(null);

    // 1. Validate file format and size
    const validation = validatePrescriptionFile(file);
    if (!validation.isValid) {
      setErrorMessage(validation.error || 'Invalid file.');
      return;
    }

    // 2. Generate local object URL
    const previewUrl = URL.createObjectURL(file);

    // 3. Extract dimensions via Image object
    const img = new Image();
    img.onload = () => {
      const metrics = computeImageHeuristics(
        img.naturalWidth || 1800,
        img.naturalHeight || 2400,
        file.size,
        file.type
      );

      setUploadedData({
        file,
        previewUrl,
        fileName: file.name,
        source: 'user_upload',
        metrics,
      });
    };

    img.onerror = () => {
      // In case of non-renderable PDF or format, provide fallback metrics
      const fallbackMetrics = computeImageHeuristics(2400, 3200, file.size, file.type);
      setUploadedData({
        file,
        previewUrl,
        fileName: file.name,
        source: 'user_upload',
        metrics: fallbackMetrics,
      });
    };

    img.src = previewUrl;
  };

  // Handle quick loading a curated clinical sample
  const handleSelectCuratedSample = (sampleId: string) => {
    setErrorMessage(null);
    const canvas = SAMPLE_PRESCRIPTION_CANVASES[sampleId] || SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];

    // Generate an SVG data URI for instantaneous client preview
    const svgContent = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 480" width="700" height="480" style="background:#F8FAFC; font-family: sans-serif;">
        <rect width="700" height="480" fill="#F8FAFC"/>
        <line x1="20" y1="90" x2="680" y2="90" stroke="#CBD5E1" stroke-width="2"/>
        <text x="30" y="40" font-size="16" font-weight="bold" fill="#0F172A">${canvas.doctorHeader.name}</text>
        <text x="30" y="60" font-size="12" fill="#475569">${canvas.doctorHeader.clinicName} · ${canvas.doctorHeader.clinicAddress}</text>
        <text x="30" y="80" font-size="11" fill="#64748B">${canvas.doctorHeader.qualifications} | ${canvas.doctorHeader.regNo}</text>
        <text x="500" y="40" font-size="12" font-weight="bold" fill="#0284C7">Pt: ${canvas.patientInfo.name}</text>
        <text x="500" y="60" font-size="11" fill="#475569">${canvas.patientInfo.ageGender} · ${canvas.patientInfo.date}</text>
        <text x="500" y="80" font-size="10" fill="#64748B">${canvas.patientInfo.vitals}</text>
        <text x="30" y="125" font-size="28" font-weight="bold" font-family="serif" fill="#1E293B">℞</text>
        ${canvas.strokes
          .map(
            (s) =>
              `<path d="${s.svgPath}" fill="none" stroke="${s.inkColor}" stroke-width="3" stroke-linecap="round"/>`
          )
          .join('')}
        <line x1="20" y1="430" x2="680" y2="430" stroke="#CBD5E1" stroke-width="1"/>
        <text x="30" y="455" font-size="11" fill="#64748B">${canvas.clinicStampText}</text>
        <path d="${canvas.doctorSignaturePath}" fill="none" stroke="#1E3A8A" stroke-width="2"/>
        <text x="480" y="460" font-size="10" fill="#64748B">Prescriber Signature</text>
      </svg>
    `;

    const previewUrl = `data:image/svg+xml;utf8,${encodeURIComponent(svgContent)}`;
    const metrics = computeImageHeuristics(2100, 2800, 184000, 'image/svg+xml');

    setUploadedData({
      file: null,
      previewUrl,
      fileName: `${canvas.accessionId}.svg`,
      source: 'curated_sample',
      sampleId,
      metrics,
    });
  };

  const handleRemoveFile = () => {
    if (uploadedData?.previewUrl && uploadedData.source === 'user_upload') {
      URL.revokeObjectURL(uploadedData.previewUrl);
    }
    setUploadedData(null);
    setErrorMessage(null);
    setAnalysisResult(null);
  };

  // Trigger prescription analysis through the service layer
  const handleStartAnalysis = async () => {
    if (!uploadedData) return;

    // If parent supplied dedicated processing page flow, transition directly
    if (onStartProcessing) {
      onStartProcessing(uploadedData);
      return;
    }

    setIsAnalyzing(true);
    setShowProgressModal(true);

    try {
      // Dispatch to service layer matching POST /api/v1/prescriptions/analyze
      const sampleKey = uploadedData.sampleId || 'rx-sample-1';
      const result = await prescriptionService.analyzePrescription(
        uploadedData.file || sampleKey,
        {
          confidenceThreshold: 0.65,
          enableLasaDetection: true,
          targetLanguage: 'en',
        }
      );

      setAnalysisResult(result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(
          'Multimodal analysis inference failed. Verify document lighting and retry.'
        );
      }
      setShowProgressModal(false);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleViewFinalResults = (result: PrescriptionAnalysisResult) => {
    setShowProgressModal(false);
    if (onAnalysisSuccess) {
      onAnalysisSuccess(result);
    } else {
      // Fallback: return to home and scroll to analyzer with sample
      onBackToHome();
    }
  };

  return (
    <div className="min-h-screen bg-[#07090E] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/25 selection:text-cyan-200">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-[#0A0D15]/95 backdrop-blur-xl border-b border-white/[0.08] py-3.5 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToHome}
              className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 hover:border-white/20 text-xs font-mono text-slate-300 hover:text-white transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Overview</span>
            </button>

            <span className="text-slate-700 hidden sm:inline">|</span>

            <div className="hidden sm:flex items-center gap-2">
              <span className="font-extrabold text-sm tracking-tight text-white font-mono">
                AURA<span className="text-cyan-400">-Rx</span>
              </span>
              <span className="text-xs text-slate-400 font-mono">/ Optical Intake Console</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Inference Pipeline: Online</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
        {/* Page Framing & Concept Header */}
        <div className="max-w-3xl space-y-2.5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-mono">
            <FileCheck2 className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-semibold">Diagnostic Stage 01</span>
            <span className="text-cyan-600">|</span>
            <span>Spatial Intake & Optical Focus</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white font-sans">
            Bring the prescription into focus.
          </h1>

          <p className="text-xs sm:text-sm text-slate-300 font-sans leading-relaxed">
            Mount your physician&rsquo;s physical handwritten prescription onto the optical focal stage. The system pre-screens pixel density, document orientation, and edge contrast before dispatching to the multimodal vision-language model.
          </p>
        </div>

        {/* Central Viewfinder Stage */}
        <div className="space-y-4">
          <OpticalViewfinderCanvas
            uploadedData={uploadedData}
            onFileSelect={handleFileSelect}
            onRemoveFile={handleRemoveFile}
            isAnalyzing={isAnalyzing}
            errorMessage={errorMessage}
          />

          {/* Quick-Load Sample Picker (when no file uploaded) */}
          {!uploadedData && (
            <div className="pt-2">
              <CuratedSamplePicker
                onSelectSample={handleSelectCuratedSample}
              />
            </div>
          )}
        </div>

        {/* Document Diagnostics & Action Bar */}
        {uploadedData && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Real-time Quality Heuristics */}
            <ImageQualityHeuristicsCard metrics={uploadedData.metrics} />

            {/* Action Bar */}
            <div className="p-4 sm:p-5 rounded-xl bg-[#0E131F] border border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-0.5 text-center sm:text-left">
                <div className="text-sm font-bold text-white font-sans flex items-center justify-center sm:justify-start gap-2">
                  <span>Target File:</span>
                  <span className="font-mono text-cyan-400">{uploadedData.fileName}</span>
                  <Badge variant="emerald" size="xs">
                    Ready
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 font-sans">
                  Optical pre-screening passed. Formularies linked: CDSCO India & US NLM RxNorm.
                </p>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <Button
                  variant="ghost"
                  size="md"
                  onClick={handleRemoveFile}
                  className="w-full sm:w-auto text-xs"
                >
                  Change Document
                </Button>

                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleStartAnalysis}
                  isLoading={isAnalyzing}
                  className="w-full sm:w-auto"
                  rightIcon={<ArrowRight className="w-4 h-4 text-slate-950" />}
                >
                  Analyze Prescription
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Statutory Privacy & Governance Notice */}
        <div className="pt-4 border-t border-white/[0.08]">
          <PrivacySafetyNotice />
        </div>
      </main>

      {/* Multistep Processing Modal */}
      <AnalysisProgressModal
        isOpen={showProgressModal}
        onClose={() => setShowProgressModal(false)}
        analysisResult={analysisResult}
        onViewResults={handleViewFinalResults}
      />
    </div>
  );
};
