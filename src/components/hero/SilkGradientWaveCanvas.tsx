import React, { useRef, useEffect } from 'react';

export interface SilkGradientWaveCanvasProps {
  className?: string;
}

export const SilkGradientWaveCanvas: React.FC<SilkGradientWaveCanvasProps> = ({ className = '' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let isVisible = true;
    let width = 0;
    let height = 0;
    let time = 0;

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const isDarkMode = () => document.documentElement.classList.contains('dark');

    // Resize handler with high-DPI crisp pixel ratio
    const handleResize = () => {
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);

      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // Pause animation when scrolled out of viewport
    const observer = new IntersectionObserver(
      (entries) => {
        isVisible = entries[0].isIntersecting;
      },
      { threshold: 0.05 }
    );
    observer.observe(canvas);

    // -------------------------------------------------------------------------
    // 3D SILK GRADIENT WAVE RIBBONS (Autonomous, Gentle, Calibrated Light Palette)
    // -------------------------------------------------------------------------
    // Renders volumetric twisting silk ribbons with soft ambient lighting, gentle
    // specular edge accents, and translucent pastel gradients that never distract.
    // -------------------------------------------------------------------------
    const render = () => {
      if (!ctx || !isVisible) {
        if (!prefersReducedMotion) {
          animationFrameId = requestAnimationFrame(render);
        }
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Smooth, slow autonomous undulation without mouse interference
      time += prefersReducedMotion ? 0 : 0.005;
      const dark = isDarkMode();

      // Ribbon anchor parameters (positioned gracefully in lower third of hero)
      const baseHorizon = height * 0.78;
      const step = 8; // Horizontal mesh resolution
      const numSteps = Math.ceil((width + 120) / step);

      // Ribbon Definition (Soft, light, translucent, non-disturbing):
      const ribbons = [
        // Background Secondary Silk Band
        {
          baseY: baseHorizon - 22,
          amplitude1: 36,
          amplitude2: 20,
          freq1: 0.0016,
          freq2: 0.0032,
          speed1: 0.45,
          speed2: 0.70,
          phase: 1.8,
          widthBase: 60,
          widthVar: 25,
          twistFreq: 0.0020,
          opacity: dark ? 0.28 : 0.16,
          specular: false,
        },
        // Foreground Main Volumetric Silk Ribbon (Soft light focal feature)
        {
          baseY: baseHorizon,
          amplitude1: 52,
          amplitude2: 30,
          freq1: 0.0013,
          freq2: 0.0026,
          speed1: 0.55,
          speed2: 0.85,
          phase: 0.0,
          widthBase: 95,
          widthVar: 35,
          twistFreq: 0.0016,
          opacity: dark ? 0.38 : 0.22,
          specular: true,
        },
      ];

      // Soft ambient blue light bloom behind the silk ribbons
      const bloomGrad = ctx.createRadialGradient(
        width * 0.5,
        baseHorizon,
        10,
        width * 0.5,
        baseHorizon,
        width * 0.48
      );
      if (dark) {
        bloomGrad.addColorStop(0, 'rgba(56, 189, 248, 0.08)');
        bloomGrad.addColorStop(0.5, 'rgba(21, 94, 239, 0.04)');
        bloomGrad.addColorStop(1, 'rgba(10, 15, 24, 0)');
      } else {
        bloomGrad.addColorStop(0, 'rgba(186, 230, 253, 0.10)');
        bloomGrad.addColorStop(0.5, 'rgba(147, 197, 253, 0.03)');
        bloomGrad.addColorStop(1, 'rgba(247, 250, 253, 0)');
      }
      ctx.fillStyle = bloomGrad;
      ctx.fillRect(0, 0, width, height);

      // Render each silk ribbon
      ribbons.forEach((ribbon, rIdx) => {
        const topPts: Array<{ x: number; y: number; slope: number }> = [];
        const botPts: Array<{ x: number; y: number }> = [];

        for (let i = -6; i <= numSteps + 6; i++) {
          const x = i * step;

          // Multi-harmonic sine + cosine undulation
          const t1 = time * ribbon.speed1 + ribbon.phase;
          const t2 = time * ribbon.speed2 - ribbon.phase * 0.6;

          const wave1 = Math.sin(x * ribbon.freq1 + t1) * ribbon.amplitude1;
          const wave2 = Math.cos(x * ribbon.freq2 + t2) * ribbon.amplitude2;

          const centerY = ribbon.baseY + wave1 + wave2;

          // 3D twist modulation along ribbon path
          const twist = Math.sin(x * ribbon.twistFreq + time * 0.5 + ribbon.phase);
          const currentWidth = ribbon.widthBase + Math.cos(x * 0.002 + time * 0.35) * ribbon.widthVar;

          // Project upper and lower edges with 3D perspective fold
          const halfH = Math.max(10, Math.abs(twist) * currentWidth * 0.5);
          const yTop = centerY - halfH;
          const yBot = centerY + halfH;

          // Local slope calculation for specular light reflection
          const slope = (Math.cos(x * ribbon.freq1 + t1) * ribbon.amplitude1 * ribbon.freq1);

          topPts.push({ x, y: yTop, slope });
          botPts.push({ x, y: yBot });
        }

        if (topPts.length < 2) return;

        // Draw segmented volumetric silk gradient mesh
        for (let i = 0; i < topPts.length - 1; i++) {
          const p1Top = topPts[i];
          const p2Top = topPts[i + 1];
          const p1Bot = botPts[i];
          const p2Bot = botPts[i + 1];

          ctx.beginPath();
          ctx.moveTo(p1Top.x, p1Top.y);
          ctx.lineTo(p2Top.x, p2Top.y);
          ctx.lineTo(p2Bot.x, p2Bot.y);
          ctx.lineTo(p1Bot.x, p1Bot.y);
          ctx.closePath();

          // Dynamic volumetric gradient for each slice with subtle specular lighting
          const sliceGrad = ctx.createLinearGradient(p1Top.x, p1Top.y, p1Bot.x, p1Bot.y);
          const slopeFactor = 0.5 + 0.5 * Math.sin(p1Top.slope * 2.8);
          const highlightAlpha = Math.min(1, (0.75 + slopeFactor * 0.25) * ribbon.opacity);

          if (dark) {
            if (rIdx === 1) {
              // Primary Foreground Silk (Gentle luminescent cyan/azure)
              sliceGrad.addColorStop(0, `rgba(224, 242, 254, ${highlightAlpha * 0.7})`);
              sliceGrad.addColorStop(0.18, `rgba(56, 189, 248, ${0.45 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.48, `rgba(46, 144, 250, ${0.35 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.78, `rgba(21, 94, 239, ${0.25 * ribbon.opacity})`);
              sliceGrad.addColorStop(1, 'rgba(10, 15, 24, 0.0)');
            } else {
              // Secondary Background Silk
              sliceGrad.addColorStop(0, `rgba(56, 189, 248, ${0.25 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.5, `rgba(30, 58, 138, ${0.18 * ribbon.opacity})`);
              sliceGrad.addColorStop(1, 'rgba(10, 15, 24, 0.0)');
            }
          } else {
            if (rIdx === 1) {
              // Light Mode: Very soft, airy, translucent pastel ice-blue
              sliceGrad.addColorStop(0, `rgba(255, 255, 255, ${highlightAlpha * 0.6})`); // Soft pearlescent rim
              sliceGrad.addColorStop(0.18, `rgba(224, 242, 254, ${0.40 * ribbon.opacity})`); // Subtle ice cyan
              sliceGrad.addColorStop(0.48, `rgba(186, 230, 253, ${0.30 * ribbon.opacity})`); // Translucent sky blue
              sliceGrad.addColorStop(0.78, `rgba(147, 197, 253, ${0.20 * ribbon.opacity})`); // Light pastel azure
              sliceGrad.addColorStop(1, 'rgba(247, 250, 253, 0.0)'); // Clean fade
            } else {
              // Secondary Background Silk (Subtle ambient pastel veil)
              sliceGrad.addColorStop(0, `rgba(186, 230, 253, ${0.22 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.5, `rgba(147, 197, 253, ${0.14 * ribbon.opacity})`);
              sliceGrad.addColorStop(1, 'rgba(247, 250, 253, 0.0)');
            }
          }

          ctx.fillStyle = sliceGrad;
          ctx.fill();
        }

        // Luminous Crest Filament (Delicate metallic / pearlescent rim accent)
        if (ribbon.specular) {
          ctx.beginPath();
          ctx.moveTo(topPts[0].x, topPts[0].y);
          for (let i = 1; i < topPts.length; i++) {
            ctx.lineTo(topPts[i].x, topPts[i].y);
          }

          const rimGrad = ctx.createLinearGradient(0, 0, width, 0);
          if (dark) {
            rimGrad.addColorStop(0, 'rgba(56, 189, 248, 0.15)');
            rimGrad.addColorStop(0.3, 'rgba(224, 242, 254, 0.6)');
            rimGrad.addColorStop(0.5, 'rgba(56, 189, 248, 0.4)');
            rimGrad.addColorStop(0.7, 'rgba(224, 242, 254, 0.6)');
            rimGrad.addColorStop(1, 'rgba(56, 189, 248, 0.15)');
          } else {
            rimGrad.addColorStop(0, 'rgba(186, 230, 253, 0.15)');
            rimGrad.addColorStop(0.3, 'rgba(255, 255, 255, 0.6)');
            rimGrad.addColorStop(0.5, 'rgba(147, 197, 253, 0.35)');
            rimGrad.addColorStop(0.7, 'rgba(255, 255, 255, 0.6)');
            rimGrad.addColorStop(1, 'rgba(186, 230, 253, 0.15)');
          }

          ctx.strokeStyle = rimGrad;
          ctx.lineWidth = 1.0;
          ctx.stroke();

          // Subtle secondary fold accent
          ctx.beginPath();
          ctx.moveTo(botPts[0].x, botPts[0].y);
          for (let i = 1; i < botPts.length; i++) {
            ctx.lineTo(botPts[i].x, botPts[i].y);
          }
          ctx.strokeStyle = dark ? 'rgba(75, 139, 255, 0.12)' : 'rgba(147, 197, 253, 0.08)';
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      });

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      observer.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full pointer-events-none select-none ${className}`}
      aria-hidden="true"
    />
  );
};
