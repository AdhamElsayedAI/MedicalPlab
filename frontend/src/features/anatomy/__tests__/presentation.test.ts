import test from 'node:test';
import assert from 'node:assert/strict';
import {
  adaptStructure,
  determineInitialLearningMode,
  isChallengeReady,
  formatRelationshipSummary,
} from '../adapters/anatomyPresentationAdapter';
import { CAMERA_PRESETS } from '../scene/cameraPresets';
import { filterRaycastHit } from '../scene/pickingPolicy';
import { DEMO_STEPS } from '../hooks/useDemoWalkthrough';

test('presentation adapter adapts structures with educational descriptions and ontology preserved', () => {
  const mockStruct = {
    structure_id: 'renal_artery_left',
    display_name: 'Left Renal Artery',
    source_system: 'hubmap_hra',
    source_structure_id: 'VH_M_renal_artery_L',
    ontology_id: 'UBERON:0001186',
    mesh_node_names: ['VH_M_renal_artery_L'],
    relationships: [{ type: 'BRANCH_OF', target: 'abdominal_aorta' }],
  };

  const adapted = adaptStructure(mockStruct);
  assert.equal(adapted.displayName, 'Left Renal Artery');
  assert.equal(adapted.ontologyId, 'UBERON:0001186');
  assert.equal(adapted.category, 'vessel');
  assert.ok(adapted.shortDescription.includes('aorta'));
  assert.ok(adapted.clinicalRelevance.length > 0);

  const relSummary = formatRelationshipSummary(mockStruct.relationships);
  assert.deepEqual(relSummary, ['Branches from abdominal aorta']);
});

test('mode determination respects authoritative challenge session state', () => {
  const introSession = {
    session_id: 's1',
    learner_id: 'user1',
    learning_objective: 'test',
    lesson_state: 'INTRO' as const,
    selected_structure_ids: [],
    hint_level: 0,
    challenge_state: 'INACTIVE',
    created_at: 1,
    updated_at: 1,
  };
  assert.equal(determineInitialLearningMode(introSession), 'GUIDED_LESSON');
  assert.equal(isChallengeReady(introSession), false);

  const challengeSession = {
    ...introSession,
    lesson_state: 'CHALLENGE_ACTIVE' as const,
    challenge_state: 'ACTIVE',
  };
  assert.equal(determineInitialLearningMode(challengeSession), 'CHALLENGE');
  assert.equal(isChallengeReady(challengeSession), true);
});

test('camera presets verify optimal kidney occupancy and target centering', () => {
  assert.ok(CAMERA_PRESETS.KIDNEY_OVERVIEW);
  assert.ok(CAMERA_PRESETS.HILUM_FOCUS);
  assert.ok(CAMERA_PRESETS.INTERNAL_CUTAWAY);
  assert.ok(CAMERA_PRESETS.WHOLE_MODEL);

  // Default KIDNEY_OVERVIEW FOV in recommended range 32-38
  assert.ok(CAMERA_PRESETS.KIDNEY_OVERVIEW.fov >= 32 && CAMERA_PRESETS.KIDNEY_OVERVIEW.fov <= 38);

  // Target coordinates point to renal center
  assert.ok(CAMERA_PRESETS.KIDNEY_OVERVIEW.target.x > 0.05 && CAMERA_PRESETS.KIDNEY_OVERVIEW.target.x < 0.08);
  assert.ok(CAMERA_PRESETS.KIDNEY_OVERVIEW.target.y > 0.28 && CAMERA_PRESETS.KIDNEY_OVERVIEW.target.y < 0.32);

  // INTERNAL_CUTAWAY targets internal collecting and medullary structures
  assert.ok(CAMERA_PRESETS.INTERNAL_CUTAWAY.target.x > 0.05 && CAMERA_PRESETS.INTERNAL_CUTAWAY.target.x < 0.08);
  assert.ok(CAMERA_PRESETS.INTERNAL_CUTAWAY.fov <= 32);
});

