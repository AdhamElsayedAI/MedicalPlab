import * as THREE from 'three';

export type CameraPresetName =
  | 'KIDNEY_OVERVIEW'
  | 'HILUM_FOCUS'
  | 'INTERNAL_CUTAWAY'
  | 'WHOLE_MODEL';

export interface CameraPreset {
  name: CameraPresetName;
  label: string;
  description: string;
  target: THREE.Vector3;
  position: THREE.Vector3;
  fov: number;
  minDistance: number;
  maxDistance: number;
}

/**
 * Verified camera presets based on exact HuBMAP HRA renal GLB coordinates:
 * - +Y: Superior (cranial)
 * - -Y: Inferior (caudal)
 * - +X: Lateral (left flank)
 * - -X: Medial (midline / aorta / IVC)
 * - +Z: Anterior (ventral)
 * - -Z: Posterior (dorsal)
 *
 * Anatomical Centroids:
 * - Left Kidney body:   [0.062, 0.298, -0.015]
 * - Renal Vein:         [0.029, 0.303, +0.010] (anterior)
 * - Renal Artery:       [0.041, 0.307, -0.005] (intermediate depth, superior)
 * - Renal Pelvis:       [0.063, 0.298, -0.009] (posterior depth, inferior)
 * - Medullary Pyramids: [0.072, 0.302, -0.028] (deep within parenchyma)
 */
export const CAMERA_PRESETS: Record<CameraPresetName, CameraPreset> = {
  // 1. Kidney Overview: Parenchyma dominates ~60% canvas height.
  // Medial hilum cleanly articulated, distal vessels framed naturally at periphery.
  KIDNEY_OVERVIEW: {
    name: 'KIDNEY_OVERVIEW',
    label: 'Kidney Overview',
    description: 'Natural medical atlas view of intact left kidney parenchyma and hilum',
    target: new THREE.Vector3(0.062, 0.298, -0.015),
    position: new THREE.Vector3(0.012, 0.330, 0.220),
    fov: 32,
    minDistance: 0.08,
    maxDistance: 1.2,
  },

  // 2. Hilum Focus: Re-authored anteromedial oblique angle.
  // Perfectly balanced depth: Anterior Vein -> Middle Artery -> Posterior Pelvis (V-A-P).
  // Vein is clearly visible in front without visually occluding the artery and pelvis behind it.
  HILUM_FOCUS: {
    name: 'HILUM_FOCUS',
    label: 'Hilum Focus',
    description: 'Medial hilar cleft establishing simultaneous Vein-Artery-Pelvis (V-A-P) spatial depth',
    target: new THREE.Vector3(0.056, 0.302, -0.012),
    position: new THREE.Vector3(0.022, 0.322, 0.165),
    fov: 28,
    minDistance: 0.06,
    maxDistance: 0.8,
  },

  // 3. Internal Cutaway: Official calibrated didactic cutaway composition.
  // Organ occupies ~70% usable viewport height.
  // Full kidney silhouette and posterior cortical bed intact, framing medullary pyramids,
  // papillae cupped in minor calyces, major calyces, and central renal pelvis.
  INTERNAL_CUTAWAY: {
    name: 'INTERNAL_CUTAWAY',
    label: 'Internal Cutaway',
    description: 'Calibrated anatomical cutaway showing pyramids, calyces, and pelvis nested inside the organ',
    target: new THREE.Vector3(0.068, 0.298, -0.020),
    position: new THREE.Vector3(0.034, 0.320, 0.235),
    fov: 29,
    minDistance: 0.06,
    maxDistance: 1.0,
  },

  // 4. Whole Model: Wide overview fitting full assembly: kidney, hilum, and descending ureter.
  WHOLE_MODEL: {
    name: 'WHOLE_MODEL',
    label: 'Whole Model',
    description: 'Complete assembly overview showing the kidney, hilum, and full descending ureter',
    target: new THREE.Vector3(0.055, 0.190, -0.020),
    position: new THREE.Vector3(0.010, 0.260, 0.500),
    fov: 34,
    minDistance: 0.15,
    maxDistance: 2.0,
  },
};

/**
 * Region-aware camera framing helper.
 * Fits the camera to frame a bounding box with controlled padding.
 */
export function calculateFitCamera(
  box: THREE.Box3,
  aspect: number,
  fovDegrees: number,
  paddingFactor = 1.25,
  direction = new THREE.Vector3(-0.35, 0.25, 0.90).normalize()
): { position: THREE.Vector3; target: THREE.Vector3 } {
  const center = new THREE.Vector3();
  box.getCenter(center);

  const size = new THREE.Vector3();
  box.getSize(size);

  const fovRad = (fovDegrees * Math.PI) / 180;
  const maxDim = Math.max(size.x, size.y, size.z);

  // Distance based on vertical FOV and horizontal FOV
  const distY = (maxDim / 2) / Math.tan(fovRad / 2);
  const distX = (maxDim / 2) / (Math.tan(fovRad / 2) * aspect);
  const distance = Math.max(distY, distX) * paddingFactor;

  const position = center.clone().add(direction.clone().multiplyScalar(distance));
  return { position, target: center };
}

