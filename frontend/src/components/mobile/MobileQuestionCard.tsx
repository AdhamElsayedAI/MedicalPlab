"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Sparkles,
  ArrowRight,
  BookOpen,
  HelpCircle,
  Check,
  AlertTriangle,
} from "lucide-react";
import type { UniversityQuestionPayload, UniversityAnswerResponse } from "./MobileApiClient";

interface MobileQuestionCardProps {
  question: UniversityQuestionPayload;
  position?: number;
  total?: number;
  isSubmitting: boolean;
  onSubmitAnswer: (selectedOption: string) => Promise<void>;
  answerResult: UniversityAnswerResponse | null;
  onNextQuestion: () => void;
  onStartRemediation: (questionId: string, selectedOption: string) => void;
}

export const MobileQuestionCard: React.FC<MobileQuestionCardProps> = ({
  question,
  position = 1,
  total = 3,
  isSubmitting,
  onSubmitAnswer,
  answerResult,
  onNextQuestion,
  onStartRemediation,
}) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const handleSelect = (key: string) => {
    if (answerResult) return; // Locked once answered
    setSelectedOption(key);
  };

  const handleSubmit = async () => {
    if (!selectedOption || isSubmitting || answerResult) return;
    await onSubmitAnswer(selectedOption);
  };

  const isAnswered = answerResult !== null;
  const isCorrect = answerResult?.is_correct === true;

  return (
    <div className="space-y-4">
      {/* Question Header & Stem */}
      <div className="rounded-2xl bg-slate-900/90 border border-slate-800 p-4 sm:p-5 shadow-lg relative overflow-hidden">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-3 border-b border-slate-800/80 pb-2.5">
          <span className="flex items-center gap-1.5 font-medium text-sky-400">
            <BookOpen className="w-3.5 h-3.5" />
            {question.topic}
          </span>
          <span className="font-mono bg-slate-800/80 px-2 py-0.5 rounded-full text-[11px] text-slate-300">
            {position} of {total}
          </span>
        </div>

        <h2 className="text-base sm:text-lg font-medium text-slate-100 leading-snug">
          {question.stem}
        </h2>
      </div>

      {/* Options List */}
      <div className="space-y-2.5">
        {Object.entries(question.options).map(([key, text]) => {
          const isChosen = selectedOption === key;
          const isKeyCorrect = answerResult?.correct_answer === key;
          const isChosenWrong = isChosen && isAnswered && !isCorrect;

          let cardStyle = "bg-slate-900/60 border-slate-800/80 text-slate-300 hover:border-slate-700";
          if (isChosen && !isAnswered) {
            cardStyle = "bg-sky-950/40 border-sky-500 text-sky-100 ring-1 ring-sky-500/50";
          } else if (isAnswered) {
            if (isKeyCorrect) {
              cardStyle = "bg-emerald-950/40 border-emerald-500/80 text-emerald-100 ring-1 ring-emerald-500/30";
            } else if (isChosenWrong) {
              cardStyle = "bg-rose-950/40 border-rose-500/80 text-rose-100 ring-1 ring-rose-500/30";
            } else {
              cardStyle = "bg-slate-900/30 border-slate-800/40 text-slate-500 opacity-60";
            }
          }

          return (
            <button
              key={key}
              type="button"
              disabled={isAnswered || isSubmitting}
              onClick={() => handleSelect(key)}
              className={`w-full text-left p-3.5 sm:p-4 rounded-xl border transition-all duration-150 flex items-start gap-3 active:scale-[0.99] ${cardStyle}`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center font-semibold text-xs shrink-0 transition-colors ${
                  isAnswered && isKeyCorrect
                    ? "bg-emerald-500 text-slate-950"
                    : isChosenWrong
                    ? "bg-rose-500 text-white"
                    : isChosen
                    ? "bg-sky-500 text-slate-950"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {isAnswered && isKeyCorrect ? (
                  <Check className="w-4 h-4 stroke-[3]" />
                ) : isChosenWrong ? (
                  <XCircle className="w-4 h-4" />
                ) : (
                  key
                )}
              </div>
              <div className="text-sm font-normal pt-0.5 leading-relaxed">{text}</div>
            </button>
          );
        })}
      </div>

      {/* Action Area */}
      {!isAnswered ? (
        <button
          type="button"
          disabled={!selectedOption || isSubmitting}
          onClick={handleSubmit}
          className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm transition-all duration-200 shadow-md flex items-center justify-center gap-2 ${
            selectedOption && !isSubmitting
              ? "bg-sky-500 hover:bg-sky-400 active:bg-sky-600 text-slate-950 shadow-sky-500/20"
              : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-850"
          }`}
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              <span>Evaluating answer…</span>
            </>
          ) : (
            <span>Submit Answer</span>
          )}
        </button>
      ) : (
        /* Feedback Card */
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 sm:p-5 space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-center gap-2.5">
            {isCorrect ? (
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            ) : (
              <div className="w-8 h-8 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                <XCircle className="w-5 h-5" />
              </div>
            )}
            <div>
              <div
                className={`font-semibold text-sm ${
                  isCorrect ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {isCorrect ? "Correct Answer" : "Incorrect Option Selected"}
              </div>
              <div className="text-xs text-slate-400">
                Correct answer is: <strong className="text-slate-200">{answerResult.correct_answer}</strong>
              </div>
            </div>
          </div>

          {/* Grounded Explanation from Backend */}
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
            {answerResult.explanation}
          </p>

          {/* Action buttons */}
          <div className="pt-1 flex flex-col sm:flex-row gap-2.5">
            {!isCorrect && (
              <button
                type="button"
                onClick={() => onStartRemediation(question.id, selectedOption || "B")}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 active:from-sky-700 active:to-indigo-700 text-white font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-sky-600/20 transition-all duration-150"
              >
                <Sparkles className="w-4 h-4 text-sky-200" />
                <span>Start Socratic Remediation</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => {
                setSelectedOption(null);
                onNextQuestion();
              }}
              className={`w-full py-3 px-4 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 transition-colors ${
                isCorrect
                  ? "bg-sky-500 hover:bg-sky-400 text-slate-950"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              }`}
            >
              <span>Next Question</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
