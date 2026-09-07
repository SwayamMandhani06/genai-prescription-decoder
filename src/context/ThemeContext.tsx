import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

export type ThemeMode = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

export interface ThemeContextType {
  theme: ThemeMode;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
}

const THEME_STORAGE_KEY = 'aura-theme-preference';

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null;
      if (saved === 'light' || saved === 'dark' || saved === 'system') {
        return saved;
      }
    }
    return 'light';
  });

  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('light');
  const isFirstMount = useRef<boolean>(true);

  // Compute resolved theme and update DOM
  useEffect(() => {
    const root = document.documentElement;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    let transitionTimer: number | null = null;

    const applyTheme = (triggerTransition = false) => {
      let resolved: ResolvedTheme = 'light';
      if (theme === 'system') {
        resolved = mediaQuery.matches ? 'dark' : 'light';
      } else {
        resolved = theme;
      }

      setResolvedTheme(resolved);

      if (triggerTransition) {
        root.classList.add('theme-transitioning');
        if (transitionTimer) window.clearTimeout(transitionTimer);
        transitionTimer = window.setTimeout(() => {
          root.classList.remove('theme-transitioning');
        }, 200);
      }

      if (resolved === 'dark') {
        root.classList.add('dark');
        root.classList.remove('light');
      } else {
        root.classList.remove('dark');
        root.classList.add('light');
      }
    };

    if (isFirstMount.current) {
      isFirstMount.current = false;
      // First mount without animation to prevent flicker
      applyTheme(false);
    } else {
      // User-initiated or dynamic change: apply fast, smooth transition
      applyTheme(true);
    }

    const handleChange = () => {
      if (theme === 'system') {
        applyTheme(true);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
      if (transitionTimer) window.clearTimeout(transitionTimer);
    };
  }, [theme]);

  const setTheme = (newTheme: ThemeMode) => {
    setThemeState(newTheme);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, newTheme);
    } catch {
      // Storage unavailable, ignore
    }
  };

  const toggleTheme = () => {
    // Cycles Light -> Dark -> System -> Light
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('system');
    else setTheme('light');
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
