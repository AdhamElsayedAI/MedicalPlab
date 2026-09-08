"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { FINANCIAL_PROJECTIONS_DATA, REVENUE_STREAMS_DATA, FinancialProjection } from "@/lib/startup-data";

export default function FinancialModel() {
  const [selectedYear, setSelectedYear] = useState<FinancialProjection["year"]>("Year 2");
  const [b2cPrice, setB2cPrice] = useState<number>(29); // £ / mo
  const [campusPrice, setCampusPrice] = useState<number>(120); // £ / student / yr
  const [scenarioGrowth, setScenarioGrowth] = useState<"Base" | "Optimistic">("Base");

  const baseProj = FINANCIAL_PROJECTIONS_DATA.find((p) => p.year === selectedYear) || FINANCIAL_PROJECTIONS_DATA[1];

  // Dynamic calculations based on interactive assumptions
  const multiplier = scenarioGrowth === "Optimistic" ? 1.35 : 1.0;
  const priceMultiplier = (b2cPrice / 29) * 0.5 + (campusPrice / 120) * 0.5;

  const dynamicPayingUsers = Math.round(baseProj.payingUsers * multiplier);
  const dynamicInstitutions = Math.round(baseProj.institutionalClients * multiplier);
  const dynamicLTV = Math.round(baseProj.ltvUsd * (b2cPrice / 29));
  const dynamicPayback = (baseProj.paybackMonths * (29 / b2cPrice)).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Top Banner & Assumption Toggles */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-emerald-400">
                Unit Economics & 3-Year Projections
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Interactive SaaS Model
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab SaaS Financial Intelligence
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              High-margin recurring revenue engine combining low-CAC consumer loops with high-ACV institutional contracts.
            </p>
          </div>

          {/* Year Selector */}
          <div className="flex items-center gap-2">
            {FINANCIAL_PROJECTIONS_DATA.map((p) => (
              <button
                key={p.year}
                onClick={() => setSelectedYear(p.year)}
                className={`text-xs px-3.5 py-1.5 rounded-lg border transition-all ${
                  selectedYear === p.year
                    ? "bg-emerald-500 text-black font-semibold border-emerald-400 shadow-md shadow-emerald-500/20"
                    : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                }`}
              >
                {p.year} ({p.classification})
              </button>
            ))}
          </div>
        </div>

        {/* Interactive Assumption Sliders */}
        <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">B2C Subscription Price:</span>
              <span className="text-cyan-400 font-bold">£{b2cPrice} / mo</span>
            </div>
            <input
              type="range"
              min="19"
              max="49"
              value={b2cPrice}
              onChange={(e) => setB2cPrice(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>£19 (Discount)</span>
              <span>£49 (Premium OSCE)</span>
            </div>
          </div>

          <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">University Seat Price:</span>
              <span className="text-cyan-400 font-bold">£{campusPrice} / yr</span>
            </div>
            <input
              type="range"
              min="80"
              max="180"
              value={campusPrice}
              onChange={(e) => setCampusPrice(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>£80 (Entry)</span>
              <span>£180 (Full Lab)</span>
            </div>
          </div>

          <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">Growth Scenario:</span>
              <span className="text-emerald-400 font-bold">{scenarioGrowth} (+{((multiplier - 1) * 100).toFixed(0)}%)</span>
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => setScenarioGrowth("Base")}
                className={`flex-1 py-1 text-xs rounded-lg border transition-colors ${
                  scenarioGrowth === "Base" ? "bg-slate-800 text-cyan-300 border-cyan-500/40 font-semibold" : "bg-slate-900 text-slate-400 border-slate-800"
                }`}
              >
                Base Case
              </button>
              <button
                onClick={() => setScenarioGrowth("Optimistic")}
                className={`flex-1 py-1 text-xs rounded-lg border transition-colors ${
                  scenarioGrowth === "Optimistic" ? "bg-emerald-950 text-emerald-300 border-emerald-500/40 font-semibold" : "bg-slate-900 text-slate-400 border-slate-800"
                }`}
              >
                Bull Case
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 6 Macro SaaS Unit Economics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 text-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Annual Run Rate</span>
          <span className="text-xl font-bold font-mono text-cyan-400 mt-1 block">
            {selectedYear === "Year 1" ? "$840k" : selectedYear === "Year 2" ? "$4.82M" : "$16.4M"}
          </span>
          <span className="text-[10px] font-mono text-slate-400">{baseProj.classification}</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 text-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Monthly Recurring</span>
          <span className="text-xl font-bold font-mono text-emerald-400 mt-1 block">
            {selectedYear === "Year 1" ? "$70k" : selectedYear === "Year 2" ? "$401k" : "$1.36M"}
          </span>
          <span className="text-[10px] font-mono text-slate-400">MRR</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 text-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Blended CAC</span>
          <span className="text-xl font-bold font-mono text-teal-400 mt-1 block">
            ${baseProj.cacUsd}
          </span>
          <span className="text-[10px] font-mono text-emerald-400">Organic Viral</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 text-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Customer LTV</span>
          <span className="text-xl font-bold font-mono text-indigo-400 mt-1 block">
            ${dynamicLTV}
          </span>
          <span className="text-[10px] font-mono text-slate-400">{(dynamicLTV / baseProj.cacUsd).toFixed(1)}x LTV/CAC</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 text-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Gross Margin</span>
          <span className="text-xl font-bold font-mono text-amber-400 mt-1 block">
            {baseProj.grossMarginPercent}%
          </span>
          <span className="text-[10px] font-mono text-emerald-400">Token Cached</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 text-center">
          <span className="text-[10px] font-mono text-slate-500 uppercase block">Payback Period</span>
          <span className="text-xl font-bold font-mono text-purple-400 mt-1 block">
            {dynamicPayback} mo
          </span>
          <span className="text-[10px] font-mono text-slate-400">Rapid Recycling</span>
        </div>
      </div>

      {/* Revenue Streams & Cost Structure Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 6 Cols: Revenue Streams Matrix */}
        <div className="lg:col-span-6 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider block pb-2 border-b border-slate-800">
            Active Monetization Streams
          </span>

          <div className="space-y-3">
            {REVENUE_STREAMS_DATA.map((stream) => (
              <div
                key={stream.streamName}
                className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">{stream.streamName}</span>
                    <span className="text-[10px] font-mono text-cyan-400">{stream.status}</span>
                  </div>
                  <span className="text-xs font-mono text-slate-400 mt-0.5 block">{stream.pricePoint}</span>
                  <span className="text-[10px] text-slate-500 font-mono">{stream.volumeLabel}</span>
                </div>
                <div className="text-right">
                  <span className="text-base font-bold font-mono text-emerald-400 block">{stream.annualizedValue}</span>
                  <span className="text-[10px] font-mono text-slate-400">{stream.marginPercent}% margin</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 6 Cols: OpEx Cost Breakdown */}
        <div className="lg:col-span-6 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block pb-2 border-b border-slate-800">
            {selectedYear} Annual OpEx Structure
          </span>

          <div className="space-y-3 font-mono text-xs">
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-slate-300">GPU Cloud & Inference:</span>
              <span className="text-cyan-400 font-bold">{baseProj.costBreakdown.cloudAndInference}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-slate-300">Engineering & Core AI Team:</span>
              <span className="text-blue-400 font-bold">{baseProj.costBreakdown.engineeringAndTeam}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-slate-300">Clinical Governance & Compliance:</span>
              <span className="text-emerald-400 font-bold">{baseProj.costBreakdown.clinicalAdvisoryAndCompliance}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-slate-300">GTM & Institutional Sales:</span>
              <span className="text-amber-400 font-bold">{baseProj.costBreakdown.gtmAndSales}</span>
            </div>
          </div>

          <div className="p-3 bg-cyan-950/30 border border-cyan-500/20 rounded-xl text-[11px] text-cyan-300 font-mono">
            Projection Note: Token caching and vector indexing keep AI inference costs below 14% of overall revenue, preserving high software margins.
          </div>
        </div>
      </div>
    </div>
  );
}
