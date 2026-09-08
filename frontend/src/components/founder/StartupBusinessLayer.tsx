"use client";

import React from "react";
import {
  DollarSign,
  TrendingUp,
  Users,
  Building2,
  PieChart,
  Zap,
  ArrowUpRight,
  Sparkles,
  CheckCircle2,
  Globe2,
} from "lucide-react";
import { STARTUP_CUSTOMER_SEGMENTS } from "@/lib/founder-data";

export const StartupBusinessLayer: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5 text-cyan-400" />
              STARTUP BUSINESS & REVENUE INTELLIGENCE
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              SERIES SEED READY
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Dual B2C/B2B Engine with 94.2% Software Gross Margin
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Clear market sizing with labeled estimates, defensible CPU unit economics, and rapid multi-tenant global expansion.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-cyan-500/30 text-right">
            <span className="text-[10px] font-mono text-slate-400 block">CPU UNIT ECONOMICS</span>
            <span className="text-xs font-mono font-bold text-emerald-400">$0.0039 / Active Session</span>
          </div>
        </div>
      </div>

      {/* TAM / SAM / SOM Market Sizing Hierarchy (With Explicit Labels) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* TAM */}
        <div className="p-6 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg relative overflow-hidden space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">
              Total Addressable Market (TAM)
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-950 text-purple-300 border border-purple-500/40">
              Future opportunity
            </span>
          </div>
          <div className="text-3xl sm:text-4xl font-black font-mono text-white">
            $4.80 Billion
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            Global healthcare licensing examinations, USMLE Step 1/2, UK PLAB/MLA, Australian AMC, Canadian MCCQE, and continuous clinical recertification.
          </p>
          <div className="text-[11px] font-mono text-cyan-400 pt-2 border-t border-slate-800">
            Worldwide Healthcare Education Market
          </div>
        </div>

        {/* SAM */}
        <div className="p-6 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg relative overflow-hidden space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">
              Serviceable Addressable Market (SAM)
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-950 text-blue-300 border border-blue-500/40">
              Market estimate
            </span>
          </div>
          <div className="text-3xl sm:text-4xl font-black font-mono text-cyan-300">
            $950 Million
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            UK, Commonwealth, and English-speaking medical licensing diets, international graduates transitioning into English-speaking health systems.
          </p>
          <div className="text-[11px] font-mono text-emerald-400 pt-2 border-t border-slate-800">
            UK & Commonwealth Medical Certifications
          </div>
        </div>

        {/* SOM */}
        <div className="p-6 rounded-3xl bg-slate-950/90 border border-emerald-500/30 shadow-[0_0_25px_rgba(16,185,129,0.15)] relative overflow-hidden space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">
              Serviceable Obtainable Market (SOM)
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40">
              Target market
            </span>
          </div>
          <div className="text-3xl sm:text-4xl font-black font-mono text-emerald-400">
            $75 Million
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            Immediate 45,000 annual PLAB/UKMLA test takers and 215 NHS Foundation Hospital Trusts onboarding international junior doctors.
          </p>
          <div className="text-[11px] font-mono text-white pt-2 border-t border-slate-800">
            UK Beachhead: PLAB 1 & 2 Candidates + Trusts
          </div>
        </div>
      </div>

      {/* Customer Segments: B2C vs B2B */}
      <div className="space-y-4">
        <h4 className="text-sm font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <Users className="w-4 h-4 text-cyan-400" />
          <span>Target Customer Segments & Sales Cycles</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {STARTUP_CUSTOMER_SEGMENTS.map((seg, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 hover:border-cyan-500/40 transition-colors space-y-3"
            >
              <div className="flex items-center justify-between">
                <span
                  className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded ${
                    seg.type === "B2C"
                      ? "bg-cyan-950 text-cyan-300 border border-cyan-500/40"
                      : "bg-purple-950 text-purple-300 border border-purple-500/40"
                  }`}
                >
                  {seg.type} SEGMENT
                </span>
                <span className="text-xs font-mono font-bold text-white">
                  {seg.willingnessToPay}
                </span>
              </div>

              <h5 className="font-bold text-white text-sm">{seg.title}</h5>

              <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                {seg.targetAudience}
              </p>

              <div className="pt-2 border-t border-slate-800 space-y-1 text-[11px]">
                <div className="text-slate-500 font-mono">
                  Cycle: <span className="text-slate-300">{seg.salesCycle}</span>
                </div>
                <p className="text-cyan-200/90 font-sans leading-tight">
                  {seg.valueProp}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Revenue Models & Pricing Tiers */}
      <div className="space-y-4">
        <h4 className="text-sm font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <PieChart className="w-4 h-4 text-emerald-400" />
          <span>Core Monetization Tiers</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Tier 1 */}
          <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-cyan-400 font-bold uppercase">
                B2C Candidate Access
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-400">
                Self-serve
              </span>
            </div>
            <div className="text-3xl font-black font-mono text-white">
              £39 <span className="text-sm font-normal text-slate-400">/ month</span>
            </div>
            <ul className="space-y-2 text-xs text-slate-300 font-sans">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>Unlimited Socratic AI Tutor sessions</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>Zero-hallucination NICE NG185 citations</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>3D WebGL anatomical reasoning lab</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>Dynamic emergency resuscitation simulations</span>
              </li>
            </ul>
          </div>

          {/* Tier 2 */}
          <div className="p-6 rounded-3xl bg-gradient-to-b from-cyan-950/30 to-slate-950 border-2 border-cyan-400/50 shadow-[0_0_30px_rgba(0,242,254,0.15)] space-y-4 relative">
            <span className="absolute -top-3 right-6 px-3 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-400 text-black uppercase">
              HIGH VALUE B2B
            </span>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-cyan-300 font-bold uppercase">
                NHS Deanery Institutional
              </span>
            </div>
            <div className="text-3xl font-black font-mono text-white">
              £18,000 <span className="text-sm font-normal text-slate-400">/ yr / trust</span>
            </div>
            <ul className="space-y-2 text-xs text-slate-300 font-sans">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>Up to 250 junior doctor / candidate seats</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>Stage-G multi-tenant data isolation & RBAC</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>Deanery cohort weakness telemetry & audit logs</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>Custom hospital local guideline ingestion</span>
              </li>
            </ul>
          </div>

          {/* Tier 3 */}
          <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-purple-400 font-bold uppercase">
                International University
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-400">
                Academic
              </span>
            </div>
            <div className="text-3xl font-black font-mono text-white">
              £25,000 <span className="text-sm font-normal text-slate-400">/ yr / faculty</span>
            </div>
            <ul className="space-y-2 text-xs text-slate-300 font-sans">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                <span>Up to 1,000 medical students per academic year</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                <span>Full curriculum alignment to GMC & international standards</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                <span>Faculty predictive pass rate early warning engine</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                <span>Dedicated account manager & clinical onboarding</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
