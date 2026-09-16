"use client";

import React from "react";
import {
  BrainCircuit,
  TrendingUp,
  Award,
  AlertCircle,
  Sparkles,
  ArrowRight,
  BookOpen,
  CheckCircle2,
} from "lucide-react";
import type { LearnerState, AdaptiveRecommendation } from "../../lib/types";

interface MobileMasterySummaryProps {
  learnerState: LearnerState | null;
  recommendation: AdaptiveRecommendation | null;
  onSelectTopic: (subject: string, topic: string) => void;
  onRefresh: () => void;
}

export const MobileMasterySummary: React.FC<MobileMasterySummaryProps> = ({
  learnerState,
  recommendation,
  onSelectTopic,
  onRefresh,
}) => {
  if (!learnerState) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        Loading learner state…
      </div>
    );
  }

  const overallAccuracyPct =
    learnerState.overall_accuracy !== null && learnerState.overall_accuracy !== undefined
      ? Math.round(learnerState.overall_accuracy * 100)
      : null;

  return (
    <div className="space-y-4">
      {/* Top Stats Card */}
      <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950/40 border border-sky-500/30 p-4 sm:p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Educational Progress</h3>
              <p className="text-[11px] text-slate-400 font-mono truncate max-w-[180px]">
                {learnerState.learner_id}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-sky-400 font-mono">
              {overallAccuracyPct !== null ? `${overallAccuracyPct}%` : "—"}
            </div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">
              Overall Accuracy
            </div>
          </div>
        </div>

        {/* 2-col Metrics */}
        <div className="grid grid-cols-2 gap-2.5 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-slate-500 text-[10px] block uppercase">Total Questions</span>
            <span className="text-base font-semibold text-slate-200 font-mono">
              {learnerState.total_attempts}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-slate-500 text-[10px] block uppercase">Correct Attempts</span>
            <span className="text-base font-semibold text-emerald-400 font-mono">
              {learnerState.correct_attempts}
            </span>
          </div>
        </div>
      </div>

      {/* Authoritative Recommendation Card */}
      {recommendation && (
        <div className="rounded-2xl bg-gradient-to-r from-sky-950/40 to-indigo-950/40 border border-sky-500/30 p-4 space-y-2.5 shadow-md">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-sky-400 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Authoritative Next Step</span>
          </div>
          <h4 className="text-sm font-semibold text-slate-100">
            {recommendation.action === "SOLVE_TARGETED_QUESTION"
              ? "Targeted Practice"
              : recommendation.action === "ASK_GROUNDED_TUTOR"
              ? "Socratic Remediation"
              : recommendation.action === "REVIEW_CONCEPT"
              ? "Concept Review"
              : "Topic Reinforcement"}
            : <span className="text-sky-300 font-normal">{recommendation.topic}</span>
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            {recommendation.explanation}
          </p>
          <div className="pt-1">
            <button
              type="button"
              onClick={() => onSelectTopic(recommendation.subject, recommendation.topic)}
              className="w-full py-2.5 px-3 rounded-xl bg-sky-500 hover:bg-sky-400 active:bg-sky-600 text-slate-950 font-semibold text-xs flex items-center justify-center gap-2 transition-colors"
            >
              <span>Practice {recommendation.topic}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Topic Mastery List */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
          Topic Breakdown
        </h4>

        {Object.keys(learnerState.topic_mastery).length === 0 ? (
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-slate-500 text-xs text-center">
            No topic attempts recorded yet.
          </div>
        ) : (
          Object.entries(learnerState.topic_mastery).map(([topicName, record]) => {
            const acc =
              record.accuracy !== null && record.accuracy !== undefined
                ? Math.round(record.accuracy * 100)
                : null;

            return (
              <div
                key={topicName}
                className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">{topicName}</div>
                  <div className="text-[11px] text-slate-400">
                    Mastery:{" "}
                    <span className="capitalize text-sky-400 font-medium">
                      {record.mastery_level}
                    </span>{" "}
                    • Status:{" "}
                    <span className="capitalize text-slate-300">
                      {record.mastery_status.replace("_", " ")}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-mono font-semibold text-slate-200">
                    {acc !== null ? `${acc}%` : "—"}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {record.correct_attempts}/{record.total_attempts} correct
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
