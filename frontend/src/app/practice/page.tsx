"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { UniversityLearning } from "@/components/UniversityLearning";
import { PLABPracticeView } from "@/components/practice/PLABPracticeView";
import { BookOpen, Stethoscope } from "lucide-react";

function PracticeContent() {
  const searchParams = useSearchParams();
  const initialTrack = searchParams.get("track") === "plab" ? "plab" : "university";
  const [activeTrack, setActiveTrack] = useState<"university" | "plab">(initialTrack);

  useEffect(() => {
    const trackParam = searchParams.get("track");
    if (trackParam === "plab") setActiveTrack("plab");
    else if (trackParam === "university") setActiveTrack("university");
  }, [searchParams]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 med-fade-in">
      {/* Top Track Switcher Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-['Plus_Jakarta_Sans',sans-serif]">
            Medical Practice Modules
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Preclinical mechanisms and clinical decision scenarios with verified Socratic reasoning loops.
          </p>
        </div>

        {/* Track Selector Pill */}
        <div className="flex items-center gap-1.5 p-1 bg-white/[0.04] border border-white/[0.08] rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTrack("university")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTrack === "university"
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/30 shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Preclinical University</span>
          </button>

          <button
            onClick={() => setActiveTrack("plab")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTrack === "plab"
                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Clinical PLAB</span>
          </button>
        </div>
      </div>

      {/* Render Active Track Component */}
      {activeTrack === "university" ? (
        <UniversityLearning />
      ) : (
        <PLABPracticeView onSwitchToUniversity={() => setActiveTrack("university")} />
      )}
    </div>
  );
}

export default function PracticePage() {
  return (
    <AppShell>
      <Suspense fallback={<div className="p-8 text-center text-slate-400 text-sm">Loading practice modules...</div>}>
        <PracticeContent />
      </Suspense>
    </AppShell>
  );
}
