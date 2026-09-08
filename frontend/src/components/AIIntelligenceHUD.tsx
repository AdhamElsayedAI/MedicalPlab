"use client";

import React from "react";
import { ShieldAlert, CheckCircle2, BookOpen, UserCheck, Flame } from "lucide-react";

interface AIIntelligenceHUDProps {
  evidenceConfidence?: number; // e.g. 98.6
  sourceCorpus?: string; // e.g. "NICE NG185 / BNF 85"
  safetyStatus?: "VERIFIED" | "TRIGGERED" | "STANDBY";
  personalizationLevel?: string; // e.g. "ADAPTIVE (COMPETENT)"
  activeTopic?: string;
}

export const AIIntelligenceHUD: React.FC<AIIntelligenceHUDProps> = ({
  evidenceConfidence = 98.4,
  sourceCorpus = "NICE NG185 & BNF 85 Guidelines",
  safetyStatus = "VERIFIED",
  personalizationLevel = "ADAPTIVE (COMPETENT)",
  activeTopic = "Acute Coronary Syndromes",
}) => {
  return (
    <div className="w-full bg-slate-950/70 border-b border-cyan-500/15 backdrop-blur-md px-4 py-2">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        {/* Metric 1: Evidence Confidence */}
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-5 h-5 rounded bg-cyan-950 text-cyan-400 border border-cyan-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
          </div>
          <span className="text-slate-400">EVIDENCE CONFIDENCE:</span>
          <span className="text-cyan-300 font-bold tracking-wider">{evidenceConfidence}% GROUNDED</span>
          <span className="hidden sm:inline-block w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
        </div>

        {/* Metric 2: Source Verification */}
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-5 h-5 rounded bg-blue-950 text-blue-400 border border-blue-500/30">
            <BookOpen className="w-3.5 h-3.5" />
          </div>
          <span className="text-slate-400">VERIFIED CORPUS:</span>
          <span className="text-blue-300 font-semibold">{sourceCorpus}</span>
        </div>

        {/* Metric 3: Safety Guard */}
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center justify-center w-5 h-5 rounded border ${
              safetyStatus === "VERIFIED"
                ? "bg-emerald-950 text-emerald-400 border-emerald-500/30"
                : "bg-rose-950 text-rose-400 border-rose-500/30"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
          </div>
          <span className="text-slate-400">SAFETY VALIDATION:</span>
          <span
            className={`font-bold ${
              safetyStatus === "VERIFIED" ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {safetyStatus === "VERIFIED" ? "STAGE-D ACTIVE (ZERO HALLUCINATION)" : "CONTRAINDICATION CAUGHT"}
          </span>
        </div>

        {/* Metric 4: Adaptive Personalization */}
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-5 h-5 rounded bg-purple-950 text-purple-400 border border-purple-500/30">
            <UserCheck className="w-3.5 h-3.5" />
          </div>
          <span className="text-slate-400">PERSONALIZATION:</span>
          <span className="text-purple-300 font-bold">{personalizationLevel}</span>
        </div>
      </div>
    </div>
  );
};
