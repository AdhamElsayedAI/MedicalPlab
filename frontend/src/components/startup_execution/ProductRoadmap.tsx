"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { ROADMAP_MILESTONES_DATA, RoadmapMilestone } from "@/lib/startup-data";

export default function ProductRoadmap() {
  const [selectedPhase, setSelectedPhase] = useState<RoadmapMilestone["phase"]>("Phase 1");

  const activeMilestone = ROADMAP_MILESTONES_DATA.find((m) => m.phase === selectedPhase) || ROADMAP_MILESTONES_DATA[0];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Strategic Execution Timeline • MVP to Global Scale
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                18-Month Seed Runway
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Product & Commercial Roadmap
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Disciplined milestones progressing from licensure exam product-market fit to enterprise hospital trust deployments.
            </p>
          </div>
        </div>

        {/* 4-Phase Interactive Timeline Navigation */}
        <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {ROADMAP_MILESTONES_DATA.map((ms) => {
            const isSelected = ms.phase === selectedPhase;
            return (
              <button
                key={ms.phase}
                onClick={() => setSelectedPhase(ms.phase)}
                className={`text-left p-3 rounded-xl border transition-all relative overflow-hidden ${
                  isSelected
                    ? "bg-cyan-950/60 border-cyan-400 shadow-md shadow-cyan-950/50"
                    : "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-400"
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className={isSelected ? "text-cyan-400 font-bold" : "text-slate-500"}>
                    {ms.phase}
                  </span>
                  <span className="text-slate-500">{ms.status}</span>
                </div>
                <div className="text-xs font-bold text-white mt-1 truncate">{ms.title}</div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">{ms.timeline}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Phase Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Phase Scope, Features & Goals */}
        <div className="lg:col-span-7 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase font-semibold">
                {activeMilestone.phase} • {activeMilestone.timeline}
              </span>
              <h3 className="text-xl font-bold text-white mt-0.5">{activeMilestone.title}</h3>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-cyan-300 font-bold">
              {activeMilestone.status}
            </span>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
              Phase Strategic Goal
            </span>
            <p className="text-xs text-slate-200 leading-relaxed font-mono">
              {activeMilestone.goal}
            </p>
          </div>

          <div className="space-y-2.5">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
              Core Capabilities & Features Shipped
            </span>
            {activeMilestone.featuresIncluded.map((feat, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 flex items-center gap-2.5 font-mono"
              >
                <span className="text-cyan-400">✦</span>
                <span>{feat}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right 5 Cols: Success Metrics & Required Resources */}
        <div className="lg:col-span-5 space-y-5">
          {/* Key Deliverable Success Metrics */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider block">
              Phase Validation Metrics
            </span>
            <div className="space-y-2.5">
              {activeMilestone.successMetrics.map((met, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs text-slate-300 block">{met.label}</span>
                    <span className="text-[10px] font-mono text-cyan-400">{met.classification}</span>
                  </div>
                  <span className="text-base font-bold font-mono text-white">{met.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Required Team & Infrastructure Resources */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
              Capital & Talent Requirements
            </span>
            <div className="space-y-2">
              {activeMilestone.requiredResources.map((res, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 flex items-center gap-2"
                >
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>{res}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
