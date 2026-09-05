import React, { useState } from 'react';
import { CLINICAL_LASA_CATALOG } from '../../data/lasaCatalog';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { ShieldCheck, AlertOctagon, Eye } from 'lucide-react';

export const LasaSafetySection: React.FC = () => {
  const [selectedLasaId, setSelectedLasaId] = useState<string>(CLINICAL_LASA_CATALOG[0].id);
  const [useTallManLettering, setUseTallManLettering] = useState<boolean>(true);

  const activePair =
    CLINICAL_LASA_CATALOG.find((p) => p.id === selectedLasaId) || CLINICAL_LASA_CATALOG[0];

  // Algorithmic phonetic keys mapping for research transparency
  const phoneticKeys: Record<string, { primary: string; secondary: string; diffChars: string }> = {
    'lasa-1': { primary: 'MTFRMN', secondary: 'MTRNDZL', diffChars: 'F/R vs R/N/D/Z' },
    'lasa-2': { primary: 'SLBRKS', secondary: 'SLKS', diffChars: 'BR/K vs K' },
    'lasa-3': { primary: 'PRDNSN', secondary: 'PRDNSLN', diffChars: 'SN vs SLN' },
    'lasa-4': { primary: 'SNTK', secondary: 'SRTK', diffChars: 'N vs R' },
    'lasa-5': { primary: 'LMKTL', secondary: 'LMSL', diffChars: 'KT vs S' },
  };

  const activePhonetic = phoneticKeys[activePair.id] || {
    primary: 'UNKNOWN',
    secondary: 'UNKNOWN',
    diffChars: 'Multiple substitutions',
  };

  return (
    <section id="lasa-safety" className="py-20 bg-[#07090E] border-b border-white/[0.06] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
          <Badge variant="coral" size="sm" dot>
            Orthographic & Phonetic Risk Engine
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight font-sans">
            LASA (Look-Alike Sound-Alike) Collision Defense
          </h2>
          <p className="text-sm sm:text-base text-slate-300 font-sans">
            Handwritten cursive silhouettes frequently merge characters into ambiguous ligatures. AURA-Rx computes dual string distances—Levenshtein orthographic and Double Metaphone acoustic—to preempt fatal dispensing errors.
          </p>
        </div>

        {/* Top Controls: TALL MAN Lettering Toggle */}
        <div className="flex items-center justify-between p-3.5 rounded-lg bg-[#0E131F] border border-white/[0.08] mb-6">
          <div className="flex items-center gap-2.5">
            <Eye className="w-4 h-4 text-cyan-400" />
            <span className="text-xs sm:text-sm font-bold text-white font-sans">
              FDA / ISMP TALL MAN Lettering Standard:
            </span>
          </div>
          <button
            onClick={() => setUseTallManLettering(!useTallManLettering)}
            className={`px-3 py-1 text-xs font-mono rounded border transition-all cursor-pointer ${
              useTallManLettering
                ? 'bg-cyan-950 text-cyan-300 border-cyan-500/40 shadow-sm'
                : 'bg-slate-800 text-slate-400 border-white/5'
            }`}
          >
            {useTallManLettering ? 'TALL MAN: ENABLED (Recommended)' : 'Standard Lowercase'}
          </button>
        </div>

        {/* Grid: LASA Pairs Selector & Live Clinical Risk Drawer */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left: Interactive Pair Selector */}
          <div className="lg:col-span-5 space-y-2.5">
            <div className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 px-1 mb-1">
              High-Incidence Clinical Ambiguity Catalog:
            </div>

            {CLINICAL_LASA_CATALOG.map((pair) => {
              const isSelected = pair.id === selectedLasaId;

              return (
                <button
                  key={pair.id}
                  onClick={() => setSelectedLasaId(pair.id)}
                  className={`w-full p-3.5 rounded-lg text-left border transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'bg-[#18111B] border-red-500/60 shadow-lg'
                      : 'bg-[#0B0E17] border-white/[0.06] hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-xs font-mono font-bold text-slate-200">
                      {useTallManLettering
                        ? pair.differentiationKey.replace('TALL MAN Lettering: ', '')
                        : `${pair.prescribedDrug} vs ${pair.confusableWith}`}
                    </span>
                    <Badge variant={pair.riskTier === 'CRITICAL' ? 'coral' : 'amber'} size="xs">
                      {pair.riskTier}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-4 text-[11px] font-mono text-slate-400">
                    <span>Levenshtein: {Math.round(pair.orthographicSimilarity * 100)}%</span>
                    <span>Phonetic: {Math.round(pair.phoneticSimilarity * 100)}%</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: Detailed Risk Inspection Card */}
          <div className="lg:col-span-7">
            <Card variant="coral" padding="lg" className="border-red-500/30 bg-[#0F111A] rounded-lg">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3.5 border-b border-white/[0.08] mb-5">
                <div className="flex items-center gap-2">
                  <AlertOctagon className="w-5 h-5 text-red-400" />
                  <span className="text-sm font-mono font-bold text-white">
                    LASA HAZARD EVALUATION REPORT · {activePair.id.toUpperCase()}
                  </span>
                </div>
                <Badge variant="coral" size="sm" dot>
                  {activePair.riskTier} RISK CLASSIFICATION
                </Badge>
              </div>

              {/* Side by side comparison pills */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5 font-sans">
                <div className="p-3 rounded bg-slate-950 border border-white/10 space-y-1">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block">
                    Prescribed Drug Candidate
                  </span>
                  <div className="text-base font-bold text-white">
                    {activePair.prescribedDrug} {activePair.prescribedDose}
                  </div>
                  <div className="text-[10px] font-mono text-slate-400">
                    Double Metaphone: [{activePhonetic.primary}]
                  </div>
                </div>

                <div className="p-3 rounded bg-slate-950 border border-red-500/30 space-y-1">
                  <span className="text-[10px] font-mono text-red-400 uppercase tracking-wider block">
                    High-Risk Confusable Counterpart
                  </span>
                  <div className="text-base font-bold text-red-300">
                    {activePair.confusableWith} {activePair.confusableDose}
                  </div>
                  <div className="text-[10px] font-mono text-slate-400">
                    Double Metaphone: [{activePhonetic.secondary}]
                  </div>
                </div>
              </div>

              {/* Algorithmic Metrics Bar */}
              <div className="grid grid-cols-2 gap-3 mb-5 font-mono text-xs">
                <div className="p-3 rounded bg-black/40 border border-white/5 space-y-1">
                  <div className="text-slate-400 text-[11px]">Levenshtein String Overlap:</div>
                  <div className="text-base font-bold text-cyan-300">
                    {Math.round(activePair.orthographicSimilarity * 100)}%
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Cursive silhouette alignment
                  </div>
                </div>

                <div className="p-3 rounded bg-black/40 border border-white/5 space-y-1">
                  <div className="text-slate-400 text-[11px]">Acoustic Phonetic Distance:</div>
                  <div className="text-base font-bold text-teal-300">
                    {Math.round(activePair.phoneticSimilarity * 100)}%
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Verbal dispensing error probability
                  </div>
                </div>
              </div>

              {/* Pharmacological Breakdown */}
              <div className="space-y-3 text-xs sm:text-sm font-sans">
                <div>
                  <span className="text-slate-400 font-mono text-xs uppercase tracking-wider block mb-1">
                    Pharmacological Contrast:
                  </span>
                  <p className="text-slate-200 leading-relaxed font-sans">
                    {activePair.pharmacologicalDifference}
                  </p>
                </div>

                <div className="p-3 rounded bg-red-950/40 border border-red-500/30 text-red-200 leading-relaxed text-xs">
                  <strong className="text-red-400 block mb-1 font-mono uppercase">
                    Fatal Clinical Consequence if Misdispensed:
                  </strong>
                  {activePair.clinicalDangerNotice}
                </div>

                <div className="p-2.5 rounded bg-cyan-950/30 border border-cyan-500/30 text-cyan-200 text-xs font-mono flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>{activePair.differentiationKey}</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};
