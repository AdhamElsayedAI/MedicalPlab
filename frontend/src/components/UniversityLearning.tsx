"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, getAuthoritativeLearnerId } from "@/lib/api-client";
import { SocraticTutorDrawer } from "./SocraticTutorDrawer";
import { AdaptiveGuidanceCard } from "./AdaptiveGuidanceCard";
import { ReasoningTimelineCard } from "./ReasoningTimelineCard";
import type { RemediationTurnResponse, TransferItemDTO, TransferSubmissionResponse } from "@/lib/types";

type Choice = { name: string; count: number };
type Question = { id: string; stem: string; subject: string; topic: string; options: Record<string, string> };
type TopicProgress = { subject: string; topic: string; attempted: number; correct: number; accuracy: number | null; mastery: string };
type Progress = { attempted: number; correct: number; accuracy: number | null; topics: TopicProgress[]; recommendation: TopicProgress | null };
type Feedback = { is_correct: boolean; correct_answer: string; explanation: string; source: { title: string; url: string }; progress: Progress };

const learnerKey = "medicalplab.university.learner.v1";

async function request<T>(path: string, learner: string, body?: object): Promise<T> {
  const response = await fetch(`${api.getBaseUrl()}/api/v1/university${path}`, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json", "X-User-Id": learner },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    let message = "University Learning is unavailable. Please retry.";
    try { const error = await response.json(); if (typeof error.detail === "string") message = error.detail; } catch { /* Retain useful fallback. */ }
    throw new Error(message);
  }
  return response.json();
}

export const ACTIVE_REMEDIATION_KEY = "medplab.active_remediation.v1";

export interface ActiveRemediationContext {
  sessionId: string;
  questionId: string;
  subject: string;
  topic: string;
  selectedOption: string;
  attemptKey: string;
  position: number;
  total: number;
  question: Question;
  feedback: Feedback;
}

