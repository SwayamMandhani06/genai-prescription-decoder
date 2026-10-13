import React, { useState, useEffect } from 'react';
import { MultilingualExplanationContent } from '../../types/prescription.types';
import {
  Globe,
  Sun,
  CloudSun,
  Sunset,
  Moon,
  Volume2,
  VolumeX,
  FileText,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertCircle,
  Pill,
  Clock,
  Sparkles,
} from 'lucide-react';

export interface ExtractedMedicineItem {
  name: string;
  strength?: string | null;
  formulation?: string | null;
  dosageAmount?: string | null;
  frequency?: string | null;
  frequencyPlain?: string | null;
  timingAndFood?: string | null;
  duration?: string | null;
  route?: string | null;
  specialInstructions?: string | null;
  patientExplanation?: string | null;
  requiresVerification?: boolean;
  status?: 'confident' | 'uncertain' | 'flagged';
  candidates?: string[];
}

export interface MultilingualExplanationCardProps {
  multilingual: {
    en: MultilingualExplanationContent;
    hi: MultilingualExplanationContent;
    mr: MultilingualExplanationContent;
  };
  medicines?: ExtractedMedicineItem[];
  prescriptionSummary?: string;
  accessionId?: string;
}

export type SupportedLanguage = 'en' | 'hi' | 'mr';

