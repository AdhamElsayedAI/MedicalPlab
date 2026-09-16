'use client';

import React, { useState } from 'react';
import { InteractionRequest } from '@/lib/anatomy/types';

interface GuidedLessonPanelProps {
  tutorMessage: string;
  interactionReq: InteractionRequest | null;
  onProceedToChallenge: () => void;
  onAskTutor: (prompt: string) => void;
  isSubmitting?: boolean;
  historyMessages?: Array<{ role: 'tutor' | 'learner'; text: string }>;
  selectedStructureName?: string | null;
  isCutawayMode?: boolean;
}

export function GuidedLessonPanel({
  tutorMessage,
  interactionReq,
  onProceedToChallenge,
  onAskTutor,
  isSubmitting = false,
  historyMessages = [],
  selectedStructureName,
  isCutawayMode = false,
}: GuidedLessonPanelProps) {
  const [showConversation, setShowConversation] = useState(false);
  const [showAskTutor, setShowAskTutor] = useState(false);
  const [learnerInput, setLearnerInput] = useState('');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!learnerInput.trim() || isSubmitting) return;
    onAskTutor(learnerInput.trim());
    setLearnerInput('');
  };

  const objectiveTitle = isCutawayMode
    ? 'Trace Urine Flow: Renal Pyramid → Collecting System'
    : 'Renal Blood Flow & Hilum Orientation (V-A-P)';

  const displayMessage = isCutawayMode
    ? 'Trace the outflow pathway through verified HRA geometry. Urine passes through collecting ducts within the renal pyramid, exits at the renal papilla, enters a minor calyx, continues into a major calyx and the renal pelvis, then flows into the ureter.'
    : tutorMessage;

  const taskPrompt = isCutawayMode
    ? 'Follow the highlighted pathway from the representative renal pyramid through the calyces to the ureter (other medullary units de-emphasized for clarity).'
    : interactionReq?.prompt;

  return (
    <div className="flex flex-col gap-4 py-2">
      {/* Objective Card */}
      <div className="p-3 bg-teal-50/70 rounded-xl border border-teal-100">
        <div className="text-[10px] font-bold uppercase tracking-wider text-teal-800 mb-0.5">
          Current Objective
        </div>
        <div className="text-xs font-semibold text-slate-800">
          {objectiveTitle}
        </div>
      </div>

      {/* Authoritative AI Tutor Guidance Card */}
      <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col gap-2.5">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
          <span className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
            AI Anatomy Tutor
          </span>
          {isCutawayMode && (
            <span className="ml-auto text-[9px] font-semibold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 border border-teal-200">
              Pathway Focus Active
            </span>
          )}
        </div>
        <p className="text-xs text-slate-700 leading-relaxed" id="tutor-dialogue-message">
          {displayMessage}
        </p>

        {/* Expected Learner Interaction Prompt */}
        {taskPrompt && (
          <div className="mt-1 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
            <span className="text-amber-600 font-bold">&bull;</span>
            <div>
              <strong>Guided Task:</strong> {taskPrompt}
            </div>
          </div>
        )}

        {/* Selected structure feedback */}
        {selectedStructureName && (
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5 pt-1 border-t border-slate-100">
            <span>Currently selected in 3D:</span>
            <strong className="text-slate-800">{selectedStructureName}</strong>
          </div>
        )}
      </div>

      {/* Primary CTA: Progress to Challenge */}
      <div className="flex flex-col gap-2 pt-1">
        <button
          onClick={onProceedToChallenge}
          className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl shadow-xs transition flex items-center justify-center gap-2"
        >
          <span>Proceed to Identification Challenge</span>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </div>

      {/* Ask Tutor Expandable */}
      <div className="border-t border-slate-200 pt-2">
        <button
          onClick={() => setShowAskTutor(!showAskTutor)}
          className="flex items-center justify-between w-full text-xs font-semibold text-slate-600 hover:text-slate-900 py-1 transition"
        >
          <span className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            Ask Tutor a Question
          </span>
          <span className="text-slate-400">{showAskTutor ? '−' : '+'}</span>
        </button>

        {showAskTutor && (
          <form onSubmit={handleSend} className="mt-2 flex gap-1.5">
            <input
              type="text"
              placeholder="e.g. 'Why is the renal vein anterior?'"
              value={learnerInput}
              onChange={(e) => setLearnerInput(e.target.value)}
              disabled={isSubmitting}
              className="flex-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500"
            />
            <button
              type="submit"
              disabled={isSubmitting || !learnerInput.trim()}
              className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white text-xs font-medium rounded-lg transition"
            >
              Ask
            </button>
          </form>
        )}
      </div>

      {/* Conversation History Drawer */}
      {historyMessages.length > 0 && (
        <div className="border-t border-slate-200 pt-2">
          <button
            onClick={() => setShowConversation(!showConversation)}
            className="flex items-center justify-between w-full text-xs font-medium text-slate-500 hover:text-slate-800 py-1 transition"
          >
            <span>View conversation history ({historyMessages.length})</span>
            <span>{showConversation ? '−' : '+'}</span>
          </button>

          {showConversation && (
            <div className="mt-2 max-h-48 overflow-y-auto space-y-2 p-2 bg-slate-50 rounded-lg border border-slate-200 text-xs">
              {historyMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`p-2 rounded-lg ${
                    msg.role === 'tutor'
                      ? 'bg-white border border-slate-200 text-slate-700'
                      : 'bg-teal-50 text-teal-900 ml-4'
                  }`}
                >
                  <div className="text-[10px] font-bold uppercase mb-0.5 text-slate-400">
                    {msg.role === 'tutor' ? 'AI Tutor' : 'You'}
                  </div>
                  <div>{msg.text}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
