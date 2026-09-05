import React from 'react';
import { Activity, BookOpen, Layers, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#05070D] border-t border-white/[0.08] pt-14 pb-12 text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 pb-12 border-b border-white/[0.08]">
          {/* Brand & Capstone Vision */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Activity className="w-4 h-4" />
              </div>
              <span className="font-mono font-bold text-lg text-white">
                AURA<span className="text-cyan-400">-Rx</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Explainable Multimodal AI for Handwritten Prescription Understanding. An academic research capstone addressing clinical illegibility, selective prediction abstention, and patient-centric vernacular explanation.
            </p>
            <div className="text-[11px] font-mono text-slate-500 space-y-1">
              <div>Domain: Medical Informatics & Vision-Language AI</div>
              <div>Languages: English · हिन्दी · मराठी</div>
            </div>
          </div>

          {/* Research Architecture */}
          <div>
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Core Modules</span>
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#pipeline" className="hover:text-cyan-400 transition-colors">
                  Multimodal Layout & Tokenization
                </a>
              </li>
              <li>
                <a href="#pipeline" className="hover:text-cyan-400 transition-colors">
                  CDSCO & RxNorm Knowledge Grounding
                </a>
              </li>
              <li>
                <a href="#uncertainty" className="hover:text-cyan-400 transition-colors">
                  Calibrated Entropy & Selective Abstention
                </a>
              </li>
              <li>
                <a href="#lasa-safety" className="hover:text-cyan-400 transition-colors">
                  LASA Confusion Detection
                </a>
              </li>
              <li>
                <a href="#multilingual" className="hover:text-cyan-400 transition-colors">
                  Vernacular Patient Posology Synthesis
                </a>
              </li>
            </ul>
          </div>

          {/* Research Evaluation */}
          <div>
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-teal-400" />
              <span>Evaluation & Benchmarks</span>
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#benchmarks" className="hover:text-cyan-400 transition-colors">
                  Character & Word Error Rates (CER/WER)
                </a>
              </li>
              <li>
                <a href="#benchmarks" className="hover:text-cyan-400 transition-colors">
                  IndoRx-1200 Handwriting Dataset
                </a>
              </li>
              <li>
                <a href="#benchmarks" className="hover:text-cyan-400 transition-colors">
                  Abstention AUROC Curves
                </a>
              </li>
              <li>
                <a href="#benchmarks" className="hover:text-cyan-400 transition-colors">
                  Comparison vs Tesseract & Zero-Shot VLMs
                </a>
              </li>
            </ul>
          </div>

          {/* Academic Capstone Details */}
          <div>
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Project Information</span>
            </h4>
            <div className="space-y-3 text-xs">
              <p className="text-slate-400">
                Capstone Engineering Project in Multimodal Artificial Intelligence & Healthcare Systems.
              </p>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-white/5 space-y-1 text-[11px] font-mono">
                <div className="text-cyan-400 font-semibold">Phase 1: Architecture & UI</div>
                <div className="text-slate-400">Phase 2: FastAPI + Swin-Doc Inference</div>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white transition-colors"
                >
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                  <span>Repository</span>
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom copyright & status */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <p className="text-slate-500">
            © 2026 AURA-Rx Capstone Research Project. Built with React, TypeScript & Vite.
          </p>
          <div className="flex items-center gap-4 text-slate-500 font-mono text-[11px]">
            <span>MIT Academic License</span>
            <span>·</span>
            <span>Evidence-Grounded AI</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
