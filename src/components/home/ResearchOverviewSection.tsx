import React from 'react';
import { BookOpen, ArrowRight, ShieldCheck } from 'lucide-react';

export interface ResearchOverviewSectionProps {
  onOpenResearchPage?: () => void;
}

export const ResearchOverviewSection: React.FC<ResearchOverviewSectionProps> = ({
  onOpenResearchPage,
}) => {
  return (
    <section id="research" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="p-8 sm:p-12 rounded-3xl bg-surface border border-theme flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 shadow-xs">
          <div className="space-y-4 max-w-2xl">
            <div className="text-xs sm:text-sm font-semibold text-[#7C5A8B] dark:text-[#F472B6] flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5" />
              <span>Academic Research Prototype</span>
            </div>

            <h2 className="text-2xl sm:text-3xl lg:text-[2.25rem] font-bold tracking-tight text-theme-primary leading-[1.1]">
              Built on clinical evidence and rigorous evaluation.
            </h2>

            <p className="text-base sm:text-lg text-theme-secondary leading-[1.65]">
              DawaAI is an assistive research prototype developed for explainable multimodal understanding of handwritten prescriptions, evidence grounding, uncertainty awareness, and multilingual patient explanations.
            </p>

            <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-xs sm:text-sm text-theme-muted pt-1">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#7C5A8B] dark:text-[#F472B6]" />
                <span>Multimodal Vision-Language Architecture</span>
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#7C5A8B] dark:text-[#F472B6]" />
                <span>Formulary Grounding</span>
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#7C5A8B] dark:text-[#F472B6]" />
                <span>Calibrated Selective Abstention</span>
              </span>
            </div>
          </div>

          <div className="shrink-0 w-full lg:w-auto">
            {onOpenResearchPage && (
              <button
                onClick={onOpenResearchPage}
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-surface-subtle hover:bg-surface border border-theme text-theme-primary text-sm sm:text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-xs cursor-pointer group"
              >
                <span>Read Research &amp; Methodology</span>
                <ArrowRight className="w-4 h-4 text-theme-muted group-hover:translate-x-0.5 transition-transform" />
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
