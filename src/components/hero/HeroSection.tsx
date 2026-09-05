import React, { useState } from 'react';
import { HeroPrescriptionCanvas, HeroTransformationStage } from './HeroPrescriptionCanvas';
import { Button } from '../ui/Button';
import {
  Sparkles,
  Languages,
  BookOpen,
  ArrowDown,
  Activity,
  CheckCircle2,
  UploadCloud,
  FileSpreadsheet,
} from 'lucide-react';

export interface HeroSectionProps {
  onScrollToAnalyzer: () => void;
  onScrollToMethodology: () => void;
  onOpenUpload?: () => void;
  onOpenResults?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onScrollToAnalyzer,
  onScrollToMethodology,
  onOpenUpload,
  onOpenResults,
}) => {
  const [currentStage, setCurrentStage] = useState<HeroTransformationStage>(0);

  return (
    <section className="relative pt-24 pb-16 sm:pt-32 sm:pb-24 overflow-hidden bg-coordinate-grid border-b border-white/[0.06]">

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Academic Capstone Meta */}
        <div className="flex flex-col items-center text-center space-y-4 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-mono backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-semibold">Academic Capstone Research</span>
            <span className="text-cyan-600">|</span>
            <span>Multimodal Vision-Language Architecture</span>
          </div>

          {/* Main Research Headline */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.12]">
            Turn difficult handwriting into{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400">
              verified medical understanding.
            </span>
          </h1>

          {/* Subtitle / Objective */}
          <p className="text-sm sm:text-base lg:text-lg text-slate-300 max-w-2xl leading-relaxed font-normal">
            Explainable multimodal AI that decodes complex handwritten prescription scripts, grounds medicine candidates against trusted pharmacopeias, abstains when ink is ambiguous, and delivers clear patient posology in English, Hindi, and Marathi.
          </p>

          {/* Primary Action Buttons */}
          <div className="pt-2 flex flex-wrap items-center justify-center gap-3 sm:gap-4">
            {onOpenUpload && (
              <Button
                variant="primary"
                size="lg"
                onClick={onOpenUpload}
                rightIcon={<UploadCloud className="w-4 h-4 text-slate-950" />}
              >
                Upload & Focus Script
              </Button>
            )}
            {onOpenResults && (
              <Button
                variant="secondary"
                size="lg"
                onClick={onOpenResults}
                leftIcon={<FileSpreadsheet className="w-4 h-4 text-cyan-400" />}
              >
                Diagnostic Findings
              </Button>
            )}
            <Button
              variant="outline"
              size="lg"
              onClick={onScrollToAnalyzer}
              rightIcon={<Sparkles className="w-4 h-4 text-slate-300" />}
            >
              Simulated Analyzer
            </Button>
            <Button
              variant="ghost"
              size="lg"
              onClick={onScrollToMethodology}
              leftIcon={<BookOpen className="w-4 h-4 text-slate-400" />}
            >
              Methodology
            </Button>
          </div>

          {/* Credibility / Protocol Bullets */}
          <div className="pt-4 flex flex-wrap items-center justify-center gap-4 sm:gap-8 text-xs font-mono text-slate-400">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Evidence-Grounded (CDSCO/RxNorm)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-amber-400" />
              <span>Calibrated Selective Abstention</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Languages className="w-3.5 h-3.5 text-cyan-400" />
              <span>English · हिन्दी · मराठी</span>
            </div>
          </div>
        </div>

        {/* Centerpiece Interactive Prescription Canvas */}
        <div className="mt-12 sm:mt-16">
          <div className="text-center mb-4">
            <span className="text-xs font-mono uppercase tracking-widest text-slate-400">
              Interactive Architectural Transformation Narrative
            </span>
          </div>
          <HeroPrescriptionCanvas
            currentStage={currentStage}
            onSelectStage={setCurrentStage}
          />
        </div>

        {/* Subtle Scroll Cue */}
        <div className="mt-12 flex justify-center">
          <a
            href="#pipeline"
            className="flex items-center gap-2 text-xs font-mono text-slate-500 hover:text-slate-300 transition-colors py-2"
          >
            <span>DISCOVER THE 5-STAGE GROUNDED PIPELINE</span>
            <ArrowDown className="w-3.5 h-3.5 animate-bounce" />
          </a>
        </div>
      </div>
    </section>
  );
};
