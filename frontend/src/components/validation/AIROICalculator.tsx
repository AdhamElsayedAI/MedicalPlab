"use client";

import React, { useState } from "react";
import {
  Calculator,
  TrendingUp,
  DollarSign,
  Users,
  Clock,
  Briefcase,
  Sparkles,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";

export const AIROICalculator: React.FC = () => {
  // Input parameters
  const [numCandidates, setNumCandidates] = useState<number>(200);
  const [currentFailureRate, setCurrentFailureRate] = useState<number>(38); // 38%
  const [resitCostPerCandidate, setResitCostPerCandidate] = useState<number>(4500); // £4,500
  const [locumCostPerMonth, setLocumCostPerMonth] = useState<number>(6200); // £6,200
  const [facultyHoursSaved, setFacultyHoursSaved] = useState<number>(18); // 18 hrs / candidate

  // Constants
  const facultyHourlyRate = 85; // £85 / hour consultant tariff
  const annualLicensePerDoctor = 540; // £45/mo = £540/yr B2B tiered SaaS
  const projectedFailureRateWithPlab = 11; // 11% (from 38% baseline)

  // Dynamic calculations
  const failureReductionPct = (currentFailureRate - projectedFailureRateWithPlab) / 100;
  const candidatesSavedFromFailure = Math.round(numCandidates * failureReductionPct);

  // 1. Direct Exam Resit Savings
  const directResitSavings = candidatesSavedFromFailure * resitCostPerCandidate;

  // 2. Locum Agency Replacement Savings (Assume 4 months vacancy avoided per failed doctor)
  const locumMonthsAvoided = candidatesSavedFromFailure * 4;
  const locumSavings = locumMonthsAvoided * locumCostPerMonth;

  // 3. Faculty Tutoring Time Reclaimed
  const totalFacultyHours = numCandidates * facultyHoursSaved;
  const facultyTimeValue = totalFacultyHours * facultyHourlyRate;

  // 4. Total Economic Value
  const totalGrossValue = directResitSavings + locumSavings + facultyTimeValue;

  // 5. MedicalPlab Software Investment
  const totalSoftwareCost = numCandidates * annualLicensePerDoctor;

  // 6. Net Value & ROI Multiplier
  const netSavings = Math.max(0, totalGrossValue - totalSoftwareCost);
  const roiMultiplier = (totalGrossValue / totalSoftwareCost).toFixed(1);
  const paybackMonths = ((totalSoftwareCost / totalGrossValue) * 12).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Top Banner with Projection Compliance Label */}
      <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              HEALTH ECONOMICS MODEL
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              [Prototype Projection &amp; Future Target]
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <Calculator className="w-5 h-5 text-emerald-400" />
            <span>Interactive Hospital Trust ROI &amp; Value Engine</span>
          </h2>
        </div>

        <div className="text-right">
          <span className="text-[10px] font-mono text-slate-400 block uppercase">Projected Net ROI</span>
          <span className="text-2xl font-black text-emerald-400 font-mono">{roiMultiplier}x Multiplier</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Inputs (5 cols) */}
        <div className="lg:col-span-5 p-5 rounded-2xl border border-slate-800 bg-slate-950/70 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
              Institutional Parameters
            </h3>
            <span className="text-xs font-mono text-slate-400">Adjust Sliders</span>
          </div>

          {/* Input 1: Number of Candidates */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-300 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-cyan-400" />
                <span>Junior Doctors / Candidates:</span>
              </span>
              <span className="font-bold text-cyan-300 font-mono text-sm">{numCandidates} Doctors</span>
            </div>
            <input
              type="range"
              min={25}
              max={600}
              step={25}
              value={numCandidates}
              onChange={(e) => setNumCandidates(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>25 Cohort</span>
              <span>300 Deanery</span>
              <span>600 Multi-Trust</span>
            </div>
          </div>

          {/* Input 2: Current Failure Rate */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-300 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>Current Exam Failure / Resit Rate:</span>
              </span>
              <span className="font-bold text-rose-300 font-mono text-sm">{currentFailureRate}%</span>
            </div>
            <input
              type="range"
              min={15}
              max={55}
              step={1}
              value={currentFailureRate}
              onChange={(e) => setCurrentFailureRate(Number(e.target.value))}
              className="w-full accent-rose-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>15% (UK Average)</span>
              <span>38% (IMG Benchmark)</span>
              <span>55% (High Deficit)</span>
            </div>
          </div>

          {/* Input 3: Resit & Placement Delay Cost */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-300">Resit Fee &amp; Delayed Placement Cost:</span>
              <span className="font-bold text-amber-300 font-mono text-sm">
                £{resitCostPerCandidate.toLocaleString()} / doctor
              </span>
            </div>
            <input
              type="range"
              min={2000}
              max={8000}
              step={500}
              value={resitCostPerCandidate}
              onChange={(e) => setResitCostPerCandidate(Number(e.target.value))}
              className="w-full accent-amber-400 cursor-pointer"
            />
          </div>

          {/* Input 4: Monthly Locum Agency Cost */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-300">Locum Agency Replacement (Per Month):</span>
              <span className="font-bold text-emerald-300 font-mono text-sm">
                £{locumCostPerMonth.toLocaleString()} / month
              </span>
            </div>
            <input
              type="range"
              min={4000}
              max={10000}
              step={200}
              value={locumCostPerMonth}
              onChange={(e) => setLocumCostPerMonth(Number(e.target.value))}
              className="w-full accent-emerald-400 cursor-pointer"
            />
          </div>

          {/* Input 5: Faculty Hours Saved */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-300 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-purple-400" />
                <span>Faculty Hours Saved per Doctor:</span>
              </span>
              <span className="font-bold text-purple-300 font-mono text-sm">{facultyHoursSaved} hrs / year</span>
            </div>
            <input
              type="range"
              min={5}
              max={35}
              step={1}
              value={facultyHoursSaved}
              onChange={(e) => setFacultyHoursSaved(Number(e.target.value))}
              className="w-full accent-purple-400 cursor-pointer"
            />
          </div>
        </div>

        {/* Right Column: Calculated Outputs (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Big Output Hero Card */}
          <div className="p-6 rounded-2xl border border-emerald-500/40 bg-gradient-to-br from-emerald-950/40 via-slate-900 to-slate-950">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-emerald-400 tracking-wider uppercase">
                Projected Annual Net Economic Value
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                [Future Target]
              </span>
            </div>

            <div className="mt-3 flex items-baseline gap-3">
              <h2 className="text-4xl sm:text-5xl font-black text-white font-mono tracking-tight">
                £{netSavings.toLocaleString()}
              </h2>
              <span className="text-sm font-bold text-emerald-400 font-mono">
                / Year Net Benefit
              </span>
            </div>

            <p className="text-xs text-slate-300 mt-2">
              Based on avoiding <strong className="text-white">{candidatesSavedFromFailure} failed exam cycles</strong> and reclaiming{" "}
              <strong className="text-white">{totalFacultyHours.toLocaleString()} consultant tutoring hours</strong>.
            </p>

            {/* Quick Metrics Bar */}
            <div className="mt-5 grid grid-cols-3 gap-3 pt-4 border-t border-slate-800">
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase block">ROI Multiplier</span>
                <span className="text-xl font-bold font-mono text-emerald-400">{roiMultiplier}x</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase block">Payback Period</span>
                <span className="text-xl font-bold font-mono text-cyan-400">{paybackMonths} Mo</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase block">Doctors Accelerated</span>
                <span className="text-xl font-bold font-mono text-purple-400">{candidatesSavedFromFailure}</span>
              </div>
            </div>
          </div>

          {/* Breakdown Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Locum Vacancy Avoidance */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60">
              <span className="text-[10px] font-mono text-slate-400 uppercase block">
                Locum Vacancy Avoidance
              </span>
              <span className="text-lg font-bold text-emerald-300 font-mono mt-1 block">
                £{locumSavings.toLocaleString()}
              </span>
              <span className="text-[11px] text-slate-500 mt-1 block">
                {locumMonthsAvoided} locum months saved
              </span>
            </div>

            {/* Resit Fee Elimination */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60">
              <span className="text-[10px] font-mono text-slate-400 uppercase block">
                Resit Fee Elimination
              </span>
              <span className="text-lg font-bold text-cyan-300 font-mono mt-1 block">
                £{directResitSavings.toLocaleString()}
              </span>
              <span className="text-[11px] text-slate-500 mt-1 block">
                {candidatesSavedFromFailure} candidates on 1st sitting
              </span>
            </div>

            {/* Faculty Productivity */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60">
              <span className="text-[10px] font-mono text-slate-400 uppercase block">
                Faculty Hours Value
              </span>
              <span className="text-lg font-bold text-purple-300 font-mono mt-1 block">
                £{facultyTimeValue.toLocaleString()}
              </span>
              <span className="text-[11px] text-slate-500 mt-1 block">
                {totalFacultyHours} hours at £85/hr
              </span>
            </div>
          </div>

          {/* Software Cost Transparency Notice */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400">
              Annual MedicalPlab Tiered SaaS License:
            </span>
            <span className="text-white font-bold">
              £{totalSoftwareCost.toLocaleString()} (£45/doctor/month)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
