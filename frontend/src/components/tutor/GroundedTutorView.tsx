"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import {
  Sparkles,
  Send,
  ShieldCheck,
  AlertTriangle,
  BookOpen,
  FileText,
  ChevronDown,
  ChevronUp,
  Loader2,
  HelpCircle,
  ExternalLink,
  BrainCircuit,
  Lightbulb,
  CheckCircle2,
  XCircle,
  Quote,
} from "lucide-react";
import { api, getAuthoritativeLearnerId } from "@/lib/api-client";
import type { TutorChatResponse } from "@/lib/types";

interface ChatTurn {
  id: string;
  sender: "student" | "tutor";
  timestamp: string;
  query?: string;
  response?: TutorChatResponse;
}

const DEFAULT_PROMPTS = [
  {
    topic: "RAAS mechanisms",
    prompt: "In the renin-angiotensin pathway, how does active renin act on angiotensinogen?",
  },
  {
    topic: "Glomerular filtration barrier",
    prompt: "Explain the three physical layers of the glomerular filtration barrier and podocyte slit diaphragms.",
  },
  {
    topic: "Renal hemodynamics",
    prompt: "How do afferent vs efferent arteriole resistance changes affect GFR and filtration fraction?",
  },
  {
    topic: "Juxtaglomerular apparatus",
    prompt: "What triggers renin secretion from the granular juxtaglomerular cells in the afferent arteriole?",
  },
];

