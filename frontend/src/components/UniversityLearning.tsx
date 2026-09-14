"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { SocraticTutorDrawer } from "./SocraticTutorDrawer";

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

  useEffect(() => {
    let active = true;
    try {
      learner.current = localStorage.getItem(learnerKey) || `uni-${crypto.randomUUID()}`;
      localStorage.setItem(learnerKey, learner.current);
    } catch { learner.current = `uni-${crypto.randomUUID()}`; }
    Promise.all([
      request<{ items: Choice[] }>("/subjects", learner.current),
      request<Progress>("/progress", learner.current),
    ]).then(([bank, p]) => { if (active) { setSubjects(bank.items); setProgress(p); } })
      .catch(() => { if (active) setError("University Learning could not load. Check your connection and retry."); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, []);

  async function run(action: () => Promise<void>) {
    setBusy(true); setError("");
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : "Please retry."); }
    finally { setBusy(false); }
  }

  function clearQuestion() { setQuestion(null); setFeedback(null); setSelected(""); setComplete(false); }

  async function chooseSubject(name: string) {
    await run(async () => {
      const data = await request<{ items: Choice[] }>(`/topics?subject=${encodeURIComponent(name)}`, learner.current);
      setSubject(name); setTopics(data.items); setTopic(""); clearQuestion();
    });
  }

  async function loadQuestion(name: string, after?: string, targetSubject = subject) {
    await run(async () => {
      const params = new URLSearchParams({ subject: targetSubject, topic: name });
      if (after) params.set("after", after);
      const data = await request<{ question: Question | null; position?: number; total?: number }>(`/question?${params}`, learner.current);
      setSubject(targetSubject); setTopic(name); setQuestion(data.question);
      setPosition(data.position || 0); setTotal(data.total || 0);
      setSelected(""); setFeedback(null); setComplete(!data.question);
      setAttemptKey(crypto.randomUUID());
    });
  }

  async function submit() {
    if (!question || !selected || feedback) return;
    await run(async () => {
      const result = await request<Feedback>("/answer", learner.current, {
        question_id: question.id, selected_option: selected, idempotency_key: attemptKey,
      });
      setFeedback(result); setProgress(result.progress);
    });
  }

  const button = "rounded-xl border border-slate-600 px-5 py-3 text-left text-slate-100 hover:border-sky-400 focus-visible:outline-2 focus-visible:outline-sky-400 disabled:opacity-50 disabled:cursor-not-allowed";

  return <main className="min-h-screen bg-slate-950 text-slate-100 px-5 py-8">
    <div className="max-w-5xl mx-auto space-y-8">
      <header className="space-y-4">
        <Link className="text-sky-300 underline" href="/">← MedicalPlab home</Link>
        <p className="text-sm uppercase tracking-widest text-sky-300">Undergraduate medical education</p>
        <h1 className="text-3xl font-bold">University Learning</h1>
        <p className="text-slate-300 max-w-2xl">Build your foundations with short, source-backed practice. Choose a topic, check your understanding, and review the explanation.</p>
        <p className="text-sm text-slate-400">Educational basic science • Independent University progress • No clinician approval claimed</p>
      </header>

      {error && <div role="alert" className="rounded-xl border border-amber-500 p-4 space-y-3">
        <p>{error}</p>
        <button className={button} onClick={() => window.location.reload()}>Reload University Learning</button>
        {question && !feedback && <p className="text-sm">You can also retry your answer below. A retry will not count twice.</p>}
      </div>}
      {busy && <p role="status" className="text-sky-300">Loading University Learning…</p>}

      <div className="grid lg:grid-cols-[1fr_300px] gap-6">
        <section className="med-card p-6 space-y-5" aria-label="University practice">
          <nav aria-label="Learning steps" className="flex flex-wrap gap-3 text-sm">
            <button disabled={busy} className="text-sky-300 underline disabled:opacity-50" onClick={() => { setSubject(""); setTopic(""); clearQuestion(); }}>Subjects</button>
            {subject && <button disabled={busy} className="text-sky-300 underline disabled:opacity-50" onClick={() => void chooseSubject(subject)}>{subject}</button>}
            {topic && <span>{topic}</span>}
          </nav>

          {!subject && <>
            <h2 className="text-xl font-semibold">Choose a subject</h2>
            {!busy && !error && !subjects.length && <p>No University questions are available yet. Please return later.</p>}
            {subjects.map(s => <button disabled={busy} className={`${button} block w-full`} key={s.name} onClick={() => void chooseSubject(s.name)}>{s.name}<span className="block text-sm text-slate-400 mt-1">{s.count} questions</span></button>)}
          </>}

          {subject && !topic && <>
            <h2 className="text-xl font-semibold">Choose a topic</h2>
            {topics.map(t => <button disabled={busy} className={`${button} block w-full`} key={t.name} onClick={() => void loadQuestion(t.name)}>{t.name}<span className="block text-sm text-slate-400 mt-1">{t.count} questions</span></button>)}
          </>}

          {question && <>
            <p className="text-sm text-slate-400">Question {position} of {total} • Foundation level</p>
            <h2 className="text-xl leading-relaxed font-semibold">{question.stem}</h2>
            <fieldset disabled={busy || !!feedback} className="space-y-3">
              <legend className="sr-only">Select one answer</legend>
              {Object.entries(question.options).map(([key, value]) => <label key={key} className={`${button} flex gap-3 items-start cursor-pointer ${selected === key ? "bg-sky-950 border-sky-400" : ""}`}>
                <input type="radio" name="university-answer" value={key} checked={selected === key} onChange={() => setSelected(key)} className="mt-1" />
                <span>{key}. {value}</span>
              </label>)}
            </fieldset>
            {!feedback && <button className={`${button} bg-sky-900`} disabled={!selected || busy} onClick={() => void submit()}>Check answer</button>}
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
            </div>}

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
