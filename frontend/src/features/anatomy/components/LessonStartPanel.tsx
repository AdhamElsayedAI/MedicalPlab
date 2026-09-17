'use client';

import React from 'react';

interface LessonStartPanelProps {
  hasExistingSession: boolean;
  onResumeLesson: () => void;
  onStartNewLesson: () => void;
  onExploreFreely: () => void;
}

export function LessonStartPanel({
  hasExistingSession,
  onResumeLesson,
  onStartNewLesson,
  onExploreFreely,
}: LessonStartPanelProps) {
  return (
    <div className="flex flex-col gap-4 py-2">
      <div className="p-4 bg-teal-50/70 rounded-xl border border-teal-100">
        <span className="text-[10px] font-bold uppercase tracking-wider text-teal-800">
          Module Overview
        </span>
        <h2 className="text-sm font-bold text-slate-900 mt-1 mb-2">
          Understand the renal hilum
        </h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          Explore how the renal artery, renal vein, and renal pelvis relate at the kidney&apos;s medial border.
        </p>
      </div>

      <div className="flex flex-col gap-2 pt-2">
        {hasExistingSession ? (
          <>
            <button
              onClick={onResumeLesson}
              className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-xs transition"
            >
              Resume Lesson
            </button>
            <button
              onClick={onStartNewLesson}
              className="w-full py-2 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition"
            >
              Start New Lesson
            </button>
          </>
        ) : (
          <button
            onClick={onStartNewLesson}
            className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-xs transition"
          >
            Start Guided Lesson
          </button>
        )}

        <button
          onClick={onExploreFreely}
          className="w-full py-2 px-4 text-slate-600 hover:text-slate-900 font-medium text-xs rounded-xl transition text-center"
        >
          Explore Freely
        </button>
      </div>
    </div>
  );
}
