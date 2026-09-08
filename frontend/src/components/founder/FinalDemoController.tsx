"use client";

import React, { useState, useEffect } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Zap,
  Activity,
  Layers,
  GraduationCap,
  ShieldCheck,
  Building2,
  Lock,
  ArrowRight,
} from "lucide-react";
import { NavigationMode } from "@/lib/types";

export interface HackathonDemoScene {
  id: number;
  title: string;
  stageBadge: string;
  durationSeconds: number;
  targetMode: NavigationMode;
  tagline: string;
  description: string;
  presenterAction: string;
  keyMoatHighlighted: string;
}

export const HACKATHON_DEMO_SCENES: HackathonDemoScene[] = [
  {
    id: 1,
    title: "Scene 1: The Medical Education Crisis",
    stageBadge: "Market Crisis",
    durationSeconds: 30,
    targetMode: "landing",
    tagline: "45,000 international doctors, 42% failure rate, static question banks.",
    description:
      "Open on the high-stakes problem: doctors spend thousands on disconnected flashcards, and ungrounded LLMs invent fatal clinical dosages.",
    presenterAction: "Highlight the 42% failure bottleneck and the need for evidence-grounded AI.",
    keyMoatHighlighted: "Clinical Urgency & High-Stakes Exam Pain",
  },
  {
    id: 2,
    title: "Scene 2: The MedicalPlab Ecosystem",
    stageBadge: "Stage-G Platform",
    durationSeconds: 30,
    targetMode: "command_center",
    tagline: "Integrated diagnostic hub under NHS Imperial Trust tenant boundary.",
    description:
      "Demonstrate candidate entry into the digital laboratory: real-time mastery vectors across 14 specialties and tenant data isolation.",
    presenterAction: "Point out Alice's diagnostic profile and the highlighted Left Anterior Descending (LAD) weakness.",
    keyMoatHighlighted: "Enterprise Multi-Tenancy & Student Intelligence",
  },
  {
    id: 3,
    title: "Scene 3: 3D Spatial Anatomy Experience",
    stageBadge: "Stage-H Lab",
    durationSeconds: 40,
    targetMode: "anatomy",
    tagline: "Doctors think spatially. Interactive 3D coronary tree with diagnostic hotspots.",
    description:
      "Rotate the 3D cardiac organ model. Click the LAD hotspot to reveal clinical significance, hemodynamic risk, and bridge into Socratic tutoring.",
    presenterAction: "Click the LAD coronary artery hotspot and click 'Consult AI Tutor'.",
    keyMoatHighlighted: "Spatial WebGL Anatomy-to-Clinical Reasoning Bridge",
  },
  {
    id: 4,
    title: "Scene 4: Socratic AI Medical Tutor",
    stageBadge: "Stage-D Reasoning",
    durationSeconds: 40,
    targetMode: "tutor",
    tagline: "Conversational pedagogical mentor that asks probing diagnostic questions.",
    description:
      "Prompt the AI on acute coronary syndrome. The tutor responds Socratically, building clinical acumen rather than regurgitating answers.",
    presenterAction: "Ask about LAD occlusion and primary PCI delivery targets under 120 minutes.",
    keyMoatHighlighted: "Socratic Clinical Pedagogy",
  },
  {
    id: 5,
    title: "Scene 5: Zero-Hallucination Evidence Verification",
    stageBadge: "Stage-B & Stage-R",
    durationSeconds: 40,
    targetMode: "tutor",
    tagline: "Every token mathematically verified against NICE NG185 & BNF monographs.",
    description:
      "Open the interactive Evidence Provenance Panel. Show the 98.6% confidence score and exact clause quote. Unsupported claims are dropped.",
    presenterAction: "Click citation [NICE-NG185:Sec 1.2] to reveal the source quote.",
    keyMoatHighlighted: "Mathematical Claim Provenance (0.0% Hallucinations)",
  },
  {
    id: 6,
    title: "Scene 6: Clinical Emergency Resuscitation Sim",
    stageBadge: "Stage-D Safety Interceptor",
    durationSeconds: 45,
    targetMode: "simulation",
    tagline: "Dynamic patient physiology, live ECG strip, and lethal contraindication blocker.",
    description:
      "Patient in cardiac tamponade. Attempting to administer Nitrates triggers an immediate autonomous block by Stage-D Safety Interceptor.",
    presenterAction: "Select sublingual nitrates to demonstrate the safety interceptor blocking lethal harm.",
    keyMoatHighlighted: "Autonomous Real-Time Clinical Safety Interceptor",
  },
  {
    id: 7,
    title: "Scene 7: Adaptive Bayesian Mastery Update",
    stageBadge: "Stage-E Intelligence",
    durationSeconds: 30,
    targetMode: "command_center",
    tagline: "Real-time Bayesian knowledge tracing updates competency to 82% Competent.",
    description:
      "Student profile dynamically reflects mastery progression: LAD topic weakness cleared, overall competency elevated, attempt logged.",
    presenterAction: "Show the updated diagnostic radar and the cleared weak topic list.",
    keyMoatHighlighted: "Bayesian Knowledge Tracing & Dynamic Difficulty",
  },
  {
    id: 8,
    title: "Scene 8: Business Vision & Investor Horizon",
    stageBadge: "Series Seed Round",
    durationSeconds: 45,
    targetMode: "investor",
    tagline: "$4.8B TAM, 94% gross margin at $0.0039/session, £18k NHS Deanery licenses.",
    description:
      "Close on the commercial opportunity: dual B2C/B2B engine, proven CPU unit economics, and roadmap to universal clinical decision companion.",
    presenterAction: "Display the $4.8B TAM, NHS Trust pipeline, and seed investment thesis.",
    keyMoatHighlighted: "Scalable B2B/B2C SaaS with 94% Software Gross Margin",
  },
];

