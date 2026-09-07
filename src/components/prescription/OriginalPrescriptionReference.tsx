import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { CheckCircle2, UserCheck, ShieldAlert } from 'lucide-react';

export const OriginalPrescriptionReference: React.FC = () => {
  const protocolSteps = [
    {
      step: 'STEP 01',
      title: 'Non-Destructive Spatial Layering',
      desc: 'The original optical scan is preserved as an immutable baseline layer. AI annotations are projected onto a transparent coordinate plane, never altering or obscuring raw ink pixels.',
      status: 'Statutory Baseline',
      statusColor: 'text-cyan-400',
    },
    {
      step: 'STEP 02',
      title: 'Tri-Tier Escalation Matrix',
      desc: 'Confidence is divided into Verified (>85%), Advisory Review (65-85%), and Hard Abstention (<65%). Low-confidence tokens trigger an automatic dispensing halt.',
      status: 'Safety Gate Active',
      statusColor: 'text-amber-400',
    },
    {
      step: 'STEP 03',
      title: 'Pharmacist Sign-Off Prerequisite',
      desc: 'Whenever an abstention is triggered (e.g. illegible decimal or LASA match), the digital explanation is locked until a licensed pharmacist physically compares the doctor pad and signs off.',
      status: 'Mandatory Human Protocol',
      statusColor: 'text-emerald-400',
    },
  ];

  return (
    <section className="py-20 bg-canvas border-b border-theme relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Clinical Governance Philosophy */}
          <div className="lg:col-span-6 space-y-6">
            <Badge variant="teal" size="sm" dot>
              Clinical Governance &amp; Protocol
            </Badge>

            <h2 className="text-2xl sm:text-4xl font-extrabold text-theme-primary tracking-tight font-sans">
              Human-in-the-Loop Clinical Safeguard Framework
            </h2>

            <p className="text-sm sm:text-base text-theme-secondary leading-relaxed font-sans">
              Artificial intelligence in pharmacy must assist human expertise, not replace accountability. AURA-Rx operates under a strict statutory protocol: the physician&rsquo;s physical handwriting is legally binding, and the software serves as an explainable assistive bridge.
            </p>

            <div className="space-y-4 pt-2 font-sans">
              {protocolSteps.map((p) => (
                <div key={p.step} className="p-3.5 rounded-xl bg-surface border border-theme space-y-1 shadow-xs">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-bold text-theme-primary">{p.step}: {p.title}</span>
                    <span className={`text-[10px] ${p.statusColor} font-semibold`}>{p.status}</span>
                  </div>
                  <p className="text-xs text-theme-secondary leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Interactive Escalation State Machine Visualization */}
          <div className="lg:col-span-6">
            <Card variant="glass" padding="lg" className="border-theme shadow-xs">
              <div className="flex items-center justify-between pb-3.5 border-b border-theme mb-5 font-mono text-xs">
                <div className="flex items-center gap-2 text-teal-700 dark:text-teal-400 font-bold">
                  <UserCheck className="w-4 h-4" />
                  <span>DISPENSING DECISION STATE MACHINE</span>
                </div>
                <span className="text-theme-muted text-[10px]">IEC 62304 MEDICAL SOFTWARE COMPLIANT</span>
              </div>

              {/* State Machine Flow Nodes */}
              <div className="space-y-3 font-mono text-xs">
                {/* Node 1 */}
                <div className="p-3 rounded-xl bg-surface-subtle border border-theme flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-teal-500" />
                    <span className="text-theme-primary">Intake Scan Ingested</span>
                  </div>
                  <span className="text-[10px] text-theme-muted">Polygon Mesh Parsed</span>
                </div>

                <div className="flex justify-center text-theme-muted">&darr;</div>

                {/* Node 2 */}
                <div className="p-3 rounded-xl bg-surface-subtle border border-theme flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-amber-500" />
                    <span className="text-theme-primary">Confidence Evaluated Against Threshold</span>
                  </div>
                  <span className="text-[10px] text-amber-700 dark:text-amber-400 font-semibold">Threshold: &tau; = 0.65</span>
                </div>

                <div className="flex justify-center text-theme-muted">&darr;</div>

                {/* Branch Decision */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-500/30 space-y-1">
                    <div className="text-[11px] font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                      <span>Score &ge; 0.65</span>
                    </div>
                    <div className="text-[10px] text-emerald-950 dark:text-slate-300 font-sans">
                      Verified &amp; Grounded &rarr; Patient posology enabled
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-red-50/70 dark:bg-red-950/30 border border-red-200 dark:border-red-500/30 space-y-1">
                    <div className="text-[11px] font-bold text-red-800 dark:text-red-400 flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
                      <span>Score &lt; 0.65 (Abstain)</span>
                    </div>
                    <div className="text-[10px] text-red-950 dark:text-slate-300 font-sans">
                      Automated output halted &rarr; Escalated to Pharmacist
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-5 p-3 rounded-xl bg-surface-subtle border border-theme text-xs text-theme-secondary leading-relaxed font-sans">
                <strong className="text-theme-primary font-mono block text-[11px] mb-0.5">
                  Statutory Healthcare Clause:
                </strong>
                Under Section 42 of the Pharmacy Act, dispensing prescription medicines without verification by a Registered Pharmacist is an offence. AURA-Rx is engineered with physical safeguards to uphold this legal mandate.
              </div>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};
