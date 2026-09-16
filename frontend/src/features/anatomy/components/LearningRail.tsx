'use client';

import React from 'react';
import { AnatomyStructure, InteractionRequest } from '@/lib/anatomy/types';
import { LearningMode } from '../adapters/anatomyPresentationAdapter';
import { ModeSwitcher } from './ModeSwitcher';
import { ExplorePanel } from './ExplorePanel';
import { GuidedLessonPanel } from './GuidedLessonPanel';
import { ChallengePanel } from './ChallengePanel';

interface LearningRailProps {
  currentMode: LearningMode;
  onSelectMode: (mode: LearningMode) => void;
  selectedStructure: AnatomyStructure | null;
  onFocusStructure: (structureId: string) => void;
  onIsolateStructure: (structureId: string) => void;
  onAskTutor: (prompt: string) => void;
  onSelectStructureByName: (structureId: string) => void;
  tutorMessage: string;
  interactionReq: InteractionRequest | null;
  onProceedToChallenge: () => void;
  isSubmitting: boolean;
  historyMessages: Array<{ role: 'tutor' | 'learner'; text: string }>;
  onSubmitChallenge: () => void;
  challengeOutcome: {
    evaluated: boolean;
    isCorrect: boolean;
    feedback: string;
  } | null;
  onResetChallenge: () => void;
  onContinueChallenge: () => void;
  isDemoActive?: boolean;
  isCutawayMode?: boolean;
}

export function LearningRail({
  currentMode,
  onSelectMode,
  selectedStructure,
  onFocusStructure,
  onIsolateStructure,
  onAskTutor,
  onSelectStructureByName,
  tutorMessage,
  interactionReq,
  onProceedToChallenge,
  isSubmitting,
  historyMessages,
  onSubmitChallenge,
  challengeOutcome,
  onResetChallenge,
  onContinueChallenge,
  isDemoActive = false,
  isCutawayMode = false,
}: LearningRailProps) {
  return (
    <aside className="w-full md:w-[360px] bg-white border-l border-slate-200/90 flex flex-col h-full shrink-0 select-none shadow-xs z-10">
      {/* Mode Switcher Tabs */}
      <div className="p-3 border-b border-slate-100 shrink-0">
        <ModeSwitcher
          currentMode={currentMode}
          onSelectMode={onSelectMode}
          isChallengeAvailable={true}
        />
      </div>

      {/* Main Mode Content Area (One task at a time) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {currentMode === 'EXPLORE' && (
          <ExplorePanel
            selectedStructure={selectedStructure}
            onFocusStructure={onFocusStructure}
            onIsolateStructure={onIsolateStructure}
            onAskTutor={onAskTutor}
            onSelectStructureByName={onSelectStructureByName}
          />
        )}

        {currentMode === 'GUIDED_LESSON' && (
          <GuidedLessonPanel
            tutorMessage={tutorMessage}
            interactionReq={interactionReq}
            onProceedToChallenge={onProceedToChallenge}
            onAskTutor={onAskTutor}
            isSubmitting={isSubmitting}
            historyMessages={historyMessages}
            selectedStructureName={selectedStructure?.display_name}
            isCutawayMode={isCutawayMode}
          />
        )}

        {currentMode === 'CHALLENGE' && (
          <ChallengePanel
            selectedStructure={selectedStructure}
            onSubmitChallenge={onSubmitChallenge}
            isSubmitting={isSubmitting}
            challengeOutcome={challengeOutcome}
            onResetChallenge={onResetChallenge}
            onContinue={onContinueChallenge}
          />
        )}
      </div>

      {/* Subtle Educational Trust Footer */}
      <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 shrink-0">
        <span className="truncate">Verified HuBMAP HRA · CC BY 4.0</span>
        <span className="text-teal-700 font-medium">AI-guided</span>
      </div>
    </aside>
  );
}
