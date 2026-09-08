"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { HEALTHCARE_METRICS, HealthcareMetric } from "@/lib/stage-x-data";

export default function GlobalHealthcareAnalytics() {
  const [selectedHospitalId, setSelectedHospitalId] = useState<string>(HEALTHCARE_METRICS[0].id);

  const activeHospital = HEALTHCARE_METRICS.find((h) => h.id === selectedHospitalId) || HEALTHCARE_METRICS[0];

  return (
    <div className="space-y-6">
      {/* Top Banner & Multi-Hospital Selector */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Enterprise Hospital Network Operations
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                Global Clinical Federation Active
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Global Healthcare Intelligence Analytics
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Population-level clinical diagnostic precision, workforce competency telemetry, and adverse event mitigation.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {HEALTHCARE_METRICS.map((hosp) => (
              <button
                key={hosp.id}
                onClick={() => setSelectedHospitalId(hosp.id)}
                className={`text-xs px-3.5 py-1.5 rounded-lg border transition-all ${
                  selectedHospitalId === hosp.id
                    ? "bg-cyan-500 text-black font-semibold border-cyan-400 shadow-md shadow-cyan-500/20"
                    : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                }`}
              >
                {hosp.hospitalName.split(" ")[0]} ({hosp.country})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 4 Enterprise Macro KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            Overall Diagnostic Accuracy
          </span>
          <span className="text-3xl font-black font-mono text-cyan-400 mt-2 block">
            {activeHospital.overallDiagnosticAccuracy}%
          </span>
          <div className="mt-2 text-xs text-emerald-400 font-mono flex items-center gap-1">
            <span>↑ 6.4%</span>
            <span className="text-slate-500">since AI baseline deployment</span>
          </div>
        </div>

        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            Adverse Event Reduction
          </span>
          <span className="text-3xl font-black font-mono text-emerald-400 mt-2 block">
            {activeHospital.annualAdverseEventReduction}
          </span>
          <div className="mt-2 text-xs text-emerald-400 font-mono flex items-center gap-1">
            <span>Verified</span>
            <span className="text-slate-500">clinical audit register</span>
          </div>
        </div>

        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            Workforce Clinicians Trained
          </span>
          <span className="text-3xl font-black font-mono text-teal-400 mt-2 block">
            {activeHospital.clinicalWorkforceTrained.toLocaleString()}
          </span>
          <div className="mt-2 text-xs text-slate-400 font-mono">
            Across {activeHospital.bedCapacity} acute beds
          </div>
        </div>

        <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase block">
            Regional Quality Rank
          </span>
          <span className="text-3xl font-black font-mono text-amber-400 mt-2 block">
            #{activeHospital.regionalRank}
          </span>
          <div className="mt-2 text-xs text-slate-400 font-mono">
            {activeHospital.region}
          </div>
        </div>
      </div>

      {/* Main Departmental Performance & Workforce Gap Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Departmental KPIs & Throughput */}
        <div className="lg:col-span-7 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
              Departmental Adherence & Throughput
            </span>
            <span className="text-xs font-mono text-slate-500">
              {activeHospital.hospitalName}
            </span>
          </div>

          <div className="space-y-3.5">
            {activeHospital.departmentalKPIs.map((kpi) => (
              <div
                key={kpi.department}
                className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-white">{kpi.department}</span>
                  <span className="text-xs font-mono text-emerald-400 font-semibold">
                    Saved {kpi.costSavingsEst}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                  <span>Throughput: {kpi.throughput}</span>
                  <span>Protocol Adherence: {kpi.protocolAdherence}%</span>
                </div>

                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${kpi.protocolAdherence}%` }}
                    transition={{ duration: 0.5 }}
                    className="h-full bg-cyan-400 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 5 Cols: Regional Heatmap & Training Gap Index */}
        <div className="lg:col-span-5 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-3">
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
                Regional Training Gap Index
              </span>
              <span className="text-xs font-mono text-amber-400 font-bold">
                {activeHospital.trainingGapIndex}% Discrepancy
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Real-time monitoring of deviations between published NICE/ESC clinical guidelines and actual electronic health record (EHR) order entries.
            </p>

            <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Target Discrepancy SLA:</span>
                <span className="text-emerald-400">&lt; 10.0%</span>
              </div>
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Current Facility Index:</span>
                <span className="text-cyan-400 font-bold">{activeHospital.trainingGapIndex}%</span>
              </div>
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Automated Remediation:</span>
                <span className="text-emerald-400">Enabled (Shift-Sync Active)</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span>Federated Privacy: Fully Anonymized</span>
            <span className="text-cyan-400">NHS DTAC Certified</span>
          </div>
        </div>
      </div>
    </div>
  );
}
