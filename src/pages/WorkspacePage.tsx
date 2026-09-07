import React, { useState } from 'react';
import { WorkspaceShell } from '../components/workspace/WorkspaceShell';
import { UploadStep } from '../components/workspace/UploadStep';
import { ReviewStep } from '../components/workspace/ReviewStep';
import { AnalyzeStep } from '../components/workspace/AnalyzeStep';
import { FindingsStep } from '../components/workspace/FindingsStep';
import { WorkspaceStep, UploadedPrescriptionFile } from '../types/navigation.types';
import { PrescriptionAnalysisResult } from '../types/prescription.types';
import { SAMPLE_PRESCRIPTION_CANVASES } from '../data/sampleHandwrittenSvg';
import { computeImageHeuristics } from '../utils/imageHeuristics';

export interface WorkspacePageProps {
  onBackToHome: () => void;
  initialStep?: WorkspaceStep;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  onBackToHome,
  initialStep = 'upload',
}) => {
  const [currentStep, setCurrentStep] = useState<WorkspaceStep>(initialStep);

  // Initialize with curated sample 1 as a baseline fallback so review/analyze/findings are instantly interactive even if user directly opens workspace
  const defaultSampleCanvas = SAMPLE_PRESCRIPTION_CANVASES['rx-sample-1'];
  const defaultSampleMetrics = computeImageHeuristics(2480, 3508, 1024 * 1024 * 1.8, 'image/svg+xml');

  const [uploadedData, setUploadedData] = useState<UploadedPrescriptionFile | null>({
    file: null,
    previewUrl: '/assets/sample-standard.svg',
    fileName: `${defaultSampleCanvas.accessionId}.svg`,
    source: 'curated_sample',
    sampleId: 'rx-sample-1',
    metrics: defaultSampleMetrics,
  });

  const [rotation, setRotation] = useState<number>(0);
  const [zoom, setZoom] = useState<number>(100);
  const [analysisResult, setAnalysisResult] = useState<PrescriptionAnalysisResult | null>(null);

  const handleContinueToReview = () => {
    setCurrentStep('review');
  };

  const handleStartAnalysis = () => {
    setCurrentStep('analyze');
  };

  const handleAnalysisCompleted = (result: PrescriptionAnalysisResult) => {
    setAnalysisResult(result);
    setCurrentStep('findings');
  };

  const handleNewPrescription = () => {
    setUploadedData(null);
    setAnalysisResult(null);
    setRotation(0);
    setZoom(100);
    setCurrentStep('upload');
  };

  return (
    <WorkspaceShell
      currentStep={currentStep}
      onNavigateStep={(step) => setCurrentStep(step)}
      onBackToHome={onBackToHome}
    >
      {currentStep === 'upload' && (
        <UploadStep
          uploadedData={uploadedData}
          onSetUploadedData={setUploadedData}
          rotation={rotation}
          onSetRotation={setRotation}
          zoom={zoom}
          onSetZoom={setZoom}
          onContinueToReview={handleContinueToReview}
        />
      )}

      {currentStep === 'review' && (
        <ReviewStep
          uploadedData={uploadedData}
          rotation={rotation}
          onSetRotation={setRotation}
          onBackToUpload={() => setCurrentStep('upload')}
          onStartAnalysis={handleStartAnalysis}
        />
      )}

      {currentStep === 'analyze' && (
        <AnalyzeStep
          uploadedData={uploadedData}
          rotation={rotation}
          onAnalysisCompleted={handleAnalysisCompleted}
          onBackToReview={() => setCurrentStep('review')}
        />
      )}

      {currentStep === 'findings' && (
        <FindingsStep
          uploadedData={uploadedData}
          initialResult={analysisResult}
          rotation={rotation}
          onNewPrescription={handleNewPrescription}
        />
      )}
    </WorkspaceShell>
  );
};
