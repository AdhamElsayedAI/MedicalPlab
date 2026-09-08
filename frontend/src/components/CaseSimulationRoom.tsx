"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Activity,
  Heart,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Clock,
  User,
  PlusCircle,
  FileText,
  Volume2,
  VolumeX,
} from "lucide-react";
import { DEMO_PATIENT_CASE } from "@/lib/demo-data";
import { PatientCase } from "@/lib/types";

export const CaseSimulationRoom: React.FC = () => {
  const [patientCase, setPatientCase] = useState<PatientCase>(DEMO_PATIENT_CASE);
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [executedActions, setExecutedActions] = useState<string[]>([]);
  const [safetyAlert, setSafetyAlert] = useState<string | null>(null);
  const [isStabilized, setIsStabilized] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);

  // Dynamic Vitals
  const [hr, setHr] = useState(patientCase.vitals.heartRate);
  const [bp, setBp] = useState(patientCase.vitals.bloodPressure);
  const [spo2, setSpo2] = useState(patientCase.vitals.oxygenSat);

  // Canvas for Real-Time Dynamic ECG Waveform
  const ecgCanvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ecgCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let x = 0;
    let animId: number;
    const height = canvas.height;
    const width = canvas.width;
    const mid = height / 2;

    ctx.fillStyle = "#030712";
    ctx.fillRect(0, 0, width, height);

    const draw = () => {
      animId = requestAnimationFrame(draw);

      // Fade trail
      ctx.fillStyle = "rgba(3, 7, 18, 0.04)";
      ctx.fillRect(x, 0, 16, height);

      ctx.strokeStyle = isStabilized ? "#00e676" : "#00f2fe";
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(x, mid);

      // Generate P-Q-R-S-T ECG wave pattern
      const step = x % 70;
      let y = mid;
      if (step > 15 && step < 22) {
        y = mid - 8; // P wave
      } else if (step === 28) {
        y = mid + 6; // Q wave
      } else if (step === 32) {
        y = mid - 38; // R peak
      } else if (step === 36) {
        y = mid + 18; // S drop
      } else if (step > 42 && step < 54) {
        y = mid - 12; // T wave
      }

      ctx.lineTo(x + 2, y);
      ctx.stroke();

      x = (x + 2) % width;
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [isStabilized]);

  const handleExecuteAction = (actionId: string) => {
    const action = patientCase.availableInterventions.find((a) => a.id === actionId);
    if (!action) return;

    if (action.isContraindicated) {
      setSafetyAlert(action.contraindicationReason || "Contraindicated Intervention!");
      return;
    }

    setSafetyAlert(null);
    setExecutedActions((prev) => [...prev, actionId]);

    // If pericardiocentesis executed, patient stabilizes!
    if (actionId === "action_pericardiocentesis") {
      setIsStabilized(true);
      setHr(84);
      setBp("118/74");
      setSpo2(98);
    } else if (actionId === "action_fluids") {
      setBp("94/65");
      setHr(110);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-500/40">
              <Activity className="w-4 h-4" />
            </span>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
              EMERGENCY RESUSCITATION SIMULATOR
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            STAGE-F CLINICAL STATE ENGINE // REAL-TIME ECG MONITOR // CONTRAINDICATION SAFETY FILTER
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-900 border border-slate-700 text-slate-400 hover:text-white"
          >
            {soundEnabled ? <Volume2 className="w-3.5 h-3.5 text-cyan-400" /> : <VolumeX className="w-3.5 h-3.5" />}
            <span>Monitor Audio {soundEnabled ? "ON" : "OFF"}</span>
          </button>
        </div>
      </div>

      {/* Primary Vitals HUD Panel */}
      <div className="cyber-card rounded-2xl p-5 border border-cyan-500/30 bg-slate-950/90 shadow-[0_0_30px_rgba(0,0,0,0.8)]">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* ECG Monitor Canvas (Left 7 Cols) */}
          <div className="lg:col-span-7 bg-slate-950 rounded-xl p-3 border border-slate-800 relative overflow-hidden">
            <div className="flex items-center justify-between text-[11px] font-mono mb-1.5">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>LEAD II (RHYTHM STRIP)</span>
              </div>
              <span className="text-slate-400 font-mono">25 mm/s | 10 mm/mV</span>
            </div>

            <canvas
              ref={ecgCanvasRef}
              width={620}
              height={120}
              className="w-full h-[120px] rounded bg-[#030712] border border-slate-900"
            />

            <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span>QRS DURATION: 88ms</span>
              <span>QTc: 412ms</span>
              <span className={isStabilized ? "text-emerald-400 font-bold" : "text-cyan-400 font-bold"}>
                STATUS: {isStabilized ? "HEMODYNAMICALLY STABILIZED" : "DECOMPENSATING (TAMPONADE)"}
              </span>
            </div>
          </div>

          {/* Vitals Digital Meters (Right 5 Cols) */}
          <div className="lg:col-span-5 grid grid-cols-3 gap-3 text-center">
            {/* HR */}
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <div className="flex items-center justify-center gap-1 text-[11px] font-mono text-slate-400 mb-1">
                <Heart className="w-3.5 h-3.5 text-rose-500 animate-pulse" />
                <span>HR (bpm)</span>
              </div>
              <div className={`text-2xl font-black font-mono ${hr > 110 ? "text-rose-400" : "text-emerald-400"}`}>
                {hr}
              </div>
              <span className="text-[10px] font-mono text-slate-500">NORM: 60-100</span>
            </div>

            {/* BP */}
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <div className="text-[11px] font-mono text-slate-400 mb-1">
                BP (mmHg)
              </div>
              <div className={`text-xl font-black font-mono ${!isStabilized ? "text-amber-400" : "text-emerald-400"}`}>
                {bp}
              </div>
              <span className="text-[10px] font-mono text-slate-500">MAP: ~68</span>
            </div>

            {/* SpO2 */}
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <div className="text-[11px] font-mono text-slate-400 mb-1">
                SpO2 (%)
              </div>
              <div className={`text-2xl font-black font-mono ${spo2 < 93 ? "text-cyan-400" : "text-emerald-400"}`}>
                {spo2}%
              </div>
              <span className="text-[10px] font-mono text-slate-500">ON 4L O2</span>
            </div>
          </div>
        </div>
      </div>

      {/* Safety Alert Banner if Contraindicated Action clicked */}
      {safetyAlert && (
        <div className="p-4 rounded-xl bg-rose-950/80 border border-rose-500 text-white flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
          <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="text-xs font-mono font-bold text-rose-300 tracking-wider uppercase block">
              STAGE-D CLINICAL SAFETY VALIDATOR BLOCKED HARMFUL ORDER
            </span>
            <p className="text-xs text-rose-100 leading-relaxed font-sans">
              {safetyAlert}
            </p>
          </div>
        </div>
      )}

      {/* Split Details: Patient Profile & Action Decision Pad */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Patient Profile & Timeline (Left 5 Cols) */}
        <div className="lg:col-span-5 cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="text-xs font-mono text-cyan-400 font-bold flex items-center gap-1.5">
              <User className="w-4 h-4" />
              PATIENT FILE // RESUSCITATION BAY 2
            </span>
            <span className="text-[11px] font-mono text-slate-400">MRN: #UK-98442</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60 font-mono">
              <span className="text-slate-400">PATIENT NAME:</span>
              <span className="text-white font-bold">{patientCase.patient.name}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60 font-mono">
              <span className="text-slate-400">DEMOGRAPHICS:</span>
              <span className="text-white">{patientCase.patient.age} y/o {patientCase.patient.gender}</span>
            </div>
            <div className="py-1 border-b border-slate-800/60 font-mono">
              <span className="text-slate-400 block mb-1">PRESENTING COMPLAINT:</span>
              <span className="text-cyan-300 font-semibold">{patientCase.patient.presentingComplaint}</span>
            </div>
            <div className="py-1 border-b border-slate-800/60 font-mono">
              <span className="text-slate-400 block mb-1">KNOWN ALLERGIES:</span>
              <span className="text-rose-400 font-bold">{patientCase.patient.allergies.join(", ")}</span>
            </div>
          </div>

          {/* Clinical Timeline */}
          <div className="pt-2">
            <span className="text-[11px] font-mono text-slate-400 font-bold block mb-2">
              SYMPTOM TIMELINE:
            </span>
            <div className="space-y-2 border-l-2 border-cyan-500/30 pl-3">
              {patientCase.symptomsTimeline.map((item, i) => (
                <div key={i} className="text-xs">
                  <span className="text-[10px] font-mono text-cyan-400 font-bold mr-2">[{item.time}]</span>
                  <span className="text-slate-300">{item.event}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Decision Pad (Right 7 Cols) */}
        <div className="lg:col-span-7 cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="text-xs font-mono text-cyan-400 font-bold flex items-center gap-1.5">
              <FileText className="w-4 h-4" />
              CLINICAL ORDER PAD // DECISION INTERFACE
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              EXECUTED: {executedActions.length} ORDERS
            </span>
          </div>

          <div className="space-y-2.5">
            {patientCase.availableInterventions.map((action) => {
              const isExecuted = executedActions.includes(action.id);

              return (
                <div
                  key={action.id}
                  className={`p-3.5 rounded-xl border text-xs transition-all ${
                    isExecuted
                      ? "bg-slate-900/60 border-emerald-500/40 text-slate-300"
                      : "bg-slate-900/90 border-slate-800 hover:border-cyan-500/40"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-slate-950 border border-slate-800 text-slate-400">
                        {action.type}
                      </span>
                      <span className="font-bold text-white text-sm">{action.name}</span>
                    </div>

                    {!isExecuted ? (
                      <button
                        onClick={() => handleExecuteAction(action.id)}
                        className="px-3 py-1.5 rounded-lg text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white transition-colors"
                      >
                        Execute Order
                      </button>
                    ) : (
                      <span className="text-xs text-emerald-400 font-bold flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4" /> Order Fulfilled
                      </span>
                    )}
                  </div>

                  {isExecuted && (
                    <div className="mt-2 pt-2 border-t border-slate-800/80 text-xs text-slate-300 font-mono">
                      <span className="text-cyan-400 font-bold mr-1">AI Clinical Outcome:</span>
                      <span>{action.aiFeedback}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
