import { useCallback, useEffect, useRef, useState } from 'react';
import { CameraPresetName } from '../scene/cameraPresets';
import { SurfacePresentationMode } from '../scene/pickingPolicy';
import { LearningMode } from '../adapters/anatomyPresentationAdapter';

export interface DemoStep {
  id: number;
  label: string;
  durationMs: number;
  caption: string;
  cameraPreset: CameraPresetName;
  surfaceMode: SurfacePresentationMode;
  selectStructureId?: string | null;
  targetLearningMode: LearningMode;
}

export const DEMO_STEPS: DemoStep[] = [
  {
    id: 1,
    label: 'Kidney Overview',
    durationMs: 8000,
    caption: 'Verified HuBMAP Human Reference Atlas (HRA) 3D renal anatomy in canonical CCF coordinates.',
    cameraPreset: 'KIDNEY_OVERVIEW',
    surfaceMode: 'SURFACE',
    selectStructureId: null,
    targetLearningMode: 'EXPLORE',
  },
  {
    id: 2,
    label: 'Physical Structure Grounding',
    durationMs: 9000,
    caption: 'Deterministic raycast selection grounds anatomy to authoritative ontology (Left Kidney · UBERON:0002113).',
    cameraPreset: 'KIDNEY_OVERVIEW',
    surfaceMode: 'SURFACE',
    selectStructureId: 'kidney_capsule_left',
    targetLearningMode: 'EXPLORE',
  },
  {
    id: 3,
    label: 'Hilum Focus (V-A-P Readability)',
    durationMs: 11000,
    caption: 'Anteromedial oblique vantage point establishes balanced spatial depth: Anterior Vein -> Middle Artery -> Posterior Pelvis.',
    cameraPreset: 'HILUM_FOCUS',
    surfaceMode: 'SURFACE',
    selectStructureId: null,
    targetLearningMode: 'EXPLORE',
  },
  {
    id: 4,
    label: 'AI Tutor Socratic Guidance',
    durationMs: 12000,
    caption: 'AI Anatomy Tutor provides clinical reasoning and Socratic teaching grounded in verified anatomical relationships.',
    cameraPreset: 'HILUM_FOCUS',
    surfaceMode: 'SURFACE',
    selectStructureId: 'renal_artery_left',
    targetLearningMode: 'GUIDED_LESSON',
  },
  {
    id: 5,
    label: 'Real Server Challenge',
    durationMs: 18000,
    caption: 'Labels suppressed; learner clicks the real 3D specimen and receives deterministic server-evaluated feedback.',
    cameraPreset: 'HILUM_FOCUS',
    surfaceMode: 'SURFACE',
    selectStructureId: null,
    targetLearningMode: 'CHALLENGE',
  },
];

interface UseDemoWalkthroughProps {
  onApplyCamera: (preset: CameraPresetName) => void;
  onSetSurfaceMode: (mode: SurfacePresentationMode) => void;
  onSelectStructure: (structureId: string | null) => void;
  onSetLearningMode: (mode: LearningMode) => void;
}

export function useDemoWalkthrough({
  onApplyCamera,
  onSetSurfaceMode,
  onSelectStructure,
  onSetLearningMode,
}: UseDemoWalkthroughProps) {
  const [isActive, setIsActive] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const executeStep = useCallback((index: number) => {
    if (index < 0 || index >= DEMO_STEPS.length) return;
    const step = DEMO_STEPS[index];
    setCurrentStepIndex(index);

    onApplyCamera(step.cameraPreset);
    onSetSurfaceMode(step.surfaceMode);
    if (step.selectStructureId !== undefined) {
      onSelectStructure(step.selectStructureId);
    }
    onSetLearningMode(step.targetLearningMode);
  }, [onApplyCamera, onSetSurfaceMode, onSelectStructure, onSetLearningMode]);

  const stopWalkthrough = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setIsActive(false);
    setIsPaused(false);
  }, []);

  const startWalkthrough = useCallback(() => {
    stopWalkthrough();
    setIsActive(true);
    setIsPaused(false);
    executeStep(0);
  }, [stopWalkthrough, executeStep]);

  const pauseWalkthrough = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setIsPaused(true);
  }, []);

  const resumeWalkthrough = useCallback(() => {
    setIsPaused(false);
  }, []);

  // Step progression timer
  useEffect(() => {
    if (!isActive || isPaused) return;

    const currentStep = DEMO_STEPS[currentStepIndex];
    timerRef.current = setTimeout(() => {
      if (currentStepIndex + 1 < DEMO_STEPS.length) {
        executeStep(currentStepIndex + 1);
      } else {
        // End of walkthrough
        stopWalkthrough();
      }
    }, currentStep.durationMs);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [isActive, isPaused, currentStepIndex, executeStep, stopWalkthrough]);

  return {
    isDemoActive: isActive,
    isDemoPaused: isPaused,
    currentStep: DEMO_STEPS[currentStepIndex],
    currentStepIndex,
    totalSteps: DEMO_STEPS.length,
    startWalkthrough,
    stopWalkthrough,
    pauseWalkthrough,
    resumeWalkthrough,
    executeStep,
  };
}
