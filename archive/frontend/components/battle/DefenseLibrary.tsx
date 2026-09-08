"use client";

import React, { useState } from "react";
import {
  BookOpen,
  Search,
  Cpu,
  ShieldCheck,
  TrendingUp,
  Code2,
  Sparkles,
  Zap,
  CheckCircle2,
} from "lucide-react";
import { DEFENSE_LIBRARY_TOPICS } from "@/lib/stage-l-data";
import { DefenseTopic } from "@/lib/types";

export const DefenseLibrary: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<
    "All" | "AI Technology" | "Clinical Safety" | "Business & Scale"
  >("All");
  const [search, setSearch] = useState("");
  const [activeTopicId, setActiveTopicId] = useState(DEFENSE_LIBRARY_TOPICS[0].id);

  const filtered = DEFENSE_LIBRARY_TOPICS.filter((t) => {
    const matchCat = activeCategory === "All" || t.category === activeCategory;
    const matchSearch =
      search.trim() === "" ||
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.summary.toLowerCase().includes(search.toLowerCase()) ||
      t.counterPunch.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  const activeTopic =
    DEFENSE_LIBRARY_TOPICS.find((t) => t.id === activeTopicId) ||
    DEFENSE_LIBRARY_TOPICS[0];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
              DEFENSE KNOWLEDGE LIBRARY
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              6 CORE STRATEGIC DOMAINS
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Technical & Business Defense Reference Manual
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Deep reference covering hybrid RAG, mathematical claim verification, real-time safety interceptors, unit economics, and competitive moats.
          </p>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 self-start md:self-center">
          {(["All", "AI Technology", "Clinical Safety", "Business & Scale"] as const).map(
            (cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold whitespace-nowrap transition-all ${
                  activeCategory === cat
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,242,254,0.25)]"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {cat}
              </button>
            )
          )}
        </div>
      </div>

      {/* Main Grid: Topic Nav + Deep Dive */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left 4 Cols: Topic List */}
        <div className="lg:col-span-4 p-4 rounded-3xl bg-slate-950/90 border border-slate-800 space-y-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase font-bold tracking-wider px-2 block mb-1">
            Reference Topics (6)
          </span>

          {filtered.map((topic) => {
            const isActive = topic.id === activeTopicId;
            return (
              <button
                key={topic.id}
                onClick={() => setActiveTopicId(topic.id)}
                className={`w-full text-left p-3.5 rounded-2xl transition-all space-y-1 ${
                  isActive
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-400/50 shadow-[0_0_15px_rgba(0,242,254,0.2)]"
                    : "bg-slate-900/40 border border-transparent text-slate-400 hover:text-white hover:bg-slate-900"
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="uppercase font-bold">{topic.category}</span>
                  {isActive && <span className="text-cyan-400 font-bold">ACTIVE</span>}
                </div>
                <h4 className="text-xs sm:text-sm font-bold text-white">
                  {topic.title}
                </h4>
              </button>
            );
          })}
        </div>

        {/* Right 8 Cols: Topic Deep Dive Card */}
        <div className="lg:col-span-8 p-6 sm:p-8 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg space-y-6">
          <div className="border-b border-slate-800 pb-4 space-y-1">
            <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-widest block">
              {activeTopic.category}
            </span>
            <h3 className="text-2xl font-black text-white">{activeTopic.title}</h3>
            <p className="text-xs sm:text-sm text-slate-300 font-sans mt-1">
              {activeTopic.summary}
            </p>
          </div>

          {/* Architectural Details */}
          <div className="space-y-3">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold tracking-wider block">
              Key Engineering Proof Points
            </span>
            <div className="space-y-2">
              {activeTopic.architecturalDetails.map((detail, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-200 font-sans"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{detail}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Formula or Code Contract */}
          <div className="space-y-2">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold tracking-wider block">
              Contract & Mathematical Logic
            </span>
            <div className="p-3.5 rounded-2xl bg-black/70 border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto">
              <code>{activeTopic.keyQuotesOrFormulas}</code>
            </div>
          </div>

          {/* Winning Counter-Punch */}
          <div className="p-4 rounded-2xl bg-cyan-950/25 border border-cyan-500/40 space-y-1">
            <span className="text-xs font-mono text-cyan-300 font-bold uppercase block flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-cyan-400" />
              Winning Founder Counter-Punch
            </span>
            <p className="text-xs sm:text-sm text-slate-100 font-sans italic leading-relaxed">
              &ldquo;{activeTopic.counterPunch}&rdquo;
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
