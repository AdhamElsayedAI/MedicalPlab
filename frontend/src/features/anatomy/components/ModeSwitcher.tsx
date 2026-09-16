'use client';

import React from 'react';
import { LearningMode } from '../adapters/anatomyPresentationAdapter';

interface ModeSwitcherProps {
  currentMode: LearningMode;
  onSelectMode: (mode: LearningMode) => void;
  isChallengeAvailable?: boolean;
}

export function ModeSwitcher({
  currentMode,
  onSelectMode,
  isChallengeAvailable = true,
}: ModeSwitcherProps) {
  return (
    <div className="flex items-center p-1 bg-slate-100 rounded-lg border border-slate-200 select-none">
      <button
        onClick={() => onSelectMode('EXPLORE')}
        className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition ${
          currentMode === 'EXPLORE'
            ? 'bg-white text-slate-800 shadow-sm'
            : 'text-slate-500 hover:text-slate-700'
        }`}
      >
        Explore
      </button>

      <button
        onClick={() => onSelectMode('GUIDED_LESSON')}
        className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition ${
          currentMode === 'GUIDED_LESSON'
            ? 'bg-white text-slate-800 shadow-sm'
            : 'text-slate-500 hover:text-slate-700'
        }`}
      >
        Guided Lesson
      </button>

      <button
        onClick={() => onSelectMode('CHALLENGE')}
        className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition flex items-center justify-center gap-1 ${
          currentMode === 'CHALLENGE'
            ? 'bg-white text-slate-800 shadow-sm'
            : 'text-slate-500 hover:text-slate-700'
        }`}
      >
        <span>Challenge</span>
        {isChallengeAvailable && (
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
        )}
      </button>
    </div>
  );
}
