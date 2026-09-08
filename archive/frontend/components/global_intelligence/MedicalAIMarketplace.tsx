"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MEDICAL_MODULES, MedicalModule } from "@/lib/stage-x-data";

export default function MedicalAIMarketplace() {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedProvider, setSelectedProvider] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeModule, setActiveModule] = useState<MedicalModule | null>(null);
  const [installedIds, setInstalledIds] = useState<string[]>(["mod-neuro-agent"]);

  const categories = ["all", "AI Agents", "Simulation Modules", "Medical Courses", "Clinical Packages"];
  const providers = ["all", "Universities", "Hospitals", "Researchers", "Medical educators"];
  const statuses = ["all", "Verified", "Prototype", "Future Vision"];

  const filteredModules = useMemo(() => {
    return MEDICAL_MODULES.filter((mod) => {
      if (selectedCategory !== "all" && mod.category !== selectedCategory) return false;
      if (selectedProvider !== "all" && mod.providerType !== selectedProvider) return false;
      if (selectedStatus !== "all" && mod.status !== selectedStatus) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          mod.title.toLowerCase().includes(q) ||
          mod.providerName.toLowerCase().includes(q) ||
          mod.description.toLowerCase().includes(q) ||
          mod.tags.some((t) => t.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [selectedCategory, selectedProvider, selectedStatus, searchQuery]);

  const toggleInstall = (id: string) => {
    setInstalledIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const getStatusBadge = (status: MedicalModule["status"]) => {
    switch (status) {
      case "Verified":
        return (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            [Verified]
          </span>
        );
      case "Prototype":
        return (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/70 border border-amber-500/40 text-amber-300 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            [Prototype]
          </span>
        );
      case "Future Vision":
        return (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/70 border border-purple-500/40 text-purple-300 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
            [Future Vision]
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Global Clinical Ecosystem Registry
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Peer-Reviewed Deployments
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Global AI Marketplace
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Decentralized ecosystem connecting universities, research hospitals, and clinical developers.
            </p>
          </div>

          {/* Quick Search */}
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search agents, courses, clinical packages..."
              className="bg-slate-950/90 border border-slate-800 focus:border-cyan-500 text-xs text-white rounded-lg px-3 py-2 pl-8 outline-none w-72 placeholder-slate-500 font-mono transition-colors"
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

        {/* Filter Toolbar */}
        <div className="mt-5 pt-4 border-t border-slate-800 flex flex-wrap gap-4 items-center justify-between">
          {/* Category Tabs */}
          <div className="flex flex-wrap gap-1.5">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  selectedCategory === cat
                    ? "bg-cyan-500 text-black font-semibold border-cyan-400 shadow-md shadow-cyan-500/20"
                    : "bg-slate-950/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white"
                }`}
              >
                {cat === "all" ? "All Ecosystem Items" : cat}
              </button>
            ))}
          </div>

          {/* Provider and Status Dropdown/Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1 text-xs bg-slate-950/80 border border-slate-800 rounded-lg p-1">
              <span className="text-slate-500 text-[10px] uppercase font-mono px-2">Provider:</span>
              {providers.map((p) => (
                <button
                  key={p}
                  onClick={() => setSelectedProvider(p)}
                  className={`text-[11px] px-2 py-1 rounded transition-colors ${
                    selectedProvider === p
                      ? "bg-slate-800 text-cyan-300 font-medium"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {p === "all" ? "All" : p}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1 text-xs bg-slate-950/80 border border-slate-800 rounded-lg p-1">
              <span className="text-slate-500 text-[10px] uppercase font-mono px-2">Status:</span>
              {statuses.map((s) => (
                <button
                  key={s}
                  onClick={() => setSelectedStatus(s)}
                  className={`text-[11px] px-2 py-1 rounded transition-colors ${
                    selectedStatus === s
                      ? "bg-slate-800 text-cyan-300 font-medium"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {s === "all" ? "All" : s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Marketplace Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredModules.map((item) => {
          const isInstalled = installedIds.includes(item.id);

          return (
            <motion.div
              key={item.id}
              whileHover={{ y: -3 }}
              className="bg-slate-900/60 backdrop-blur-md border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 shadow-xl flex flex-col justify-between transition-all group"
            >
              <div>
                {/* Header: Provider Type & Status Badge */}
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase">
                    {item.providerType}
                  </span>
                  {getStatusBadge(item.status)}
                </div>

                <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors leading-snug">
                  {item.title}
                </h3>

                <p className="text-xs text-cyan-400 font-mono mt-1">
                  By {item.providerName}
                </p>

                <p className="text-xs text-slate-400 mt-2.5 line-clamp-3 leading-relaxed">
                  {item.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {item.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Footer: Metrics, Price, and Action */}
              <div className="mt-5 pt-4 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs font-mono mb-3">
                  <div className="flex items-center gap-1 text-amber-300">
                    <span>★</span>
                    <span className="text-slate-200">{item.rating.toFixed(2)}</span>
                  </div>
                  <span className="text-slate-400">{item.installsOrUsers}</span>
                  <span className="text-cyan-400 font-semibold">{item.pricing}</span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setActiveModule(item)}
                    className="flex-1 text-xs py-2 px-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-600 text-slate-300 hover:text-white font-medium transition-colors"
                  >
                    Inspect Audit
                  </button>
                  <button
                    onClick={() => toggleInstall(item.id)}
                    className={`flex-1 text-xs py-2 px-3 rounded-xl font-semibold transition-all shadow-md ${
                      isInstalled
                        ? "bg-emerald-950/80 border border-emerald-500/50 text-emerald-300"
                        : "bg-gradient-to-r from-cyan-500 to-blue-600 text-black hover:from-cyan-400 hover:to-blue-500"
                    }`}
                  >
                    {isInstalled ? "Integrated ✓" : "Deploy / Test"}
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Module Inspection Modal */}
      <AnimatePresence>
        {activeModule && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-cyan-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative"
            >
              <button
                onClick={() => setActiveModule(null)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white text-lg font-mono"
              >
                ✕
              </button>

              <div className="flex items-center gap-2 mb-2">
                {getStatusBadge(activeModule.status)}
                <span className="text-xs font-mono text-cyan-400 uppercase">
                  {activeModule.category}
                </span>
              </div>

              <h3 className="text-lg font-bold text-white">{activeModule.title}</h3>
              <p className="text-xs font-mono text-slate-400 mt-0.5">
                Author: {activeModule.providerName} ({activeModule.providerType})
              </p>

              <div className="mt-4 space-y-3 text-xs">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                    Clinical Architecture & Scope
                  </span>
                  <p className="text-slate-300 leading-relaxed">{activeModule.description}</p>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5">
                  <div className="flex justify-between font-mono">
                    <span className="text-slate-400">Clinical Verification Audit:</span>
                    <span className="text-emerald-400 font-semibold">{activeModule.verificationAudit}</span>
                  </div>
                  <div className="flex justify-between font-mono">
                    <span className="text-slate-400">Regulatory Compliance:</span>
                    <span className="text-cyan-400">{activeModule.complianceLevel}</span>
                  </div>
                  <div className="flex justify-between font-mono">
                    <span className="text-slate-400">Active Hospital Deployments:</span>
                    <span className="text-white">{activeModule.installsOrUsers}</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setActiveModule(null)}
                  className="text-xs px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    toggleInstall(activeModule.id);
                    setActiveModule(null);
                  }}
                  className="text-xs px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-semibold shadow-md shadow-cyan-500/20"
                >
                  {installedIds.includes(activeModule.id) ? "Revoke Integration" : "Deploy To Enterprise Instance"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
