import React from 'react';
import { Card } from '../ui/Card';
import { ShieldCheck, Lock, AlertTriangle } from 'lucide-react';

export const PrivacySafetyNotice: React.FC = () => {
  return (
    <Card variant="subtle" padding="md" className="border-white/[0.06] bg-[#0A0D15] rounded-xl space-y-3">
      <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
        <ShieldCheck className="w-4 h-4 text-emerald-400" />
        <span>Clinical Privacy & Statutory Protocol</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-sans text-slate-300">
        <div className="p-3 rounded bg-black/30 border border-white/5 space-y-1">
          <div className="flex items-center gap-1.5 font-bold text-white font-mono text-[11px]">
            <Lock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Ephemeral Session Isolation</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Uploaded prescription scans are processed locally in session memory. Images are never pooled for public LLM training or retained without explicit clinical consent.
          </p>
        </div>

        <div className="p-3 rounded bg-black/30 border border-white/5 space-y-1">
          <div className="flex items-center gap-1.5 font-bold text-white font-mono text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Prescriber Ground Truth</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            The original signed physical doctor&rsquo;s pad remains the primary legal document. AI-extracted posology provides explainable assistance, not an autonomous dispensary order.
          </p>
        </div>

        <div className="p-3 rounded bg-black/30 border border-white/5 space-y-1">
          <div className="flex items-center gap-1.5 font-bold text-white font-mono text-[11px]">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Mandatory Verification</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Whenever ink entropy exceeds calibrated thresholds, the system halts autonomous prediction and flags mandatory consultation with a licensed pharmacist.
          </p>
        </div>
      </div>
    </Card>
  );
};
