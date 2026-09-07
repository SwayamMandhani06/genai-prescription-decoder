import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { HomePage } from './pages/HomePage';
import { WorkspacePage } from './pages/WorkspacePage';
import { ResearchPage } from './pages/ResearchPage';
import { AppView, WorkspaceStep } from './types/navigation.types';

export const AppContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>('home');
  const [initialWorkspaceStep, setInitialWorkspaceStep] = useState<WorkspaceStep>('upload');

  const handleOpenWorkspace = (step: WorkspaceStep = 'upload') => {
    setInitialWorkspaceStep(step);
    setCurrentView('workspace');
  };

  if (currentView === 'research') {
    return (
      <ResearchPage
        onBackToHome={() => setCurrentView('home')}
        onOpenUpload={() => handleOpenWorkspace('upload')}
      />
    );
  }

  if (currentView === 'workspace' || currentView === 'upload' || currentView === 'processing' || currentView === 'results') {
    return (
      <WorkspacePage
        onBackToHome={() => setCurrentView('home')}
        initialStep={initialWorkspaceStep}
      />
    );
  }

  return (
    <HomePage
      onOpenUpload={() => handleOpenWorkspace('upload')}
      onOpenResults={() => handleOpenWorkspace('findings')}
      onOpenResearch={() => setCurrentView('research')}
    />
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
};

export default App;
