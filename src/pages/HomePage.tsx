import React from 'react';
import { Navbar } from '../components/layout/Navbar';
import { HeroSection } from '../components/hero/HeroSection';
import { TransformationDemoSection } from '../components/home/TransformationDemoSection';
import { CoreCapabilitiesSection } from '../components/home/CoreCapabilitiesSection';
import { SafetyPhilosophySection } from '../components/home/SafetyPhilosophySection';
import { LanguageSupportSection } from '../components/home/LanguageSupportSection';
import { ResearchOverviewSection } from '../components/home/ResearchOverviewSection';
import { FinalCtaSection } from '../components/home/FinalCtaSection';
import { Footer } from '../components/layout/Footer';

export interface HomePageProps {
  onOpenUpload?: () => void;
  onOpenResults?: () => void;
  onOpenResearch?: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({
  onOpenUpload,
  onOpenResults,
  onOpenResearch,
}) => {
  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-theme-primary flex flex-col font-sans selection:bg-teal-500/20 selection:text-teal-800 dark:selection:text-teal-200">
      {/* Top Navigation */}
      <Navbar
        onNavigateToAnalyze={onOpenUpload}
        onNavigateToHowItWorks={() => scrollToSection('transformation')}
        onNavigateToSafety={() => scrollToSection('safety')}
        onNavigateToResearch={onOpenResearch}
        onOpenUploadClick={onOpenUpload}
        onOpenResultsClick={onOpenResults}
        activeView="home"
      />

      {/* Main Product Journey */}
      <main className="flex-1">
        {/* 1. Hero: Problem, Prescription Object & Visual 4-Phase Transformation */}
        <HeroSection
          onOpenUpload={onOpenUpload}
          onScrollToHowItWorks={() => scrollToSection('transformation')}
        />

        {/* 2. First Scroll: "See what changes." Interactive Before/After */}
        <TransformationDemoSection />

        {/* 3. Three Core Capabilities: Understand · Verify · Explain */}
        <CoreCapabilitiesSection />

        {/* 4. Safety Philosophy: "The system should know when it does not know." */}
        <SafetyPhilosophySection />

        {/* 5. Multilingual Posology: English · हिन्दी · मराठी */}
        <LanguageSupportSection />

        {/* 6. Compact Research Prototype Statement */}
        <ResearchOverviewSection onOpenResearchPage={onOpenResearch} />

        {/* 7. Final Calm CTA */}
        <FinalCtaSection onOpenUpload={onOpenUpload} />
      </main>

      {/* 8. Clean, Professional Footer */}
      <Footer
        onNavigateToResearch={onOpenResearch}
        onOpenUpload={onOpenUpload}
      />
    </div>
  );
};
