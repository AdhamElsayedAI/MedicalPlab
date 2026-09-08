"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { API_PRODUCTS, APIProduct } from "@/lib/stage-x-data";

export default function MedicalAPIPlatform() {
  const [selectedEndpointId, setSelectedEndpointId] = useState<string>(API_PRODUCTS[0].id);
  const [copied, setCopied] = useState(false);

  const activeApi = API_PRODUCTS.find((a) => a.id === selectedEndpointId) || API_PRODUCTS[0];

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
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
                Developer Ecosystem & Public API Infrastructure
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                REST • WebSocket • gRPC
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Global Medical API Platform
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Powering electronic health records, ambient triage co-pilots, and medical education networks.
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs text-slate-400">
            <span className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800">
              Uptime: <span className="text-emerald-400 font-bold">99.99%</span>
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800">
              Avg Latency: <span className="text-cyan-400 font-bold">82ms</span>
            </span>
          </div>
        </div>

        {/* Endpoint Selector Tabs */}
        <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {API_PRODUCTS.map((api) => {
            const isSelected = selectedEndpointId === api.id;
            return (
              <button
                key={api.id}
                onClick={() => setSelectedEndpointId(api.id)}
                className={`text-left p-3 rounded-xl border transition-all ${
                  isSelected
                    ? "bg-cyan-950/60 border-cyan-400 shadow-md shadow-cyan-950/50"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-400"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-cyan-400">{api.method}</span>
                  <span className="text-[10px] font-mono text-slate-500">{api.latencyMs}ms</span>
                </div>
                <div className="text-xs font-bold text-white mt-1 truncate">{api.endpoint}</div>
                <div className="text-[10px] text-slate-400 mt-0.5 truncate">{api.name}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main API Exploration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 6 Cols: Endpoint Documentation & Enterprise Use Cases */}
        <div className="lg:col-span-6 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-cyan-400">{activeApi.method}</span>
              <span className="text-sm font-bold font-mono text-white">{activeApi.endpoint}</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300">
              {activeApi.version}
            </span>
          </div>

          <div>
            <h3 className="text-base font-bold text-white">{activeApi.name}</h3>
            <p className="text-xs text-slate-300 mt-1.5 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800">
              {activeApi.description}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs font-mono">
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-center">
              <span className="text-slate-500 text-[10px] uppercase block">Global Volume</span>
              <span className="text-cyan-400 font-bold">{activeApi.monthlyCalls}</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-center">
              <span className="text-slate-500 text-[10px] uppercase block">Latency</span>
              <span className="text-emerald-400 font-bold">{activeApi.latencyMs} ms</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-center">
              <span className="text-slate-500 text-[10px] uppercase block">SLA</span>
              <span className="text-white font-bold">{activeApi.uptimePercent}%</span>
            </div>
          </div>

          {/* Enterprise Use Cases */}
          <div className="space-y-2 pt-2">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
              Enterprise Usage Scenarios
            </span>
            {activeApi.enterpriseUseCases.map((uc, i) => (
              <div
                key={i}
                className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300 flex items-center gap-2 font-mono"
              >
                <span className="text-cyan-400">⚡</span>
                <span>{uc}</span>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-slate-800 text-[10px] font-mono text-slate-500">
            Authentication: {activeApi.authentication}
          </div>
        </div>

        {/* Right 6 Cols: cURL Snippet & Response Schema */}
        <div className="lg:col-span-6 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
              cURL Request Sample
            </span>
            <button
              onClick={() => handleCopy(activeApi.curlSnippet)}
              className="text-[10px] font-mono px-2 py-1 rounded bg-slate-800 text-slate-300 hover:text-white transition-colors"
            >
              {copied ? "Copied ✓" : "Copy cURL"}
            </button>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-cyan-300 overflow-x-auto">
            <pre className="whitespace-pre">{activeApi.curlSnippet}</pre>
          </div>

          <div className="pt-2">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block mb-2">
              Sample 200 OK Response Payload
            </span>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 max-h-56 overflow-y-auto">
              <pre className="whitespace-pre">{activeApi.responseSchemaSample}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
