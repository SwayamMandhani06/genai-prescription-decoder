import React from 'react';
import { UploadCloud, ArrowRight } from 'lucide-react';

export interface FinalCtaSectionProps {
  onOpenUpload?: () => void;
}

export const FinalCtaSection: React.FC<FinalCtaSectionProps> = ({ onOpenUpload }) => {
  return (
    <section id="analyze" className="py-24 sm:py-32 bg-canvas">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
        {/* The Exact Prompt Headline */}
        <h2 className="text-3xl sm:text-5xl lg:text-[3.5rem] font-bold tracking-tight text-theme-primary leading-[1.05]">
          Have a prescription that is difficult to read?
        </h2>

        <p className="text-lg sm:text-xl text-theme-secondary max-w-2xl mx-auto leading-[1.65]">
          Upload an image or select a curated clinic sample to see grounded extraction, formulary verification, and plain-language explanation.
        </p>

        {/* Primary CTA Button */}
        <div className="pt-3">
          {onOpenUpload && (
            <button
              onClick={onOpenUpload}
              className="px-9 py-4.5 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base sm:text-lg font-semibold transition-all inline-flex items-center gap-3 shadow-md hover:shadow-lg cursor-pointer group"
            >
              <UploadCloud className="w-5 h-5" />
              <span>Analyze a prescription</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          )}
        </div>

        {/* Calm Safety Reminder Nearby */}
        <p className="text-xs sm:text-sm text-theme-muted max-w-md mx-auto pt-4 leading-[1.6]">
          Assistive research prototype. Does not provide medical diagnosis or replace a licensed physician or pharmacist. Always verify uncertain prescriptions against the signed original.
        </p>
      </div>
    </section>
  );
};
