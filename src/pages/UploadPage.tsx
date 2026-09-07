import React, { useState } from 'react';
import { OpticalViewfinderCanvas } from '../components/upload/OpticalViewfinderCanvas';
import { ImageQualityHeuristicsCard } from '../components/upload/ImageQualityHeuristicsCard';
import { PrivacySafetyNotice } from '../components/upload/PrivacySafetyNotice';
import { CuratedSamplePicker } from '../components/upload/CuratedSamplePicker';
import { AnalysisProgressModal } from '../components/upload/AnalysisProgressModal';
import { ThemeSwitcher } from '../components/layout/ThemeSwitcher';
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
      // Fallback heuristics if image fails to load dimensions
      const metrics = computeImageHeuristics(1800, 2400, file.size, file.type);
      setUploadedData({
        file,
        previewUrl,
        fileName: file.name,
        source: 'user_upload',
        metrics,
      });
    };

    img.src = previewUrl;
  };

  // Handle sample selection from curated clinical benchmark library
  const handleSelectCuratedSample = (sampleId: string) => {
    setErrorMessage(null);

    const canvas = SAMPLE_PRESCRIPTION_CANVASES[sampleId] || SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];
    const previewUrl =
      sampleId === 'rx-sample-2'
        ? '/assets/sample-lasa.svg'
        : sampleId === 'rx-sample-3'
        ? '/assets/sample-flagged.svg'
        : '/assets/sample-standard.svg';

    const metrics = computeImageHeuristics(
      2480,
      3508,
      1024 * 1024 * 1.8,
      'image/svg+xml'
    );

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
      onBackToHome();
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-theme-primary flex flex-col font-sans transition-colors">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-theme py-3.5 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToHome}
              className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface border border-theme text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Overview</span>
            </button>

            <span className="text-theme-muted hidden sm:inline">|</span>

            <div className="hidden sm:flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-theme-primary">
                AURA-Rx
              </span>
              <span className="text-xs text-theme-muted">/ Prescription Intake</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ThemeSwitcher />
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/40 px-3 py-1 rounded-full border border-teal-200 dark:border-teal-800">
              <span className="w-2 h-2 rounded-full bg-teal-500" />
              <span>Intake Pipeline Ready</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
        {/* Page Header */}
        <div className="max-w-3xl space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs font-medium">
            <FileCheck2 className="w-3.5 h-3.5" />
            <span>Stage 01: Document Intake</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-theme-primary">
            Bring the prescription into focus.
          </h1>

          <p className="text-sm text-theme-secondary leading-relaxed">
            Mount your physician&rsquo;s physical handwritten prescription onto the focal stage. The system evaluates resolution, angle, and stroke contrast before running multimodal interpretation.
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
            <div className="p-4 sm:p-5 rounded-2xl bg-surface border border-theme flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xs">
              <div className="space-y-0.5 text-center sm:text-left">
                <div className="text-sm font-bold text-theme-primary flex items-center justify-center sm:justify-start gap-2">
                  <span>Prescription:</span>
                  <span className="font-mono text-teal-700 dark:text-teal-400">{uploadedData.fileName}</span>
                  <Badge variant="emerald" size="xs">
                    Ready
                  </Badge>
                </div>
                <p className="text-xs text-theme-secondary">
                  Pre-screening complete. Formularies linked: CDSCO & RxNorm.
                </p>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <Button
                  variant="secondary"
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
                  rightIcon={<ArrowRight className="w-4 h-4 text-white" />}
                >
                  Analyze Prescription
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Statutory Privacy & Governance Notice */}
        <div className="pt-4 border-t border-theme">
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
