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
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-theme-primary leading-tight">
          Have a prescription that is difficult to read?
        </h2>

        <p className="text-base sm:text-lg text-theme-secondary max-w-xl mx-auto leading-relaxed">
          Upload an image or select a curated clinic sample to see grounded extraction, formulary verification, and plain-language explanation.
        </p>

        {/* Primary CTA Button */}
        <div className="pt-2">
          {onOpenUpload && (
            <button
              onClick={onOpenUpload}
              className="px-8 py-4 rounded-xl bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-base font-semibold transition-all inline-flex items-center gap-2.5 shadow-sm cursor-pointer group"
            >
              <UploadCloud className="w-5 h-5" />
              <span>Analyze a prescription</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>
          )}
        </div>

        {/* Calm Safety Reminder Nearby */}
        <p className="text-xs text-theme-muted max-w-md mx-auto pt-4 leading-relaxed">
          Assistive research prototype. Does not provide medical diagnosis or replace a licensed physician or pharmacist. Always verify uncertain prescriptions against the signed original.
        </p>
      </div>
    </section>
  );
};
