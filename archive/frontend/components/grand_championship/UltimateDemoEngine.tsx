"use client";

import React, { useState, useEffect } from "react";
import {
  Play,
  Pause,
  ArrowRight,
  ArrowLeft,
  Clock,
  Sparkles,
  ShieldCheck,
  Zap,
  Terminal,
  Layers,
  ChevronRight,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { GRAND_DEMO_SCENES, DemoScene } from "@/lib/grand-stage-data";
import { NavigationMode } from "@/lib/types";

interface UltimateDemoEngineProps {
  activeSceneIdx: number;
  onSelectScene: (idx: number) => void;
  onNavigateToMode?: (mode: NavigationMode) => void;
}

export const UltimateDemoEngine: React.FC<UltimateDemoEngineProps> = ({
  activeSceneIdx,
  onSelectScene,
  onNavigateToMode,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(
    GRAND_DEMO_SCENES[activeSceneIdx].durationSeconds
  );

  const currentScene: DemoScene = GRAND_DEMO_SCENES[activeSceneIdx];

  // Sync timer when scene changes
  useEffect(() => {
    setSecondsRemaining(currentScene.durationSeconds);
  }, [activeSceneIdx, currentScene.durationSeconds]);

  // Autoplay timer
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isPlaying) {
      timer = setInterval(() => {
        setSecondsRemaining((prev) => {
          if (prev <= 1) {
            // Auto advance
            if (activeSceneIdx < GRAND_DEMO_SCENES.length - 1) {
              onSelectScene(activeSceneIdx + 1);
            } else {
              setIsPlaying(false);
            }
            return currentScene.durationSeconds;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, activeSceneIdx, currentScene.durationSeconds, onSelectScene]);

  // Quick navigation mapping for live product demo jumps
  const getRelevantMode = (sceneId: number): NavigationMode => {
    switch (sceneId) {
      case 1:
        return "landing";
      case 2:
        return "validation";
      case 3:
        return "tutor";
      case 4:
        return "anatomy";
      case 5:
        return "simulation";
      case 6:
        return "quiz";
      case 7:
        return "admin";
      case 8:
        return "investor";
      default:
        return "landing";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner with Autoplay & Timer */}
      <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              5-MINUTE CHAMPIONSHIP DEMO
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              Deterministic 8-Scene Controller
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <span>{currentScene.title}</span>
            <span className="text-sm font-normal text-slate-400">— {currentScene.subtitle}</span>
          </h2>
        </div>

        {/* Autoplay & Scene Counter */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">Scene Time: </span>
            <span className="font-bold text-cyan-300">{secondsRemaining}s remaining</span>
          </div>

          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
              isPlaying
                ? "bg-amber-500 text-black shadow-[0_0_12px_rgba(245,158,11,0.4)]"
                : "bg-cyan-500 text-black shadow-[0_0_12px_rgba(0,242,254,0.4)]"
            }`}
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause Auto-Scrubber</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Autoplay Demo</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 8-Scene Progress Stepper */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        {GRAND_DEMO_SCENES.map((scene, idx) => {
          const isSelected = activeSceneIdx === idx;
          const isPassed = activeSceneIdx > idx;
          return (
            <button
              key={scene.id}
              onClick={() => onSelectScene(idx)}
              className={`p-2.5 rounded-xl border text-left transition-all relative overflow-hidden ${
                isSelected
                  ? "bg-slate-900 border-cyan-400 shadow-[0_0_15px_rgba(0,242,254,0.2)] ring-1 ring-cyan-400/60"
                  : isPassed
                  ? "bg-slate-950/90 border-slate-800 text-slate-400 hover:border-slate-700"
                  : "bg-slate-950/50 border-slate-900 text-slate-500 hover:border-slate-800"
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                <span>SCENE 0{scene.id}</span>
                <span className="text-cyan-400 font-bold">{scene.durationSeconds}s</span>
              </div>
              <p
                className={`text-xs font-bold truncate ${
                  isSelected ? "text-cyan-300" : isPassed ? "text-slate-200" : "text-slate-400"
                }`}
              >
                {scene.title.replace(/^Scene \d+: /, "")}
              </p>
            </button>
          );
        })}
      </div>

      {/* Main Scene Deep Dive & Presenter HUD */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Speaker Teleprompter Script (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Spoken Script Card */}
          <div className="p-6 rounded-2xl border border-cyan-500/30 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 relative">
            <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-3">
              <span className="text-xs font-mono font-bold text-cyan-400 tracking-wider uppercase flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>FOUNDER SPOKEN SCRIPT ({currentScene.durationSeconds} SECONDS)</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                {currentScene.activeStageTag}
              </span>
            </div>

            <p className="text-base sm:text-lg text-slate-100 font-serif leading-relaxed italic">
              "{currentScene.speakerScript}"
            </p>

            {/* Screen Action Instructions */}
            <div className="mt-5 p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider block font-bold">
                PRESENTER SCREEN ACTION TRIGGER:
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                {currentScene.screenAction}
              </p>
            </div>

            {/* Live Jump Button */}
            {onNavigateToMode && (
              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                <span className="text-xs font-mono text-slate-400">
                  Switch view to live product:
                </span>
                <button
                  onClick={() => onNavigateToMode(getRelevantMode(currentScene.id))}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 transition-all"
                >
                  <span>Launch {getRelevantMode(currentScene.id).toUpperCase()} View</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right: Judge Takeaway & Technical Proof (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Judge Takeaway Card */}
          <div className="p-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4" />
              <span>KEY JUDGE TAKEAWAY</span>
            </div>
            <p className="text-sm text-emerald-200 font-semibold leading-relaxed">
              {currentScene.judgeTakeaway}
            </p>
          </div>

          {/* Technical Proof & Empirical Code Contract */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
              <Terminal className="w-4 h-4" />
              <span>TECHNICAL PROOF &amp; BENCHMARK</span>
            </div>
            <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              {currentScene.technicalProof}
            </p>
          </div>

          {/* Offline Fallback State */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>DETERMINISTIC FALLBACK STATE</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              {currentScene.fallbackState}
            </p>
          </div>

          {/* Stepper Navigation Buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              disabled={activeSceneIdx === 0}
              onClick={() => onSelectScene(Math.max(0, activeSceneIdx - 1))}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-30 transition-all"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous Scene</span>
            </button>

            <button
              disabled={activeSceneIdx === GRAND_DEMO_SCENES.length - 1}
              onClick={() => onSelectScene(Math.min(GRAND_DEMO_SCENES.length - 1, activeSceneIdx + 1))}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-mono font-bold bg-cyan-500 hover:bg-cyan-400 text-black shadow-[0_0_15px_rgba(0,242,254,0.35)] disabled:opacity-30 transition-all"
            >
              <span>Advance to Scene {Math.min(8, activeSceneIdx + 2)}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
