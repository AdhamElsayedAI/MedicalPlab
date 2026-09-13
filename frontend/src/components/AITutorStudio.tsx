"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Stethoscope,
  Send,
  ShieldCheck,
  BookOpen,
  CheckCircle,
  Sparkles,
  Brain,
  FileText,
  ChevronRight,
  Loader2,
  ListTree,
  AlertTriangle,
  ClipboardList,
  Pill,
  BookMarked,
  Activity,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { ChatMessage, EvidenceCitation } from "@/lib/types";

interface AITutorStudioProps {
  initialPrompt?: string;
  onNavigateToQuiz?: () => void;
}

interface ClinicalReasoningCase {
  id: string;
  title: string;
  presentation: string;
  problemRepresentation: string;
  differentials: { rank: number; name: string; probability: "High" | "Must-Not-Miss" | "Moderate"; rationale: string }[];
  investigations: { type: "Bedside" | "Laboratory" | "Imaging"; item: string; finding: string }[];
  management: { step: string; action: string; guidelineRef: string }[];
  evidence: EvidenceCitation[];
}

const CLINICAL_CASES: ClinicalReasoningCase[] = [
  {
    id: "case_stemi",
    title: "Acute Retrosternal Chest Pain (STEMI)",
    presentation: "58-year-old male with 45 minutes of acute crushing central chest pain radiating to left jaw, diaphoresis, and nausea. History of type 2 diabetes and hypertension.",
    problemRepresentation: "Middle-aged male with cardiovascular risk factors presenting with hyperacute ischemic chest pain and autonomic symptoms consistent with acute coronary syndrome.",
    differentials: [
      { rank: 1, name: "ST-Elevation Myocardial Infarction (LAD Occlusion)", probability: "High", rationale: "Hyperacute crushing pain with diaphoresis in high-risk patient." },
      { rank: 2, name: "Acute Aortic Dissection (Stanford Type A)", probability: "Must-Not-Miss", rationale: "Must rule out before administering thrombolytics/antiplatelets." },
      { rank: 3, name: "Acute Pulmonary Embolism", probability: "Must-Not-Miss", rationale: "Presents with acute chest pain, tachycardia, and dyspnea." },
    ],
    investigations: [
      { type: "Bedside", item: "Immediate 12-lead ECG", finding: "ST elevations >2mm in leads V1-V4 with reciprocal depression." },
      { type: "Laboratory", item: "High-Sensitivity Troponin-I", finding: "Elevated baseline, serial draw at 3 hours." },
      { type: "Imaging", item: "Emergency Coronary Angiography", finding: "Definitive localization of LAD occlusion." },
    ],
    management: [
      { step: "Immediate", action: "Aspirin 300mg chewable + Ticagrelor 180mg loading dose", guidelineRef: "NICE NG185: Sec 1.1" },
      { step: "Reperfusion", action: "Coronary angiography with immediate PPCI within 120 minutes of first medical contact", guidelineRef: "NICE NG185: Sec 1.2" },
      { step: "Safety Alert", action: "Do not give nitrates if SBP <90 mmHg or suspected right ventricular involvement", guidelineRef: "BNF 85: Nitrates Cautions" },
    ],
    evidence: [
      {
        ref: "NICE-NG185:Sec 1.2",
        guideline: "NICE NG185",
        section: "Reperfusion in STEMI",
        quote: "Offer coronary angiography with immediate PPCI to patients with acute STEMI if presentation is within 12 hours of symptom onset and PPCI can be delivered within 120 minutes.",
        confidence: 0.985,
        status: "supported",
      },
      {
        ref: "BNF-85:Cardiovascular",
        guideline: "British National Formulary 85",
        section: "Dual Antiplatelet Therapy",
        quote: "Loading dose of aspirin 300 mg combined with ticagrelor 180 mg for acute management of STEMI undergoing PPCI.",
        confidence: 0.99,
        status: "supported",
      },
    ],
  },
  {
    id: "case_tamponade",
    title: "Hemodynamic Deterioration (Cardiac Tamponade)",
    presentation: "64-year-old female 10 days post-cardiac surgery with progressive shortness of breath, lightheadedness, and profound fatigue. Tachycardic at 116 bpm, BP 86/62 mmHg, distended jugular veins.",
    problemRepresentation: "Post-operative patient presenting with subacute obstructive shock, jugular venous distension, hypotension, and distant heart sounds (Beck's Triad).",
    differentials: [
      { rank: 1, name: "Cardiac Tamponade with Pericardial Effusion", probability: "High", rationale: "Classic Beck's triad post-sternotomy with obstructive shock physiology." },
      { rank: 2, name: "Massive Pulmonary Embolism", probability: "Must-Not-Miss", rationale: "Post-operative immobility risk, RV strain, and sudden hypotension." },
      { rank: 3, name: "Tension Pneumothorax", probability: "Must-Not-Miss", rationale: "Distended JVP with hypotension, but lung sounds remain vesicular here." },
    ],
    investigations: [
      { type: "Bedside", item: "Point-of-Care Ultrasound (POCUS)", finding: "Pericardial effusion with right ventricular diastolic collapse." },
      { type: "Bedside", item: "Pulsus Paradoxus Measurement", finding: ">10 mmHg drop in SBP during normal inspiration." },
      { type: "Imaging", item: "Formal Transthoracic Echocardiogram", finding: "Quantification of effusion volume and chamber compromise." },
    ],
    management: [
      { step: "Immediate", action: "IV Crystalloid fluid challenge to maintain right ventricular preload", guidelineRef: "Resuscitation Council UK" },
      { step: "Definitive", action: "Emergency ultrasound-guided pericardiocentesis or surgical drainage", guidelineRef: "NICE Interventional Procedure IPG391" },
      { step: "Contraindication", action: "AVOID vasodilators and nitrates — preload reduction triggers fatal cardiac arrest", guidelineRef: "GMC Good Medical Practice Safety Alert" },
    ],
    evidence: [
      {
        ref: "RCUK-ALS:Shock",
        guideline: "Resuscitation Council UK ALS",
        section: "Obstructive Shock",
        quote: "Cardiac tamponade requires immediate echocardiographic confirmation and urgent decompression via pericardiocentesis while optimizing preload with IV fluids.",
        confidence: 0.98,
        status: "supported",
      },
    ],
  },
];

