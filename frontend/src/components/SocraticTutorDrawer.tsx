"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import type { TutorChatRequest, TutorChatResponse, TutorMode, DistractorItem, TutorCitationDTO } from "@/lib/types";
import { Sparkles, BookOpen, AlertCircle, Send, CheckCircle2, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";

interface SocraticTutorDrawerProps {
  questionId: string | null;
  topic: string;
  selectedOption: string | null;
  isSubmitted: boolean;
  attemptKey: string | null;
}

interface DialogueTurn {
  id: string;
  role: "user" | "tutor";
  queryText?: string;
  response?: TutorChatResponse;
  timestamp: string;
}

export function SocraticTutorDrawer({
  questionId,
  topic,
  selectedOption,
  isSubmitted,
  attemptKey,
}: SocraticTutorDrawerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [turns, setTurns] = useState<DialogueTurn[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  async function handleSendQuery(query: string, mode: TutorMode = "auto", hintLevel?: number) {
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    const userTurnId = `u-${Date.now()}`;
    const userTurn: DialogueTurn = {
      id: userTurnId,
      role: "user",
      queryText: query,
      timestamp: new Date().toLocaleTimeString(),
    };
    setTurns((prev) => [...prev, userTurn]);
    setInputQuery("");

    try {
      const req: TutorChatRequest = {
        query,
        mode,
        topic: topic || "Renal Physiology",
        question_id: questionId,
        attempt_key: isSubmitted ? attemptKey : null,
        hint_level: hintLevel,
        selected_option: selectedOption,
        is_submitted: isSubmitted,
      };

      const resp = await api.sendTutorChat(req);
      const tutorTurn: DialogueTurn = {
        id: `t-${Date.now()}`,
        role: "tutor",
        response: resp,
        timestamp: new Date().toLocaleTimeString(),
      };
      setTurns((prev) => [...prev, tutorTurn]);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Tutor connection error";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  }

  function toggleCitation(turnId: string) {
    setExpandedCitations((prev) => ({
      ...prev,
      [turnId]: !prev[turnId],
    }));
  }

  return (
    <div className="mt-6 border-t border-slate-700 pt-6">
      {/* Drawer Toggle Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/80 border border-sky-500/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/20 flex items-center justify-center text-sky-400 border border-sky-400/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-100">Socratic Renal Tutor</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> PMC Verified • CC BY
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {isSubmitted
                ? "Post-submission mode: In-depth mechanistic explanations & distractor analysis"
                : "Pre-submission mode: Progressive Socratic hints without answer key disclosure"}
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="px-4 py-2 text-sm font-medium rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors flex items-center gap-2"
        >
          {isOpen ? (
            <>
              Hide Tutor <ChevronUp className="w-4 h-4" />
            </>
          ) : (
            <>
              Ask Socratic Tutor <ChevronDown className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {/* Expanded Tutor Panel */}
      {isOpen && (
        <div className="mt-4 p-5 rounded-2xl bg-slate-900/90 border border-slate-700/80 space-y-6">
          {/* Fast Action Quick Buttons */}
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Quick Inquiries</p>
            <div className="flex flex-wrap gap-2">
              {!isSubmitted ? (
                <>
                  <button
                    disabled={loading}
                    onClick={() => handleSendQuery("I need a hint on the fundamental concept.", "socratic_hint", 1)}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-sky-900/40 border border-slate-700 text-sky-300 disabled:opacity-50"
                  >
                    💡 Level 1: Concept Hint
                  </button>
                  <button
                    disabled={loading}
                    onClick={() => handleSendQuery("How does the underlying physiological mechanism work?", "socratic_hint", 2)}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-sky-900/40 border border-slate-700 text-sky-300 disabled:opacity-50"
                  >
                    🔍 Level 2: Mechanistic Hint
                  </button>
                  <button
                    disabled={loading}
                    onClick={() => handleSendQuery("What is the key relationship needed to solve this?", "socratic_hint", 3)}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-sky-900/40 border border-slate-700 text-sky-300 disabled:opacity-50"
                  >
                    🎯 Level 3: Near-Answer Hint
                  </button>
                </>
              ) : (
                <>
                  <button
                    disabled={loading}
                    onClick={() => handleSendQuery("Explain the underlying mechanism in full detail.", "mechanistic_explanation")}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-sky-900/40 border border-slate-700 text-emerald-300 disabled:opacity-50"
                  >
                    🔬 Detailed Mechanism
                  </button>
                  <button
                    disabled={loading}
                    onClick={() => handleSendQuery("Why are each of the other options incorrect?", "distractor_explanation")}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-sky-900/40 border border-slate-700 text-amber-300 disabled:opacity-50"
                  >
                    ❌ Distractor Analysis
                  </button>
                  <button
                    disabled={loading}
                    onClick={() => handleSendQuery("Provide a concise revision takeaway for this topic.", "revision_summary")}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-sky-900/40 border border-slate-700 text-sky-300 disabled:opacity-50"
                  >
                    📝 Revision Summary
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Dialogue History */}
          <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
            {turns.length === 0 && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-dashed border-slate-800 text-center text-slate-400 text-sm">
                <BookOpen className="w-6 h-6 mx-auto mb-2 text-slate-500" />
                Select a quick hint above or ask any question about the renal physiology mechanisms in this question.
              </div>
            )}

            {turns.map((turn) => (
              <div key={turn.id} className="space-y-3">
                {turn.role === "user" ? (
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-xl px-4 py-2.5 bg-sky-600 text-white text-sm shadow-md">
                      {turn.queryText}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3 max-w-[95%]">
                    <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 text-sm space-y-3">
                      {/* Main Message */}
                      <p className="leading-relaxed">{turn.response?.message}</p>

                      {/* Socratic Question Prompt */}
                      {turn.response?.socratic_question && (
                        <div className="p-3 rounded-lg bg-sky-950/40 border border-sky-500/30 text-sky-200 text-xs">
                          <span className="font-semibold text-sky-400 block mb-1">🤔 Think About This:</span>
                          {turn.response.socratic_question}
                        </div>
                      )}

                      {/* Hints List */}
                      {turn.response?.hints && turn.response.hints.length > 0 && (
                        <div className="space-y-1.5 pt-1">
                          {turn.response.hints.map((h, idx) => (
                            <div key={idx} className="text-xs p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                              {h}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Mechanistic Explanation */}
                      {turn.response?.mechanistic_explanation && (
                        <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-700 text-xs space-y-1">
                          <span className="font-semibold text-emerald-400 block">⚙️ Mechanistic Path:</span>
                          <p className="text-slate-300 leading-relaxed">{turn.response.mechanistic_explanation}</p>
                        </div>
                      )}

                      {/* Distractor Analysis (Post-submission) */}
                      {turn.response?.distractor_analysis && turn.response.distractor_analysis.length > 0 && (
                        <div className="space-y-2 pt-2 border-t border-slate-800">
                          <span className="font-semibold text-xs text-amber-400 block">Distractor Review:</span>
                          <div className="grid gap-2">
                            {turn.response.distractor_analysis.map((d: DistractorItem, didx: number) => (
                              <div key={didx} className="p-2.5 rounded bg-slate-900/60 border border-slate-800 text-xs space-y-1">
                                <div className="flex items-center gap-2 font-medium text-slate-200">
                                  <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-mono">
                                    Option {d.option}
                                  </span>
                                  <span>{d.text}</span>
                                </div>
                                <p className="text-slate-400 pl-1">{d.why_incorrect}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Evidence Citations Accordion */}
                      {turn.response?.citations && turn.response.citations.length > 0 && (
                        <div className="pt-2 border-t border-slate-800">
                          <button
                            onClick={() => toggleCitation(turn.id)}
                            className="flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 font-medium"
                          >
                            <BookOpen className="w-3.5 h-3.5" />
                            {turn.response.citations.length} Verified Evidence Source
                            {turn.response.citations.length > 1 ? "s" : ""}{" "}
                            {expandedCitations[turn.id] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>

                          {expandedCitations[turn.id] && (
                            <div className="mt-2 space-y-2">
                              {turn.response.citations.map((cit: TutorCitationDTO, cidx: number) => (
                                <div key={cidx} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
                                  <div className="flex items-center justify-between gap-2">
                                    <span className="font-medium text-sky-300 truncate">{cit.title}</span>
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono">
                                      {cit.license}
                                    </span>
                                  </div>
                                  <blockquote className="border-l-2 border-sky-500/50 pl-2 text-slate-400 italic text-[11px] leading-relaxed">
                                    &ldquo;{cit.quote}&rdquo;
                                  </blockquote>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Telemetry & Verification Footer */}
                      <div className="pt-2 flex flex-wrap items-center justify-between text-[11px] text-slate-500 border-t border-slate-800/60">
                        <span className="flex items-center gap-1 text-emerald-400/80">
                          <CheckCircle2 className="w-3 h-3" />
                          Zero ungrounded assertions • CC BY Grounded
                        </span>
                        <span>
                          Latency: {Math.round(turn.response?.latency_breakdown?.total_ms || 0)}ms
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-sky-400 p-3 rounded-lg bg-slate-950/40 animate-pulse">
                <Sparkles className="w-4 h-4 animate-spin" />
                Retrieving verified PMC evidence and validating claims...
              </div>
            )}
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Custom Query Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void handleSendQuery(inputQuery);
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={loading}
              placeholder={
                isSubmitted
                  ? "Ask about renal mechanisms, Starling forces, or options..."
                  : "Ask for conceptual guidance (direct answers are withheld)..."
              }
              className="flex-1 px-4 py-2.5 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !inputQuery.trim()}
              className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs disabled:opacity-50 transition-colors flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
