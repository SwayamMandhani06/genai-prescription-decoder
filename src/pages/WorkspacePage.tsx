import React, { useState } from 'react';
import { WorkspaceShell } from '../components/workspace/WorkspaceShell';
import { UploadStep } from '../components/workspace/UploadStep';
import { ReviewStep } from '../components/workspace/ReviewStep';
import { AnalyzeStep } from '../components/workspace/AnalyzeStep';
import { FindingsStep } from '../components/workspace/FindingsStep';
import { WorkspaceStep, UploadedPrescriptionFile } from '../types/navigation.types';
import { PrescriptionAnalysisResult, ResultsDemoState } from '../types/prescription.types';

export interface WorkspacePageProps {
  onBackToHome: () => void;
  initialStep?: WorkspaceStep;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  onBackToHome,
  initialStep = 'upload',
}) => {
  const [currentStep, setCurrentStep] = useState<WorkspaceStep>(initialStep);

  const [uploadedData, setUploadedData] = useState<UploadedPrescriptionFile | null>(null);

  const [rotation, setRotation] = useState<number>(0);
  const [zoom, setZoom] = useState<number>(100);
  const [analysisResult, setAnalysisResult] = useState<PrescriptionAnalysisResult | null>(null);
  const [liveDemoState, setLiveDemoState] = useState<ResultsDemoState | null>(null);

  const handleContinueToReview = () => {
    setCurrentStep('review');
  };

  const handleStartAnalysis = () => {
    setCurrentStep('analyze');
  };

  const handleAnalysisCompleted = (result: PrescriptionAnalysisResult, demoState?: ResultsDemoState) => {
    setAnalysisResult(result);
    setLiveDemoState(demoState || null);
    setCurrentStep('findings');
  };

  const handleNewPrescription = () => {
    setUploadedData(null);
    setAnalysisResult(null);
    setLiveDemoState(null);
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
          liveDemoState={liveDemoState}
          rotation={rotation}
          onNewPrescription={handleNewPrescription}
        />
      )}
    </WorkspaceShell>
  );
};
