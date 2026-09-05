import React from 'react';
import { Navbar } from '../components/layout/Navbar';
import { HeroSection } from '../components/hero/HeroSection';
import { PipelineSection } from '../components/pipeline/PipelineSection';
import { InteractiveAnalyzer } from '../components/prescription/InteractiveAnalyzer';
import { UncertaintyAbstentionSection } from '../components/safety/UncertaintyAbstentionSection';
import { LasaSafetySection } from '../components/safety/LasaSafetySection';
import { MultilingualExplanationSection } from '../components/explanation/MultilingualExplanationSection';
import { OriginalPrescriptionReference } from '../components/prescription/OriginalPrescriptionReference';
import { ResearchBenchmarkSection } from '../components/research/ResearchBenchmarkSection';
import { SafetyDisclaimer } from '../components/layout/SafetyDisclaimer';
import { Footer } from '../components/layout/Footer';

export interface HomePageProps {
  onOpenUpload?: () => void;
  onOpenResults?: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onOpenUpload, onOpenResults }) => {
  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#060911] text-slate-100 flex flex-col selection:bg-cyan-500/25 selection:text-cyan-200">
      {/* Top Navbar */}
      <Navbar
        onLaunchDemoClick={() => scrollToSection('analyzer')}
        onOpenUploadClick={onOpenUpload}
        onOpenResultsClick={onOpenResults}
        activeView="home"
      />

      {/* Main Content Sections */}
      <main className="flex-1">
        {/* 1. Hero Section & Interactive Transformation Narrative */}
        <HeroSection
          onScrollToAnalyzer={() => scrollToSection('analyzer')}
          onScrollToMethodology={() => scrollToSection('benchmarks')}
          onOpenUpload={onOpenUpload}
          onOpenResults={onOpenResults}
        />

        {/* 2. Pipeline: From Handwriting to Understanding */}
        <PipelineSection />

        {/* 3. Interactive Simulated Prescription Analyzer */}
        <InteractiveAnalyzer />

        {/* 4. Uncertainty & Calibrated Selective Abstention */}
        <UncertaintyAbstentionSection />

        {/* 5. LASA Safety Awareness & TALL MAN Lettering */}
        <LasaSafetySection />

        {/* 6. Multilingual Explanation & Audio Synthesis (EN / HI / MR) */}
        <MultilingualExplanationSection />

        {/* 7. Original Prescription as Ground Truth */}
        <OriginalPrescriptionReference />

        {/* 8. Research Benchmark & Quantitative Methodology */}
        <ResearchBenchmarkSection />

        {/* 9. Statutory Safety Disclaimer */}
        <SafetyDisclaimer />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};
