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
            'absolute z-50 px-2.5 py-1.5 text-xs text-slate-200 bg-slate-900/95 border border-white/10 rounded-md shadow-2xl backdrop-blur-md pointer-events-none whitespace-nowrap font-mono animate-in fade-in zoom-in-95 duration-150',
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
