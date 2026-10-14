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
    // 3D SILK GRADIENT WAVE RIBBONS (VisualJoy inspired, DawaAI Clinical Palette)
    // -------------------------------------------------------------------------
    // Renders volumetric twisting silk ribbons with gradient lighting, specular
    // highlights, and soft ambient occlusion folds.
    // Purely autonomous, smooth harmonic undulation (no mouse interaction).
    // -------------------------------------------------------------------------
    const render = () => {
      if (!ctx || !isVisible) {
        if (!prefersReducedMotion) {
          animationFrameId = requestAnimationFrame(render);
        }
        return;
      }

      ctx.clearRect(0, 0, width, height);

      time += prefersReducedMotion ? 0 : 0.007;
      const dark = isDarkMode();

      // Ribbon anchor parameters (positioned in between content text and action buttons)
      const baseHorizon = height * 0.63;
      const step = 8; // Horizontal mesh resolution
      const numSteps = Math.ceil((width + 120) / step);

      // Ribbon Definition:
      // Ribbon 1: Soft broad background silk layer (Deep ambient glow & volume)
      // Ribbon 2: Primary foreground 3D chrome-silk ribbon with specular highlights & folds
      const ribbons = [
        // Background Secondary Silk Band
        {
          baseY: baseHorizon - 20,
          amplitude1: 45,
          amplitude2: 25,
          freq1: 0.0018,
          freq2: 0.0036,
          speed1: 0.55,
          speed2: 0.85,
          phase: 1.8,
          widthBase: 70,
          widthVar: 30,
          twistFreq: 0.0022,
          opacity: dark ? 0.75 : 0.40,
          specular: false,
        },
        // Foreground Main Volumetric Silk Ribbon (Primary focal feature)
        {
          baseY: baseHorizon,
          amplitude1: 65,
          amplitude2: 38,
          freq1: 0.0014,
          freq2: 0.0028,
          speed1: 0.7,
          speed2: 1.1,
          phase: 0.0,
          widthBase: 110,
          widthVar: 45,
          twistFreq: 0.0018,
          opacity: dark ? 0.95 : 0.75,
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
        bloomGrad.addColorStop(0, 'rgba(46, 144, 250, 0.22)');
        bloomGrad.addColorStop(0.4, 'rgba(21, 94, 239, 0.12)');
        bloomGrad.addColorStop(0.8, 'rgba(16, 42, 67, 0.05)');
        bloomGrad.addColorStop(1, 'rgba(10, 15, 24, 0)');
      } else {
        bloomGrad.addColorStop(0, 'rgba(46, 144, 250, 0.14)');
        bloomGrad.addColorStop(0.5, 'rgba(21, 94, 239, 0.06)');
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
          const twist = Math.sin(x * ribbon.twistFreq + time * 0.6 + ribbon.phase);
          const currentWidth = ribbon.widthBase + Math.cos(x * 0.002 + time * 0.4) * ribbon.widthVar;

          // Project upper and lower edges with 3D perspective fold
          const halfH = Math.max(12, Math.abs(twist) * currentWidth * 0.5);
          const yTop = centerY - halfH;
          const yBot = centerY + halfH;

          // Local slope calculation for specular light reflection
          const slope = (Math.cos(x * ribbon.freq1 + t1) * ribbon.amplitude1 * ribbon.freq1);

          topPts.push({ x, y: yTop, slope });
          botPts.push({ x, y: yBot });
        }

        if (topPts.length < 2) return;

        // Draw segmented volumetric silk gradient mesh
        // We draw vertical slice quads with rich chromatic gradients
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

          // Dynamic volumetric gradient for each slice with slope-based specular lighting
          const sliceGrad = ctx.createLinearGradient(p1Top.x, p1Top.y, p1Bot.x, p1Bot.y);
          const slopeFactor = 0.5 + 0.5 * Math.sin(p1Top.slope * 2.8);
          const highlightAlpha = Math.min(1, (0.85 + slopeFactor * 0.15) * ribbon.opacity);

          if (dark) {
            if (rIdx === 1) {
              // Primary Foreground Silk (Electric Cyan to Royal Cobalt to Obsidian)
              sliceGrad.addColorStop(0, `rgba(224, 242, 254, ${highlightAlpha})`); // Crisp chrome edge
              sliceGrad.addColorStop(0.12, `rgba(56, 189, 248, ${0.85 * ribbon.opacity})`); // Electric cyan highlight
              sliceGrad.addColorStop(0.38, `rgba(46, 144, 250, ${0.75 * ribbon.opacity})`); // Vibrant azure
              sliceGrad.addColorStop(0.68, `rgba(21, 94, 239, ${0.70 * ribbon.opacity})`); // Deep clinical cobalt
              sliceGrad.addColorStop(0.88, `rgba(16, 42, 67, ${0.55 * ribbon.opacity})`); // Deep navy shadow fold
              sliceGrad.addColorStop(1, 'rgba(10, 15, 24, 0.05)'); // Seamless dark fade
            } else {
              // Secondary Background Silk (Deep Indigo to Translucent Cyan)
              sliceGrad.addColorStop(0, `rgba(75, 139, 255, ${0.60 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.4, `rgba(21, 94, 239, ${0.50 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.8, `rgba(16, 42, 67, ${0.35 * ribbon.opacity})`);
              sliceGrad.addColorStop(1, 'rgba(10, 15, 24, 0.0)');
            }
          } else {
            if (rIdx === 1) {
              // Light Mode: Gleaming clinical blue silk with ice highlights
              sliceGrad.addColorStop(0, `rgba(240, 249, 255, ${highlightAlpha})`); // Crisp rim highlight
              sliceGrad.addColorStop(0.14, `rgba(56, 189, 248, ${0.65 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.42, `rgba(46, 144, 250, ${0.55 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.72, `rgba(21, 94, 239, ${0.45 * ribbon.opacity})`);
              sliceGrad.addColorStop(1, 'rgba(247, 250, 253, 0.0)');
            } else {
              sliceGrad.addColorStop(0, `rgba(46, 144, 250, ${0.40 * ribbon.opacity})`);
              sliceGrad.addColorStop(0.5, `rgba(21, 94, 239, ${0.30 * ribbon.opacity})`);
              sliceGrad.addColorStop(1, 'rgba(247, 250, 253, 0.0)');
            }
          }

          ctx.fillStyle = sliceGrad;
          ctx.fill();
        }

        // Luminous Crest Filament (Razor-sharp metallic / specular rim light on top edge)
        if (ribbon.specular) {
          ctx.beginPath();
          ctx.moveTo(topPts[0].x, topPts[0].y);
          for (let i = 1; i < topPts.length; i++) {
            ctx.lineTo(topPts[i].x, topPts[i].y);
          }

          // Specular stroke
          const rimGrad = ctx.createLinearGradient(0, 0, width, 0);
          if (dark) {
            rimGrad.addColorStop(0, 'rgba(56, 189, 248, 0.3)');
            rimGrad.addColorStop(0.3, 'rgba(224, 242, 254, 0.95)'); // Ultra-bright glint
            rimGrad.addColorStop(0.5, 'rgba(46, 144, 250, 0.8)');
            rimGrad.addColorStop(0.7, 'rgba(224, 242, 254, 0.95)'); // Ultra-bright glint
            rimGrad.addColorStop(1, 'rgba(56, 189, 248, 0.3)');
          } else {
            rimGrad.addColorStop(0, 'rgba(46, 144, 250, 0.4)');
            rimGrad.addColorStop(0.5, 'rgba(21, 94, 239, 0.9)');
            rimGrad.addColorStop(1, 'rgba(46, 144, 250, 0.4)');
          }

          ctx.strokeStyle = rimGrad;
          ctx.lineWidth = 2.2;
          ctx.stroke();

          // Subtle glowing secondary crest line inside the fold
          ctx.beginPath();
          ctx.moveTo(botPts[0].x, botPts[0].y);
          for (let i = 1; i < botPts.length; i++) {
            ctx.lineTo(botPts[i].x, botPts[i].y);
          }
          ctx.strokeStyle = dark ? 'rgba(75, 139, 255, 0.25)' : 'rgba(21, 94, 239, 0.15)';
          ctx.lineWidth = 1.2;
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
