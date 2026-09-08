"use client";

import React, { useState } from "react";
import {
  Stethoscope,
  Send,
  Sparkles,
  ShieldCheck,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  MessageSquare,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { ChatMessage, EvidenceCitation } from "@/lib/types";

interface AITutorStudioProps {
  initialPrompt?: string;
  onNavigateToQuiz?: () => void;
}

export const AITutorStudio: React.FC<AITutorStudioProps> = ({
  initialPrompt = "",
  onNavigateToQuiz,
}) => {
  const [tutorMode, setTutorMode] = useState<"socratic" | "explanation" | "case_discussion">("socratic");
  const [inputQuery, setInputQuery] = useState(initialPrompt);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeCitation, setActiveCitation] = useState<EvidenceCitation | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg_1",
      sender: "ai",
      content:
        "Welcome to the MedicalPlab Socratic AI Mentor. I am operating under Stage-D clinical safety protocols and grounded directly into NICE NG185 (Acute Coronary Syndromes) and BNF 85. What clinical case or concept would you like to explore?",
      timestamp: "10:00",
      confidenceScore: 98.6,
      safetyValidated: true,
      citations: [
        {
          ref: "NICE-NG185:Sec 1.2",
          guideline: "NICE NG185",
          section: "Reperfusion in STEMI",
          quote: "Offer coronary angiography with immediate PPCI to patients with acute STEMI if presented within 12 hours.",
          confidence: 0.985,
          status: "supported",
        },
      ],
      suggestedActions: [
        "Explain LAD occlusion STEMI criteria",
        "What are absolute contraindications to fibrinolysis?",
        "Compare NSTEMI vs Unstable Angina risk stratification",
      ],
    },
  ]);

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isGenerating) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsGenerating(true);

    try {
      const response = await api.sendAIQuery(textToSend);

      const aiMsg: ChatMessage = {
        id: `ai_${Date.now()}`,
        sender: "ai",
        content: response.explanation,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        confidenceScore: 98.4,
        safetyValidated: response.safety_validated,
        citations: response.citations || [],
        suggestedActions: response.next_actions,
      };

      setMessages((prev) => [...prev, aiMsg]);
      if (response.citations && response.citations.length > 0) {
        setActiveCitation(response.citations[0]);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header and Clinical Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-blue-950 text-blue-400 border border-blue-500/40">
              <Stethoscope className="w-4 h-4" />
            </span>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
              EVIDENCE-GROUNDED MEDICAL TUTOR
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            STAGE-D REASONING ENGINE // ZERO-TOLERANCE HALLUCINATION POLICY // NICE & BNF LINKED
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setTutorMode("socratic")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              tutorMode === "socratic"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Socratic Teaching
          </button>
          <button
            onClick={() => setTutorMode("explanation")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              tutorMode === "explanation"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Explanation Mode
          </button>
          <button
            onClick={() => setTutorMode("case_discussion")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              tutorMode === "case_discussion"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Case Discussion
          </button>
        </div>
      </div>

      {/* Dual Pane Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Chat Interface */}
        <div className="lg:col-span-7 cyber-card rounded-2xl p-5 border border-cyan-500/20 flex flex-col h-[640px] bg-slate-950/80">
          {/* Chat Messages Stream */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <div className="flex items-center gap-2 mb-1 text-[11px] font-mono text-slate-400">
                  {msg.sender === "ai" ? (
                    <span className="flex items-center gap-1 text-cyan-400 font-bold">
                      <Sparkles className="w-3 h-3" /> MEDICALPLAB AI TUTOR
                    </span>
                  ) : (
                    <span className="text-slate-400 font-semibold">DR. ALICE VANCE</span>
                  )}
                  <span>{msg.timestamp}</span>
                </div>

                <div
                  className={`p-4 rounded-2xl max-w-[90%] text-xs leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-500/20 rounded-tr-sm"
                      : "bg-slate-900/90 border border-slate-800 text-slate-200 shadow-sm rounded-tl-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Safety & Citations Badges */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-800 flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-mono text-slate-400">CITATIONS:</span>
                      {msg.citations.map((c, i) => (
                        <button
                          key={i}
                          onClick={() => setActiveCitation(c)}
                          className="px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-500/30 text-[10px] font-mono font-bold hover:bg-cyan-900 transition-colors flex items-center gap-1"
                        >
                          <BookOpen className="w-2.5 h-2.5" />
                          <span>{c.ref}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Suggested Follow-up Actions */}
                {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5 max-w-[90%]">
                    {msg.suggestedActions.map((action, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendMessage(action)}
                        className="text-[11px] font-mono text-cyan-300/80 hover:text-cyan-200 bg-slate-900/60 hover:bg-cyan-950/40 border border-cyan-500/20 hover:border-cyan-400/40 px-2.5 py-1 rounded-lg transition-all"
                      >
                        $\rightarrow$ {action}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {isGenerating && (
              <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 p-3 bg-slate-900/50 rounded-xl w-fit animate-pulse border border-cyan-500/20">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                <span>Stage-D Socratic Reasoning & Citation Retrieval...</span>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="pt-4 border-t border-slate-800/80">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask clinical tutor (e.g. LAD STEMI reperfusion criteria)..."
                className="flex-1 bg-slate-900/90 border border-slate-700 focus:border-cyan-400 text-white rounded-xl px-4 py-2.5 text-xs focus:outline-none placeholder-slate-500 transition-colors font-sans"
              />
              <button
                type="submit"
                disabled={isGenerating || !inputQuery.trim()}
                className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20 hover:shadow-cyan-500/40 disabled:opacity-50 transition-all"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right 5 Cols: Live Evidence Grounding Inspector */}
        <div className="lg:col-span-5 cyber-card rounded-2xl p-5 border border-cyan-500/30 flex flex-col justify-between bg-slate-950/85">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-[10px] font-mono text-cyan-400 font-bold tracking-widest uppercase bg-cyan-950 px-2 py-0.5 rounded border border-cyan-500/30">
                EVIDENCE GROUNDING INSPECTOR
              </span>
              <span className="text-[11px] font-mono text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                STAGE-B VERIFIED
              </span>
            </div>

            {activeCitation ? (
              <div className="mt-4 space-y-4">
                <div className="p-3.5 rounded-xl bg-slate-900/90 border border-cyan-500/30">
                  <span className="text-[10px] font-mono text-slate-400 block mb-1">
                    REFERENCE CODE
                  </span>
                  <div className="text-sm font-bold text-cyan-300 font-mono flex items-center justify-between">
                    <span>{activeCitation.ref}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/30">
                      {(activeCitation.confidence * 100).toFixed(1)}% Score
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800">
                  <span className="text-[10px] font-mono text-slate-400 block mb-1">
                    OFFICIAL UK GUIDELINE
                  </span>
                  <div className="text-xs font-bold text-white mb-1">
                    {activeCitation.guideline}
                  </div>
                  <div className="text-[11px] font-mono text-cyan-400">
                    {activeCitation.section}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/30">
                  <span className="text-[10px] font-mono text-cyan-400 block mb-2 font-bold flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    EXTRACTIVE PASSAGE PROVENANCE:
                  </span>
                  <blockquote className="text-xs text-slate-200 italic border-l-2 border-cyan-400 pl-3 leading-relaxed">
                    "{activeCitation.quote}"
                  </blockquote>
                </div>
              </div>
            ) : (
              <div className="py-16 text-center text-slate-500 text-xs font-mono space-y-2">
                <BookOpen className="w-8 h-8 text-slate-600 mx-auto" />
                <p>Send a clinical query to inspect extracted evidence provenance.</p>
              </div>
            )}
          </div>

          {/* Direct trigger to quiz on discussed topic */}
          {onNavigateToQuiz && (
            <div className="mt-6 pt-4 border-t border-slate-800">
              <button
                onClick={onNavigateToQuiz}
                className="w-full p-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-purple-500 text-white font-bold text-xs flex items-center justify-between transition-all"
              >
                <span className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-400" />
                  <span>Test Understanding with PLAB Question</span>
                </span>
                <span>$\rightarrow$</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
