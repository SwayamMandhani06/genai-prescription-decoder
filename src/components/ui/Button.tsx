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
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none rounded-full focus-visible:outline-2 focus-visible:outline-offset-2';

  const sizeStyles = {
    sm: 'text-xs px-3.5 py-1.5 gap-1.5',
    md: 'text-sm px-5 py-2.5 gap-2',
    lg: 'text-base px-7 py-3.5 gap-2.5 font-semibold',
  };

  const variantStyles = {
    primary:
      'bg-gradient-to-r from-[#155EEF] to-[#2E90FA] hover:from-[#1249C7] hover:to-[#155EEF] text-white font-semibold shadow-xs hover:shadow-md hover:-translate-y-0.5 active:translate-y-0 focus-visible:outline-[#155EEF]',
    clinical:
      'bg-[#102A43] hover:bg-[#1E3A5F] active:bg-[#0B1D2D] text-white font-medium shadow-xs focus-visible:outline-[#102A43]',
    secondary:
      'bg-white dark:bg-[#102A43]/60 hover:bg-[#F7FAFD] dark:hover:bg-[#1E3A5F]/70 text-[#102A43] dark:text-white border border-[#D0D5DD] dark:border-[#1E3A5F] shadow-xs focus-visible:outline-[#155EEF]',
    outline:
      'bg-transparent hover:bg-[#EAF2FF]/50 text-[#155EEF] dark:text-[#4B8BFF] border border-[#155EEF]/30 hover:border-[#155EEF] shadow-xs focus-visible:outline-[#155EEF]',
    ghost:
      'bg-transparent hover:bg-[#EAF2FF]/40 text-[#102A43] dark:text-[#EAF2FF] hover:text-[#155EEF] dark:hover:text-[#4B8BFF] focus-visible:outline-[#155EEF]',
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