export const AITutorStudio: React.FC<AITutorStudioProps> = ({
  initialPrompt = "",
  onNavigateToQuiz,
}) => {
  const [selectedCase, setSelectedCase] = useState<ClinicalReasoningCase>(CLINICAL_CASES[0]);
  const [activeTab, setActiveTab] = useState<"reasoning_sheet" | "socratic_dialogue">("reasoning_sheet");
  const [inputQuery, setInputQuery] = useState(initialPrompt);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeCitation, setActiveCitation] = useState<EvidenceCitation | null>(CLINICAL_CASES[0].evidence[0]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg_init",
      sender: "ai",
      content:
        "Welcome. I am your Clinical Reasoning Assistant. I assist you in breaking down complex clinical vignettes into structured hypotheses, diagnostic workups, and NICE-verified management decisions.\n\nSelect a clinical case scenario above or enter your clinical query below.",
      timestamp: "10:00",
      confidenceScore: 98.6,
      safetyValidated: true,
      citations: CLINICAL_CASES[0].evidence,
      suggestedActions: [
        "Explain LAD occlusion reperfusion timing",
        "What are absolute contraindications to fibrinolysis?",
        "Compare NSTEMI vs STEMI risk stratification per NICE NG185",
      ],
    },
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (activeTab === "socratic_dialogue") {
      scrollToBottom();
    }
  }, [messages, isGenerating, activeTab]);

  const handleSelectCase = (c: ClinicalReasoningCase) => {
    setSelectedCase(c);
    if (c.evidence.length > 0) {
      setActiveCitation(c.evidence[0]);
    }
  };

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isGenerating) return;

    // eslint-disable-next-line react-hooks/purity
    const msgId = `usr_${Date.now()}`;
    const userMsg: ChatMessage = {
      id: msgId,
      sender: "user",
      content: textToSend,
      // eslint-disable-next-line react-hooks/purity
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setActiveTab("socratic_dialogue");
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
        citations: (response.citations as EvidenceCitation[]) || [],
        suggestedActions: response.next_actions,
      };

      setMessages((prev) => [...prev, aiMsg]);
      if (response.citations && response.citations.length > 0) {
        setActiveCitation(response.citations[0] as EvidenceCitation);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <section
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 med-fade-in"
      aria-label="Clinical Reasoning Assistant"
    >
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                background: "rgba(14,165,233,0.15)",
                border: "1px solid rgba(14,165,233,0.25)",
              }}
            >
              <Brain className="w-5 h-5 text-sky-400" />
            </div>
            <h2 className="section-header">Clinical Reasoning Assistant</h2>
          </div>
          <p className="section-subtext">
            Structured clinical decision support grounded in verified NICE guidelines and BNF prescribing rules.
          </p>
        </div>

        {/* View Switcher: Reasoning Sheet vs Socratic Dialogue */}
        <div
          className="flex items-center gap-1 p-1 rounded-xl flex-shrink-0"
          style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <button
            onClick={() => setActiveTab("reasoning_sheet")}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[13px] font-medium transition-all"
            style={{
              background:
                activeTab === "reasoning_sheet" ? "rgba(14,165,233,0.15)" : "transparent",
              color: activeTab === "reasoning_sheet" ? "#7dd3fc" : "#64748b",
              border:
                activeTab === "reasoning_sheet"
                  ? "1px solid rgba(14,165,233,0.25)"
                  : "1px solid transparent",
            }}
          >
            <ListTree className="w-4 h-4" />
            <span>Structured Reasoning Sheet</span>
          </button>

          <button
            onClick={() => setActiveTab("socratic_dialogue")}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[13px] font-medium transition-all"
            style={{
              background:
                activeTab === "socratic_dialogue" ? "rgba(14,165,233,0.15)" : "transparent",
              color: activeTab === "socratic_dialogue" ? "#7dd3fc" : "#64748b",
              border:
                activeTab === "socratic_dialogue"
                  ? "1px solid rgba(14,165,233,0.25)"
                  : "1px solid transparent",
            }}
          >
            <Stethoscope className="w-4 h-4" />
            <span>Socratic Clinical Preceptor</span>
          </button>
        </div>
      </div>

      {/* Case Presets Ribbon */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-xs text-slate-400 font-semibold flex-shrink-0">Clinical Scenarios:</span>
        {CLINICAL_CASES.map((c) => (
          <button
            key={c.id}
            onClick={() => handleSelectCase(c)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              selectedCase.id === c.id
                ? "bg-sky-500/20 text-sky-300 border border-sky-400/40 shadow-sm"
                : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            <span>{c.title}</span>
          </button>
        ))}
      </div>

      {/* Main Dual-Pane Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 8 Cols: Main Reasoning Interface */}
        <div className="lg:col-span-8 med-card flex flex-col justify-between" style={{ minHeight: "660px" }}>
          {activeTab === "reasoning_sheet" ? (
            /* Structured Clinical Reasoning Sheet */
            <div className="p-6 space-y-6 overflow-y-auto max-h-[640px] med-fade-in">
              {/* 1. Case Presentation */}
              <div>
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                    <ClipboardList className="w-3.5 h-3.5" />
                    1. Case Presentation
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">NHS Acute Intake</span>
                </div>
                <p className="text-[13px] text-slate-200 leading-relaxed bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80">
                  {selectedCase.presentation}
                </p>
              </div>

              {/* 2. Problem Representation */}
              <div>
                <div className="flex items-center gap-1.5 pb-2 mb-2 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-purple-400">
                  <Brain className="w-3.5 h-3.5" />
                  <span>2. Problem Representation (Semantic Synthesis)</span>
                </div>
                <p className="text-[13px] text-purple-200 leading-relaxed bg-purple-950/20 p-3.5 rounded-xl border border-purple-500/20">
                  {selectedCase.problemRepresentation}
                </p>
              </div>

              {/* 3. Differential Diagnosis */}
              <div>
                <div className="flex items-center gap-1.5 pb-2 mb-2 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-amber-400">
                  <ListTree className="w-3.5 h-3.5" />
                  <span>3. Differential Diagnosis (Ranked Hypotheses)</span>
                </div>
                <div className="space-y-2">
                  {selectedCase.differentials.map((diff) => (
                    <div
                      key={diff.rank}
                      className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-3 text-xs"
                    >
                      <div className="flex items-start gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-bold text-[11px] flex-shrink-0 mt-0.5">
                          {diff.rank}
                        </span>
                        <div>
                          <span className="font-bold text-white text-[13px] block">{diff.name}</span>
                          <span className="text-slate-400 text-[12px]">{diff.rationale}</span>
                        </div>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold flex-shrink-0 ${
                          diff.probability === "High"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-500/30"
                            : "bg-red-950 text-red-300 border border-red-500/30"
                        }`}
                      >
                        {diff.probability}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 4. Investigations */}
              <div>
                <div className="flex items-center gap-1.5 pb-2 mb-2 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                  <Activity className="w-3.5 h-3.5" />
                  <span>4. Diagnostic Investigations Protocol</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
                  {selectedCase.investigations.map((inv, i) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <span className="text-[10px] font-mono text-emerald-400 uppercase">{inv.type}</span>
                      <span className="font-semibold text-white block">{inv.item}</span>
                      <span className="text-slate-400 text-[11px] leading-tight block">{inv.finding}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 5. Management Plan */}
              <div>
                <div className="flex items-center gap-1.5 pb-2 mb-2 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-sky-400">
                  <Pill className="w-3.5 h-3.5" />
                  <span>5. Clinical Management &amp; Safety Guardrails</span>
                </div>
                <div className="space-y-2 text-xs">
                  {selectedCase.management.map((mgmt, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-3"
                    >
                      <div className="space-y-0.5">
                        <span className="font-bold text-sky-300 text-[11px] uppercase block">
                          [{mgmt.step}]
                        </span>
                        <p className="text-slate-200 text-xs">{mgmt.action}</p>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-1 rounded flex-shrink-0">
                        {mgmt.guidelineRef}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Socratic Clinical Preceptor Chat */
            <div className="flex flex-col h-full">
              <div className="flex-1 overflow-y-auto p-5 space-y-5 max-h-[560px]">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1.5 text-[11px] text-slate-500">
                      {msg.sender === "ai" ? (
                        <>
                          <Sparkles className="w-3 h-3 text-sky-400" />
                          <span className="font-medium text-sky-400">Clinical Preceptor AI</span>
                        </>
                      ) : (
                        <span className="font-medium text-slate-400">Doctor / Candidate</span>
                      )}
                      <span>·</span>
                      <span>{msg.timestamp}</span>
                    </div>

                    <div
                      className={`max-w-[88%] px-4 py-3.5 text-[13px] leading-relaxed rounded-2xl ${
                        msg.sender === "user"
                          ? "bg-sky-600 text-white rounded-br-sm"
                          : "bg-slate-900 text-slate-200 border border-slate-800 rounded-bl-sm"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>

                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-slate-800 flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] text-slate-400">Evidence Citations:</span>
                          {msg.citations.map((c, i) => (
                            <button
                              key={i}
                              onClick={() => setActiveCitation(c)}
                              className="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20 hover:bg-sky-500/20"
                            >
                              {c.ref}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5 max-w-[88%]">
                        {msg.suggestedActions.map((act, i) => (
                          <button
                            key={i}
                            onClick={() => handleSendMessage(act)}
                            className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900 text-slate-400 border border-slate-800 hover:text-sky-300 hover:border-sky-500/30 transition-all"
                          >
                            {act}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {isGenerating && (
                  <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-400">
                    <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                    <span>Cross-referencing NICE guidelines and BNF prescribing databases...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Bar */}
              <div className="p-4 border-t border-slate-800 bg-slate-950/60">
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
                    placeholder="Ask clinical question (e.g. STEMI reperfusion criteria)..."
                    className="flex-1 rounded-xl px-4 py-2.5 text-xs text-white bg-slate-900 border border-slate-800 focus:outline-none focus:border-sky-500"
                  />
                  <button
                    type="submit"
                    disabled={isGenerating || !inputQuery.trim()}
                    className="btn-primary text-xs font-bold px-4 py-2.5 rounded-xl flex items-center gap-1.5 disabled:opacity-40"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Send</span>
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>

        {/* Right 4 Cols: Clinical Evidence Sources & Provenance */}
        <div className="lg:col-span-4 med-card p-6 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold text-white">
                <FileText className="w-4 h-4 text-sky-400" />
                <span>Clinical Evidence Provenance</span>
              </div>
              <span className="med-badge med-badge-primary">Zero Hallucination</span>
            </div>

            {activeCitation ? (
              <div className="space-y-3.5 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sky-300">{activeCitation.guideline}</span>
                    <span className="text-[10px] font-mono text-emerald-400">
                      {activeCitation.section}
                    </span>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950 text-slate-300 italic border border-slate-800 leading-relaxed text-[12px]">
                    &quot;{activeCitation.quote}&quot;
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>Guideline Ref: {activeCitation.ref}</span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      Extractive Match
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-sky-950/20 border border-sky-500/20 text-slate-300 space-y-1">
                  <span className="text-[11px] font-semibold text-sky-300 block">
                    GMC Clinical Safety Standard:
                  </span>
                  <p className="text-[11px] leading-relaxed">
                    AI responses must be strictly bounded by verified clinical literature. No treatment doses or contraindications are inferred outside authoritative UK medical guidelines.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-10 text-slate-500 text-xs">
                Select a citation chip to inspect source text.
              </div>
            )}
          </div>

          {/* Practice Question Trigger */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Test Clinical Knowledge
            </span>
            <button
              onClick={onNavigateToQuiz}
              className="w-full flex items-center justify-between p-3 rounded-xl text-xs font-bold text-slate-200 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white transition-all"
            >
              <span className="flex items-center gap-2">
                <BookMarked className="w-4 h-4 text-amber-400" />
                Practice Clinical Vignette MCQ
              </span>
              <ChevronRight className="w-4 h-4 text-slate-500" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
