import React, { useState } from 'react';
import { MULTILINGUAL_EXPLANATIONS } from '../../data/multilingualCatalog';
import { LanguageCode } from '../../types/explanation.types';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import {
  Sun,
  CloudSun,
  Sunset,
  Moon,
  Play,
  Pause,
  Clock,
  Utensils,
  CheckCircle2,
} from 'lucide-react';

export const MultilingualExplanationSection: React.FC = () => {
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('hi');
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  const sampleData = MULTILINGUAL_EXPLANATIONS['rx-sample-1'][selectedLanguage];
  const primaryMed = sampleData.medications[0]; // Augmentin 625

  const timeSlots = [
    { period: 'morning', label: 'Morning', icon: Sun, color: 'text-amber-400' },
    { period: 'afternoon', label: 'Afternoon', icon: CloudSun, color: 'text-sky-400' },
    { period: 'evening', label: 'Evening', icon: Sunset, color: 'text-orange-400' },
    { period: 'night', label: 'Night', icon: Moon, color: 'text-indigo-400' },
  ];

  return (
    <section id="multilingual" className="py-20 bg-canvas border-t border-theme relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-14 space-y-3">
          <Badge variant="cyan" size="sm" dot>
            Vernacular Accessibility
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-theme-primary tracking-tight">
            Patient-Centric Multilingual Posology
          </h2>
          <p className="text-sm sm:text-base text-theme-secondary">
            Medical compliance fails when patients cannot decipher instructions. AURA-Rx translates cryptic clinical abbreviations into clear posology schedules and spoken audio guidance in English, Hindi, and Marathi.
          </p>
        </div>

        {/* Language Switcher Tabs */}
        <div className="flex justify-center mb-10">
          <div className="inline-flex bg-surface-subtle p-1.5 rounded-2xl border border-theme shadow-xs">
            {[
              { code: 'en' as LanguageCode, label: 'English', sub: 'Latin Script' },
              { code: 'hi' as LanguageCode, label: 'हिन्दी (Hindi)', sub: 'Devanagari' },
              { code: 'mr' as LanguageCode, label: 'मराठी (Marathi)', sub: 'Devanagari' },
            ].map((item) => (
              <button
                key={item.code}
                onClick={() => setSelectedLanguage(item.code)}
                className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all cursor-pointer flex flex-col items-center gap-0.5 ${
                  selectedLanguage === item.code
                    ? 'bg-teal-600 text-white font-bold shadow-xs'
                    : 'text-theme-secondary hover:text-theme-primary hover:bg-surface'
                }`}
              >
                <span>{item.label}</span>
                <span
                  className={`text-[10px] ${
                    selectedLanguage === item.code ? 'text-teal-100' : 'text-theme-muted'
                  }`}
                >
                  {item.sub}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Featured Posology Schedule Card */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left: Interactive Medication Posology Schedule */}
          <div className="lg:col-span-8">
            <Card variant="glass" padding="lg" className="border-theme shadow-xs">
              <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-theme mb-6">
                <div>
                  <Badge variant="cyan" size="xs" className="mb-1.5">
                    {selectedLanguage === 'en'
                      ? 'Antibiotic Schedule'
                      : selectedLanguage === 'hi'
                      ? 'एंटीबायोटिक खुराक'
                      : 'अँटिबायोटिक वेळापत्रक'}
                  </Badge>
                  <h3 className="text-xl font-extrabold text-theme-primary tracking-tight">
                    {primaryMed.localizedName}
                  </h3>
                  <p className="text-xs font-mono text-theme-secondary mt-1">
                    {primaryMed.genericName} · {primaryMed.dosageSummary}
                  </p>
                </div>

                {/* Spoken Audio Demonstration Widget */}
                <button
                  onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                  className="px-3.5 py-2 rounded-xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 hover:border-teal-400 text-teal-800 dark:text-teal-300 text-xs font-mono flex items-center gap-2 transition-all cursor-pointer shadow-xs"
                >
                  {isPlayingAudio ? (
                    <Pause className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  ) : (
                    <Play className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  )}
                  <span>
                    {isPlayingAudio ? 'Pause Voice Explainer' : 'Listen Vernacular Audio (AI)'}
                  </span>
                  {isPlayingAudio && (
                    <div className="flex items-center gap-0.5 ml-1">
                      <span className="w-1 h-3 bg-teal-600 dark:bg-teal-400 animate-pulse" />
                      <span className="w-1 h-4 bg-teal-600 dark:bg-teal-400 animate-pulse delay-75" />
                      <span className="w-1 h-2 bg-teal-600 dark:bg-teal-400 animate-pulse delay-150" />
                    </div>
                  )}
                </button>
              </div>

              {/* Purpose & Clinical Meaning */}
              <div className="mb-6 p-4 rounded-xl bg-surface-subtle border border-theme space-y-1">
                <span className="text-[11px] font-mono text-theme-muted uppercase tracking-wider block">
                  {selectedLanguage === 'en'
                    ? 'Why this medicine was prescribed:'
                    : selectedLanguage === 'hi'
                    ? 'यह दवा किसलिए दी गई है:'
                    : 'हे औषध कशासाठी दिले आहे:'}
                </span>
                <p className="text-xs sm:text-sm text-theme-primary leading-relaxed font-medium">
                  {primaryMed.purpose}
                </p>
              </div>

              {/* 4-Period Visual Dosage Schedule Timeline */}
              <div className="space-y-2 mb-6">
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-theme-muted block mb-3">
                  {selectedLanguage === 'en'
                    ? 'Daily Dosage Schedule (1-0-1):'
                    : selectedLanguage === 'hi'
                    ? 'दैनिक खुराक का समय (1-0-1):'
                    : 'दररोजच्या डोसची वेळ (1-0-1):'}
                </span>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {primaryMed.schedule.map((slot, sIdx) => {
                    const slotMeta = timeSlots[sIdx];
                    const SlotIcon = slotMeta.icon;

                    return (
                      <div
                        key={slot.period}
                        className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between min-h-[140px] ${
                          slot.isActive
                            ? 'bg-sky-50 dark:bg-sky-950/30 border-sky-300 dark:border-sky-800 shadow-xs'
                            : 'bg-surface-subtle/60 border-theme opacity-60'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-mono font-semibold text-theme-primary">
                            {slotMeta.label}
                          </span>
                          <SlotIcon className={`w-4 h-4 ${slotMeta.color}`} />
                        </div>

                        <div>
                          <div
                            className={`text-base font-bold font-mono ${
                              slot.isActive ? 'text-theme-primary' : 'text-theme-muted'
                            }`}
                          >
                            {slot.amount}
                          </div>
                          <div className="text-[11px] font-mono text-teal-700 dark:text-teal-400 mt-0.5">
                            {slot.timeRange}
                          </div>
                        </div>

                        <div className="mt-2 pt-2 border-t border-theme text-[10px] text-theme-secondary line-clamp-2">
                          {slot.mealRelation}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Instructions Bar */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono pt-4 border-t border-theme">
                <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-1">
                  <div className="text-theme-muted flex items-center gap-1.5 text-[11px]">
                    <Utensils className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                    <span>Food Instruction:</span>
                  </div>
                  <div className="text-theme-primary font-medium">{primaryMed.foodInstruction}</div>
                </div>

                <div className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-1">
                  <div className="text-theme-muted flex items-center gap-1.5 text-[11px]">
                    <Clock className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                    <span>Duration:</span>
                  </div>
                  <div className="text-theme-primary font-medium">{primaryMed.durationString}</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right: Accompanying Medications & Patient Advice Card */}
          <div className="lg:col-span-4 space-y-4">
            <div className="p-5 rounded-2xl bg-surface border border-theme shadow-xs space-y-3">
              <span className="text-xs font-mono font-bold text-theme-primary uppercase tracking-wider block">
                {selectedLanguage === 'en'
                  ? 'All Script Medications'
                  : selectedLanguage === 'hi'
                  ? 'पर्चे की अन्य दवाएं'
                  : 'प्रिस्क्रिप्शनमधील इतर औषधे'}
              </span>

              {sampleData.medications.map((m) => (
                <div
                  key={m.medicineId}
                  className="p-3 rounded-xl bg-surface-subtle border border-theme space-y-1"
                >
                  <div className="text-xs font-bold text-theme-primary">{m.localizedName}</div>
                  <div className="text-[11px] text-theme-secondary">{m.purpose}</div>
                  <div className="text-[10px] font-mono text-teal-700 dark:text-teal-400 font-semibold">{m.dosageSummary}</div>
                </div>
              ))}
            </div>

            {/* Overall Advice Callout */}
            <div className="p-5 rounded-2xl bg-sky-50 dark:bg-sky-950/20 border border-sky-200 dark:border-sky-800/80 space-y-2 text-xs">
              <div className="font-mono font-bold text-sky-900 dark:text-sky-300 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                <span>
                  {selectedLanguage === 'en'
                    ? 'General Recovery Advice'
                    : selectedLanguage === 'hi'
                    ? 'स्वास्थ्य सुधार परामर्श'
                    : 'आरोग्य सुधारणा सल्ला'}
                </span>
              </div>
              <p className="text-sky-950 dark:text-sky-200 leading-relaxed font-sans">
                {sampleData.overallPatientAdvice}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
