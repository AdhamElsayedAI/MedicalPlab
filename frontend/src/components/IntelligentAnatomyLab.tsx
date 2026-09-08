"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import {
  Layers3,
  Stethoscope,
  BookOpen,
  Activity,
  RotateCcw,
  ChevronRight,
  Maximize2,
  Info,
  FileQuestion,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sparkles,
  ArrowRight,
  Award,
} from "lucide-react";
import { ANATOMICAL_SYSTEMS } from "@/lib/demo-data";
import { AnatomicalSystem, OrganHotspot } from "@/lib/types";

interface IntelligentAnatomyLabProps {
  onNavigateToTutor: (query: string) => void;
  onNavigateToQuiz: (mcqId: string) => void;
  onNavigateToSim: () => void;
}

type WorkflowStep = 1 | 2 | 3 | 4;

const WORKFLOW_STEPS: { step: WorkflowStep; label: string; icon: React.ReactNode }[] = [
  { step: 1, label: "Spatial Anatomy", icon: <Layers3 className="w-3.5 h-3.5" /> },
  { step: 2, label: "Clinical Correlation", icon: <Info className="w-3.5 h-3.5" /> },
  { step: 3, label: "Pathophysiology", icon: <Activity className="w-3.5 h-3.5" /> },
  { step: 4, label: "Exam Preparation", icon: <Award className="w-3.5 h-3.5" /> },
];

