"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Send,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  FileText,
  X,
  MessageSquare,
  ShieldCheck,
  ChevronDown,
  HelpCircle,
} from "lucide-react";
import type { RemediationTurnResponse, RemediationSessionResponse } from "../../lib/types";

interface MessageItem {
  sender: "tutor" | "student";
  text: string;
  probe?: string | null;
  citations?: Array<any>;
}

interface MobileRemediationDrawerProps {
  initialTurn: RemediationTurnResponse;
  restoredSession?: RemediationSessionResponse | null;
  onSubmitTurn: (message: string) => Promise<RemediationTurnResponse>;
  onStartTransfer: (sessionId: string) => void;
  onExitRemediation: (sessionId: string) => void;
}

export const MobileRemediationDrawer: React.FC<MobileRemediationDrawerProps> = ({
  initialTurn,
  restoredSession,
  onSubmitTurn,
  onStartTransfer,
  onExitRemediation,
}) => {
  const [currentTurn, setCurrentTurn] = useState<RemediationTurnResponse>(initialTurn);
  const [messages, setMessages] = useState<MessageItem[]>(() => {
    if (restoredSession && restoredSession.turns && restoredSession.turns.length > 0) {
      const restoredMsgs: MessageItem[] = [];
      for (const t of restoredSession.turns) {
        restoredMsgs.push({
          sender: "tutor",
          text: t.tutor_message,
          probe: t.socratic_probe,
          citations: t.citations,
        });
        if (t.student_message) {
          restoredMsgs.push({
            sender: "student",
            text: t.student_message,
          });
        }
      }
      return restoredMsgs;
    }
    return [
      {
        sender: "tutor",
        text: initialTurn.tutor_message,
        probe: initialTurn.socratic_probe,
        citations: initialTurn.citations,
      },
    ];
  });
  const [inputText, setInputText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const turnNumber = currentTurn.turn_number;
  const isAwaitingTransfer = currentTurn.lifecycle_state === "AWAITING_TRANSFER";
  const isCompleted = currentTurn.lifecycle_state === "COMPLETED";
  const isSafetyFallback = currentTurn.outcome === "SAFETY_FALLBACK";
  const isTransferAvailable = currentTurn.transfer_available === true;

  const handleSend = async (messageToSend?: string) => {
    const text = (messageToSend || inputText).trim();
    if (!text || isSubmitting || isAwaitingTransfer || isCompleted) return;

    setErrorText(null);
    setIsSubmitting(true);

    // Optimistically add student message
    const updatedMessages: MessageItem[] = [
      ...messages,
      { sender: "student", text },
    ];
    setMessages(updatedMessages);
    setInputText("");

    try {
      const nextTurn = await onSubmitTurn(text);
      setCurrentTurn(nextTurn);
      setMessages([
        ...updatedMessages,
        {
          sender: "tutor",
          text: nextTurn.tutor_message,
          probe: nextTurn.socratic_probe,
          citations: nextTurn.citations,
        },
      ]);
    } catch (err: any) {
      setErrorText(err.message || "Failed to advance remediation turn");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 rounded-2xl border border-sky-500/30 overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="bg-slate-900/95 border-b border-slate-800 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs sm:text-sm font-semibold text-slate-100 flex items-center gap-2">
              Socratic Remediation
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono">
                Phase 2B
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              {isSafetyFallback
                ? "Safe Terminal Fallback"
                : isAwaitingTransfer
                ? "Dialogue Completed — Ready for Assessment"
                : `Turn ${turnNumber} of 3 • ${
                    turnNumber === 1
                      ? "Challenge Premise"
                      : turnNumber === 2
                      ? "Mechanistic Clue"
                      : "Consolidate Understanding"
                  }`}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => onExitRemediation(currentTurn.session_id)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          title="Exit Remediation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-900 h-1">
        <div
          className={`h-full transition-all duration-300 ${
            isSafetyFallback
              ? "bg-amber-500 w-full"
              : isAwaitingTransfer || isCompleted
              ? "bg-emerald-500 w-full"
              : turnNumber === 1
              ? "bg-sky-500 w-1/3"
              : "bg-sky-500 w-2/3"
          }`}
        />
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs sm:text-sm">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${
              m.sender === "student" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-[90%] rounded-2xl p-3.5 leading-relaxed shadow-sm ${
                m.sender === "student"
                  ? "bg-sky-600 text-white rounded-br-none"
                  : "bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-none"
              }`}
            >
              <p>{m.text}</p>

              {/* Socratic Probe Highlight */}
              {m.probe && (
                <div className="mt-2.5 p-2.5 rounded-xl bg-sky-950/40 border border-sky-500/30 text-sky-200 font-medium flex items-start gap-2">
                  <HelpCircle className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                  <span>{m.probe}</span>
                </div>
              )}

              {/* Citations chip */}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5 pt-1.5 border-t border-slate-800/80">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    Verified Citation:
                  </span>
                  {m.citations.map((c: any, i: number) => (
                    <span
                      key={i}
                      className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono"
                    >
                      {c.source || c.ref || "Evidence doc"}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Safety Fallback Card */}
        {isSafetyFallback && (
          <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-200 text-xs space-y-2">
            <div className="flex items-center gap-2 font-semibold">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Evidence Verification Notice</span>
            </div>
            <p className="leading-relaxed text-amber-100/90">
              The AI tutor encountered an evidence-grounding constraint and safely concluded the dialogue. No further responses are needed.
            </p>
            <div className="pt-2">
              <button
                type="button"
                onClick={() => onExitRemediation(currentTurn.session_id)}
                className="w-full py-2.5 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 font-semibold text-xs transition-colors"
              >
                Return to Topics
              </button>
            </div>
          </div>
        )}

        {/* Awaiting Transfer Card */}
        {isAwaitingTransfer && (
          <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-emerald-200 text-xs space-y-2.5 animate-in fade-in duration-200">
            <div className="flex items-center gap-2 font-semibold text-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Socratic Practice Complete</span>
            </div>
            <p className="leading-relaxed text-slate-300">
              You have completed the guided dialogue. To confirm your understanding, take an independent held-out question without clues.
            </p>
            {isTransferAvailable ? (
              <button
                type="button"
                onClick={() => onStartTransfer(currentTurn.session_id)}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/30 transition-all"
              >
                <span>Take Independent Transfer Assessment</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <div className="space-y-2">
                <p className="text-[11px] text-slate-400 italic">
                  Note: A held-out transfer item is not currently available for this question. Dialogue is concluded.
                </p>
                <button
                  type="button"
                  onClick={() => onExitRemediation(currentTurn.session_id)}
                  className="w-full py-2.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition-colors"
                >
                  Return to Topics
                </button>
              </div>
            )}
          </div>
        )}

        {errorText && (
          <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
            {errorText}
          </div>
        )}
      </div>

      {/* Input Area (Only active if not completed and not awaiting transfer) */}
      {!isAwaitingTransfer && !isCompleted && !isSafetyFallback && (
        <div className="bg-slate-900/95 border-t border-slate-800 p-3 sm:p-4 shrink-0 space-y-2">
          {/* Quick preset response chips for mobile speed */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] text-slate-300 scrollbar-none">
            <span className="text-slate-500 text-[10px] shrink-0 uppercase tracking-wider">Suggestions:</span>
            <button
              type="button"
              onClick={() => handleSend("I understand that renin acts directly upon angiotensinogen.")}
              className="px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700/80 shrink-0 text-slate-300"
            >
              Renin acts on angiotensinogen
            </button>
            <button
              type="button"
              onClick={() => handleSend("Can you clarify how juxtaglomerular cells regulate release?")}
              className="px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700/80 shrink-0 text-slate-300"
            >
              Juxtaglomerular release
            </button>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              disabled={isSubmitting}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`Type your Turn ${turnNumber} explanation…`}
              className="flex-1 bg-slate-950 border border-slate-800 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 outline-none transition-colors"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || isSubmitting}
              className={`p-2.5 rounded-xl font-semibold text-xs shrink-0 flex items-center justify-center transition-all ${
                inputText.trim() && !isSubmitting
                  ? "bg-sky-500 hover:bg-sky-400 text-slate-950 shadow-md shadow-sky-500/20"
                  : "bg-slate-800 text-slate-500 cursor-not-allowed"
              }`}
            >
              {isSubmitting ? (
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
