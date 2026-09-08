"use client";

import React, { useState, useEffect } from "react";
import confetti from "canvas-confetti";
import {
  BookMarked,
  Clock,
  CheckCircle,
  XCircle,
  ChevronRight,
  BookOpen,
  Award,
  ArrowRight,
  Stethoscope,
} from "lucide-react";
import { PLAB_QUESTIONS } from "@/lib/demo-data";
import { PLABQuestion } from "@/lib/types";
import { api } from "@/lib/api-client";

interface ClinicalMCQEngineProps {
  initialQuestionId?: string;
  onNavigateToTutor?: (query: string) => void;
  onAttemptCompleted?: (topic: string, isCorrect: boolean) => void;
}

const DIFFICULTY_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  Novice:     { bg: 'rgba(34,197,94,0.08)',  color: '#86efac', border: 'rgba(34,197,94,0.2)'  },
  Developing: { bg: 'rgba(14,165,233,0.08)', color: '#7dd3fc', border: 'rgba(14,165,233,0.2)' },
  Competent:  { bg: 'rgba(245,158,11,0.08)', color: '#fcd34d', border: 'rgba(245,158,11,0.2)' },
  Mastery:    { bg: 'rgba(239,68,68,0.08)',  color: '#fca5a5', border: 'rgba(239,68,68,0.2)'  },
};

