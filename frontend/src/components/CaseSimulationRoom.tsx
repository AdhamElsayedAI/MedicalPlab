"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Activity,
  Heart,
  HeartPulse,
  AlertTriangle,
  CheckCircle,
  ShieldAlert,
  Clock,
  User,
  ChevronRight,
  Volume2,
  VolumeX,
  Pill,
  Stethoscope,
  ClipboardList,
  TrendingUp,
  AlertCircle,
  Sparkles,
  Award,
  ChevronDown,
  RotateCcw,
} from "lucide-react";
import { DEMO_PATIENT_CASE, STEMI_PATIENT_CASE } from "@/lib/demo-data";
import { PatientCase } from "@/lib/types";

export const CaseSimulationRoom: React.FC = () => {
  const [selectedCaseId, setSelectedCaseId] = useState<string>("stemi");
  const [patientCase, setPatientCase] = useState<PatientCase>(STEMI_PATIENT_CASE);
  const [executedActions, setExecutedActions] = useState<string[]>([]);
  const [safetyAlert, setSafetyAlert] = useState<string | null>(null);
  const [isStabilized, setIsStabilized] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [activeAbcdeTab, setActiveAbcdeTab] = useState<"ALL" | "A_B" | "C" | "D_E">("ALL");
  const [sbarOpen, setSbarOpen] = useState(true);

  // Dynamic Vitals
  const [hr, setHr] = useState(patientCase.vitals.heartRate);
  const [bp, setBp] = useState(patientCase.vitals.bloodPressure);
  const [spo2, setSpo2] = useState(patientCase.vitals.oxygenSat);

  // Resuscitation Log
  const [resusLog, setResusLog] = useState<{ time: string; text: string; status: "success" | "warning" }[]>([
    { time: "10:14:02", text: "Patient arrived via emergency ambulance. Triaged Category 1 (Resus Bay 2).", status: "warning" },
    { time: "10:14:15", text: "Continuous monitor attached: Hyperacute ST-segment elevation detected.", status: "warning" },
  ]);

  // ECG canvas
  const ecgCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const resetCaseState = (c: PatientCase) => {
    setPatientCase(c);
    setExecutedActions([]);
    setSafetyAlert(null);
    setIsStabilized(false);
    setHr(c.vitals.heartRate);
    setBp(c.vitals.bloodPressure);
    setSpo2(c.vitals.oxygenSat);
    setResusLog([
      { time: "10:14:02", text: `Patient (${c.patient.name}) admitted to Resus Bay 2. Immediate triage active.`, status: "warning" },
      { time: "10:14:15", text: `Continuous ECG active: ${c.vitals.ecgRhythm}.`, status: "warning" },
    ]);
  };

  const handleSwitchCase = (caseType: "stemi" | "tamponade") => {
    setSelectedCaseId(caseType);
    if (caseType === "stemi") {
      resetCaseState(STEMI_PATIENT_CASE);
    } else {
      resetCaseState(DEMO_PATIENT_CASE);
    }
  };

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

    const isStemi = selectedCaseId === "stemi";

    const draw = () => {
      animId = requestAnimationFrame(draw);

      ctx.fillStyle = "rgba(3, 7, 18, 0.04)";
      ctx.fillRect(x, 0, 16, height);

      ctx.strokeStyle = isStabilized ? "#22c55e" : isStemi ? "#ef4444" : "#38bdf8";
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(x, mid);

      const step = x % 70;
      let y = mid;

      if (isStemi && !isStabilized) {
        // High ST elevation waveform
        if (step > 15 && step < 22) {
          y = mid - 6; // P wave
        } else if (step === 28) {
          y = mid + 4; // Q wave
        } else if (step === 32) {
          y = mid - 40; // High R wave
        } else if (step > 33 && step < 46) {
          y = mid - 24; // Elevated ST segment (Tombstone ST)
        } else if (step >= 46 && step < 54) {
          y = mid - 14; // High T wave
        }
      } else {
        // Normal or stabilized rhythm
        if (step > 15 && step < 22) {
          y = mid - 8;
        } else if (step === 28) {
          y = mid + 6;
        } else if (step === 32) {
          y = mid - (isStabilized ? 38 : 22);
        } else if (step === 36) {
          y = mid + (isStabilized ? 18 : 10);
        } else if (step > 42 && step < 54) {
          y = mid - 12;
        }
      }

      ctx.lineTo(x + 2, y);
      ctx.stroke();

      x = (x + 2) % width;
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [isStabilized, selectedCaseId]);

  const handleExecuteAction = (actionId: string) => {
    const action = patientCase.availableInterventions.find((a) => a.id === actionId);
    if (!action) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    if (action.isContraindicated) {
      setSafetyAlert(action.contraindicationReason || "Contraindicated intervention — order intercepted by patient safety filter.");
      setResusLog((prev) => [
        { time: timeStr, text: `INTERCEPTED: ${action.name} blocked by Clinical Safety Filter.`, status: "warning" },
        ...prev,
      ]);
      return;
    }

    setSafetyAlert(null);
    setExecutedActions((prev) => [...prev, actionId]);

    // Flagship STEMI Handlers
    if (actionId === "action_stemi_ppci") {
      setIsStabilized(true);
      setHr(76);
      setBp("124/78");
      setSpo2(99);
      setResusLog((prev) => [
        { time: timeStr, text: `PPCI REPERFUSION SUCCESS: LAD 99% lesion stented. TIMI 3 flow restored. ST elevations normalized.`, status: "success" },
        ...prev,
      ]);
    } else if (actionId === "action_stemi_dapt") {
      setHr(96);
      setBp("132/84");
      setResusLog((prev) => [
        { time: timeStr, text: `DAPT Loading administered (Aspirin 300mg + Ticagrelor 180mg). Antiplatelet coverage active.`, status: "success" },
        ...prev,
      ]);
    } else if (actionId === "action_pericardiocentesis") {
      setIsStabilized(true);
      setHr(84);
      setBp("118/74");
      setSpo2(98);
      setResusLog((prev) => [
        { time: timeStr, text: `DECOMPRESSION SUCCESS: Pericardiocentesis completed. 120ml aspirated. Hemodynamics restored.`, status: "success" },
        ...prev,
      ]);
    } else if (actionId === "action_fluids") {
      setBp("94/65");
      setHr(110);
      setResusLog((prev) => [
        { time: timeStr, text: `IV Crystalloid bolus administered. RV preload transiently augmented (BP 94/65 mmHg).`, status: "success" },
        ...prev,
      ]);
    } else {
      setResusLog((prev) => [
        { time: timeStr, text: `ORDERED: ${action.name}. Results integrated into clinical chart.`, status: "success" },
        ...prev,
      ]);
    }
  };

  const typeIcon = (type: string) => {
    switch (type) {
      case "medication":
        return <Pill className="w-3.5 h-3.5" />;
      case "procedure":
        return <Stethoscope className="w-3.5 h-3.5" />;
      case "investigation":
        return <ClipboardList className="w-3.5 h-3.5" />;
      default:
        return <TrendingUp className="w-3.5 h-3.5" />;
    }
  };

  return (
    <section
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 med-fade-in"
      aria-label="Emergency Resuscitation Bay"
    >
      {/* Section Header with Hospital Bay Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                background: "rgba(34,197,94,0.15)",
                border: "1px solid rgba(34,197,94,0.25)",
              }}
            >
              <HeartPulse className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="section-header">Emergency Clinical Simulation</h2>
                <span className="med-badge med-badge-primary">Resus Bay 2</span>
              </div>
              <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                <span className="font-semibold text-slate-300">St. Mary&apos;s NHS Trust · Resus Bay 2</span>
                <span>•</span>
                <span className="text-amber-400 font-medium">Triage Priority: Category 1 (Immediate)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Case Switcher & Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => handleSwitchCase("stemi")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                selectedCaseId === "stemi"
                  ? "bg-sky-500/20 text-sky-300 border border-sky-400/40"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Flagship STEMI
            </button>
            <button
              onClick={() => handleSwitchCase("tamponade")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                selectedCaseId === "tamponade"
                  ? "bg-sky-500/20 text-sky-300 border border-sky-400/40"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Tamponade
            </button>
          </div>

          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-medium"
            style={{
              background: isStabilized ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
              color: isStabilized ? "#86efac" : "#fca5a5",
              border: `1px solid ${isStabilized ? "rgba(34,197,94,0.25)" : "rgba(239,68,68,0.25)"}`,
            }}
          >
            <span
              className={`w-2 h-2 rounded-full ${isStabilized ? "bg-green-400" : "bg-red-400"}`}
              style={{ animation: isStabilized ? "none" : "pulse 1s infinite" }}
            />
            {isStabilized ? "Hemodynamically Stabilized" : "Critical Emergency"}
          </div>

          <button
            onClick={() => resetCaseState(selectedCaseId === "stemi" ? STEMI_PATIENT_CASE : DEMO_PATIENT_CASE)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white bg-slate-900 border border-slate-800 transition-colors"
            title="Reset Simulation Case"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* SBAR Clinical Handover Collapsible Drawer */}
      <div className="med-card p-4 rounded-xl">
        <button
          onClick={() => setSbarOpen(!sbarOpen)}
          className="w-full flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-2 text-xs font-bold text-sky-300">
            <ClipboardList className="w-4 h-4 text-sky-400" />
            <span>SBAR Emergency Handover Briefing</span>
            <span className="text-[10px] text-slate-500 font-normal">(Ambulance to Resus Team)</span>
          </div>
          <ChevronDown
            className={`w-4 h-4 text-slate-400 transition-transform ${sbarOpen ? "rotate-180" : ""}`}
          />
        </button>

        {sbarOpen && (
          <div className="mt-3 pt-3 border-t border-slate-800 grid grid-cols-1 md:grid-cols-4 gap-3 text-xs med-fade-in">
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="font-bold text-sky-400 block mb-0.5">S · Situation</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {patientCase.patient.name}, {patientCase.patient.age}M, presenting with {patientCase.patient.presentingComplaint}.
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="font-bold text-purple-400 block mb-0.5">B · Background</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                {patientCase.patient.pastHistory.slice(0, 2).join("; ")}.
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="font-bold text-amber-400 block mb-0.5">A · Assessment</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                HR {patientCase.vitals.heartRate}, BP {patientCase.vitals.bloodPressure}. {patientCase.vitals.ecgRhythm}.
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="font-bold text-emerald-400 block mb-0.5">R · Recommendation</span>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Execute ABCDE resuscitation, continuous ECG, and urgent definitive reperfusion.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ECG Monitor + Real-Time Vitals */}
      <div className="med-card p-5">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-center">
          {/* ECG Monitor */}
          <div className="lg:col-span-7">
            <div className="flex items-center justify-between mb-2">
              <div
                className="flex items-center gap-2 text-[12px] font-semibold"
                style={{ color: isStabilized ? "#86efac" : selectedCaseId === "stemi" ? "#ef4444" : "#38bdf8" }}
              >
                <span
                  className={`w-2 h-2 rounded-full ${isStabilized ? "bg-green-400" : "bg-red-400"} animate-pulse`}
                />
                Lead II/V2 — Continuous Rhythm Strip
              </div>
              <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                <span>25 mm/s</span>
                <span>10 mm/mV</span>
                <span className={`font-semibold ${isStabilized ? "text-green-400" : "text-amber-400"}`}>
                  {isStabilized ? "Normal Sinus Rhythm" : patientCase.vitals.ecgRhythm}
                </span>
              </div>
            </div>

            <div className="monitor-display">
              <canvas
                ref={ecgCanvasRef}
                width={620}
                height={110}
                className="w-full rounded"
                style={{ height: "110px", background: "#030712" }}
              />
            </div>

            <div className="flex items-center justify-between mt-2 text-[10px] font-mono text-slate-500">
              <span>Rhythm: {isStabilized ? "Regular Sinus" : "Hyperacute ST Elevation"}</span>
              <span>Reperfusion Target: &lt;120 mins</span>
              <span>Status: {isStabilized ? "Reperfused (TIMI 3)" : "Cath Lab Alerted"}</span>
            </div>
          </div>

          {/* Vitals Grid */}
          <div className="lg:col-span-5 grid grid-cols-3 gap-3">
            {/* HR */}
            <div className="vital-card">
              <div className="flex items-center justify-center gap-1 vital-label mb-2">
                <Heart className="w-3 h-3 text-rose-400 animate-pulse" />
                HR
              </div>
              <div className={`vital-value ${hr > 100 ? "text-rose-400" : "text-emerald-400"}`}>{hr}</div>
              <div className="text-[10px] text-slate-500 font-mono mt-1">bpm</div>
            </div>

            {/* BP */}
            <div className="vital-card">
              <div className="vital-label mb-2">BP</div>
              <div className={`vital-value text-[22px] ${!isStabilized ? "text-amber-400" : "text-emerald-400"}`}>
                {bp}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-1">mmHg</div>
            </div>

            {/* SpO2 */}
            <div className="vital-card">
              <div className="vital-label mb-2">SpO₂</div>
              <div className={`vital-value ${spo2 < 95 ? "text-sky-400" : "text-emerald-400"}`}>
                {spo2}
                <span className="text-[16px]">%</span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-1">Room Air</div>
            </div>
          </div>
        </div>
      </div>

      {/* Safety Interceptor Banner */}
      {safetyAlert && (
        <div
          className="flex items-start gap-4 p-4 rounded-xl med-fade-in"
          style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.3)" }}
          role="alert"
        >
          <ShieldAlert className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs">
            <div className="font-bold text-red-400">Clinical Safety Interceptor — Hazardous Order Blocked</div>
            <p className="text-red-200 leading-relaxed">{safetyAlert}</p>
            <div className="text-[11px] text-red-300 font-mono pt-1">
              Autonomous Safety Filter: Prevents internalizing lethal prescribing habits during medical simulation.
            </div>
          </div>
        </div>
      )}

      {/* Post-Stabilization Debrief Scorecard */}
      {isStabilized && (
        <div
          className="p-5 rounded-2xl med-fade-in"
          style={{
            background: "rgba(34,197,94,0.06)",
            border: "1px solid rgba(34,197,94,0.25)",
          }}
        >
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-emerald-500/20">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-emerald-400" />
              <span className="font-bold text-white text-sm">
                Case Debrief: {selectedCaseId === "stemi" ? "STEMI Reperfusion Successful" : "Tamponade Decompressed"}
              </span>
            </div>
            <span className="med-badge" style={{ background: "rgba(34,197,94,0.15)", color: "#86efac", border: "1px solid rgba(34,197,94,0.3)" }}>
              NICE NG185 Adherence: 100%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-emerald-500/20">
              <span className="text-[11px] text-slate-400 block mb-0.5">Diagnostic Accuracy</span>
              <span className="font-bold text-white">Anterior STEMI (LAD) Identified</span>
              <p className="text-[11px] text-slate-400 mt-1">Confirmed V1-V4 elevations without delay for unneeded cardiac enzymes.</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-emerald-500/20">
              <span className="text-[11px] text-slate-400 block mb-0.5">Patient Safety Filter</span>
              <span className="font-bold text-emerald-400">Zero Harm Incurred</span>
              <p className="text-[11px] text-slate-400 mt-1">Inappropriate thrombolysis blocked; PPCI pathway preserved.</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-emerald-500/20">
              <span className="text-[11px] text-slate-400 block mb-0.5">Definitive Intervention</span>
              <span className="font-bold text-sky-400">Emergency Primary PCI</span>
              <p className="text-[11px] text-slate-400 mt-1">Door-to-balloon target achieved within 120 mins per NICE guideline standards.</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Simulation Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 5 Cols: Patient Chart & Resuscitation Log */}
        <div className="lg:col-span-5 space-y-6">
          {/* Patient Profile */}
          <div className="med-card p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold text-white">
                <User className="w-4 h-4 text-sky-400" />
                <span>Patient Electronic Record</span>
              </div>
              <span className="med-badge med-badge-primary">NHS #482-901-22</span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Patient:</span>
                <span className="font-medium text-slate-200">{patientCase.patient.name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Demographics:</span>
                <span className="font-medium text-slate-200">{patientCase.patient.age} y/o {patientCase.patient.gender}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Chief Complaint:</span>
                <span className="font-medium text-sky-300">{patientCase.patient.presentingComplaint}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Known Allergies:</span>
                <span className="font-medium text-slate-300">{patientCase.patient.allergies.join(", ")}</span>
              </div>
            </div>
          </div>

          {/* Electronic Resuscitation Event Log */}
          <div className="med-card p-5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Resuscitation Event Log</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500">Live Audit Trail</span>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {resusLog.map((entry, idx) => (
                <div key={idx} className="text-xs p-2 rounded-lg bg-slate-900/60 border border-slate-800/60 space-y-0.5">
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-500">{entry.time}</span>
                    <span className={entry.status === "success" ? "text-emerald-400 font-bold" : "text-amber-400"}>
                      {entry.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-tight">{entry.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 7 Cols: ABCDE Interventions & Clinical Decision Pad */}
        <div className="lg:col-span-7 med-card p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold text-white">
                <ClipboardList className="w-4 h-4 text-emerald-400" />
                <span>ABCDE Clinical Decision Pad</span>
              </div>
              <span className="text-xs text-slate-400">
                {executedActions.length} of {patientCase.availableInterventions.length} interventions ordered
              </span>
            </div>

            {/* Interventions List */}
            <div className="space-y-3 mt-4">
              {patientCase.availableInterventions.map((action) => {
                const isExecuted = executedActions.includes(action.id);

                return (
                  <div
                    key={action.id}
                    className="p-4 rounded-xl transition-all"
                    style={{
                      background: isExecuted ? "rgba(34,197,94,0.06)" : "rgba(255,255,255,0.03)",
                      border: isExecuted
                        ? "1px solid rgba(34,197,94,0.2)"
                        : "1px solid rgba(255,255,255,0.07)",
                    }}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className="flex items-center justify-center w-7 h-7 rounded-lg flex-shrink-0"
                          style={{ background: "rgba(255,255,255,0.06)", color: "#94a3b8" }}
                        >
                          {typeIcon(action.type)}
                        </div>
                        <div className="min-w-0">
                          <div className="text-[13px] font-semibold text-white truncate">
                            {action.name}
                          </div>
                          <div className="text-[11px] font-medium capitalize text-slate-500">
                            {action.type}
                          </div>
                        </div>
                      </div>

                      {!isExecuted ? (
                        <button
                          onClick={() => handleExecuteAction(action.id)}
                          className="flex-shrink-0 px-3.5 py-1.5 rounded-lg text-[12px] font-semibold text-white transition-all shadow-sm"
                          style={{ background: "linear-gradient(135deg, #0ea5e9, #2563eb)" }}
                        >
                          Execute Order
                        </button>
                      ) : (
                        <div className="flex items-center gap-1.5 text-[12px] font-semibold text-emerald-400 flex-shrink-0">
                          <CheckCircle className="w-4 h-4" />
                          <span>Executed</span>
                        </div>
                      )}
                    </div>

                    {/* Educational Feedback & Clinical Reasoning Explanation */}
                    {isExecuted && (
                      <div className="mt-3 pt-3 text-[12px] text-slate-300 leading-relaxed border-t border-slate-800/80 med-fade-in">
                        <span className="font-semibold text-sky-400">Clinical Impact: </span>
                        {action.aiFeedback}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
