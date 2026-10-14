import React from 'react';
import { motion, useReducedMotion, type Variants } from 'framer-motion';
import { ArrowRight, ShieldCheck } from 'lucide-react';

export interface HeroSectionProps {
  onOpenUpload?: () => void;
  onScrollToHowItWorks?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onOpenUpload,
  onScrollToHowItWorks,
}) => {
  const shouldReduceMotion = useReducedMotion();
  const [pointerOffset, setPointerOffset] = React.useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLElement>) => {
    if (shouldReduceMotion) return;
    const { clientX, clientY, currentTarget } = e;
    const rect = currentTarget.getBoundingClientRect();
    const xRel = (clientX - (rect.left + rect.width / 2)) / (rect.width / 2);
    const yRel = (clientY - (rect.top + rect.height / 2)) / (rect.height / 2);
    setPointerOffset({ x: Math.round(xRel * 14), y: Math.round(yRel * 8) });
  };

  const handleMouseLeave = () => {
    setPointerOffset({ x: 0, y: 0 });
  };

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
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative pt-28 pb-20 sm:pt-36 sm:pb-32 lg:pt-42 lg:pb-36 overflow-hidden bg-gradient-to-b from-[#F7FAFD] via-[#F0F6FE] to-[#F7FAFD] dark:from-[#0A0F18] dark:via-[#101826] dark:to-[#0A0F18] border-b border-theme transition-colors"
    >
      {/* --------------------------------------------------------------- */}
      {/* FLOWING WAVE BACKGROUND: Multi-layered organic SVG wave curves  */}
      {/* Cloud white, pale blue, translucent blue & dark navy gradients  */}
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

        {/* Wave Layer 1: Broad soft-blue background wave (Continuous Seamless Scroll) */}
        <div
          style={{
            transform: shouldReduceMotion
              ? undefined
              : `translate3d(${pointerOffset.x * 0.25}px, ${pointerOffset.y * 0.25}px, 0)`,
            transition: 'transform 0.4s ease-out',
          }}
          className="absolute top-12 left-0 w-full overflow-hidden opacity-50 dark:opacity-20 pointer-events-none"
        >
          <div className="w-[200%] flex animate-wave-continuous">
            <svg viewBox="0 0 2880 320" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto block">
              <path
                d="M 0 110.0 C 84.0 103.0, 156.0 69.8, 240.0 75.0 C 324.0 80.2, 396.0 121.5, 480.0 125.0 C 564.0 128.5, 636.0 81.5, 720.0 85.0 C 804.0 88.5, 876.0 131.5, 960.0 135.0 C 1044.0 138.5, 1116.0 103.8, 1200.0 95.0 C 1284.0 86.2, 1356.0 117.0, 1440.0 110.0 C 1524.0 103.0, 1596.0 69.8, 1680.0 75.0 C 1764.0 80.2, 1836.0 121.5, 1920.0 125.0 C 2004.0 128.5, 2076.0 81.5, 2160.0 85.0 C 2244.0 88.5, 2316.0 131.5, 2400.0 135.0 C 2484.0 138.5, 2556.0 103.8, 2640.0 95.0 C 2724.0 86.2, 2796.0 117.0, 2880.0 110.0 L 2880 320 L 0 320 Z"
                fill="url(#heroWaveGrad1)"
              />
              <defs>
                <linearGradient id="heroWaveGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#155EEF" stopOpacity="0.12" />
                  <stop offset="50%" stopColor="#2E90FA" stopOpacity="0.22" />
                  <stop offset="100%" stopColor="#155EEF" stopOpacity="0.12" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* Wave Layer 2: Subtle luminous light band shifting across wave surface */}
        <div className="absolute top-1/4 left-0 right-0 h-44 bg-gradient-to-r from-transparent via-[#2E90FA]/15 dark:via-[#4B8BFF]/10 to-transparent animate-wave-shimmer pointer-events-none blur-3xl" />

        {/* Wave Layer 3: Translucent secondary wave with counter-phase continuous scroll */}
        <div
          style={{
            transform: shouldReduceMotion
              ? undefined
              : `translate3d(${-pointerOffset.x * 0.35}px, ${-pointerOffset.y * 0.3}px, 0)`,
            transition: 'transform 0.4s ease-out',
          }}
          className="absolute top-1/2 -translate-y-1/2 left-0 w-full overflow-hidden opacity-65 dark:opacity-22 pointer-events-none"
        >
          <div className="w-[200%] flex animate-wave-continuous-reverse">
            <svg viewBox="0 0 2880 340" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto block">
              <path
                d="M 0 160.0 C 84.0 170.5, 156.0 217.0, 240.0 210.0 C 324.0 203.0, 396.0 145.2, 480.0 140.0 C 564.0 134.8, 636.0 198.5, 720.0 195.0 C 804.0 191.5, 876.0 135.2, 960.0 130.0 C 1044.0 124.8, 1116.0 169.5, 1200.0 180.0 C 1284.0 190.5, 1356.0 149.5, 1440.0 160.0 C 1524.0 170.5, 1596.0 217.0, 1680.0 210.0 C 1764.0 203.0, 1836.0 145.2, 1920.0 140.0 C 2004.0 134.8, 2076.0 198.5, 2160.0 195.0 C 2244.0 191.5, 2316.0 135.2, 2400.0 130.0 C 2484.0 124.8, 2556.0 169.5, 2640.0 180.0 C 2724.0 190.5, 2796.0 149.5, 2880.0 160.0 L 2880 340 L 0 340 Z"
                fill="url(#heroWaveGrad2)"
              />
              <defs>
                <linearGradient id="heroWaveGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#EAF2FF" stopOpacity="0.80" />
                  <stop offset="50%" stopColor="#D0E4FF" stopOpacity="0.60" />
                  <stop offset="100%" stopColor="#EAF2FF" stopOpacity="0.80" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* Wave Layer 4: Thin crisp blue highlight wave tracing the crest for depth */}
        <div className="absolute top-12 left-0 w-full overflow-hidden opacity-75 dark:opacity-35 pointer-events-none">
          <div className="w-[200%] flex animate-wave-highlight">
            <svg viewBox="0 0 2880 320" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto block">
              <path
                d="M 0 110.0 C 84.0 103.0, 156.0 69.8, 240.0 75.0 C 324.0 80.2, 396.0 121.5, 480.0 125.0 C 564.0 128.5, 636.0 81.5, 720.0 85.0 C 804.0 88.5, 876.0 131.5, 960.0 135.0 C 1044.0 138.5, 1116.0 103.8, 1200.0 95.0 C 1284.0 86.2, 1356.0 117.0, 1440.0 110.0 C 1524.0 103.0, 1596.0 69.8, 1680.0 75.0 C 1764.0 80.2, 1836.0 121.5, 1920.0 125.0 C 2004.0 128.5, 2076.0 81.5, 2160.0 85.0 C 2244.0 88.5, 2316.0 131.5, 2400.0 135.0 C 2484.0 138.5, 2556.0 103.8, 2640.0 95.0 C 2724.0 86.2, 2796.0 117.0, 2880.0 110.0"
                stroke="url(#heroWaveStrokeGrad)"
                strokeWidth="2.2"
                strokeLinecap="round"
                fill="none"
              />
              <defs>
                <linearGradient id="heroWaveStrokeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#155EEF" stopOpacity="0.45" />
                  <stop offset="50%" stopColor="#4B8BFF" stopOpacity="0.75" />
                  <stop offset="100%" stopColor="#155EEF" stopOpacity="0.45" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* Wave Layer 5: Seamless bottom transition into the interactive demo section */}
        <div className="absolute -bottom-1 left-0 right-0 w-full pointer-events-none opacity-95 dark:opacity-60">
          <svg
            viewBox="0 0 1440 90"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full h-auto block"
            preserveAspectRatio="none"
          >
            <path
              d="M0 35C240 70 480 15 720 45C960 75 1200 25 1440 50V90H0V35Z"
              className="fill-[#F7FAFD] dark:fill-[#0A0F18]"
            />
          </svg>
        </div>
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
