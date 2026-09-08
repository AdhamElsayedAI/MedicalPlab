"use client";

import React, { useState, useEffect } from "react";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Clock,
  ShieldAlert,
  Zap,
  CheckCircle2,
} from "lucide-react";
import { GRAND_DEMO_SCENES } from "@/lib/grand-stage-data";

interface FinalStageControllerProps {
  activeSceneIdx: number;
  onSelectScene: (idx: number) => void;
  onPanicReset: () => void;
}

export const FinalStageController: React.FC<FinalStageControllerProps> = ({
  activeSceneIdx,
  onSelectScene,
  onPanicReset,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Target presentation time: 5 minutes = 300 seconds
  const targetSeconds = 300;

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        onSelectScene(Math.min(GRAND_DEMO_SCENES.length - 1, activeSceneIdx + 1));
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        onSelectScene(Math.max(0, activeSceneIdx - 1));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeSceneIdx, onSelectScene]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const isOvertime = elapsedSeconds > targetSeconds;

  return (
    <div className="sticky bottom-4 z-40 max-w-5xl mx-auto px-4">
      <div className="p-3.5 rounded-2xl bg-slate-950/90 backdrop-blur-xl border border-cyan-500/30 shadow-[0_0_30px_rgba(0,0,0,0.8)] flex flex-wrap items-center justify-between gap-4">
        {/* Left: Timer & Scene Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
            <Clock className={`w-4 h-4 ${isOvertime ? "text-rose-400 animate-pulse" : "text-cyan-400"}`} />
            <span
              className={`font-mono text-sm font-black ${
                isOvertime ? "text-rose-400" : "text-white"
              }`}
            >
              {formatTime(elapsedSeconds)}
            </span>
            <span className="text-[10px] font-mono text-slate-400">/ 05:00</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-slate-300">
            <span className="font-bold text-cyan-300">
              Scene {activeSceneIdx + 1} of {GRAND_DEMO_SCENES.length}:
            </span>
            <span className="truncate max-w-[200px] text-slate-400">
              {GRAND_DEMO_SCENES[activeSceneIdx].title.replace(/^Scene \d+: /, "")}
            </span>
          </div>
        </div>

        {/* Center: Playback Controls */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => onSelectScene(Math.max(0, activeSceneIdx - 1))}
            disabled={activeSceneIdx === 0}
            title="Previous Scene (Left Arrow)"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 transition-all"
          >
            <SkipBack className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsPlaying(!isPlaying)}
            title="Play / Pause Presentation (Space)"
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              isPlaying
                ? "bg-amber-500 text-black shadow-[0_0_12px_rgba(245,158,11,0.4)]"
                : "bg-cyan-500 text-black shadow-[0_0_12px_rgba(0,242,254,0.4)]"
            }`}
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Start</span>
              </>
            )}
          </button>

          <button
            onClick={() => onSelectScene(Math.min(GRAND_DEMO_SCENES.length - 1, activeSceneIdx + 1))}
            disabled={activeSceneIdx === GRAND_DEMO_SCENES.length - 1}
            title="Next Scene (Right Arrow)"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 transition-all"
          >
            <SkipForward className="w-4 h-4" />
          </button>

          <button
            onClick={() => {
              setElapsedSeconds(0);
              setIsPlaying(false);
              onSelectScene(0);
            }}
            title="Reset to Scene 1"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Right: Stage Panic Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={onPanicReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-bold bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 transition-all hover:scale-105 active:scale-95"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>PANIC RESET</span>
          </button>
        </div>
      </div>
    </div>
  );
};
