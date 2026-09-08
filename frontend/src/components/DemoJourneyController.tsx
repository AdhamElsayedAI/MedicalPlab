"use client";

import React from "react";
import { CheckCircle2, ChevronRight, ChevronLeft, X, Sparkles, Zap } from "lucide-react";
import { NavigationMode } from "@/lib/types";

export interface DemoStep {
  id: number;
  title: string;
  stage: string;
  description: string;
  targetMode: NavigationMode;
  actionCallout: string;
}

export const DEMO_STEPS: DemoStep[] = [
  {
    id: 1,
    title: "1. Candidate Entry & Tenant Boundary",
    stage: "Stage-G Platform",
    description: "Dr. Alice Vance logs in under NHS Imperial Trust. Tenant boundary isolation and role-based access control are actively enforced.",
    targetMode: "command_center",
    actionCallout: "Inspect student diagnostic profile and weak topics.",
  },
  {
    id: 2,
    title: "2. 3D Anatomy Lab Exploration",
    stage: "Stage-H Lab",
    description: "Navigate the 3D WebGL cardiac model. Rotate and inspect the Left Anterior Descending (LAD) coronary artery hotspot.",
    targetMode: "anatomy",
    actionCallout: "Click the LAD hotspot to reveal clinical significance.",
  },
  {
    id: 3,
    title: "3. Socratic AI Medical Tutor",
    stage: "Stage-D & Stage-F",
    description: "Deep dive into anterior STEMI reperfusion criteria. The conversational mentor engages with Socratic follow-up prompts.",
    targetMode: "tutor",
    actionCallout: "Ask about LAD occlusion and primary PCI delivery targets.",
  },
  {
    id: 4,
    title: "4. Evidence Verification & Citations",
    stage: "Stage-R & Stage-B",
    description: "Inspect the Evidence Grounding Panel. All statements cite verified passages from NICE Guideline NG185 with zero hallucinations.",
    targetMode: "tutor",
    actionCallout: "Click citation [NICE-NG185:Sec 1.2] to read the source quote.",
  },
  {
    id: 5,
    title: "5. Generated Clinical MCQ Engine",
    stage: "Stage-C Generator",
    description: "Attempt an adaptive Single Best Answer clinical scenario with animated timer and instant distractor elimination analysis.",
    targetMode: "quiz",
    actionCallout: "Select option B (Immediate PPCI) to verify clinical rationale.",
  },
  {
    id: 6,
    title: "6. Emergency Resuscitation Sim",
    stage: "Stage-F & Stage-D Safety",
    description: "Manage a deteriorating patient with cardiac tamponade. Live ECG waveform, dynamic vitals, and strict clinical contraindication filtering.",
    targetMode: "simulation",
    actionCallout: "Order bedside ultrasound (POCUS) and avoid contraindicated nitrates.",
  },
  {
    id: 7,
    title: "7. Adaptive Mastery Progression",
    stage: "Stage-E Intelligence",
    description: "Review real-time mastery score update. Accuracy rises to 82% Competent; LAD weakness cleared; attempt saved to Stage-G database.",
    targetMode: "command_center",
    actionCallout: "Review updated mastery radar and cleared weakness.",
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
  const currentStep = DEMO_STEPS[currentStepIndex];
  const isFirst = currentStepIndex === 0;
  const isLast = currentStepIndex === DEMO_STEPS.length - 1;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 w-[95%] max-w-4xl cyber-card p-4 rounded-2xl border border-cyan-400/50 bg-slate-950/95 shadow-[0_0_40px_rgba(0,242,254,0.3)] animate-in fade-in slide-in-from-bottom-6 duration-300">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-cyan-500/20 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 text-white font-bold">
            <Zap className="w-4 h-4 fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white">GUIDED DEMO JOURNEY</span>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-500/40 rounded-full font-bold">
                Step {currentStep.id} of {DEMO_STEPS.length}
              </span>
            </div>
            <span className="text-[11px] font-mono text-cyan-400">
              Active Stage: {currentStep.stage}
            </span>
          </div>
        </div>

        {/* Step dots */}
        <div className="flex items-center gap-1.5 self-center">
          {DEMO_STEPS.map((step, idx) => (
            <button
              key={step.id}
              onClick={() => onSelectStep(idx)}
              className={`h-2 rounded-full transition-all ${
                idx === currentStepIndex
                  ? "w-6 bg-cyan-400 shadow-[0_0_8px_rgba(0,242,254,0.8)]"
                  : idx < currentStepIndex
                  ? "w-2.5 bg-emerald-400"
                  : "w-2.5 bg-slate-700"
              }`}
              title={step.title}
            />
          ))}
        </div>

        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content & Action Callout */}
      <div className="py-2.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h4 className="text-sm font-bold text-cyan-300 flex items-center gap-2">
            <span>{currentStep.title}</span>
          </h4>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            {currentStep.description}
          </p>
          <div className="inline-flex items-center gap-1.5 text-[11px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
            <Sparkles className="w-3 h-3" />
            <span>Action: {currentStep.actionCallout}</span>
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <button
            onClick={() => onSelectStep(currentStepIndex - 1)}
            disabled={isFirst}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 border ${
              isFirst
                ? "text-slate-600 border-slate-800 cursor-not-allowed"
                : "text-slate-300 border-slate-700 hover:bg-slate-800"
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Prev</span>
          </button>

          <button
            onClick={() => onSelectStep(currentStepIndex + 1)}
            disabled={isLast}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1 transition-all ${
              isLast
                ? "bg-emerald-600 text-white cursor-default shadow-[0_0_15px_rgba(0,230,118,0.4)]"
                : "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-[0_0_15px_rgba(0,242,254,0.3)] hover:shadow-[0_0_25px_rgba(0,242,254,0.5)]"
            }`}
          >
            <span>{isLast ? "Tour Complete" : "Next Stage"}</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
