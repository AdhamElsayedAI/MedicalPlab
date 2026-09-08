"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { FOUNDER_TASKS_DATA, FounderTask } from "@/lib/startup-data";

export default function FounderOperatingSystem() {
  const [tasks, setTasks] = useState<FounderTask[]>(FOUNDER_TASKS_DATA);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const categories = ["ALL", "Product", "Growth", "Sales", "Engineering", "Medical Validation"];

  const toggleTask = (id: string) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, isComplete: !t.isComplete } : t))
    );
  };

  const filteredTasks = tasks.filter((t) => {
    if (selectedCategory === "ALL") return true;
    return t.category === selectedCategory;
  });

  const sprintObjectives = [
    { area: "User Interviews", goal: "Complete 15 PLAB/UKMLA candidate diagnostic feedback calls", progress: "11 / 15 Calls Done" },
    { area: "Product Iterations", goal: "Deploy Socratic dialogue speed optimizations (sub-80ms)", progress: "Shipped & Tested ✓" },
    { area: "Partnership Outreach", goal: "Submit Imperial College pilot contract to curriculum dean", progress: "Draft Under Review" },
    { area: "Investor Conversations", goal: "Brief 5 seed angel syndicates specializing in digital health", progress: "3 Pitch Meetings Scheduled" },
  ];

  const criticalRisks = [
    { risk: "UKMLA Blueprint Evolution", impact: "High", mitigation: "Continuous autonomous guideline synchronization pipeline (Stage-X indexed)" },
    { risk: "GPU Inference Cost at Scale", impact: "Medium", mitigation: "Semantic caching layer reducing redundant token invocations by 40%" },
    { risk: "NHS Enterprise Procurement Cycle", impact: "High", mitigation: "B2C student bottom-up wedge converts demand before formal tender" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Daily Founder Execution & Operating Cadence
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Sprint Week 36 • Seed Stage Focus
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Founder Operating System (Founder OS)
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Ruthless prioritization across product iteration, user interviews, university partnerships, and venture fundraising.
            </p>
          </div>

          {/* Quick Filter */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs flex-wrap">
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setSelectedCategory(c)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  selectedCategory === c
                    ? "bg-cyan-500 text-black font-semibold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main OS Layout: Weekly Objectives & Active Priority Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Active Priority Task Board */}
        <div className="lg:col-span-7 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider font-semibold">
              Founder Daily Priority Action Items ({tasks.filter((t) => !t.isComplete).length} Pending)
            </span>
            <span className="text-xs font-mono text-slate-500">Click check to toggle</span>
          </div>

          <div className="space-y-3">
            {filteredTasks.map((t) => (
              <div
                key={t.id}
                onClick={() => toggleTask(t.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3 ${
                  t.isComplete
                    ? "bg-slate-950/40 border-slate-800/60 opacity-60 line-through"
                    : "bg-slate-950/80 border-slate-800 hover:border-cyan-500/50 text-slate-200"
                }`}
              >
                <input
                  type="checkbox"
                  checked={t.isComplete}
                  onChange={() => toggleTask(t.id)}
                  className="mt-1 accent-cyan-400 cursor-pointer"
                />
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold">
                      {t.category}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        t.priority === "P0 Critical"
                          ? "bg-red-950/80 border border-red-800 text-red-300"
                          : "bg-amber-950/80 border border-amber-800 text-amber-300"
                      }`}
                    >
                      {t.priority}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">Due: {t.dueDate}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-white">{t.title}</h4>
                  <p className="text-xs text-slate-400 font-mono">Target Deliverable: {t.deliverable}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 5 Cols: Weekly Sprint Focus & Risk Register */}
        <div className="lg:col-span-5 space-y-5">
          {/* Weekly Objectives */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider block">
              This Week&apos;s 4 Strategic Objectives
            </span>
            <div className="space-y-2.5">
              {sprintObjectives.map((obj) => (
                <div key={obj.area} className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-white font-bold">{obj.area}</span>
                    <span className="text-cyan-400">{obj.progress}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">{obj.goal}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Strategic Risk & Mitigation Register */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-amber-500/30 rounded-2xl p-5 shadow-xl space-y-3">
            <span className="text-xs font-mono text-amber-400 uppercase tracking-wider block">
              Executive Risk Register & Countermeasures
            </span>
            <div className="space-y-2.5">
              {criticalRisks.map((r, i) => (
                <div key={i} className="bg-slate-950 p-3 rounded-xl border border-amber-900/40 text-xs space-y-1">
                  <div className="flex justify-between font-mono">
                    <span className="text-amber-300 font-bold">{r.risk}</span>
                    <span className="text-slate-500 text-[10px]">Impact: {r.impact}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    <span className="text-emerald-400 font-mono">Mitigation:</span> {r.mitigation}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
