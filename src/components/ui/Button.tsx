import React from 'react';
import { cn } from '../../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'clinical';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2';

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2.5 gap-2',
    lg: 'text-base px-6 py-3 gap-2.5 font-semibold',
  };

  const variantStyles = {
    primary:
      'bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white font-medium shadow-xs focus-visible:outline-teal-600',
    clinical:
      'bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white font-medium shadow-xs focus-visible:outline-sky-600',
    secondary:
      'bg-surface hover:bg-surface-subtle text-theme-primary border border-theme shadow-xs focus-visible:outline-sky-500',
    outline:
      'bg-transparent hover:bg-surface text-theme-primary border border-theme hover:border-theme-hover shadow-xs focus-visible:outline-sky-500',
    ghost:
      'bg-transparent hover:bg-surface-subtle text-theme-secondary hover:text-theme-primary focus-visible:outline-sky-500',
    danger:
      'bg-red-50 hover:bg-red-100 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 focus-visible:outline-red-600',
  };

  return (
    <button
      className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          />
        </svg>
      ) : (
        leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>
      )}
      <span>{children}</span>
      {rightIcon && <span className="inline-flex shrink-0">{rightIcon}</span>}
    </button>
  );
};
