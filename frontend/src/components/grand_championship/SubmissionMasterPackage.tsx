"use client";

import React, { useState } from "react";
import {
  FileText,
  Copy,
  Download,
  CheckCircle2,
  Sparkles,
  ExternalLink,
  Layers,
} from "lucide-react";
import { SUBMISSION_SECTIONS, SubmissionSection } from "@/lib/grand-stage-data";

export const SubmissionMasterPackage: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const [selectedSectionIdx, setSelectedSectionIdx] = useState(0);

  const fullMarkdown = SUBMISSION_SECTIONS.map((s) => s.markdownContent).join("\n\n---\n\n");

  const handleCopyMarkdown = async () => {
    try {
      await navigator.clipboard.writeText(fullMarkdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch {
      // Fallback
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  const handleDownloadMarkdown = () => {
    const blob = new Blob([fullMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "MedicalPlab_Grand_Championship_Submission.md";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setDownloaded(true);
    setTimeout(() => setDownloaded(false), 3000);
  };

  const activeSection: SubmissionSection = SUBMISSION_SECTIONS[selectedSectionIdx];

  return (
    <div className="space-y-6">
      {/* Top Banner with Actions */}
      <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              10-SECTION MASTER PACKAGE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              Grand Prize Ready
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            <span>Championship Submission &amp; Devpost Master Dossier</span>
          </h2>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleCopyMarkdown}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all border ${
              copied
                ? "bg-emerald-500 text-black border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.5)]"
                : "bg-cyan-500 hover:bg-cyan-400 text-black border-cyan-400 shadow-[0_0_15px_rgba(0,242,254,0.35)]"
            }`}
          >
            {copied ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>COPIED TO CLIPBOARD!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>COPY FULL SUBMISSION (.MD)</span>
              </>
            )}
          </button>

          <button
            onClick={handleDownloadMarkdown}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all border ${
              downloaded
                ? "bg-emerald-500 text-black border-emerald-400"
                : "bg-slate-900 hover:bg-slate-800 text-cyan-300 border-cyan-500/30"
            }`}
          >
            {downloaded ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>DOWNLOADED!</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>DOWNLOAD PACKAGE</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Two Column Layout: Section Navigator (4 cols) & Markdown Preview (8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Section List */}
        <div className="lg:col-span-4 space-y-2">
          <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider block mb-2">
            10 Audited Submission Chapters:
          </span>

          {SUBMISSION_SECTIONS.map((sec, idx) => {
            const isSelected = selectedSectionIdx === idx;
            return (
              <button
                key={sec.id}
                onClick={() => setSelectedSectionIdx(idx)}
                className={`w-full p-3 rounded-xl border text-left text-xs font-mono transition-all flex items-center justify-between ${
                  isSelected
                    ? "bg-slate-900 border-cyan-400 text-cyan-300 font-bold shadow-[0_0_12px_rgba(0,242,254,0.2)]"
                    : "bg-slate-950/70 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                <span>{sec.title}</span>
                {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />}
              </button>
            );
          })}
        </div>

        {/* Right Section Preview */}
        <div className="lg:col-span-8 p-6 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-mono text-cyan-400 font-bold uppercase">
              CHAPTER 0{activeSection.id} PREVIEW
            </span>
            <span className="text-xs font-mono text-slate-400">
              Markdown Formatted Output
            </span>
          </div>

          <div className="prose prose-invert max-w-none text-xs leading-relaxed text-slate-300 font-mono bg-slate-900/60 p-5 rounded-xl border border-slate-800/80 whitespace-pre-wrap">
            {activeSection.markdownContent}
          </div>
        </div>
      </div>
    </div>
  );
};
