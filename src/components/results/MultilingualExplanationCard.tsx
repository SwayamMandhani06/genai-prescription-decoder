import React, { useState } from 'react';
import { MultilingualExplanationContent } from '../../types/prescription.types';
import {
  Globe,
  Sun,
  CloudSun,
  Sunset,
  Moon,
  Volume2,
  VolumeX,
  Sparkles,
} from 'lucide-react';

export interface MultilingualExplanationCardProps {
  multilingual: {
    en: MultilingualExplanationContent;
    hi: MultilingualExplanationContent;
    mr: MultilingualExplanationContent;
  };
}

export type SupportedLanguage = 'en' | 'hi' | 'mr';

export const MultilingualExplanationCard: React.FC<MultilingualExplanationCardProps> = ({
  multilingual,
}) => {
  const [activeLang, setActiveLang] = useState<SupportedLanguage>('en');
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  const currentContent = multilingual[activeLang] || multilingual.en;

  const languages = [
    { code: 'en' as SupportedLanguage, label: 'English', sub: 'Clinical' },
    { code: 'hi' as SupportedLanguage, label: 'हिन्दी', sub: 'Hindi' },
    { code: 'mr' as SupportedLanguage, label: 'मराठी', sub: 'Marathi' },
  ];

  const getSlotIcon = (iconName: string) => {
    switch (iconName) {
      case 'Sun':
        return Sun;
      case 'CloudSun':
        return CloudSun;
      case 'Sunset':
        return Sunset;
      case 'Moon':
        return Moon;
      default:
        return Sun;
    }
  };

  return (
    <div className="rounded-2xl border border-theme bg-surface p-5 sm:p-6 space-y-5 shadow-xs transition-colors">
      {/* Header with Language Segmented Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-theme pb-4">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-teal-600 dark:text-teal-400" />
          <div>
            <h3 className="text-sm font-bold text-theme-primary tracking-tight">
              Patient Posology &amp; Instructions
            </h3>
            <p className="text-xs text-theme-secondary">
              Plain-Language Guidance in English, Hindi, and Marathi
            </p>
          </div>
        </div>

        {/* Language Switcher Buttons */}
        <div className="flex items-center p-1 rounded-xl bg-surface-subtle border border-theme w-full sm:w-auto">
          {languages.map((lang) => {
            const isSelected = activeLang === lang.code;
            return (
              <button
                key={lang.code}
                onClick={() => setActiveLang(lang.code)}
                className={`flex-1 sm:flex-none px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                  isSelected
                    ? 'bg-teal-600 text-white font-semibold shadow-xs'
                    : 'text-theme-secondary hover:text-theme-primary'
                }`}
              >
                <span>{lang.label}</span>
                <span className="text-[10px] opacity-80 hidden md:inline">({lang.sub})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Summary Card with Audio Simulation */}
      <div className="p-4 rounded-xl bg-teal-50/70 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs text-teal-800 dark:text-teal-300 font-semibold">
            <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>PATIENT SUMMARY</span>
          </div>

          {/* Audio Explanation Simulator */}
          <button
            onClick={() => setIsPlayingAudio(!isPlayingAudio)}
            className={`px-3 py-1 rounded-lg text-xs transition-all flex items-center gap-1.5 cursor-pointer border ${
              isPlayingAudio
                ? 'bg-teal-700 text-white border-teal-800 animate-pulse'
                : 'bg-surface text-theme-secondary hover:text-theme-primary border-theme'
            }`}
          >
            {isPlayingAudio ? (
              <>
                <VolumeX className="w-3.5 h-3.5" />
                <span>Pause Audio</span>
              </>
            ) : (
              <>
                <Volume2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                <span>Listen Audio</span>
              </>
            )}
          </button>
        </div>

        <p className="text-sm text-theme-primary leading-relaxed font-medium">
          {currentContent.instructions}
        </p>

        {isPlayingAudio && (
          <div className="p-2.5 rounded-lg bg-surface border border-theme flex items-center gap-3 text-xs text-teal-700 dark:text-teal-300 animate-in fade-in">
            <div className="flex items-end gap-0.5 h-3.5">
              <span className="w-1 bg-teal-500 h-2 animate-bounce" />
              <span className="w-1 bg-teal-500 h-3.5 animate-bounce delay-75" />
              <span className="w-1 bg-teal-500 h-2.5 animate-bounce delay-150" />
              <span className="w-1 bg-teal-500 h-1 animate-bounce" />
            </div>
            <span>Playing {activeLang.toUpperCase()} Vernacular Audio Explanation...</span>
          </div>
        )}
      </div>

      {/* 4-Period Dosing Timeline Schedule */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-theme-secondary">
          Daily Posology Schedule:
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {currentContent.timing.map((item, idx) => {
            const SlotIcon = getSlotIcon(item.icon);
            const isSkip = item.dose.includes('0') || item.dose.includes('छोड़ें') || item.dose.includes('नाही');

            return (
              <div
                key={idx}
                className={`p-3 rounded-xl border transition-all ${
                  isSkip
                    ? 'bg-surface-subtle/50 border-theme opacity-60'
                    : 'bg-surface border-theme shadow-xs'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-theme-primary">{item.slot}</span>
                  <SlotIcon className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                </div>
                <div
                  className={`text-sm font-bold font-mono ${
                    isSkip ? 'text-theme-muted' : 'text-teal-700 dark:text-teal-400'
                  }`}
                >
                  {item.dose}
                </div>
                <div className="text-[11px] text-theme-secondary mt-1">{item.foodNote}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Precautions List */}
      {currentContent.precautions && currentContent.precautions.length > 0 && (
        <div className="p-3.5 rounded-xl bg-surface-subtle border border-theme space-y-2">
          <span className="text-xs font-semibold text-theme-primary uppercase tracking-wider block">
            Important Precautions:
          </span>
          <ul className="space-y-1.5 text-xs text-theme-secondary list-disc list-inside">
            {currentContent.precautions.map((prec, idx) => (
              <li key={idx} className="leading-relaxed">
                {prec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
