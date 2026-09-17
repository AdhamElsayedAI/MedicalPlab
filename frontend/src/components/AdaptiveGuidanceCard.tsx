"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { AdaptiveRecommendation, LearnerState } from "@/lib/types";
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Lightbulb,
} from "lucide-react";

interface AdaptiveGuidanceCardProps {
  learnerId: string;
  onSelectTopic?: (subject: string, topic: string, questionId?: string) => void;
  onOpenTutorWithQuery?: (query: string, topic: string, questionId?: string) => void;
  refreshTrigger?: number;
}

export function AdaptiveGuidanceCard({
  learnerId,
  onSelectTopic,
  onOpenTutorWithQuery,
  refreshTrigger = 0,
}: AdaptiveGuidanceCardProps) {
  const [state, setState] = useState<LearnerState | null>(null);
  const [recommendation, setRecommendation] = useState<AdaptiveRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (!learnerId) return;

    setLoading(true);
    setError(null);

    Promise.all([
      api.getAdaptiveState(learnerId),
      api.getAdaptiveRecommendation(learnerId),
    ])
      .then(([s, rec]) => {
        if (active) {
          setState(s);
          setRecommendation(rec);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load adaptive guidance");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [learnerId, refreshTrigger]);

  if (loading && !state) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 text-sm flex items-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
        Analyzing your learning state and knowledge gaps…
      </div>
    );
  }

  if (error || !state) {
    return null;
  }

  const primaryWeakness = state.weak_topics.length > 0 ? state.weak_topics[0] : null;

  return (
    <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-sky-950/40 border border-sky-500/30 p-5 space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-500/20 border border-sky-400/40 flex items-center justify-center text-sky-400">
            <BrainCircuit className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Adaptive Learning Guidance
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-semibold border border-teal-500/30">
                Personalized
              </span>
            </h3>
            <p className="text-xs text-slate-400">Continuous diagnostic mastery &amp; guided reinforcement</p>
          </div>
        </div>

        {state.total_attempts > 0 && (
          <div className="text-right text-xs">
            <span className="text-slate-400">Accuracy: </span>
            <span className="font-bold text-sky-300">
              {state.overall_accuracy !== null ? `${Math.round(state.overall_accuracy * 100)}%` : "—"}
            </span>
            <span className="text-slate-500 ml-1">({state.total_attempts} attempts)</span>
          </div>
        )}
      </div>

      {/* Weakness Detection Section */}
      {primaryWeakness ? (
        <div className="space-y-3">
          <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/30 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                Detected Weakness
              </span>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                {primaryWeakness.priority} priority
              </span>
            </div>

            <div className="text-base font-bold text-slate-100">{primaryWeakness.topic}</div>

            <div className="text-xs text-slate-300 leading-relaxed">
              <strong className="text-slate-200">Why? </strong>
              {primaryWeakness.reason}
            </div>
          </div>

          {/* Actionable Next Step */}
          {recommendation && (
            <div className="p-3.5 rounded-xl bg-sky-950/30 border border-sky-500/30 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-sky-400">
                <Lightbulb className="w-3.5 h-3.5" />
                Recommended Next Step
              </div>

              <div className="text-sm font-medium text-slate-200">
                {recommendation.action === "ASK_GROUNDED_TUTOR"
                  ? "Guided Socratic Remediation"
                  : recommendation.action === "SOLVE_TARGETED_QUESTION"
                  ? "Targeted Question Practice"
                  : recommendation.action === "REVIEW_CONCEPT"
                  ? "Evidence-Grounded Concept Review"
                  : "Topic Review & Reinforcement"}
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {recommendation.explanation}
              </p>

              <div className="pt-2 flex flex-wrap gap-2">
                {recommendation.action === "ASK_GROUNDED_TUTOR" && onOpenTutorWithQuery && (
                  <button
                    onClick={() =>
                      onOpenTutorWithQuery(
                        recommendation.tutor_query ||
                          `I am having difficulty understanding ${recommendation.topic}. Can you explain the core mechanism?`,
                        recommendation.topic,
                        recommendation.target_question_id || undefined
                      )
                    }
                    className="px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Start Socratic Remediation
                  </button>
                )}

                {recommendation.target_question_id && onSelectTopic && (
                  <button
                    onClick={() =>
                      onSelectTopic(
                        recommendation.subject,
                        recommendation.topic,
                        recommendation.target_question_id || undefined
                      )
                    }
                    className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <span>Practice Targeted Question</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* No active weaknesses */
        <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4" />
            <span>No Severe Knowledge Gaps Detected</span>
          </div>
          <p className="text-xs text-slate-300">
            {state.total_attempts === 0
              ? "Answer questions to begin adaptive diagnostic tracking. MedicalPlab will detect patterns in your mistakes and tailor interventions."
              : "Great job! All practiced topics are currently meeting baseline competency standards."}
          </p>

          {recommendation && (
            <div className="pt-2">
              <span className="text-[11px] text-slate-400 block mb-1">Recommended Next Topic:</span>
              <button
                onClick={() =>
                  onSelectTopic &&
                  onSelectTopic(recommendation.subject, recommendation.topic, recommendation.target_question_id || undefined)
                }
                className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium inline-flex items-center gap-1.5 transition-colors"
              >
                <span>Practice {recommendation.topic}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
