"use client";

/**
 * MedicalPlab Reference Mobile Client & API Contract Harness
 * 
 * NOTE: This is NOT the production mobile application.
 * This is a reference client and API contract harness designed to:
 * 1. Validate frozen backend REST API contracts
 * 2. Provide a deterministic demo & integration testing harness
 * 3. Accelerate the dedicated mobile developer by documenting exact endpoint patterns
 * 4. Reproduce integration and lifecycle bugs
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  BookOpen,
  Sparkles,
  ShieldCheck,
  BrainCircuit,
  Smartphone,
  Maximize2,
  RefreshCw,
  User,
  CheckCircle2,
  AlertCircle,
  Wifi,
  ChevronRight,
  Layers,
  HelpCircle,
  ArrowRight,
  RotateCcw,
} from "lucide-react";
import {
  mobileApi,
  UniversityQuestionPayload,
  UniversityAnswerResponse,
} from "../../components/mobile/MobileApiClient";
import { MobileQuestionCard } from "../../components/mobile/MobileQuestionCard";
import { MobileRemediationDrawer } from "../../components/mobile/MobileRemediationDrawer";
import { MobileTransferView } from "../../components/mobile/MobileTransferView";
import { MobileMasterySummary } from "../../components/mobile/MobileMasterySummary";
import { MobileResumeBanner } from "../../components/mobile/MobileResumeBanner";
import type {
  LearnerState,
  AdaptiveRecommendation,
  RemediationTurnResponse,
  RemediationSessionResponse,
  TransferItemDTO,
} from "../../lib/types";

type ActiveTab = "practice" | "remediation" | "transfer" | "mastery";

export default function MobilePage() {
  // Framing & Layout
  const [deviceFrame, setDeviceFrame] = useState(true);
  const [activeTab, setActiveTab] = useState<ActiveTab>("practice");

  // Learner Identity & Connectivity
  const [learnerId, setLearnerId] = useState<string>("");
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  // Practice State
  const [subject, setSubject] = useState<string>("Renal physiology");
  const [topic, setTopic] = useState<string>("RAAS mechanisms");
  const [question, setQuestion] = useState<UniversityQuestionPayload | null>(null);
  const [questionPosition, setQuestionPosition] = useState<number>(1);
  const [questionTotal, setQuestionTotal] = useState<number>(3);
  const [isQuestionLoading, setIsQuestionLoading] = useState(false);
  const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false);
  const [answerResult, setAnswerResult] = useState<UniversityAnswerResponse | null>(null);

  // Adaptive & Learning State
  const [adaptiveRecommendation, setAdaptiveRecommendation] = useState<AdaptiveRecommendation | null>(null);
  const [learnerState, setLearnerState] = useState<LearnerState | null>(null);

  // Remediation State
  const [activeRemediation, setActiveRemediation] = useState<RemediationTurnResponse | null>(null);
  const [restoredSession, setRestoredSession] = useState<RemediationSessionResponse | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Transfer State
  const [activeTransferItem, setActiveTransferItem] = useState<TransferItemDTO | null>(null);
  const [transferSessionId, setTransferSessionId] = useState<string | null>(null);
  const [isTransferSubmitting, setIsTransferSubmitting] = useState(false);

  // Error Banner
  const [apiError, setApiError] = useState<string | null>(null);

  // Initialize Learner ID and fetch initial question
  useEffect(() => {
    const id = mobileApi.getLearnerId();
    setLearnerId(id);

    // Verify backend connectivity
    fetch(`${mobileApi.getBaseUrl()}/health`)
      .then((res) => setBackendHealthy(res.ok))
      .catch(() => setBackendHealthy(false));

    loadInitialQuestion();
    loadLearnerState();
  }, []);

  const loadInitialQuestion = async () => {
    setIsQuestionLoading(true);
    setApiError(null);
    setAnswerResult(null);
    try {
      const res = await mobileApi.getQuestion(subject, topic);
      if (res.question) {
        setQuestion(res.question);
        setQuestionPosition(res.position || 1);
        setQuestionTotal(res.total || 3);
      } else {
        // Fallback default fixture
        setQuestion({
          id: "UNI-RENAL-001",
          track: "UNIVERSITY",
          subject: "Renal physiology",
          topic: "RAAS mechanisms",
          stem: "A 45-year-old male with essential hypertension is started on an ACE inhibitor. Two weeks later, routine labs show a modest rise in serum creatinine from 88 µmol/L to 102 µmol/L and serum potassium from 4.4 mmol/L to 4.8 mmol/L. What is the physiological mechanism responsible for the initial reduction in glomerular filtration rate (GFR)?",
          options: {
            A: "Preferential dilation of the efferent arteriole reducing glomerular capillary hydrostatic pressure",
            B: "Constriction of the afferent arteriole mediated by tubuloglomerular feedback",
            C: "Direct inhibition of renal sodium-potassium ATPase in the proximal tubule",
            D: "Increased production of aldosterone leading to renal vasoconstriction",
          },
          difficulty: "intermediate",
        });
      }
    } catch (err: any) {
      setApiError(err.message || "Failed to load question from backend");
    } finally {
      setIsQuestionLoading(false);
    }
  };

  const loadLearnerState = async () => {
    try {
      const state = await mobileApi.getAdaptiveState();
      setLearnerState(state);
      const rec = await mobileApi.getAdaptiveRecommendation();
      setAdaptiveRecommendation(rec);
    } catch (err: any) {
      // Non-blocking
    }
  };

  const handleResetIdentity = () => {
    if (typeof window !== "undefined") {
      const confirmed = window.confirm(
        "Warning: Resetting your anonymous learner identity will disconnect from current remediation sessions and progress history. Do you want to proceed?"
      );
      if (!confirmed) return;
    }
    const newId = mobileApi.resetIdentity();
    setLearnerId(newId);
    setAnswerResult(null);
    setActiveRemediation(null);
    setRestoredSession(null);
    setActiveTransferItem(null);
    setTransferSessionId(null);
    loadInitialQuestion();
    loadLearnerState();
  };

  // Step 2: Answer Submission
  const handleSubmitAnswer = async (selectedOption: string) => {
    if (!question) return;
    setIsSubmittingAnswer(true);
    setApiError(null);
    try {
      const res = await mobileApi.submitAnswer(question.id, selectedOption);
      setAnswerResult(res);

      // Refresh adaptive recommendation & learner state
      const [rec, state] = await Promise.all([
        mobileApi.getAdaptiveRecommendation().catch(() => null),
        mobileApi.getAdaptiveState().catch(() => null),
      ]);
      if (rec) setAdaptiveRecommendation(rec);
      if (state) setLearnerState(state);
    } catch (err: any) {
      setApiError(err.message || "Answer submission failed");
    } finally {
      setIsSubmittingAnswer(false);
    }
  };

  // Step 4: Start Socratic Remediation
  const handleStartRemediation = async (questionId: string, selectedOption: string) => {
    setApiError(null);
    try {
      const initialTurn = await mobileApi.startRemediation(questionId, selectedOption);
      setActiveRemediation(initialTurn);
      setRestoredSession(null);
      setIsDrawerOpen(true);
      setActiveTab("remediation");
    } catch (err: any) {
      setApiError(err.message || "Failed to initiate Socratic remediation");
    }
  };

  // Submit Remediation Turn
  const handleSubmitTurn = async (message: string): Promise<RemediationTurnResponse> => {
    if (!activeRemediation?.session_id) {
      throw new Error("No active remediation session");
    }
    const nextTurn = await mobileApi.submitRemediationTurn(activeRemediation.session_id, message);
    setActiveRemediation(nextTurn);
    return nextTurn;
  };

  // Step 5: Advance to Independent Transfer Assessment
  const handleStartTransfer = async (sessionId: string) => {
    setApiError(null);
    try {
      const item = await mobileApi.getTransferItem(sessionId);
      setActiveTransferItem(item);
      setTransferSessionId(sessionId);
      setIsDrawerOpen(false);
      setActiveTab("transfer");
    } catch (err: any) {
      if (err?.status === 404 || err?.message?.includes("404")) {
        setApiError("Transfer assessment unavailable for this session.");
      } else {
        setApiError(err.message || "Failed to retrieve transfer assessment item");
      }
    }
  };

  // Submit Transfer
  const handleSubmitTransfer = async (selectedOption: string, wasAssisted: boolean) => {
    if (!transferSessionId || !activeTransferItem) {
      throw new Error("Missing transfer session or item");
    }
    setIsTransferSubmitting(true);
    try {
      const res = await mobileApi.submitTransfer(
        transferSessionId,
        activeTransferItem.question_id,
        selectedOption,
        wasAssisted
      );
      // Refresh learner state
      loadLearnerState();
      return res;
    } finally {
      setIsTransferSubmitting(false);
    }
  };

  // Step 7: Resume In-Progress Session
  const handleResumeSession = async (session: RemediationSessionResponse) => {
    setRestoredSession(session);
    setApiError(null);

    // If already awaiting transfer, load transfer view directly
    if (session.lifecycle_state === "AWAITING_TRANSFER") {
      try {
        const item = await mobileApi.getTransferItem(session.session_id);
        setActiveTransferItem(item);
        setTransferSessionId(session.session_id);
        setActiveTab("transfer");
        return;
      } catch (err) {
        // Fall back to remediation drawer
      }
    }

    // Otherwise reconstruct turn for drawer
    const lastTurnIndex = (session.turns?.length || 1) - 1;
    const lastTurnData = session.turns?.[lastTurnIndex];
    const turnRes: RemediationTurnResponse = {
      session_id: session.session_id,
      turn_number: session.turn_number,
      max_turns: session.max_turns,
      is_complete: session.is_complete,
      lifecycle_state: session.lifecycle_state,
      outcome: session.outcome,
      remediation_status: session.is_complete ? "RESOLVED" : (session.turn_number === 1 ? "PROBING" : "GUIDING"),
      strategy: session.strategy,
      timeline: session.timeline,
      tutor_message: lastTurnData?.tutor_message || "Let's review the physiological mechanism.",
      socratic_probe: lastTurnData?.socratic_probe || null,
      citations: lastTurnData?.citations || [],
      transfer_available: session.lifecycle_state === "AWAITING_TRANSFER",
    };

    setActiveRemediation(turnRes);
    setIsDrawerOpen(true);
    setActiveTab("remediation");
  };

  // Exit / Abandon remediation
  const handleExitRemediation = async (sessionId: string) => {
    try {
      await mobileApi.abandonRemediation(sessionId);
    } catch {
      // Ignore
    }
    setActiveRemediation(null);
    setRestoredSession(null);
    setIsDrawerOpen(false);
    setActiveTab("practice");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-start p-2 sm:p-6 lg:p-8 font-sans selection:bg-sky-500/30">
      {/* Top Bar / Mode Controls */}
      <header className="w-full max-w-md lg:max-w-4xl flex items-center justify-between py-2 px-3 mb-3 bg-slate-900/80 border border-slate-800/90 rounded-xl backdrop-blur-md shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold tracking-wide text-slate-200">
            MedicalPlab Reference Mobile
          </span>
          <span className="text-[10px] bg-sky-950/80 text-sky-400 border border-sky-800/60 px-1.5 py-0.5 rounded font-mono">
            Harness
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {/* Device Frame Toggle */}
          <button
            type="button"
            onClick={() => setDeviceFrame(!deviceFrame)}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/60 text-[11px]"
            title={deviceFrame ? "Switch to Full Screen" : "Switch to Mobile Device Frame"}
          >
            {deviceFrame ? (
              <>
                <Maximize2 className="w-3 h-3 text-sky-400" />
                <span className="hidden sm:inline">Expand View</span>
              </>
            ) : (
              <>
                <Smartphone className="w-3 h-3 text-sky-400" />
                <span className="hidden sm:inline">Phone Frame</span>
              </>
            )}
          </button>

          {/* Reset Identity */}
          <button
            type="button"
            onClick={handleResetIdentity}
            className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors text-[11px]"
            title="Reset anonymous student identity UUID"
          >
            <RotateCcw className="w-3 h-3" />
            <span className="hidden sm:inline">New Learner</span>
          </button>
        </div>
      </header>

      {/* Main Container: Mobile Frame or Fluid Responsive */}
      <main
        className={`w-full transition-all duration-200 flex flex-col ${
          deviceFrame
            ? "max-w-[420px] rounded-[42px] border-[10px] border-slate-800 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8),0_0_0_1px_rgba(255,255,255,0.08)] overflow-hidden bg-slate-950"
            : "max-w-2xl rounded-2xl border border-slate-800/80 bg-slate-950/95 shadow-xl"
        }`}
      >
        {/* Simulated Phone Notch & Status Bar (in device frame mode) */}
        {deviceFrame && (
          <div className="bg-slate-900/90 pt-3 pb-2 px-6 flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800/80 select-none">
            <span className="font-semibold text-slate-200 font-mono">09:41</span>
            <div className="w-24 h-4 bg-slate-950 rounded-full mx-auto -mt-1 border border-slate-800/60 flex items-center justify-center">
              <div className="w-2.5 h-2.5 rounded-full bg-slate-900" />
            </div>
            <div className="flex items-center gap-1.5 text-slate-400">
              <Wifi className="w-3 h-3" />
              <div className="w-5 h-2.5 border border-slate-400 rounded-sm p-0.5 flex items-center">
                <div className="w-3 h-full bg-slate-300 rounded-[1px]" />
              </div>
            </div>
          </div>
        )}

        {/* Mobile App Header */}
        <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
              <BookOpen className="w-3.5 h-3.5" />
            </div>
            <div>
              <h1 className="text-xs font-bold text-slate-100 tracking-tight">
                PLAB 1 Reference Mobile
              </h1>
              <p className="text-[10px] text-slate-400 truncate max-w-[150px]">
                {subject}
              </p>
            </div>
          </div>

          {/* Learner ID Chip */}
          <div
            className="flex items-center gap-1.5 bg-slate-800/90 border border-slate-700/60 px-2 py-0.5 rounded-full text-[10px] text-slate-300 font-mono cursor-pointer hover:border-sky-500/50 transition-colors"
            title={`Active X-User-Id: ${learnerId}`}
            onClick={() => {
              if (typeof navigator !== "undefined") {
                navigator.clipboard.writeText(learnerId);
                alert(`Copied Learner ID:\n${learnerId}`);
              }
            }}
          >
            <User className="w-2.5 h-2.5 text-sky-400" />
            <span className="truncate max-w-[85px]">{learnerId || "connecting…"}</span>
          </div>
        </div>

        {/* Scrollable Viewport */}
        <div className="p-3 sm:p-4 space-y-3 min-h-[520px] max-h-[640px] overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800">
          {/* Active Session Resume Prompt */}
          <MobileResumeBanner
            onResume={handleResumeSession}
            onDismiss={() => {}}
          />

          {/* API Error Notification */}
          {apiError && (
            <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-500/50 text-rose-200 text-xs flex items-start gap-2 animate-in fade-in duration-150">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1 leading-snug">
                <span className="font-semibold block">API Contract Notice</span>
                {apiError}
              </div>
            </div>
          )}

          {/* TAB 1: PRACTICE QUESTION */}
          {activeTab === "practice" && (
            <div className="space-y-3">
              {isQuestionLoading ? (
                <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin text-sky-400" />
                  <span>Loading clinical vignette…</span>
                </div>
              ) : question ? (
                <>
                  <MobileQuestionCard
                    question={question}
                    position={questionPosition}
                    total={questionTotal}
                    isSubmitting={isSubmittingAnswer}
                    onSubmitAnswer={handleSubmitAnswer}
                    answerResult={answerResult}
                    onNextQuestion={loadInitialQuestion}
                    onStartRemediation={handleStartRemediation}
                  />

                  {/* Adaptive Recommendation guidance if available */}
                  {answerResult && adaptiveRecommendation && (
                    <div className="rounded-xl bg-gradient-to-r from-sky-950/40 to-slate-900 border border-sky-500/30 p-3 text-xs flex items-center justify-between gap-2 shadow-md">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-sky-400 shrink-0" />
                        <div>
                          <span className="text-[10px] uppercase font-semibold text-sky-400 block tracking-wider">
                            Authoritative Recommendation
                          </span>
                          <span className="text-slate-200 font-medium">
                            {adaptiveRecommendation.action === "SOLVE_TARGETED_QUESTION"
                              ? "Continue Targeted Practice"
                              : "Engage Socratic Remediation"}
                          </span>
                        </div>
                      </div>
                      {!answerResult.is_correct && (
                        <button
                          type="button"
                          onClick={() => handleStartRemediation(question.id, answerResult.correct_answer === "A" ? "B" : "A")}
                          className="px-2.5 py-1 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 text-[11px] font-semibold flex items-center gap-1 transition-all"
                        >
                          <span>Start</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs">
                  No question available. Click reset to reload.
                </div>
              )}
            </div>
          )}

          {/* TAB 2: SOCRATIC REMEDIATION */}
          {activeTab === "remediation" && (
            <div className="h-[520px]">
              {activeRemediation ? (
                <MobileRemediationDrawer
                  initialTurn={activeRemediation}
                  restoredSession={restoredSession}
                  onSubmitTurn={handleSubmitTurn}
                  onStartTransfer={handleStartTransfer}
                  onExitRemediation={handleExitRemediation}
                />
              ) : (
                <div className="p-8 text-center text-slate-400 text-xs flex flex-col items-center justify-center h-full gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-200 text-sm">No Active Remediation</h3>
                    <p className="text-[11px] text-slate-500 mt-1 max-w-[220px]">
                      Answer a question incorrectly in the Practice tab to trigger a grounded Socratic dialogue.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveTab("practice")}
                    className="px-4 py-2 rounded-xl bg-sky-500 text-slate-950 font-medium text-xs hover:bg-sky-400 transition-all"
                  >
                    Go to Practice
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: INDEPENDENT TRANSFER */}
          {activeTab === "transfer" && (
            <div>
              {activeTransferItem && transferSessionId ? (
                <MobileTransferView
                  transferItem={activeTransferItem}
                  sessionId={transferSessionId}
                  isSubmitting={isTransferSubmitting}
                  onSubmitTransfer={handleSubmitTransfer}
                  onViewMastery={() => setActiveTab("mastery")}
                  onExit={() => setActiveTab("practice")}
                />
              ) : (
                <div className="p-8 text-center text-slate-400 text-xs flex flex-col items-center justify-center min-h-[380px] gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-200 text-sm">
                      {apiError === "Transfer assessment unavailable for this session."
                        ? "Transfer Assessment Unavailable"
                        : "No Active Transfer Assessment"}
                    </h3>
                    <p className="text-[11px] text-slate-400 mt-1 max-w-[220px]">
                      {apiError === "Transfer assessment unavailable for this session."
                        ? "Transfer assessment unavailable for this session."
                        : "Complete all 3 Socratic remediation turns to qualify for an independent transfer assessment."}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveTab("practice")}
                    className="px-4 py-2 rounded-xl bg-indigo-500 text-white font-medium text-xs hover:bg-indigo-400 transition-all"
                  >
                    Return to Practice
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MASTERY & PROGRESS */}
          {activeTab === "mastery" && (
            <div className="space-y-3">
              <MobileMasterySummary
                learnerState={learnerState}
                recommendation={adaptiveRecommendation}
                onSelectTopic={(subj, top) => {
                  setSubject(subj);
                  setTopic(top);
                  setActiveTab("practice");
                  loadInitialQuestion();
                }}
                onRefresh={loadLearnerState}
              />
            </div>
          )}
        </div>

        {/* Mobile Bottom Navigation Bar */}
        <nav className="bg-slate-900/95 border-t border-slate-800/90 px-2 py-2 flex items-center justify-around shrink-0 select-none">
          {/* 1. Practice */}
          <button
            type="button"
            onClick={() => setActiveTab("practice")}
            className={`flex flex-col items-center justify-center gap-1 py-1 px-3 rounded-xl transition-all ${
              activeTab === "practice"
                ? "text-sky-400 font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span className="text-[10px]">Practice</span>
          </button>

          {/* 2. Remediation */}
          <button
            type="button"
            onClick={() => setActiveTab("remediation")}
            className={`flex flex-col items-center justify-center gap-1 py-1 px-3 rounded-xl transition-all relative ${
              activeTab === "remediation"
                ? "text-sky-400 font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {activeRemediation && (
              <span className="absolute top-1 right-3 w-2 h-2 rounded-full bg-sky-400 ring-2 ring-slate-900" />
            )}
            <Sparkles className="w-4 h-4" />
            <span className="text-[10px]">Remediation</span>
          </button>

          {/* 3. Transfer */}
          <button
            type="button"
            onClick={() => setActiveTab("transfer")}
            className={`flex flex-col items-center justify-center gap-1 py-1 px-3 rounded-xl transition-all relative ${
              activeTab === "transfer"
                ? "text-indigo-400 font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {activeTransferItem && (
              <span className="absolute top-1 right-3 w-2 h-2 rounded-full bg-indigo-400 ring-2 ring-slate-900" />
            )}
            <ShieldCheck className="w-4 h-4" />
            <span className="text-[10px]">Transfer</span>
          </button>

          {/* 4. Mastery */}
          <button
            type="button"
            onClick={() => {
              setActiveTab("mastery");
              loadLearnerState();
            }}
            className={`flex flex-col items-center justify-center gap-1 py-1 px-3 rounded-xl transition-all ${
              activeTab === "mastery"
                ? "text-emerald-400 font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <BrainCircuit className="w-4 h-4" />
            <span className="text-[10px]">Mastery</span>
          </button>
        </nav>
      </main>

      {/* Footer info & contract notes */}
      <footer className="w-full max-w-md lg:max-w-4xl mt-4 text-center text-[11px] text-slate-500 space-y-1">
        <p>
          MedicalPlab Mobile Integration Prototype &bull; Frozen Backend Contract &bull; Authoritative Learning Engine
        </p>
        <p className="text-slate-600">
          Device ID is saved to device storage &bull; Scoring and transfer logic strictly managed by backend
        </p>
      </footer>
    </div>
  );
}
