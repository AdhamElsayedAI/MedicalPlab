'use client';

import React from 'react';
import { AnatomyStructure } from '@/lib/anatomy/types';

interface ChallengePanelProps {
  selectedStructure: AnatomyStructure | null;
  onSubmitChallenge: () => void;
  isSubmitting: boolean;
  challengeOutcome: {
    evaluated: boolean;
    isCorrect: boolean;
    feedback: string;
  } | null;
  onResetChallenge: () => void;
  onContinue: () => void;
}

export function ChallengePanel({
  selectedStructure,
  onSubmitChallenge,
  isSubmitting,
  challengeOutcome,
  onResetChallenge,
  onContinue,
}: ChallengePanelProps) {
  return (
    <div className="flex flex-col gap-4 py-2">
      {/* Challenge Header Card */}
      <div className="p-3 bg-purple-50/60 rounded-xl border border-purple-100">
        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-purple-800 mb-1">
          <span>Identification Challenge</span>
          <span className="px-1.5 py-0.2 rounded bg-purple-100 text-purple-700 font-mono text-[9px]">
            Authoritative Scoring
          </span>
        </div>
        <p className="text-xs text-slate-800 leading-relaxed font-medium">
          Identify the vessel that branches from the abdominal aorta to supply oxygenated blood to the kidney.
        </p>
      </div>

      {/* Selected 3D Target Display */}
      <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col gap-1.5">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Your 3D Selection
        </span>
        <div className="flex items-center justify-between">
          <div className="text-xs font-semibold text-slate-900">
            {selectedStructure ? selectedStructure.display_name : 'No structure selected'}
          </div>
          {selectedStructure ? (
            <span className="w-2 h-2 rounded-full bg-teal-500" />
          ) : (
            <span className="text-[11px] text-amber-600 italic">Click 3D model</span>
          )}
        </div>
      </div>

      {/* Primary Action Button */}
      {!challengeOutcome?.evaluated ? (
        <button
          id="btn-submit-challenge"
          onClick={onSubmitChallenge}
          disabled={!selectedStructure || isSubmitting}
          className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-xs rounded-xl shadow-xs transition flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Evaluating...
            </span>
          ) : (
            <span>Check Answer</span>
          )}
        </button>
      ) : null}

      {/* Authoritative Server Feedback */}
      {challengeOutcome?.evaluated && (
        <div
          id="challenge-result-banner"
          className={`p-4 rounded-xl border flex flex-col gap-2.5 animate-fade-in ${
            challengeOutcome.isCorrect
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}
        >
          <div className="flex items-center gap-2 font-bold text-xs">
            {challengeOutcome.isCorrect ? (
              <>
                <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                <span>Correct — {selectedStructure?.display_name || 'Target Identified'}</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span>Not quite.</span>
              </>
            )}
          </div>

          <p className="text-xs leading-relaxed">
            {challengeOutcome.feedback}
          </p>

          <div className="pt-2">
            {challengeOutcome.isCorrect ? (
              <button
                onClick={onContinue}
                className="w-full py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg shadow-xs transition"
              >
                Continue
              </button>
            ) : (
              <button
                onClick={onResetChallenge}
                className="w-full py-2 px-3 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-lg shadow-xs transition"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
