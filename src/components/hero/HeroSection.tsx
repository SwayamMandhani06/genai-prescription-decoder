import React from 'react';
import { motion, useReducedMotion, type Variants } from 'framer-motion';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import { SilkGradientWaveCanvas } from './SilkGradientWaveCanvas';

export interface HeroSectionProps {
  onOpenUpload?: () => void;
  onScrollToHowItWorks?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onOpenUpload,
  onScrollToHowItWorks,
}) => {
  const shouldReduceMotion = useReducedMotion();

  const handleScrollToDemo = () => {
    const el = document.getElementById('demo');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    } else if (onScrollToHowItWorks) {
      onScrollToHowItWorks();
    }
  };

  // Coordinated entrance animation variants
  const containerVariants: Variants = {
    hidden: { opacity: shouldReduceMotion ? 1 : 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : 0.12,
        delayChildren: shouldReduceMotion ? 0 : 0.08,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: {
      opacity: shouldReduceMotion ? 1 : 0,
      y: shouldReduceMotion ? 0 : 20,
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: shouldReduceMotion ? 0 : 0.6,
        ease: 'easeOut',
      },
    },
  };

  return (
    <section
      className="relative pt-28 pb-20 sm:pt-36 sm:pb-32 lg:pt-42 lg:pb-36 overflow-hidden bg-gradient-to-b from-[#F7FAFD] via-[#F0F6FE] to-[#F7FAFD] dark:from-[#0A0F18] dark:via-[#101826] dark:to-[#0A0F18] border-b border-theme transition-colors"
    >
      {/* --------------------------------------------------------------- */}
      {/* FLOWING SILK GRADIENT HORIZON (VisualJoy aesthetic reference)   */}
      {/* Volumetric chromatic silk ribbons with specular edge highlights */}
      {/* --------------------------------------------------------------- */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        {/* Soft Clinical Radial Glows */}
        <div
          className="absolute -top-32 left-1/2 -translate-x-1/2 w-[850px] h-[550px] rounded-full opacity-45 dark:opacity-20 blur-3xl pointer-events-none"
          style={{
            background:
              'radial-gradient(circle, rgba(21, 94, 239, 0.22) 0%, rgba(234, 242, 255, 0.15) 60%, transparent 100%)',
          }}
        />
        <div
          className="absolute top-1/3 -right-24 w-[600px] h-[500px] rounded-full opacity-35 dark:opacity-15 blur-3xl pointer-events-none"
          style={{
            background:
              'radial-gradient(circle, rgba(46, 144, 250, 0.18) 0%, rgba(221, 247, 236, 0.12) 65%, transparent 100%)',
          }}
        />

        {/* Faint subtle grid pattern for mathematical clinical precision */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.25] dark:opacity-[0.06]"
          style={{
            backgroundImage: 'radial-gradient(rgba(21, 94, 239, 0.22) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        {/* 3D Volumetric Silk Gradient Wave Canvas */}
        <SilkGradientWaveCanvas />

        {/* Soft bottom blend into the subsequent interactive demo section */}
        <div className="absolute bottom-0 left-0 right-0 h-28 bg-gradient-to-t from-canvas via-canvas/60 to-transparent pointer-events-none" />
      </div>

      {/* ========================================================= */}
      {/* CENTERED HERO CONTENT COLUMN (Elevated Typography Scale)   */}
      {/* ========================================================= */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-6 sm:space-y-8 flex flex-col items-center"
        >
          {/* Eyebrow Badge */}
          <motion.div variants={itemVariants}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#EAF2FF] dark:bg-[#16263D] border border-[#B2DDFF] dark:border-[rgba(255,255,255,0.12)] text-xs font-semibold text-[#155EEF] dark:text-[#84CAFF] shadow-xs hover:border-[#155EEF]/40 transition-colors">
              <span className="w-2 h-2 rounded-full bg-[#155EEF] dark:bg-[#4B8BFF] animate-pulse" />
              <span>PRESCRIPTION UNDERSTANDING, WITH CLARITY</span>
            </div>
          </motion.div>

          {/* Headline with Serif Italic Pairing (Enlarged by ~12% for Commanding Presence) */}
          <motion.div variants={itemVariants} className="max-w-4xl">
            <h1 className="text-[clamp(3.1rem,6.2vw,5.25rem)] font-extrabold tracking-[-0.038em] leading-[1.06] text-[#102A43] dark:text-[#F5F7FA]">
              Your prescription,{' '}
              <span className="font-serif italic font-normal tracking-tight text-[#155EEF] dark:text-[#4B8BFF] block sm:inline">
                understood with clarity.
              </span>
            </h1>
          </motion.div>

          {/* Supporting Paragraph (Elevated to 18–20px with Generous Line Height) */}
          <motion.div variants={itemVariants} className="max-w-2xl">
            <p className="text-base sm:text-lg lg:text-[1.25rem] text-theme-secondary leading-[1.65] font-normal">
              Understand handwritten prescriptions through structured medicine details, clear explanations, and honest uncertainty—so you know what needs professional verification.
            </p>
          </motion.div>

          {/* Action CTAs: High-presence 56px Pill Buttons */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-4 pt-3 w-full sm:w-auto"
          >
            {onOpenUpload && (
              <button
                type="button"
                onClick={onOpenUpload}
                className="btn-primary-pill group"
              >
                <span>Analyze a Prescription</span>
                <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
              </button>
            )}

            <button
              type="button"
              onClick={handleScrollToDemo}
              className="btn-secondary-pill"
            >
              <span>See How It Works</span>
            </button>
          </motion.div>

          {/* Trust Footnote */}
          <motion.div
            variants={itemVariants}
            className="pt-4 flex flex-wrap items-center justify-center gap-3 text-xs text-theme-muted"
          >
            <div className="flex items-center gap-1.5 font-medium">
              <ShieldCheck className="w-4 h-4 text-[#155EEF] dark:text-[#4B8BFF] shrink-0" />
              <span>Grounded Drug Formularies</span>
            </div>
            <span className="text-theme-muted/40 hidden sm:inline">&bull;</span>
            <div className="flex items-center gap-1.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>Selective Abstention on Ambiguity</span>
            </div>
            <span className="text-theme-muted/40 hidden sm:inline">&bull;</span>
            <div className="text-[11px] text-theme-muted">
              Original Document Remains Primary Authority
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};