export const ClinicalMCQEngine: React.FC<ClinicalMCQEngineProps> = ({
  initialQuestionId,
  onNavigateToTutor,
  onAttemptCompleted,
}) => {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [timeLeft, setTimeLeft] = useState(75);
  const [timerActive, setTimerActive] = useState(true);

  useEffect(() => {
    if (initialQuestionId) {
      const idx = PLAB_QUESTIONS.findIndex((q) => q.id === initialQuestionId);
      if (idx !== -1) setCurrentIdx(idx);
    }
  }, [initialQuestionId]);

  const currentQ: PLABQuestion = PLAB_QUESTIONS[currentIdx] || PLAB_QUESTIONS[0];

  useEffect(() => {
    if (!timerActive || isSubmitted || timeLeft <= 0) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [timerActive, isSubmitted, timeLeft]);

  const handleSelectOption = (key: string) => {
    if (isSubmitted) return;
    setSelectedOption(key);
  };

  const handleSubmit = async () => {
    if (!selectedOption || isSubmitted) return;
    setIsSubmitted(true);
    setTimerActive(false);

    const chosen = currentQ.options.find((o) => o.key === selectedOption);
    const isCorrect = chosen?.isCorrect || false;

    if (isCorrect) {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
        colors: ["#38bdf8", "#22c55e", "#a78bfa"],
      });
    }

    await api.recordAttempt(currentQ.topic, isCorrect);
    if (onAttemptCompleted) {
      onAttemptCompleted(currentQ.topic, isCorrect);
    }
  };

  const handleNext = () => {
    const nextIdx = (currentIdx + 1) % PLAB_QUESTIONS.length;
    setCurrentIdx(nextIdx);
    setSelectedOption(null);
    setIsSubmitted(false);
    setTimeLeft(75);
    setTimerActive(true);
  };

  const isCurrentCorrect = currentQ.options.find((o) => o.key === selectedOption)?.isCorrect;
  const diffStyle = DIFFICULTY_STYLES[currentQ.difficulty] || DIFFICULTY_STYLES.Developing;
  const timerWarning = timeLeft < 20;

  return (
    <section className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6 med-fade-in" aria-label="Clinical Assessment">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.25)' }}>
              <BookMarked className="w-5 h-5 text-amber-400" />
            </div>
            <h2 className="section-header">Clinical Assessment</h2>
          </div>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-[13px] font-medium text-sky-400">{currentQ.specialty}</span>
            <span className="text-slate-600">·</span>
            <div
              className="med-badge"
              style={{ background: diffStyle.bg, color: diffStyle.color, border: `1px solid ${diffStyle.border}` }}
            >
              {currentQ.difficulty}
            </div>
            <span className="text-[12px] text-slate-500">Question {currentIdx + 1} of {PLAB_QUESTIONS.length}</span>
          </div>
        </div>

        {/* Timer */}
        <div
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-[14px] font-bold flex-shrink-0"
          style={{
            background: timerWarning ? 'rgba(239,68,68,0.1)' : 'rgba(255,255,255,0.04)',
            border: `1px solid ${timerWarning ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.08)'}`,
            color: timerWarning ? '#fca5a5' : '#e2e8f0',
          }}
        >
          <Clock className={`w-4 h-4 ${timerWarning ? 'text-red-400 animate-pulse' : 'text-slate-400'}`} />
          <span>{timeLeft}s</span>
        </div>
      </div>

      {/* Question Card */}
      <div className="med-card p-7 space-y-6">

        {/* Evidence ref */}
        <div className="flex items-center justify-between text-[12px]" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)', paddingBottom: '16px' }}>
          <span className="text-slate-500 font-mono">Vignette #{String(currentIdx + 1).padStart(2, '0')}</span>
          <div className="flex items-center gap-1.5 text-sky-400 font-mono font-semibold">
            <BookOpen className="w-3.5 h-3.5" />
            {currentQ.evidenceRef}
          </div>
        </div>

        {/* Vignette */}
        <p className="text-[15px] text-slate-100 leading-relaxed" style={{ fontFamily: "'Inter', sans-serif" }}>
          {currentQ.vignette}
        </p>

        {/* Options */}
        <div className="space-y-3">
          {currentQ.options.map((opt) => {
            const isSelected = selectedOption === opt.key;
            let bg = 'rgba(255,255,255,0.03)';
            let border = 'rgba(255,255,255,0.08)';
            let textColor = '#cbd5e1';
            let icon = null;

            if (isSelected && !isSubmitted) {
              bg = 'rgba(14,165,233,0.1)';
              border = 'rgba(14,165,233,0.4)';
              textColor = '#e2e8f0';
            } else if (isSubmitted) {
              if (opt.isCorrect) {
                bg = 'rgba(34,197,94,0.1)';
                border = 'rgba(34,197,94,0.4)';
                textColor = '#d1fae5';
                icon = <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />;
              } else if (isSelected && !opt.isCorrect) {
                bg = 'rgba(239,68,68,0.1)';
                border = 'rgba(239,68,68,0.4)';
                textColor = '#fecaca';
                icon = <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />;
              }
            }

            return (
              <div
                key={opt.key}
                onClick={() => handleSelectOption(opt.key)}
                className="flex items-center gap-4 p-4 rounded-xl transition-all"
                style={{ background: bg, border: `1px solid ${border}`, cursor: isSubmitted ? 'default' : 'pointer', color: textColor }}
                onMouseEnter={(e) => {
                  if (!isSubmitted && !isSelected) {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.06)';
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.15)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSubmitted && !isSelected) {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.03)';
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.08)';
                  }
                }}
                role="button"
                aria-pressed={isSelected}
              >
                <span
                  className="w-7 h-7 rounded-lg flex items-center justify-center font-mono font-bold text-[13px] flex-shrink-0"
                  style={{
                    background: isSelected && !isSubmitted ? 'rgba(14,165,233,0.25)' : 'rgba(255,255,255,0.06)',
                    color: isSelected && !isSubmitted ? '#38bdf8' : '#64748b',
                  }}
                >
                  {opt.key}
                </span>
                <span className="flex-1 text-[14px] font-medium leading-snug">{opt.text}</span>
                {icon}
              </div>
            );
          })}
        </div>

        {/* Submit/Next Row */}
        <div className="flex items-center justify-between pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.07)' }}>
          <div className="text-[12px] text-slate-500">
            {isSubmitted
              ? isCurrentCorrect
                ? "✓ Correct — well reasoned"
                : "✗ Incorrect — review the explanation"
              : "Select the single best answer"}
          </div>

          {!isSubmitted ? (
            <button
              onClick={handleSubmit}
              disabled={!selectedOption}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-[14px] text-white transition-all disabled:opacity-40"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)', boxShadow: '0 4px 14px rgba(14,165,233,0.25)' }}
            >
              Submit Answer
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-[14px] text-white transition-all"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)', boxShadow: '0 4px 14px rgba(14,165,233,0.25)' }}
            >
              Next Question
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Explanation (shown after submit) */}
      {isSubmitted && (
        <div className="med-card p-7 space-y-5 med-fade-in">
          <div className="flex items-center justify-between pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
            <div className="flex items-center gap-2 text-[14px] font-semibold text-white">
              <BookOpen className="w-4 h-4 text-sky-400" />
              Clinical Explanation
            </div>
            <div className="med-badge med-badge-success">
              <CheckCircle className="w-3 h-3" />
              NICE Verified
            </div>
          </div>

          <p className="text-[14px] text-slate-200 leading-relaxed">{currentQ.explanation}</p>

          {/* Distractor breakdown */}
          <div>
            <div className="text-[12px] font-semibold text-slate-500 uppercase tracking-wider mb-3">Option Analysis</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {currentQ.options.map((opt) => (
                <div
                  key={opt.key}
                  className="p-3.5 rounded-xl text-[12px] leading-relaxed"
                  style={{
                    background: opt.isCorrect ? 'rgba(34,197,94,0.07)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${opt.isCorrect ? 'rgba(34,197,94,0.2)' : 'rgba(255,255,255,0.07)'}`,
                  }}
                >
                  <span className="font-bold text-white">Option {opt.key}: </span>
                  <span className="text-slate-400">{opt.eliminationRationale}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Ask tutor */}
          {onNavigateToTutor && (
            <div className="flex justify-end">
              <button
                onClick={() => onNavigateToTutor(`Discuss rationale for ${currentQ.specialty} question: ${currentQ.explanation}`)}
                className="flex items-center gap-2 text-[13px] font-semibold transition-colors"
                style={{ color: '#7dd3fc' }}
                onMouseEnter={(e) => { e.currentTarget.style.color = '#38bdf8'; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = '#7dd3fc'; }}
              >
                <Stethoscope className="w-4 h-4" />
                Explore this topic with AI Tutor
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
