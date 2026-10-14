import React, { useRef, useEffect } from 'react';

export interface InteractiveWaveCanvasProps {
  className?: string;
}

export const InteractiveWaveCanvas: React.FC<InteractiveWaveCanvasProps> = ({ className = '' }) => {
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

    // Smooth interpolated mouse tracking
    const mouse = {
      x: -2000,
      y: -2000,
      targetX: -2000,
      targetY: -2000,
      vx: 0,
      vy: 0,
      lastX: 0,
      lastY: 0,
      radius: 260,
      force: 0,
      targetForce: 0,
      ripples: [] as Array<{ x: number; y: number; radius: number; maxRadius: number; strength: number; age: number }>,
    };

    // Check prefers-reduced-motion
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Detect dark theme
    const isDarkMode = () => document.documentElement.classList.contains('dark');

    // Handle high-DPI canvas resizing
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

      // Default cursor to center when initialized
      if (mouse.targetX === -2000) {
        mouse.targetX = width * 0.5;
        mouse.targetY = height * 0.45;
        mouse.x = mouse.targetX;
        mouse.y = mouse.targetY;
        mouse.lastX = mouse.x;
        mouse.lastY = mouse.y;
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // Pointer events on the parent section for seamless coverage
    const sectionElement = canvas.closest('section') || canvas.parentElement || window;

    const handlePointerMove = (e: MouseEvent | TouchEvent) => {
      const clientX = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : (e as MouseEvent).clientY;
      const rect = canvas.getBoundingClientRect();

      const newTargetX = clientX - rect.left;
      const newTargetY = clientY - rect.top;

      // Calculate cursor speed for dynamic ripple generation
      const dx = newTargetX - mouse.lastX;
      const dy = newTargetY - mouse.lastY;
      const speed = Math.sqrt(dx * dx + dy * dy);

      mouse.targetX = newTargetX;
      mouse.targetY = newTargetY;
      mouse.targetForce = 1;

      // Spawn localized soft ripple pulses on noticeable mouse gestures
      if (speed > 18 && mouse.ripples.length < 5) {
        mouse.ripples.push({
          x: newTargetX,
          y: newTargetY,
          radius: 10,
          maxRadius: 280,
          strength: Math.min(speed * 0.04, 1.2),
          age: 0,
        });
      }

      mouse.lastX = newTargetX;
      mouse.lastY = newTargetY;
    };

    const handlePointerLeave = () => {
      mouse.targetForce = 0;
    };

    sectionElement.addEventListener('mousemove', handlePointerMove as EventListener, { passive: true });
    sectionElement.addEventListener('touchmove', handlePointerMove as EventListener, { passive: true });
    sectionElement.addEventListener('mouseleave', handlePointerLeave as EventListener);
    sectionElement.addEventListener('touchend', handlePointerLeave as EventListener);

    // Visibility observer to pause RAF when out of viewport
    const observer = new IntersectionObserver(
      (entries) => {
        isVisible = entries[0].isIntersecting;
      },
      { threshold: 0.05 }
    );
    observer.observe(canvas);

    // Harmonic biometric strands (mathematical frequency ribbons, NOT ocean waves)
    // Multiple overlapping resonant signals with varying wavelengths and ultra-slow speeds
    const strands = [
      {
        baseYRatio: 0.36,
        amplitude: 24,
        freq1: 0.0016,
        freq2: 0.0034,
        speed: 0.00035,
        phase: 0.0,
        lightStroke: 'rgba(21, 94, 239, 0.45)',
        darkStroke: 'rgba(75, 139, 255, 0.42)',
        lightGlow: 'rgba(21, 94, 239, 0.15)',
        darkGlow: 'rgba(75, 139, 255, 0.18)',
        lineWidth: 1.8,
        dots: true,
      },
      {
        baseYRatio: 0.44,
        amplitude: 34,
        freq1: 0.0012,
        freq2: 0.0028,
        speed: -0.00028,
        phase: 1.7,
        lightStroke: 'rgba(46, 144, 250, 0.38)',
        darkStroke: 'rgba(46, 144, 250, 0.35)',
        lightGlow: 'rgba(46, 144, 250, 0.12)',
        darkGlow: 'rgba(46, 144, 250, 0.14)',
        lineWidth: 2.2,
        dots: false,
      },
      {
        baseYRatio: 0.52,
        amplitude: 28,
        freq1: 0.0019,
        freq2: 0.0041,
        speed: 0.00042,
        phase: 3.14,
        lightStroke: 'rgba(11, 165, 233, 0.32)',
        darkStroke: 'rgba(56, 189, 248, 0.30)',
        lightGlow: 'rgba(11, 165, 233, 0.10)',
        darkGlow: 'rgba(56, 189, 248, 0.12)',
        lineWidth: 1.6,
        dots: true,
      },
      {
        baseYRatio: 0.60,
        amplitude: 38,
        freq1: 0.0014,
        freq2: 0.0031,
        speed: -0.00032,
        phase: 4.6,
        lightStroke: 'rgba(21, 94, 239, 0.28)',
        darkStroke: 'rgba(75, 139, 255, 0.26)',
        lightGlow: 'rgba(21, 94, 239, 0.08)',
        darkGlow: 'rgba(75, 139, 255, 0.10)',
        lineWidth: 1.8,
        dots: false,
      },
      {
        baseYRatio: 0.68,
        amplitude: 22,
        freq1: 0.0022,
        freq2: 0.0048,
        speed: 0.00025,
        phase: 5.8,
        lightStroke: 'rgba(46, 144, 250, 0.22)',
        darkStroke: 'rgba(46, 144, 250, 0.20)',
        lightGlow: 'rgba(46, 144, 250, 0.06)',
        darkGlow: 'rgba(46, 144, 250, 0.08)',
        lineWidth: 1.4,
        dots: true,
      },
    ];

    // Animation Render Loop
    const render = () => {
      if (!ctx || !isVisible) {
        if (!prefersReducedMotion) {
          animationFrameId = requestAnimationFrame(render);
        }
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Smooth damped lerp for mouse coordinates and activation force
      mouse.x += (mouse.targetX - mouse.x) * 0.045;
      mouse.y += (mouse.targetY - mouse.y) * 0.045;
      mouse.force += (mouse.targetForce - mouse.force) * 0.04;

      time += prefersReducedMotion ? 0 : 1;
      const dark = isDarkMode();

      // Update and age dynamic ripples
      for (let i = mouse.ripples.length - 1; i >= 0; i--) {
        const ripple = mouse.ripples[i];
        ripple.radius += 2.8;
        ripple.age += 1;
        ripple.strength *= 0.965;
        if (ripple.radius > ripple.maxRadius || ripple.strength < 0.02) {
          mouse.ripples.splice(i, 1);
        }
      }

      // Draw subtle ambient connection aura behind the waves when mouse is near
      if (mouse.force > 0.05) {
        const aura = ctx.createRadialGradient(
          mouse.x,
          mouse.y,
          0,
          mouse.x,
          mouse.y,
          mouse.radius
        );
        if (dark) {
          aura.addColorStop(0, `rgba(75, 139, 255, ${0.14 * mouse.force})`);
          aura.addColorStop(0.5, `rgba(46, 144, 250, ${0.05 * mouse.force})`);
          aura.addColorStop(1, 'rgba(10, 15, 24, 0)');
        } else {
          aura.addColorStop(0, `rgba(21, 94, 239, ${0.12 * mouse.force})`);
          aura.addColorStop(0.5, `rgba(46, 144, 250, ${0.04 * mouse.force})`);
          aura.addColorStop(1, 'rgba(247, 250, 253, 0)');
        }
        ctx.fillStyle = aura;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, mouse.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      // Render each strand as a flowing luminous biometric filament
      // (NO solid bottom fills - maintains scientific signal aesthetic)
      const step = 10; // High fidelity horizontal resolution

      // We pre-compute points for strand pairing and delicate band shading
      const strandPoints: Array<Array<{ x: number; y: number }>> = [];

      strands.forEach((strand) => {
        const centerY = height * strand.baseYRatio;
        const points: Array<{ x: number; y: number }> = [];

        for (let x = -20; x <= width + 20; x += step) {
          const t = time * strand.speed + strand.phase;
          // Dual harmonic superposition
          const wave1 = Math.sin(x * strand.freq1 + t) * strand.amplitude;
          const wave2 = Math.cos(x * strand.freq2 - t * 0.65) * (strand.amplitude * 0.42);
          let y = centerY + wave1 + wave2;

          // Interactive smooth Gaussian mouse displacement
          if (mouse.force > 0.01) {
            const dx = x - mouse.x;
            const dy = y - mouse.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < mouse.radius) {
              const normDist = dist / mouse.radius;
              // Smooth cosine bell-curve falloff
              const bell = Math.cos(normDist * (Math.PI / 2));
              const falloff = bell * bell;

              // Smoothly deform the line away/toward cursor based on relative vertical offset
              const verticalDirection = dy < 0 ? -1 : 1;
              const displacement = falloff * 54 * mouse.force * verticalDirection;
              y += displacement;
            }
          }

          // Active expanding ripple perturbations
          for (const rip of mouse.ripples) {
            const rdx = x - rip.x;
            const rdy = y - rip.y;
            const rdist = Math.sqrt(rdx * rdx + rdy * rdy);
            const diff = Math.abs(rdist - rip.radius);
            if (diff < 45) {
              const factor = (1 - diff / 45) * rip.strength;
              y += Math.sin((rdist - rip.radius) * 0.15) * 12 * factor;
            }
          }

          points.push({ x, y });
        }
        strandPoints.push(points);
      });

      // Render ultra-delicate gradient band between strands 1 & 2, and strands 3 & 4
      // This creates a soft volumetric ribbon of light without looking like an ocean wave
      const renderVolumetricBand = (topIdx: number, bottomIdx: number) => {
        const ptsTop = strandPoints[topIdx];
        const ptsBottom = strandPoints[bottomIdx];
        if (!ptsTop || !ptsBottom || ptsTop.length === 0) return;

        ctx.beginPath();
        ctx.moveTo(ptsTop[0].x, ptsTop[0].y);
        for (let i = 1; i < ptsTop.length; i++) {
          ctx.lineTo(ptsTop[i].x, ptsTop[i].y);
        }
        for (let i = ptsBottom.length - 1; i >= 0; i--) {
          ctx.lineTo(ptsBottom[i].x, ptsBottom[i].y);
        }
        ctx.closePath();

        const bandGrad = ctx.createLinearGradient(0, height * 0.35, 0, height * 0.65);
        if (dark) {
          bandGrad.addColorStop(0, 'rgba(75, 139, 255, 0.035)');
          bandGrad.addColorStop(0.5, 'rgba(46, 144, 250, 0.025)');
          bandGrad.addColorStop(1, 'rgba(21, 94, 239, 0.015)');
        } else {
          bandGrad.addColorStop(0, 'rgba(21, 94, 239, 0.035)');
          bandGrad.addColorStop(0.5, 'rgba(46, 144, 250, 0.025)');
          bandGrad.addColorStop(1, 'rgba(11, 165, 233, 0.015)');
        }
        ctx.fillStyle = bandGrad;
        ctx.fill();
      };

      renderVolumetricBand(0, 1);
      renderVolumetricBand(2, 3);

      // Stroke each strand curve with soft glowing aesthetics
      strands.forEach((strand, idx) => {
        const pts = strandPoints[idx];
        if (!pts || pts.length === 0) return;

        const strokeColor = dark ? strand.darkStroke : strand.lightStroke;
        const glowColor = dark ? strand.darkGlow : strand.lightGlow;

        // Outer soft glow pass
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) {
          ctx.lineTo(pts[i].x, pts[i].y);
        }
        ctx.strokeStyle = glowColor;
        ctx.lineWidth = strand.lineWidth + 2.5;
        ctx.stroke();

        // Core crisp filament line
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) {
          ctx.lineTo(pts[i].x, pts[i].y);
        }
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = strand.lineWidth;
        ctx.stroke();

        // Biometric data pulse nodes along select strands
        if (strand.dots) {
          const dotInterval = 14;
          for (let i = 0; i < pts.length; i += dotInterval) {
            const p = pts[i];
            // Slow breathing alpha for pulse dots
            const pulse = 0.4 + 0.6 * Math.sin(time * 0.02 + i * 0.3);
            ctx.beginPath();
            ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
            ctx.fillStyle = dark
              ? `rgba(180, 215, 255, ${0.45 * pulse})`
              : `rgba(21, 94, 239, ${0.4 * pulse})`;
            ctx.fill();
          }
        }
      });

      // Interactive subtle tension lines connecting cursor to nearest wave crests
      if (mouse.force > 0.25) {
        strandPoints.forEach((pts) => {
          let nearestPt = pts[0];
          let minDist = 99999;
          for (let i = 0; i < pts.length; i += 4) {
            const dx = pts[i].x - mouse.x;
            const dy = pts[i].y - mouse.y;
            const d = dx * dx + dy * dy;
            if (d < minDist) {
              minDist = d;
              nearestPt = pts[i];
            }
          }

          const dist = Math.sqrt(minDist);
          if (dist < 180) {
            const alpha = (1 - dist / 180) * 0.25 * mouse.force;
            ctx.beginPath();
            ctx.moveTo(mouse.x, mouse.y);
            ctx.lineTo(nearestPt.x, nearestPt.y);
            ctx.strokeStyle = dark
              ? `rgba(147, 197, 253, ${alpha})`
              : `rgba(46, 144, 250, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 4]);
            ctx.stroke();
            ctx.setLineDash([]);
          }
        });
      }

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      observer.disconnect();
      window.removeEventListener('resize', handleResize);
      sectionElement.removeEventListener('mousemove', handlePointerMove as EventListener);
      sectionElement.removeEventListener('touchmove', handlePointerMove as EventListener);
      sectionElement.removeEventListener('mouseleave', handlePointerLeave as EventListener);
      sectionElement.removeEventListener('touchend', handlePointerLeave as EventListener);
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