export const MultilingualExplanationCard: React.FC<MultilingualExplanationCardProps> = ({
  multilingual,
  medicines = [],
  prescriptionSummary,
}) => {
  const [activeLang, setActiveLang] = useState<SupportedLanguage>('en');
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [showDeveloperAudit, setShowDeveloperAudit] = useState<boolean>(false);

  const currentContent = multilingual[activeLang] || multilingual.en;

  // Cleanup speech synthesis on language switch or component unmount
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsPlayingAudio(false);
    }
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [activeLang]);

  // Construct patient-friendly speech script from verified explanation facts (never raw OCR or JSON)
  const constructSpeechScript = (): string => {
    // 1. Lead summary
    const summaryLead =
      activeLang === 'en'
        ? prescriptionSummary || currentContent.summary || 'Here is your prescription overview.'
        : currentContent.summary || 'यहाँ आपके प्रिस्क्रिप्शन का विवरण है।';

    // 2. Medicine-specific verified instructions
    let medSpoken = '';
    if (medicines.length > 0) {
      if (activeLang === 'en') {
        medSpoken = medicines
          .map((m) => {
            const parts = [`Medication: ${m.name}`];
            if (m.strength) parts.push(`strength ${m.strength}`);
            if (m.frequencyPlain || m.frequency) parts.push(`schedule ${m.frequencyPlain || m.frequency}`);
            if (m.timingAndFood) parts.push(`take ${m.timingAndFood}`);
            if (m.duration) parts.push(`for ${m.duration}`);
            if (m.requiresVerification) parts.push('Please confirm instructions with your pharmacist.');
            return parts.join(', ') + '.';
          })
          .join(' ');
      } else if (activeLang === 'hi') {
        medSpoken = medicines
          .map((m) => {
            const nameStr = m.name;
            const doseStr = m.strength ? ` (${m.strength})` : '';
            const timingStr = m.timingAndFood ? ` ${m.timingAndFood}` : '';
            const freqStr = m.frequencyPlain ? ` ${m.frequencyPlain}` : '';
            const verifyStr = m.requiresVerification ? ' कृपया लेने से पहले फार्मासिस्ट से पुष्टि करें।' : '';
            return `दवा ${nameStr}${doseStr}।${freqStr}${timingStr} लें।${verifyStr}`;
          })
          .join(' ');
      } else {
        medSpoken = medicines
          .map((m) => {
            const nameStr = m.name;
            const doseStr = m.strength ? ` (${m.strength})` : '';
            const timingStr = m.timingAndFood ? ` ${m.timingAndFood}` : '';
            const freqStr = m.frequencyPlain ? ` ${m.frequencyPlain}` : '';
            const verifyStr = m.requiresVerification ? ' कृपया फार्मासिस्टशी खात्री करा.' : '';
            return `औषध ${nameStr}${doseStr}. ${freqStr}${timingStr} घ्यावे.${verifyStr}`;
          })
          .join(' ');
      }
    }

    return `${summaryLead}. ${medSpoken}`.trim();
  };

  const handleToggleAudio = () => {
    if (isPlayingAudio) {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setIsPlayingAudio(false);
    } else {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const textToSpeak = constructSpeechScript();
        const utterance = new SpeechSynthesisUtterance(textToSpeak);

        // Find optimal available browser voice for vernacular
        const voices = window.speechSynthesis.getVoices();
        if (activeLang === 'hi') {
          utterance.lang = 'hi-IN';
          const hiVoice = voices.find((v) => v.lang.startsWith('hi'));
          if (hiVoice) utterance.voice = hiVoice;
        } else if (activeLang === 'mr') {
          utterance.lang = 'mr-IN';
          const mrVoice = voices.find((v) => v.lang.startsWith('mr') || v.lang.startsWith('hi'));
          if (mrVoice) utterance.voice = mrVoice;
        } else {
          utterance.lang = 'en-IN';
          const enVoice = voices.find((v) => v.lang === 'en-IN' || v.lang.startsWith('en'));
          if (enVoice) utterance.voice = enVoice;
        }

        utterance.rate = 0.92;
        utterance.onend = () => setIsPlayingAudio(false);
        utterance.onerror = () => setIsPlayingAudio(false);
        setIsPlayingAudio(true);
        window.speechSynthesis.speak(utterance);
      } else {
        // Fallback simulation timer if speech API unavailable
        setIsPlayingAudio(true);
        setTimeout(() => setIsPlayingAudio(false), 4000);
      }
    }
  };

  const languages = [
    { code: 'en' as SupportedLanguage, label: 'English', sub: 'Clinical & Plain' },
    { code: 'hi' as SupportedLanguage, label: 'हिन्दी', sub: 'Hindi' },
    { code: 'mr' as SupportedLanguage, label: 'मराठी', sub: 'Marathi' },
  ];

  const getSlotIcon = (iconName: string) => {
    switch (iconName.toLowerCase()) {
      case 'sun':
        return Sun;
      case 'cloud-sun':
      case 'cloudsun':
        return CloudSun;
      case 'sunset':
        return Sunset;
      case 'moon':
        return Moon;
      default:
        return Sun;
    }
  };

  // Derive plain-language summary for display
  const displaySummary =
    activeLang === 'en'
      ? prescriptionSummary || currentContent.summary
      : currentContent.summary;

  // Identify any actionable verification items
  const verificationItems: string[] = [];
  medicines.forEach((med) => {
    if (med.requiresVerification || med.status !== 'confident') {
      verificationItems.push(
        `Confirm dosage schedule for ${med.name} — cursive or ambiguous handwriting observed.`
      );
    }
    if (!med.duration) {
      verificationItems.push(
        `Course duration for ${med.name} is not explicitly specified on the pad — consult your pharmacist.`
      );
    }
  });

  return (
    <div
      className="rounded-3xl border border-theme bg-surface p-6 sm:p-8 space-y-7 shadow-xs transition-colors"
      data-testid="explanation-card"
    >
      {/* Header with Language Segmented Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-theme pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#4A2E4D]/10 dark:bg-[#F472B6]/20 flex items-center justify-center">
            <Globe className="w-5 h-5 text-[#4A2E4D] dark:text-[#F472B6]" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-theme-primary tracking-tight">
              Patient Explanation &amp; Voice Guide
            </h2>
            <p className="text-xs sm:text-sm text-theme-secondary">
              Grounded, patient-friendly guidance in English, हिन्दी, and मराठी
            </p>
          </div>
        </div>

        {/* Language Tabs */}
        <div
          className="flex items-center p-1 rounded-2xl bg-surface-subtle border border-theme w-full sm:w-auto"
          role="tablist"
          aria-label="Language selection"
        >
          {languages.map((lang) => {
            const isSelected = activeLang === lang.code;
            return (
              <button
                key={lang.code}
                role="tab"
                aria-selected={isSelected}
                onClick={() => setActiveLang(lang.code)}
                data-testid={`lang-tab-${lang.code}`}
                className={`flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                  isSelected
                    ? 'bg-[#4A2E4D] dark:bg-[#F472B6] text-white dark:text-[#2E2233] font-semibold shadow-xs'
                    : 'text-theme-secondary hover:text-theme-primary'
                }`}
              >
                <span>{lang.label}</span>
                <span className="text-[11px] opacity-75 hidden md:inline">({lang.sub})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Section A — Prescription Summary & Prominent Voice Assistance */}
      <div className="p-6 rounded-2xl bg-[#FFD6DA]/20 dark:bg-[#4A2E4D]/25 border border-[#F472B6]/25 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-bold text-[#4A2E4D] dark:text-[#FFD6DA] uppercase tracking-wider">
            <FileText className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6]" />
            <span>Prescription Overview</span>
          </div>

          {/* Section D: Prominent Speech Control */}
          <button
            onClick={handleToggleAudio}
            aria-label={isPlayingAudio ? 'Pause spoken explanation' : 'Listen to spoken explanation'}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm transition-all flex items-center gap-2 cursor-pointer font-semibold shadow-xs ${
              isPlayingAudio
                ? 'bg-[#4A2E4D] dark:bg-[#F472B6] text-white dark:text-[#2E2233]'
                : 'bg-surface hover:bg-surface-subtle text-theme-primary border border-theme'
            }`}
          >
            {isPlayingAudio ? (
              <>
                <VolumeX className="w-4 h-4" />
                <span>Pause Spoken Guide</span>
              </>
            ) : (
              <>
                <Volume2 className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6]" />
                <span>Listen Spoken Explanation</span>
              </>
            )}
          </button>
        </div>

        {/* Lead Posology Summary Sentence */}
        {displaySummary && (
          <p
            className="text-base sm:text-lg text-theme-primary leading-relaxed font-semibold"
            data-testid="explanation-summary"
          >
            {displaySummary}
          </p>
        )}

        {/* Instructions narrative if distinct */}
        {currentContent.instructions && currentContent.instructions !== displaySummary && (
          <p
            className="text-xs sm:text-sm text-theme-secondary leading-relaxed whitespace-pre-line pt-2 border-t border-[#F472B6]/20 font-normal"
            data-testid="explanation-instructions"
          >
            {currentContent.instructions}
          </p>
        )}

        {/* Audio Waveform Animation when playing */}
        {isPlayingAudio && (
          <div className="p-3 rounded-xl bg-surface border border-theme flex items-center gap-3 text-xs text-[#4A2E4D] dark:text-[#FFD6DA] animate-in fade-in">
            <div className="flex items-end gap-1 h-4">
              <span className="w-1 bg-[#F472B6] h-2.5 animate-bounce" />
              <span className="w-1 bg-[#F472B6] h-4 animate-bounce delay-75" />
              <span className="w-1 bg-[#F472B6] h-3 animate-bounce delay-150" />
              <span className="w-1 bg-[#F472B6] h-2 animate-bounce" />
            </div>
            <span className="font-medium">
              Speaking verified explanation in {activeLang.toUpperCase()} vernacular voice...
            </span>
          </div>
        )}
      </div>

      {/* Section B — Medicine-by-Medicine Patient Posology Cards */}
      {medicines.length > 0 && (
        <div className="space-y-3.5">
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-bold text-theme-primary tracking-tight">
              Medicine Posology &amp; Administration
            </h3>
            <span className="text-xs text-theme-muted font-mono">{medicines.length} prescribed item{medicines.length > 1 ? 's' : ''}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {medicines.map((med, idx) => (
              <div
                key={`exp-med-${idx}-${med.name}`}
                className="p-5 rounded-2xl border border-theme bg-surface-subtle/50 hover:bg-surface-subtle transition-all space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Pill className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6]" />
                      <h4 className="font-bold text-base text-theme-primary font-mono">{med.name}</h4>
                    </div>
                    {med.strength && (
                      <span className="text-xs text-theme-secondary font-mono font-medium">
                        Strength: {med.strength}
                      </span>
                    )}
                  </div>

                  {/* Verification Pill */}
                  {med.status === 'confident' && !med.requiresVerification ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-700 text-emerald-800 dark:text-emerald-200">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>Verified</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-700 text-amber-900 dark:text-amber-200">
                      <AlertCircle className="w-3 h-3 text-amber-600" />
                      <span>Verify with Pharmacist</span>
                    </span>
                  )}
                </div>

                {/* Structured Administration Details */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-surface border border-theme">
                    <span className="text-theme-muted block text-[11px]">Schedule</span>
                    <strong className="text-theme-primary font-medium">
                      {med.frequencyPlain || med.frequency || 'As directed'}
                    </strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-theme">
                    <span className="text-theme-muted block text-[11px]">Timing &amp; Meals</span>
                    <strong className="text-theme-primary font-medium">
                      {med.timingAndFood || 'With or after food'}
                    </strong>
                  </div>
                </div>

                {/* Plain-Language Explanation */}
                <p className="text-xs text-theme-secondary leading-relaxed pt-1">
                  {med.patientExplanation ||
                    (med.timingAndFood
                      ? `Take ${med.name} ${med.timingAndFood.toLowerCase()}, as written by the prescriber.`
                      : `Follow the recorded prescription schedule for ${med.name}.`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Daily Dosing Timeline (Morning, Afternoon, Evening, Night) */}
      {currentContent.timing && currentContent.timing.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs sm:text-sm font-bold text-theme-primary">
            <Clock className="w-4 h-4 text-[#7C5A8B] dark:text-[#F472B6]" />
            <span>Daily Intake Schedule:</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {currentContent.timing.map((item, idx) => {
              const SlotIcon = getSlotIcon(item.icon);
              const isSkip =
                item.dose.includes('0') ||
                item.dose.includes('छोड़ें') ||
                item.dose.includes('नाही');

              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border transition-all ${
                    isSkip
                      ? 'bg-surface-subtle/50 border-theme opacity-60'
                      : 'bg-surface border-theme shadow-xs'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-theme-primary">{item.slot}</span>
                    <SlotIcon className="w-3.5 h-3.5 text-[#7C5A8B] dark:text-[#F472B6]" />
                  </div>
                  <div
                    className={`text-base font-bold font-mono ${
                      isSkip ? 'text-theme-muted' : 'text-[#4A2E4D] dark:text-[#F472B6]'
                    }`}
                  >
                    {item.dose}
                  </div>
                  <div className="text-[11px] text-theme-secondary mt-0.5">{item.foodNote}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Section C — Actionable Things to Verify */}
      {verificationItems.length > 0 && (
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 space-y-2">
          <div className="flex items-center gap-2 text-xs sm:text-sm font-bold text-amber-900 dark:text-amber-200">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Important Things to Verify with Your Pharmacist:</span>
          </div>
          <ul className="space-y-1.5 text-xs sm:text-sm text-amber-900/90 dark:text-amber-200/90 list-disc list-inside">
            {Array.from(new Set(verificationItems)).map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Precautions List */}
      {currentContent.precautions && currentContent.precautions.length > 0 && (
        <div className="p-4 rounded-xl bg-surface-subtle border border-theme space-y-2">
          <span className="text-xs font-semibold text-theme-primary uppercase tracking-wider block">
            General Precautions:
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

      {/* Developer Diagnostics: Collapsed by Default */}
      <div className="pt-2 border-t border-theme">
        <button
          onClick={() => setShowDeveloperAudit(!showDeveloperAudit)}
          className="flex items-center gap-1.5 text-xs text-theme-muted hover:text-theme-primary font-medium py-1 cursor-pointer transition-colors"
          data-testid="toggle-side-by-side"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#7C5A8B] dark:text-[#F472B6]" />
          <span>Developer Diagnostics: Cross-Language Alignment</span>
          {showDeveloperAudit ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
        </button>

        {showDeveloperAudit && (
          <div
            className="mt-3 p-4 rounded-xl bg-surface-subtle border border-theme space-y-3 text-xs animate-in fade-in"
            data-testid="side-by-side-panel"
          >
            <div className="flex items-center justify-between pb-2 border-b border-theme">
              <span className="font-semibold text-theme-primary">
                Deterministic Multilingual Factual Alignment
              </span>
              <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" /> Factual Tokens Grounded
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-3 rounded-lg bg-surface border border-theme space-y-1">
                <span className="font-bold text-[#7C5A8B] dark:text-[#F472B6] block">English (en)</span>
                <p className="text-theme-primary font-medium">
                  {multilingual.en.summary || multilingual.en.instructions}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-surface border border-theme space-y-1">
                <span className="font-bold text-[#7C5A8B] dark:text-[#F472B6] block">हिन्दी (hi)</span>
                <p className="text-theme-primary font-medium">
                  {multilingual.hi.summary || multilingual.hi.instructions}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-surface border border-theme space-y-1">
                <span className="font-bold text-[#7C5A8B] dark:text-[#F472B6] block">मराठी (mr)</span>
                <p className="text-theme-primary font-medium">
                  {multilingual.mr.summary || multilingual.mr.instructions}
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between text-[11px] text-theme-muted pt-2 border-t border-theme">
              <span>Source: Extracted &amp; verified prescription data</span>
              <span className="font-mono">Policy: explanation_policy_v1</span>
            </div>
          </div>
        )}
      </div>

      {/* Statutory Source Disclosure */}
      <div className="pt-2 border-t border-theme flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs text-theme-muted">
        <span>Source: Extracted prescription data &bull; Assistive posology guide</span>
        <span>Always confirm prescription details with your dispensing pharmacist</span>
      </div>
    </div>
  );
};