export const GroundedTutorView: React.FC = () => {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("query") || "";
  const initialTopic = searchParams.get("topic") || "Renal physiology";

  const [inputQuery, setInputQuery] = useState(initialQuery);
  const [activeTopic, setActiveTopic] = useState(initialTopic);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});
  const [learnerId, setLearnerId] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = getAuthoritativeLearnerId();
    setLearnerId(id);

    // Initial greeting from tutor
    const initialTurn: ChatTurn = {
      id: "welcome-tutor-001",
      sender: "tutor",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      response: {
        response_id: "WELCOME-001",
        session_id: "welcome-session",
        mode: "auto",
        message:
          "Welcome to the Evidence-Grounded Socratic Tutor. I assist medical students by explaining physiological and clinical concepts using verified peer-reviewed literature. Every proposition is checked against our verified active medical corpus. Ask a question below or choose a high-yield clinical topic.",
        socratic_question: "Which renal physiology topic would you like to explore today?",
        hints: null,
        misconception: null,
        mechanistic_explanation: null,
        distractor_analysis: null,
        revision_summary: null,
        citations: [],
        support_status: "SUPPORTED",
        abstain: false,
        abstain_reason: null,
        fallback_applied: false,
        pedagogical_state: "GENERAL_STUDY",
      } as any,
    };
    setTurns([initialTurn]);

    // If query in URL, auto send
    if (initialQuery) {
      sendMessage(initialQuery, initialTopic);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, loading]);

  const sendMessage = async (queryText: string, topicText: string) => {
    const query = queryText.trim();
    if (!query || loading) return;

    const studentTurn: ChatTurn = {
      id: `student-${Date.now()}`,
      sender: "student",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      query,
    };

    setTurns((prev) => [...prev, studentTurn]);
    setInputQuery("");
    setLoading(true);

    try {
      const resp = await api.sendTutorChat({
        query,
        topic: topicText || activeTopic,
        mode: "auto",
      });

      const tutorTurn: ChatTurn = {
        id: `tutor-${Date.now()}`,
        sender: "tutor",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        response: resp,
      };

      setTurns((prev) => [...prev, tutorTurn]);
    } catch (err: any) {
      const errorTurn: ChatTurn = {
        id: `tutor-err-${Date.now()}`,
        sender: "tutor",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        response: {
          response_id: "ERR-001",
          session_id: "err-session",
          mode: "auto",
          message:
            "I could not connect to the Socratic tutor service right now. Please verify backend connectivity.",
          socratic_question: null,
          hints: null,
          citations: [],
          support_status: "SAFE_FALLBACK",
        } as any,
      };
      setTurns((prev) => [...prev, errorTurn]);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputQuery, activeTopic);
  };

  const toggleCitation = (turnId: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [turnId]: !prev[turnId],
    }));
  };

  const renderSupportStatusBadge = (status?: string, fallbackApplied?: boolean) => {
    if (status === "SUPPORTED" && !fallbackApplied) {
      return (
        <span className="med-badge med-badge-success flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          <span>Evidence Supported (CC BY 4.0)</span>
        </span>
      );
    }
    if (status === "SAFE_FALLBACK" || fallbackApplied) {
      return (
        <span className="med-badge med-badge-warning flex items-center gap-1">
          <ShieldCheck className="w-3 h-3 text-amber-400" />
          <span>Fail-Closed Socratic Guidance</span>
        </span>
      );
    }
    if (status === "ABSTAIN") {
      return (
        <span className="med-badge med-badge-danger flex items-center gap-1">
          <AlertTriangle className="w-3 h-3 text-rose-400" />
          <span>Clinical Governance Abstain</span>
        </span>
      );
    }
    return (
      <span className="med-badge med-badge-primary flex items-center gap-1">
        <Sparkles className="w-3 h-3 text-sky-400" />
        <span>Grounded Analysis</span>
      </span>
    );
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 med-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="med-badge med-badge-primary">Grounded Socratic Preceptor</span>
            <span className="text-xs text-slate-400">Zero Clinical Hallucination</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-['Plus_Jakarta_Sans',sans-serif]">
            Evidence-Grounded AI Medical Tutor
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Peer-reviewed citations from active CC BY 4.0 medical literature with proposition-level verification.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white/[0.03] border border-white/[0.08] px-3 py-1.5 rounded-xl text-xs text-slate-300">
          <span className="text-slate-400">Context:</span>
          <span className="font-semibold text-sky-300">{activeTopic}</span>
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
          High-Yield Practice Queries
        </span>
        <div className="flex flex-wrap gap-2">
          {DEFAULT_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setActiveTopic(p.topic);
                setInputQuery(p.prompt);
                sendMessage(p.prompt, p.topic);
              }}
              className="text-left text-xs bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.08] hover:border-sky-500/30 text-slate-300 hover:text-white px-3 py-2 rounded-xl transition-all max-w-sm truncate"
            >
              <span className="text-sky-400 font-semibold mr-1.5">{p.topic}:</span>
              <span>{p.prompt}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Conversation Turns */}
      <div className="space-y-6 pt-2">
        {turns.map((turn) => {
          if (turn.sender === "student") {
            return (
              <div key={turn.id} className="flex justify-end">
                <div className="max-w-2xl bg-gradient-to-br from-sky-600/90 to-blue-700/90 text-white p-4 rounded-2xl rounded-tr-sm shadow-md text-sm leading-relaxed">
                  <div className="text-[10px] text-sky-200/80 mb-1 flex items-center justify-between">
                    <span>Medical Student</span>
                    <span>{turn.timestamp}</span>
                  </div>
                  {turn.query}
                </div>
              </div>
            );
          }

          const resp = turn.response;
          if (!resp) return null;

          const isExpanded = !!expandedCitations[turn.id];
          const hasCitations = resp.citations && resp.citations.length > 0;

          return (
            <div key={turn.id} className="flex justify-start">
              <div className="max-w-3xl w-full med-card p-6 space-y-4 border border-white/[0.1] rounded-2xl rounded-tl-sm">
                {/* Tutor Card Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-white/[0.08]">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="font-bold text-white text-sm block">Grounded Clinical Tutor</span>
                      <span className="text-[10px] text-slate-400">Peer-Reviewed Socratic Guidance</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {renderSupportStatusBadge(resp.support_status, resp.fallback_applied)}
                    <span className="text-[11px] text-slate-500">{turn.timestamp}</span>
                  </div>
                </div>

                {/* Key Learning Point / Concept (if available) */}
                {resp.revision_summary && (
                  <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-xs text-emerald-100 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-emerald-300 block mb-0.5 font-semibold">Key Clinical Concept</strong>
                      <p className="leading-relaxed">{resp.revision_summary}</p>
                    </div>
                  </div>
                )}

                {/* Main Clinical Explanation */}
                <div className="space-y-1.5 pt-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                    Mechanistic Explanation
                  </span>
                  <div className="text-sm text-slate-100 leading-relaxed space-y-2 bg-white/[0.02] p-4 rounded-xl border border-white/[0.05]">
                    <p>{resp.message}</p>
                  </div>
                </div>

                {/* Socratic Probe Callout */}
                {resp.socratic_question && (
                  <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/25 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-sky-300">
                      <Lightbulb className="w-4 h-4 text-sky-400" />
                      <span>Socratic Reasoning Probe:</span>
                    </div>
                    <p className="text-xs text-sky-100 leading-relaxed pl-5 font-medium">
                      {resp.socratic_question}
                    </p>
                  </div>
                )}

                {/* Progressive Disclosure Hints */}
                {resp.hints && resp.hints.length > 0 && (
                  <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                      Guiding Clues
                    </span>
                    <ul className="space-y-1 text-xs text-slate-300">
                      {resp.hints.map((hint, hIdx) => (
                        <li key={hIdx} className="flex items-start gap-2">
                          <span className="text-sky-400 font-bold">•</span>
                          <span>{hint}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Extractive Literature Citations */}
                {hasCitations && (
                  <div className="pt-2 border-t border-white/[0.06]">
                    <button
                      onClick={() => toggleCitation(turn.id)}
                      className="flex items-center justify-between w-full py-1.5 text-xs text-slate-300 hover:text-white font-medium transition-colors"
                    >
                      <span className="flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-sky-400" />
                        <span>Peer-Reviewed Citations ({resp.citations.length} verified references)</span>
                      </span>
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    {isExpanded && (
                      <div className="mt-3 space-y-2.5 med-fade-in">
                        {resp.citations.map((cite: any, cIdx: number) => (
                          <div
                            key={cIdx}
                            className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.08] space-y-1.5 text-xs"
                          >
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="font-bold text-sky-300">
                                {cite.document_id || cite.ref || `Source #${cIdx + 1}`}
                              </span>
                              {cite.pmcid && (
                                <span className="font-mono text-[10px] text-slate-400 bg-white/[0.04] px-1.5 py-0.5 rounded">
                                  {cite.pmcid}
                                </span>
                              )}
                            </div>
                            {cite.quote && (
                              <blockquote className="text-slate-300 italic border-l-2 border-sky-400/50 pl-2.5 py-0.5 my-1 text-[11px] leading-relaxed">
                                &ldquo;{cite.quote}&rdquo;
                              </blockquote>
                            )}
                            {cite.license && (
                              <span className="text-[10px] text-slate-500 block">
                                License: {cite.license}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Verification Metadata (Subtle) */}
                {resp.verification && (
                  <div className="flex items-center justify-between pt-2 border-t border-white/[0.04] text-[10px] text-slate-500">
                    <span>Propositions Verified: {resp.verification.total_propositions} verified statements</span>
                    <span>Veto Flags: {resp.verification.veto_flags.length === 0 ? "0 (Safe)" : resp.verification.veto_flags.join(", ")}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="med-card p-4 rounded-2xl flex items-center gap-3 text-xs text-slate-400">
              <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
              <span>Checking verified medical corpus & formulating Socratic response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={handleFormSubmit}
        className="sticky bottom-20 md:bottom-4 z-20 pt-2"
      >
        <div className="relative flex items-center rounded-2xl bg-[#0f172a]/95 border border-white/[0.12] shadow-2xl shadow-black p-2 focus-within:border-sky-400/60 focus-within:ring-1 focus-within:ring-sky-400/40">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask a physiological mechanism or clinical case question..."
            disabled={loading}
            className="flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || loading}
            className="btn-primary text-xs py-2 px-4 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span className="hidden sm:inline">Inquire</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
        <p className="text-[10px] text-slate-500 text-center mt-1.5">
          MedicalPlab verifies clinical claims against open-access literature. Unsupported claims fail closed into Socratic guidance.
        </p>
      </form>
    </div>
  );
};
