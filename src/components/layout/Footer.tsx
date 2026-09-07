import React from 'react';
import { FileText, ShieldCheck, ArrowUpRight } from 'lucide-react';

export interface FooterProps {
  onNavigateToResearch?: () => void;
  onOpenUpload?: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigateToResearch, onOpenUpload }) => {
  return (
    <footer className="bg-surface border-t border-theme pt-12 pb-10 text-theme-secondary transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 pb-10 border-b border-theme">
          {/* Brand & Project Description */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 flex items-center justify-center text-teal-700 dark:text-teal-300">
                <FileText className="w-4 h-4" />
              </div>
              <span className="font-bold text-base text-theme-primary">
                AURA<span className="text-teal-600 dark:text-teal-400">-Rx</span>
              </span>
            </div>
            <p className="text-xs text-theme-secondary leading-relaxed">
              Explainable Multimodal AI for Handwritten Prescription Understanding. An academic research prototype designed for clinical clarity, evidence grounding, and patient safety.
            </p>
            <div className="text-[11px] text-theme-muted font-mono">
              CDSCO &bull; RxNorm &bull; EN / HI / MR
            </div>
          </div>

          {/* Navigation Links: Analyze & How It Works */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-theme-primary">
              Product
            </h4>
            <ul className="space-y-2 text-xs">
              {onOpenUpload && (
                <li>
                  <button
                    onClick={onOpenUpload}
                    className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors cursor-pointer text-left"
                  >
                    Analyze a Prescription
                  </button>
                </li>
              )}
              <li>
                <a href="#transformation" className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">
                  How It Works (Transformation)
                </a>
              </li>
              <li>
                <a href="#capabilities" className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">
                  Core Capabilities
                </a>
              </li>
              <li>
                <a href="#languages" className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">
                  Multilingual Explanations
                </a>
              </li>
            </ul>
          </div>

          {/* Safety, Research & GitHub */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-theme-primary">
              Safety &amp; Source
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#safety" className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">
                  Safety &amp; Uncertainty Philosophy
                </a>
              </li>
              <li>
                <button
                  onClick={onNavigateToResearch}
                  className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors cursor-pointer text-left"
                >
                  Research &amp; Methodology
                </button>
              </li>
              <li>
                <a
                  href="https://github.com/SwayamMandhani06/genai-prescription-decoder"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:text-teal-600 dark:hover:text-teal-400 transition-colors"
                >
                  <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current" aria-hidden="true">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                  <span>GitHub Repository</span>
                  <ArrowUpRight className="w-3 h-3 text-theme-muted" />
                </a>
              </li>
            </ul>
          </div>

          {/* Team & Capstone Information */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-theme-primary flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              <span>Academic Capstone</span>
            </h4>
            <p className="text-[11px] text-theme-muted leading-relaxed">
              Multidisciplinary Engineering Capstone Project. Supervised academic prototype for assistive clinical workflow safety. Does not dispense medical advice.
            </p>
            <div className="text-[11px] text-theme-secondary font-medium">
              Lead Architect &amp; Research Team
            </div>
          </div>
        </div>

        {/* Compact Bottom Bar */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-theme-muted">
          <div>
            &copy; {new Date().getFullYear()} AURA-Rx &middot; All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <a href="#safety" className="hover:underline">Safety Disclaimer</a>
            <span>&bull;</span>
            <button onClick={onNavigateToResearch} className="hover:underline cursor-pointer">Methodology</button>
          </div>
        </div>
      </div>
    </footer>
  );
};