interface FinalDemoControllerProps {
  onNavigateToScene: (mode: NavigationMode) => void;
  isOfflineMode: boolean;
  onToggleOfflineMode: () => void;
}

export const FinalDemoController: React.FC<FinalDemoControllerProps> = ({
  onNavigateToScene,
  isOfflineMode,
  onToggleOfflineMode,
}) => {
  const [currentSceneIdx, setCurrentSceneIdx] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [sceneSecondsRemaining, setSceneSecondsRemaining] = useState(
    HACKATHON_DEMO_SCENES[0].durationSeconds
  );

  const scene = HACKATHON_DEMO_SCENES[currentSceneIdx];
  const totalScenes = HACKATHON_DEMO_SCENES.length;

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isAutoPlaying) {
      timer = setInterval(() => {
        setSceneSecondsRemaining((prev) => {
          if (prev <= 1) {
            // Auto advance
            if (currentSceneIdx < totalScenes - 1) {
              const nextIdx = currentSceneIdx + 1;
              setCurrentSceneIdx(nextIdx);
              onNavigateToScene(HACKATHON_DEMO_SCENES[nextIdx].targetMode);
              return HACKATHON_DEMO_SCENES[nextIdx].durationSeconds;
            } else {
              setIsAutoPlaying(false);
              return 0;
            }
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isAutoPlaying, currentSceneIdx, totalScenes, onNavigateToScene]);

  const goToScene = (idx: number) => {
    setCurrentSceneIdx(idx);
    setSceneSecondsRemaining(HACKATHON_DEMO_SCENES[idx].durationSeconds);
    onNavigateToScene(HACKATHON_DEMO_SCENES[idx].targetMode);
  };

  const nextScene = () => {
    if (currentSceneIdx < totalScenes - 1) {
      goToScene(currentSceneIdx + 1);
    }
  };

  const prevScene = () => {
    if (currentSceneIdx > 0) {
      goToScene(currentSceneIdx - 1);
    }
  };

  const resetFlow = () => {
    setIsAutoPlaying(false);
    goToScene(0);
  };

  return (
    <div className="space-y-6">
      {/* Top Controller Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-[0_0_20px_rgba(0,242,254,0.3)]">
            <Zap className="w-5 h-5 fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-extrabold text-base text-white tracking-wide">
                HACKATHON FINAL DEMO CONTROLLER
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-cyan-950 text-cyan-300 border border-cyan-500/40">
                8-Scene Flow
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              One-click orchestrated narrative: Problem $\rightarrow$ Product $\rightarrow$ Anatomy $\rightarrow$ Tutor $\rightarrow$ Verification $\rightarrow$ Simulation $\rightarrow$ Adaptive $\rightarrow$ Vision.
            </p>
          </div>
        </div>

        {/* Presenter Auto-Play & Offline Toggle */}
        <div className="flex items-center gap-3 self-start md:self-center">
          {/* Offline Fallback Toggle */}
          <button
            onClick={onToggleOfflineMode}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono border transition-all ${
              isOfflineMode
                ? "bg-emerald-950/80 border-emerald-500/50 text-emerald-300 shadow-[0_0_10px_rgba(16,185,129,0.2)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
            title="Toggle between live Stage-G REST API and 100% preloaded offline fallback"
          >
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>{isOfflineMode ? "Offline Fallback ON" : "Live API Mode"}</span>
          </button>

          {/* Auto-Play Toggle */}
          <button
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-mono font-bold border transition-all ${
              isAutoPlaying
                ? "bg-amber-950/80 border-amber-500/50 text-amber-300"
                : "bg-cyan-950/80 border-cyan-400/50 text-cyan-300 shadow-[0_0_15px_rgba(0,242,254,0.2)]"
            }`}
          >
            {isAutoPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>{isAutoPlaying ? "Pause Auto-Flow" : "Auto-Play Demo"}</span>
          </button>

          <button
            onClick={resetFlow}
            className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 transition-colors"
            title="Reset demo to Scene 1"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Scene Spotlight Card */}
      <div className="rounded-3xl p-6 sm:p-8 bg-gradient-to-b from-slate-950 via-[#060b18] to-slate-950 border-2 border-cyan-500/30 shadow-[0_0_40px_rgba(0,242,254,0.15)] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-500/40 uppercase">
                {scene.stageBadge}
              </span>
              <span className="text-xs font-mono text-slate-400">
                Scene {scene.id} of {totalScenes}
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-wide">
              {scene.title}
            </h2>
            <p className="text-xs sm:text-sm text-cyan-200/80 font-sans mt-0.5">
              {scene.tagline}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-right font-mono">
              <span className="text-[10px] text-slate-400 block">SCENE TIMER</span>
              <span className="text-lg font-bold text-cyan-300">
                {sceneSecondsRemaining}s
              </span>
            </div>

            <button
              onClick={() => onNavigateToScene(scene.targetMode)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/25 hover:scale-[1.02] transition-transform"
            >
              <span>Launch Live View</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Scene Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1.5">
            <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">
              Narrative Objective
            </span>
            <p className="text-xs sm:text-sm text-slate-200 font-sans leading-relaxed">
              {scene.description}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/80 border border-cyan-500/20 space-y-1.5">
            <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
              Presenter Action Callout
            </span>
            <p className="text-xs sm:text-sm text-cyan-100 font-sans leading-relaxed">
              {scene.presenterAction}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/80 border border-purple-500/20 space-y-1.5">
            <span className="text-[10px] font-mono text-purple-400 uppercase font-bold block">
              Defensible Moat Proven
            </span>
            <p className="text-xs sm:text-sm text-purple-200 font-sans leading-relaxed">
              {scene.keyMoatHighlighted}
            </p>
          </div>
        </div>

        {/* Stepper Dots & Navigation */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-800 pt-5">
          <button
            onClick={prevScene}
            disabled={currentSceneIdx === 0}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentSceneIdx === 0
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-slate-300 bg-slate-900 hover:bg-slate-800 hover:text-white border border-slate-700"
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Prev Scene</span>
          </button>

          {/* Stepper Timeline */}
          <div className="flex items-center gap-2 overflow-x-auto py-1">
            {HACKATHON_DEMO_SCENES.map((sc, idx) => (
              <button
                key={sc.id}
                onClick={() => goToScene(idx)}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
                  idx === currentSceneIdx
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400 shadow-[0_0_12px_rgba(0,242,254,0.3)]"
                    : idx < currentSceneIdx
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
            disabled={currentSceneIdx === totalScenes - 1}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentSceneIdx === totalScenes - 1
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
