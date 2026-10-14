import React from 'react';
import { Navbar } from '../components/layout/Navbar';
import { HeroSection } from '../components/hero/HeroSection';
import { InteractivePrescriptionSection } from '../components/home/InteractivePrescriptionSection';
import { CoreCapabilitiesSection } from '../components/home/CoreCapabilitiesSection';
import { HowItWorksSection } from '../components/home/HowItWorksSection';
import { SafetyPhilosophySection } from '../components/home/SafetyPhilosophySection';
import { LanguageSupportSection } from '../components/home/LanguageSupportSection';
import { FaqSection } from '../components/home/FaqSection';
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
    <div className="min-h-screen bg-canvas text-theme-primary flex flex-col font-sans selection:bg-[#155EEF]/20 selection:text-[#102A43] dark:selection:text-[#EAF2FF]">
      {/* Top Navigation */}
      <Navbar
        onNavigateToAnalyze={onOpenUpload}
        onNavigateToHowItWorks={() => scrollToSection('how-it-works')}
        onNavigateToSafety={() => scrollToSection('safety')}
        onNavigateToResearch={onOpenResearch}
        onOpenUploadClick={onOpenUpload}
        onOpenResultsClick={onOpenResults}
        onHomeClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        activeView="home"
      />

      {/* Main Product Journey */}
      <main className="flex-1">
        {/* Section 1: Hero (Centered Spacious Composition, No Dashboard) */}
        <HeroSection
          onOpenUpload={onOpenUpload}
          onScrollToHowItWorks={() => scrollToSection('demo')}
        />

        {/* Section 2: Interactive Prescription Preview ("From handwriting to understanding") */}
        <InteractivePrescriptionSection />

        {/* Section 3: How DawaAI Works (4-Stage Pipeline: Upload, Extract, Review Uncertainty, Understand) */}
        <HowItWorksSection />

        {/* Section 4: Safety & Uncertainty Philosophy */}
        <SafetyPhilosophySection />

        {/* Three Core Capabilities: Understand · Verify · Explain */}
        <CoreCapabilitiesSection />

        {/* Multilingual Posology: English · हिन्दी · मराठी */}
        <LanguageSupportSection />

        {/* Section 5: Short FAQ Section with Accessible Accordions */}
        <FaqSection />

        {/* Compact Research Prototype Statement */}
        <ResearchOverviewSection onOpenResearchPage={onOpenResearch} />

        {/* Final Calm Call to Action */}
        <FinalCtaSection onOpenUpload={onOpenUpload} />
      </main>

      {/* Section 6: Clean, Professional Footer */}
      <Footer
        onNavigateToResearch={onOpenResearch}
        onOpenUpload={onOpenUpload}
      />
    </div>
  );
};
