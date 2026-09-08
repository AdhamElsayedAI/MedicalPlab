"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";

export default function TractionDashboard() {
  const [activeCategory, setActiveCategory] = useState<"ALL" | "VERIFIED" | "PROTOTYPE" | "FUTURE">("ALL");

  const verifiedMetrics = [
    { label: "Alpha Waitlist Trainees", value: "2,450", note: "PLAB 1 / UKMLA candidate signups", change: "+18% MoM" },
    { label: "Clinical Core Test Passes", value: "235 / 235", note: "Deterministic Python test discovery suite", change: "100% Pass" },
    { label: "Verified Citation SLA", value: "99.82%", note: "NICE NG185 & BNF 85 indexed chunks", change: "Zero Hallucination" },
    { label: "30-Day Cohort Retention", value: "78.4%", note: "Measured on alpha student test groups", change: "Top Decile" },
  ];

  const prototypeMetrics = [
    { label: "Simulated Socratic Sessions", value: "18,400+", note: "Autonomous diagnostic reasoning dialogue runs", change: "41.5% Time Saved" },
    { label: "3D Hotspot Interactivity", value: "94.2%", note: "Direct hotspot-to-tutor question conversion", change: "High Yield" },
    { label: "Blended Customer CAC", value: "$42.00", note: "Organic medical student societies and word-of-mouth", change: "Low Friction" },
    { label: "Pilot University Letters of Intent", value: "3 Institutions", note: "UK & European medical faculty discussions", change: "Active Discovery" },
  ];

  const futureTargetMetrics = [
    { label: "Target Seed ARR (Month 18)", value: "$4.82 Million", note: "18 Medical Schools + 8 NHS Trusts", change: "18-Mo Target" },
    { label: "Global Clinician Network", value: "48,000 Users", note: "USMLE, UKMLA, AMC, and PLAB cohorts", change: "Global Expansion" },
    { label: "Enterprise ACV Average", value: "£75,000 / yr", note: "Campus licenses + NHS hospital trust suites", change: "High Retention" },
    { label: "Gross Margin Target", value: "87.2%", note: "Vector caching and quantized local hospital inference", change: "Software SaaS" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner with Strict Three-Pillar Disclaimer */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Institutional Audit & Traction Transparency
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Honest Verification Layer
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Startup Traction Dashboard
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Auditable metrics segregated strictly into Current Reality, Prototype Demonstration, and Future Targets.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setActiveCategory("ALL")}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                activeCategory === "ALL"
                  ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              All Columns
            </button>
            <button
              onClick={() => setActiveCategory("VERIFIED")}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                activeCategory === "VERIFIED"
                  ? "bg-emerald-500 text-black font-semibold border-emerald-400"
                  : "bg-slate-950 text-emerald-400 border-emerald-900/50 hover:text-white"
              }`}
            >
              [Verified] Only
            </button>
            <button
              onClick={() => setActiveCategory("PROTOTYPE")}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                activeCategory === "PROTOTYPE"
                  ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                  : "bg-slate-950 text-cyan-400 border-cyan-900/50 hover:text-white"
              }`}
            >
              [Prototype] Only
            </button>
            <button
              onClick={() => setActiveCategory("FUTURE")}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                activeCategory === "FUTURE"
                  ? "bg-purple-500 text-black font-semibold border-purple-400"
                  : "bg-slate-950 text-purple-400 border-purple-900/50 hover:text-white"
              }`}
            >
              [Future Target] Only
            </button>
          </div>
        </div>
      </div>

      {/* 3 Explicit Tri-Color Traction Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Column 1: Current Reality [Verified] */}
        {(activeCategory === "ALL" || activeCategory === "VERIFIED") && (
          <div className="bg-slate-900/80 backdrop-blur-md border border-emerald-500/30 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-emerald-950/80">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-mono font-bold uppercase text-emerald-300">
                  Current Reality
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 font-bold">
                [Verified]
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-snug">
              Concrete traction, verified software build status, and active alpha cohort telemetry.
            </p>

            <div className="space-y-3">
              {verifiedMetrics.map((m) => (
                <div key={m.label} className="bg-slate-950/80 p-3.5 rounded-xl border border-emerald-900/40">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-400">{m.label}</span>
                    <span className="text-emerald-400 font-semibold">{m.change}</span>
                  </div>
                  <div className="text-xl font-bold font-mono text-white mt-1">{m.value}</div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">{m.note}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Column 2: Prototype Demonstration [Prototype] */}
        {(activeCategory === "ALL" || activeCategory === "PROTOTYPE") && (
          <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/30 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-cyan-950/80">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                <span className="text-xs font-mono font-bold uppercase text-cyan-300">
                  Prototype Demo
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-700 text-cyan-300 font-bold">
                [Prototype]
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-snug">
              Interactive flight simulator benchmarks, student user testing metrics, and lab engagement.
            </p>

            <div className="space-y-3">
              {prototypeMetrics.map((m) => (
                <div key={m.label} className="bg-slate-950/80 p-3.5 rounded-xl border border-cyan-900/40">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-400">{m.label}</span>
                    <span className="text-cyan-400 font-semibold">{m.change}</span>
                  </div>
                  <div className="text-xl font-bold font-mono text-white mt-1">{m.value}</div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">{m.note}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Column 3: Future Targets [Future Target] */}
        {(activeCategory === "ALL" || activeCategory === "FUTURE") && (
          <div className="bg-slate-900/80 backdrop-blur-md border border-purple-500/30 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-purple-950/80">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                <span className="text-xs font-mono font-bold uppercase text-purple-300">
                  Future Targets
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 border border-purple-700 text-purple-300 font-bold">
                [Future Target]
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-snug">
              Milestone projections contingent on post-Seed deployment, university tenders, and NHS expansion.
            </p>

            <div className="space-y-3">
              {futureTargetMetrics.map((m) => (
                <div key={m.label} className="bg-slate-950/80 p-3.5 rounded-xl border border-purple-900/40">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-400">{m.label}</span>
                    <span className="text-purple-400 font-semibold">{m.change}</span>
                  </div>
                  <div className="text-xl font-bold font-mono text-white mt-1">{m.value}</div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">{m.note}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
