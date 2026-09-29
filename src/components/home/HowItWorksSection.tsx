import React from 'react';
import { Camera, FileSearch, ShieldCheck, Languages } from 'lucide-react';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: '1. Upload',
      desc: 'High-resolution prescription intake with automated image quality inspection, stroke contrast checks, and blur screening.',
      icon: Camera,
    },
    {
      num: '02',
      title: '2. Understand',
      desc: 'Multimodal AI extracts localized cursive pen strokes into structured medication name, strength, frequency, and duration slots.',
      icon: FileSearch,
    },
    {
      num: '03',
      title: '3. Verify',
      desc: 'Candidates are cross-referenced with CDSCO and RxNorm databases, triggering selective abstention and LASA alerts when ambiguous.',
      icon: ShieldCheck,
    },
    {
      num: '04',
      title: '4. Explain',
      desc: 'Empathetic, clear patient guidance generated in English, Hindi, and Marathi with meal schedules and safety precautions.',
      icon: Languages,
    },
  ];

  return (
    <section id="how-it-works" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <div className="text-xs font-semibold text-[#7C5A8B] dark:text-[#F472B6]">
            Transparent Methodology
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-theme-primary">
            How DawaAI processes your prescription.
          </h2>
          <p className="text-base text-theme-secondary leading-relaxed">
            A transparent four-stage pipeline: Upload &rarr; Understand &rarr; Verify &rarr; Explain.
          </p>
        </div>

        {/* 4 Step Pipeline Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.num}
                className="relative p-6 rounded-2xl bg-surface border border-theme flex flex-col justify-between space-y-4 shadow-xs hover:border-[#F472B6]/40 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-bold text-[#7C5A8B] dark:text-[#F472B6]">
                      Stage {step.num}
                    </span>
                    <Icon className="w-5 h-5 text-theme-muted" />
                  </div>
                  <h3 className="text-base font-bold text-theme-primary mb-2">
                    {step.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-theme-secondary leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
