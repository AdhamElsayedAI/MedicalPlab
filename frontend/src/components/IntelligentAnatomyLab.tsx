"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import {
  Layers,
  Sparkles,
  Stethoscope,
  GraduationCap,
  Activity,
  Maximize2,
  RotateCcw,
  BookOpen,
  CheckCircle2,
  ArrowRight,
  Eye,
} from "lucide-react";
import { ANATOMICAL_SYSTEMS } from "@/lib/demo-data";
import { AnatomicalSystem, OrganHotspot, NavigationMode } from "@/lib/types";

interface IntelligentAnatomyLabProps {
  onNavigateToTutor: (query: string) => void;
  onNavigateToQuiz: (mcqId: string) => void;
  onNavigateToSim: () => void;
}

export const IntelligentAnatomyLab: React.FC<IntelligentAnatomyLabProps> = ({
  onNavigateToTutor,
  onNavigateToQuiz,
  onNavigateToSim,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [selectedSystem, setSelectedSystem] = useState<AnatomicalSystem>(ANATOMICAL_SYSTEMS[0]);
  const [selectedHotspot, setSelectedHotspot] = useState<OrganHotspot | null>(ANATOMICAL_SYSTEMS[0].hotspots[0]);
  const [activeLayer, setActiveLayer] = useState<"vascular" | "muscular" | "wireframe">("vascular");
  const [isRotating, setIsRotating] = useState(true);

  // References for Three.js animation
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const groupRef = useRef<THREE.Group | null>(null);
  const heartMeshRef = useRef<THREE.Mesh | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight || 550;

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
    const ambientLight = new THREE.AmbientLight(0x0a2540, 2.5);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x00f2fe, 4, 50);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x3b82f6, 3, 50);
    pointLight2.position.set(-5, -3, 3);
    scene.add(pointLight2);

    // 3D Anatomical Group
    const modelGroup = new THREE.Group();
    groupRef.current = modelGroup;
    scene.add(modelGroup);

    // Create Anatomical Organ representation based on selected system
    if (selectedSystem.id === "cardiovascular") {
      // Procedural Cardiac Geometry (Ventricular Body & Atria)
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

      // Aorta Great Vessel Arch
      const aortaCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0, 0.9, 0),
        new THREE.Vector3(0.2, 1.5, 0),
        new THREE.Vector3(-0.4, 1.8, 0.2),
        new THREE.Vector3(-0.7, 1.2, -0.2),
      ]);
      const aortaGeo = new THREE.TubeGeometry(aortaCurve, 32, 0.22, 16, false);
      const aortaMat = new THREE.MeshStandardMaterial({
        color: 0xff3b30,
        roughness: 0.3,
        metalness: 0.7,
        emissive: 0x880808,
        emissiveIntensity: 0.5,
      });
      const aortaMesh = new THREE.Mesh(aortaGeo, aortaMat);
      modelGroup.add(aortaMesh);

      // Coronary Arterial Branches (LAD & LCx)
      const ladCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0.1, 0.8, 0.7),
        new THREE.Vector3(0.3, 0.3, 1.05),
        new THREE.Vector3(0.4, -0.5, 0.95),
        new THREE.Vector3(0.1, -1.0, 0.6),
      ]);
      const ladGeo = new THREE.TubeGeometry(ladCurve, 32, 0.06, 12, false);
      const ladMat = new THREE.MeshStandardMaterial({
        color: 0x00f2fe,
        emissive: 0x00f2fe,
        emissiveIntensity: 0.9,
      });
      const ladMesh = new THREE.Mesh(ladGeo, ladMat);
      modelGroup.add(ladMesh);
    } else {
      // Neurological / Pulmonary Procedural Geometry
      const brainGeo = new THREE.TorusKnotGeometry(0.9, 0.32, 128, 32);
      const brainMat = new THREE.MeshStandardMaterial({
        color: 0x2563eb,
        roughness: 0.3,
        metalness: 0.7,
        wireframe: activeLayer === "wireframe",
        emissive: 0x1d4ed8,
        emissiveIntensity: 0.5,
      });
      const brainMesh = new THREE.Mesh(brainGeo, brainMat);
      modelGroup.add(brainMesh);
    }

    // Add Interactive Hotspot Rings in 3D Space
    selectedSystem.hotspots.forEach((spot) => {
      const ringGeo = new THREE.RingGeometry(0.08, 0.12, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x00f2fe,
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
      if (!isDragging || !groupRef.current) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      groupRef.current.rotation.y += deltaX * 0.007;
      groupRef.current.rotation.x += deltaY * 0.007;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    // Animation Loop (Heart contraction pulse & subtle rotation)
    let clock = new THREE.Clock();
    let animId: number;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Subtle heartbeat systolic/diastolic contraction
      if (heartMeshRef.current && selectedSystem.id === "cardiovascular") {
        const pulse = 1.0 + 0.04 * Math.sin(elapsedTime * 4.5) * Math.sin(elapsedTime * 4.5);
        heartMeshRef.current.scale.set(pulse, pulse, pulse);
      }

      // Continuous subtle idle rotation
      if (isRotating && !isDragging && modelGroup) {
        modelGroup.rotation.y += 0.004;
      }

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container || !renderer) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight || 550;
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
    };
  }, [selectedSystem, activeLayer, isRotating]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header Bar with System Selectors */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded bg-cyan-950 text-cyan-400 border border-cyan-500/30">
              <Layers className="w-4 h-4" />
            </span>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
              INTELLIGENT 3D ANATOMY LABORATORY
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            CLICK ANY ANATOMICAL STRUCTURE TO RETRIEVE EVIDENCE, CONSULT AI TUTOR, AND TEST MCQS
          </p>
        </div>

        {/* Organ System Switcher */}
        <div className="flex items-center gap-2 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          {ANATOMICAL_SYSTEMS.map((sys) => (
            <button
              key={sys.id}
              onClick={() => {
                setSelectedSystem(sys);
                setSelectedHotspot(sys.hotspots[0]);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedSystem.id === sys.id
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(0,242,254,0.25)]"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {sys.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main 3D Lab Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 3D WebGL Canvas */}
        <div className="lg:col-span-2 cyber-card rounded-2xl p-4 relative overflow-hidden border border-cyan-500/20 min-h-[500px] flex flex-col justify-between">
          {/* Top Canvas Controls HUD */}
          <div className="relative z-10 flex items-center justify-between gap-3 text-xs font-mono">
            <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-300 font-semibold">{selectedSystem.clinicalFocus}</span>
            </div>

            <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setActiveLayer("vascular")}
                className={`px-2 py-1 rounded text-[11px] ${
                  activeLayer === "vascular" ? "bg-cyan-500/30 text-cyan-300 font-bold" : "text-slate-400"
                }`}
              >
                Vascular
              </button>
              <button
                onClick={() => setActiveLayer("muscular")}
                className={`px-2 py-1 rounded text-[11px] ${
                  activeLayer === "muscular" ? "bg-cyan-500/30 text-cyan-300 font-bold" : "text-slate-400"
                }`}
              >
                Muscular
              </button>
              <button
                onClick={() => setActiveLayer("wireframe")}
                className={`px-2 py-1 rounded text-[11px] ${
                  activeLayer === "wireframe" ? "bg-cyan-500/30 text-cyan-300 font-bold" : "text-slate-400"
                }`}
              >
                Holo Grid
              </button>
              <button
                onClick={() => setIsRotating(!isRotating)}
                className={`p-1.5 rounded ${isRotating ? "text-cyan-400" : "text-slate-500"}`}
                title="Toggle Auto Rotation"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* WebGL Canvas Container */}
          <div ref={mountRef} className="absolute inset-0 z-0 cursor-grab active:cursor-grabbing" />

          {/* Bottom Hotspots Ribbon */}
          <div className="relative z-10 pt-4 flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400 mr-2 flex items-center gap-1">
              <Eye className="w-3.5 h-3.5 text-cyan-400" />
              HOTSPOTS:
            </span>
            {selectedSystem.hotspots.map((spot) => (
              <button
                key={spot.id}
                onClick={() => setSelectedHotspot(spot)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  selectedHotspot?.id === spot.id
                    ? "bg-cyan-500 text-slate-950 font-bold shadow-[0_0_15px_rgba(0,242,254,0.4)]"
                    : "bg-slate-900/80 text-slate-300 border border-slate-700 hover:border-cyan-500/40"
                }`}
              >
                {spot.name}
              </button>
            ))}
          </div>
        </div>

        {/* Right Col: Intelligent Hotspot AI Connected Drawer */}
        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/30 flex flex-col justify-between space-y-4 bg-slate-950/80">
          {selectedHotspot ? (
            <>
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <span className="text-[10px] font-mono text-cyan-400 font-bold tracking-widest uppercase bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-500/30">
                    ANATOMICAL TARGET
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    {selectedHotspot.niceGuidelineRef}
                  </span>
                </div>

                <h3 className="mt-3 text-lg font-black text-white">
                  {selectedHotspot.name}
                </h3>

                <div className="mt-3 p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                  <span className="text-[11px] font-mono text-cyan-300 font-bold block">
                    CLINICAL SIGNIFICANCE:
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedHotspot.clinicalSignificance}
                  </p>
                </div>

                <div className="mt-3 p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 space-y-1">
                  <span className="text-[11px] font-mono text-rose-400 font-bold block">
                    ASSOCIATED CLINICAL PATHOLOGY:
                  </span>
                  <p className="text-xs text-slate-300 font-medium">
                    {selectedHotspot.relatedCondition}
                  </p>
                </div>
              </div>

              {/* Action Buttons Connecting to AI Stages */}
              <div className="space-y-2.5 pt-4 border-t border-slate-800">
                <button
                  onClick={() => onNavigateToTutor(selectedHotspot.recommendedTutorQuery)}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/35 transition-all hover:scale-[1.01]"
                >
                  <span className="flex items-center gap-2">
                    <Stethoscope className="w-4 h-4" />
                    <span>Consult AI Tutor on this Topic</span>
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  onClick={() => onNavigateToQuiz(selectedHotspot.highYieldMcqId)}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 hover:border-purple-500/50 text-xs font-semibold transition-all"
                >
                  <span className="flex items-center gap-2">
                    <GraduationCap className="w-4 h-4 text-purple-400" />
                    <span>Generate Target MCQ (Stage-C)</span>
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-400" />
                </button>

                <button
                  onClick={onNavigateToSim}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 hover:border-emerald-500/50 text-xs font-semibold transition-all"
                >
                  <span className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    <span>Launch Emergency Sim (Stage-F)</span>
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-400" />
                </button>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center py-12 text-slate-500">
              <Sparkles className="w-8 h-8 text-cyan-400 mb-2 animate-bounce" />
              <p className="text-xs">Click any anatomical marker to load clinical intelligence.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
