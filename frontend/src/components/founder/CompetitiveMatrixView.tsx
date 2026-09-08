"use client";

import React from "react";
import {
  Check,
  X,
  AlertTriangle,
  ShieldCheck,
  Zap,
  Sparkles,
  Layers,
  Award,
} from "lucide-react";
import { COMPETITIVE_DIMENSIONS } from "@/lib/founder-data";

export const CompetitiveMatrixView: React.FC = () => {
  const renderStatusBadge = (status: "pass" | "partial" | "fail") => {
    switch (status) {
      case "pass":
        return (
          <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 text-xs font-mono font-bold shadow-[0_0_10px_rgba(16,185,129,0.2)]">
            <Check className="w-3.5 h-3.5" />
            <span>EXCELLENT</span>
          </div>
        );
      case "partial":
        return (
          <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-950/80 border border-amber-500/40 text-amber-400 text-xs font-mono font-bold">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>PARTIAL</span>
          </div>
        );
      case "fail":
        return (
          <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-950/80 border border-rose-500/40 text-rose-400 text-xs font-mono font-bold">
            <X className="w-3.5 h-3.5" />
            <span>DEFICIENT</span>
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              COMPETITIVE INTELLIGENCE MATRIX
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              UNASSAILABLE MOATS
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            MedicalPlab vs Generic AI vs Incumbent Question Banks
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Why single-prompt wrappers and legacy static publishers cannot compete with a verified 9-stage clinical AI OS.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-cyan-500/30 text-right">
            <span className="text-[10px] font-mono text-slate-400 block">CORE DIFFERENTIATOR</span>
            <span className="text-xs font-mono font-bold text-cyan-300">0.0% Hallucination Math</span>
          </div>
        </div>
      </div>

      {/* Comparison Matrix Table */}
      <div className="rounded-3xl border border-cyan-500/20 bg-slate-950/80 overflow-hidden shadow-[0_0_30px_rgba(0,242,254,0.08)]">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-xs font-mono uppercase tracking-wider">
                <th className="p-4 sm:p-5 text-slate-400 w-1/4">Evaluation Dimension</th>
                <th className="p-4 sm:p-5 text-slate-400 w-1/4">Generic AI (ChatGPT, Claude)</th>
                <th className="p-4 sm:p-5 text-slate-400 w-1/4">Traditional Q-Banks (PassMed)</th>
                <th className="p-4 sm:p-5 text-cyan-300 bg-cyan-950/40 border-l border-cyan-500/30 w-1/4">
                  <div className="flex items-center gap-1.5 font-black text-white">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span>MedicalPlab Core</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-xs font-sans">
              {COMPETITIVE_DIMENSIONS.map((item, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-slate-900/30 transition-colors group"
                >
                  {/* Dimension Name */}
                  <td className="p-4 sm:p-5 align-top space-y-1">
                    <span className="font-bold text-white text-sm block">
                      {item.dimension}
                    </span>
                    <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                      {item.description}
                    </p>
                  </td>

                  {/* Generic AI */}
                  <td className="p-4 sm:p-5 align-top space-y-2">
                    {renderStatusBadge(item.genericAI.status)}
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      {item.genericAI.details}
                    </p>
                  </td>

                  {/* Traditional Q-Banks */}
                  <td className="p-4 sm:p-5 align-top space-y-2">
                    {renderStatusBadge(item.traditionalBanks.status)}
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      {item.traditionalBanks.details}
                    </p>
                  </td>

                  {/* MedicalPlab */}
                  <td className="p-4 sm:p-5 align-top space-y-2 bg-cyan-950/20 border-l border-cyan-500/30">
                    {renderStatusBadge(item.medicalPlab.status)}
                    <p className="text-[11px] text-cyan-100 font-semibold leading-relaxed">
                      {item.medicalPlab.details}
                    </p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
