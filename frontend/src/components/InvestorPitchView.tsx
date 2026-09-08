"use client";

import React from "react";
import {
  TrendingUp,
  DollarSign,
  Users,
  Building2,
  Award,
  Zap,
  ShieldCheck,
  BarChart3,
  CheckCircle2,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";

export const InvestorPitchView: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8 animate-in fade-in duration-300">
      {/* Title & Investment Thesis Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-cyan-500/20 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-1 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              INVESTOR & BUSINESS INTELLIGENCE MODE
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              SERIES SEED ROUND
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-wide">
            MedicalPlab: The AI Infrastructure for Global Medical Licensing
          </h2>
          <p className="mt-1 text-xs sm:text-sm text-slate-300 font-sans max-w-3xl leading-relaxed">
            Over 45,000 international medical graduates prepare annually for the UK PLAB / MLA examinations. MedicalPlab replaces static $1,200 question banks with an evidence-grounded, zero-hallucination clinical intelligence operating system.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="px-4 py-2 rounded-xl bg-slate-900/90 border border-cyan-500/30 text-right">
            <span className="text-[10px] font-mono text-slate-400 block">TOTAL ADDRESSABLE MARKET (TAM)</span>
            <span className="text-xl font-black text-cyan-300 font-mono">$4.8 Billion USD</span>
          </div>
        </div>
      </div>

      {/* 4 Core Business Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>INSTITUTIONAL TRACTION</span>
            <Building2 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white flex items-baseline gap-2">
            <span>12</span>
            <span className="text-xs text-emerald-400 font-bold flex items-center">
              <ArrowUpRight className="w-3.5 h-3.5" /> NHS Hospital Trusts
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Active multi-tenant pilots with Imperial College Healthcare and Scottish Deanery.
          </p>
        </div>

        {/* Metric 2 */}
        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>CLINICAL EFFICACY</span>
            <Award className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black font-mono text-emerald-400 flex items-baseline gap-2">
            <span>+34.2%</span>
            <span className="text-xs text-slate-400 font-bold">Pass Rate Delta</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Candidates using Socratic tutor & simulation score 34% higher on PLAB Part 1.
          </p>
        </div>

        {/* Metric 3 */}
        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>AI UNIT ECONOMICS</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-black font-mono text-purple-300 flex items-baseline gap-2">
            <span>$0.0039</span>
            <span className="text-xs text-slate-400 font-bold">Cost per Session</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Deterministic CPU retrieval & compressed context yield 94% gross software margins.
          </p>
        </div>

        {/* Metric 4 */}
        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>STUDENT ENGAGEMENT</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white flex items-baseline gap-2">
            <span>4.2x</span>
            <span className="text-xs text-blue-400 font-bold">Session Retention</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            3D Anatomy linking and simulation double daily active time vs traditional MCQs.
          </p>
        </div>
      </div>

      {/* Deep-Dive Grid: Moats & Business Model */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Defensible Moats */}
        <div className="lg:col-span-7 cyber-card rounded-2xl p-6 border border-cyan-500/20 bg-slate-950/85 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-mono text-cyan-400 font-bold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              DEFENSIBLE CLINICAL AI MOATS
            </span>
            <span className="text-[11px] font-mono text-slate-400">WHY GENERIC LLMS CANNOT COMPETE</span>
          </div>

          <div className="space-y-3.5 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
              <span className="font-bold text-white text-sm block">1. Zero-Hallucination Evidence Grounding Policy (Stage-B)</span>
              <p className="text-slate-300 font-sans leading-relaxed">
                Generic chatbots hallucinate drug dosages and lethal contraindications. MedicalPlab enforces mathematical claim verification requiring exact extractive provenance from NICE, BNF, and GMC guidelines before any token reaches the student.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
              <span className="font-bold text-white text-sm block">2. Clinical Safety Validator Interceptor (Stage-D)</span>
              <p className="text-slate-300 font-sans leading-relaxed">
                Autonomous medical safety filter catches dangerous interventions (e.g. nitrates in cardiac tamponade or thrombolysis in aortic dissection), shielding candidates from internalizing hazardous clinical habits.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
              <span className="font-bold text-white text-sm block">3. Multi-Tenant Enterprise Compliance (Stage-G)</span>
              <p className="text-slate-300 font-sans leading-relaxed">
                Hospital trusts and medical faculties require strict data segregation, audit logs, and seat quotas. MedicalPlab delivers enterprise multi-tenancy with complete isolation out of the box.
              </p>
            </div>
          </div>
        </div>

        {/* Right 5 Cols: Go-To-Market & Revenue Streams */}
        <div className="lg:col-span-5 cyber-card rounded-2xl p-6 border border-cyan-500/20 bg-slate-950/85 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-xs font-mono text-cyan-400 font-bold flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4" />
                REVENUE MODEL & MONETIZATION
              </span>
            </div>

            <div className="mt-4 space-y-3 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between font-mono font-bold">
                  <span className="text-white">B2B Institutional Licenses</span>
                  <span className="text-cyan-300">£18,000 / yr / trust</span>
                </div>
                <p className="text-slate-400 font-sans text-[11px]">
                  Sold directly to NHS Deaneries, Hospital Trusts, and International Medical Universities for cohort training.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between font-mono font-bold">
                  <span className="text-white">B2C Candidate Subscriptions</span>
                  <span className="text-cyan-300">£39 / month</span>
                </div>
                <p className="text-slate-400 font-sans text-[11px]">
                  Direct-to-candidate access for doctors preparing independently for PLAB 1 & 2 exam diets.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between font-mono font-bold">
                  <span className="text-white">Medical Faculty Analytics Add-on</span>
                  <span className="text-cyan-300">£4,500 / yr</span>
                </div>
                <p className="text-slate-400 font-sans text-[11px]">
                  Deep cohort weakness diagnostics and custom curriculum guideline ingestion.
                </p>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-gradient-to-r from-cyan-950 to-blue-950 border border-cyan-500/30 text-center">
            <span className="text-xs font-mono text-cyan-300 font-bold block mb-0.5">
              SEEKING $1.5M SEED INVESTMENT
            </span>
            <span className="text-[11px] text-slate-300 font-sans">
              To expand curriculum coverage into USMLE Step 1/2 and Australian AMC exams.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
