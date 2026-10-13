import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { HomePage } from './pages/HomePage';
import { WorkspacePage } from './pages/WorkspacePage';
import { ResearchPage } from './pages/ResearchPage';
import { ResultsPage } from './pages/ResultsPage';
import { AppView, WorkspaceStep } from './types/navigation.types';

export const AppContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const v = params.get('view') as AppView;
      if (v && ['home', 'workspace', 'research', 'upload', 'processing', 'results'].includes(v)) {
        return v;
      }
      if (window.location.hash === '#results') return 'results';
      if (window.location.hash === '#research') return 'research';
    }
    return 'home';
  });
  const [initialWorkspaceStep, setInitialWorkspaceStep] = useState<WorkspaceStep>('upload');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).__setView = (v: AppView) => setCurrentView(v);
    }
  }, []);

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

  if (currentView === 'results') {
    return (
      <ResultsPage
        onBackToHome={() => setCurrentView('home')}
        onBackToUpload={() => handleOpenWorkspace('upload')}
      />
    );
  }

  if (currentView === 'workspace' || currentView === 'upload' || currentView === 'processing') {
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
      onOpenResults={() => setCurrentView('results')}
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
