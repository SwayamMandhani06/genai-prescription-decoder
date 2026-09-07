import React, { useState } from 'react';
import { ThemeSwitcher } from '../layout/ThemeSwitcher';
import { WorkspaceStep } from '../../types/navigation.types';
import {
  ArrowLeft,
  HelpCircle,
  ShieldCheck,
  Check,
  AlertTriangle,
  FileText,
  X,
} from 'lucide-react';

export interface WorkspaceShellProps {
  currentStep: WorkspaceStep;
  onNavigateStep?: (step: WorkspaceStep) => void;
  onBackToHome: () => void;
  children: React.ReactNode;
}

export const WorkspaceShell: React.FC<WorkspaceShellProps> = ({
  currentStep,
  onNavigateStep,
  onBackToHome,
  children,
}) => {
  const [showHelpModal, setShowHelpModal] = useState<boolean>(false);

  const steps: { id: WorkspaceStep; num: string; label: string }[] = [
    { id: 'upload', num: '01', label: 'Upload' },
    { id: 'review', num: '02', label: 'Review' },
    { id: 'analyze', num: '03', label: 'Analyze' },
    { id: 'findings', num: '04', label: 'Findings' },
  ];

  const currentIdx = steps.findIndex((s) => s.id === currentStep);

  return (
    <div className="min-h-screen bg-canvas text-theme-primary flex flex-col font-sans transition-colors">
      {/* Light, Calm Application Shell Header */}
      <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-theme py-3 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Left: Back / Home & AURA-Rx Brand */}
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToHome}
              className="px-3 py-1.5 rounded-xl bg-surface-subtle hover:bg-surface border border-theme text-xs font-semibold text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer shadow-xs group"
              title="Return to Homepage"
            >
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
              <span>Home</span>
            </button>

            <span className="text-theme-muted hidden sm:inline">|</span>

            <div className="flex items-center gap-1.5">
              <div className="w-6 h-6 rounded-md bg-teal-50 dark:bg-teal-950/50 border border-teal-200 dark:border-teal-800 flex items-center justify-center text-teal-700 dark:text-teal-300">
                <FileText className="w-3.5 h-3.5" />
              </div>
              <span className="font-extrabold text-sm tracking-tight text-theme-primary">
                AURA<span className="text-teal-600 dark:text-teal-400">-Rx</span>
              </span>
              <span className="text-[11px] font-mono text-theme-muted hidden md:inline">
                Workspace
              </span>
            </div>
          </div>

          {/* Center: Calm Typographic Progress Tracker (1 Upload · 2 Review · 3 Analyze · 4 Findings) */}
          <nav aria-label="Progress" className="hidden md:flex items-center gap-2">
            {steps.map((step, idx) => {
              const isCurrent = step.id === currentStep;
              const isPast = idx < currentIdx;
              const isClickable = isPast && onNavigateStep;

              return (
                <div key={step.id} className="flex items-center">
                  <button
                    disabled={!isClickable}
                    onClick={() => isClickable && onNavigateStep(step.id)}
                    className={`flex items-center gap-1.5 px-2 py-1 text-xs transition-colors ${
                      isCurrent
                        ? 'text-teal-700 dark:text-teal-400 font-bold'
                        : isPast
                        ? 'text-theme-secondary hover:text-theme-primary cursor-pointer'
                        : 'text-theme-muted cursor-not-allowed opacity-50'
                    }`}
                  >
                    <span className={`text-[11px] ${isCurrent ? 'font-bold' : ''}`}>
                      {isPast ? <Check className="w-3 h-3 text-teal-600 dark:text-teal-400 inline" /> : `${idx + 1}.`}
                    </span>
                    <span>{step.label}</span>
                    {isCurrent && (
                      <span className="w-1 h-1 rounded-full bg-teal-600 dark:bg-teal-400 inline-block ml-0.5" />
                    )}
                  </button>

                  {idx < steps.length - 1 && (
                    <span className="text-theme-muted/40 mx-1.5 text-xs select-none">&rarr;</span>
                  )}
                </div>
              );
            })}
          </nav>

          {/* Mobile Current Step */}
          <div className="flex md:hidden items-center gap-1.5 text-xs text-theme-secondary">
            <span className="text-teal-700 dark:text-teal-400 font-bold">
              {currentIdx + 1}.
            </span>
            <span className="font-semibold text-theme-primary">
              {steps[currentIdx]?.label}
            </span>
          </div>

          {/* Right: Theme Switcher & Help/Safety */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHelpModal(true)}
              className="text-xs text-theme-secondary hover:text-theme-primary transition-colors flex items-center gap-1.5 cursor-pointer py-1 px-2"
              title="Help &amp; Clinical Safety"
            >
              <HelpCircle className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              <span className="hidden sm:inline">Help &amp; Safety</span>
            </button>

            <ThemeSwitcher />
          </div>
        </div>
      </header>

      {/* Main Workspace Stage */}
      <main className="flex-1 flex flex-col">
        {children}
      </main>

      {/* Help & Safety Modal */}
      {showHelpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-surface border border-theme rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 flex items-center justify-center text-teal-700 dark:text-teal-300">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-theme-primary">
                    Workspace Guidance &amp; Safety
                  </h3>
                  <p className="text-xs text-theme-muted">
                    Explainable Multimodal Assistance
                  </p>
                </div>
              </div>

              <button
                onClick={() => setShowHelpModal(false)}
                className="text-theme-muted hover:text-theme-primary p-1 rounded-lg hover:bg-surface-subtle cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-theme-secondary leading-relaxed">
              <div className="p-3 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-300 flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
                <div>
                  <strong>Assistive Medical Tool:</strong> AURA-Rx is designed to assist document reading and verification. It does not provide medical diagnosis or replace a licensed physician or pharmacist.
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-theme-primary text-xs">
                  How the workspace operates:
                </h4>
                <ul className="space-y-1.5 list-disc pl-4 text-theme-secondary">
                  <li><strong>01 Upload:</strong> Mount a clear image or select a clinic benchmark sample.</li>
                  <li><strong>02 Review:</strong> Inspect document focus, rotation, and lighting before analysis.</li>
                  <li><strong>03 Analyze:</strong> Watch human-readable extraction stages as handwriting is decoded.</li>
                  <li><strong>04 Findings:</strong> Review verified posology, uncertainty flags, and vernacular guidance.</li>
                </ul>
              </div>

              <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-1">
                <strong className="text-theme-primary block">Uncertainty Philosophy:</strong>
                <span>
                  When handwriting is ambiguous, the system triggers selective abstention rather than guessing. Look for &ldquo;Needs Verification&rdquo; flags on low-confidence cursive strokes.
                </span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowHelpModal(false)}
                className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
