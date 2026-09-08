"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { GOVERNANCE_METRICS, GovernanceMetric } from "@/lib/stage-x-data";

export default function AIGovernanceCenter() {
  const [selectedCategory, setSelectedCategory] = useState<GovernanceMetric["category"]>("Evidence Coverage");

  const activeMetric = GOVERNANCE_METRICS.find((g) => g.category === selectedCategory) || GOVERNANCE_METRICS[0];

  const categories: GovernanceMetric["category"][] = [
    "Evidence Coverage",
    "Safety Validation",
    "Audit History",
    "Human Oversight"
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs uppercase tracking-widest font-mono text-emerald-400">
                AI Trust, Safety & Institutional Governance
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-300">
                EU AI Act & FDA SaMD Tier-1 Compliant
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab AI Governance & Trust Center
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Cryptographically verifiable citation trails, human clinical oversight, and autonomous fail-safe safety barriers.
            </p>
          </div>

          {/* Category Tabs */}
          <div className="flex items-center gap-2 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  selectedCategory === cat
                    ? "bg-emerald-500 text-black font-semibold border-emerald-400 shadow-md shadow-emerald-500/20"
                    : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 4 Macro Safety Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">Evidence Provenance</span>
          <span className="text-2xl md:text-3xl font-black font-mono text-cyan-400 mt-2 block">99.82%</span>
          <span className="text-xs text-emerald-400 font-mono mt-1 block">Zero Uncited Claims</span>
        </div>

        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">Lethal Omission Shield</span>
          <span className="text-2xl md:text-3xl font-black font-mono text-emerald-400 mt-2 block">100.00%</span>
          <span className="text-xs text-emerald-400 font-mono mt-1 block">Zero Critical Failures</span>
        </div>

        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">Audit Trail Events</span>
          <span className="text-2xl md:text-3xl font-black font-mono text-teal-400 mt-2 block">382,900+</span>
          <span className="text-xs text-slate-400 font-mono mt-1 block">SHA-256 Ledger</span>
        </div>

        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">Board Reviewers</span>
          <span className="text-2xl md:text-3xl font-black font-mono text-amber-400 mt-2 block">142 MDs</span>
          <span className="text-xs text-emerald-400 font-mono mt-1 block">Human-in-the-Loop</span>
        </div>
      </div>

      {/* Main Detail Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Specific Governance Category Deep-Dive */}
        <div className="lg:col-span-7 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider">
                {activeMetric.category} Inspector
              </span>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300">
              {activeMetric.status}
            </span>
          </div>

          <div>
            <h3 className="text-lg font-bold text-white">{activeMetric.title}</h3>
            <p className="text-xs text-slate-300 mt-2 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 leading-relaxed">
              {activeMetric.safetyDetails}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono text-xs">
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] uppercase block">Benchmark:</span>
              <span className="text-white font-semibold">{activeMetric.benchmark}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] uppercase block">Human Oversight Rate:</span>
              <span className="text-emerald-400 font-semibold">{activeMetric.humanInterventionRate}</span>
            </div>
          </div>

          <div className="pt-2 text-xs font-mono text-slate-500 flex justify-between">
            <span>Audit Trail Count: {activeMetric.auditTrailCount.toLocaleString()}</span>
            <span>Last Certified: {activeMetric.lastCertifiedDate}</span>
          </div>
        </div>

        {/* Right 5 Cols: AI Risk Monitoring Vectors */}
        <div className="lg:col-span-5 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
              AI Risk Monitoring Vectors
            </span>
            <span className="text-[10px] font-mono text-slate-500">Live Scanners</span>
          </div>

          <div className="space-y-3">
            {activeMetric.riskVectorScores.map((vec) => (
              <div key={vec.vector} className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-200">{vec.vector}</span>
                  <span className="text-emerald-400 font-bold">{vec.score}%</span>
                </div>
                <div className="flex justify-between text-[10px] font-mono text-slate-500">
                  <span>Risk Level: {vec.riskLevel}</span>
                  <span>Safety Guardrail Enforced</span>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-xl text-[11px] text-emerald-300 font-mono">
            Investor Due Diligence: Full compliance logs exportable with cryptographic SHA-256 proofs.
          </div>
        </div>
      </div>
    </div>
  );
}
