"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { PARTNERSHIPS_DATA, PartnershipOpportunity } from "@/lib/startup-data";

export default function PartnershipEngine() {
  const [selectedStage, setSelectedStage] = useState<string>("ALL");
  const [selectedType, setSelectedType] = useState<string>("ALL");

  const stages = ["ALL", "Lead", "Contact", "Discovery", "Pilot", "Contract", "Expansion"];
  const orgTypes = ["ALL", "Universities", "Hospitals", "Medical Organizations"];

  const filteredPartnerships = PARTNERSHIPS_DATA.filter((item) => {
    if (selectedStage !== "ALL" && item.stage !== selectedStage) return false;
    if (selectedType !== "ALL" && item.orgType !== selectedType) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Pipeline Health */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Institutional Enterprise Pipeline & BD Engine
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                UK / EU / US Medical Networks
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Partnership Engine
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Structured relationship pipeline spanning medical universities, academic hospital trusts, and accreditation bodies.
            </p>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
              <span className="text-slate-500">Pipeline Pipeline Value:</span>{" "}
              <span className="text-emerald-400 font-bold">£570,000+ ARR</span>
            </div>
            <div className="bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
              <span className="text-slate-500">Active Pilots:</span>{" "}
              <span className="text-cyan-400 font-bold">1 In-Flight</span>
            </div>
          </div>
        </div>

        {/* Filters Toolbar */}
        <div className="mt-5 pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
          {/* Stages Filter */}
          <div className="flex flex-wrap gap-1">
            {stages.map((stg) => (
              <button
                key={stg}
                onClick={() => setSelectedStage(stg)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  selectedStage === stg
                    ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                    : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white"
                }`}
              >
                {stg === "ALL" ? "All Stages" : stg}
              </button>
            ))}
          </div>

          {/* Org Type Filter */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            {orgTypes.map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  selectedType === t ? "bg-slate-800 text-cyan-300 font-semibold" : "text-slate-400 hover:text-white"
                }`}
              >
                {t === "ALL" ? "All Types" : t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Partnership Pipeline Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPartnerships.map((p) => (
          <motion.div
            key={p.id}
            whileHover={{ y: -3 }}
            className="bg-slate-900/70 backdrop-blur-md border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 shadow-xl flex flex-col justify-between transition-all group"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 uppercase">
                  {p.orgType}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 font-bold">
                  Stage: {p.stage}
                </span>
              </div>

              <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                {p.organizationName}
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-0.5">{p.region}</p>

              <div className="mt-4 space-y-2.5 text-xs">
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 font-mono">
                  <div className="text-slate-400">Institutional Champion:</div>
                  <div className="text-white font-bold">{p.championName}</div>
                  <div className="text-[11px] text-slate-500">{p.championTitle}</div>
                </div>

                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-slate-300 leading-snug">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase block mb-0.5">
                    Strategic Impact:
                  </span>
                  {p.strategicValue}
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500 text-[10px]">Estimated ACV:</span>
                <span className="text-emerald-400 font-bold">{p.dealSizeEst}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 text-[10px]">Next Milestone:</span>
                <span className="text-slate-300 text-right truncate max-w-[180px]">{p.nextMilestone}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
