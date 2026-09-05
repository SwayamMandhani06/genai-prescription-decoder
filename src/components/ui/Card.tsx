import React from 'react';
import { cn } from '../../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'subtle' | 'elevated' | 'cyan' | 'amber' | 'coral' | 'interactive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, className, variant = 'glass', padding = 'md', ...props }, ref) => {
    const baseStyles = 'rounded-xl border transition-all duration-300 relative overflow-hidden';

    const paddingStyles = {
      none: 'p-0',
      sm: 'p-3 sm:p-4',
      md: 'p-5 sm:p-6',
      lg: 'p-6 sm:p-8',
    };

    const variantStyles = {
      glass: 'bg-slate-900/70 backdrop-blur-md border-white/[0.08] shadow-xl',
      subtle: 'bg-[#0B0F19]/60 backdrop-blur-sm border-white/[0.05]',
      elevated: 'bg-slate-900/90 border-white/[0.12] shadow-2xl',
      cyan: 'bg-cyan-950/20 backdrop-blur-md border-cyan-500/30 shadow-[0_0_30px_rgba(14,165,233,0.08)]',
      amber: 'bg-amber-950/20 backdrop-blur-md border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.08)]',
      coral: 'bg-red-950/20 backdrop-blur-md border-red-500/30 shadow-[0_0_30px_rgba(239,68,68,0.08)]',
      interactive:
        'bg-slate-900/60 backdrop-blur-md border-white/[0.08] hover:border-cyan-500/40 hover:bg-slate-900/80 hover:shadow-[0_8px_30px_rgba(14,165,233,0.12)] cursor-pointer',
    };

    return (
      <div
        ref={ref}
        className={cn(baseStyles, paddingStyles[padding], variantStyles[variant], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
