"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { STARTUP_DEMO_SCENES, StartupScene } from "@/lib/startup-data";

interface StartupDemoControllerProps {
  onSelectView: (viewId: string) => void;
  activeViewId: string;
}

export default function StartupDemoController({
  onSelectView,
  activeViewId,
}: StartupDemoControllerProps) {
  const [currentSceneIdx, setCurrentSceneIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progressSec, setProgressSec] = useState(0);

  const scene: StartupScene = STARTUP_DEMO_SCENES[currentSceneIdx];

  // Auto-play timer
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setProgressSec((prev) => {
          if (prev >= scene.durationSec) {
            // Advance to next scene
            if (currentSceneIdx < STARTUP_DEMO_SCENES.length - 1) {
              const nextIdx = currentSceneIdx + 1;
              setCurrentSceneIdx(nextIdx);
              onSelectView(STARTUP_DEMO_SCENES[nextIdx].targetView);
              return 0;
            } else {
              setIsPlaying(false);
              return scene.durationSec;
            }
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, currentSceneIdx, scene.durationSec, onSelectView]);

  const handleSelectScene = (idx: number) => {
    setCurrentSceneIdx(idx);
    setProgressSec(0);
    onSelectView(STARTUP_DEMO_SCENES[idx].targetView);
  };

  const handleTogglePlay = () => {
    if (!isPlaying) {
      onSelectView(scene.targetView);
    }
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900/95 to-cyan-950/40 backdrop-blur-md border border-cyan-500/40 rounded-2xl p-5 shadow-2xl space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <span className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
          <div>
            <span className="text-xs font-mono uppercase tracking-widest text-cyan-400 font-bold block">
              5-Minute Founder Venture Pitch Controller
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              Cinematic Investor & Judge Pitch Engine
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const prev = Math.max(0, currentSceneIdx - 1);
              handleSelectScene(prev);
            }}
            disabled={currentSceneIdx === 0}
            className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 disabled:opacity-30 hover:text-white"
          >
            ← Prev
          </button>

          <button
            onClick={handleTogglePlay}
            className={`text-xs px-4 py-1.5 rounded-lg font-bold font-mono transition-all flex items-center gap-1.5 ${
              isPlaying
                ? "bg-amber-400 text-black shadow-md shadow-amber-400/20"
                : "bg-cyan-500 text-black shadow-md shadow-cyan-500/20 hover:bg-cyan-400"
            }`}
          >
            <span>{isPlaying ? "❚❚ Pause" : "▶ Start 5-Min Founder Pitch"}</span>
          </button>

          <button
            onClick={() => {
              const next = Math.min(STARTUP_DEMO_SCENES.length - 1, currentSceneIdx + 1);
              handleSelectScene(next);
            }}
            disabled={currentSceneIdx === STARTUP_DEMO_SCENES.length - 1}
            className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 disabled:opacity-30 hover:text-white"
          >
            Next →
          </button>
        </div>
      </div>

      {/* 5-Scene Timeline Navigation */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {STARTUP_DEMO_SCENES.map((sc, idx) => {
          const isCurrent = idx === currentSceneIdx;
          return (
            <button
              key={sc.sceneNumber}
              onClick={() => handleSelectScene(idx)}
              className={`text-left p-2.5 rounded-xl border text-xs transition-all relative overflow-hidden ${
                isCurrent
                  ? "bg-cyan-950/70 border-cyan-400 shadow-md shadow-cyan-950/60"
                  : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700 text-slate-400"
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className={isCurrent ? "text-cyan-400 font-bold" : "text-slate-500"}>
                  SCENE 0{sc.sceneNumber}
                </span>
                <span className="text-slate-500">{sc.durationSec}s</span>
              </div>
              <div className="font-semibold text-white mt-1 truncate">{sc.title}</div>
              {isCurrent && isPlaying && (
                <div
                  className="absolute bottom-0 left-0 h-1 bg-cyan-400 transition-all duration-300"
                  style={{ width: `${(progressSec / sc.durationSec) * 100}%` }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Active Scene Narration & Telemetry */}
      <AnimatePresence mode="wait">
        <motion.div
          key={scene.sceneNumber}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          className="grid grid-cols-1 lg:grid-cols-12 gap-4 pt-1"
        >
          {/* Narration Script (Left 7 Cols) */}
          <div className="lg:col-span-7 bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                Founder Pitch Script
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                Time: {progressSec}s / {scene.durationSec}s
              </span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed italic">
              &ldquo;{scene.founderScript}&rdquo;
            </p>
            <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono">
              <span className="text-cyan-400 font-semibold">Target Product Action:</span> {scene.screenAction}
            </div>
          </div>

          {/* Investor Takeaway (Right 5 Cols) */}
          <div className="lg:col-span-5 bg-gradient-to-br from-slate-950 to-cyan-950/30 p-4 rounded-xl border border-cyan-500/30 flex flex-col justify-between space-y-2">
            <div>
              <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider block mb-1">
                VC Takeaway Thesis
              </span>
              <p className="text-xs font-semibold text-white leading-snug">
                {scene.investorTakeaway}
              </p>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <span className="text-[10px] font-mono text-slate-400">
                Linked View: {scene.targetView}
              </span>
              <button
                onClick={() => onSelectView(scene.targetView)}
                className="text-[10px] font-mono px-2 py-1 rounded bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/30"
              >
                Jump to View →
              </button>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
