"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Stethoscope,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  RotateCcw,
  Sparkles,
  BookOpen,
  Info,
  Loader2,
  FileText,
} from "lucide-react";
import { api, getAuthoritativeLearnerId } from "@/lib/api-client";
import type { PLABQuestionPublic, PLABEvaluationResult } from "@/lib/types";

interface PLABPracticeViewProps {
  onSwitchToUniversity?: () => void;
}

export const PLABPracticeView: React.FC<PLABPracticeViewProps> = ({
  onSwitchToUniversity,
}) => {
  const [questions, setQuestions] = useState<PLABQuestionPublic[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [selectedOption, setSelectedOption] = useState<"A" | "B" | "C" | "D" | "E" | "">("");
  const [evaluation, setEvaluation] = useState<PLABEvaluationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [learnerId, setLearnerId] = useState<string>("");

  useEffect(() => {
    const id = getAuthoritativeLearnerId();
    setLearnerId(id);

    async function fetchQuestions() {
      try {
        setLoading(true);
        setError("");
        const items = await api.getPLABQuestions();
        setQuestions(items);
      } catch (err: any) {
        setError(err.message || "Failed to load PLAB questions.");
      } finally {
        setLoading(false);
      }
    }

    fetchQuestions();
  }, []);

  const currentQuestion = questions[currentIndex] || null;

  const handleSubmit = async () => {
    if (!currentQuestion || !selectedOption || evaluating) return;
    try {
      setEvaluating(true);
      setError("");
      const idempotencyKey = `plab-${currentQuestion.question_id}-${Date.now()}`;
      const result = await api.evaluatePLABAnswer({
        questionId: currentQuestion.question_id,
        selectedOption: selectedOption as "A" | "B" | "C" | "D" | "E",
        idempotencyKey,
      });
      setEvaluation(result);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate clinical answer.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleNext = () => {
    setEvaluation(null);
    setSelectedOption("");
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setCurrentIndex(0);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading PLAB clinical exam bank...</p>
      </div>
    );
  }

  // 1. Production Mode: No Golden questions promoted yet
  if (questions.length === 0) {
    return (
      <div className="max-w-3xl mx-auto py-8">
        <div className="med-card p-8 text-center space-y-6 border border-white/[0.1]">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 mx-auto flex items-center justify-center">
            <ShieldCheck className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <span className="med-badge med-badge-warning">GOLDEN_ONLY Production Governance</span>
            <h2 className="text-2xl font-bold text-white font-['Plus_Jakarta_Sans',sans-serif]">
              PLAB Clinical Curriculum Locked
            </h2>
            <p className="text-sm text-slate-400 max-w-lg mx-auto leading-relaxed">
              Public student delivery is strictly gated until candidate items complete formal clinician promotion. To prevent unvetted medical items from entering study sessions, the platform enforces fail-closed clinical governance.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] text-left max-w-md mx-auto space-y-2 text-xs">
            <div className="flex items-center justify-between text-slate-300">
              <span>Public Release Status:</span>
              <strong className="text-amber-400">Gated (0 Promoted)</strong>
            </div>
            <div className="flex items-center justify-between text-slate-300">
              <span>Candidate Items in Review:</span>
              <span className="text-slate-400">36 Cardiology Questions</span>
            </div>
            <div className="flex items-center justify-between text-slate-300">
              <span>Demo / QA Override:</span>
              <code className="text-[10px] text-sky-300 bg-black/40 px-1.5 py-0.5 rounded">MEDICALPLAB_PLAB_PREVIEW_QA=1</code>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={onSwitchToUniversity}
              className="btn-primary inline-flex items-center gap-2 text-xs py-2.5 px-6 rounded-xl"
            >
              <BookOpen className="w-4 h-4" />
              <span>Practice Preclinical University MCQs</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 2. Preview QA Mode: Clinical questions available for testing
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Governance Banner */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
          <div>
            <span className="font-bold text-amber-300 mr-2">PREVIEW QA MODE ACTIVE</span>
            <span className="text-amber-200/80">
              Candidate clinical questions are undergoing expert review. Not officially approved for public student curriculum.
            </span>
          </div>
        </div>
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-semibold bg-amber-400/20 text-amber-300 flex-shrink-0 self-start sm:self-auto">
          36 QA Items
        </span>
      </div>

      {/* Question Card */}
      {currentQuestion && (
        <div className="med-card p-6 sm:p-8 space-y-6">
          {/* Question Metadata Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-white/[0.08] text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sky-400">
                Question {currentIndex + 1} of {questions.length}
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400">{currentQuestion.question_id}</span>
            </div>
            <div className="flex items-center gap-2">
              {currentQuestion.specialty && (
                <span className="med-badge bg-indigo-500/10 text-indigo-300 border-indigo-500/20">
                  {currentQuestion.specialty}
                </span>
              )}
              <span className="med-badge med-badge-primary">
                {currentQuestion.topic}
              </span>
            </div>
          </div>

          {/* Clinical Vignette Stem */}
          <div className="text-base sm:text-lg text-slate-100 font-medium leading-relaxed font-['Inter',sans-serif]">
            {currentQuestion.stem}
          </div>

          {/* Answer Options */}
          <div className="space-y-3 pt-2" role="radiogroup" aria-label="Clinical Answer Options">
            {currentQuestion.options.map((opt) => {
              const isSelected = selectedOption === opt.id;
              const isCorrectAnswer = evaluation && opt.id === evaluation.correct_answer;
              const isWrongSelection = evaluation && isSelected && !evaluation.correct;

              let optionStyle = "bg-white/[0.03] border-white/[0.08] hover:bg-white/[0.06] hover:border-white/[0.15] text-slate-200";
              if (isSelected && !evaluation) {
                optionStyle = "bg-sky-500/15 border-sky-400/60 text-white ring-1 ring-sky-400/40";
              } else if (isCorrectAnswer) {
                optionStyle = "bg-emerald-500/15 border-emerald-400/60 text-white ring-1 ring-emerald-400/40";
              } else if (isWrongSelection) {
                optionStyle = "bg-rose-500/15 border-rose-400/60 text-white ring-1 ring-rose-400/40";
              }

              return (
                <button
                  key={opt.id}
                  disabled={evaluating || !!evaluation}
                  onClick={() => setSelectedOption(opt.id as any)}
                  className={`w-full p-4 rounded-xl border text-left flex items-start gap-3.5 transition-all text-sm ${optionStyle} disabled:cursor-not-allowed`}
                >
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0 transition-colors ${
                      isSelected
                        ? "bg-sky-500 text-white"
                        : "bg-white/[0.06] text-slate-400"
                    }`}
                  >
                    {opt.id}
                  </div>
                  <span className="pt-0.5 leading-relaxed">{opt.text}</span>
                </button>
              );
            })}
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}

          {/* Action CTA */}
          {!evaluation ? (
            <div className="pt-4 flex justify-end">
              <button
                disabled={!selectedOption || evaluating}
                onClick={handleSubmit}
                className="btn-primary text-xs py-3 px-8 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {evaluating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Evaluating Clinical Answer...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Answer</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          ) : (
            /* Post-Evaluation Feedback */
            <div className="mt-6 p-6 rounded-2xl bg-white/[0.02] border border-white/[0.1] space-y-4 med-fade-in">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
                <div className="flex items-center gap-2">
                  {evaluation.correct ? (
                    <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-sm">
                      <CheckCircle2 className="w-5 h-5" />
                      <span>Correct Clinical Decision</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-rose-400 font-bold text-sm">
                      <XCircle className="w-5 h-5" />
                      <span>Incorrect — Correct Answer is {evaluation.correct_answer}</span>
                    </div>
                  )}
                </div>
                <span className="text-xs text-slate-400">Attempt ID: {evaluation.attempt_id}</span>
              </div>

              <div className="text-sm text-slate-200 leading-relaxed">
                <strong className="text-white block mb-1">Clinical Explanation:</strong>
                {evaluation.explanation}
              </div>

              {evaluation.learning_feedback && (
                <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-xs text-sky-200">
                  <strong>Learning Feedback:</strong> {evaluation.learning_feedback}
                </div>
              )}

              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleNext}
                  className="btn-primary text-xs py-2.5 px-6 rounded-xl flex items-center gap-2"
                >
                  <span>Next Question</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
