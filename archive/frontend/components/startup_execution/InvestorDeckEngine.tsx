"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { INVESTOR_DECK_SLIDES, InvestorSlide, MetricClassification } from "@/lib/startup-data";

export default function InvestorDeckEngine() {
  const [currentSlideIdx, setCurrentSlideIdx] = useState(0);

  const slide: InvestorSlide = INVESTOR_DECK_SLIDES[currentSlideIdx];

  const getBadgeStyle = (classification: MetricClassification) => {
    switch (classification) {
      case "[Verified]":
        return "bg-emerald-950/80 border-emerald-500/50 text-emerald-300";
      case "[Prototype]":
        return "bg-cyan-950/80 border-cyan-500/50 text-cyan-300";
      case "[Projection]":
        return "bg-amber-950/80 border-amber-500/50 text-amber-300";
      case "[Future Target]":
        return "bg-purple-950/80 border-purple-500/50 text-purple-300";
      default:
        return "bg-slate-800 border-slate-700 text-slate-300";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Deck Navigation Bar */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Institutional Pitch Engine • Seed Round Presentation
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                10-Slide Standard
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Investor Pitch Deck
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              The Venture-Scale Healthcare AI Thesis: Socratic Intelligence, Clinical Provenance, and Enterprise Simulation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentSlideIdx((prev) => Math.max(0, prev - 1))}
              disabled={currentSlideIdx === 0}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
            >
              ← Prev Slide
            </button>
            <span className="text-xs font-mono text-cyan-400 px-2 font-semibold">
              Slide {slide.slideNumber} / {INVESTOR_DECK_SLIDES.length}
            </span>
            <button
              onClick={() => setCurrentSlideIdx((prev) => Math.min(INVESTOR_DECK_SLIDES.length - 1, prev + 1))}
              disabled={currentSlideIdx === INVESTOR_DECK_SLIDES.length - 1}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
            >
              Next Slide →
            </button>
          </div>
        </div>

        {/* 10-Slide Timeline Selector */}
        <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-1.5">
          {INVESTOR_DECK_SLIDES.map((s, idx) => {
            const isActive = idx === currentSlideIdx;
            return (
              <button
                key={s.slideNumber}
                onClick={() => setCurrentSlideIdx(idx)}
                className={`p-2 rounded-xl text-left border text-xs transition-all ${
                  isActive
                    ? "bg-cyan-950/70 border-cyan-400 text-cyan-300 shadow-md shadow-cyan-950/50 font-bold"
                    : "bg-slate-950/40 border-slate-800/80 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                <div className="text-[10px] font-mono text-slate-500">0{s.slideNumber}</div>
                <div className="truncate mt-0.5">{s.title}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Slide Presentation Theater */}
      <AnimatePresence mode="wait">
        <motion.div
          key={slide.slideNumber}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
          className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl space-y-6"
        >
          {/* Slide Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono font-bold text-cyan-400">
                  SLIDE 0{slide.slideNumber} OF 10
                </span>
                <span className="text-slate-600">•</span>
                <span className="text-xs font-mono text-slate-400">{slide.subtitle}</span>
              </div>
              <h3 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                {slide.title}
              </h3>
            </div>

            {/* Key Metric Spotlight */}
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-right min-w-[220px]">
              <div className="flex items-center justify-end gap-1.5 mb-1">
                <span className="text-[10px] font-mono uppercase text-slate-500">
                  {slide.keyMetric.label}
                </span>
                <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border font-semibold ${getBadgeStyle(slide.keyMetric.classification)}`}>
                  {slide.keyMetric.classification}
                </span>
              </div>
              <div className="text-2xl font-black font-mono text-cyan-400">
                {slide.keyMetric.value}
              </div>
              {slide.keyMetric.subtext && (
                <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                  {slide.keyMetric.subtext}
                </div>
              )}
            </div>
          </div>

          {/* Slide Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left 7 Cols: Key Bullet Points & Screen Action */}
            <div className="lg:col-span-7 space-y-5">
              <div className="space-y-3">
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
                  Core Venture Thesis & Argument Points
                </span>
                {slide.bulletPoints.map((pt, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-sm text-slate-200 flex items-start gap-3"
                  >
                    <span className="text-cyan-400 font-bold font-mono mt-0.5">0{i + 1}.</span>
                    <span className="leading-relaxed">{pt}</span>
                  </div>
                ))}
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs font-mono text-slate-400">
                <span className="text-cyan-400 font-semibold uppercase block mb-1">
                  Target Product Demonstration Action:
                </span>
                <p className="text-slate-300">{slide.screenAction}</p>
              </div>
            </div>

            {/* Right 5 Cols: Founder Narration Script & Investor Takeaway */}
            <div className="lg:col-span-5 space-y-5 flex flex-col justify-between">
              {/* Founder Narration Card */}
              <div className="bg-slate-950/90 p-4 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
                    Founder Pitch Script
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">60-second delivery</span>
                </div>
                <p className="text-xs text-slate-200 italic leading-relaxed">
                  &ldquo;{slide.founderNarration}&rdquo;
                </p>
              </div>

              {/* Investor Takeaway Card */}
              <div className="bg-gradient-to-br from-slate-950 to-cyan-950/30 p-4 rounded-2xl border border-cyan-500/30 space-y-1.5">
                <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider block">
                  Lead Investor Takeaway
                </span>
                <p className="text-xs font-bold text-white leading-snug">
                  {slide.investorTakeaway}
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
