import { ArrowRight, ShieldCheck } from 'lucide-react';

export interface ResearchOverviewSectionProps {
  onOpenResearchPage?: () => void;
}

export const ResearchOverviewSection: React.FC<ResearchOverviewSectionProps> = ({
  onOpenResearchPage,
}) => {
  return (
    <section id="safety-transparency" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="p-8 sm:p-12 rounded-3xl bg-surface border border-theme flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 shadow-xs">
          <div className="space-y-4 max-w-2xl">
            <div className="text-xs sm:text-sm font-semibold text-[#155EEF] dark:text-[#4B8BFF] flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>Clinical Safety &amp; Grounding Architecture</span>
            </div>

            <h2 className="text-2xl sm:text-3xl lg:text-[2.25rem] font-bold tracking-tight text-theme-primary leading-[1.15]">
              Built with uncompromising data integrity and zero AI hallucinations.
            </h2>

            <p className="text-base sm:text-lg text-theme-secondary leading-[1.65]">
              DawaAI is designed from first principles for patient safety. Every extracted medicine is grounded against national drug formularies, evaluated for sound-alike hazards, and verified before dispensing.
            </p>

            <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-xs sm:text-sm text-theme-muted pt-1">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
                <span>CDSCO &amp; RxNorm Grounding</span>
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
                <span>LASA Look-Alike Conflict Screening</span>
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#155EEF] dark:text-[#4B8BFF]" />
                <span>Deterministic Multilingual Posology</span>
              </span>
            </div>
          </div>

          <div className="shrink-0 w-full lg:w-auto">
            {onOpenResearchPage && (
              <button
                onClick={onOpenResearchPage}
                className="w-full sm:w-auto px-7 py-3 rounded-full bg-white dark:bg-[#102A43]/60 hover:bg-[#F7FAFD] dark:hover:bg-[#1E3A5F]/70 border border-[#D0D5DD] dark:border-[#1E3A5F] text-[#102A43] dark:text-white text-sm sm:text-base font-semibold transition-all flex items-center justify-center gap-2.5 shadow-xs hover:shadow-sm cursor-pointer group"
              >
                <span>Explore Safety Architecture</span>
                <ArrowRight className="w-4 h-4 text-theme-muted group-hover:translate-x-0.5 transition-transform" />
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
