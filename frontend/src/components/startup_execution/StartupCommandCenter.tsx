"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { COMPANY_METRIC_DATA, MetricClassification } from "@/lib/startup-data";
import InvestorDeckEngine from "./InvestorDeckEngine";
import MarketStrategy from "./MarketStrategy";
import ProductRoadmap from "./ProductRoadmap";
import FinancialModel from "./FinancialModel";
import TractionDashboard from "./TractionDashboard";
import PartnershipEngine from "./PartnershipEngine";
import FundraisingRoom from "./FundraisingRoom";
import FounderOperatingSystem from "./FounderOperatingSystem";
import StartupDemoController from "./StartupDemoController";

export default function StartupCommandCenter() {
  const [activeTab, setActiveTab] = useState<string>("command");
  const [showDemoController, setShowDemoController] = useState<boolean>(true);

  const tabs = [
    { id: "command", name: "Startup Cockpit", icon: "🚀", subtitle: "Founder Overview" },
    { id: "deck", name: "Seed Pitch Deck", icon: "📊", subtitle: "10-Slide VC Thesis" },
    { id: "strategy", name: "GTM Strategy", icon: "🎯", subtitle: "B2C & B2B Playbook" },
    { id: "roadmap", name: "Product Roadmap", icon: "🗺️", subtitle: "MVP to Scale" },
    { id: "financials", name: "Financial Model", icon: "💰", subtitle: "Unit Economics" },
    { id: "traction", name: "Traction Telemetry", icon: "📈", subtitle: "Audited Metrics" },
    { id: "partnerships", name: "Partnership BD", icon: "🤝", subtitle: "Institutional Pipeline" },
    { id: "questions", name: "Fundraising Room", icon: "🛡️", subtitle: "Objection Simulator" },
    { id: "os", name: "Founder OS", icon: "⚡", subtitle: "Daily Cadence" },
  ];

  const getBadgeStyle = (classification: MetricClassification) => {
    switch (classification) {
      case "[Verified]":
        return "bg-emerald-950/80 border-emerald-500/50 text-emerald-300";
      case "[Prototype]":
        return "bg-cyan-950/80 border-cyan-500/50 text-cyan-300";
      case "[Projection]":
        return "bg-amber-950/80 border-amber-500/50 text-amber-300";
      case "[Future Target]":
        return "bg-purple-950/80 border-purple-500/50 text-purple-300";
      default:
        return "bg-slate-800 border-slate-700 text-slate-300";
    }
  };

  const handleSelectViewFromDemo = (viewId: string) => {
    setActiveTab(viewId);
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 p-4 md:p-8 space-y-6">
      {/* Top Global Command Center Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-cyan-500/30 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-emerald-600/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-sm shadow-cyan-400" />
              <span className="text-xs font-mono uppercase tracking-widest text-cyan-400 font-semibold">
                Stage-Y Execution Layer • Startup Launch & Investor Readiness
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 font-bold">
                {COMPANY_METRIC_DATA.stage}
              </span>
            </div>

            <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
              MedicalPlab Startup Command Center
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 text-xl md:text-2xl mt-1 font-semibold">
                Venture-Scale Healthcare AI Startup Operating System
              </span>
            </h1>

            <p className="text-xs md:text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
              Transforming hackathon-winning technical architecture into a venture-funded, high-margin, market-ready enterprise healthcare startup.
            </p>
          </div>

          {/* Startup Readiness Scores & Pitch Demo Launcher */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {/* Readiness Scores Capsule */}
            <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-3.5 space-y-1.5 text-xs font-mono min-w-[240px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Product Maturity:</span>
                <span className="text-cyan-400 font-bold">{COMPANY_METRIC_DATA.scores.productMaturity}/100</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Investor Readiness:</span>
                <span className="text-emerald-400 font-bold">{COMPANY_METRIC_DATA.scores.investorReadiness}/100</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Market Readiness:</span>
                <span className="text-teal-400 font-bold">{COMPANY_METRIC_DATA.scores.marketReadiness}/100</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Technical Readiness:</span>
                <span className="text-indigo-400 font-bold">{COMPANY_METRIC_DATA.scores.technicalReadiness}/100</span>
              </div>
            </div>

            {/* 5-Min Pitch Experience Launcher */}
            <button
              onClick={() => setShowDemoController(!showDemoController)}
              className={`px-4 py-4 rounded-2xl font-bold font-mono text-xs transition-all shadow-xl flex flex-col items-center justify-center gap-1 ${
                showDemoController
                  ? "bg-cyan-500 text-black shadow-cyan-500/20"
                  : "bg-slate-900 border border-cyan-500/40 text-cyan-300 hover:bg-slate-800"
              }`}
            >
              <span className="text-base">🎬</span>
              <span>{showDemoController ? "Hide Pitch Controller" : "Launch 5-Min Pitch"}</span>
            </button>
          </div>
        </div>

        {/* Headline Startup Metrics Strip */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          {COMPANY_METRIC_DATA.headlineMetrics.slice(0, 4).map((hm) => (
            <div key={hm.label} className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <div className="flex items-center justify-center gap-1 mb-0.5">
                <span className="text-[10px] font-mono text-slate-400 uppercase">{hm.label}</span>
                <span className={`text-[9px] font-mono px-1 rounded border ${getBadgeStyle(hm.classification)}`}>
                  {hm.classification}
                </span>
              </div>
              <span className="text-lg md:text-xl font-bold font-mono text-white">{hm.value}</span>
              {hm.subtext && <span className="text-[10px] text-slate-500 font-mono block mt-0.5">{hm.subtext}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* 5-Minute Pitch Presentation Controller */}
      <AnimatePresence>
        {showDemoController && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <StartupDemoController
              onSelectView={handleSelectViewFromDemo}
              activeViewId={activeTab}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 9-Module Navigation Tabs */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-2.5 shadow-xl">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`text-left px-3.5 py-2.5 rounded-xl text-xs font-mono transition-all whitespace-nowrap flex items-center gap-2 border ${
                  isActive
                    ? "bg-cyan-500 text-black font-bold border-cyan-400 shadow-md shadow-cyan-500/20"
                    : "bg-slate-950/60 text-slate-400 border-slate-800/80 hover:border-slate-700 hover:text-white"
                }`}
              >
                <span>{tab.icon}</span>
                <div className="text-left">
                  <div className="font-semibold">{tab.name}</div>
                  <div className={`text-[10px] ${isActive ? "text-slate-900" : "text-slate-500"}`}>
                    {tab.subtitle}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Viewport */}
      <div className="transition-all duration-300">
        {activeTab === "command" && (
          <div className="space-y-6">
            {/* Founder Priority Panel for This Week */}
            <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/30 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                  <span className="text-xs font-mono font-bold uppercase text-cyan-300">
                    Founder Weekly Priority Panel (Sprint 36)
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  Execution Focus: Product Validation & Investor Briefings
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase font-semibold">Priority 1: Product</span>
                  <h4 className="text-sm font-bold text-white">UKMLA Alpha Feedback</h4>
                  <p className="text-xs text-slate-400">Complete 15 one-on-one diagnostic sessions with PLAB 1 candidates.</p>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-emerald-400 uppercase font-semibold">Priority 2: Growth</span>
                  <h4 className="text-sm font-bold text-white">Student Society Loops</h4>
                  <p className="text-xs text-slate-400">Partner with 3 UK university student medical societies for organic onboarding.</p>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-teal-400 uppercase font-semibold">Priority 3: Enterprise</span>
                  <h4 className="text-sm font-bold text-white">Imperial College Pilot</h4>
                  <p className="text-xs text-slate-400">Submit formal curriculum committee pilot proposal for 450 students.</p>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-purple-400 uppercase font-semibold">Priority 4: Fundraising</span>
                  <h4 className="text-sm font-bold text-white">Seed Syndicate Briefings</h4>
                  <p className="text-xs text-slate-400">Complete pitch deck circulation with 5 health tech specialist angel funds.</p>
                </div>
              </div>
            </div>

            {/* Quick Preview of Other Modules */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div
                onClick={() => setActiveTab("deck")}
                className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all space-y-2"
              >
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-cyan-400 font-bold">10-Slide VC Deck</span>
                  <span>Inspect →</span>
                </div>
                <h4 className="text-base font-bold text-white">Institutional Seed Pitch</h4>
                <p className="text-xs text-slate-400">Full 10-slide VC thesis with speaker notes, investor takeaways, and metrics.</p>
              </div>

              <div
                onClick={() => setActiveTab("financials")}
                className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all space-y-2"
              >
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-emerald-400 font-bold">Unit Economics</span>
                  <span>Inspect →</span>
                </div>
                <h4 className="text-base font-bold text-white">Financial SaaS Model</h4>
                <p className="text-xs text-slate-400">CAC $42, LTV $380, Gross Margin 84% with dynamic assumption sliders.</p>
              </div>

              <div
                onClick={() => setActiveTab("questions")}
                className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all space-y-2"
              >
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-amber-400 font-bold">VC Due Diligence</span>
                  <span>Inspect →</span>
                </div>
                <h4 className="text-base font-bold text-white">Investor Objection Simulator</h4>
                <p className="text-xs text-slate-400">Battle-tested responses to &ldquo;Why not ChatGPT?&rdquo; and hospital willingness to pay.</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === "deck" && <InvestorDeckEngine />}
        {activeTab === "strategy" && <MarketStrategy />}
        {activeTab === "roadmap" && <ProductRoadmap />}
        {activeTab === "financials" && <FinancialModel />}
        {activeTab === "traction" && <TractionDashboard />}
        {activeTab === "partnerships" && <PartnershipEngine />}
        {activeTab === "questions" && <FundraisingRoom />}
        {activeTab === "os" && <FounderOperatingSystem />}
      </div>
    </div>
  );
}
