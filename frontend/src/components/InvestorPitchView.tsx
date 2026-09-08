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
  Layers3,
  HeartPulse,
  BookOpen,
  Calendar,
  Target,
} from "lucide-react";

export const InvestorPitchView: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 med-fade-in" aria-label="Investor & Strategic Workspace">
      {/* Top Title & Investment Thesis Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5" style={{ background: "rgba(14,165,233,0.12)", color: "#7dd3fc", border: "1px solid rgba(14,165,233,0.25)" }}>
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              EXECUTIVE BRIEFING · SERIES SEED MEMO
            </span>
            <span className="text-xs font-medium text-emerald-400">
              CONFIDENTIAL DEMO ENVIRONMENT
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
            MedicalPlab: The AI Platform for Clinical Education &amp; Licensing
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
            Replacing static multiple-choice question banks with an evidence-grounded, zero-hallucination clinical intelligence operating system for doctors and healthcare institutions.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-right">
            <span className="text-[10px] text-slate-400 block font-medium">TOTAL ADDRESSABLE MARKET (TAM MODEL)</span>
            <span className="text-xl font-black text-sky-300 font-mono">$4.8 Billion USD</span>
          </div>
        </div>
      </div>

      {/* Vision, Problem & Solution 3-Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Vision */}
        <div className="med-card p-6 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-sky-400 uppercase tracking-wider">
            <Target className="w-4 h-4" />
            <span>The Vision</span>
          </div>
          <h2 className="text-base font-bold text-white">Clinical Competence for Every Doctor</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Ensure every international medical graduate and junior doctor demonstrates verified clinical reasoning and acute patient safety before stepping into a hospital ward.
          </p>
        </div>

        {/* Problem */}
        <div className="med-card p-6 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
            <Layers3 className="w-4 h-4" />
            <span>The Problem</span>
          </div>
          <h2 className="text-base font-bold text-white">Outdated $1,200 Question Banks</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Over 45,000 doctors prepare annually for UK licensing exams using flat, static multiple-choice PDFs. Candidates memorize trivia rather than developing acute clinical decision-making.
          </p>
        </div>

        {/* Solution */}
        <div className="med-card p-6 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
            <HeartPulse className="w-4 h-4" />
            <span>The Solution</span>
          </div>
          <h2 className="text-base font-bold text-white">Integrated Clinical Intelligence</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            A 4-pillar ecosystem: Socratic AI preceptor, interactive 3D spatial anatomy, realistic hemodynamic simulation, and mathematical evidence grounding against NICE &amp; BNF standards.
          </p>
        </div>
      </div>

      {/* 4 Core Business & Unit Economics Projections */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="med-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>INSTITUTIONAL TARGET</span>
            <Building2 className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-black font-mono text-white flex items-baseline gap-2">
            <span>14+</span>
            <span className="text-xs text-emerald-400 font-bold flex items-center">
              <ArrowUpRight className="w-3.5 h-3.5" /> NHS Foundation Trusts
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Multi-tenant pilot readiness for UK deaneries and university teaching hospitals.
          </p>
        </div>

        {/* Metric 2 */}
        <div className="med-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>CLINICAL EFFICACY DELTA</span>
            <Award className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-400 flex items-baseline gap-2">
            <span>+34%</span>
            <span className="text-xs text-slate-400 font-medium">Projected Pass Delta</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Targeted weakness remediation via Socratic simulation vs passive rote MCQ memorization.
          </p>
        </div>

        {/* Metric 3 */}
        <div className="med-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>INFERENCE UNIT ECONOMICS</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-purple-300 flex items-baseline gap-2">
            <span>&lt;$0.01</span>
            <span className="text-xs text-slate-400 font-medium">Inference Cost / Session</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Deterministic local retrieval and compressed guidelines ensure &gt;90% software gross margins.
          </p>
        </div>

        {/* Metric 4 */}
        <div className="med-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>TARGET LEARNER ENGAGEMENT</span>
            <TrendingUp className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-black font-mono text-white flex items-baseline gap-2">
            <span>3.8x</span>
            <span className="text-xs text-sky-400 font-medium">Session Retention</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            3D anatomy exploration linked with acute simulation triples daily active engagement.
          </p>
        </div>
      </div>

      {/* Defensible Moats & Revenue Model Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Defensible Moats */}
        <div className="lg:col-span-7 med-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-sky-400 flex items-center gap-1.5 uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4" />
              Defensible Clinical AI Advantages
            </span>
            <span className="text-[11px] text-slate-500 font-medium">WHY COMMODITY LLMS FAIL</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="font-bold text-white text-[13px] block">
                1. Zero-Hallucination Extractive Evidence Provenance
              </span>
              <p className="text-slate-300 leading-relaxed">
                Generic chatbots hallucinate drug dosages and lethal contraindications. MedicalPlab enforces mathematical claim verification requiring exact extractive provenance from NICE, BNF, and GMC guidelines before any token reaches the student.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="font-bold text-white text-[13px] block">
                2. Autonomous Patient Safety Interceptor
              </span>
              <p className="text-slate-300 leading-relaxed">
                A deterministic clinical safety filter catches hazardous candidate orders (e.g. nitrates in cardiac tamponade or thrombolysis in suspected dissection), shielding doctors from internalizing fatal prescribing habits.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="font-bold text-white text-[13px] block">
                3. Enterprise Institutional Multi-Tenancy
              </span>
              <p className="text-slate-300 leading-relaxed">
                NHS hospital trusts and medical faculties require strict data segregation, audit logs, and cohort progression telemetry. MedicalPlab provides complete multi-tenant tenant isolation out of the box.
              </p>
            </div>
          </div>
        </div>

        {/* Right 5 Cols: Revenue Model & Commercial Streams */}
        <div className="lg:col-span-5 med-card p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-xs font-bold text-sky-400 flex items-center gap-1.5 uppercase tracking-wider">
                <BarChart3 className="w-4 h-4" />
                Commercial Model &amp; Revenue Tiers
              </span>
            </div>

            <div className="mt-4 space-y-3 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-white">B2B Institutional Licenses</span>
                  <span className="text-sky-300 font-mono">£18,000 / yr / trust</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Sold to NHS Foundation Trusts, Postgraduate Deaneries, and International Medical Universities for cohort training.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-white">B2C Candidate Subscriptions</span>
                  <span className="text-sky-300 font-mono">£39 / month</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Direct candidate subscription for international medical graduates preparing for PLAB Part 1 &amp; 2 diets.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-white">Faculty Analytics Add-On</span>
                  <span className="text-sky-300 font-mono">£4,500 / yr</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Deanery cohort telemetry, weakness heatmaps, and custom institutional curriculum guideline ingestion.
                </p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-sky-950/30 border border-sky-500/25 text-center">
            <span className="text-xs text-sky-300 font-bold block mb-1">
              FINANCING ROADMAP · SEED ROUND
            </span>
            <span className="text-[11px] text-slate-300 leading-relaxed block">
              Expanding curriculum coverage to USMLE Step 1/2 and Australian Medical Council (AMC) examinations.
            </span>
          </div>
        </div>
      </div>

      {/* Strategic Product Roadmap */}
      <div className="med-card p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
            <Calendar className="w-4 h-4 text-purple-400" />
            <span>Product &amp; Clinical Expansion Roadmap</span>
          </div>
          <span className="text-[11px] text-slate-400">2026 Strategic Horizon</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/15 text-sky-300 border border-sky-500/30">
              Q1 2026 · CURRENT
            </span>
            <h3 className="font-bold text-white text-[13px]">UKMLA &amp; PLAB Core</h3>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Complete blueprint coverage of PLAB Part 1 &amp; 2, 3D cardiovascular &amp; neuro anatomy, and emergency simulation.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">
              Q2 2026
            </span>
            <h3 className="font-bold text-white text-[13px]">Voice OSCE Preceptor</h3>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Real-time conversational voice agent for clinical communication examinations and patient history taking.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
              Q3 2026
            </span>
            <h3 className="font-bold text-white text-[13px]">USMLE Step 1/2 CK</h3>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Expansion into North American medical licensing guidelines and American College of Cardiology standards.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
              Q4 2026
            </span>
            <h3 className="font-bold text-white text-[13px]">Hospital Resident CDS</h3>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Point-of-care clinical decision support companion for junior doctor hospital onboarding and night shifts.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
