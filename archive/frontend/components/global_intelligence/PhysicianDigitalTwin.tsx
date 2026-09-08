"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { PHYSICIAN_PROFILES, PhysicianProfile } from "@/lib/stage-x-data";

export default function PhysicianDigitalTwin() {
  const [selectedPhysicianId, setSelectedPhysicianId] = useState<string>(PHYSICIAN_PROFILES[0].id);

  const profile = PHYSICIAN_PROFILES.find((p) => p.id === selectedPhysicianId) || PHYSICIAN_PROFILES[0];

  return (
    <div className="space-y-6">
      {/* Top Banner & Profile Switcher */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Cognitive Digital Twin & Competency Matrix
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                {profile.lastActive}
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Physician Digital Twin Profile
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Continuous clinical aptitude tracking, Bayesian reasoning telemetry, and lifelong credentialing.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {PHYSICIAN_PROFILES.map((doc) => (
              <button
                key={doc.id}
                onClick={() => setSelectedPhysicianId(doc.id)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  selectedPhysicianId === doc.id
                    ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                    : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                }`}
              >
                {doc.specialty}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Physician Twin Cockpit */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 4 Cols: Clinician Overview & Identity HUD */}
        <div className="lg:col-span-4 space-y-5">
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center gap-3 mb-4 pb-3 border-b border-slate-800">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-lg font-bold text-white shadow-lg shadow-cyan-950/80">
                {profile.name.split(" ")[1]?.charAt(0) || "D"}
              </div>
              <div>
                <h3 className="text-sm md:text-base font-bold text-white leading-tight">
                  {profile.name}
                </h3>
                <span className="text-xs font-mono text-cyan-400">{profile.specialty}</span>
              </div>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Subspecialty:</span>
                <span className="text-slate-300 font-medium">{profile.subspecialty}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Affiliation:</span>
                <span className="text-slate-300 font-medium text-right max-w-[180px] truncate">
                  {profile.hospitalAffiliation}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Cases Analyzed:</span>
                <span className="text-cyan-400 font-bold">{profile.recentCasesCompleted} verified</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Status:</span>
                <span className="text-emerald-400 font-semibold">{profile.certificationStatus}</span>
              </div>
            </div>

            {/* Continuous Learning Progress */}
            <div className="mt-5 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <div className="flex justify-between text-xs font-mono mb-1.5">
                <span className="text-slate-400">Learning Progress</span>
                <span className="text-cyan-400 font-bold">{profile.learningProgress}%</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyan-400 rounded-full"
                  style={{ width: `${profile.learningProgress}%` }}
                />
              </div>
            </div>
          </div>

          {/* AI-Identified Knowledge Gaps & Remediation */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-amber-500/30 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-amber-400 uppercase tracking-wider">
                Precision Knowledge Gaps
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300">
                Targeted Remediation
              </span>
            </div>

            <div className="space-y-2.5">
              {profile.knowledgeGaps.map((gap, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-slate-950/90 border border-amber-500/20 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-300">{gap.topic}</span>
                    <span className="text-[10px] font-mono text-slate-400">
                      Severity: {gap.severity}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300">{gap.recommendation}</p>
                  <div className="text-[10px] font-mono text-cyan-400 pt-1 border-t border-slate-900">
                    Target: {gap.evidenceTarget}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 8 Cols: 4 Main Core Scores & Multi-Axis Radar Competencies */}
        <div className="lg:col-span-8 space-y-5">
          {/* 4 Core Quantitative Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-4 text-center">
              <span className="text-[10px] font-mono text-slate-500 uppercase block">
                Reasoning Score
              </span>
              <span className="text-2xl md:text-3xl font-black font-mono text-cyan-400 mt-1 block">
                {profile.reasoningScore}%
              </span>
              <span className="text-[10px] font-mono text-emerald-400">+4.2% vs Cohort</span>
            </div>

            <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-4 text-center">
              <span className="text-[10px] font-mono text-slate-500 uppercase block">
                Guideline Knowledge
              </span>
              <span className="text-2xl md:text-3xl font-black font-mono text-blue-400 mt-1 block">
                {profile.guidelineAwareness}%
              </span>
              <span className="text-[10px] font-mono text-emerald-400">99th Percentile</span>
            </div>

            <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-4 text-center">
              <span className="text-[10px] font-mono text-slate-500 uppercase block">
                Sim Performance
              </span>
              <span className="text-2xl md:text-3xl font-black font-mono text-teal-400 mt-1 block">
                {profile.simulationPerformance}%
              </span>
              <span className="text-[10px] font-mono text-emerald-400">Zero Critical Omissions</span>
            </div>

            <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-4 text-center">
              <span className="text-[10px] font-mono text-slate-500 uppercase block">
                Learning Velocity
              </span>
              <span className="text-2xl md:text-3xl font-black font-mono text-indigo-400 mt-1 block">
                {profile.learningProgress}%
              </span>
              <span className="text-[10px] font-mono text-emerald-400">Optimal Pace</span>
            </div>
          </div>

          {/* Competency Axis Breakdown Bars */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
                Multi-Axis Clinical Skill Competency Matrix
              </span>
              <span className="text-xs font-mono text-slate-500">
                Clinician (Cyan) vs National Royal College Benchmark (Slate)
              </span>
            </div>

            <div className="space-y-3.5">
              {profile.radarSkills.map((skill) => (
                <div key={skill.axis} className="space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-300">{skill.axis}</span>
                    <span className="text-cyan-400 font-bold">{skill.score}%</span>
                  </div>
                  <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden relative border border-slate-800">
                    {/* Benchmark line */}
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-slate-500 z-10"
                      style={{ left: `${skill.benchmark}%` }}
                      title={`National Benchmark: ${skill.benchmark}%`}
                    />
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${skill.score}%` }}
                      transition={{ duration: 0.6 }}
                      className="h-full bg-gradient-to-r from-cyan-500 to-teal-400 rounded-full"
                    />
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>Baseline Target</span>
                    <span>Benchmark: {skill.benchmark}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
