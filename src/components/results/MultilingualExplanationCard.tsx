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
    { code: 'en' as SupportedLanguage, label: 'English', sub: 'Clinical Standard' },
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
    <div className="rounded-xl border border-white/10 bg-[#0A0E1A] p-5 sm:p-6 space-y-5">
      {/* Header with Language Segmented Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="text-sm font-bold text-white font-mono tracking-tight uppercase">
              Patient Vernacular Posology &amp; Instructions
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Plain-Language Explanation with Preserved Medicine Names &amp; Dosages
            </p>
          </div>
        </div>

        {/* Language Switcher Buttons */}
        <div className="flex items-center p-1 rounded-lg bg-black/50 border border-white/10 w-full sm:w-auto">
          {languages.map((lang) => {
            const isSelected = activeLang === lang.code;
            return (
              <button
                key={lang.code}
                onClick={() => setActiveLang(lang.code)}
                className={`flex-1 sm:flex-none px-3.5 py-1.5 rounded text-xs font-mono transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                  isSelected
                    ? 'bg-cyan-950 text-cyan-300 font-bold border border-cyan-500/50 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <span>{lang.label}</span>
                <span className="text-[10px] text-slate-500 hidden md:inline">({lang.sub})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Vernacular Summary Card with Audio Simulation */}
      <div className="p-4 rounded-lg bg-cyan-950/20 border border-cyan-500/20 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-300">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="font-bold uppercase tracking-wider">PATIENT-FRIENDLY SUMMARY</span>
          </div>

          {/* Audio Explanation Simulator */}
          <button
            onClick={() => setIsPlayingAudio(!isPlayingAudio)}
            className={`px-3 py-1 rounded text-xs font-mono transition-all flex items-center gap-1.5 cursor-pointer border ${
              isPlayingAudio
                ? 'bg-cyan-900 text-cyan-200 border-cyan-400 animate-pulse'
                : 'bg-black/40 text-slate-300 hover:text-white border-white/10'
            }`}
          >
            {isPlayingAudio ? (
              <>
                <VolumeX className="w-3.5 h-3.5 text-cyan-300" />
                <span>Pause Audio</span>
              </>
            ) : (
              <>
                <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>Listen Vernacular Audio</span>
              </>
            )}
          </button>
        </div>

        <p className="text-sm text-slate-100 font-sans leading-relaxed">
          {currentContent.instructions}
        </p>

        {isPlayingAudio && (
          <div className="p-2.5 rounded bg-black/40 border border-cyan-500/30 flex items-center gap-3 text-xs font-mono text-cyan-300 animate-in fade-in">
            <div className="flex items-end gap-0.5 h-4">
              <span className="w-1 bg-cyan-400 h-2 animate-bounce" />
              <span className="w-1 bg-cyan-400 h-4 animate-bounce delay-75" />
              <span className="w-1 bg-cyan-400 h-3 animate-bounce delay-150" />
              <span className="w-1 bg-cyan-400 h-1 animate-bounce" />
            </div>
            <span>Playing {activeLang.toUpperCase()} Vernacular Posology Audio Synthesis...</span>
          </div>
        )}
      </div>

      {/* 4-Period Dosing Timeline Schedule */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400">
          <span className="uppercase tracking-wider">Daily Schedule &amp; Meal Association</span>
          <span className="text-[10px] text-slate-500">PRESERVED POSOLOGY TIMELINE</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {currentContent.timing.map((item, idx) => {
            const SlotIcon = getSlotIcon(item.icon);
            const isSkip = item.dose.includes('0') || item.dose.includes('छोड़ें') || item.dose.includes('नाही');

            return (
              <div
                key={idx}
                className={`p-3 rounded-lg border transition-all ${
                  isSkip
                    ? 'bg-black/20 border-white/5 opacity-50'
                    : 'bg-[#0E1422] border-cyan-500/30 shadow-md'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-300 font-sans">{item.slot}</span>
                  <SlotIcon className="w-4 h-4 text-cyan-400" />
                </div>
                <div
                  className={`text-sm font-mono font-bold ${
                    isSkip ? 'text-slate-500' : 'text-cyan-300'
                  }`}
                >
                  {item.dose}
                </div>
                <div className="text-[11px] text-slate-400 font-sans mt-1">{item.foodNote}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Precautions List */}
      {currentContent.precautions && currentContent.precautions.length > 0 && (
        <div className="p-3.5 rounded-lg bg-black/30 border border-white/5 space-y-2">
          <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider block">
            Important Clinical Precautions:
          </span>
          <ul className="space-y-1.5 text-xs text-slate-300 font-sans list-disc list-inside">
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
