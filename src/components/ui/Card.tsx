import React from 'react';
import { cn } from '../../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'subtle' | 'elevated' | 'cyan' | 'amber' | 'coral' | 'interactive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, className, variant = 'glass', padding = 'md', ...props }, ref) => {
    const baseStyles = 'rounded-xl border transition-all duration-200 relative overflow-hidden';

    const paddingStyles = {
      none: 'p-0',
      sm: 'p-3 sm:p-4',
      md: 'p-5 sm:p-6',
      lg: 'p-6 sm:p-8',
    };

    const variantStyles = {
      glass: 'bg-surface/90 border-theme shadow-xs',
      subtle: 'bg-surface-subtle border-theme',
      elevated: 'bg-surface border-theme shadow-md',
      cyan: 'bg-sky-50/70 dark:bg-sky-950/20 border-sky-200 dark:border-sky-800/80',
      amber: 'bg-amber-50/70 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800/80',
      coral: 'bg-red-50/70 dark:bg-red-950/20 border-red-200 dark:border-red-800/80',
      interactive:
        'bg-surface border-theme hover:border-theme-hover hover:shadow-sm cursor-pointer',
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
