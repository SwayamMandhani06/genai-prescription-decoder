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
    cyan: 'bg-[#EAF2FF] dark:bg-[#155EEF]/20 text-[#155EEF] dark:text-[#4B8BFF] border border-[#155EEF]/25',
    teal: 'bg-[#DDF7EC] dark:bg-emerald-950/40 text-[#027A48] dark:text-[#6CE9A6] border border-[#12B76A]/30',
    emerald: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800',
    amber: 'bg-[#FFFAEB] dark:bg-amber-950/40 text-[#B54708] dark:text-[#FEDF89] border border-[#F79009]/30',
    coral: 'bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800',
    slate: 'bg-surface-subtle text-theme-secondary border border-theme',
    outline: 'bg-transparent text-theme-secondary border border-theme',
  };

  const dotColors = {
    cyan: 'bg-[#155EEF]',
    teal: 'bg-[#12B76A]',
    emerald: 'bg-emerald-500',
    amber: 'bg-[#F79009]',
    coral: 'bg-red-500',
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
