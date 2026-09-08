"use client";

import React, { useState, useEffect } from "react";
import {
  Volume2,
  Clock,
  ArrowRight,
  Sparkles,
  Play,
  Pause,
  RotateCcw,
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Settings2,
  BookOpen,
} from "lucide-react";
import { CHAMPIONSHIP_SCENES } from "@/lib/championship-data";

export const FounderNarrativeEngine: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [fontSize, setFontSize] = useState<"normal" | "large" | "xlarge">("large");
  const [isPrompterRunning, setIsPrompterRunning] = useState(false);
  const [prompterSeconds, setPrompterSeconds] = useState(0);

  const scene = CHAMPIONSHIP_SCENES[activeStep];
  const totalSteps = CHAMPIONSHIP_SCENES.length;

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPrompterRunning) {
      interval = setInterval(() => {
        setPrompterSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPrompterRunning]);

  const formatSecs = (s: number) => {
    const mins = Math.floor(s / 60);
    const remainder = s % 60;
    return `${mins}:${remainder < 10 ? "0" : ""}${remainder}`;
  };

  const getFontSizeClass = () => {
    switch (fontSize) {
      case "normal":
        return "text-sm sm:text-base leading-relaxed";
      case "large":
        return "text-base sm:text-lg leading-relaxed";
      case "xlarge":
        return "text-lg sm:text-xl leading-relaxed";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
              FOUNDER NARRATIVE & TELEPROMPTER ENGINE
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              8-STEP SCRIPT
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            High-Impact Pitch Delivery & Spoken Prompter
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Step-by-step founder scripts, timing targets, and clinical transition callouts for flawless stage delivery.
          </p>
        </div>

        {/* Teleprompter Controls */}
        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span className="text-white font-bold">{formatSecs(prompterSeconds)}</span>
          </div>

          <button
            onClick={() => setIsPrompterRunning(!isPrompterRunning)}
            className={`p-2 rounded-xl border text-xs font-mono transition-all ${
              isPrompterRunning
                ? "bg-amber-950/80 border-amber-500/50 text-amber-300"
                : "bg-emerald-950/80 border-emerald-500/50 text-emerald-300"
            }`}
          >
            {isPrompterRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={() => {
              setPrompterSeconds(0);
              setIsPrompterRunning(false);
            }}
            className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-white"
            title="Reset timer"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          {/* Font Size Toggle */}
          <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
            {(["normal", "large", "xlarge"] as const).map((sz) => (
              <button
                key={sz}
                onClick={() => setFontSize(sz)}
                className={`px-2.5 py-1 rounded-lg uppercase ${
                  fontSize === sz
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-500/40"
                    : "text-slate-500 hover:text-white"
                }`}
              >
                {sz[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Prompter Stage */}
      <div className="rounded-3xl p-6 sm:p-10 bg-gradient-to-b from-slate-950 via-[#070e1e] to-slate-950 border-2 border-cyan-500/30 shadow-[0_0_50px_rgba(0,242,254,0.15)] space-y-6">
        {/* Step Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <span className="text-[11px] font-mono tracking-widest uppercase text-cyan-400 font-bold block mb-1">
              STEP {scene.id} OF {totalSteps} — {scene.stageBadge}
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-white">
              {scene.title}
            </h2>
            <div className="mt-1 text-xs font-mono text-emerald-400 font-bold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Core Key Message: {scene.keyMessage}</span>
            </div>
          </div>

          <div className="px-4 py-2 rounded-2xl bg-slate-900 border border-slate-700 text-right font-mono flex-shrink-0">
            <span className="text-[10px] text-slate-400 block">TARGET PACING</span>
            <span className="text-base font-bold text-cyan-300">
              ~{scene.durationSeconds} seconds
            </span>
          </div>
        </div>

        {/* Large Prompter Script */}
        <div className="p-6 sm:p-8 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 space-y-4">
          <span className="text-xs font-mono text-cyan-400 uppercase font-bold tracking-wider block">
            Exact Spoken Narrative
          </span>
          <p className={`text-slate-100 font-sans font-medium ${getFontSizeClass()}`}>
            &ldquo;{scene.spokenScript}&rdquo;
          </p>
        </div>

        {/* Transition & Screen Action Guidance */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[11px] font-mono text-cyan-400 font-bold uppercase block">
              Transition Callout
            </span>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              {scene.transitionInstruction}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/80 border border-purple-500/20 space-y-1">
            <span className="text-[11px] font-mono text-purple-400 font-bold uppercase block">
              Judge Takeaway Anchor
            </span>
            <p className="text-xs text-purple-200 font-sans leading-relaxed font-semibold">
              {scene.judgeTakeaway}
            </p>
          </div>
        </div>

        {/* Step Navigation */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-5">
          <button
            onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
            disabled={activeStep === 0}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              activeStep === 0
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-slate-300 bg-slate-900 hover:bg-slate-800 hover:text-white border border-slate-700"
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous Step</span>
          </button>

          <span className="text-xs font-mono text-slate-500">
            Step {scene.id} of {totalSteps}
          </span>

          <button
            onClick={() => setActiveStep((prev) => Math.min(totalSteps - 1, prev + 1))}
            disabled={activeStep === totalSteps - 1}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              activeStep === totalSteps - 1
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-white bg-gradient-to-r from-cyan-500 to-blue-600 shadow-[0_0_12px_rgba(0,242,254,0.25)] hover:scale-[1.02]"
            }`}
          >
            <span>Next Step</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
