"use client";

import React, { useState, useEffect } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Zap,
  ArrowRight,
  Clock,
  ShieldCheck,
  Layers,
  Terminal,
  Volume2,
} from "lucide-react";
import { BATTLE_SCENES } from "@/lib/stage-l-data";
import { NavigationMode } from "@/lib/types";

interface FinalDemoMasterProps {
  onLaunchScene: (mode: NavigationMode) => void;
  isOfflineMode: boolean;
}

export const FinalDemoMaster: React.FC<FinalDemoMasterProps> = ({
  onLaunchScene,
  isOfflineMode,
}) => {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [remainingSecs, setRemainingSecs] = useState(BATTLE_SCENES[0].durationSeconds);

  const scene = BATTLE_SCENES[currentIdx];
  const total = BATTLE_SCENES.length;

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying) {
      timer = setInterval(() => {
        setRemainingSecs((prev) => {
          if (prev <= 1) {
            if (currentIdx < total - 1) {
              const next = currentIdx + 1;
              setCurrentIdx(next);
              onLaunchScene(BATTLE_SCENES[next].targetMode);
              return BATTLE_SCENES[next].durationSeconds;
            } else {
              setIsPlaying(false);
              return 0;
            }
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isPlaying, currentIdx, total, onLaunchScene]);

  const selectScene = (idx: number) => {
    setCurrentIdx(idx);
    setRemainingSecs(BATTLE_SCENES[idx].durationSeconds);
    onLaunchScene(BATTLE_SCENES[idx].targetMode);
  };

  const nextScene = () => {
    if (currentIdx < total - 1) selectScene(currentIdx + 1);
  };

  const prevScene = () => {
    if (currentIdx > 0) selectScene(currentIdx - 1);
  };

  const reset = () => {
    setIsPlaying(false);
    selectScene(0);
  };

  return (
    <div className="space-y-6">
      {/* Master Controller HUD Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-[0_0_20px_rgba(0,242,254,0.35)]">
            <Zap className="w-5 h-5 fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-extrabold text-base text-white tracking-wide">
                FINAL DEMO MASTER CONTROLLER
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-cyan-950 text-cyan-300 border border-cyan-500/40">
                Cinematic 8-Scene Flow
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              One-click orchestrated presentation: Problem $\rightarrow$ Vision $\rightarrow$ Anatomy $\rightarrow$ Tutor $\rightarrow$ Evidence $\rightarrow$ Simulation $\rightarrow$ Learning $\rightarrow$ Business.
            </p>
          </div>
        </div>

        {/* Presenter Controls */}
        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span className="text-white font-bold">{remainingSecs}s</span>
            <span className="text-slate-500">remaining</span>
          </div>

          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-mono font-bold border transition-all ${
              isPlaying
                ? "bg-amber-950/80 border-amber-500/50 text-amber-300"
                : "bg-cyan-950/80 border-cyan-400/50 text-cyan-300 shadow-[0_0_15px_rgba(0,242,254,0.2)]"
            }`}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>{isPlaying ? "Pause Flow" : "Auto-Advance"}</span>
          </button>

          <button
            onClick={reset}
            className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-white"
            title="Reset to Scene 1"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Scene Display Stage */}
      <div className="rounded-3xl p-6 sm:p-8 bg-gradient-to-b from-slate-950 via-[#070e1e] to-slate-950 border-2 border-cyan-500/30 shadow-[0_0_40px_rgba(0,242,254,0.12)] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-500/40 uppercase">
                {scene.stageBadge}
              </span>
              <span className="text-xs font-mono text-slate-400">
                Scene {scene.id} of {total}
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-wide">
              {scene.title}
            </h2>
          </div>

          <button
            onClick={() => onLaunchScene(scene.targetMode)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-mono font-bold bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/25 hover:scale-[1.02] transition-transform flex-shrink-0"
          >
            <span>Launch Live Scene</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* 3 Core Execution Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-slate-900/80 border border-cyan-500/20 space-y-1.5">
            <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block flex items-center gap-1">
              <Layers className="w-3.5 h-3.5" /> Screen Action
            </span>
            <p className="text-xs text-slate-200 font-sans leading-relaxed">
              {scene.screenAction}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/80 border border-purple-500/20 space-y-1.5">
            <span className="text-[10px] font-mono text-purple-400 uppercase font-bold block flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Judge Takeaway Anchor
            </span>
            <p className="text-xs text-purple-200 font-sans leading-relaxed font-semibold">
              {scene.judgeTakeaway}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/80 border border-emerald-500/20 space-y-1.5">
            <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold block flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Backup State
            </span>
            <p className="text-xs text-emerald-200 font-sans leading-relaxed">
              {scene.backupState}
            </p>
          </div>
        </div>

        {/* Speaker Script Teleprompter Drawer */}
        <div className="p-5 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-400 border-b border-cyan-500/20 pb-1.5">
            <div className="flex items-center gap-1.5 font-bold">
              <Volume2 className="w-4 h-4 text-cyan-300" />
              <span>EXACT PRESENTER SPOKEN SCRIPT</span>
            </div>
            <span className="text-slate-400">Target Time: {scene.durationSeconds}s</span>
          </div>
          <p className="text-sm sm:text-base text-slate-100 font-sans leading-relaxed italic">
            &ldquo;{scene.speakerScript}&rdquo;
          </p>
        </div>

        {/* Stepper Timeline & Navigation */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-800 pt-5">
          <button
            onClick={prevScene}
            disabled={currentIdx === 0}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentIdx === 0
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-slate-300 bg-slate-900 hover:bg-slate-800 hover:text-white border border-slate-700"
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Prev Scene</span>
          </button>

          <div className="flex items-center gap-2 overflow-x-auto py-1">
            {BATTLE_SCENES.map((sc, idx) => (
              <button
                key={sc.id}
                onClick={() => selectScene(idx)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
                  idx === currentIdx
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400 shadow-[0_0_12px_rgba(0,242,254,0.3)]"
                    : idx < currentIdx
                    ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                    : "bg-slate-900 text-slate-500 border border-slate-800 hover:text-slate-300"
                }`}
              >
                <span>{sc.id}</span>
              </button>
            ))}
          </div>

          <button
            onClick={nextScene}
            disabled={currentIdx === total - 1}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentIdx === total - 1
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-white bg-gradient-to-r from-cyan-500 to-blue-600 shadow-[0_0_12px_rgba(0,242,254,0.25)] hover:scale-[1.02]"
            }`}
          >
            <span>Next Scene</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
