"use client";

import React, { useState, useEffect } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  Mic,
  Maximize2,
  Sparkles,
  ShieldCheck,
  TrendingUp,
  Award,
  Layers,
  FileText,
  Play,
  Pause,
  RotateCcw,
} from "lucide-react";
import { FOUNDER_PITCH_SLIDES } from "@/lib/founder-data";
import { MetricLabel, PitchSlide } from "@/lib/types";

export const FounderPitchEngine: React.FC = () => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [showSpeakerNotes, setShowSpeakerNotes] = useState(true);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const slide = FOUNDER_PITCH_SLIDES[currentSlideIndex];
  const totalSlides = FOUNDER_PITCH_SLIDES.length;

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isTimerRunning) {
      interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "Space") {
        nextSlide();
      } else if (e.key === "ArrowLeft") {
        prevSlide();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentSlideIndex]);

  const nextSlide = () => {
    if (currentSlideIndex < totalSlides - 1) {
      setCurrentSlideIndex((prev) => prev + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlideIndex > 0) {
      setCurrentSlideIndex((prev) => prev - 1);
    }
  };

  const resetPitch = () => {
    setCurrentSlideIndex(0);
    setElapsedSeconds(0);
    setIsTimerRunning(false);
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    return `${mins}:${remainder < 10 ? "0" : ""}${remainder}`;
  };

  const getMetricBadge = (tag: MetricLabel) => {
    switch (tag) {
      case "Verified metric":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-500/40">
            ✓ Verified metric
          </span>
        );
      case "Demo projection":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-300 border border-cyan-500/40">
            ⚡ Demo projection
          </span>
        );
      case "Future target":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-950/80 text-purple-300 border border-purple-500/40">
            🎯 Future target
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Pitch Deck Header Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-cyan-950 border border-cyan-400/40 text-cyan-300 shadow-[0_0_15px_rgba(0,242,254,0.25)]">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-extrabold text-sm sm:text-base text-white tracking-wide">
                STARTUP PITCH ENGINE
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-cyan-950 text-cyan-300 border border-cyan-500/40">
                10-Slide Deck
              </span>
            </div>
            <div className="text-xs text-slate-400 font-mono">
              Slide {slide.id} of {totalSlides}:{" "}
              <span className="text-cyan-400 font-bold uppercase">
                {slide.category}
              </span>
            </div>
          </div>
        </div>

        {/* Presenter Timer Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span className="text-white font-bold">{formatTime(elapsedSeconds)}</span>
            <span className="text-slate-500">/ 5:30 target</span>
          </div>

          <button
            onClick={() => setIsTimerRunning(!isTimerRunning)}
            className={`p-2 rounded-xl border text-xs font-mono transition-all ${
              isTimerRunning
                ? "bg-amber-950/60 border-amber-500/50 text-amber-300"
                : "bg-emerald-950/60 border-emerald-500/50 text-emerald-300"
            }`}
            title={isTimerRunning ? "Pause timer" : "Start timer"}
          >
            {isTimerRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={resetPitch}
            className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 transition-colors"
            title="Reset pitch"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowSpeakerNotes(!showSpeakerNotes)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono border transition-all ${
              showSpeakerNotes
                ? "bg-cyan-950/80 border-cyan-400/50 text-cyan-300 shadow-[0_0_10px_rgba(0,242,254,0.2)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            <span>Speaker Notes</span>
          </button>
        </div>
      </div>

      {/* Main Pitch Slide Stage */}
      <div className="relative rounded-3xl p-6 sm:p-10 bg-gradient-to-b from-slate-950 via-[#070d1d] to-slate-950 border-2 border-cyan-500/30 shadow-[0_0_50px_rgba(0,242,254,0.15)] min-h-[480px] flex flex-col justify-between">
        {/* Slide Progress Pill Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <span className="text-[11px] font-mono tracking-widest uppercase text-cyan-400 font-bold block mb-1">
              {slide.category} SECTION — SLIDE {slide.id}/{totalSlides}
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
              {slide.title}
            </h2>
            <p className="text-sm sm:text-base text-cyan-200/80 font-sans mt-1">
              {slide.subtitle}
            </p>
          </div>

          <div className="flex items-center gap-1 self-start sm:self-center">
            {FOUNDER_PITCH_SLIDES.map((s, idx) => (
              <button
                key={s.id}
                onClick={() => setCurrentSlideIndex(idx)}
                className={`h-2 rounded-full transition-all ${
                  idx === currentSlideIndex
                    ? "w-8 bg-cyan-400 shadow-[0_0_10px_rgba(0,242,254,0.8)]"
                    : idx < currentSlideIndex
                    ? "w-2.5 bg-emerald-400"
                    : "w-2.5 bg-slate-800 hover:bg-slate-600"
                }`}
                title={`${s.id}. ${s.title}`}
              />
            ))}
          </div>
        </div>

        {/* Slide Content Body: Bullet Points & Labeled Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 py-8 items-start">
          {/* Left 7 Columns: Core Value Proposition */}
          <div className="lg:col-span-7 space-y-4">
            <h4 className="text-xs font-mono text-slate-400 tracking-wider uppercase">
              Key Strategic Points
            </h4>
            <div className="space-y-3.5">
              {slide.bulletPoints.map((point, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3.5 p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-cyan-500/30 transition-colors"
                >
                  <div className="flex-shrink-0 w-6 h-6 rounded-lg bg-cyan-950/90 border border-cyan-400/40 text-cyan-300 flex items-center justify-center text-xs font-mono font-bold mt-0.5">
                    {i + 1}
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed font-sans">
                    {point}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Right 5 Columns: Labeled Metrics Display */}
          <div className="lg:col-span-5 space-y-4">
            <h4 className="text-xs font-mono text-slate-400 tracking-wider uppercase">
              Financial & Clinical Proof Points
            </h4>
            <div className="space-y-3">
              {slide.metrics.map((metric, i) => (
                <div
                  key={i}
                  className="p-4 rounded-2xl bg-slate-900/90 border border-cyan-500/20 shadow-inner space-y-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono text-slate-300 font-semibold">
                      {metric.label}
                    </span>
                    {getMetricBadge(metric.tag)}
                  </div>
                  <div className="text-2xl sm:text-3xl font-black font-mono text-white tracking-tight">
                    {metric.value}
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans leading-normal">
                    {metric.detail}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Slide Navigation Footbar */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-6">
          <button
            onClick={prevSlide}
            disabled={currentSlideIndex === 0}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentSlideIndex === 0
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-slate-300 bg-slate-900 hover:bg-slate-800 hover:text-white border border-slate-700"
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous Slide</span>
          </button>

          <span className="text-xs font-mono text-slate-500">
            Use Left / Right arrow keys or spacebar
          </span>

          <button
            onClick={nextSlide}
            disabled={currentSlideIndex === totalSlides - 1}
            className={`flex items-center gap-2 px-5 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentSlideIndex === totalSlides - 1
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-white bg-gradient-to-r from-cyan-500 to-blue-600 shadow-[0_0_15px_rgba(0,242,254,0.3)] hover:scale-[1.02]"
            }`}
          >
            <span>Next Slide</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Speaker Notes Drawer */}
      {showSpeakerNotes && (
        <div className="rounded-2xl p-5 bg-slate-950/90 border border-cyan-500/30 shadow-lg space-y-2 animate-in fade-in duration-200">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-400 border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Mic className="w-4 h-4 text-cyan-300 animate-pulse" />
              <span className="font-bold uppercase tracking-wide">
                PRESENTER SCRIPT & SPEAKER NOTES
              </span>
            </div>
            <span className="text-slate-400">
              Target slide time: ~{slide.targetDurationSeconds} seconds
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-200 font-sans leading-relaxed italic">
            &ldquo;{slide.speakerNotes}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
};
