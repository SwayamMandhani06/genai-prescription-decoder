import React, { useState, useEffect } from 'react';
import { ThemeSwitcher } from './ThemeSwitcher';
import {
  FileText,
  ShieldCheck,
  Sparkles,
  HelpCircle,
  Menu,
  X,
  UploadCloud,
  FileCheck,
} from 'lucide-react';
import { AppView } from '../../types/navigation.types';

export interface NavbarProps {
  onNavigateToAnalyze?: () => void;
  onNavigateToHowItWorks?: () => void;
  onNavigateToSafety?: () => void;
  onNavigateToResearch?: () => void;
  onOpenUploadClick?: () => void;
  onOpenResultsClick?: () => void;
  onHomeClick?: () => void;
  activeView?: AppView;
}

export const Navbar: React.FC<NavbarProps> = ({
  onNavigateToAnalyze,
  onNavigateToHowItWorks,
  onNavigateToSafety,
  onNavigateToResearch,
  onOpenUploadClick,
  onOpenResultsClick,
  onHomeClick,
  activeView = 'home',
}) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 15);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLinkClick = (e: React.MouseEvent, callback?: () => void, targetId?: string) => {
    if (activeView !== 'home' && onHomeClick) {
      e.preventDefault();
      onHomeClick();
      if (targetId) {
        setTimeout(() => {
          const el = document.getElementById(targetId);
          if (el) el.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
      return;
    }

    if (callback) {
      e.preventDefault();
      callback();
    } else if (targetId) {
      e.preventDefault();
      const el = document.getElementById(targetId);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-200 ${
        isScrolled
          ? 'bg-surface/90 backdrop-blur-md border-b border-theme shadow-sm py-2.5'
          : 'bg-transparent py-4'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Logo & Product Identification */}
          <button
            onClick={onHomeClick}
            className="flex items-center gap-2.5 text-left group cursor-pointer focus:outline-none"
          >
            <div className="w-8 h-8 rounded-lg bg-teal-600/10 dark:bg-teal-400/10 border border-teal-600/20 dark:border-teal-400/20 flex items-center justify-center text-teal-700 dark:text-teal-300">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-theme-primary">
                  AURA<span className="text-teal-600 dark:text-teal-400">-Rx</span>
                </span>
              </div>
              <p className="text-[10px] text-theme-muted tracking-tight font-medium hidden sm:block">
                Prescription Understanding Workspace
              </p>
            </div>
          </button>

          {/* Primary Navigation (Desktop) */}
          <nav className="hidden md:flex items-center gap-1 bg-surface-subtle/80 px-2 py-1 rounded-full border border-theme backdrop-blur-sm">
            <a
              href="#analyze"
              onClick={(e) => handleLinkClick(e, onNavigateToAnalyze, 'analyze')}
              className="px-3.5 py-1.5 text-xs font-medium text-theme-secondary hover:text-theme-primary hover:bg-surface rounded-full transition-all flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-theme-muted" />
              <span>Analyze</span>
            </a>

            <a
              href="#how-it-works"
              onClick={(e) => handleLinkClick(e, onNavigateToHowItWorks, 'how-it-works')}
              className="px-3.5 py-1.5 text-xs font-medium text-theme-secondary hover:text-theme-primary hover:bg-surface rounded-full transition-all flex items-center gap-1.5"
            >
              <HelpCircle className="w-3.5 h-3.5 text-theme-muted" />
              <span>How It Works</span>
            </a>

            <a
              href="#safety"
              onClick={(e) => handleLinkClick(e, onNavigateToSafety, 'safety')}
              className="px-3.5 py-1.5 text-xs font-medium text-theme-secondary hover:text-theme-primary hover:bg-surface rounded-full transition-all flex items-center gap-1.5"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-theme-muted" />
              <span>Safety</span>
            </a>

            <button
              onClick={onNavigateToResearch}
              className="px-3.5 py-1.5 text-xs font-medium text-theme-secondary hover:text-theme-primary hover:bg-surface rounded-full transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-theme-muted" />
              <span>Research</span>
            </button>
          </nav>

          {/* Right Action Bar (Desktop) */}
          <div className="hidden sm:flex items-center gap-2">
            {onOpenResultsClick && (
              <button
                onClick={onOpenResultsClick}
                className="px-3 py-1.5 rounded-lg border border-theme bg-surface hover:bg-surface-subtle text-xs font-medium text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <FileCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                <span>Findings</span>
              </button>
            )}

            <ThemeSwitcher />

            {onOpenUploadClick && (
              <button
                onClick={onOpenUploadClick}
                className="px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-xs font-medium transition-all flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Upload Script</span>
              </button>
            )}
          </div>

          {/* Mobile Bar: Theme switcher + Upload + Menu toggle */}
          <div className="flex sm:hidden items-center gap-1.5">
            <ThemeSwitcher />

            {onOpenUploadClick && (
              <button
                onClick={onOpenUploadClick}
                className="px-2.5 py-1 rounded-md bg-teal-600 text-white text-xs font-medium"
              >
                Upload
              </button>
            )}

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded-lg text-theme-secondary hover:text-theme-primary border border-theme"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="sm:hidden bg-surface border-b border-theme px-4 pt-3 pb-5 mt-2 space-y-1.5 shadow-lg">
          <a
            href="#analyze"
            onClick={(e) => {
              setMobileMenuOpen(false);
              handleLinkClick(e, onNavigateToAnalyze, 'analyze');
            }}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-lg"
          >
            <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>Analyze</span>
          </a>

          <a
            href="#how-it-works"
            onClick={(e) => {
              setMobileMenuOpen(false);
              handleLinkClick(e, onNavigateToHowItWorks, 'how-it-works');
            }}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-lg"
          >
            <HelpCircle className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>How It Works</span>
          </a>

          <a
            href="#safety"
            onClick={(e) => {
              setMobileMenuOpen(false);
              handleLinkClick(e, onNavigateToSafety, 'safety');
            }}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-lg"
          >
            <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>Safety Philosophy</span>
          </a>

          <button
            onClick={() => {
              setMobileMenuOpen(false);
              if (onNavigateToResearch) onNavigateToResearch();
            }}
            className="w-full text-left flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-lg cursor-pointer"
          >
            <FileText className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>Research & Methodology</span>
          </button>

          {onOpenResultsClick && (
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenResultsClick();
              }}
              className="w-full text-left flex items-center gap-2.5 px-3 py-2 text-sm text-teal-700 dark:text-teal-300 hover:bg-surface-subtle rounded-lg cursor-pointer"
            >
              <FileCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />
              <span>Prescription Findings</span>
            </button>
          )}
        </div>
      )}
    </header>
  );
};
