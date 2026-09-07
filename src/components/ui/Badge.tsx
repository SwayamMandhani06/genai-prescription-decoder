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
    cyan: 'bg-sky-50 dark:bg-sky-950/40 text-sky-800 dark:text-sky-300 border border-sky-200 dark:border-sky-800',
    teal: 'bg-teal-50 dark:bg-teal-950/40 text-teal-800 dark:text-teal-300 border border-teal-200 dark:border-teal-800',
    emerald: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800',
    amber: 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800',
    coral: 'bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800',
    slate: 'bg-surface-subtle text-theme-secondary border border-theme',
    outline: 'bg-transparent text-theme-secondary border border-theme',
  };

  const dotColors = {
    cyan: 'bg-sky-500',
    teal: 'bg-teal-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
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
