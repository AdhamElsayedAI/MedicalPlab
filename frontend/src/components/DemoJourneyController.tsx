"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  X,
  Sparkles,
  Play,
  RotateCcw,
  ShieldCheck,
  Stethoscope,
  Layers3,
  HeartPulse,
  Award,
  TrendingUp,
  HelpCircle,
  Clock,
  ArrowRight,
} from "lucide-react";
import { NavigationMode } from "@/lib/types";

export interface DemoStep {
  id: number;
  title: string;
  category: string;
  stage: string;
  description: string;
  targetMode: NavigationMode;
  actionCallout: string;
  keyHighlight: string;
}

export const DEMO_STEPS: DemoStep[] = [
  {
    id: 1,
    title: "1. Reason: Socratic AI Clinical Preceptor",
    category: "Clinical Reasoning",
    stage: "Reason",
    description:
      "Flagship STEMI Case: 58M with crushing retrosternal pain. The AI preceptor synthesizes a Problem Representation, ranks differentials, and specifies NICE NG185 diagnostics without hallucination.",
    targetMode: "tutor",
    actionCallout: "Review Problem Representation & Differentials (LAD STEMI vs Aortic Dissection).",
    keyHighlight: "Socratic Guidance & Zero-Hallucination Grounding",
  },
  {
    id: 2,
    title: "2. Explore: 3D Spatial Anatomy Lab",
    category: "Spatial Pathology",
    stage: "Explore",
    description:
      "Seamless anatomical transition: Inspect the Left Anterior Descending (LAD) coronary artery in 3D WebGL. Follow the 4-phase workflow connecting vascular occlusion to precordial leads V1-V4.",
    targetMode: "anatomy",
    actionCallout: "Inspect LAD artery in 3D and review Pathophysiology & Exam Prep.",
    keyHighlight: "4-Phase Pedagogical Workflow (Spatial → Pathology)",
  },
  {
    id: 3,
    title: "3. Simulate: Emergency Resuscitation Bay",
    category: "Acute Resuscitation",
    stage: "Simulate",
    description:
      "Manage the acute STEMI in the resuscitation bay. Execute ABCDE orders with live ECG rhythm, and test the Autonomous Safety Interceptor by attempting contraindicated thrombolysis.",
    targetMode: "simulation",
    actionCallout: "Order 12-lead ECG, Dual Antiplatelets (DAPT), and Urgent PPCI activation.",
    keyHighlight: "Live ECG Waveform & Autonomous Contraindication Safety Filter",
  },
  {
    id: 4,
    title: "4. Verify: Extractive Evidence Provenance",
    category: "Patient Safety & Compliance",
    stage: "Verify",
    description:
      "Audit the clinical evidence layer. Every recommendation contains exact extractive provenance from NICE Guideline NG185 Section 1.2 and BNF 85 with zero hallucinations.",
    targetMode: "tutor",
    actionCallout: "Inspect citation chips to verify authoritative medical quotes.",
    keyHighlight: "100% Extractive Guideline Provenance (NICE NG185 / BNF 85)",
  },
  {
    id: 5,
    title: "Closing: Scalability & Investor Briefing",
    category: "Institutional Impact",
    stage: "Impact",
    description:
      "Scalable multi-tenant architecture designed for NHS Foundation Trusts and global medical faculties ($4.8B TAM model, <$0.01 inference unit economics).",
    targetMode: "investor",
    actionCallout: "Review market opportunity ($4.8B TAM), unit economics, and licensing roadmap.",
    keyHighlight: "Scalable SaaS Architecture for Healthcare Education",
  },
];

interface DemoJourneyControllerProps {
  currentStepIndex: number;
  onSelectStep: (index: number) => void;
  onClose: () => void;
}

