import React, { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { ChevronDown, HelpCircle } from 'lucide-react';

interface FaqItem {
  id: string;
  question: string;
  answer: string | React.ReactNode;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    id: 'faq-1',
    question: 'What is DawaAI?',
    answer:
      'DawaAI is an explainable healthcare technology tool designed to help patients and caregivers understand information written on doctor prescriptions. It interprets handwritten penmanship into structured medication details (brand, generic formulation, strength, meal relationship, and schedule) and presents plain-language patient explanations in English, Hindi, and Marathi.',
  },
  {
    id: 'faq-2',
    question: 'Can DawaAI read every handwritten prescription?',
    answer:
      'No. Handwriting legibility varies widely across clinical practice. Severe cursive ambiguity, damaged prescription pads, low image resolution, extreme motion blur, or missing ink strokes can prevent reliable transcription. Rather than guessing or inventing details, DawaAI flags unreadable content as uncertain and advises professional review.',
  },
  {
    id: 'faq-3',
    question: 'What happens when a medicine or instruction is unclear?',
    answer:
      'When ink strokes cannot be resolved with high confidence—or when shorthand instructions like "OD" (once daily) vs "BD" (twice daily) are ambiguous—DawaAI activates Selective Abstention. The unclear field is explicitly marked with a caution state, and the system prompts the patient to verify the instruction with a pharmacist or prescribing clinician before taking medication.',
  },
  {
    id: 'faq-4',
    question: 'Can I upload any image?',
    answer:
      'No. DawaAI is strictly intended for prescription documents. The system validates incoming uploads and automatically rejects non-prescription images—such as landscape photographs, selfies, restaurant receipts, food photos, or textbook pages—with an explicit validation error, preventing fabricated or hallucinated medication results.',
  },
  {
    id: 'faq-5',
    question: 'Does DawaAI replace a doctor or pharmacist?',
    answer:
      'No, absolutely not. DawaAI is an assistive understanding tool, not a diagnostic or prescribing service. It does not replace the professional clinical judgment of a licensed physician or pharmacist. The original signed prescription remains the sole legal and clinical authority for your treatment regimen.',
  },
  {
    id: 'faq-6',
    question: 'How should I protect my prescription information?',
    answer:
      'We treat clinical document privacy with high rigor. Uploaded prescription images are processed in-memory for optical and AI extraction, stored ephemerally in an isolated scratch directory during your active session, and are automatically purged. DawaAI does not sell, market, or share health data with third parties.',
  },
];

export const FaqSection: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();
  const [openId, setOpenId] = useState<string | null>('faq-1');

  const toggleAccordion = (id: string) => {
    setOpenId((prev) => (prev === id ? null : id));
  };

  return (
    <section id="faq" className="py-20 sm:py-28 bg-canvas border-b border-theme relative overflow-hidden">
      {/* Subtle ambient background glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full pointer-events-none opacity-20 dark:opacity-10 blur-3xl"
        style={{
          background: 'radial-gradient(circle, rgba(21, 94, 239, 0.25) 0%, rgba(234, 242, 255, 0.1) 70%, transparent 100%)',
        }}
        aria-hidden="true"
      />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="text-center max-w-2xl mx-auto mb-12 sm:mb-16 space-y-4"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EAF2FF] dark:bg-[#16263D] border border-[#B2DDFF] dark:border-[rgba(255,255,255,0.12)] text-xs font-semibold text-[#155EEF] dark:text-[#84CAFF]">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>FREQUENTLY ASKED QUESTIONS</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-theme-primary leading-[1.12]">
            Answers to common questions about DawaAI
          </h2>

          <p className="text-base sm:text-lg text-theme-secondary leading-relaxed">
            Learn how DawaAI interprets prescriptions, handles uncertainty, and protects patient privacy.
          </p>
        </motion.div>

        {/* Accordion List */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.5, delay: shouldReduceMotion ? 0 : 0.08, ease: 'easeOut' }}
          className="space-y-3.5"
          role="region"
          aria-label="Frequently Asked Questions"
        >
          {FAQ_ITEMS.map((item) => {
            const isOpen = openId === item.id;
            return (
              <div
                key={item.id}
                className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
                  isOpen
                    ? 'bg-surface border-[#155EEF]/40 dark:border-[#4B8BFF]/50 shadow-sm'
                    : 'bg-surface/80 hover:bg-surface card-border-subtle hover:border-[#155EEF]/30'
                }`}
              >
                <button
                  type="button"
                  id={`accordion-btn-${item.id}`}
                  aria-expanded={isOpen}
                  aria-controls={`accordion-panel-${item.id}`}
                  onClick={() => toggleAccordion(item.id)}
                  className="w-full py-4.5 px-6 sm:px-7 flex items-center justify-between text-left gap-4 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#155EEF] focus-visible:ring-offset-2"
                >
                  <span className="text-base sm:text-lg font-semibold text-theme-primary pr-2">
                    {item.question}
                  </span>
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 border transition-all duration-200 ${
                      isOpen
                        ? 'bg-[#155EEF] text-white border-[#155EEF] rotate-180 dark:bg-[#4B8BFF] dark:border-[#4B8BFF]'
                        : 'bg-surface-subtle text-theme-secondary border-theme hover:border-theme-hover'
                    }`}
                  >
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      id={`accordion-panel-${item.id}`}
                      role="region"
                      aria-labelledby={`accordion-btn-${item.id}`}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 sm:px-7 pb-5 pt-1 text-sm sm:text-base text-theme-secondary leading-relaxed border-t border-theme/40">
                        {item.answer}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
};
