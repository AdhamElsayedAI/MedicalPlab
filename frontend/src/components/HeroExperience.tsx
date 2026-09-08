"use client";

import React from "react";
import {
  Layers,
  Stethoscope,
  GraduationCap,
  Activity,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { NavigationMode } from "@/lib/types";

interface HeroExperienceProps {
  onLaunchMode: (mode: NavigationMode) => void;
  onStartDemoJourney: () => void;
  onOpenPipelineModal: () => void;
}

export const HeroExperience: React.FC<HeroExperienceProps> = ({
  onLaunchMode,
  onStartDemoJourney,
  onOpenPipelineModal,
}) => {
  const portals: {
    mode: NavigationMode;
    title: string;
    description: string;
    badge: string;
    icon: React.ReactNode;
    color: string;
  }[] = [
    {
      mode: "anatomy",
      title: "3D Anatomy Lab",
      description: "Holographic interactive exploration with hotspot clinical links & Stage-F query triggers.",
      badge: "THREE.JS LAB",
      icon: <Layers className="w-6 h-6 text-cyan-400" />,
      color: "border-cyan-500/30 hover:border-cyan-400 hover:shadow-cyan-500/20",
    },
    {
      mode: "tutor",
      title: "AI Medical Tutor",
      description: "Socratic clinical mentorship grounded in verified NICE/BNF guidelines with citation proof.",
      badge: "STAGE-D & STAGE-B",
      icon: <Stethoscope className="w-6 h-6 text-blue-400" />,
      color: "border-blue-500/30 hover:border-blue-400 hover:shadow-blue-500/20",
    },
    {
      mode: "quiz",
      title: "Adaptive PLAB Quiz",
      description: "High-yield Single Best Answer MCQs generated deterministically with distractor elimination.",
      badge: "STAGE-C & STAGE-E",
      icon: <GraduationCap className="w-6 h-6 text-purple-400" />,
      color: "border-purple-500/30 hover:border-purple-400 hover:shadow-purple-500/20",
    },
    {
      mode: "simulation",
      title: "Emergency Ward Sim",
      description: "Resuscitation bay simulation with live ECG waveform, dynamic vitals, and safety contraindication filters.",
      badge: "STAGE-F ENGINE",
      icon: <Activity className="w-6 h-6 text-emerald-400" />,
      color: "border-emerald-500/30 hover:border-emerald-400 hover:shadow-emerald-500/20",
    },
  ];

  return (
    <section className="relative overflow-hidden py-12 lg:py-16">
      {/* Ambient Cybernetic Lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-gradient-to-tr from-cyan-500/10 via-blue-600/10 to-transparent blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Top Tag */}
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/70 border border-cyan-500/40 text-cyan-300 text-xs font-mono tracking-wide shadow-[0_0_15px_rgba(0,242,254,0.2)]">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" style={{ animationDuration: "6s" }} />
            <span>STARTUP-GRADE MEDICAL AI PLATFORM</span>
            <span className="w-1 h-1 rounded-full bg-cyan-400" />
            <span className="text-emerald-400 font-bold">100% EVIDENCE-GROUNDED</span>
          </div>
        </div>

        {/* Hero Title */}
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
            The Digital Anatomy Laboratory &{" "}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-300 text-glow-cyan">
              Clinical Intelligence OS
            </span>
          </h1>
          <p className="mt-4 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Engineered for UK PLAB & GMC licensing exams. MedicalPlab couples a 3D anatomical exploration lab with a frozen 7-stage evidence verification and clinical safety pipeline.
          </p>

          {/* Action CTAs */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={onStartDemoJourney}
              className="flex items-center gap-3 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-sm shadow-[0_0_25px_rgba(0,242,254,0.35)] hover:shadow-[0_0_35px_rgba(0,242,254,0.5)] transition-all hover:scale-[1.03] active:scale-[0.98]"
            >
              <Zap className="w-4 h-4 fill-current" />
              <span>Launch 3-Minute Guided Demo Flow</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onOpenPipelineModal}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 border border-slate-700 hover:border-cyan-500/40 text-sm font-semibold transition-all"
            >
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>Inspect AI Architecture (Stages R $\rightarrow$ G)</span>
            </button>
          </div>
        </div>

        {/* 4 Interactive Portal Cards */}
        <div className="mt-14 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {portals.map((portal) => (
            <div
              key={portal.mode}
              onClick={() => onLaunchMode(portal.mode)}
              className={`cyber-card cursor-pointer p-5 rounded-2xl border transition-all duration-300 hover:-translate-y-1 group ${portal.color}`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 group-hover:border-cyan-500/40 transition-colors">
                  {portal.icon}
                </div>
                <span className="text-[10px] font-mono font-bold tracking-widest px-2 py-0.5 rounded bg-slate-900/90 text-slate-400 border border-slate-800">
                  {portal.badge}
                </span>
              </div>

              <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors flex items-center justify-between">
                <span>{portal.title}</span>
                <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-cyan-400" />
              </h3>

              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                {portal.description}
              </p>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-cyan-400 font-semibold">
                <span>Enter Laboratory</span>
                <span className="text-slate-500">$\rightarrow$</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
