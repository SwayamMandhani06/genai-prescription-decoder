import React from 'react';
import { Camera, FileSearch, ShieldCheck, Languages } from 'lucide-react';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Prescription Intake',
      desc: 'The physical prescription image is brought into focus. Document orientation, stroke contrast, and paper conditions are verified.',
      icon: Camera,
    },
    {
      num: '02',
      title: 'Handwriting Interpretation',
      desc: 'Multimodal vision models analyze cursive pen trajectories, separating letterhead context from handwritten drug posology.',
      icon: FileSearch,
    },
    {
      num: '03',
      title: 'Formulary Verification',
      desc: 'Extracted candidates are matched against official CDSCO and RxNorm databases. Ambiguous or high-risk entries are flagged.',
      icon: ShieldCheck,
    },
    {
      num: '04',
      title: 'Plain-Language Guidance',
      desc: 'Instructions are formulated in patient-friendly English, Hindi, and Marathi, clarifying meal schedules and warnings.',
      icon: Languages,
    },
  ];

  return (
    <section id="how-it-works" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <div className="text-xs font-semibold text-teal-700 dark:text-teal-400">
            Methodology
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-theme-primary">
            How the prescription is processed.
          </h2>
          <p className="text-base text-theme-secondary leading-relaxed">
            A transparent four-stage pipeline that prioritizes medical evidence over blind guesswork.
          </p>
        </div>

        {/* 4 Step Pipeline Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.num}
                className="relative p-6 rounded-2xl bg-surface border border-theme flex flex-col justify-between space-y-4 shadow-xs hover:border-theme-hover transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-bold text-teal-700 dark:text-teal-400">
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