export function UniversityLearning() {
  const learner = useRef("");
  const [attemptKey, setAttemptKey] = useState("");
  const [subjects, setSubjects] = useState<Choice[]>([]);
  const [topics, setTopics] = useState<Choice[]>([]);
  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [question, setQuestion] = useState<Question | null>(null);
  const [position, setPosition] = useState(0);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [complete, setComplete] = useState(false);
  const [adaptiveRefresh, setAdaptiveRefresh] = useState(0);
  const [remediation, setRemediation] = useState<RemediationTurnResponse | null>(null);
  const [remediationLoading, setRemediationLoading] = useState(false);
  const [remediationInput, setRemediationInput] = useState("");
  const [remediationError, setRemediationError] = useState("");
  const [transferItem, setTransferItem] = useState<TransferItemDTO | null>(null);
  const [transferSelected, setTransferSelected] = useState("");
  const [transferLoading, setTransferLoading] = useState(false);
  const [transferResult, setTransferResult] = useState<TransferSubmissionResponse | null>(null);
  const [transferUnavailable, setTransferUnavailable] = useState(false);
  const [abandonLoading, setAbandonLoading] = useState(false);

  const currentQuestionRef = useRef<Question | null>(question);
  currentQuestionRef.current = question;
  const currentRemediationRef = useRef<RemediationTurnResponse | null>(remediation);
  currentRemediationRef.current = remediation;
  const contextGenRef = useRef(0);

  function resetRemediationState() {
    setRemediation(null);
    setRemediationInput("");
    setRemediationError("");
    setRemediationLoading(false);
    setAbandonLoading(false);
    setTransferItem(null);
    setTransferSelected("");
    setTransferLoading(false);
    setTransferResult(null);
    setTransferUnavailable(false);
  }

  useEffect(() => {
    let active = true;
    learner.current = getAuthoritativeLearnerId();
    api.setUser(learner.current);

    async function init() {
      // 1. Initialise subjects and progress
      try {
        const [bank, p] = await Promise.all([
          request<{ items: Choice[] }>("/subjects", learner.current),
          request<Progress>("/progress", learner.current),
        ]);
        if (active) {
          setSubjects(bank.items);
          setProgress(p);
        }
      } catch {
        if (active) setError("University Learning could not load. Check your connection and retry.");
      }

      // 2. Server-authoritative remediation reload recovery
      try {
        const rawNav = typeof window !== "undefined" ? sessionStorage.getItem(ACTIVE_REMEDIATION_KEY) : null;
        if (rawNav) {
          const nav = JSON.parse(rawNav) as ActiveRemediationContext;
          if (nav && nav.sessionId && nav.questionId) {
            const sess = await api.getRemediationSession(nav.sessionId, learner.current);
            if (!active) return;
            if (sess.user_id === learner.current && sess.question_id === nav.questionId) {
              const restoredSubject = nav.subject || nav.question?.subject || "";
              const restoredTopic = nav.topic || sess.topic || nav.question?.topic || "";

              setSubject(restoredSubject);
              setTopic(restoredTopic);
              setQuestion(nav.question);
              setPosition(nav.position || 1);
              setTotal(nav.total || 1);
              setSelected(nav.selectedOption || "");
              setFeedback(nav.feedback);
              setAttemptKey(nav.attemptKey || "");

              // Fetch topics for breadcrumb navigation in the background
              if (restoredSubject) {
                request<{ items: Choice[] }>(`/topics?subject=${encodeURIComponent(restoredSubject)}`, learner.current)
                  .then((data) => { if (active) setTopics(data.items); })
                  .catch(() => {});
              }

              const lastTurn = sess.turns && sess.turns.length > 0 ? sess.turns[sess.turns.length - 1] : null;
              const isAwaitingTransfer = sess.lifecycle_state === "AWAITING_TRANSFER";
              const isCompleted = sess.lifecycle_state === "COMPLETED" || sess.is_complete;

              const isTransferEligibleCompletion = isCompleted && sess.outcome !== "SAFETY_FALLBACK" && sess.outcome !== "ABANDONED";

              const turnRes: RemediationTurnResponse = {
                session_id: sess.session_id,
                turn_number: sess.turn_number,
                max_turns: sess.max_turns,
                is_complete: sess.is_complete,
                lifecycle_state: sess.lifecycle_state,
                outcome: sess.outcome,
                remediation_status: isCompleted
                  ? (sess.outcome === "TRANSFER_CONFIRMED" ? "RESOLVED" : "UNRESOLVED")
                  : isAwaitingTransfer
                  ? "CONFIRMING"
                  : sess.turn_number === 1
                  ? "PROBING"
                  : "GUIDING",
                pattern_id: null,
                reasoning_pattern: null,
                strategy: sess.strategy,
                timeline: sess.timeline,
                tutor_message: lastTurn ? lastTurn.tutor_message : "Resumed active session.",
                socratic_probe: isCompleted ? null : (lastTurn ? lastTurn.socratic_probe : null),
                citations: lastTurn ? lastTurn.citations : [],
                transfer_available: isAwaitingTransfer || isTransferEligibleCompletion,
              };
              setRemediation(turnRes);

              if (isAwaitingTransfer) {
                setTransferResult(null);
                setTransferLoading(true);
                try {
                  const item = await api.getTransferItem(sess.session_id, learner.current);
                  if (active) {
                    setTransferItem(item);
                    setTransferUnavailable(false);
                  }
                } catch {
                  if (active) {
                    setTransferItem(null);
                    setTransferUnavailable(true);
                  }
                } finally {
                  if (active) setTransferLoading(false);
                }
              } else if (isTransferEligibleCompletion) {
                if (sess.transfer_attempt) {
                  setTransferSelected(sess.transfer_attempt.submitted_option);
                }
                setTransferUnavailable(false);
                setTransferResult({
                  session_id: sess.session_id,
                  outcome: sess.outcome || "UNRESOLVED",
                  is_correct: sess.transfer_attempt ? sess.transfer_attempt.is_correct : (sess.outcome === "TRANSFER_CONFIRMED"),
                  explanation: sess.timeline?.transfer_result || (sess.outcome === "TRANSFER_CONFIRMED" ? "Transfer demonstrated on this question" : "Transfer not demonstrated."),
                  citations: [],
                  timeline: sess.timeline,
                  next_recommendation: sess.timeline?.next_recommendation
                    ? { recommendation: sess.timeline.next_recommendation }
                    : null,
                });
              } else {
                setTransferSelected("");
                setTransferItem(null);
                setTransferUnavailable(false);
                setTransferResult(null);
              }
            } else {
              // Ownership mismatch or question mismatch: purge stale pointer
              try { sessionStorage.removeItem(ACTIVE_REMEDIATION_KEY); } catch {}
            }
          }
        }
      } catch {
        if (!active) return;
        // 403 / 404 / stale / network failure: clear reference and safely fall back
        try { sessionStorage.removeItem(ACTIVE_REMEDIATION_KEY); } catch {}
      } finally {
        if (active) setBusy(false);
      }
    }

    void init();
    return () => { active = false; };
  }, []);

  async function run(action: () => Promise<void>) {
    setBusy(true); setError("");
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : "Please retry."); }
    finally { setBusy(false); }
  }

  function clearQuestion() {
    ++contextGenRef.current;
    try {
      sessionStorage.removeItem(ACTIVE_REMEDIATION_KEY);
      if (question) sessionStorage.removeItem(`medplab_rem_${question.id}`);
    } catch {}
    setQuestion(null);
    setFeedback(null);
    setSelected("");
    setComplete(false);
    resetRemediationState();
  }

  async function chooseSubject(name: string) {
    ++contextGenRef.current;
    await run(async () => {
      const data = await request<{ items: Choice[] }>(`/topics?subject=${encodeURIComponent(name)}`, learner.current);
      setSubject(name); setTopics(data.items); setTopic(""); clearQuestion();
    });
  }

  async function loadQuestion(name: string, after?: string, targetSubject = subject) {
    const gen = ++contextGenRef.current;
    try {
      sessionStorage.removeItem(ACTIVE_REMEDIATION_KEY);
      if (question) sessionStorage.removeItem(`medplab_rem_${question.id}`);
    } catch {}
    resetRemediationState();
    await run(async () => {
      const params = new URLSearchParams({ subject: targetSubject, topic: name });
      if (after) params.set("after", after);
      const data = await request<{ question: Question | null; position?: number; total?: number }>(`/question?${params}`, learner.current);
      if (contextGenRef.current !== gen) return;
      setSubject(targetSubject); setTopic(name); setQuestion(data.question);
      setPosition(data.position || 0); setTotal(data.total || 0);
      setSelected(""); setFeedback(null); setComplete(!data.question);
      setAttemptKey(crypto.randomUUID());
    });
  }

  async function initiateRemediation() {
    if (!question || !selected || remediationLoading) return;
    const gen = ++contextGenRef.current;
    const currentQId = question.id;
    // Invalidate previous outgoing remediation state before waiting on async work
    resetRemediationState();
    setRemediationLoading(true);
    try {
      const res = await api.startRemediation({
        question_id: question.id,
        selected_option: selected,
        topic: topic || question.topic,
        attempt_id: attemptKey,
      }, learner.current);
      // Stale response protection: only apply if student is still on the same generation and question
      if (contextGenRef.current === gen && currentQuestionRef.current?.id === currentQId) {
        setRemediation(res);
        try {
          const navData: ActiveRemediationContext = {
            sessionId: res.session_id,
            questionId: question.id,
            subject: subject || question.subject,
            topic: topic || question.topic,
            selectedOption: selected,
            attemptKey: attemptKey || "",
            position,
            total,
            question,
            feedback: feedback!,
          };
          sessionStorage.setItem(ACTIVE_REMEDIATION_KEY, JSON.stringify(navData));
        } catch {}
      }
    } catch (err) {
      if (contextGenRef.current === gen && currentQuestionRef.current?.id === currentQId) {
        const msg = err instanceof Error ? err.message : "Could not initiate Socratic remediation.";
        setRemediationError(msg.includes("503") ? "Socratic remediation is currently unavailable (feature flag disabled)." : msg);
      }
    } finally {
      if (contextGenRef.current === gen && currentQuestionRef.current?.id === currentQId) {
        setRemediationLoading(false);
      }
    }
  }

  async function submitRemediationTurn() {
    if (!remediation || !remediationInput.trim() || remediation.is_complete || remediationLoading) return;
    const gen = ++contextGenRef.current;
    const currentSessionId = remediation.session_id;
    const currentQId = question?.id;
    setRemediationLoading(true);
    setRemediationError("");
    try {
      const res = await api.submitRemediationTurn({
        session_id: remediation.session_id,
        student_message: remediationInput.trim(),
      }, learner.current);
      // Stale response protection: only apply if still matching active generation and session
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        !currentRemediationRef.current?.is_complete &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setRemediation(res);
        setRemediationInput("");
        if (res.transfer_available) {
          // Automatically fetch transfer item
          setTransferLoading(true);
          try {
            const item = await api.getTransferItem(res.session_id, learner.current);
            if (
              contextGenRef.current === gen &&
              currentRemediationRef.current?.session_id === currentSessionId &&
              !currentRemediationRef.current?.is_complete &&
              (!currentQId || currentQuestionRef.current?.id === currentQId)
            ) {
              setTransferItem(item);
              setTransferUnavailable(false);
            }
          } catch {
            if (
              contextGenRef.current === gen &&
              currentRemediationRef.current?.session_id === currentSessionId &&
              !currentRemediationRef.current?.is_complete &&
              (!currentQId || currentQuestionRef.current?.id === currentQId)
            ) {
              setTransferItem(null);
              setTransferUnavailable(true);
            }
          } finally {
            if (
              contextGenRef.current === gen &&
              currentRemediationRef.current?.session_id === currentSessionId &&
              !currentRemediationRef.current?.is_complete &&
              (!currentQId || currentQuestionRef.current?.id === currentQId)
            ) {
              setTransferLoading(false);
            }
          }
        }
      }
    } catch (err) {
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        !currentRemediationRef.current?.is_complete &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setRemediationError(err instanceof Error ? err.message : "Could not advance remediation turn.");
      }
    } finally {
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        !currentRemediationRef.current?.is_complete &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setRemediationLoading(false);
      }
    }
  }

  async function fetchTransferItem() {
    if (!remediation) return;
    const gen = ++contextGenRef.current;
    const currentSessionId = remediation.session_id;
    const currentQId = question?.id;
    setTransferLoading(true);
    setRemediationError("");
    try {
      const item = await api.getTransferItem(remediation.session_id, learner.current);
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        !currentRemediationRef.current?.is_complete &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setTransferItem(item);
        setTransferUnavailable(false);
      }
    } catch (err) {
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        !currentRemediationRef.current?.is_complete &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setTransferItem(null);
        setTransferUnavailable(true);
        setRemediationError(err instanceof Error ? err.message : "Could not load transfer assessment.");
      }
    } finally {
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        !currentRemediationRef.current?.is_complete &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setTransferLoading(false);
      }
    }
  }

  async function submitTransferAssessment() {
    if (!remediation || !transferItem || !transferSelected) return;
    const gen = ++contextGenRef.current;
    const currentSessionId = remediation.session_id;
    const currentQId = question?.id;
    setTransferLoading(true);
    setRemediationError("");
    try {
      const res = await api.submitTransferAnswer({
        session_id: remediation.session_id,
        question_id: transferItem.question_id,
        selected_option: transferSelected,
        was_assisted: false,
        idempotency_key: crypto.randomUUID(),
      }, learner.current);
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        // Defensive session binding: associate transferResult explicitly with active session ID
        const boundResult: TransferSubmissionResponse = {
          ...res,
          session_id: currentSessionId,
        };
        setTransferResult(boundResult);
        setRemediation((prev) =>
          prev
            ? {
                ...prev,
                is_complete: true,
                outcome: res.outcome,
                lifecycle_state: "COMPLETED",
                timeline: res.timeline,
              }
            : null
        );
        setAdaptiveRefresh((r) => r + 1);
      }
    } catch (err) {
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setRemediationError(err instanceof Error ? err.message : "Could not score transfer assessment.");
      }
    } finally {
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setTransferLoading(false);
      }
    }
  }

  async function abandonRemediation() {
    if (!remediation) return;
    const gen = ++contextGenRef.current;
    const currentSessionId = remediation.session_id;
    const currentQId = question?.id;

    // Synchronous invalidation before first await:
    // Establish new generation and immediately clear transient turn/error state
    setRemediationError("");
    setRemediationInput("");
    setTransferItem(null);
    setTransferSelected("");
    setTransferResult(null);
    setTransferUnavailable(false);
    setAbandonLoading(true);
    setRemediationLoading(false);

    try {
      const res = await api.abandonRemediation(currentSessionId, learner.current);
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setRemediation(res);
        try {
          sessionStorage.removeItem(ACTIVE_REMEDIATION_KEY);
        } catch {}
      }
    } catch (err) {
      if (
        contextGenRef.current === gen &&
        currentRemediationRef.current?.session_id === currentSessionId &&
        (!currentQId || currentQuestionRef.current?.id === currentQId)
      ) {
        setRemediationError(err instanceof Error ? err.message : "Could not abandon session.");
      }
    } finally {
      if (contextGenRef.current === gen) {
        setAbandonLoading(false);
      }
    }
  }

  async function submit() {
    if (!question || !selected || feedback) return;
    const gen = ++contextGenRef.current;
    resetRemediationState();
    await run(async () => {
      const result = await request<Feedback>("/answer", learner.current, {
        question_id: question.id, selected_option: selected, idempotency_key: attemptKey,
      });
      if (contextGenRef.current !== gen) return;
      setFeedback(result); setProgress(result.progress);
      setAdaptiveRefresh((prev) => prev + 1);
    });
  }

  const button = "rounded-xl border border-slate-600 px-5 py-3 text-left text-slate-100 hover:border-sky-400 focus-visible:outline-2 focus-visible:outline-sky-400 disabled:opacity-50 disabled:cursor-not-allowed";

  // Defensive render guard: terminal transfer UI renders ONLY if result belongs to active session AND lifecycle is completed
  const isTerminalResultValid = Boolean(
    transferResult &&
    remediation &&
    transferResult.session_id === remediation.session_id &&
    (remediation.lifecycle_state === "COMPLETED" || remediation.is_complete) &&
    (remediation.outcome === "TRANSFER_CONFIRMED" || remediation.outcome === "TRANSFER_NOT_CONFIRMED" || remediation.outcome === "UNRESOLVED")
  );

  return <main className="min-h-screen bg-slate-950 text-slate-100 px-5 py-8">
    <div className="max-w-5xl mx-auto space-y-8">
      <header className="space-y-4">
        <Link className="text-sky-300 underline" href="/">← MedicalPlab home</Link>
        <p className="text-sm uppercase tracking-widest text-sky-300">Undergraduate medical education</p>
        <h1 className="text-3xl font-bold">University Learning</h1>
        <p className="text-slate-300 max-w-2xl">Build your foundations with short, source-backed practice. Choose a topic, check your understanding, and review the explanation.</p>
        <p className="text-sm text-slate-400">Educational basic science • Independent University progress • No clinician approval claimed</p>
      </header>

      <AdaptiveGuidanceCard
        learnerId={learner.current}
        refreshTrigger={adaptiveRefresh}
        onSelectTopic={(targetSubj, targetTopic) => {
          void loadQuestion(targetTopic, undefined, targetSubj);
        }}
      />

      {error && <div role="alert" className="rounded-xl border border-amber-500 p-4 space-y-3">
        <p>{error}</p>
        <button className={button} onClick={() => window.location.reload()}>Reload University Learning</button>
        {question && !feedback && <p className="text-sm">You can also retry your answer below. A retry will not count twice.</p>}
      </div>}
      {busy && <p role="status" className="text-sky-300">Loading University Learning…</p>}

      <div className="grid lg:grid-cols-[1fr_300px] gap-6">
        <section id="university-content" aria-label="Learning content" className="space-y-6">
          {!subject && <div className="space-y-4">
            <h2 className="text-xl font-semibold">Choose a subject</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {subjects.map((item) => (
                <button key={item.name} className={button} disabled={busy} onClick={() => void chooseSubject(item.name)}>
                  <span className="font-semibold text-sky-300 block">{item.name}</span>
                  <span className="text-sm text-slate-400">{item.count} questions available</span>
                </button>
              ))}
            </div>
          </div>}

          {subject && !topic && <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">{subject}: choose a topic</h2>
              <button className="text-sm text-sky-300 underline" disabled={busy} onClick={() => { setSubject(""); clearQuestion(); }}>All subjects</button>
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              {topics.map((item) => (
                <button key={item.name} className={button} disabled={busy} onClick={() => void loadQuestion(item.name)}>
                  <span className="font-semibold text-sky-300 block">{item.name}</span>
                  <span className="text-sm text-slate-400">{item.count} questions</span>
                </button>
              ))}
            </div>
          </div>}

          {question && <>
            <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-300">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sky-300">{subject}</span>
                <span>/</span>
                <span>{topic}</span>
              </div>
              <div className="flex items-center gap-4">
                {total > 0 && <span>Question {position} of {total}</span>}
                <button className="text-sky-300 underline" disabled={busy} onClick={() => { setTopic(""); clearQuestion(); }}>Change topic</button>
              </div>
            </div>

            <div className="med-card p-6 space-y-4">
              <h2 className="text-lg font-semibold leading-relaxed">{question.stem}</h2>
              <div className="space-y-3" role="radiogroup" aria-label="Answer options">
                {Object.entries(question.options).map(([key, value]) => {
                  const isChosen = selected === key;
                  return <button
                    key={key}
                    role="radio"
                    aria-checked={isChosen}
                    disabled={busy || !!feedback}
                    className={`w-full text-left p-4 rounded-xl border transition-colors ${isChosen ? "border-sky-400 bg-sky-950/40 text-sky-100" : "border-slate-700 bg-slate-900/40 text-slate-200 hover:border-slate-500"}`}
                    onClick={() => setSelected(key)}
                  >
                    <span className="font-bold mr-3 font-mono">[{key}]</span>
                    {value}
                  </button>;
                })}
              </div>

              {!feedback && <div className="pt-2">
                <button className={`${button} bg-sky-600 hover:bg-sky-500 text-white font-semibold`} disabled={busy || !selected} onClick={() => void submit()}>
                  Check answer
                </button>
              </div>}

              {feedback && <div role="status" className="border-t border-slate-700 pt-5 space-y-4">
                <h3 className={`text-xl font-semibold ${feedback.is_correct ? "text-emerald-300" : "text-amber-300"}`}>{feedback.is_correct ? "Correct" : "Not quite"}</h3>
                <p>Correct answer: {feedback.correct_answer}. {question.options[feedback.correct_answer]}</p>
                <h3 className="font-semibold">Explanation</h3>
                <p className="leading-relaxed text-slate-200">{feedback.explanation}</p>
                <a href={feedback.source.url} target="_blank" rel="noreferrer" className="text-sm text-sky-300 underline">Source: {feedback.source.title}</a>
                <div className="flex flex-wrap gap-3">
                  <button disabled={busy} className={`${button} bg-sky-900`} onClick={() => void loadQuestion(topic, question.id)}>Next question</button>
                  <a className={button} href="#university-progress">View progress</a>
                </div>

                {!feedback.is_correct && (
                  <div className="border-t border-slate-700/80 pt-5 space-y-4">
                    {!remediation ? (
                      <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <h4 className="font-semibold text-indigo-300 flex items-center gap-2">
                            <span>🧠</span> Targeted Guided Practice Available
                          </h4>
                          <p className="text-xs text-slate-300 mt-1">
                            Work through this concept using targeted guided practice in a bounded 3-turn Socratic dialogue.
                          </p>
                          {remediationError && <p className="text-xs text-rose-400 mt-1">{remediationError}</p>}
                        </div>
                        <button
                          className={`${button} bg-indigo-600 hover:bg-indigo-500 text-white font-medium shrink-0`}
                          disabled={remediationLoading}
                          onClick={() => void initiateRemediation()}
                        >
                          {remediationLoading ? "Preparing guided practice..." : "Launch Socratic Remediation"}
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <ReasoningTimelineCard
                          timeline={remediation.timeline}
                          strategy={remediation.strategy}
                          turnNumber={remediation.turn_number}
                          maxTurns={remediation.max_turns}
                          remediationStatus={remediation.remediation_status}
                          isComplete={remediation.is_complete}
                        />

                        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-sky-400 uppercase tracking-wider">
                              Tutor Socratic {remediation.turn_number === 1 ? "Probe (Turn 1/3)" : remediation.turn_number === 2 ? "Guidance (Turn 2/3)" : "Consolidation & readiness check (Turn 3/3)"}
                            </span>
                            {remediation.is_complete ? (
                              <span className="text-xs text-emerald-400 font-medium">Session Complete</span>
                            ) : (
                              <span className="text-xs text-indigo-400">Step {remediation.turn_number} of 3</span>
                            )}
                          </div>

                          <p className="text-sm text-slate-200 leading-relaxed">
                            {remediation.tutor_message}
                          </p>

                          {remediation.socratic_probe && (
                            <div className="rounded-lg bg-indigo-950/40 border border-indigo-500/30 p-3">
                              <p className="text-xs font-semibold text-indigo-300">Socratic Question:</p>
                              <p className="text-xs text-slate-200 mt-1 italic font-medium">
                                "{remediation.socratic_probe}"
                              </p>
                            </div>
                          )}

                          {remediation.citations && remediation.citations.length > 0 && (
                            <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-2 items-center">
                              <span className="text-[11px] text-slate-400">Grounded PMC Evidence:</span>
                              {remediation.citations.map((c, i) => (
                                <span key={i} className="text-[10px] bg-slate-800 text-sky-300 px-2 py-0.5 rounded font-mono border border-slate-700">
                                  {c.ref || c.chunk_id}
                                </span>
                              ))}
                            </div>
                          )}

                          {remediationError && <p className="text-xs text-rose-400">{remediationError}</p>}

                          {/* Turn Dialogue Input (Turns 1-2) */}
                          {!remediation.is_complete && !remediation.transfer_available && (
                            <div className="space-y-2 pt-2">
                              <label htmlFor="remediation-input" className="text-xs text-slate-300 font-medium block">
                                Your Reasoning:
                              </label>
                              <textarea
                                id="remediation-input"
                                rows={2}
                                value={remediationInput}
                                onChange={(e) => setRemediationInput(e.target.value)}
                                placeholder="Type your explanation or answer the Socratic question..."
                                disabled={remediationLoading}
                                className="w-full rounded-lg bg-slate-950 border border-slate-700 p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-400 focus:outline-none"
                              />
                              <div className="flex justify-between items-center">
                                <button
                                  type="button"
                                  onClick={() => void abandonRemediation()}
                                  disabled={abandonLoading || remediation.is_complete}
                                  className="text-xs text-slate-400 hover:text-slate-200 underline"
                                >
                                  {abandonLoading ? "Exiting..." : "Exit Practice"}
                                </button>
                                <button
                                  onClick={() => void submitRemediationTurn()}
                                  disabled={!remediationInput.trim() || remediationLoading || abandonLoading}
                                  className={`${button} bg-indigo-600 hover:bg-indigo-500 text-white text-xs py-2 px-4`}
                                >
                                  {remediationLoading ? "Processing..." : `Submit Turn ${remediation.turn_number}`}
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Stage 4: Independent Transfer Assessment */}
                          {remediation.transfer_available && (
                            <div className="border-t border-slate-800 pt-4 space-y-3">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                                  <span>🎯</span> Independent Transfer Assessment
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] text-slate-400 font-mono">Held-out Item</span>
                                  <span className="text-[10px] text-amber-400/90 font-mono bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-800/40">Technical demo content — not clinically reviewed</span>
                                </div>
                              </div>

                              {isTerminalResultValid && transferResult ? (
                                <div className="space-y-3 rounded-lg bg-slate-950/80 border border-slate-800 p-3.5">
                                  <div className="flex items-center gap-2">
                                    <span className={`text-xs font-semibold ${transferResult.outcome === "TRANSFER_CONFIRMED" ? "text-emerald-400" : "text-amber-400"}`}>
                                      {transferResult.outcome === "TRANSFER_CONFIRMED"
                                        ? "Transfer demonstrated on this question"
                                        : transferResult.outcome === "TRANSFER_NOT_CONFIRMED"
                                        ? "More practice needed on this target concept"
                                        : "Transfer assessment unconfirmed"}
                                    </span>
                                  </div>
                                  <p className="text-xs text-slate-200 leading-relaxed">
                                    {transferResult.explanation}
                                  </p>
                                  {transferResult.timeline?.next_recommendation && (
                                    <div className="rounded-lg bg-purple-950/30 border border-purple-500/20 p-2.5">
                                      <span className="text-[11px] font-semibold text-purple-300 uppercase tracking-wider block">
                                        Next Adaptive Step:
                                      </span>
                                      <p className="text-xs text-slate-200 mt-1">
                                        {transferResult.timeline.next_recommendation}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              ) : transferUnavailable ? (
                                <div className="p-3.5 bg-slate-900/70 border border-slate-800 rounded-lg space-y-2">
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs text-slate-300">
                                      Transfer assessment unavailable for this session.
                                    </span>
                                    <button
                                      type="button"
                                      disabled={abandonLoading || remediation.is_complete}
                                      onClick={() => void abandonRemediation()}
                                      className="text-xs text-slate-400 hover:text-slate-200 underline"
                                    >
                                      {abandonLoading ? "Exiting..." : "Exit Practice"}
                                    </button>
                                  </div>
                                  <p className="text-[11px] text-slate-400">
                                    Targeted transfer items are currently curated for select baseline questions only.
                                  </p>
                                </div>
                              ) : transferItem ? (
                                <div className="space-y-3 rounded-lg bg-slate-950/70 border border-slate-800 p-3.5">
                                  <p className="text-xs text-slate-200 font-medium leading-relaxed">
                                    {transferItem.stem}
                                  </p>
                                  <div className="space-y-2">
                                    {Object.entries(transferItem.options).map(([optKey, optText]) => (
                                      <button
                                        key={optKey}
                                        type="button"
                                        disabled={transferLoading}
                                        onClick={() => setTransferSelected(optKey)}
                                        className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                                          transferSelected === optKey
                                            ? "border-emerald-400 bg-emerald-950/30 text-emerald-200 font-medium"
                                            : "border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700"
                                        }`}
                                      >
                                        <span className="font-mono font-bold mr-2 text-slate-400">[{optKey}]</span>
                                        {optText}
                                      </button>
                                    ))}
                                  </div>
                                  <div className="flex justify-end pt-2">
                                    <button
                                      type="button"
                                      disabled={!transferSelected || transferLoading}
                                      onClick={() => void submitTransferAssessment()}
                                      className={`${button} bg-emerald-600 hover:bg-emerald-500 text-white text-xs py-2 px-4`}
                                    >
                                      {transferLoading ? "Evaluating..." : "Submit Transfer Assessment"}
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <div className="p-3 bg-indigo-950/30 border border-indigo-500/20 rounded-lg flex items-center justify-between">
                                  <span className="text-xs text-slate-300">
                                    Socratic practice complete. Ready to take your independent assessment?
                                  </span>
                                  <button
                                    type="button"
                                    disabled={transferLoading}
                                    onClick={() => void fetchTransferItem()}
                                    className={`${button} bg-indigo-600 hover:bg-indigo-500 text-white text-xs py-2 px-3 shrink-0`}
                                  >
                                    {transferLoading ? "Loading..." : "Take Transfer Assessment"}
                                  </button>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>}
            </div>

            <SocraticTutorDrawer
              questionId={question.id}
              topic={topic}
              selectedOption={selected || null}
              isSubmitted={!!feedback}
              attemptKey={attemptKey || null}
            />
          </>}

          {complete && <div className="space-y-4">
            <h2 className="text-xl font-semibold">Topic practice complete</h2>
            <p>Review your progress, revisit these questions, or choose another topic.</p>
            <button className={button} disabled={busy} onClick={() => void loadQuestion(topic)}>Review topic</button>
            <button className={`${button} ml-3`} disabled={busy} onClick={() => void chooseSubject(subject)}>Choose another topic</button>
          </div>}
        </section>

        <aside id="university-progress" className="med-card p-6 space-y-5 self-start scroll-mt-6" aria-label="University progress">
          <h2 className="text-xl font-semibold">Your University progress</h2>
          {progress && <>
            <dl className="grid grid-cols-2 gap-4">
              <div><dt className="text-sm text-slate-400">Questions attempted</dt><dd className="text-3xl font-bold mt-2">{progress.attempted}</dd></div>
              <div><dt className="text-sm text-slate-400">Accuracy</dt><dd className="text-3xl font-bold mt-2">{progress.accuracy === null ? "—" : `${Math.round(progress.accuracy * 100)}%`}</dd></div>
            </dl>
            {progress.attempted === 0 && <p className="text-sm text-slate-300">Your learning starts here. Answer a question to see your progress.</p>}
            {progress.topics.filter(t => t.attempted > 0).map(t => <div key={`${t.subject}/${t.topic}`} className="border-t border-slate-700 pt-3">
              <p className="font-medium">{t.topic}</p>
              <p className="text-sm text-slate-300">{t.correct}/{t.attempted} correct · {t.mastery}</p>
              {t.accuracy !== null && t.accuracy < .6 && <p className="text-sm text-amber-300">Needs review</p>}
            </div>)}
            {progress.recommendation && <div className="space-y-3 border-t border-slate-700 pt-4">
              <h3 className="font-semibold">Recommended next topic</h3>
              <p className="text-sm text-slate-300">{progress.recommendation.topic}</p>
              <button className={button} disabled={busy} onClick={() => {
                const t = progress.recommendation!; void loadQuestion(t.topic, undefined, t.subject);
              }}>Practice recommended topic</button>
            </div>}
          </>}
          <p className="text-xs leading-relaxed text-slate-400">Practice accuracy reflects your recorded attempts, including repeats. It is not a clinical competency assessment. Progress is saved for this browser identity; clearing browser storage starts a new learner.</p>
        </aside>
      </div>
    </div>
  </main>;
}
