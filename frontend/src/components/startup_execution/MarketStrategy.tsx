"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { MARKET_SEGMENTS_DATA, MarketSegment } from "@/lib/startup-data";

export default function MarketStrategy() {
  const [selectedFilter, setSelectedFilter] = useState<"ALL" | "B2C" | "B2B">("ALL");

  const filteredSegments = MARKET_SEGMENTS_DATA.filter((seg) => {
    if (selectedFilter === "ALL") return true;
    return seg.segmentType === selectedFilter;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Filter Controls */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Go-To-Market Engine & Customer Segmentation
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                B2C Wedge $\to$ Enterprise Land-and-Expand
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Market Strategy & GTM Playbook
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Capital-efficient viral student acquisition unlocking multi-year enterprise medical school and hospital licenses.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedFilter("ALL")}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                selectedFilter === "ALL"
                  ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              All Segments (5)
            </button>
            <button
              onClick={() => setSelectedFilter("B2C")}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                selectedFilter === "B2C"
                  ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              B2C Learners (2)
            </button>
            <button
              onClick={() => setSelectedFilter("B2B")}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                selectedFilter === "B2B"
                  ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              B2B Enterprise (3)
            </button>
          </div>
        </div>
      </div>

      {/* Segment Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSegments.map((seg) => (
          <motion.div
            key={seg.id}
            whileHover={{ y: -3 }}
            className="bg-slate-900/70 backdrop-blur-md border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 shadow-xl flex flex-col justify-between transition-all group"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 font-bold uppercase">
                  {seg.segmentType} Segment
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {seg.activeStatus}
                </span>
              </div>

              <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                {seg.targetCustomer}
              </h3>
              <span className="text-xs font-mono text-emerald-400 font-semibold block mt-0.5">
                TAM: {seg.estimatedTAM}
              </span>

              <div className="mt-4 space-y-2.5 text-xs">
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                  <span className="text-[10px] font-mono text-slate-500 uppercase block mb-0.5">
                    Customer Problem
                  </span>
                  <p className="text-slate-300 leading-snug">{seg.customerProblem}</p>
                </div>

                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                  <span className="text-[10px] font-mono text-slate-500 uppercase block mb-0.5">
                    Value Proposition
                  </span>
                  <p className="text-slate-200 leading-snug">{seg.valueProposition}</p>
                </div>

                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                  <span className="text-[10px] font-mono text-slate-500 uppercase block mb-0.5">
                    Acquisition Channel
                  </span>
                  <p className="text-slate-300 leading-snug">{seg.acquisitionChannel}</p>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500 text-[10px]">Pricing:</span>
                <span className="text-cyan-400 font-bold text-right truncate max-w-[180px]">{seg.pricingModel}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 text-[10px]">Expansion:</span>
                <span className="text-slate-300 text-right truncate max-w-[180px]">{seg.expansionStrategy}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
