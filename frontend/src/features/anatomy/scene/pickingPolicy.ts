import * as THREE from 'three';

export type SurfacePresentationMode = 'SURFACE' | 'REVEAL' | 'CUTAWAY';

export interface PickingContext {
  surfaceMode: SurfacePresentationMode;
  isolatedStructureId: string | null;
  meshToStructureId: Map<string, string>;
  structureVisibility: Map<string, boolean>;
  clippingPlane?: THREE.Plane | null;
}

/**
 * Filter raycast intersections according to active presentation & picking policy:
 * 1. In 'CUTAWAY' / 'REVEAL' mode: if clipping planes slice the outer capsule/cortex,
 *    raycast hits within the discarded region pass through directly to internal structures.
 * 2. In 'ISOLATE' mode: only the isolated structure can be picked.
 * 3. Hidden meshes must not intercept raycasts.
 */
export function filterRaycastHit(
  hit: THREE.Intersection,
  context: PickingContext
): { mesh: THREE.Mesh; structureId: string } | null {
  const obj = hit.object;
  if (!obj || !(obj as THREE.Mesh).isMesh) {
    return null;
  }

  const mesh = obj as THREE.Mesh;
  if (!mesh.visible) {
    return null;
  }

  // Discard hits in the clipped-away geometry region so rays reach internal structures
  if (context.clippingPlane && hit.point) {
    const mat = mesh.material as THREE.Material & { clippingPlanes?: THREE.Plane[] };
    if (mat && mat.clippingPlanes && mat.clippingPlanes.includes(context.clippingPlane)) {
      if (context.clippingPlane.distanceToPoint(hit.point) < 0) {
        return null;
      }
    }
  }

  const structureId = context.meshToStructureId.get(mesh.name) || mesh.name;

  // Check if structure is hidden by policy
  if (context.structureVisibility.get(structureId) === false) {
    return null;
  }

  // If isolation is active, only allow picking the isolated structure
  if (context.isolatedStructureId && structureId !== context.isolatedStructureId) {
    return null;
  }

  return { mesh, structureId };
}

