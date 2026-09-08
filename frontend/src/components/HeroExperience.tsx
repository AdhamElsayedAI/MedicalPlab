"use client";

import React, { useState } from "react";
import {
  Stethoscope,
  Layers3,
  HeartPulse,
  ArrowRight,
  ShieldCheck,
  Play,
  BookOpen,
  CheckCircle,
  Sparkles,
  ChevronRight,
  Activity,
  Award,
  Clock,
  Zap,
} from "lucide-react";
import { NavigationMode } from "@/lib/types";

interface HeroExperienceProps {
  onLaunchMode: (mode: NavigationMode) => void;
  onStartDemoJourney: () => void;
  onOpenPipelineModal: () => void;
}

const PREVIEW_MODULES = [
  {
    id: "tutor" as NavigationMode,
    name: "AI Clinical Preceptor",
    tagline: "Socratic Clinical Reasoning",
    icon: <Stethoscope className="w-4 h-4 text-sky-400" />,
    badgeColor: "rgba(14,165,233,0.15)",
    badgeText: "#38bdf8",
    accentColor: "#38bdf8",
    vignette: "58-year-old male with acute retrosternal chest pain radiating to the left jaw. Onset 45 minutes ago.",
    aiResponse: "Under NICE NG185, first-line management requires immediate 12-lead ECG, high-sensitivity Troponin-I, and oxygen titration (target 94-98%). What is your top differential before administering antiplatelet therapy?",
    evidenceCitation: "NICE NG185 · Acute Coronary Syndromes (Sec 1.2)",
  },
  {
    id: "anatomy" as NavigationMode,
    name: "3D Spatial Anatomy",
    tagline: "Pathology-Linked 3D Exploration",
    icon: <Layers3 className="w-4 h-4 text-purple-400" />,
    badgeColor: "rgba(168,85,247,0.15)",
    badgeText: "#c084fc",
    accentColor: "#a855f7",
    vignette: "Left Anterior Descending (LAD) Artery & Anterolateral Myocardium",
    aiResponse: "Occlusion of the proximal LAD compromises anterior ventricular perfusion, precipitating ST-segment elevation in leads V1-V4 and loss of apical kinetic function.",
    evidenceCitation: "Clinical Anatomy Correlation · Anterior Wall Infarction",
  },
  {
    id: "simulation" as NavigationMode,
    name: "Emergency Simulation",
    tagline: "Dynamic Resuscitation & Live Vitals",
    icon: <HeartPulse className="w-4 h-4 text-emerald-400" />,
    badgeColor: "rgba(34,197,94,0.15)",
    badgeText: "#4ade80",
    accentColor: "#22c55e",
    vignette: "Bedside Monitor: Sinus Tachycardia (118 bpm) · BP 88/60 mmHg · Pulsus Paradoxus",
    aiResponse: "Patient exhibits Beck's Triad (Hypotension, Distended Neck Veins, Muffled Heart Sounds). Autonomous safety check: Nitrates contraindicated. Immediate bedside echocardiogram and pericardiocentesis indicated.",
    evidenceCitation: "Resuscitation Council UK · Hemodynamic Tamponade Protocol",
  },
];

const COMPARISON_ROWS = [
  {
    feature: "Learning Methodology",
    traditional: "Static 2D multiple-choice question memorization",
    medicalPlab: "Interactive Socratic preceptor guiding clinical hypotheses",
  },
  {
    feature: "Anatomical Context",
    traditional: "Flat textbook diagrams disconnected from clinical vignettes",
    medicalPlab: "Interactive 3D spatial models connected directly to pathology & exam pearls",
  },
  {
    feature: "Acute Care Training",
    traditional: "Theoretical MCQ questions without time or physiological feedback",
    medicalPlab: "Realistic emergency resuscitation bay with dynamic ECG, vitals & safety alerts",
  },
  {
    feature: "AI Evidence Safety",
    traditional: "Ungrounded, black-box chatbots prone to clinical hallucinations",
    medicalPlab: "Zero-hallucination engine with exact extractive citations from NICE & BNF",
  },
];

