"use client";

import React from "react";
import type { ReasoningTimelineItem } from "@/lib/types";
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Lightbulb,
  ArrowDown,
  Sparkles,
  ShieldAlert,
  GraduationCap,
  Compass,
  Hourglass,
} from "lucide-react";

interface ReasoningTimelineCardProps {
  timeline: ReasoningTimelineItem;
  strategy?: string;
  turnNumber?: number;
  maxTurns?: number;
  remediationStatus?: string;
  isComplete?: boolean;
}

export function ReasoningTimelineCard({
  timeline,
  strategy,
  turnNumber = 1,
  maxTurns = 3,
  remediationStatus = "PROBING",
  isComplete = false,
}: ReasoningTimelineCardProps) {
  const isTransferConfirmed =
    timeline.status === "COMPLETED" ||
    (timeline.transfer_result && timeline.transfer_result.includes("Transfer demonstrated"));
  const isAwaitingTransfer = timeline.status === "AWAITING_TRANSFER";
  const isUnresolved = timeline.status === "UNRESOLVED";
  const isSafetyFallback = timeline.status === "SAFETY_FALLBACK";

  return (
    <div className="rounded-xl border border-indigo-500/20 bg-gradient-to-b from-slate-900/95 to-slate-950/95 p-5 shadow-xl backdrop-blur-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 mb-4 gap-2">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
            <BrainCircuit className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Reasoning Progression Timeline
              <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            </h4>
            <p className="text-xs text-slate-400">
              Hypothesis-driven cognitive remediation and independent transfer measurement
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div>
          {isTransferConfirmed ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Transfer Demonstrated
            </span>
          ) : isAwaitingTransfer ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300 border border-indigo-500/30 animate-pulse">
              <Hourglass className="h-3.5 w-3.5" />
              Awaiting Transfer Assessment
            </span>
          ) : isSafetyFallback ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-3 py-1 text-xs font-medium text-rose-300 border border-rose-500/30">
              <ShieldAlert className="h-3.5 w-3.5" />
              Safety Fallback Active
            </span>
          ) : isUnresolved ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300 border border-amber-500/20">
              <AlertCircle className="h-3.5 w-3.5" />
              More Practice Needed
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-300 border border-sky-500/20">
              <Lightbulb className="h-3.5 w-3.5" />
              {remediationStatus} (Turn {turnNumber}/{maxTurns})
            </span>
          )}
        </div>
      </div>

      {/* 5-Stage Visual Progression */}
      <div className="space-y-3">
        {/* Stage 1: Initial Answer & Flawed Premise */}
        <div className="flex items-start gap-3 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-amber-400">
            <AlertCircle className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">
                1. Initial Observed Choice
              </span>
              <span className="text-[10px] text-amber-400/70 font-mono">Original Attempt</span>
            </div>
            <p className="mt-1 text-xs text-slate-200 leading-relaxed">
              {timeline.initial_pattern}
            </p>
          </div>
        </div>

        <div className="flex justify-center -my-1 text-slate-600">
          <ArrowDown className="h-3.5 w-3.5" />
        </div>

        {/* Stage 2: Suspected Learning Gap (Hypothesis) */}
        <div className="flex items-start gap-3 rounded-lg border border-sky-500/20 bg-sky-500/5 p-3">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-500/20 text-sky-400">
            <Lightbulb className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-sky-400">
                2. Suspected Learning Gap
              </span>
              {strategy && (
                <span className="rounded bg-sky-500/10 px-2 py-0.5 text-[10px] font-mono text-sky-300 border border-sky-500/20">
                  {strategy}
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-slate-200 leading-relaxed">
              {timeline.learning_gap}
            </p>
          </div>
        </div>

        <div className="flex justify-center -my-1 text-slate-600">
          <ArrowDown className="h-3.5 w-3.5" />
        </div>

        {/* Stage 3: Guided Socratic Remediation */}
        <div className="flex items-start gap-3 rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-3">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400">
            <BrainCircuit className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                3. Guided Practice Progress
              </span>
              <span className="text-[10px] text-indigo-400/70 font-mono">
                {turnNumber <= maxTurns ? `Step ${turnNumber} of ${maxTurns}` : "Completed"}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-200 leading-relaxed">
              {timeline.guided_practice ||
                (turnNumber === 1
                  ? "Turn 1: Socratic probe of flawed premise initiated"
                  : turnNumber === 2
                  ? "Turn 2: Mechanistic guidance provided"
                  : "Turn 3: Reasoning consolidated; ready for transfer check")}
            </p>
          </div>
        </div>

        <div className="flex justify-center -my-1 text-slate-600">
          <ArrowDown className="h-3.5 w-3.5" />
        </div>

        {/* Stage 4: Independent Transfer Assessment */}
        <div
          className={`flex items-start gap-3 rounded-lg border p-3 transition-all duration-300 ${
            isTransferConfirmed
              ? "border-emerald-500/30 bg-emerald-500/10 shadow-lg shadow-emerald-500/5"
              : isAwaitingTransfer
              ? "border-indigo-500/40 bg-indigo-950/30 animate-pulse"
              : isUnresolved
              ? "border-amber-500/30 bg-amber-950/20"
              : "border-slate-800 bg-slate-900/40 opacity-70"
          }`}
        >
          <div
            className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${
              isTransferConfirmed
                ? "bg-emerald-500/20 text-emerald-400"
                : isAwaitingTransfer
                ? "bg-indigo-500/20 text-indigo-300"
                : "bg-slate-800 text-slate-500"
            }`}
          >
            {isTransferConfirmed ? (
              <CheckCircle2 className="h-3.5 w-3.5" />
            ) : (
              <GraduationCap className="h-3.5 w-3.5" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span
                className={`text-xs font-semibold uppercase tracking-wider ${
                  isTransferConfirmed
                    ? "text-emerald-400"
                    : isAwaitingTransfer
                    ? "text-indigo-300"
                    : "text-slate-400"
                }`}
              >
                4. Independent Transfer Assessment
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                {isTransferConfirmed
                  ? "Transfer Demonstrated"
                  : isAwaitingTransfer
                  ? "Pending Held-Out Test"
                  : isUnresolved
                  ? "Evaluation Concluded"
                  : "Held-Out Item"}
              </span>
            </div>
            <p
              className={`mt-1 text-xs leading-relaxed ${
                isTransferConfirmed
                  ? "text-emerald-100 font-medium"
                  : "text-slate-300"
              }`}
            >
              {timeline.transfer_result ||
                "Administered post-dialogue to independently measure concept retention."}
            </p>
          </div>
        </div>

        {/* Stage 5: Next Adaptive Recommendation (Phase 2A) */}
        {timeline.next_recommendation && (
          <>
            <div className="flex justify-center -my-1 text-slate-600">
              <ArrowDown className="h-3.5 w-3.5" />
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-purple-400">
                <Compass className="h-3.5 w-3.5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-purple-300">
                    5. Next Adaptive Recommendation
                  </span>
                  <span className="text-[10px] text-purple-400/70 font-mono">Phase 2A Engine</span>
                </div>
                <p className="mt-1 text-xs text-slate-200 leading-relaxed">
                  {timeline.next_recommendation}
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