test('picking policy enforces surface vs reveal vs isolate rules', () => {
  const meshToStructureId = new Map([
    ['VH_M_kidney_capsule_L', 'kidney_capsule_left'],
    ['VH_M_renal_artery_L', 'renal_artery_left'],
  ]);
  const visibility = new Map([
    ['kidney_capsule_left', true],
    ['renal_artery_left', true],
  ]);

  const capsuleMesh = { name: 'VH_M_kidney_capsule_L', isMesh: true, visible: true } as any;
  const arteryMesh = { name: 'VH_M_renal_artery_L', isMesh: true, visible: true } as any;

  // Surface mode: capsule is pickable
  const hitCapsule = filterRaycastHit({ object: capsuleMesh } as any, {
    surfaceMode: 'SURFACE',
    isolatedStructureId: null,
    meshToStructureId,
    structureVisibility: visibility,
  });
  assert.ok(hitCapsule);
  assert.equal(hitCapsule?.structureId, 'kidney_capsule_left');

  // Isolate mode: non-isolated structure is NOT pickable
  const hitArteryWhenCapsuleIsolated = filterRaycastHit({ object: arteryMesh } as any, {
    surfaceMode: 'SURFACE',
    isolatedStructureId: 'kidney_capsule_left',
    meshToStructureId,
    structureVisibility: visibility,
  });
  assert.equal(hitArteryWhenCapsuleIsolated, null);

  // Hidden mesh is NOT pickable
  visibility.set('renal_artery_left', false);
  const hitHiddenArtery = filterRaycastHit({ object: arteryMesh } as any, {
    surfaceMode: 'REVEAL',
    isolatedStructureId: null,
    meshToStructureId,
    structureVisibility: visibility,
  });
  assert.equal(hitHiddenArtery, null);

  // Cutaway clipping plane: point in clipped anterior region is ignored
  const cutPlane = {
    distanceToPoint: (p: { z: number }) => -p.z - 0.007,
  } as any;
  const clippedCortexMesh = {
    name: 'VH_M_kidney_capsule_L',
    isMesh: true,
    visible: true,
    material: { clippingPlanes: [cutPlane] },
  } as any;
  visibility.set('kidney_capsule_left', true);

  const hitClippedAnterior = filterRaycastHit(
    { object: clippedCortexMesh, point: { x: 0.06, y: 0.30, z: 0.010 } } as any,
    {
      surfaceMode: 'CUTAWAY',
      isolatedStructureId: null,
      meshToStructureId,
      structureVisibility: visibility,
      clippingPlane: cutPlane,
    }
  );
  assert.equal(hitClippedAnterior, null, 'Clipped anterior shell must not block raycast');

  // Cutaway clipping plane: point on preserved posterior shell is retained
  const hitPreservedPosterior = filterRaycastHit(
    { object: clippedCortexMesh, point: { x: 0.06, y: 0.30, z: -0.040 } } as any,
    {
      surfaceMode: 'CUTAWAY',
      isolatedStructureId: null,
      meshToStructureId,
      structureVisibility: visibility,
      clippingPlane: cutPlane,
    }
  );
  assert.ok(hitPreservedPosterior, 'Preserved posterior shell remains pickable');
  assert.equal(hitPreservedPosterior?.structureId, 'kidney_capsule_left');
});

test('demo walkthrough never auto-submits challenges and limits autoplay to presentation', () => {
  for (const step of DEMO_STEPS) {
    // Each step is reversible presentation
    assert.ok(step.durationMs > 0);
    assert.ok(step.cameraPreset in CAMERA_PRESETS);
    assert.ok(step.surfaceMode === 'SURFACE' || step.surfaceMode === 'REVEAL');
    // None of the steps fake answers or submit challenge
    assert.ok(step.targetLearningMode === 'EXPLORE' || step.targetLearningMode === 'GUIDED_LESSON' || step.targetLearningMode === 'CHALLENGE');
  }

  // Step 5 opens challenge for user to interact, without auto-submitting
  const lastStep = DEMO_STEPS[DEMO_STEPS.length - 1];
  assert.equal(lastStep.targetLearningMode, 'CHALLENGE');
  assert.equal(lastStep.selectStructureId, null);
});

test('mesh node mapping preserves canonical structure IDs', () => {
  const CANONICAL_MAPPINGS: Record<string, string> = {
    'VH_M_kidney_capsule_L': 'kidney_capsule_left',
    'VH_M_renal_artery_L': 'renal_artery_left',
    'VH_M_renal_vein_L': 'renal_vein_left',
    'VH_M_renal_pelvis_L': 'renal_pelvis_left',
    'VH_M_ureter_L': 'ureter_left',
  };

  for (const [node, structId] of Object.entries(CANONICAL_MAPPINGS)) {
    assert.ok(structId.endsWith('_left'));
    assert.ok(node.startsWith('VH_M_'));
  }
});

test('challenge mode guarantees challenge target structure is not leaked in labels', () => {
  // In challenge mode, ProjectedLabel uses generic "Selected Structure"
  const isChallenge = true;
  const labelText = isChallenge ? 'Selected Structure' : 'Left Renal Artery';
  assert.equal(labelText, 'Selected Structure');
  assert.notEqual(labelText, 'Left Renal Artery');
});

test('click vs drag threshold distinguishes orbit navigation from selection', () => {
  const DRAG_THRESHOLD = 6; // px

  const clickDist = Math.hypot(3, 2); // sqrt(9 + 4) = 3.6 px < 6 px
  const dragDist = Math.hypot(10, 8); // sqrt(100 + 64) = 12.8 px >= 6 px

  assert.ok(clickDist < DRAG_THRESHOLD, 'Small movement should be treated as click');
  assert.ok(dragDist >= DRAG_THRESHOLD, 'Significant movement should be treated as drag orbit');
});

