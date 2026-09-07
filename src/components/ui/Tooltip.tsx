import React, { useState } from 'react';
import { cn } from '../../utils/cn';

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  position?: 'top' | 'bottom';
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  className,
  position = 'top',
}) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className={cn(
            'absolute z-50 px-2.5 py-1.5 text-xs text-theme-primary bg-surface border border-theme rounded-lg shadow-lg pointer-events-none whitespace-nowrap font-mono animate-in fade-in zoom-in-95 duration-150',
            position === 'top' && 'bottom-full mb-2 left-1/2 -translate-x-1/2',
            position === 'bottom' && 'top-full mt-2 left-1/2 -translate-x-1/2',
            className
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
};