export const DemoJourneyController: React.FC<DemoJourneyControllerProps> = ({
  currentStepIndex,
  onSelectStep,
  onClose,
}) => {
  const [isOpeningModalOpen, setIsOpeningModalOpen] = useState(currentStepIndex === 0);

  const currentStep = DEMO_STEPS[currentStepIndex] || DEMO_STEPS[0];
  const isFirst = currentStepIndex === 0;
  const isLast = currentStepIndex === DEMO_STEPS.length - 1;

  const handleStartEvaluation = () => {
    setIsOpeningModalOpen(false);
    onSelectStep(0);
  };

  const handleResetDemo = () => {
    onSelectStep(0);
    setIsOpeningModalOpen(true);
  };

  return (
    <>
      {/* ── Demo Opening Screen: 3-Minute Clinical Intelligence Experience ── */}
      {isOpeningModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div
            className="med-card w-full max-w-2xl rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6"
            style={{ background: "#0b1120", border: "1px solid rgba(56, 189, 248, 0.35)" }}
          >
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-500/15 text-sky-300 border border-sky-500/30 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                    Championship Demo Mode
                  </span>
                  <span className="text-[11px] text-emerald-400 font-medium">Offline-Safe Preloaded</span>
                </div>
                <h2
                  className="text-xl sm:text-2xl font-extrabold text-white tracking-tight"
                  style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
                >
                  MedicalPlab 3-Minute Clinical Intelligence Experience
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Flagship Scenario: <strong className="text-sky-300">58-Year-Old Male with Acute Retrosternal Chest Pain (Anterior STEMI)</strong>
                </p>
              </div>

              <button
                onClick={() => setIsOpeningModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 4-Stage Pathway Overview */}
            <div className="space-y-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                The 4-Stage Clinical Journey:
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-sky-500/15 text-sky-400 flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                    1
                  </div>
                  <div>
                    <span className="font-bold text-sky-300 block">REASON: AI Preceptor</span>
                    <span className="text-slate-400 text-[11px]">Problem Representation, ranked differentials &amp; NICE NG185 workup.</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-purple-500/15 text-purple-400 flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                    2
                  </div>
                  <div>
                    <span className="font-bold text-purple-300 block">EXPLORE: 3D Anatomy</span>
                    <span className="text-slate-400 text-[11px]">LAD coronary occlusion mapped to transmural anterior ischemia.</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                    3
                  </div>
                  <div>
                    <span className="font-bold text-emerald-300 block">SIMULATE: Resuscitation Bay</span>
                    <span className="text-slate-400 text-[11px]">Live ECG, DAPT, urgent PPCI &amp; Safety Filter interception.</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-amber-500/15 text-amber-400 flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                    4
                  </div>
                  <div>
                    <span className="font-bold text-amber-300 block">VERIFY: Evidence Provenance</span>
                    <span className="text-slate-400 text-[11px]">Extractive guideline verification with zero hallucinations.</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Launch CTA */}
            <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                <span>Estimated Evaluation Time: Exactly 3 Minutes</span>
              </div>

              <button
                onClick={handleStartEvaluation}
                className="btn-primary text-xs font-bold px-6 py-2.5 rounded-xl flex items-center gap-2 w-full sm:w-auto justify-center shadow-lg"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Begin 3-Minute Evaluation</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Floating Executive Stepper Dock ── */}
      <aside
        className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40 w-[95%] max-w-4xl rounded-2xl shadow-2xl overflow-hidden med-fade-in"
        style={{
          background: "rgba(11, 17, 32, 0.96)",
          border: "1px solid rgba(56, 189, 248, 0.35)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(14, 165, 233, 0.15)",
        }}
        aria-label="3-Minute Demo Stepper"
      >
        {/* Top Header Bar */}
        <div
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 px-5 py-2.5"
          style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="flex items-center justify-center w-7 h-7 rounded-lg flex-shrink-0"
              style={{
                background: "linear-gradient(135deg, #0ea5e9, #2563eb)",
                color: "#ffffff",
                boxShadow: "0 0 12px rgba(14, 165, 233, 0.4)",
              }}
            >
              <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span
                  className="font-bold text-[12px] text-white tracking-tight"
                  style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
                >
                  3-MINUTE JUDGE DEMO
                </span>
                <span
                  className="px-2 py-0.5 text-[10px] font-semibold rounded-full"
                  style={{
                    background: "rgba(14, 165, 233, 0.15)",
                    color: "#7dd3fc",
                    border: "1px solid rgba(14, 165, 233, 0.3)",
                  }}
                >
                  Step {currentStep.id} of {DEMO_STEPS.length}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Jump Buttons for Stages */}
          <div className="flex items-center gap-1.5 self-center overflow-x-auto">
            {DEMO_STEPS.map((step, idx) => (
              <button
                key={step.id}
                onClick={() => onSelectStep(idx)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all flex items-center gap-1 ${
                  idx === currentStepIndex
                    ? "bg-sky-500/25 text-sky-300 border border-sky-400/40 shadow-sm"
                    : idx < currentStepIndex
                    ? "text-emerald-400 hover:bg-emerald-500/10"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                title={step.title}
              >
                {idx < currentStepIndex && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                <span>{step.stage}</span>
              </button>
            ))}
          </div>

          {/* Controls: Reset Demo & Close */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleResetDemo}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors flex items-center gap-1 text-[11px]"
              title="Reset Demo to Step 1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset</span>
            </button>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              title="Exit Tour"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content & Action Callout */}
        <div className="px-5 py-3 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1 flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4
                className="text-[13px] font-bold text-white leading-tight"
                style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
              >
                {currentStep.title}
              </h4>
              <span
                className="hidden lg:inline-block px-2 py-0.5 rounded text-[10px] font-semibold"
                style={{ background: "rgba(34, 197, 94, 0.12)", color: "#86efac" }}
              >
                {currentStep.keyHighlight}
              </span>
            </div>
            <p className="text-[11px] text-slate-300 max-w-2xl leading-relaxed">
              {currentStep.description}
            </p>
            <div
              className="inline-flex items-center gap-1.5 text-[10px] font-medium px-2 py-0.5 rounded-lg"
              style={{
                background: "rgba(14, 165, 233, 0.08)",
                color: "#38bdf8",
                border: "1px solid rgba(14, 165, 233, 0.2)",
              }}
            >
              <Sparkles className="w-3 h-3 text-sky-400 flex-shrink-0" />
              <span>Recommended Action: {currentStep.actionCallout}</span>
            </div>
          </div>

          {/* Navigation Actions */}
          <div className="flex items-center gap-2 w-full md:w-auto justify-end flex-shrink-0">
            <button
              onClick={() => onSelectStep(currentStepIndex - 1)}
              disabled={isFirst}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 transition-all ${
                isFirst
                  ? "text-slate-600 border border-slate-800/60 cursor-not-allowed"
                  : "text-slate-300 border border-slate-700 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <button
              onClick={() => onSelectStep(currentStepIndex + 1)}
              disabled={isLast}
              className={`px-4 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                isLast
                  ? "bg-emerald-600 text-white cursor-default shadow-md"
                  : "btn-primary shadow-lg"
              }`}
            >
              <span>{isLast ? "Tour Complete" : "Next Stage"}</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
