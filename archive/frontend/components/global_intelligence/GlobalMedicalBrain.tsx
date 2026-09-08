"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GLOBAL_MEDICAL_NODES, GlobalMedicalNode } from "@/lib/stage-x-data";

export default function GlobalMedicalBrain() {
  const [selectedPathway, setSelectedPathway] = useState<"all" | "dis-acs" | "dis-sepsis">("all");
  const [selectedNodeId, setSelectedNodeId] = useState<string>("dis-acs");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeStepFilter, setActiveStepFilter] = useState<number | null>(null);

  const steps = [
    { step: 1, label: "Disease", category: "disease", color: "from-cyan-500 to-blue-600" },
    { step: 2, label: "Symptoms", category: "symptom", color: "from-blue-500 to-indigo-600" },
    { step: 3, label: "Investigations", category: "investigation", color: "from-indigo-500 to-purple-600" },
    { step: 4, label: "Treatment", category: "treatment", color: "from-purple-500 to-emerald-600" },
    { step: 5, label: "Evidence", category: "evidence", color: "from-emerald-500 to-teal-600" },
    { step: 6, label: "Clinical Outcomes", category: "outcome", color: "from-teal-500 to-cyan-400" }
  ];

  const filteredNodes = useMemo(() => {
    return GLOBAL_MEDICAL_NODES.filter((node) => {
      if (selectedPathway === "dis-acs" && !node.id.includes("acs") && !node.id.includes("cp") && !node.id.includes("dyspnea") && !node.id.includes("ecg") && !node.id.includes("trop") && !node.id.includes("pci") && !node.id.includes("antiplatelet") && !node.id.includes("ng185") && !node.id.includes("esc") && !node.id.includes("stemi")) {
        return false;
      }
      if (selectedPathway === "dis-sepsis" && !node.id.includes("sepsis") && !node.id.includes("fever") && !node.id.includes("lactate") && !node.id.includes("ssc")) {
        return false;
      }
      if (activeStepFilter && node.stageStep !== activeStepFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          node.name.toLowerCase().includes(q) ||
          node.sourceProvenance.toLowerCase().includes(q) ||
          node.description.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [selectedPathway, activeStepFilter, searchQuery]);

  const selectedNode = useMemo(() => {
    return GLOBAL_MEDICAL_NODES.find((n) => n.id === selectedNodeId) || GLOBAL_MEDICAL_NODES[0];
  }, [selectedNodeId]);

  const connectedNodes = useMemo(() => {
    if (!selectedNode) return [];
    return GLOBAL_MEDICAL_NODES.filter(
      (n) =>
        selectedNode.connectedNodeIds.includes(n.id) ||
        n.connectedNodeIds.includes(selectedNode.id)
    );
  }, [selectedNode]);

  return (
    <div className="space-y-6">
      {/* Top Banner & Control HUD */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-sm shadow-cyan-400/50" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Knowledge Topology Architecture
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800 text-cyan-300">
                NICE / ESC 2026 Indexed
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              MedicalPlab Global Medical Knowledge Brain
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Transforming fragmented medical literature into an interconnected, computable clinical graph.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1.5 flex items-center gap-2">
              <span className="text-xs text-slate-400">Filter Pathway:</span>
              <button
                onClick={() => setSelectedPathway("all")}
                className={`text-xs px-2.5 py-1 rounded transition-all ${
                  selectedPathway === "all"
                    ? "bg-cyan-500 text-black font-semibold shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                All Pathways
              </button>
              <button
                onClick={() => setSelectedPathway("dis-acs")}
                className={`text-xs px-2.5 py-1 rounded transition-all ${
                  selectedPathway === "dis-acs"
                    ? "bg-cyan-500 text-black font-semibold shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Acute Coronary Syndrome
              </button>
              <button
                onClick={() => setSelectedPathway("dis-sepsis")}
                className={`text-xs px-2.5 py-1 rounded transition-all ${
                  selectedPathway === "dis-sepsis"
                    ? "bg-cyan-500 text-black font-semibold shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Sepsis-6 Resuscitation
              </button>
            </div>

            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search graph nodes..."
                className="bg-slate-950/90 border border-slate-800 focus:border-cyan-500 text-xs text-white rounded-lg px-3 py-2 pl-8 outline-none w-48 placeholder-slate-500 font-mono transition-colors"
              />
              <svg
                className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* 6-Step Pathway Flow Visualization Header */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 pt-4 border-t border-slate-800/80">
          {steps.map((st, idx) => {
            const isActive = activeStepFilter === st.step;
            return (
              <button
                key={st.step}
                onClick={() => setActiveStepFilter(isActive ? null : st.step)}
                className={`text-left p-2.5 rounded-xl border transition-all text-xs relative overflow-hidden group ${
                  isActive
                    ? "bg-cyan-950/40 border-cyan-400 shadow-lg shadow-cyan-950/40"
                    : "bg-slate-950/40 border-slate-800 hover:border-slate-700 text-slate-400"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-cyan-400">STAGE {st.step}</span>
                  {idx < steps.length - 1 && (
                    <span className="hidden lg:inline text-slate-600 group-hover:text-slate-400 text-xs">→</span>
                  )}
                </div>
                <div className="font-semibold text-white mt-1 group-hover:text-cyan-300 transition-colors">
                  {st.label}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 capitalize font-mono">
                  {GLOBAL_MEDICAL_NODES.filter((n) => n.stageStep === st.step).length} Nodes Verified
                </div>
                <div
                  className={`h-0.5 w-full mt-2 rounded bg-gradient-to-r ${st.color} ${
                    isActive ? "opacity-100" : "opacity-40 group-hover:opacity-80"
                  }`}
                />
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Interactive Visualization + Clinical Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Columns: Knowledge Nodes Matrix */}
        <div className="lg:col-span-7 bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                Live Neural Pathway Nodes
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/50 text-cyan-400">
                {filteredNodes.length} active
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-mono">
              Click node to inspect clinical provenance
            </span>
          </div>

          <div className="space-y-3 max-h-[580px] overflow-y-auto pr-2 custom-scrollbar">
            {filteredNodes.map((node) => {
              const isSelected = node.id === selectedNodeId;
              const isRelated = selectedNode?.connectedNodeIds.includes(node.id);

              return (
                <motion.div
                  key={node.id}
                  onClick={() => setSelectedNodeId(node.id)}
                  whileHover={{ scale: 1.01 }}
                  className={`p-4 rounded-xl border cursor-pointer transition-all relative ${
                    isSelected
                      ? "bg-gradient-to-r from-cyan-950/60 via-slate-900 to-slate-900 border-cyan-400 shadow-lg shadow-cyan-950/50"
                      : isRelated
                      ? "bg-slate-900/90 border-cyan-700/60 hover:border-cyan-500"
                      : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 font-semibold uppercase">
                          Step {node.stageStep}: {node.category}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 font-medium">
                          Confidence {node.confidenceScore}%
                        </span>
                        {node.metrics && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                            {node.metrics.label}: {node.metrics.value}
                          </span>
                        )}
                      </div>

                      <h3
                        className={`text-sm md:text-base font-semibold transition-colors ${
                          isSelected ? "text-cyan-300" : "text-white hover:text-cyan-200"
                        }`}
                      >
                        {node.name}
                      </h3>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                        {node.description}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 rounded px-2 py-1 block">
                        {node.sourceProvenance.split("/")[0]}
                      </span>
                    </div>
                  </div>

                  {/* Connected Nodes Badges */}
                  <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] font-mono text-slate-500">Linked to:</span>
                    {node.connectedNodeIds.map((targetId) => {
                      const targetNode = GLOBAL_MEDICAL_NODES.find((t) => t.id === targetId);
                      return (
                        <span
                          key={targetId}
                          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800"
                        >
                          {targetNode ? targetNode.name.split(" ")[0] : targetId}
                        </span>
                      );
                    })}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Right 5 Columns: Clinical Node Provenance & Evidence Inspector */}
        <div className="lg:col-span-5 bg-slate-900/80 backdrop-blur-md border border-cyan-500/30 rounded-2xl p-5 shadow-2xl flex flex-col justify-between">
          <AnimatePresence mode="wait">
            <motion.div
              key={selectedNode.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" />
                  <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
                    Node Provenance Inspector
                  </span>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-700 text-cyan-300">
                  ID: {selectedNode.id}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-mono text-slate-500 uppercase">
                  Stage {selectedNode.stageStep} • {selectedNode.category}
                </span>
                <h3 className="text-lg font-bold text-white mt-0.5 text-cyan-300">
                  {selectedNode.name}
                </h3>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  {selectedNode.description}
                </p>
              </div>

              {/* Source Provenance Banner */}
              <div className="bg-gradient-to-br from-slate-950 to-slate-900 p-3.5 rounded-xl border border-cyan-500/20">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                    Evidence Source Provenance
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-1.5 py-0.5 rounded">
                    Verified Citation
                  </span>
                </div>
                <div className="text-xs font-semibold text-white font-mono">
                  {selectedNode.sourceProvenance}
                </div>
                <div className="text-[11px] text-slate-400 mt-1 italic">
                  &ldquo;{selectedNode.clinicalNotes}&rdquo;
                </div>
              </div>

              {/* Confidence Telemetry Gauge */}
              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Algorithmic Evidence Confidence</span>
                  <span className="text-cyan-400 font-bold">{selectedNode.confidenceScore}%</span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 rounded-full transition-all duration-500"
                    style={{ width: `${selectedNode.confidenceScore}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>Peer-Reviewed Standard</span>
                  <span>System Consensus 99.4%</span>
                </div>
              </div>

              {/* Connected Pathway Graph Links */}
              <div>
                <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
                  Active Graph Dependencies ({connectedNodes.length})
                </div>
                <div className="space-y-1.5">
                  {connectedNodes.map((cn) => (
                    <div
                      key={cn.id}
                      onClick={() => setSelectedNodeId(cn.id)}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-cyan-500 cursor-pointer text-xs transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                          {cn.category}
                        </span>
                        <span className="text-slate-200 font-medium truncate max-w-[200px]">
                          {cn.name}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-cyan-400">Inspect →</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span>Global Knowledge Graph Engine</span>
            <span className="text-cyan-400">MedicalPlab Core v4.2</span>
          </div>
        </div>
      </div>
    </div>
  );
}
