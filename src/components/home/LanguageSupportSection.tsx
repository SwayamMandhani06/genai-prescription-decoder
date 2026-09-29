import React, { useState } from 'react';
import { Languages, Volume2, CheckCircle2, Clock, Utensils, AlertCircle } from 'lucide-react';

export const LanguageSupportSection: React.FC = () => {
  const [activeLang, setActiveLang] = useState<'en' | 'hi' | 'mr'>('en');

  const languages = [
    { id: 'en' as const, label: 'English', script: 'English', brandTagline: 'Your Prescription, Made Clear.' },
    { id: 'hi' as const, label: 'Hindi', script: 'हिंदी', brandTagline: 'आपकी दवा की जानकारी' },
    { id: 'mr' as const, label: 'Marathi', script: 'मराठी', brandTagline: 'तुमच्या औषधाची माहिती' },
  ];

  const content = {
    en: {
      headline: 'Medical guidance in the patient’s language.',
      subhead: 'Converting clinical shorthand into clear, unambiguous directions.',
      brandMotto: 'Your Prescription, Made Clear.',
      drug: 'Augmentin 625 Duo Tablet',
      generic: 'Amoxicillin (500mg) + Clavulanic Acid (125mg)',
      schedule: 'Take 1 tablet twice a day (morning and night), strictly after meals.',
      timing: 'Morning (9:00 AM) and Evening (9:00 PM)',
      meals: 'Always take with or immediately after a meal to prevent stomach upset.',
      precaution: 'Complete all 5 days of medicine even if fever or pain subsides.',
      audioLabel: 'Listen to instruction in English',
    },
    hi: {
      headline: 'मरीज़ की अपनी भाषा में स्पष्ट चिकित्सकीय मार्गदर्शन।',
      subhead: 'कठिन डॉक्टरी संक्षिप्त अक्षरों को सरल और समझने योग्य निर्देशों में बदलना।',
      brandMotto: 'आपकी दवा की जानकारी',
      drug: 'Augmentin 625 Duo Tablet (ऑगमेंटिन 625)',
      generic: 'Amoxicillin (500mg) + Clavulanic Acid (125mg)',
      schedule: 'दिन में 2 बार 1 गोली लें (सुबह और रात), हमेशा भोजन के बाद।',
      timing: 'सुबह (9:00 बजे) और रात (9:00 बजे)',
      meals: 'पेट की ख़राबी से बचने के लिए हमेशा भोजन के साथ या तुरंत बाद लें।',
      precaution: 'बुखार या दर्द ठीक होने पर भी पूरे 5 दिनों की खुराक समाप्त करें।',
      audioLabel: 'हिंदी में निर्देश सुनें',
    },
    mr: {
      headline: 'रुग्णाच्या स्वतःच्या भाषेत स्पष्ट वैद्यकीय मार्गदर्शन.',
      subhead: 'क्लिष्ट डॉक्टरी संक्षेप सोप्या आणि समजण्याजोग्या सूचनांमध्ये रूपांतरित करणे.',
      brandMotto: 'तुमच्या औषधाची माहिती',
      drug: 'Augmentin 625 Duo Tablet (ऑगमेंटिन ६२५)',
      generic: 'Amoxicillin (500mg) + Clavulanic Acid (125mg)',
      schedule: 'दिवसातून २ वेळा १ गोळी घ्या (सकाळी आणि रात्री), नेहमी जेवणानंतर.',
      timing: 'सकाळी (९:०० वाजता) आणि रात्री (९:०० वाजता)',
      meals: 'पोट खराब होऊ नये म्हणून नेहमी जेवणासोबत किंवा जेवणानंतर लगेच घ्या.',
      precaution: 'ताप किंवा वेदना थांबली तरीही पूर्ण ५ दिवसांचा औषधांचा कोर्स संपवा.',
      audioLabel: 'मराठीत सूचना ऐका',
    },
  };

  const active = content[activeLang];

  return (
    <section id="languages" className="py-20 sm:py-28 bg-canvas border-b border-theme">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
          {/* Left Column: Context & Controls */}
          <div className="lg:col-span-5 space-y-6">
            <div className="text-sm font-semibold text-[#7C5A8B] dark:text-[#F472B6] flex items-center gap-2">
              <Languages className="w-4 h-4" />
              <span>Multilingual Posology</span>
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-[2.5rem] font-bold tracking-tight text-theme-primary leading-[1.08]">
              Medical guidance in the patient&rsquo;s language.
            </h2>

            <p className="text-lg sm:text-xl text-theme-secondary leading-[1.65]">
              Prescriptions in India are written in Latin abbreviations like <em>1-0-1 PC</em> or <em>TDS AC</em>. DawaAI converts shorthand into actionable, patient-friendly guidance in English, Hindi, and Marathi.
            </p>

            {/* Official DawaAI Brand Language Banner */}
            <div className="p-3.5 rounded-xl bg-surface border border-theme shadow-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-brand-serif font-bold text-base text-[#4A2E4D] dark:text-white">Dawa</span>
                <span className="font-bold text-base text-[#F472B6]">AI</span>
                <span className="text-xs text-theme-muted">&bull;</span>
                <span className="text-xs font-semibold text-theme-primary">{active.brandMotto}</span>
              </div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#7C5A8B] dark:text-[#F472B6]">
                {activeLang.toUpperCase()}
              </span>
            </div>

            {/* Interactive Language Selector Tabs */}
            <div className="space-y-2 pt-1">
              <div className="text-xs font-semibold uppercase tracking-wider text-theme-muted">
                Switch Language:
              </div>
              <div className="inline-flex p-1.5 rounded-2xl bg-surface border border-theme shadow-xs">
                {languages.map((lang) => (
                  <button
                    key={lang.id}
                    onClick={() => setActiveLang(lang.id)}
                    className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                      activeLang === lang.id
                        ? 'bg-[#4A2E4D] dark:bg-[#F472B6] text-white dark:text-[#2E2233] shadow-xs'
                        : 'text-theme-secondary hover:text-theme-primary'
                    }`}
                  >
                    <span>{lang.script}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-2 flex items-center gap-2 text-xs sm:text-sm text-theme-muted">
              <CheckCircle2 className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6] shrink-0" />
              <span>Standardized medical glossaries validated for Indian vernaculars</span>
            </div>
          </div>

          {/* Right Column: Animated Explanation Display */}
          <div className="lg:col-span-7">
            <div className="p-7 sm:p-9 rounded-3xl bg-surface shadow-elevated-card border border-theme space-y-6 transition-all duration-300">
              {/* Header with Drug Name and Audio Button */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-theme pb-4">
                <div>
                  <div className="text-xs font-semibold text-[#7C5A8B] dark:text-[#F472B6]">
                    Patient guidance card &middot; {languages.find((l) => l.id === activeLang)?.label}
                  </div>
                  <h3 className="text-xl sm:text-2xl font-bold text-theme-primary mt-1">
                    {active.drug}
                  </h3>
                  <p className="text-sm text-theme-secondary mt-0.5">
                    {active.generic}
                  </p>
                </div>

                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-subtle text-xs font-semibold text-theme-primary border border-theme">
                  <Volume2 className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6]" />
                  <span>{active.audioLabel}</span>
                </div>
              </div>

              {/* Animated Detail Rows */}
              <div
                key={activeLang}
                className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
              >
                {/* Primary Schedule Instruction */}
                <div className="p-4 sm:p-5 rounded-xl bg-surface-subtle/70 space-y-1.5">
                  <div className="text-xs font-semibold text-[#7C5A8B] dark:text-[#F472B6] flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>How &amp; when to take</span>
                  </div>
                  <p className="text-lg sm:text-xl font-bold text-theme-primary leading-snug">
                    {active.schedule}
                  </p>
                  <p className="text-sm text-theme-secondary pt-0.5">
                    {active.timing}
                  </p>
                </div>

                {/* Dietary Condition & Precaution Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs sm:text-sm">
                  <div className="p-3.5 rounded-xl bg-surface-subtle/50 space-y-1">
                    <div className="font-semibold text-theme-primary flex items-center gap-1.5">
                      <Utensils className="w-3.5 h-3.5 text-[#7C5A8B] dark:text-[#F472B6]" />
                      <span>Meal relationship</span>
                    </div>
                    <p className="text-theme-secondary leading-[1.6]">
                      {active.meals}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface-subtle/50 space-y-1">
                    <div className="font-semibold text-theme-primary flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                      <span>Important precaution</span>
                    </div>
                    <p className="text-theme-secondary leading-[1.6]">
                      {active.precaution}
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer reassurance */}
              <div className="text-xs text-theme-muted pt-2 border-t border-theme flex items-center justify-between">
                <span>Original English doctor handwriting preserved side-by-side</span>
                <span>English &bull; Hindi &bull; Marathi</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
