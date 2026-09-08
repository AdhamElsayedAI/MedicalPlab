"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { INVESTOR_QUESTIONS_DATA, InvestorQuestion } from "@/lib/startup-data";

export default function FundraisingRoom() {
  const [activeQuestionId, setActiveQuestionId] = useState<string>(INVESTOR_QUESTIONS_DATA[0].id);
  const [activePillar, setActivePillar] = useState<"why_now" | "why_market" | "why_medicalplab" | "why_team">("why_now");

  const question = INVESTOR_QUESTIONS_DATA.find((q) => q.id === activeQuestionId) || INVESTOR_QUESTIONS_DATA[0];

  const pillars = [
    {
      id: "why_now",
      title: "Why Now?",
      headline: "The Convergence of Healthcare Shortages & LLM Hallucination Liability",
      body: "Medical schools and hospital trusts cannot tolerate generative AI hallucinations. Frontier generalist models have made basic AI accessible, but exposed a massive liability vacuum. Institutions are urgently tendering for compliance-certified, guideline-grounded AI architectures with tamper-proof audit trails.",
    },
    {
      id: "why_market",
      title: "Why This Market?",
      headline: "An Urgent $18.4B Global Addressable Market",
      body: "The 10-million clinician global deficit creates an unprecedented demand for accelerated, scalable clinical reasoning. Starting with high-urgency B2C medical licensure exams (UKMLA, PLAB, USMLE), we naturally bridge into high-retention enterprise medical school and hospital trust SaaS contracts.",
    },
    {
      id: "why_medicalplab",
      title: "Why MedicalPlab?",
      headline: "The Only Verified Deterministic Safety Shield in Healthcare EdTech",
      body: "We own a proprietary knowledge graph with 20,000+ indexed chunks of NICE NG185 and BNF guidelines, combined with a browser-native 60fps deterministic physiological flight simulator. We eliminate hallucination at the runtime level and catch 100% of contraindicated clinical decisions.",
    },
    {
      id: "why_team",
      title: "Why This Team?",
      headline: "Hybrid Clinical Precision Meets Senior AI Systems Architecture",
      body: "Our founding leadership bridges NHS consultant emergency clinicians, medical education researchers, and seasoned full-stack AI engineers who previously built production-grade low-latency inference systems. We live and breathe clinical safety and software scalability.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Institutional Due Diligence & Seed Round Preparation
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                VC Objection Simulator Active
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              MedicalPlab Fundraising & Investor Arena
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              The defensible investment thesis and battle-tested responses to tier-1 venture capital due diligence challenges.
            </p>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono text-right">
            <span className="text-slate-500 block text-[10px]">Seed Round Target:</span>
            <span className="text-emerald-400 font-bold text-base">$2.5M Seed</span>
            <span className="text-slate-400 text-[10px] block">18-Month Runway to $4.8M ARR</span>
          </div>
        </div>
      </div>

      {/* 4 Pillars of Seed Narrative */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider font-semibold">
            The 4 Pillars of Our Seed Investment Thesis
          </span>
          <span className="text-xs font-mono text-slate-500">Core Narrative</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {pillars.map((p) => {
            const isActive = activePillar === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setActivePillar(p.id as any)}
                className={`p-3 rounded-xl text-left border transition-all text-xs ${
                  isActive
                    ? "bg-cyan-950/70 border-cyan-400 text-cyan-300 shadow-md shadow-cyan-950/50 font-bold"
                    : "bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white"
                }`}
              >
                <div className="font-semibold text-sm">{p.title}</div>
              </button>
            );
          })}
        </div>

        {/* Active Pillar Narrative Box */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/90 space-y-2">
          <h4 className="text-sm md:text-base font-bold text-white font-mono">
            {pillars.find((p) => p.id === activePillar)?.headline}
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            {pillars.find((p) => p.id === activePillar)?.body}
          </p>
        </div>
      </div>

      {/* Investor Attack / Objection Simulator */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/30 rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
              Investor Objection Defense Simulator (5 Core Attacks)
            </span>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Click question to review founder defense playbook
          </span>
        </div>

        {/* Objection Questions Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
          {INVESTOR_QUESTIONS_DATA.map((q) => {
            const isSelected = activeQuestionId === q.id;
            return (
              <button
                key={q.id}
                onClick={() => setActiveQuestionId(q.id)}
                className={`text-left p-3 rounded-xl border transition-all text-xs ${
                  isSelected
                    ? "bg-amber-950/60 border-amber-400 text-amber-300 shadow-md shadow-amber-950/50 font-bold"
                    : "bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white"
                }`}
              >
                <div className="text-[10px] font-mono text-slate-500">{q.objectionTheme}</div>
                <div className="truncate mt-1 text-white font-medium">{q.question}</div>
              </button>
            );
          })}
        </div>

        {/* Selected Objection Detailed Breakdown */}
        <AnimatePresence mode="wait">
          <motion.div
            key={question.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="space-y-4 pt-2"
          >
            <div className="bg-slate-950 p-4 rounded-xl border border-amber-500/30">
              <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider block mb-1">
                VC Inquiry Challenge:
              </span>
              <h3 className="text-base md:text-lg font-bold text-white leading-snug">
                &ldquo;{question.question}&rdquo;
              </h3>
            </div>

            {/* Founder 4-Layer Defense Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Founder Response */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1.5">
                <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider block font-semibold">
                  Founder Verbal Response
                </span>
                <p className="text-xs text-slate-200 leading-relaxed italic">
                  &ldquo;{question.founderResponse}&rdquo;
                </p>
              </div>

              {/* Technical Proof */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1.5">
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider block font-semibold">
                  Technical Architecture Proof
                </span>
                <p className="text-xs text-slate-300 leading-relaxed font-mono">
                  {question.technicalProof}
                </p>
              </div>

              {/* Business Proof */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1.5">
                <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider block font-semibold">
                  Commercial & Regulatory Proof
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {question.businessProof}
                </p>
              </div>

              {/* Follow-up Defense */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1.5">
                <span className="text-xs font-mono text-purple-400 uppercase tracking-wider block font-semibold">
                  Long-Term Moat Defense
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {question.followUpDefense}
                </p>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
