"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RESEARCH_INSIGHTS, ResearchInsight } from "@/lib/stage-x-data";

export default function ResearchIntelligence() {
  const [selectedInsightId, setSelectedInsightId] = useState<string>(RESEARCH_INSIGHTS[0].id);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [customQuestion, setCustomQuestion] = useState("");

  const activeInsight = RESEARCH_INSIGHTS.find((r) => r.id === selectedInsightId) || RESEARCH_INSIGHTS[0];

  const handleRunSynthesis = () => {
    setIsSynthesizing(true);
    setTimeout(() => {
      setIsSynthesizing(false);
    }, 900);
  };

  const pipelineStages = [
    { num: 1, label: "Research Question", subtitle: "Clinical Dilemma Formulation", color: "text-cyan-400" },
    { num: 2, label: "Literature Discovery", subtitle: `${activeInsight.literatureDiscoveryCount} Trials Indexed`, color: "text-blue-400" },
    { num: 3, label: "Evidence Ranking", subtitle: `${activeInsight.evidenceRanking.grade} (${activeInsight.evidenceRanking.score}/100)`, color: "text-indigo-400" },
    { num: 4, label: "Knowledge Synthesis", subtitle: "Bayesian Meta-Regressed", color: "text-teal-400" },
    { num: 5, label: "Research Opportunity", subtitle: `Impact Potential ${activeInsight.impactScore}/100`, color: "text-emerald-400" }
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Autonomous Biomedical Discovery
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300">
                PubMed • Cochrane • NEJM Mesh Connected
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Research Intelligence Pipeline
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Accelerating translational medical science from raw hypotheses to systematic knowledge synthesis.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedInsightId(RESEARCH_INSIGHTS[0].id)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                selectedInsightId === RESEARCH_INSIGHTS[0].id
                  ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              HFpEF SGLT2i Study
            </button>
            <button
              onClick={() => setSelectedInsightId(RESEARCH_INSIGHTS[1].id)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                selectedInsightId === RESEARCH_INSIGHTS[1].id
                  ? "bg-cyan-500 text-black font-semibold border-cyan-400"
                  : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              Sepsis Transcriptomics
            </button>
          </div>
        </div>

        {/* 5-Step Pipeline Flow Banner */}
        <div className="mt-5 pt-4 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {pipelineStages.map((st, idx) => (
            <div
              key={st.num}
              className="bg-slate-950/60 border border-slate-800/90 rounded-xl p-3 relative overflow-hidden"
            >
              <div className="flex items-center justify-between">
                <span className={`text-[10px] font-mono font-semibold ${st.color}`}>
                  PHASE 0{st.num}
                </span>
                {idx < 4 && <span className="text-slate-600 text-xs hidden lg:inline">→</span>}
              </div>
              <div className="text-xs font-bold text-white mt-1">{st.label}</div>
              <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">{st.subtitle}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Research Cockpit */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 8 Cols: Synthesis & Hypotheses Engine */}
        <div className="lg:col-span-8 space-y-5">
          {/* Research Question Box */}
          <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                Step 1: Primary Research Question Formulation
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                PICO Framework Validated
              </span>
            </div>

            <h3 className="text-base md:text-lg font-bold text-white leading-relaxed">
              &ldquo;{activeInsight.researchQuestion}&rdquo;
            </h3>

            <div className="mt-3 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
              <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                Working Biological Hypothesis
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                {activeInsight.hypothesis}
              </p>
            </div>

            {/* Mesh Terms */}
            <div className="mt-3 flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] font-mono text-slate-500">MeSH Indexing:</span>
              {activeInsight.meshTerms.map((m) => (
                <span
                  key={m}
                  className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-800/40 text-cyan-300"
                >
                  {m}
                </span>
              ))}
            </div>
          </div>

          {/* Step 4: Knowledge Synthesis */}
          <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-teal-400" />
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">
                  Step 4: Meta-Synthesized Clinical Evidence
                </span>
              </div>
              <button
                onClick={handleRunSynthesis}
                disabled={isSynthesizing}
                className="text-[11px] font-mono px-3 py-1 rounded bg-teal-950/60 border border-teal-700/50 text-teal-300 hover:bg-teal-900/60 transition-colors"
              >
                {isSynthesizing ? "Regressing Meta-Analysis..." : "Re-run Live Synthesis ↻"}
              </button>
            </div>

            <div className="bg-slate-950/90 p-4 rounded-xl border border-teal-500/20 text-xs text-slate-200 leading-relaxed">
              {activeInsight.synthesisSummary}
            </div>

            {/* Top Journals Indexed */}
            <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between flex-wrap gap-2">
              <span className="text-[10px] font-mono text-slate-500">
                Synthesized Sources ({activeInsight.literatureDiscoveryCount} papers):
              </span>
              <div className="flex gap-2 flex-wrap">
                {activeInsight.topJournals.map((j) => (
                  <span
                    key={j}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300"
                  >
                    {j}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Step 5: Research Opportunity & Study Design */}
          <div className="bg-gradient-to-br from-slate-900/90 to-emerald-950/30 backdrop-blur-md border border-emerald-500/30 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider">
                Step 5: Translational Research Opportunity
              </span>
              <span className="text-xs font-mono font-bold text-emerald-400">
                Impact Score: {activeInsight.impactScore}/100
              </span>
            </div>

            <h4 className="text-sm md:text-base font-bold text-white mb-2">
              {activeInsight.researchOpportunity}
            </h4>

            <div className="bg-slate-950/80 p-3.5 rounded-xl border border-emerald-900/40 mt-3">
              <span className="text-[10px] font-mono text-emerald-400 uppercase block mb-1">
                AI-Prescribed Trial Design & Methodology
              </span>
              <p className="text-xs text-slate-300 font-mono leading-relaxed">
                {activeInsight.aiRecommendedStudyDesign}
              </p>
            </div>
          </div>
        </div>

        {/* Right 4 Cols: Evidence Quality, Knowledge Gaps, Impact Meters */}
        <div className="lg:col-span-4 space-y-5">
          {/* Evidence Quality Ranking Meter */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
            <span className="text-[10px] font-mono text-indigo-400 uppercase tracking-wider block mb-3">
              Step 3: GRADE Evidence Quality
            </span>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
              <div className="text-3xl font-black text-cyan-400 font-mono">
                {activeInsight.evidenceRanking.grade}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                GRADE Synthesis Score: {activeInsight.evidenceRanking.score}/100
              </div>

              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-800 text-xs font-mono">
                <div className="bg-slate-900 p-2 rounded-lg">
                  <div className="text-emerald-400 font-bold">{activeInsight.evidenceRanking.metaAnalysesCount}</div>
                  <div className="text-[10px] text-slate-400">Meta-Analyses</div>
                </div>
                <div className="bg-slate-900 p-2 rounded-lg">
                  <div className="text-cyan-400 font-bold">{activeInsight.evidenceRanking.rctCount}</div>
                  <div className="text-[10px] text-slate-400">Published RCTs</div>
                </div>
              </div>
            </div>
          </div>

          {/* Critical Knowledge Gaps Identified */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
            <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider block mb-3">
              Unresolved Knowledge Gaps
            </span>

            <div className="space-y-2.5">
              {activeInsight.knowledgeGaps.map((gap, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-slate-950/80 border border-amber-500/20 text-xs text-slate-300 flex items-start gap-2"
                >
                  <span className="text-amber-400 font-mono font-bold mt-0.5">!</span>
                  <span>{gap}</span>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              Auto-suggested grant proposal drafts available via API.
            </div>
          </div>

          {/* Interactive Query Box */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4 shadow-xl">
            <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider block mb-2">
              Explore New Medical Hypothesis
            </span>
            <input
              type="text"
              value={customQuestion}
              onChange={(e) => setCustomQuestion(e.target.value)}
              placeholder="e.g., GLP-1 agonists in Parkinson's disease..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 outline-none font-mono"
            />
            <button
              onClick={() => {
                if (customQuestion.trim()) {
                  alert(`Hypothesis query "${customQuestion}" initiated on global PubMed cluster.`);
                  setCustomQuestion("");
                }
              }}
              className="w-full mt-2 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-xs font-mono transition-colors"
            >
              Analyze Biomarker Literature
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
