import React, { useState, useEffect, lazy, Suspense } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { HomePage } from './pages/HomePage';
import { AppView, WorkspaceStep } from './types/navigation.types';

const WorkspacePage = lazy(() =>
  import('./pages/WorkspacePage').then((m) => ({ default: m.WorkspacePage }))
);
const ResearchPage = lazy(() =>
  import('./pages/ResearchPage').then((m) => ({ default: m.ResearchPage }))
);
const ResultsPage = lazy(() =>
  import('./pages/ResultsPage').then((m) => ({ default: m.ResultsPage }))
);

const PageLoadingFallback: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-200">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-sm text-slate-400 font-medium">Loading DawaAI...</span>
    </div>
  </div>
);

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
      <Suspense fallback={<PageLoadingFallback />}>
        <ResearchPage
          onBackToHome={() => setCurrentView('home')}
          onOpenUpload={() => handleOpenWorkspace('upload')}
        />
      </Suspense>
    );
  }

  if (currentView === 'results') {
    return (
      <Suspense fallback={<PageLoadingFallback />}>
        <ResultsPage
          onBackToHome={() => setCurrentView('home')}
          onBackToUpload={() => handleOpenWorkspace('upload')}
        />
      </Suspense>
    );
  }

  if (currentView === 'workspace' || currentView === 'upload' || currentView === 'processing') {
    return (
      <Suspense fallback={<PageLoadingFallback />}>
        <WorkspacePage
          onBackToHome={() => setCurrentView('home')}
          initialStep={initialWorkspaceStep}
        />
      </Suspense>
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
