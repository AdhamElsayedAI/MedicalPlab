/**
 * Deterministic Three.js Scene Controller for MedicalPlab 3D Anatomy Lab.
 *
 * Enforces the strict architectural boundary:
 * LLM -> Validated Structured Actions -> Deterministic Scene Controller -> Three.js
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { AnatomyActionType, AnatomyStructure, SceneAction } from './types';

export interface SceneControllerOptions {
  container: HTMLDivElement;
  structures: AnatomyStructure[];
  onSelectStructure: (structureId: string, meshName: string) => void;
  onLoadComplete?: (stats: { loadTimeMs: number; meshCount: number; triangleCount: number; vertexCount: number }) => void;
  onError?: (error: string) => void;
}

export class AnatomySceneController {
  private container: HTMLDivElement;
  private structures: AnatomyStructure[];
  private onSelectStructure: (structureId: string, meshName: string) => void;
  private onLoadComplete?: (stats: { loadTimeMs: number; meshCount: number; triangleCount: number; vertexCount: number }) => void;
  private onError?: (error: string) => void;

  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private animationFrameId: number | null = null;

  // Scene registries
  private meshMap: Map<string, THREE.Mesh> = new Map();
  private structureToMeshes: Map<string, THREE.Mesh[]> = new Map();
  private meshToStructureId: Map<string, string> = new Map();
  private originalMaterials: Map<string, THREE.Material | THREE.Material[]> = new Map();

  private defaultCameraPos = new THREE.Vector3(0.22, 0.32, 0.35);
  private defaultTarget = new THREE.Vector3(0.06, 0.28, -0.02);
  private highlightedStructureId: string | null = null;

  constructor(options: SceneControllerOptions) {
    this.container = options.container;
    this.structures = options.structures;
    this.onSelectStructure = options.onSelectStructure;
    this.onLoadComplete = options.onLoadComplete;
    this.onError = options.onError;

    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 600;

    // 1. Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0d14);

    const grid = new THREE.GridHelper(1.2, 24, 0x1e293b, 0x0f172a);
    grid.position.y = -0.05;
    this.scene.add(grid);

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.01, 100);
    this.camera.position.copy(this.defaultCameraPos);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;
    this.container.appendChild(this.renderer.domElement);

    // 4. Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.target.copy(this.defaultTarget);
    this.controls.maxDistance = 2.5;
    this.controls.minDistance = 0.04;

    // 5. Lighting
    this.setupLighting();

    // 6. Raycaster
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // 7. Event listeners
    this.renderer.domElement.addEventListener('pointerdown', this.handlePointerDown);
    window.addEventListener('resize', this.handleResize);

    // 8. Build mapping index
    this.buildStructureIndices();

    // 9. Start animation loop
    this.animate();

    // 10. Load co-registered HRA renal assets
    this.loadRenalAssets();
  }

  private setupLighting(): void {
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
    this.scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 2.2);
    dirLight1.position.set(1.5, 2.5, 2.0);
    this.scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x60a5fa, 1.2);
    dirLight2.position.set(-1.5, -1.0, -1.5);
    this.scene.add(dirLight2);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.6);
    rimLight.position.set(0, 1.5, -2.0);
    this.scene.add(rimLight);
  }

  private buildStructureIndices(): void {
    this.meshToStructureId.clear();
    for (const struct of this.structures) {
      for (const nodeName of struct.mesh_node_names) {
        this.meshToStructureId.set(nodeName, struct.structure_id);
      }
    }
  }

  private async loadRenalAssets(): Promise<void> {
    const loader = new GLTFLoader();
    const assets = [
      '/models/anatomy/hra/renal/VH_M_Kidney_L.glb',
      '/models/anatomy/hra/renal/VH_M_Ureter_L.glb',
      '/models/anatomy/hra/renal/VH_M_Blood_Vasculature_Kidney.glb',
    ];

    const startTime = performance.now();
    let totalMeshes = 0;
    let totalTriangles = 0;
    let totalVertices = 0;

    const loadPromises = assets.map((url) => {
      return new Promise<THREE.Group>((resolve, reject) => {
        loader.load(
          url,
          (gltf) => resolve(gltf.scene),
          undefined,
          (err) => reject(err)
        );
      });
    });

    try {
      const groups = await Promise.all(loadPromises);

      for (const group of groups) {
        group.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            totalMeshes++;
            const name = mesh.name;
            this.meshMap.set(name, mesh);

            // Save original material reference
            this.originalMaterials.set(mesh.uuid, mesh.material);

            // Compute geometric stats
            if (mesh.geometry) {
              const pos = mesh.geometry.attributes.position;
              const idx = mesh.geometry.index;
              totalVertices += pos.count;
              totalTriangles += idx ? idx.count / 3 : pos.count / 3;
            }

            // Map to structure ID
            let mappedId = this.meshToStructureId.get(name);
            if (!mappedId) {
              // Try prefix match (e.g. pyramids a-i)
              for (const [nodePrefix, sid] of this.meshToStructureId.entries()) {
                if (name.startsWith(nodePrefix)) {
                  mappedId = sid;
                  break;
                }
              }
            }

            if (mappedId) {
              const list = this.structureToMeshes.get(mappedId) || [];
              list.push(mesh);
              this.structureToMeshes.set(mappedId, list);
              this.meshToStructureId.set(name, mappedId);
            }

            // Default capsule translucency for internal visibility
            if (name.includes('capsule')) {
              if (Array.isArray(mesh.material)) {
                mesh.material = mesh.material[0].clone();
              } else {
                mesh.material = mesh.material.clone();
              }
              const stdMat = mesh.material as THREE.MeshStandardMaterial;
              stdMat.transparent = true;
              stdMat.opacity = 0.35;
              stdMat.roughness = 0.3;
            }
          }
        });

        this.scene.add(group);
      }

      const loadDuration = Math.round(performance.now() - startTime);
      if (this.onLoadComplete) {
        this.onLoadComplete({
          loadTimeMs: loadDuration,
          meshCount: totalMeshes,
          triangleCount: Math.round(totalTriangles),
          vertexCount: Math.round(totalVertices),
        });
      }
    } catch (error) {
      console.error('Failed to load HRA renal assets:', error);
      if (this.onError) {
        this.onError(`Asset loading failed: ${String(error)}`);
      }
    }
  }

  private handlePointerDown = (event: MouseEvent): void => {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.scene.children, true);

    const hit = intersects.find((i) => (i.object as THREE.Mesh).isMesh && i.object.type === 'Mesh');
    if (hit) {
      const mesh = hit.object as THREE.Mesh;
      const nodeName = mesh.name;
      const structureId = this.meshToStructureId.get(nodeName) || nodeName;
      this.onSelectStructure(structureId, nodeName);
    }
  };

  private handleResize = (): void => {
    if (!this.container) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  };

  private animate = (): void => {
    this.animationFrameId = requestAnimationFrame(this.animate);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };

  /**
   * Deterministically execute a validated scene action.
   */
  public executeAction(action: SceneAction): void {
    const actionType = action.action;
    const sid = action.structure_id ? action.structure_id.trim().toLowerCase() : null;

    switch (actionType) {
      case 'RESET_SCENE':
        this.resetScene();
        break;

      case 'HIGHLIGHT_STRUCTURE':
        if (sid) this.highlightStructure(sid);
        break;

      case 'FOCUS_STRUCTURE':
        if (sid) this.focusStructure(sid);
        break;

      case 'ISOLATE_STRUCTURE':
        if (sid) this.isolateStructure(sid);
        break;

      case 'SHOW_STRUCTURE':
        if (sid) this.setStructureVisibility(sid, true);
        break;

      case 'HIDE_STRUCTURE':
        if (sid) this.setStructureVisibility(sid, false);
        break;

      case 'SET_STRUCTURE_OPACITY':
        if (sid && action.opacity !== undefined && action.opacity !== null) {
          this.setStructureOpacity(sid, action.opacity);
        }
        break;

      case 'SHOW_RELATION':
        if (sid) this.highlightStructure(sid);
        break;

      default:
        console.warn(`Unrecognized scene action ignored: ${actionType}`);
    }
  }

  public highlightStructure(structureId: string): void {
    this.clearHighlights();
    const meshes = this.structureToMeshes.get(structureId) || [];
    for (const mesh of meshes) {
      const origMat = mesh.material;
      const highlightMat = (Array.isArray(origMat) ? origMat[0] : origMat).clone() as THREE.MeshStandardMaterial;
      highlightMat.emissive = new THREE.Color(0x06b6d4); // Glowing cyan
      highlightMat.emissiveIntensity = 0.85;
      highlightMat.roughness = 0.2;
      if (highlightMat.transparent) {
        highlightMat.opacity = Math.max(highlightMat.opacity, 0.85);
      }
      mesh.material = highlightMat;
    }
    this.highlightedStructureId = structureId;
  }

  public focusStructure(structureId: string): void {
    const meshes = this.structureToMeshes.get(structureId) || [];
    if (meshes.length === 0) return;

    const bbox = new THREE.Box3();
    for (const m of meshes) {
      bbox.expandByObject(m);
    }
    const center = bbox.getCenter(new THREE.Vector3());

    // Smooth focus target
    this.controls.target.copy(center);
    this.camera.lookAt(center);
  }

  public isolateStructure(structureId: string): void {
    // Dim everything except target
    for (const [sid, meshes] of this.structureToMeshes.entries()) {
      const isTarget = sid === structureId;
      for (const m of meshes) {
        if (isTarget) {
          m.visible = true;
          const orig = this.originalMaterials.get(m.uuid);
          if (orig) {
            const mat = (Array.isArray(orig) ? orig[0] : orig).clone() as THREE.MeshStandardMaterial;
            mat.emissive = new THREE.Color(0x06b6d4);
            mat.emissiveIntensity = 0.9;
            m.material = mat;
          }
        } else {
          // Dim non-targets
          const orig = this.originalMaterials.get(m.uuid);
          if (orig) {
            const dimMat = (Array.isArray(orig) ? orig[0] : orig).clone() as THREE.MeshStandardMaterial;
            dimMat.transparent = true;
            dimMat.opacity = 0.12;
            m.material = dimMat;
          }
        }
      }
    }
    this.highlightedStructureId = structureId;
  }

  public setStructureVisibility(structureId: string, visible: boolean): void {
    const meshes = this.structureToMeshes.get(structureId) || [];
    for (const m of meshes) {
      m.visible = visible;
    }
  }

  public setStructureOpacity(structureId: string, opacity: number): void {
    const meshes = this.structureToMeshes.get(structureId) || [];
    for (const m of meshes) {
      if (Array.isArray(m.material)) {
        m.material = m.material[0].clone();
      } else {
        m.material = m.material.clone();
      }
      const mat = m.material as THREE.MeshStandardMaterial;
      mat.transparent = opacity < 1.0;
      mat.opacity = opacity;
      mat.visible = opacity > 0.01;
      mat.needsUpdate = true;
    }
  }

  public clearHighlights(): void {
    for (const [uuid, origMat] of this.originalMaterials.entries()) {
      for (const mesh of this.meshMap.values()) {
        if (mesh.uuid === uuid) {
          // Restore original material unless it's capsule with custom opacity
          if (mesh.name.includes('capsule')) {
            const std = mesh.material as THREE.MeshStandardMaterial;
            std.emissive.setHex(0x000000);
            std.emissiveIntensity = 0.0;
          } else {
            mesh.material = origMat;
          }
        }
      }
    }
    this.highlightedStructureId = null;
  }

  public resetScene(): void {
    this.clearHighlights();
    for (const mesh of this.meshMap.values()) {
      mesh.visible = true;
      const origMat = this.originalMaterials.get(mesh.uuid);
      if (origMat) {
        if (mesh.name.includes('capsule')) {
          const std = mesh.material as THREE.MeshStandardMaterial;
          std.transparent = true;
          std.opacity = 0.35;
          std.emissive.setHex(0x000000);
        } else {
          mesh.material = origMat;
        }
      }
    }
    this.camera.position.copy(this.defaultCameraPos);
    this.controls.target.copy(this.defaultTarget);
    this.controls.update();
  }

  public dispose(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
    }
    this.renderer.domElement.removeEventListener('pointerdown', this.handlePointerDown);
    window.removeEventListener('resize', this.handleResize);
    this.renderer.dispose();
    if (this.container.contains(this.renderer.domElement)) {
      this.container.removeChild(this.renderer.domElement);
    }
  }
}