export const IntelligentAnatomyLab: React.FC<IntelligentAnatomyLabProps> = ({
  onNavigateToTutor,
  onNavigateToQuiz,
  onNavigateToSim,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [selectedSystem, setSelectedSystem] = useState<AnatomicalSystem>(ANATOMICAL_SYSTEMS[0]);
  const [selectedHotspot, setSelectedHotspot] = useState<OrganHotspot | null>(
    ANATOMICAL_SYSTEMS[0].hotspots[0]
  );
  const [activeLayer, setActiveLayer] = useState<"vascular" | "muscular" | "wireframe">("vascular");
  const [isRotating, setIsRotating] = useState(true);
  const [workflowStep, setWorkflowStep] = useState<WorkflowStep>(1);
  const [showVignetteAnswer, setShowVignetteAnswer] = useState(false);

  // References for Three.js animation
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const groupRef = useRef<THREE.Group | null>(null);
  const heartMeshRef = useRef<THREE.Mesh | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight || 520;

    // Scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 4.2);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    rendererRef.current = renderer;
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0x0a1828, 2.5);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x38bdf8, 4, 50);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x3b82f6, 3, 50);
    pointLight2.position.set(-5, -3, 3);
    scene.add(pointLight2);

    const pointLight3 = new THREE.PointLight(0x22d3ee, 1.5, 30);
    pointLight3.position.set(0, -4, 4);
    scene.add(pointLight3);

    // 3D Anatomical Group
    const modelGroup = new THREE.Group();
    groupRef.current = modelGroup;
    scene.add(modelGroup);

    if (selectedSystem.id === "cardiovascular") {
      const heartGeo = new THREE.DodecahedronGeometry(1.2, 3);
      const heartMat = new THREE.MeshStandardMaterial({
        color: 0x1e3a8a,
        roughness: 0.25,
        metalness: 0.8,
        wireframe: activeLayer === "wireframe",
        emissive: 0x0c4a6e,
        emissiveIntensity: 0.6,
      });
      const heartMesh = new THREE.Mesh(heartGeo, heartMat);
      heartMeshRef.current = heartMesh;
      modelGroup.add(heartMesh);

      const aortaCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0, 0.9, 0),
        new THREE.Vector3(0.2, 1.5, 0),
        new THREE.Vector3(-0.4, 1.8, 0.2),
        new THREE.Vector3(-0.7, 1.2, -0.2),
      ]);
      const aortaGeo = new THREE.TubeGeometry(aortaCurve, 32, 0.22, 16, false);
      const aortaMat = new THREE.MeshStandardMaterial({
        color: 0xdc2626,
        roughness: 0.3,
        metalness: 0.7,
        emissive: 0x7f1d1d,
        emissiveIntensity: 0.4,
      });
      modelGroup.add(new THREE.Mesh(aortaGeo, aortaMat));

      const ladCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0.1, 0.8, 0.7),
        new THREE.Vector3(0.3, 0.3, 1.05),
        new THREE.Vector3(0.4, -0.5, 0.95),
        new THREE.Vector3(0.1, -1.0, 0.6),
      ]);
      const ladGeo = new THREE.TubeGeometry(ladCurve, 32, 0.06, 12, false);
      const ladMat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x0ea5e9,
        emissiveIntensity: 0.7,
      });
      modelGroup.add(new THREE.Mesh(ladGeo, ladMat));
    } else {
      const brainGeo = new THREE.TorusKnotGeometry(0.9, 0.32, 128, 32);
      const brainMat = new THREE.MeshStandardMaterial({
        color: 0x2563eb,
        roughness: 0.3,
        metalness: 0.7,
        wireframe: activeLayer === "wireframe",
        emissive: 0x1d4ed8,
        emissiveIntensity: 0.5,
      });
      modelGroup.add(new THREE.Mesh(brainGeo, brainMat));
    }

    // Hotspot markers
    selectedSystem.hotspots.forEach((spot) => {
      const ringGeo = new THREE.RingGeometry(0.08, 0.12, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.set(...spot.position);
      ring.lookAt(camera.position);
      modelGroup.add(ring);
    });

    // Mouse Drag Rotation Logic
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging || !modelGroup) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      modelGroup.rotation.y += deltaX * 0.008;
      modelGroup.rotation.x += deltaY * 0.008;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (isRotating && !isDragging && modelGroup) {
        modelGroup.rotation.y += 0.004;
      }

      if (heartMeshRef.current && selectedSystem.id === "cardiovascular") {
        const scale = 1 + Math.sin(Date.now() * 0.003) * 0.025;
        heartMeshRef.current.scale.set(scale, scale, scale);
      }

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight || 520;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [selectedSystem, activeLayer, isRotating]);

  const handleSelectHotspot = (spot: OrganHotspot) => {
    setSelectedHotspot(spot);
    setShowVignetteAnswer(false);
  };

  return (
    <section
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 med-fade-in"
      aria-label="3D Clinical Anatomy Lab"
    >
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                background: "rgba(139,92,246,0.15)",
                border: "1px solid rgba(139,92,246,0.25)",
              }}
            >
              <Layers3 className="w-5 h-5 text-purple-400" />
            </div>
            <h2 className="section-header">3D Clinical Anatomy Lab</h2>
          </div>
          <p className="section-subtext">
            Step through a 4-phase pedagogical workflow: from spatial landmark identification to clinical exam application.
          </p>
        </div>

        {/* Anatomical System Switcher */}
        <div
          className="flex items-center gap-1 p-1 rounded-xl flex-shrink-0"
          style={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          {ANATOMICAL_SYSTEMS.map((sys) => (
            <button
              key={sys.id}
              onClick={() => {
                setSelectedSystem(sys);
                setSelectedHotspot(sys.hotspots[0]);
                setShowVignetteAnswer(false);
              }}
              className="px-3.5 py-2 rounded-lg text-[13px] font-medium transition-all"
              style={{
                background: selectedSystem.id === sys.id ? "rgba(139,92,246,0.18)" : "transparent",
                color: selectedSystem.id === sys.id ? "#c4b5fd" : "#64748b",
                border:
                  selectedSystem.id === sys.id
                    ? "1px solid rgba(139,92,246,0.25)"
                    : "1px solid transparent",
              }}
            >
              {sys.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Lab Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: 3D Canvas */}
        <div
          className="lg:col-span-7 relative rounded-2xl overflow-hidden flex flex-col justify-between"
          style={{
            background:
              "linear-gradient(160deg, #0d1b2e 0%, #0b1120 60%, #0d1520 100%)",
            border: "1px solid rgba(255,255,255,0.07)",
            minHeight: "540px",
          }}
        >
          {/* Top Canvas Controls */}
          <div className="p-4 z-10 flex items-center justify-between">
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px]"
              style={{
                background: "rgba(11,17,32,0.85)",
                border: "1px solid rgba(255,255,255,0.08)",
                backdropFilter: "blur(8px)",
              }}
            >
              <span className="med-status-dot online" />
              <span className="font-medium text-slate-300">{selectedSystem.clinicalFocus}</span>
            </div>

            {/* Layer Controls */}
            <div
              className="flex items-center gap-1 p-1 rounded-lg"
              style={{
                background: "rgba(11,17,32,0.85)",
                border: "1px solid rgba(255,255,255,0.08)",
                backdropFilter: "blur(8px)",
              }}
            >
              {(["vascular", "muscular", "wireframe"] as const).map((layer) => (
                <button
                  key={layer}
                  onClick={() => setActiveLayer(layer)}
                  className="px-2.5 py-1 rounded text-[11px] font-medium capitalize transition-all"
                  style={{
                    background: activeLayer === layer ? "rgba(139,92,246,0.2)" : "transparent",
                    color: activeLayer === layer ? "#c4b5fd" : "#64748b",
                  }}
                >
                  {layer === "wireframe" ? "Structure" : layer.charAt(0).toUpperCase() + layer.slice(1)}
                </button>
              ))}
              <button
                onClick={() => setIsRotating(!isRotating)}
                className="p-1.5 rounded transition-colors"
                style={{ color: isRotating ? "#a78bfa" : "#475569" }}
                title="Toggle auto-rotation"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* WebGL Canvas Mount */}
          <div ref={mountRef} className="absolute inset-0 z-0 cursor-grab active:cursor-grabbing" />

          {/* Drag hint */}
          <div className="z-10 text-center pb-2 pointer-events-none">
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] text-slate-400"
              style={{ background: "rgba(11,17,32,0.7)", backdropFilter: "blur(6px)" }}
            >
              <Maximize2 className="w-3 h-3" />
              Click &amp; drag 3D model to inspect orientation
            </div>
          </div>

          {/* Hotspot Structure Ribbon */}
          <div className="p-4 z-10" style={{ background: "linear-gradient(to top, rgba(11,17,32,0.9), transparent)" }}>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] text-slate-400 font-medium flex-shrink-0">
                Landmark Pinpoints:
              </span>
              {selectedSystem.hotspots.map((spot) => (
                <button
                  key={spot.id}
                  onClick={() => handleSelectHotspot(spot)}
                  className="px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all"
                  style={{
                    background: selectedHotspot?.id === spot.id ? "#38bdf8" : "rgba(11,17,32,0.85)",
                    color: selectedHotspot?.id === spot.id ? "#0b1120" : "#94a3b8",
                    border: "1px solid",
                    borderColor:
                      selectedHotspot?.id === spot.id ? "#38bdf8" : "rgba(255,255,255,0.08)",
                    backdropFilter: "blur(8px)",
                  }}
                >
                  {spot.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right 5 Cols: 4-Step Clinical Learning Journey */}
        <div className="lg:col-span-5 med-card p-6 flex flex-col justify-between">
          {selectedHotspot ? (
            <div className="flex-1 flex flex-col justify-between space-y-5">
              {/* Header */}
              <div>
                <div className="flex items-start justify-between pb-3 mb-3 border-b border-slate-800">
                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Structure Under Inspection
                    </span>
                    <h3
                      className="text-lg font-bold text-white leading-tight mt-0.5"
                      style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
                    >
                      {selectedHotspot.name}
                    </h3>
                  </div>
                  <span className="med-badge med-badge-primary flex-shrink-0">
                    {selectedHotspot.niceGuidelineRef}
                  </span>
                </div>

                {/* 4-Phase Workflow Stepper */}
                <div className="grid grid-cols-4 gap-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800 mb-4">
                  {WORKFLOW_STEPS.map((ws) => (
                    <button
                      key={ws.step}
                      onClick={() => setWorkflowStep(ws.step)}
                      className={`flex flex-col items-center justify-center py-1.5 px-1 rounded-lg text-[11px] font-medium transition-all ${
                        workflowStep === ws.step
                          ? "bg-sky-500/20 text-sky-300 border border-sky-400/30"
                          : ws.step < workflowStep
                          ? "text-emerald-400"
                          : "text-slate-500 hover:text-slate-300"
                      }`}
                      title={ws.label}
                    >
                      <div className="flex items-center gap-1">
                        <span>{ws.icon}</span>
                        <span className="font-bold">{ws.step}</span>
                      </div>
                      <span className="text-[9px] mt-0.5 truncate max-w-full">
                        {ws.label.split(" ")[0]}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Step 1: Spatial Anatomy */}
                {workflowStep === 1 && (
                  <div className="space-y-3 med-fade-in">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-sky-400">
                      <Layers3 className="w-4 h-4" />
                      <span>Phase 1: Spatial Anatomy &amp; Orientation</span>
                    </div>
                    <p className="text-[13px] text-slate-300 leading-relaxed bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
                      {selectedHotspot.clinicalSignificance}
                    </p>
                    <div className="p-3 rounded-xl bg-sky-950/30 border border-sky-500/20 text-xs text-sky-200">
                      <span className="font-semibold block mb-0.5">Spatial Landmark:</span>
                      Arises from the left main coronary artery in the anterior interventricular sulcus, supplying the anterior left ventricular wall and apex.
                    </div>
                    <button
                      onClick={() => setWorkflowStep(2)}
                      className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <span>Proceed to Clinical Correlation</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Step 2: Clinical Correlation */}
                {workflowStep === 2 && (
                  <div className="space-y-3 med-fade-in">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-purple-400">
                      <Info className="w-4 h-4" />
                      <span>Phase 2: Clinical Presentation &amp; Bedside Signs</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/20 text-xs text-slate-200 space-y-2">
                      <div>
                        <span className="text-[11px] font-semibold text-purple-300 block">Associated Condition:</span>
                        <span className="font-bold text-white text-[13px]">{selectedHotspot.relatedCondition}</span>
                      </div>
                      <p className="text-slate-300 leading-relaxed">
                        Patients typically present with acute crushing retrosternal chest pain, diaphoresis, dyspnea, and radiation to the left arm or jaw.
                      </p>
                    </div>
                    <button
                      onClick={() => setWorkflowStep(3)}
                      className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <span>Proceed to Pathophysiology</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Step 3: Pathophysiology */}
                {workflowStep === 3 && (
                  <div className="space-y-3 med-fade-in">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400">
                      <Activity className="w-4 h-4" />
                      <span>Phase 3: Pathophysiological Mechanism</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/20 text-xs text-slate-200 space-y-2">
                      <p className="leading-relaxed">
                        Atherosclerotic plaque rupture causes acute thrombotic occlusion. Cessation of blood flow leads to transmural ischemia of the anterior myocardium within minutes.
                      </p>
                      <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-amber-300">
                        ECG Hallmark: ST-elevation &gt;2mm in precordial leads V1-V4 with reciprocal inferior depression.
                      </div>
                    </div>
                    <button
                      onClick={() => setWorkflowStep(4)}
                      className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <span>Proceed to Exam Preparation</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Step 4: Exam Preparation */}
                {workflowStep === 4 && (
                  <div className="space-y-3 med-fade-in">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
                      <Award className="w-4 h-4" />
                      <span>Phase 4: High-Yield Exam Preparation (PLAB / UKMLA)</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs space-y-2.5">
                      <div className="flex items-center justify-between text-slate-400 font-semibold text-[11px]">
                        <span>Diagnostic Case Pearl</span>
                        <span className="text-emerald-400">High-Yield</span>
                      </div>
                      <p className="text-slate-200 text-xs leading-relaxed">
                        &quot;A 62-year-old male with 90 minutes of acute crushing chest pain and ST elevations in leads V1-V4. Coronary angiogram is ordered.&quot;
                      </p>

                      {!showVignetteAnswer ? (
                        <button
                          onClick={() => setShowVignetteAnswer(true)}
                          className="text-[11px] font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1"
                        >
                          <HelpCircle className="w-3.5 h-3.5" />
                          <span>Reveal Board Exam Answer</span>
                        </button>
                      ) : (
                        <div className="p-2.5 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs space-y-1">
                          <span className="font-bold block">Correct Diagnosis:</span>
                          <span>Anterior STEMI secondary to Left Anterior Descending (LAD) artery occlusion. Urgent PPCI indicated within 120 minutes per NICE NG185.</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Natural Clinical Actions: Ask AI Tutor & Practice Clinical Question */}
              <div className="space-y-2 pt-4 border-t border-slate-800">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
                  Clinical Action Paths
                </span>

                <button
                  onClick={() => onNavigateToTutor(selectedHotspot.recommendedTutorQuery)}
                  className="w-full flex items-center justify-between p-3 rounded-xl font-bold text-xs text-white transition-all shadow-md"
                  style={{ background: "linear-gradient(135deg, #0ea5e9, #2563eb)" }}
                >
                  <span className="flex items-center gap-2">
                    <Stethoscope className="w-4 h-4" />
                    Ask AI Tutor About This Pathology
                  </span>
                  <ChevronRight className="w-4 h-4" />
                </button>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => onNavigateToQuiz(selectedHotspot.highYieldMcqId)}
                    className="flex items-center justify-center gap-1.5 p-2.5 rounded-xl text-xs font-semibold text-slate-200 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white transition-all"
                  >
                    <FileQuestion className="w-3.5 h-3.5 text-purple-400" />
                    <span>Practice MCQ</span>
                  </button>

                  <button
                    onClick={onNavigateToSim}
                    className="flex items-center justify-center gap-1.5 p-2.5 rounded-xl text-xs font-semibold text-slate-200 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white transition-all"
                  >
                    <Activity className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Simulate Case</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center py-16 text-slate-500">
              <Layers3 className="w-10 h-10 text-slate-700 mb-3" />
              <p className="text-sm">Select an anatomical structure to begin the 4-phase learning journey</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
