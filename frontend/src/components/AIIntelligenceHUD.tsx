"use client";

import React from "react";
import { ShieldCheck, BookOpen, CheckCircle, User } from "lucide-react";

interface AIIntelligenceHUDProps {
  evidenceConfidence?: number;
  sourceCorpus?: string;
  safetyStatus?: "VERIFIED" | "TRIGGERED" | "STANDBY";
  personalizationLevel?: string;
  activeTopic?: string;
}

export const AIIntelligenceHUD: React.FC<AIIntelligenceHUDProps> = ({
  evidenceConfidence = 98.4,
  sourceCorpus = "NICE NG185 & BNF 85",
  safetyStatus = "VERIFIED",
  personalizationLevel = "Competent",
}) => {
  return (
    <div
      className="w-full px-4 py-2"
      style={{
        background: 'rgba(17,24,39,0.85)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(12px)',
      }}
    >
      <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-x-6 gap-y-1.5 text-[12px]">

        {/* Evidence */}
        <div className="flex items-center gap-1.5 text-slate-400">
          <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#22c55e' }} />
          <span>Evidence grounded</span>
          <span className="font-semibold" style={{ color: '#86efac' }}>{evidenceConfidence}%</span>
        </div>

        {/* Separator */}
        <div className="w-px h-3 bg-slate-700 hidden sm:block" />

        {/* Source */}
        <div className="flex items-center gap-1.5 text-slate-400">
          <BookOpen className="w-3.5 h-3.5 flex-shrink-0 text-slate-500" />
          <span>{sourceCorpus}</span>
        </div>

        {/* Separator */}
        <div className="w-px h-3 bg-slate-700 hidden md:block" />

        {/* Safety */}
        <div className="flex items-center gap-1.5">
          <ShieldCheck
            className="w-3.5 h-3.5 flex-shrink-0"
            style={{ color: safetyStatus === "VERIFIED" ? '#22c55e' : '#ef4444' }}
          />
          <span
            className="font-medium"
            style={{ color: safetyStatus === "VERIFIED" ? '#86efac' : '#fca5a5' }}
          >
            {safetyStatus === "VERIFIED" ? "Safety verified" : "Contraindication detected"}
          </span>
        </div>

        {/* Separator */}
        <div className="w-px h-3 bg-slate-700 hidden md:block" />

        {/* Personalization */}
        <div className="flex items-center gap-1.5 text-slate-400">
          <User className="w-3.5 h-3.5 flex-shrink-0 text-slate-500" />
          <span>{personalizationLevel}</span>
        </div>

      </div>
    </div>
  );
};