export const HeroExperience: React.FC<HeroExperienceProps> = ({
  onLaunchMode,
  onStartDemoJourney,
}) => {
  const [activePreviewIdx, setActivePreviewIdx] = useState(0);
  const activePreview = PREVIEW_MODULES[activePreviewIdx];

  return (
    <div className="relative overflow-hidden" aria-label="MedicalPlab Hero Experience">
      {/* Background ambient glow */}
      <div className="absolute inset-0 pointer-events-none hero-mesh opacity-75" />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.035) 1px, transparent 0)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 lg:pt-24 lg:pb-24">
        {/* ── Top Category Tag ── */}
        <div className="flex items-center justify-center mb-6">
          <div
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[12px] font-medium transition-all"
            style={{
              background: "rgba(14,165,233,0.08)",
              border: "1px solid rgba(14,165,233,0.25)",
              color: "#7dd3fc",
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400 inline-block animate-pulse" />
            AI-Powered Medical Learning &amp; Clinical Reasoning Platform
            <ChevronRight className="w-3.5 h-3.5 text-sky-400" />
          </div>
        </div>

        {/* ── Hero Headline ── */}
        <div className="text-center max-w-4xl mx-auto">
          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.12]"
            style={{
              fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif",
              letterSpacing: "-0.035em",
            }}
          >
            Master Clinical{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #34d399 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Reasoning
            </span>{" "}
            with Evidence-Grounded AI
          </h1>

          <p
            className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed"
            style={{ fontFamily: "'Inter', sans-serif" }}
          >
            MedicalPlab transforms medical licensing and clinical preparation from rote memorization
            into measurable diagnostic competence through Socratic guidance, 3D spatial anatomy, and
            realistic emergency resuscitation simulations.
          </p>

          {/* ── Primary Action Buttons ── */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onStartDemoJourney}
              className="btn-primary text-[14px] font-bold px-7 py-3.5 rounded-xl w-full sm:w-auto shadow-lg flex items-center justify-center gap-2"
              id="hero-launch-demo-primary"
            >
              <Play className="w-4 h-4 fill-current ml-0.5" />
              Launch Guided Demo (3-Min Tour)
            </button>

            <button
              onClick={() => onLaunchMode("command_center")}
              className="btn-secondary text-[14px] font-semibold px-6 py-3.5 rounded-xl w-full sm:w-auto flex items-center justify-center gap-2"
              id="hero-start-learning-sec"
            >
              <span>Explore Student Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* ── 4-Step Core Story: Learn -> Reason -> Simulate -> Improve ── */}
          <div className="mt-8 p-3 rounded-2xl bg-slate-900/90 border border-slate-800/80 max-w-3xl mx-auto shadow-sm">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
              The Clinical Mastery Journey
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <button
                onClick={() => onLaunchMode("anatomy")}
                className="p-2 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-sky-500/30 text-left transition-all group"
              >
                <div className="text-[10px] font-bold text-sky-400">1. LEARN</div>
                <div className="font-semibold text-slate-200 group-hover:text-white mt-0.5">3D Spatial Anatomy</div>
              </button>

              <button
                onClick={() => onLaunchMode("tutor")}
                className="p-2 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-purple-500/30 text-left transition-all group"
              >
                <div className="text-[10px] font-bold text-purple-400">2. REASON</div>
                <div className="font-semibold text-slate-200 group-hover:text-white mt-0.5">Socratic Preceptor</div>
              </button>

              <button
                onClick={() => onLaunchMode("simulation")}
                className="p-2 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-emerald-500/30 text-left transition-all group"
              >
                <div className="text-[10px] font-bold text-emerald-400">3. SIMULATE</div>
                <div className="font-semibold text-slate-200 group-hover:text-white mt-0.5">Resuscitation Bay</div>
              </button>

              <button
                onClick={() => onLaunchMode("command_center")}
                className="p-2 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-amber-500/30 text-left transition-all group"
              >
                <div className="text-[10px] font-bold text-amber-400">4. IMPROVE</div>
                <div className="font-semibold text-slate-200 group-hover:text-white mt-0.5">Adaptive Telemetry</div>
              </button>
            </div>
          </div>

          {/* ── Transparent Claims Separation: Verified / Prototype / Projection ── */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-[11px]">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/40 text-emerald-300 border border-emerald-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <strong>Verified:</strong> NICE &amp; BNF Clinical Corpus
            </span>
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-950/40 text-sky-300 border border-sky-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <strong>Prototype:</strong> 3D Anatomy &amp; Acute Sim
            </span>
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-950/40 text-purple-300 border border-purple-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              <strong>Projection:</strong> Learning Delta &amp; TAM Models
            </span>
          </div>

          {/* Medical Education Disclaimer */}
          <div className="mt-3 text-[11px] text-slate-500 italic max-w-xl mx-auto">
            Educational simulation platform for licensing revision. Curriculum aligned with UK GMC PLAB &amp; UKMLA standards. Not for direct patient diagnosis.
          </div>
        </div>

        {/* ── Interactive Live Feature Preview ── */}
        <div className="mt-16 max-w-4xl mx-auto">
          <div className="text-center mb-5">
            <h2
              className="text-lg font-bold text-white tracking-tight"
              style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
            >
              Explore the Clinical Learning Workflow
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Select a module below to preview the clinical intelligence engine in action.
            </p>
          </div>

          {/* Module Selector Tabs */}
          <div className="flex items-center justify-center gap-2 p-1.5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur max-w-xl mx-auto mb-6">
            {PREVIEW_MODULES.map((module, idx) => (
              <button
                key={module.id}
                onClick={() => setActivePreviewIdx(idx)}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-semibold transition-all ${
                  activePreviewIdx === idx
                    ? "bg-slate-800 text-white shadow-sm border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {module.icon}
                <span>{module.name}</span>
              </button>
            ))}
          </div>

          {/* Interactive Preview Card */}
          <div
            className="med-card p-6 md:p-8 rounded-2xl transition-all"
            style={{
              border: `1px solid ${activePreview.accentColor}33`,
              background: "rgba(15, 23, 42, 0.75)",
            }}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 mb-5 border-b border-slate-800">
              <div>
                <span
                  className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-bold mb-1.5"
                  style={{ background: activePreview.badgeColor, color: activePreview.badgeText }}
                >
                  {activePreview.tagline}
                </span>
                <h3
                  className="text-lg font-bold text-white"
                  style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
                >
                  {activePreview.name}
                </h3>
              </div>

              <button
                onClick={() => onLaunchMode(activePreview.id)}
                className="btn-primary text-xs font-bold px-4 py-2 rounded-lg self-start md:self-auto flex items-center gap-1.5"
              >
                <span>Launch Interactive Module</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
                  Clinical Vignette Context
                </span>
                <p className="text-slate-200 text-sm font-medium leading-relaxed">
                  {activePreview.vignette}
                </p>
              </div>

              <div
                className="p-4 rounded-xl space-y-2"
                style={{
                  background: "rgba(14, 165, 233, 0.04)",
                  border: "1px solid rgba(14, 165, 233, 0.15)",
                }}
              >
                <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block">
                  Clinical Preceptor Reasoning
                </span>
                <p className="text-slate-300 text-[13px] leading-relaxed">
                  {activePreview.aiResponse}
                </p>
                <div className="flex items-center gap-1.5 pt-2 text-[11px] text-sky-400 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Verified: {activePreview.evidenceCitation}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Clinical Comparison Matrix ── */}
        <div className="mt-20 max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2
              className="text-xl sm:text-2xl font-bold text-white tracking-tight"
              style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
            >
              Why Medical Education Needs Clinical Intelligence
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-2 max-w-xl mx-auto">
              Moving beyond static question banks toward verified clinical reasoning and patient safety.
            </p>
          </div>

          <div className="med-card overflow-hidden rounded-2xl border border-slate-800">
            <div className="grid grid-cols-12 bg-slate-900/90 px-5 py-3 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <div className="col-span-3 sm:col-span-3">Core Capability</div>
              <div className="col-span-4 sm:col-span-4 text-slate-500">Traditional Question Banks</div>
              <div className="col-span-5 sm:col-span-5 text-sky-400">MedicalPlab AI Platform</div>
            </div>

            <div className="divide-y divide-slate-800/60">
              {COMPARISON_ROWS.map((row, i) => (
                <div key={i} className="grid grid-cols-12 px-5 py-4 text-xs items-center gap-2">
                  <div className="col-span-3 sm:col-span-3 font-semibold text-slate-200">
                    {row.feature}
                  </div>
                  <div className="col-span-4 sm:col-span-4 text-slate-400 leading-relaxed">
                    {row.traditional}
                  </div>
                  <div className="col-span-5 sm:col-span-5 text-sky-200 font-medium leading-relaxed">
                    {row.medicalPlab}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Academic / Curriculum Note */}
          <div className="mt-4 text-center">
            <span className="text-[11px] text-slate-500 italic">
              Demonstration &amp; education platform. Designed to complement medical school teaching
              and licensing exam revision.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
