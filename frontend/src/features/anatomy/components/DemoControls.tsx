'use client';

import React from 'react';
import { DemoStep } from '../hooks/useDemoWalkthrough';

interface DemoControlsProps {
  currentStep: DemoStep;
  currentStepIndex: number;
  totalSteps: number;
  isPaused: boolean;
  onPause: () => void;
  onResume: () => void;
  onNext: () => void;
  onPrev: () => void;
  onExit: () => void;
}

export function DemoControls({
  currentStep,
  currentStepIndex,
  totalSteps,
  isPaused,
  onPause,
  onResume,
  onNext,
  onPrev,
  onExit,
}: DemoControlsProps) {
  return (
    <div className="absolute top-6 left-6 z-20 w-80 max-w-[calc(100vw-3rem)] p-3.5 bg-[#0B1522]/90 backdrop-blur-md rounded-2xl border border-teal-500/40 shadow-2xl select-none animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-teal-400 animate-ping" />
          <span className="text-xs font-bold text-teal-300 tracking-wide">
            Interactive Demo Mode
          </span>
        </div>
        <button
          onClick={onExit}
          className="text-slate-400 hover:text-white text-xs px-2 py-0.5 rounded hover:bg-slate-800 transition"
        >
          Exit
        </button>
      </div>

      {/* Step Info */}
      <div className="mb-2">
        <div className="flex items-center justify-between text-[11px] text-slate-300 font-medium mb-1">
          <span>{currentStep.label}</span>
          <span className="font-mono text-teal-400">
            {currentStepIndex + 1}/{totalSteps}
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          {currentStep.caption}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden mb-3">
        <div
          className="h-full bg-teal-400 transition-all duration-300 ease-out"
          style={{ width: `${((currentStepIndex + 1) / totalSteps) * 100}%` }}
        />
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between gap-2 pt-1 border-t border-slate-800">
        <button
          onClick={onPrev}
          disabled={currentStepIndex === 0}
          className="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300 transition"
        >
          &larr; Back
        </button>

        <button
          onClick={isPaused ? onResume : onPause}
          className="px-3 py-1 text-xs font-semibold rounded bg-teal-600/80 hover:bg-teal-600 text-white transition"
        >
          {isPaused ? 'Resume' : 'Pause'}
        </button>

        <button
          onClick={onNext}
          disabled={currentStepIndex === totalSteps - 1}
          className="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300 transition"
        >
          Next &rarr;
        </button>
      </div>
    </div>
  );
}
