import React, { useState } from 'react';
import { HomePage } from './pages/HomePage';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ResultsPage } from './pages/ResultsPage';
import { AppView, UploadedPrescriptionFile } from './types/navigation.types';
import { PrescriptionAnalysisResult } from './types/prescription.types';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>('home');
  const [uploadedFile, setUploadedFile] = useState<UploadedPrescriptionFile | null>(null);
  const [lastAnalysisResult, setLastAnalysisResult] = useState<PrescriptionAnalysisResult | null>(null);

  const handleStartProcessing = (file: UploadedPrescriptionFile) => {
    setUploadedFile(file);
    setCurrentView('processing');
  };

  const handleProcessingComplete = (result: PrescriptionAnalysisResult) => {
    setLastAnalysisResult(result);
    // Transition directly to the dedicated Results Experience
    setCurrentView('results');
  };

  if (currentView === 'results') {
    return (
      <ResultsPage
        uploadedData={uploadedFile}
        initialResult={lastAnalysisResult}
        onBackToHome={() => setCurrentView('home')}
        onBackToUpload={() => setCurrentView('upload')}
        onRerunPipeline={() => setCurrentView('processing')}
      />
    );
  }

  if (currentView === 'processing') {
    return (
      <ProcessingPage
        uploadedData={uploadedFile}
        onBackToUpload={() => setCurrentView('upload')}
        onComplete={handleProcessingComplete}
      />
    );
  }

  if (currentView === 'upload') {
    return (
      <UploadPage
        onBackToHome={() => setCurrentView('home')}
        onAnalysisSuccess={handleProcessingComplete}
        onStartProcessing={handleStartProcessing}
      />
    );
  }

  return (
    <HomePage
      onOpenUpload={() => setCurrentView('upload')}
      onOpenResults={() => setCurrentView('results')}
    />
  );
};

export default App;
