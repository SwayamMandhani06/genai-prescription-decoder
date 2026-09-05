import React, { useState, useEffect } from 'react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  FileText,
  Activity,
  ShieldCheck,
  Languages,
  Layers,
  Menu,
  X,
  Sparkles,
  UploadCloud,
  FileSpreadsheet,
} from 'lucide-react';

export interface NavbarProps {
  onLaunchDemoClick: () => void;
  onOpenUploadClick?: () => void;
  onOpenResultsClick?: () => void;
  onHomeClick?: () => void;
  activeView?: 'home' | 'upload';
}

export const Navbar: React.FC<NavbarProps> = ({
  onLaunchDemoClick,
  onOpenUploadClick,
  onOpenResultsClick,
  onHomeClick,
  activeView = 'home',
}) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { label: 'Pipeline', href: '#pipeline', icon: Layers },
    { label: 'Live Analyzer', href: '#analyzer', icon: Sparkles },
    { label: 'Uncertainty', href: '#uncertainty', icon: Activity },
    { label: 'LASA Safety', href: '#lasa-safety', icon: ShieldCheck },
    { label: 'Multilingual', href: '#multilingual', icon: Languages },
    { label: 'Benchmarks', href: '#benchmarks', icon: FileText },
  ];

  const handleLogoClick = (e: React.MouseEvent) => {
    if (onHomeClick) {
      e.preventDefault();
      onHomeClick();
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        isScrolled
          ? 'bg-[#060911]/90 backdrop-blur-xl border-b border-white/[0.08] shadow-2xl py-2.5'
          : 'bg-transparent py-4'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Logo & Capstone Identifier */}
          <a
            href="#"
            onClick={handleLogoClick}
            className="flex items-center gap-3 group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(14,165,233,0.25)] group-hover:border-cyan-400 transition-colors">
              <Activity className="w-5 h-5 text-cyan-400 animate-pulse-subtle" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg sm:text-xl tracking-tight text-white font-mono">
                  AURA<span className="text-cyan-400">-Rx</span>
                </span>
                <Badge variant="cyan" size="xs" dot className="hidden sm:inline-flex">
                  Capstone v1.0
                </Badge>
              </div>
              <p className="text-[10px] text-slate-400 tracking-wider uppercase font-mono">
                Multimodal Prescription AI
              </p>
            </div>
          </a>

          {/* Desktop Navigation (Visible on Home view) */}
          {activeView === 'home' ? (
            <nav className="hidden lg:flex items-center gap-1 bg-slate-900/60 p-1.5 rounded-full border border-white/[0.08] backdrop-blur-md">
              {navLinks.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  className="px-3.5 py-1.5 text-xs font-medium text-slate-300 hover:text-white hover:bg-white/[0.06] rounded-full transition-all flex items-center gap-1.5"
                >
                  <item.icon className="w-3.5 h-3.5 text-slate-400" />
                  <span>{item.label}</span>
                </a>
              ))}
            </nav>
          ) : (
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs font-mono">
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Optical Prescription Ingestion Mode</span>
            </div>
          )}

          {/* Right Action Bar */}
          <div className="hidden sm:flex items-center gap-2.5">
            {onOpenUploadClick && (
              <Button
                variant="primary"
                size="sm"
                onClick={onOpenUploadClick}
                leftIcon={<UploadCloud className="w-3.5 h-3.5 text-slate-950" />}
              >
                Upload Script
              </Button>
            )}

            {onOpenResultsClick && (
              <Button
                variant="outline"
                size="sm"
                onClick={onOpenResultsClick}
                leftIcon={<FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />}
              >
                Findings
              </Button>
            )}

            {activeView === 'home' && (
              <Button
                variant="secondary"
                size="sm"
                onClick={onLaunchDemoClick}
                rightIcon={<Sparkles className="w-3.5 h-3.5 text-slate-300" />}
              >
                Simulate
              </Button>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <div className="flex sm:hidden items-center gap-2">
            {onOpenUploadClick && (
              <Button
                variant="primary"
                size="sm"
                onClick={onOpenUploadClick}
                className="text-xs px-2.5 py-1"
              >
                Upload
              </Button>
            )}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-400 hover:text-white rounded-lg border border-white/10"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="sm:hidden bg-[#0A0E1A] border-b border-white/10 px-4 pt-3 pb-5 mt-2 space-y-2">
          {activeView === 'home' &&
            navLinks.map((item) => (
              <a
                key={item.label}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 text-sm text-slate-200 hover:bg-white/5 rounded-lg"
              >
                <item.icon className="w-4 h-4 text-cyan-400" />
                <span>{item.label}</span>
              </a>
            ))}
          {onOpenUploadClick && (
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenUploadClick();
              }}
              className="w-full text-left flex items-center gap-2.5 px-3 py-2 text-sm text-cyan-300 font-mono hover:bg-white/5 rounded-lg cursor-pointer"
            >
              <UploadCloud className="w-4 h-4 text-cyan-400" />
              <span>Open Upload Viewfinder</span>
            </button>
          )}
          {onOpenResultsClick && (
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenResultsClick();
              }}
              className="w-full text-left flex items-center gap-2.5 px-3 py-2 text-sm text-emerald-300 font-mono hover:bg-white/5 rounded-lg cursor-pointer"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span>Clinical Findings Console</span>
            </button>
          )}
        </div>
      )}
    </header>
  );
};
