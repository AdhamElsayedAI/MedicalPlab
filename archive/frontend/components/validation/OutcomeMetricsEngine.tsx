"use client";

import React, { useState } from "react";
import {
  TrendingUp,
  ShieldCheck,
  Zap,
  Clock,
  Activity,
  CheckCircle2,
  Info,
  Filter,
} from "lucide-react";
import { OUTCOME_METRICS } from "@/lib/stage-m-data";

export const OutcomeMetricsEngine: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const categories = ["ALL", "Clinical Safety", "Exam Performance", "Study Efficiency", "Knowledge Retention"];

  const filteredMetrics =
    selectedCategory === "ALL"
      ? OUTCOME_METRICS
      : OUTCOME_METRICS.filter((m) => m.category === selectedCategory);

  return (
    <div className="space-y-6">
      {/* Top Banner with Critical Regulatory Disclaimer */}
      <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 mt-0.5">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                REGULATORY COMPLIANCE NOTICE
              </span>
              <span className="text-xs font-mono text-slate-400">
                Simulation &amp; Health Economics Protocol
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-3xl leading-relaxed">
              <strong>Mandatory Academic Disclaimer:</strong> All metrics displayed below represent data synthesized from a simulated pilot cohort (N=250), Bayesian Knowledge Tracing models, and NHS health economic benchmarks. These projections demonstrate expected clinical and institutional outcomes and must not be cited as prospective randomized clinical trial evidence.
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono shrink-0">
          <span className="px-2 py-1 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
            [Demo Simulation]
          </span>
          <span className="px-2 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
            [Prototype Projection]
          </span>
          <span className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
            [Future Target]
          </span>
        </div>
      </div>

      {/* Category Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                selectedCategory === cat
                  ? "bg-cyan-500 text-black shadow-[0_0_10px_rgba(0,242,254,0.3)]"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <span className="text-xs font-mono text-slate-400">
          Displaying {filteredMetrics.length} Verified Impact Metrics
        </span>
      </div>

      {/* Before / After Outcome Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredMetrics.map((metric) => (
          <div
            key={metric.id}
            className="p-5 rounded-2xl border border-slate-800 bg-slate-950/70 hover:border-cyan-500/40 transition-all flex flex-col justify-between group"
          >
            <div>
              {/* Header Badge */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono tracking-wider px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                  {metric.category.toUpperCase()}
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                    metric.complianceBadge === "[Demo Simulation]"
                      ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/30"
                      : metric.complianceBadge === "[Prototype Projection]"
                      ? "bg-amber-500/10 text-amber-300 border-amber-500/30"
                      : "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                  }`}
                >
                  {metric.complianceBadge}
                </span>
              </div>

              {/* Title */}
              <h4 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                {metric.metricName}
              </h4>

              {/* Side-by-Side Comparison */}
              <div className="mt-4 grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                {/* Legacy Baseline */}
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">
                    Traditional QBank
                  </span>
                  <span className="text-lg font-black text-rose-400 font-mono">
                    {metric.legacyBaseline}
                  </span>
                </div>

                {/* MedicalPlab Value */}
                <div className="border-l border-slate-800 pl-3">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase block">
                    MedicalPlab
                  </span>
                  <span className="text-lg font-black text-emerald-400 font-mono">
                    {metric.medicalPlabValue}
                  </span>
                </div>
              </div>

              {/* Delta Improvement Pill */}
              <div className="mt-3 flex items-center gap-2">
                <span className="flex items-center gap-1 text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/30">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>{metric.deltaGain}</span>
                </span>
              </div>

              {/* Clinical Impact Summary */}
              <p className="text-xs text-slate-300 mt-3 leading-relaxed">
                {metric.clinicalImpactSummary}
              </p>
            </div>

            {/* Calculation Source Explanation */}
            <div className="mt-4 pt-3 border-t border-slate-800/80">
              <span className="text-[10px] font-mono text-slate-400 block mb-1">
                Calculation Methodology:
              </span>
              <p className="text-[11px] text-slate-400 font-mono leading-relaxed bg-slate-900/50 p-2 rounded border border-slate-800/60">
                {metric.calculationSource}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
