'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  AnatomyManifest,
  AnatomySession,
  AnatomyStructure,
  InteractionRequest,
  SceneAction,
} from '@/lib/anatomy/types';
import {
  AnatomyViewport,
  ProjectedAnchor,
  ViewportPerformanceStats,
} from './scene/AnatomyViewport';
import { CameraPresetName } from './scene/cameraPresets';
import { SurfacePresentationMode } from './scene/pickingPolicy';
import {
  LearningMode,
  determineInitialLearningMode,
} from './adapters/anatomyPresentationAdapter';
import { useReducedMotion } from './hooks/useReducedMotion';
import { useDemoWalkthrough } from './hooks/useDemoWalkthrough';

import { AnatomyHeader } from './components/AnatomyHeader';
import { ViewToolbar } from './components/ViewToolbar';
import { LearningRail } from './components/LearningRail';
import { ProjectedLabel } from './components/ProjectedLabel';
import { SourcesModal } from './components/SourcesModal';
import { DemoControls } from './components/DemoControls';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function AnatomyLabClient() {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<AnatomyViewport | null>(null);

  // Core domain state
  const [manifest, setManifest] = useState<AnatomyManifest | null>(null);
  const [session, setSession] = useState<AnatomySession | null>(null);
  const [selectedStructure, setSelectedStructure] = useState<AnatomyStructure | null>(null);
  const [tutorMessage, setTutorMessage] = useState<string>('Welcome to the Renal Anatomy Lab. Explore the 3D model or follow guided instructions.');
  const [interactionReq, setInteractionReq] = useState<InteractionRequest | null>(null);
  const [historyMessages, setHistoryMessages] = useState<Array<{ role: 'tutor' | 'learner'; text: string }>>([]);

  // UI & Viewport presentation state
  const [currentMode, setCurrentMode] = useState<LearningMode>('EXPLORE');
  const [currentPreset, setCurrentPreset] = useState<CameraPresetName>('KIDNEY_OVERVIEW');
  const [surfaceMode, setSurfaceMode] = useState<SurfacePresentationMode>('SURFACE');
  const [isIsolated, setIsIsolated] = useState(false);
  const [projectedAnchor, setProjectedAnchor] = useState<ProjectedAnchor | null>(null);
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string>('Loading verified HRA anatomy assets...');
  const [isBackendAvailable, setIsBackendAvailable] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [debugMode, setDebugMode] = useState(false);

  // Challenge Outcome
  const [challengeOutcome, setChallengeOutcome] = useState<{
    evaluated: boolean;
    isCorrect: boolean;
    feedback: string;
  } | null>(null);

  // Telemetry (hidden by default unless debugMode is true)
  const [perfStats, setPerfStats] = useState<ViewportPerformanceStats>({
    fps: 60,
    loadTimeMs: 0,
    meshCount: 0,
    triangleCount: 0,
    vertexCount: 0,
  });

  const reducedMotion = useReducedMotion();

  // Check ?debug=1 in URL
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      setDebugMode(params.get('debug') === '1');
    }
  }, []);

  // Handler for structure selection from 3D viewport or buttons
  const handleSelectStructure = useCallback(
    async (structureId: string | null, meshName?: string) => {
      if (!structureId) {
        setSelectedStructure(null);
        if (viewportRef.current) {
          viewportRef.current.selectStructure(null);
        }
        return;
      }

      const struct = manifest?.structures.find((s) => s.structure_id === structureId) || null;
      setSelectedStructure(struct);

      if (viewportRef.current) {
        viewportRef.current.selectStructure(structureId);
      }

      // If in GUIDED_LESSON mode and session active (and not challenge), trigger tutor interaction
      if (currentMode === 'GUIDED_LESSON' && session && session.challenge_state !== 'ACTIVE') {
        try {
          setIsSubmitting(true);
          const res = await fetch(`${API_BASE}/api/v1/anatomy/session/${session.session_id}/interact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              learner_id: session.learner_id,
              selected_structure_id: structureId,
            }),
          });
          if (res.ok) {
            const data = await res.json();
            setSession(data.session);
            setTutorMessage(data.tutor_response.tutor_message);
            setInteractionReq(data.tutor_response.interaction_request || null);
            setHistoryMessages((prev) => [
              ...prev,
              { role: 'learner', text: `Selected ${struct?.display_name || structureId}` },
              { role: 'tutor', text: data.tutor_response.tutor_message },
            ]);

            // Execute returned scene actions deterministically
            if (viewportRef.current) {
              for (const act of data.tutor_response.scene_actions || []) {
                viewportRef.current.executeAction(act);
              }
            }
          }
        } catch (e) {
          console.error('Anatomy interaction failed:', e);
        } finally {
          setIsSubmitting(false);
        }
      }
    },
    [manifest, session, currentMode]
  );

  // Camera presets
  const handleSelectPreset = useCallback((preset: CameraPresetName) => {
    setCurrentPreset(preset);
    if (preset === 'INTERNAL_CUTAWAY') {
      setSurfaceMode('CUTAWAY');
      if (viewportRef.current) {
        viewportRef.current.setSurfaceMode('CUTAWAY');
      }
    } else {
      if (viewportRef.current) {
        viewportRef.current.applyCameraPreset(preset, true);
      }
    }
  }, []);

  // Surface mode
  const handleSetSurfaceMode = useCallback((mode: SurfacePresentationMode) => {
    setSurfaceMode(mode);
    if (mode === 'CUTAWAY' || mode === 'REVEAL') {
      setCurrentPreset('INTERNAL_CUTAWAY');
    } else if (mode === 'SURFACE') {
      setCurrentPreset('KIDNEY_OVERVIEW');
    }
    if (viewportRef.current) {
      viewportRef.current.setSurfaceMode(mode);
    }
  }, []);

  // Toggle Isolation
  const handleToggleIsolate = useCallback(() => {
    if (!selectedStructure) return;
    const nextState = !isIsolated;
    setIsIsolated(nextState);
    if (viewportRef.current) {
      viewportRef.current.isolateStructure(nextState ? selectedStructure.structure_id : null);
    }
  }, [isIsolated, selectedStructure]);

  // Home Camera Reset
  const handleResetCamera = useCallback(() => {
    if (viewportRef.current) {
      viewportRef.current.applyCameraPreset('KIDNEY_OVERVIEW', true);
      setCurrentPreset('KIDNEY_OVERVIEW');
    }
  }, []);

  // Reset View (camera + surface + isolation)
  const handleResetView = useCallback(() => {
    setIsIsolated(false);
    setSurfaceMode('SURFACE');
    setCurrentPreset('KIDNEY_OVERVIEW');
    if (viewportRef.current) {
      viewportRef.current.resetScene();
    }
  }, []);

  // Synchronize guided internal pathway mode when in GUIDED_LESSON and CUTAWAY
  useEffect(() => {
    if (!viewportRef.current) return;
    const isGuidedCutaway = currentMode === 'GUIDED_LESSON' && surfaceMode === 'CUTAWAY';
    viewportRef.current.setGuidedPathwayMode(isGuidedCutaway, 'f');
  }, [currentMode, surfaceMode]);

  // Focus structure
  const handleFocusStructure = useCallback((structureId: string) => {
    if (viewportRef.current) {
      viewportRef.current.focusStructure(structureId);
    }
  }, []);

  // Ask Tutor custom prompt
  const handleAskTutor = useCallback(
    async (prompt: string) => {
      if (!session || !prompt.trim() || isSubmitting) return;

      setIsSubmitting(true);
      setHistoryMessages((prev) => [...prev, { role: 'learner', text: prompt }]);

      try {
        const res = await fetch(`${API_BASE}/api/v1/anatomy/session/${session.session_id}/interact`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            learner_id: session.learner_id,
            message: prompt,
          }),
        });

        if (res.ok) {
          const data = await res.json();
          setSession(data.session);
          setTutorMessage(data.tutor_response.tutor_message);
          setInteractionReq(data.tutor_response.interaction_request || null);
          setHistoryMessages((prev) => [
            ...prev,
            { role: 'tutor', text: data.tutor_response.tutor_message },
          ]);

          if (viewportRef.current) {
            for (const act of data.tutor_response.scene_actions || []) {
              viewportRef.current.executeAction(act);
            }
          }
        }
      } catch (err) {
        console.error('Ask tutor failed:', err);
      } finally {
        setIsSubmitting(false);
      }
    },
    [session, isSubmitting]
  );

  // Submit Challenge
  const handleSubmitChallenge = useCallback(async () => {
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

        if (viewportRef.current) {
          for (const act of data.scene_actions || []) {
            viewportRef.current.executeAction(act);
          }
        }
      }
    } catch (err) {
      console.error('Challenge submission failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  }, [session, selectedStructure, isSubmitting]);

  // Demo Walkthrough Integration
  const {
    isDemoActive,
    isDemoPaused,
    currentStep: demoStep,
    currentStepIndex: demoStepIndex,
    totalSteps: demoTotalSteps,
    startWalkthrough,
    stopWalkthrough,
    pauseWalkthrough,
    resumeWalkthrough,
    executeStep: demoExecuteStep,
  } = useDemoWalkthrough({
    onApplyCamera: handleSelectPreset,
    onSetSurfaceMode: handleSetSurfaceMode,
    onSelectStructure: (sid) => handleSelectStructure(sid),
    onSetLearningMode: (mode) => setCurrentMode(mode),
  });

  // Toggle Demo
  const handleToggleDemo = useCallback(() => {
    if (isDemoActive) {
      stopWalkthrough();
      handleResetView();
    } else {
      startWalkthrough();
    }
  }, [isDemoActive, startWalkthrough, stopWalkthrough, handleResetView]);

  // 1. Fetch manifest & initialize session on mount
  useEffect(() => {
    let isMounted = true;

    async function initAnatomy() {
      try {
        setIsLoading(true);

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
        let sessionData: any = null;
        try {
          const startRes = await fetch(`${API_BASE}/api/v1/anatomy/session/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              learner_id: learnerId,
              learning_objective: 'RENAL_BLOOD_FLOW_AND_HILUM',
            }),
          });
          if (startRes.ok) {
            sessionData = await startRes.json();
            if (isMounted && sessionData.session) {
              setSession(sessionData.session);
              setTutorMessage(sessionData.initial_tutor_response.tutor_message);
              setInteractionReq(sessionData.initial_tutor_response.interaction_request || null);
              setHistoryMessages([
                { role: 'tutor', text: sessionData.initial_tutor_response.tutor_message },
              ]);
              const initialMode = determineInitialLearningMode(sessionData.session);
              setCurrentMode(initialMode);
            }
          } else {
            setIsBackendAvailable(false);
          }
        } catch (e) {
          console.warn('Backend session unavailable; fallback to free exploration', e);
          setIsBackendAvailable(false);
        }

        // Initialize 3D Viewport
        if (containerRef.current) {
          const viewport = new AnatomyViewport({
            container: containerRef.current,
            structures: manifestData.structures,
            reducedMotion,
            onSelectStructure: (structureId, meshName) => {
              // Any user click on 3D structure pauses demo walkthrough
              if (isDemoActive) {
                pauseWalkthrough();
              }
              handleSelectStructure(structureId, meshName);
            },
            onAnchorUpdate: (anchor) => {
              setProjectedAnchor(anchor);
            },
            onLoadComplete: (stats) => {
              setPerfStats((p) => ({ ...p, ...stats }));
              setIsLoading(false);
              setStatusMessage('Verified HRA renal anatomy ready.');

              // Execute initial scene actions if returned by session
              if (sessionData?.initial_tutor_response?.scene_actions) {
                for (const act of sessionData.initial_tutor_response.scene_actions) {
                  viewport.executeAction(act);
                }
              }
            },
            onError: (err) => {
              console.error(err);
              setStatusMessage(err);
              setIsLoading(false);
            },
          });

          viewportRef.current = viewport;
          if (typeof window !== 'undefined') {
            (window as any).__anatomyViewport = viewport;
          }
        }
      } catch (err) {
        console.error('Failed to initialize anatomy lab:', err);
        setStatusMessage('Anatomy service unavailable or feature disabled.');
        setIsLoading(false);
      }
    }

    initAnatomy();

    return () => {
      isMounted = false;
      if (viewportRef.current) {
        viewportRef.current.dispose();
      }
    };
  }, [reducedMotion]);

  return (
    <div className="flex flex-col h-screen w-full bg-[#F4F7FA] text-slate-900 font-sans overflow-hidden select-none">
      {/* 60–64px Application Header */}
      <AnatomyHeader
        onOpenSources={() => setIsSourcesOpen(true)}
        onResetCamera={handleResetCamera}
        isDemoActive={isDemoActive}
        onToggleDemo={handleToggleDemo}
        debugMode={debugMode}
        perfStats={perfStats}
      />

      {/* Main Learning Workspace */}
      <div className="flex flex-col md:flex-row flex-1 relative overflow-hidden">
        {/* HERO 3D Anatomy Stage (Gets all remaining width) */}
        <div className="flex-1 h-full relative flex flex-col bg-[#0D1722] overflow-hidden">
          {/* Subtle Radial Stage Lighting Overlay */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'radial-gradient(circle at 45% 45%, rgba(23, 43, 58, 0.6) 0%, rgba(13, 23, 34, 0.95) 100%)',
            }}
          />

          {/* Three.js Canvas */}
          <div
            ref={containerRef}
            className="flex-1 h-full w-full cursor-grab active:cursor-grabbing z-0"
          />

          {/* Sparse Anchored DOM Label */}
          {selectedStructure && (
            <ProjectedLabel
              anchor={projectedAnchor}
              displayName={selectedStructure.display_name}
              isChallengeMode={currentMode === 'CHALLENGE'}
            />
          )}

          {/* Floating View & Layer Toolbar */}
          <ViewToolbar
            currentPreset={currentPreset}
            onSelectPreset={handleSelectPreset}
            surfaceMode={surfaceMode}
            onSetSurfaceMode={handleSetSurfaceMode}
            hasSelectedStructure={!!selectedStructure}
            isIsolated={isIsolated}
            onToggleIsolate={handleToggleIsolate}
            onResetView={handleResetView}
          />

          {/* Interactive Demo Controls Overlay */}
          {isDemoActive && (
            <DemoControls
              currentStep={demoStep}
              currentStepIndex={demoStepIndex}
              totalSteps={demoTotalSteps}
              isPaused={isDemoPaused}
              onPause={pauseWalkthrough}
              onResume={resumeWalkthrough}
              onNext={() => demoExecuteStep(demoStepIndex + 1)}
              onPrev={() => demoExecuteStep(demoStepIndex - 1)}
              onExit={() => {
                stopWalkthrough();
                handleResetView();
              }}
            />
          )}

          {/* Loading Overlay */}
          {isLoading && (
            <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-[#0D1722]/90 backdrop-blur-xs">
              <div className="w-8 h-8 border-3 border-teal-500/30 border-t-teal-400 rounded-full animate-spin mb-3" />
              <div className="text-xs font-medium text-slate-300">
                {statusMessage}
              </div>
            </div>
          )}

          {/* Backend Unavailable Notice (Allows static 3D exploration safely) */}
          {!isBackendAvailable && (
            <div className="absolute top-4 left-4 z-10 px-3 py-1.5 bg-slate-900/80 backdrop-blur-md rounded-lg border border-slate-700 text-xs text-amber-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span>Offline mode: 3D anatomy inspection available.</span>
            </div>
          )}
        </div>

        {/* 360px Light Learning Rail */}
        <LearningRail
          currentMode={currentMode}
          onSelectMode={setCurrentMode}
          selectedStructure={selectedStructure}
          onFocusStructure={handleFocusStructure}
          onIsolateStructure={(sid) => {
            setIsIsolated(true);
            if (viewportRef.current) viewportRef.current.isolateStructure(sid);
          }}
          onAskTutor={handleAskTutor}
          onSelectStructureByName={(sid) => handleSelectStructure(sid)}
          tutorMessage={tutorMessage}
          interactionReq={interactionReq}
          onProceedToChallenge={() => setCurrentMode('CHALLENGE')}
          isSubmitting={isSubmitting}
          historyMessages={historyMessages}
          onSubmitChallenge={handleSubmitChallenge}
          challengeOutcome={challengeOutcome}
          onResetChallenge={() => setChallengeOutcome(null)}
          onContinueChallenge={() => {
            setChallengeOutcome(null);
            setCurrentMode('GUIDED_LESSON');
          }}
          isDemoActive={isDemoActive}
          isCutawayMode={surfaceMode === 'CUTAWAY'}
        />
      </div>

      {/* Sources & Provenance Modal */}
      <SourcesModal
        isOpen={isSourcesOpen}
        onClose={() => setIsSourcesOpen(false)}
      />
    </div>
  );
}
