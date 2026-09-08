"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { KNOWLEDGE_SYNC_EVENTS, KnowledgeSyncEvent } from "@/lib/stage-x-data";

export default function KnowledgeSynchronization() {
  const [events, setEvents] = useState<KnowledgeSyncEvent[]>(KNOWLEDGE_SYNC_EVENTS);
  const [isSyncing, setIsSyncing] = useState(false);

  const pipelineStages = [
    { step: 1, name: "New Medical Evidence", desc: "Live ingestion of PubMed, Lancet, NEJM, NICE releases", color: "from-cyan-500 to-blue-500" },
    { step: 2, name: "Validation Engine", desc: "Cryptographic consensus & conflicting claim reconciliation", color: "from-blue-500 to-indigo-500" },
    { step: 3, name: "Knowledge Graph Update", desc: "Automated triplet node embedding and ontology links", color: "from-indigo-500 to-purple-500" },
    { step: 4, name: "Question Bank Update", desc: "UKMLA / PLAB assessment recalibration & distractors", color: "from-purple-500 to-teal-500" },
    { step: 5, name: "Tutor Update", desc: "Socratic pedagogical prompt & knowledge frontier update", color: "from-teal-500 to-emerald-500" },
    { step: 6, name: "Simulation Update", desc: "Physiological patient twin model weights refreshed", color: "from-emerald-500 to-cyan-400" }
  ];

  const handleSimulateSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      const newEv: KnowledgeSyncEvent = {
        id: `sync-${Date.now()}`,
        timestamp: "Just now",
        stage: "New Medical Evidence",
        title: "Lancet: Novel Reperfusion Timeframe Thresholds in Acute Stroke",
        source: "The Lancet Neurology (2026.09.08)",
        status: "Synchronized",
        deltaItems: 28,
        trustScore: 99.8
      };
      setEvents((prev) => [newEv, ...prev]);
      setIsSyncing(false);
    }, 800);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Autonomous Continuous Knowledge Synchronization
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                Zero Human Latency Pipeline
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Knowledge Synchronization & Self-Healing Pipeline
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Medical breakthroughs automatically propagate from scientific publication to question bank, AI tutor, and hospital simulations.
            </p>
          </div>

          <button
            onClick={handleSimulateSync}
            disabled={isSyncing}
            className="text-xs px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold font-mono transition-all shadow-lg shadow-cyan-500/20"
          >
            {isSyncing ? "Triggering Ingestion..." : "Simulate Live Evidence Sync ⚡"}
          </button>
        </div>

        {/* 6-Phase Pipeline Visualization */}
        <div className="mt-6 pt-5 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {pipelineStages.map((stage, idx) => (
            <div
              key={stage.step}
              className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3 relative overflow-hidden"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-cyan-400">
                  STAGE 0{stage.step}
                </span>
                {idx < 5 && <span className="text-slate-600 text-xs hidden lg:inline">→</span>}
              </div>
              <div className="text-xs font-bold text-white mt-1 leading-snug">{stage.name}</div>
              <div className="text-[10px] text-slate-400 mt-1 leading-tight">{stage.desc}</div>
              <div className={`h-0.5 w-full bg-gradient-to-r ${stage.color} rounded mt-2.5 opacity-80`} />
            </div>
          ))}
        </div>
      </div>

      {/* Real-time Ledger of Synced Events */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
              Autonomous Synchronization Ledger ({events.length} events logged)
            </span>
          </div>
          <span className="text-xs font-mono text-emerald-400">
            All Downstream Engines Synchronous
          </span>
        </div>

        <div className="space-y-3 max-h-[480px] overflow-y-auto pr-2 custom-scrollbar">
          {events.map((ev) => (
            <motion.div
              key={ev.id}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300">
                    {ev.stage}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    Trust Score: {ev.trustScore}%
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">{ev.timestamp}</span>
                </div>
                <h4 className="text-sm font-semibold text-white">{ev.title}</h4>
                <p className="text-xs text-slate-400 font-mono">Source: {ev.source}</p>
              </div>

              <div className="text-right shrink-0">
                <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 rounded block">
                  +{ev.deltaItems} Nodes {ev.status}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
