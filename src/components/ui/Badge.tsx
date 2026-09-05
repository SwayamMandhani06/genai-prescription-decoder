import React from 'react';
import { cn } from '../../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'cyan' | 'teal' | 'emerald' | 'amber' | 'coral' | 'slate' | 'outline';
  size?: 'xs' | 'sm' | 'md';
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className,
  variant = 'cyan',
  size = 'sm',
  dot = false,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full tracking-wide transition-colors';

  const sizeStyles = {
    xs: 'text-[10px] px-2 py-0.5 gap-1',
    sm: 'text-xs px-2.5 py-1 gap-1.5',
    md: 'text-sm px-3 py-1.5 gap-2',
  };

  const variantStyles = {
    cyan: 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30',
    teal: 'bg-teal-500/15 text-teal-300 border border-teal-500/30',
    emerald: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
    amber: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
    coral: 'bg-red-500/15 text-red-300 border border-red-500/30',
    slate: 'bg-slate-800/80 text-slate-300 border border-slate-700/60',
    outline: 'bg-transparent text-slate-300 border border-slate-700',
  };

  const dotColors = {
    cyan: 'bg-cyan-400 shadow-[0_0_8px_#38bdf8]',
    teal: 'bg-teal-400 shadow-[0_0_8px_#2dd4bf]',
    emerald: 'bg-emerald-400 shadow-[0_0_8px_#34d399]',
    amber: 'bg-amber-400 shadow-[0_0_8px_#fbbf24]',
    coral: 'bg-red-400 shadow-[0_0_8px_#f87171]',
    slate: 'bg-slate-400',
    outline: 'bg-slate-400',
  };

  return (
    <span className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)} {...props}>
      {dot && (
        <span
          className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColors[variant])}
          aria-hidden="true"
        />
      )}
      <span>{children}</span>
    </span>
  );
};
