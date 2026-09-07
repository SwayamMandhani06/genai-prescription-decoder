import React, { useState, useRef, useEffect } from 'react';
import { useTheme, ThemeMode } from '../../context/ThemeContext';
import { Sun, Moon, Monitor, Check } from 'lucide-react';

export const ThemeSwitcher: React.FC = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const options: { mode: ThemeMode; label: string; icon: React.ElementType }[] = [
    { mode: 'light', label: 'Light', icon: Sun },
    { mode: 'dark', label: 'Dark', icon: Moon },
    { mode: 'system', label: 'System', icon: Monitor },
  ];

  const currentIcon = () => {
    if (theme === 'system') return Monitor;
    return resolvedTheme === 'dark' ? Moon : Sun;
  };

  const IconComponent = currentIcon();

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Theme setting: currently ${theme}. Click to change theme.`}
        title={`Theme: ${theme} (resolved: ${resolvedTheme})`}
        className="p-2 rounded-lg text-theme-secondary hover:text-theme-primary bg-surface-subtle hover:bg-surface border border-theme transition-colors cursor-pointer flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-teal-500/40"
      >
        <IconComponent className="w-4 h-4 text-theme-primary" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-40 py-1.5 bg-surface-elevated border border-theme rounded-xl shadow-elevated-card z-50 animate-in fade-in slide-in-from-top-1 duration-150">
          <div className="px-3.5 py-1 text-[11px] font-semibold text-theme-muted uppercase tracking-wider border-b border-theme mb-1">
            Appearance
          </div>
          {options.map((opt) => {
            const OptIcon = opt.icon;
            const isSelected = theme === opt.mode;
            return (
              <button
                key={opt.mode}
                onClick={() => {
                  setTheme(opt.mode);
                  setIsOpen(false);
                }}
                className={`w-full px-3.5 py-2 text-xs font-medium flex items-center justify-between text-left transition-colors cursor-pointer ${
                  isSelected
                    ? 'text-teal-700 dark:text-teal-300 font-semibold bg-teal-500/10'
                    : 'text-theme-secondary hover:text-theme-primary hover:bg-surface-subtle'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <OptIcon className="w-4 h-4" />
                  <span>{opt.label}</span>
                </div>
                {isSelected && <Check className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
