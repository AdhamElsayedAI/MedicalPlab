'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnatomySceneController } from '@/lib/anatomy/sceneController';
import {
  AnatomyManifest,
  AnatomySession,
  AnatomyStructure,
  ChallengeResult,
  InteractionRequest,
  SceneAction,
} from '@/lib/anatomy/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AnatomyPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<AnatomySceneController | null>(null);

  // Core domain state
  const [manifest, setManifest] = useState<AnatomyManifest | null>(null);
  const [session, setSession] = useState<AnatomySession | null>(null);
  const [selectedStructure, setSelectedStructure] = useState<AnatomyStructure | null>(null);
  const [selectedMeshName, setSelectedMeshName] = useState<string>('');
  const [tutorMessage, setTutorMessage] = useState<string>('Initializing MedicalPlab AI Anatomy Tutor...');
  const [actionHistory, setActionHistory] = useState<SceneAction[]>([]);
  const [interactionReq, setInteractionReq] = useState<InteractionRequest | null>(null);

  // Telemetry & UI
  const [capsuleOpacity, setCapsuleOpacity] = useState<number>(0.35);
  const [perfStats, setPerfStats] = useState({
    loadTimeMs: 0,
    meshCount: 0,
    triangleCount: 0,
    vertexCount: 0,
    fps: 60,
  });
  const [statusMessage, setStatusMessage] = useState<string>('Loading verified HRA anatomy assets...');
  const [learnerInput, setLearnerInput] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [challengeOutcome, setChallengeOutcome] = useState<{
    evaluated: boolean;
    isCorrect: boolean;
    feedback: string;
  } | null>(null);

  // 1. Fetch manifest and initialize session on mount
  useEffect(() => {
    let isMounted = true;

    async function initAnatomy() {
      try {
        // Fetch manifest
        const manifestRes = await fetch(`${API_BASE}/api/v1/anatomy/manifest`);
        if (!manifestRes.ok) {
          throw new Error(`Manifest API returned ${manifestRes.status}`);
        }
        const manifestData: AnatomyManifest = await manifestRes.json();
        if (!isMounted) return;
        setManifest(manifestData);

        // Fetch or start session
        const learnerId = 'student_plab_demo';
        const startRes = await fetch(`${API_BASE}/api/v1/anatomy/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            learner_id: learnerId,
            learning_objective: 'RENAL_BLOOD_FLOW_AND_HILUM',
          }),
        });

        if (!startRes.ok) {
          throw new Error(`Session start API returned ${startRes.status}`);
        }
        const sessionData = await startRes.json();
        if (!isMounted) return;

        setSession(sessionData.session);
        setTutorMessage(sessionData.initial_tutor_response.tutor_message);
        setActionHistory(sessionData.initial_tutor_response.scene_actions || []);
        setInteractionReq(sessionData.initial_tutor_response.interaction_request || null);
        setStatusMessage('AI Anatomy Tutor ready. Interact with the 3D model.');

        // Initialize 3D Scene Controller
        if (containerRef.current) {
          const controller = new AnatomySceneController({
            container: containerRef.current,
            structures: manifestData.structures,
            onSelectStructure: (structureId, meshName) => {
              handleMeshClick(structureId, meshName, manifestData.structures, sessionData.session);
            },
            onLoadComplete: (stats) => {
              setPerfStats((p) => ({ ...p, ...stats }));
              setStatusMessage('All 3 verified HRA renal GLBs rendered in CCF space.');
              // Execute initial scene actions
              for (const act of sessionData.initial_tutor_response.scene_actions || []) {
                controller.executeAction(act);
              }
            },
            onError: (err) => {
              setStatusMessage(err);
            },
          });
          controllerRef.current = controller;
        }
      } catch (err) {
        console.error('Failed to initialize anatomy system:', err);
        setStatusMessage('Anatomy service unavailable or feature disabled.');
      }
    }

    initAnatomy();

    return () => {
      isMounted = false;
      if (controllerRef.current) {
        controllerRef.current.dispose();
      }
    };
  }, []);

  // 2. Handle physical mesh selection in 3D viewport
  const handleMeshClick = async (
    structureId: string,
    meshName: string,
    structuresList: AnatomyStructure[],
    currentSession: AnatomySession | null
  ) => {
    setSelectedMeshName(meshName);
    const matched = structuresList.find((s) => s.structure_id === structureId);
    setSelectedStructure(matched || null);

    if (!controllerRef.current) return;
    controllerRef.current.highlightStructure(structureId);

    // If active challenge, don't automatically trigger guided socratic turn
    if (currentSession?.challenge_state === 'ACTIVE') {
      return;
    }

    // Call backend interaction endpoint
    if (currentSession) {
      try {
        setIsSubmitting(true);
        const res = await fetch(`${API_BASE}/api/v1/anatomy/session/${currentSession.session_id}/interact`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            learner_id: currentSession.learner_id,
            selected_structure_id: structureId,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          setSession(data.session);
          setTutorMessage(data.tutor_response.tutor_message);
          setActionHistory((prev) => [...prev, ...(data.tutor_response.scene_actions || [])]);
          setInteractionReq(data.tutor_response.interaction_request || null);

          // Execute returned scene actions deterministically
          for (const act of data.tutor_response.scene_actions || []) {
            controllerRef.current.executeAction(act);
          }
        }
      } catch (e) {
        console.error('Interaction failed:', e);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  // 3. Handle natural language prompt from learner
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!learnerInput.trim() || !session || isSubmitting) return;

    const query = learnerInput.trim();
    setLearnerInput('');
    setIsSubmitting(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/anatomy/session/${session.session_id}/interact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: session.learner_id,
          message: query,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSession(data.session);
        setTutorMessage(data.tutor_response.tutor_message);
        setActionHistory((prev) => [...prev, ...(data.tutor_response.scene_actions || [])]);
        setInteractionReq(data.tutor_response.interaction_request || null);

        // Execute actions deterministically
        if (controllerRef.current) {
          for (const act of data.tutor_response.scene_actions || []) {
            controllerRef.current.executeAction(act);
          }
        }
      }
    } catch (err) {
      console.error('Send message failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 4. Handle Independent 3D Challenge Submission
  const handleSubmitChallenge = async () => {
    if (!session || !selectedStructure || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/anatomy/session/${session.session_id}/challenge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          learner_id: session.learner_id,
          selected_structure_id: selectedStructure.structure_id,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSession(data.session);
        setChallengeOutcome({
          evaluated: true,
          isCorrect: data.is_correct,
          feedback: data.tutor_feedback,
        });

        // Execute challenge result scene actions
        if (controllerRef.current) {
          for (const act of data.scene_actions || []) {
            controllerRef.current.executeAction(act);
          }
        }
      }
    } catch (err) {
      console.error('Challenge submission failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 5. Capsule opacity adjustment
  const handleOpacityChange = (opacity: number) => {
    setCapsuleOpacity(opacity);
    if (controllerRef.current) {
      controllerRef.current.setStructureOpacity('kidney_capsule_left', opacity);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-[#0a0d14] text-slate-100 font-sans select-none overflow-hidden">
      {/* Top Application Bar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-[#0e131f] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-3.5 h-3.5 rounded-full bg-cyan-400 animate-pulse" />
          <div>
            <h1 className="text-base font-semibold tracking-wide text-white">
              MedicalPlab Generative 3D Anatomy Lab
            </h1>
            <div className="text-[11px] text-slate-400">
              Renal Module &bull; Verified HuBMAP HRA Assets &bull; Structured AI Tutor
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
          <span className="px-2.5 py-1 bg-slate-900 rounded border border-slate-800">
            FPS: <strong className="text-emerald-400">{perfStats.fps}</strong>
          </span>
          <span className="px-2.5 py-1 bg-slate-900 rounded border border-slate-800">
            Load: <strong className="text-cyan-400">{perfStats.loadTimeMs}ms</strong>
          </span>
          <span className="px-2.5 py-1 bg-slate-900 rounded border border-slate-800">
            Triangles: <strong className="text-amber-400">{perfStats.triangleCount.toLocaleString()}</strong>
          </span>
        </div>
      </header>

      {/* Feature Disabled Notice Banner */}
      {statusMessage.toLowerCase().includes('disabled') && (
        <div className="bg-amber-950/80 border-b border-amber-800 px-4 py-2.5 text-xs text-amber-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-amber-400">FEATURE FLAG DISABLED:</span>
            <span>MedicalPlab 3D Anatomy Engine is currently disabled (MEDICALPLAB_ANATOMY_3D_ENABLED=false). Set environment variable to true to enable live sessions.</span>
          </div>
        </div>
      )}

      {/* Main Workspace (Split View) */}
      <div className="flex flex-1 relative overflow-hidden">
        {/* Left: 3D Viewport */}
        <div className="flex-1 h-full relative flex flex-col">
          {/* Status Overlay */}
          <div className="absolute top-4 left-4 z-10 px-4 py-2 bg-slate-900/85 backdrop-blur-md rounded-lg border border-slate-800 text-xs text-slate-300 pointer-events-none flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span id="anatomy-viewport-status">{statusMessage}</span>
          </div>

          {/* Quick HUD Navigation */}
          <div className="absolute bottom-4 left-4 z-10 px-3 py-2 bg-slate-900/85 backdrop-blur-md rounded border border-slate-800 text-[11px] text-slate-400 pointer-events-none space-y-0.5">
            <div>&bull; <strong>Left Click + Drag</strong>: Orbit / Rotate scene</div>
            <div>&bull; <strong>Scroll Wheel</strong>: Zoom in / out</div>
            <div>&bull; <strong>Click Structure</strong>: Physical 3D raycast selection</div>
          </div>

          {/* Layer Opacity Slider Float */}
          <div className="absolute top-4 right-4 z-10 p-3 bg-slate-900/85 backdrop-blur-md rounded-lg border border-slate-800 text-xs text-slate-300 w-64 shadow-xl">
            <div className="flex justify-between text-[11px] mb-1 font-medium">
              <span>Kidney Capsule (X-Ray)</span>
              <span className="font-mono text-cyan-400">{Math.round(capsuleOpacity * 100)}%</span>
            </div>
            <input
              id="slider-capsule-opacity"
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={capsuleOpacity}
              onChange={(e) => handleOpacityChange(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-slate-500 mt-1">
              <span>Internal Only</span>
              <span>Translucent</span>
              <span>Opaque</span>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 flex gap-1.5">
              <button
                id="btn-reset-scene"
                onClick={() => controllerRef.current?.resetScene()}
                className="flex-1 py-1 text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
              >
                Reset Camera
              </button>
              <button
                id="btn-isolate-selection"
                onClick={() => {
                  if (selectedStructure && controllerRef.current) {
                    controllerRef.current.isolateStructure(selectedStructure.structure_id);
                  }
                }}
                disabled={!selectedStructure}
                className="flex-1 py-1 text-[10px] bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 rounded border border-slate-700 transition"
              >
                Isolate
              </button>
            </div>
          </div>

          {/* Three.js Canvas Container */}
          <div ref={containerRef} className="flex-1 h-full w-full cursor-grab active:cursor-grabbing" />
        </div>

        {/* Right: Structured AI Anatomy Tutor Panel */}
        <aside className="w-96 bg-[#0e131f] border-l border-slate-800 flex flex-col p-4 gap-3.5 overflow-y-auto shrink-0 text-xs">
          {/* Learning Objective Card */}
          <div className="p-3 rounded-lg bg-cyan-950/40 border border-cyan-800/60">
            <div className="flex items-center justify-between text-[10px] font-bold text-cyan-400 uppercase tracking-wider mb-1">
              <span>Current Lesson Objective</span>
              <span className="px-1.5 py-0.5 rounded bg-cyan-900/60 text-cyan-300 font-mono">PLAB-RENAL-01</span>
            </div>
            <div className="text-xs font-semibold text-slate-200">
              Renal Blood Flow &amp; Hilum Orientation (V-A-P)
            </div>
          </div>

          {/* AI Tutor Dialogue Box */}
          <div className="p-4 rounded-lg bg-slate-900/95 border border-slate-800 flex flex-col gap-2.5 shadow-lg">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-[11px] font-bold text-cyan-300 uppercase tracking-wider">
                AI Anatomy Tutor
              </span>
            </div>
            <div className="text-slate-200 text-xs leading-relaxed" id="tutor-dialogue-message">
              {tutorMessage}
            </div>

            {interactionReq && (
              <div className="mt-2 p-2.5 rounded bg-amber-950/40 border border-amber-800/60 text-amber-200 text-[11px] flex items-start gap-2">
                <span className="text-amber-400 font-bold">&bull;</span>
                <div>
                  <strong>Interactive Task:</strong> {interactionReq.prompt}
                </div>
              </div>
            )}
          </div>

          {/* Physical 3D Selection Inspector */}
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 flex flex-col gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Physical 3D Selection
            </span>
            {selectedStructure ? (
              <div className="space-y-2 mt-0.5">
                <div>
                  <div className="text-sm font-bold text-cyan-300" id="selected-structure-display">
                    {selectedStructure.display_name}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    Mesh: {selectedMeshName || selectedStructure.mesh_node_names[0]}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold text-slate-500">Ontology:</span>
                  <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono text-[11px]">
                    {selectedStructure.ontology_id}
                  </span>
                </div>

                {selectedStructure.relationships && (
                  <div className="pt-1.5 border-t border-slate-800">
                    <div className="text-[10px] font-bold text-slate-400 uppercase mb-1">Grounded Relationships:</div>
                    <ul className="space-y-1">
                      {selectedStructure.relationships.map((rel, i) => (
                        <li key={i} className="text-[10px] text-slate-300 font-mono">
                          <span className="text-amber-400">{rel.type}</span> &rarr; {rel.target}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-slate-500 italic py-2 text-center text-[11px]">
                Click any part of the 3D model (capsule, artery, vein, pelvis) to inspect.
              </div>
            )}
          </div>

          {/* Independent 3D Identification Challenge */}
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Independent 3D Challenge
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800/60 font-mono">
                Deterministic Scoring
              </span>
            </div>

            <div className="text-slate-300 text-[11px] leading-relaxed">
              <strong>Question:</strong> Identify the vessel that branches from the abdominal aorta to supply oxygenated blood to the kidney.
            </div>

            <div className="flex items-center justify-between text-[11px] p-2 bg-slate-950 rounded border border-slate-800">
              <span className="text-slate-400">Your 3D Selection:</span>
              <span className="font-semibold text-cyan-300">
                {selectedStructure ? selectedStructure.display_name : 'None (Click 3D Mesh)'}
              </span>
            </div>

            <button
              id="btn-submit-challenge"
              onClick={handleSubmitChallenge}
              disabled={!selectedStructure || isSubmitting}
              className="w-full py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-40 font-semibold text-white rounded transition text-xs shadow-md"
            >
              Submit 3D Selection for Evaluation
            </button>

            {challengeOutcome && (
              <div
                id="challenge-result-banner"
                className={`p-2.5 rounded text-[11px] border ${
                  challengeOutcome.isCorrect
                    ? 'bg-emerald-950/60 border-emerald-700 text-emerald-200'
                    : 'bg-rose-950/60 border-rose-700 text-rose-200'
                }`}
              >
                <div className="font-bold mb-1">
                  {challengeOutcome.isCorrect ? '✓ Evaluation: CORRECT' : '✗ Evaluation: INCORRECT'}
                </div>
                <div>{challengeOutcome.feedback}</div>
              </div>
            )}
          </div>

          {/* Learner Interaction Form */}
          <form onSubmit={handleSendMessage} className="mt-auto flex gap-2 pt-2 border-t border-slate-800">
            <input
              type="text"
              placeholder="Ask tutor e.g. 'Teach me renal blood flow'..."
              value={learnerInput}
              onChange={(e) => setLearnerInput(e.target.value)}
              className="flex-1 px-3 py-2 bg-slate-950 rounded border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              disabled={isSubmitting || !learnerInput.trim()}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-cyan-400 rounded font-medium text-xs border border-slate-700 transition"
            >
              Send
            </button>
          </form>
        </aside>
      </div>

      {/* Bottom Attribution Bar */}
      <footer className="px-6 py-2 border-t border-slate-800 bg-[#0e131f] flex items-center justify-between text-[11px] text-slate-400 shrink-0">
        <div>
          <span>Selected: </span>
          <strong className="text-slate-200">
            {selectedStructure ? selectedStructure.display_name : 'No structure active'}
          </strong>
          {selectedStructure && (
            <span className="ml-2 font-mono text-cyan-400 text-[10px]">({selectedStructure.ontology_id})</span>
          )}
        </div>

        <div className="flex items-center gap-3 text-[10px]">
          <span>Anatomy Geometry:</span>
          <a
            href="https://humanatlas.io/3d-reference-library"
            target="_blank"
            rel="noreferrer"
            className="text-cyan-400 hover:underline"
          >
            HuBMAP Human Reference Atlas (HRA) CCF &bull; CC BY 4.0
          </a>
        </div>
      </footer>
    </div>
  );
}
