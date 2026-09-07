import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';

export const CoreCapabilitiesSection: React.FC = () => {
  const [explainLang, setExplainLang] = useState<'en' | 'hi' | 'mr'>('en');

  const explanationPhrases = {
    en: {
      lang: 'English',
      instruction: 'Take 1 tablet after breakfast and 1 tablet after dinner for 5 days.',
      note: 'Complete the entire course even if symptoms subside.',
      badge: 'Patient-friendly posology',
    },
    hi: {
      lang: 'हिन्दी',
      instruction: 'नाश्ते के बाद 1 गोली और रात के खाने के बाद 1 गोली लें (5 दिनों तक)।',
      note: 'लक्षण कम होने पर भी डॉक्टर द्वारा बताया गया 5 दिनों का कोर्स पूरा करें।',
      badge: 'स्पष्ट रोगी मार्गदर्शन',
    },
    mr: {
      lang: 'मराठी',
      instruction: 'सकाळच्या नाश्त्यानंतर 1 गोळी आणि रात्रीच्या जेवणानंतर 1 गोळी घ्या (5 दिवस).',
      note: 'लक्षणे कमी झाली तरी डॉक्टरांनी दिलेला 5 दिवसांचा पूर्ण कोर्स संपवा.',
      badge: 'रुग्ण-स्नेही मार्गदर्शन',
    },
  };

  return (
    <section id="capabilities" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Intro */}
        <div className="max-w-3xl mb-16 sm:mb-20 space-y-3">
          <div className="text-sm font-semibold text-teal-700 dark:text-teal-400">
            Core Architecture
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-[2.5rem] font-bold tracking-tight text-theme-primary leading-[1.08]">
            Designed for medical clarity, safety, and evidence.
          </h2>
          <p className="text-lg sm:text-xl text-theme-secondary leading-[1.65]">
            Three foundational capabilities ensure that AURA-Rx operates with clinical accountability.
          </p>
        </div>

        {/* 3 Visually Distinct Capabilities */}
        <div className="space-y-20">
          {/* Capability 01: UNDERSTAND */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-14 items-center">
            <div className="lg:col-span-5 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-teal-700 dark:text-teal-400">
                1. Understanding Handwriting
              </span>
              <h3 className="text-2xl sm:text-3xl lg:text-[2rem] font-bold tracking-tight text-theme-primary leading-snug">
                Structured extraction from handwritten prescriptions.
              </h3>
              <p className="text-base sm:text-lg text-theme-secondary leading-[1.65]">
                Rather than treating cursive scrawl as unconstrained text, our vision pipeline isolates localized ink stroke paths, disentangles clinical shorthands (such as 1-0-1, PC, AC, and TDS), and maps them into rigorous clinical slots.
              </p>
              <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-theme-muted pt-1">
                <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                <span>Extracts drug, strength, frequency, timing &amp; duration</span>
              </div>
            </div>

            {/* Visual 1: Token Dissection Diagram */}
            <div className="lg:col-span-7 p-6 sm:p-8 rounded-2xl bg-surface border border-theme shadow-xs space-y-5">
              <div className="flex items-center justify-between text-xs text-theme-muted pb-3 border-b border-theme">
                <span className="font-semibold text-xs text-theme-primary">
                  Stroke parsing &amp; slot extraction
                </span>
              </div>

              {/* Raw handwritten ink mockup */}
              <div className="p-3.5 rounded-xl bg-surface-subtle border border-theme flex items-center justify-between">
                <span className="font-serif italic text-lg text-theme-primary font-bold">
                  ℞ Augm 625 1-0-1 PC x 5d
                </span>
                <span className="text-xs text-theme-muted font-medium">
                  Doctor pen ink
                </span>
              </div>

              {/* Arrow Connector */}
              <div className="flex items-center justify-center text-xs text-theme-muted gap-1">
                <span>&darr; Structured parsing &darr;</span>
              </div>

              {/* Structured Extracted Slots - Clean typographic grid without 6 box-in-a-box cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs pt-1">
                <div>
                  <span className="text-[11px] text-theme-muted block">Medicine</span>
                  <span className="font-bold text-theme-primary text-sm">Augmentin</span>
                </div>
                <div>
                  <span className="text-[11px] text-theme-muted block">Strength</span>
                  <span className="font-bold text-theme-primary text-sm">625 mg</span>
                </div>
                <div>
                  <span className="text-[11px] text-theme-muted block">Frequency</span>
                  <span className="font-bold text-theme-primary text-sm">Twice Daily (1-0-1)</span>
                </div>
                <div>
                  <span className="text-[11px] text-theme-muted block">Condition</span>
                  <span className="font-bold text-theme-primary text-sm">After Meals (PC)</span>
                </div>
                <div>
                  <span className="text-[11px] text-theme-muted block">Duration</span>
                  <span className="font-bold text-theme-primary text-sm">5 Days</span>
                </div>
                <div>
                  <span className="text-[11px] text-theme-muted block">Status</span>
                  <span className="font-semibold text-emerald-700 dark:text-emerald-400 text-sm">Verified match</span>
                </div>
              </div>
            </div>
          </div>

          {/* Capability 02: VERIFY */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
            {/* Visual 2: Evidence Grounding & LASA Check (Placed on Left for Asymmetry) */}
            <div className="order-2 lg:order-1 lg:col-span-7 p-6 sm:p-8 rounded-2xl bg-surface border border-theme shadow-xs space-y-4">
              <div className="flex items-center justify-between text-xs text-theme-muted pb-3 border-b border-theme">
                <span className="font-semibold text-xs text-theme-primary">
                  Clinical formulary &amp; sound-alike safety
                </span>
                <span className="text-xs text-teal-700 dark:text-teal-400 font-medium">CDSCO / RxNorm</span>
              </div>

              {/* Verified Item */}
              <div className="p-3.5 rounded-xl bg-surface-subtle border border-theme space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <span>Amoxicillin + Potassium Clavulanate</span>
                  </span>
                  <span className="text-xs text-theme-muted font-mono">
                    RxNorm #213169
                  </span>
                </div>
                <p className="text-xs text-theme-secondary">
                  Exact formulary match in CDSCO National List of Essential Medicines. Safe posology parameters confirmed.
                </p>
              </div>

              {/* LASA Safety Alert */}
              <div className="p-3.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-900 dark:text-amber-300 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    <span>Sound-alike conflict alert</span>
                  </span>
                  <span className="text-[11px] text-amber-800 dark:text-amber-300 font-medium">
                    High Alert Pair
                  </span>
                </div>
                <div className="text-xs font-mono text-amber-900 dark:text-amber-200 flex items-center gap-2 pt-1">
                  <span className="px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-900/50">hydr<strong>OXY</strong>zine (25mg)</span>
                  <span className="text-amber-500">vs</span>
                  <span className="px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-900/50">hydr<strong>ALA</strong>zine (25mg)</span>
                </div>
                <p className="text-[11px] text-amber-800 dark:text-amber-400">
                  Antihistamine vs Antihypertensive risk. Cursive loop is ambiguous &mdash; verification required before dispensing.
                </p>
              </div>
            </div>

            <div className="order-1 lg:order-2 lg:col-span-5 space-y-4">
              <span className="text-xs font-bold text-teal-700 dark:text-teal-400">
                2. Verifying candidates
              </span>
              <h3 className="text-2xl sm:text-3xl lg:text-[2rem] font-bold tracking-tight text-theme-primary leading-snug">
                Evidence-grounded medicine validation and ambiguity detection.
              </h3>
              <p className="text-base sm:text-lg text-theme-secondary leading-[1.65]">
                Every extracted candidate is cross-referenced against authoritative clinical databases. When severe Look-Alike Sound-Alike (LASA) pairs or low-confidence strokes appear, the system applies TALL MAN lettering and flags them rather than guessing.
              </p>
              <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-theme-muted pt-1">
                <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                <span>CDSCO India &amp; US NLM RxNorm ontological verification</span>
              </div>
            </div>
          </div>

          {/* Capability 03: EXPLAIN */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
            <div className="lg:col-span-5 space-y-4">
              <span className="text-xs font-bold text-teal-700 dark:text-teal-400">
                3. Explaining posology
              </span>
              <h3 className="text-2xl sm:text-3xl lg:text-[2rem] font-bold tracking-tight text-theme-primary leading-snug">
                Patient-friendly English, Hindi and Marathi explanations.
              </h3>
              <p className="text-base sm:text-lg text-theme-secondary leading-[1.65]">
                Medical prescriptions are often written using Latin abbreviations that confuse patients. AURA-Rx converts complicated regimens into empathetic, plain-language guidance in regional languages while preserving the original signed prescription.
              </p>
              <div className="flex items-center gap-2 text-xs sm:text-sm font-medium text-theme-muted pt-1">
                <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                <span>Native Devanagari script for Hindi and Marathi</span>
              </div>
            </div>

            {/* Visual 3: Interactive Multilingual Posology Card */}
            <div className="lg:col-span-7 p-6 sm:p-8 rounded-2xl bg-surface border border-theme shadow-xs space-y-5">
              <div className="flex items-center justify-between text-xs text-theme-muted pb-3 border-b border-theme">
                <span className="font-semibold text-xs text-theme-primary">
                  Regional language explanation
                </span>

                {/* Switcher Pills */}
                <div className="flex items-center gap-1.5">
                  {(['en', 'hi', 'mr'] as const).map((lang) => (
                    <button
                      key={lang}
                      onClick={() => setExplainLang(lang)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                        explainLang === lang
                          ? 'bg-teal-600 text-white shadow-xs font-semibold'
                          : 'bg-surface-subtle hover:bg-surface border border-theme text-theme-secondary hover:text-theme-primary'
                      }`}
                    >
                      {explanationPhrases[lang].lang}
                    </button>
                  ))}
                </div>
              </div>

              {/* Active Explanation Content */}
              <div className="space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold text-theme-primary">
                    Augmentin 625 Duo &middot; Oral Tablet
                  </div>
                  <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-teal-50 dark:bg-teal-950/50 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 font-medium">
                    {explanationPhrases[explainLang].badge}
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-2">
                  <div className="text-xs font-semibold text-teal-700 dark:text-teal-400">
                    Dosing Schedule &amp; Timing
                  </div>
                  <p className="text-sm sm:text-base font-medium text-theme-primary leading-relaxed">
                    {explanationPhrases[explainLang].instruction}
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-surface border border-theme text-xs text-theme-secondary flex items-start gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  <span>{explanationPhrases[explainLang].note}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
