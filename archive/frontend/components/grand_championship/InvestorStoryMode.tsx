"use client";

import React, { useState } from "react";
import {
  TrendingUp,
  DollarSign,
  PieChart,
  ShieldCheck,
  Building2,
  Users,
  Briefcase,
  Sparkles,
  CheckCircle2,
  Info,
} from "lucide-react";
import { INVESTOR_METRICS, InvestorMetric } from "@/lib/grand-stage-data";

export const InvestorStoryMode: React.FC = () => {
  const [selectedSection, setSelectedSection] = useState<string>("ALL");

  const sections = ["ALL", "Market", "Business Model", "Technology Moat"];

  const filteredMetrics =
    selectedSection === "ALL"
      ? INVESTOR_METRICS
      : INVESTOR_METRICS.filter((m) => m.section === selectedSection);

  return (
    <div className="space-y-6">
      {/* Top Banner with Investor Rigor Notice */}
      <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              INSTITUTIONAL INVESTOR DOSSIER
            </span>
            <span className="text-xs font-mono text-slate-400">
              Seed Round Preparation: $1.5M on $12M Valuation Cap
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            <span>Market Opportunity, Monetization &amp; Technology Moat</span>
          </h2>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono shrink-0">
          <span className="px-2 py-1 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
            [Verified]
          </span>
          <span className="px-2 py-1 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
            [Prototype]
          </span>
          <span className="px-2 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
            [Projection]
          </span>
          <span className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
            [Future Target]
          </span>
        </div>
      </div>

      {/* Market Sizing Hero Cards (TAM / SAM / SOM) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase">Total Addressable Market</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              [Projection]
            </span>
          </div>
          <h3 className="text-3xl font-black text-white font-mono">$4.80B</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Global healthcare licensing exam prep, continuing medical education, and clinical simulation software market.
          </p>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase">Serviceable Addressable</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              [Projection]
            </span>
          </div>
          <h3 className="text-3xl font-black text-cyan-400 font-mono">$820M</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            International medical graduate licensing across UK (PLAB), US (USMLE), Australia (AMC), and Canada (MCCQE).
          </p>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase">Serviceable Obtainable</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              [Future Target]
            </span>
          </div>
          <h3 className="text-3xl font-black text-emerald-400 font-mono">$145M</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Immediate UK PLAB/UKMLA candidates and NHS Foundation Trust international recruit onboarding partnerships.
          </p>
        </div>
      </div>

      {/* Dual Monetization Model: B2C vs B2B */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* B2C Model */}
        <div className="p-6 rounded-2xl border border-cyan-500/30 bg-slate-950/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-cyan-400" />
              <h3 className="text-base font-bold text-white uppercase tracking-wider font-mono">
                B2C Direct-to-Candidate SaaS
              </h3>
            </div>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              [Verified]
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-white font-mono">£29.00</span>
            <span className="text-xs text-slate-400 font-mono">/ user / month</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Full individual access to 3D Anatomy Lab, Socratic AI Tutor, and Resuscitation Room simulation for PLAB 1 &amp; 2 candidates.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-2 text-xs font-mono">
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 block uppercase">Customer Lifetime</span>
              <span className="text-white font-bold mt-0.5 block">4.2 Months (£121.80 LTV)</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 block uppercase">Customer Acquisition</span>
              <span className="text-emerald-400 font-bold mt-0.5 block">&lt; £14.00 (8.7x LTV/CAC)</span>
            </div>
          </div>
        </div>

        {/* B2B Model */}
        <div className="p-6 rounded-2xl border border-purple-500/30 bg-slate-950/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-purple-400" />
              <h3 className="text-base font-bold text-white uppercase tracking-wider font-mono">
                B2B Enterprise Hospital Deanery
              </h3>
            </div>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40">
              [Prototype]
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-white font-mono">£45.00</span>
            <span className="text-xs text-slate-400 font-mono">/ doctor / month</span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Multi-tenant Deanery Command Center with real-time candidate clinical risk telemetry, automated cohort micro-drills, and audit compliance logging.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-2 text-xs font-mono">
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 block uppercase">Annual Contract (ACV)</span>
              <span className="text-white font-bold mt-0.5 block">£54k - £162k / Trust</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 block uppercase">Deanery Payback</span>
              <span className="text-purple-400 font-bold mt-0.5 block">&lt; 6 Weeks (8.5x ROI)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Software Unit Economics & Gross Margin Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/60 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-widest">
              TECHNOLOGY MOAT &amp; DEFENSIVE ECONOMICS
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              [Verified]
            </span>
          </div>
          <h4 className="text-xl font-black text-white">94.2% Software Gross Margin</h4>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Because MedicalPlab evaluates mathematical claims locally on standard CPU hardware with sub-50ms execution, runtime compute cost is less than <strong>$0.0039 per 30-minute session</strong>, shielding unit economics from third-party API price shocks.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-center shrink-0 min-w-[200px]">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">Inference Cost / Session</span>
          <span className="text-2xl font-black font-mono text-emerald-400 mt-1 block">&lt; $0.0039</span>
          <span className="text-[10px] font-mono text-slate-500 mt-0.5 block">Zero GPU Overhead</span>
        </div>
      </div>
    </div>
  );
};
