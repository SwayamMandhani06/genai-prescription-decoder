import React, { useState, useEffect } from 'react';
import { ThemeSwitcher } from './ThemeSwitcher';
import {
  FileText,
  ShieldCheck,
  ScanLine,
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
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        isScrolled
          ? 'glass-nav py-3'
          : 'bg-transparent py-4 sm:py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Logo & Product Identification — Enlarged by 35% for strong visual presence */}
          <button
            onClick={onHomeClick}
            className="flex items-center gap-3 text-left group cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#155EEF] rounded-xl p-1"
            aria-label="DawaAI Home"
          >
            <img
              src="/brand/dawaai-logo.svg"
              alt="DawaAI — Your Prescription, Made Clear."
              className="h-10 sm:h-11 md:h-12 w-auto dark:hidden object-contain transition-transform duration-200 group-hover:scale-[1.02]"
            />
            <img
              src="/brand/dawaai-logo-dark.svg"
              alt="DawaAI — Your Prescription, Made Clear."
              className="h-10 sm:h-11 md:h-12 w-auto hidden dark:block object-contain transition-transform duration-200 group-hover:scale-[1.02]"
            />
          </button>

          {/* Primary Navigation (Desktop) — Distinctive visible glass pill */}
          <nav className="hidden md:flex items-center gap-1 nav-pill-glass px-3 py-1.5 rounded-full shadow-xs">
            <a
              href="#analyze"
              onClick={(e) => handleLinkClick(e, onNavigateToAnalyze, 'analyze')}
              className="px-3.5 py-1.5 text-sm font-semibold text-theme-secondary hover:text-theme-primary hover:bg-surface/80 rounded-full transition-all flex items-center gap-1.5"
            >
              <ScanLine className="w-3.5 h-3.5 text-theme-muted" />
              <span>Analyze</span>
            </a>

            <a
              href="#how-it-works"
              onClick={(e) => handleLinkClick(e, onNavigateToHowItWorks, 'how-it-works')}
              className="px-3.5 py-1.5 text-sm font-semibold text-theme-secondary hover:text-theme-primary hover:bg-surface/80 rounded-full transition-all flex items-center gap-1.5"
            >
              <HelpCircle className="w-3.5 h-3.5 text-theme-muted" />
              <span>How It Works</span>
            </a>

            <a
              href="#safety"
              onClick={(e) => handleLinkClick(e, onNavigateToSafety, 'safety')}
              className="px-3.5 py-1.5 text-sm font-semibold text-theme-secondary hover:text-theme-primary hover:bg-surface/80 rounded-full transition-all flex items-center gap-1.5"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-theme-muted" />
              <span>Safety</span>
            </a>

            <a
              href="#faq"
              onClick={(e) => handleLinkClick(e, undefined, 'faq')}
              className="px-3.5 py-1.5 text-sm font-semibold text-theme-secondary hover:text-theme-primary hover:bg-surface/80 rounded-full transition-all flex items-center gap-1.5"
            >
              <span>FAQ</span>
            </a>

            <button
              onClick={onNavigateToResearch}
              className="px-3.5 py-1.5 text-sm font-semibold text-theme-secondary hover:text-theme-primary hover:bg-surface/80 rounded-full transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-theme-muted" />
              <span>Research</span>
            </button>
          </nav>

          {/* Right Action Bar (Desktop) */}
          <div className="hidden sm:flex items-center gap-2.5">
            {onOpenResultsClick && (
              <button
                onClick={onOpenResultsClick}
                className="px-4 py-2 rounded-full border border-theme bg-surface hover:bg-surface-subtle text-sm font-semibold text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5 cursor-pointer shadow-xs min-h-[46px]"
              >
                <FileCheck className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
                <span>Findings</span>
              </button>
            )}

            <ThemeSwitcher />

            {onOpenUploadClick && (
              <button
                onClick={onOpenUploadClick}
                className="btn-header-cta"
              >
                <UploadCloud className="w-4 h-4" />
                <span>Analyze a Prescription</span>
              </button>
            )}
          </div>

          {/* Mobile Bar: Theme switcher + Upload + Menu toggle */}
          <div className="flex sm:hidden items-center gap-2">
            <ThemeSwitcher />

            {onOpenUploadClick && (
              <button
                onClick={onOpenUploadClick}
                className="btn-header-cta !min-h-[38px] !py-1.5 !px-3.5 !text-xs"
              >
                Upload
              </button>
            )}

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-theme-secondary hover:text-theme-primary border border-theme bg-surface/70"
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
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-xl"
          >
            <ScanLine className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
            <span>Analyze</span>
          </a>

          <a
            href="#how-it-works"
            onClick={(e) => {
              setMobileMenuOpen(false);
              handleLinkClick(e, onNavigateToHowItWorks, 'how-it-works');
            }}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-xl"
          >
            <HelpCircle className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
            <span>How It Works</span>
          </a>

          <a
            href="#safety"
            onClick={(e) => {
              setMobileMenuOpen(false);
              handleLinkClick(e, onNavigateToSafety, 'safety');
            }}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-xl"
          >
            <ShieldCheck className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
            <span>Safety Philosophy</span>
          </a>

          <a
            href="#faq"
            onClick={(e) => {
              setMobileMenuOpen(false);
              handleLinkClick(e, undefined, 'faq');
            }}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-xl"
          >
            <HelpCircle className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
            <span>FAQ</span>
          </a>

          <button
            onClick={() => {
              setMobileMenuOpen(false);
              if (onNavigateToResearch) onNavigateToResearch();
            }}
            className="w-full text-left flex items-center gap-2.5 px-3 py-2 text-sm text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle rounded-xl cursor-pointer"
          >
            <FileText className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
            <span>Research & Methodology</span>
          </button>

          {onOpenResultsClick && (
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenResultsClick();
              }}
              className="w-full text-left flex items-center gap-2.5 px-3 py-2 text-sm text-[#155EEF] dark:text-[#4B8BFF] hover:bg-surface-subtle rounded-xl cursor-pointer font-medium"
            >
              <FileCheck className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF]" />
              <span>Prescription Findings</span>
            </button>
          )}
        </div>
      )}
    </header>
  );
};
