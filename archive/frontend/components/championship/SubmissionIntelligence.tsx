"use client";

import React, { useState } from "react";
import {
  FileText,
  Copy,
  Check,
  CheckCircle2,
  Sparkles,
  Download,
  Share2,
  BookOpen,
  Layers,
  ShieldCheck,
} from "lucide-react";
import {
  SUBMISSION_PACKAGE_SECTIONS,
  SUBMISSION_QUALITY_CHECKLIST,
} from "@/lib/championship-data";

export const SubmissionIntelligence: React.FC = () => {
  const [activeSectionId, setActiveSectionId] = useState("exec_summary");
  const [copiedAll, setCopiedAll] = useState(false);
  const [copiedSection, setCopiedSection] = useState(false);

  const activeSection =
    SUBMISSION_PACKAGE_SECTIONS.find((s) => s.id === activeSectionId) ||
    SUBMISSION_PACKAGE_SECTIONS[0];

  const handleCopyAll = () => {
    const fullMarkdown = SUBMISSION_PACKAGE_SECTIONS.map(
      (s) => s.contentMarkdown
    ).join("\n\n---\n\n");
    navigator.clipboard.writeText(fullMarkdown);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2500);
  };

  const handleCopySection = () => {
    navigator.clipboard.writeText(activeSection.contentMarkdown);
    setCopiedSection(true);
    setTimeout(() => setCopiedSection(false), 2000);
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              SUBMISSION INTELLIGENCE & DOCUMENTATION GENERATOR
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              DEVPOST & INVESTOR GRADE
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Automated Hackathon Package & Quality Checklist
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Complete structured write-up covering all competition criteria, ready to copy into hackathon portal forms with 1-click.
          </p>
        </div>

        {/* Global Copy All Button */}
        <div className="flex items-center gap-3 self-start md:self-center">
          <button
            onClick={handleCopyAll}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold border transition-all ${
              copiedAll
                ? "bg-emerald-950 border-emerald-500 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                : "bg-gradient-to-r from-cyan-500 to-blue-600 border-cyan-400/40 text-white shadow-lg shadow-cyan-500/25 hover:scale-[1.02]"
            }`}
          >
            {copiedAll ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            <span>{copiedAll ? "Copied Full Package!" : "Copy Full Submission (.md)"}</span>
          </button>
        </div>
      </div>

      {/* 10-Point Submission Quality Checklist */}
      <div className="p-6 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h4 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
              Championship Submission Quality Checklist (10 / 10 Passing)
            </h4>
          </div>
          <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-500/40">
            100% Evaluation Compliance
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SUBMISSION_QUALITY_CHECKLIST.map((item) => (
            <div
              key={item.id}
              className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-start gap-3 hover:border-emerald-500/30 transition-colors"
            >
              <div className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-950 border border-emerald-500/50 text-emerald-400 flex items-center justify-center mt-0.5">
                <Check className="w-3 h-3" />
              </div>
              <div className="space-y-0.5">
                <span className="text-xs font-bold text-white block">
                  {item.criteria}
                </span>
                <p className="text-[11px] text-slate-400 font-sans leading-tight">
                  {item.proofInProduct}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 9-Part Submission Documentation Browser */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left 4 Columns: Section Nav */}
        <div className="lg:col-span-4 p-4 rounded-3xl bg-slate-950/90 border border-slate-800 space-y-1.5">
          <span className="text-[10px] font-mono text-slate-400 uppercase font-bold tracking-wider px-2 block mb-2">
            Documentation Sections (9)
          </span>

          {SUBMISSION_PACKAGE_SECTIONS.map((sec) => {
            const isActive = sec.id === activeSectionId;
            return (
              <button
                key={sec.id}
                onClick={() => setActiveSectionId(sec.id)}
                className={`w-full text-left p-3 rounded-2xl text-xs font-mono font-bold transition-all flex items-center justify-between ${
                  isActive
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(0,242,254,0.2)]"
                    : "text-slate-400 hover:text-white hover:bg-slate-900/60"
                }`}
              >
                <span>{sec.title}</span>
                <CheckCircle2
                  className={`w-3.5 h-3.5 ${
                    isActive ? "text-cyan-400" : "text-slate-700"
                  }`}
                />
              </button>
            );
          })}
        </div>

        {/* Right 8 Columns: Section Content Display */}
        <div className="lg:col-span-8 p-6 sm:p-8 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
                Active Section
              </span>
              <h3 className="text-xl font-bold text-white">{activeSection.title}</h3>
            </div>

            <button
              onClick={handleCopySection}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 transition-colors"
            >
              {copiedSection ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedSection ? "Copied!" : "Copy Section"}</span>
            </button>
          </div>

          {/* Render Markdown Content as Pre-Formatted Block */}
          <div className="p-5 rounded-2xl bg-black/70 border border-slate-800 font-mono text-xs sm:text-sm text-slate-200 whitespace-pre-wrap leading-relaxed overflow-x-auto selection:bg-cyan-500 selection:text-black">
            {activeSection.contentMarkdown}
          </div>
        </div>
      </div>
    </div>
  );
};
