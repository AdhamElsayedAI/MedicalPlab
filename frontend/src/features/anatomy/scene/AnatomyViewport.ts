import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

import {
  AnatomyStructure,
  SceneAction,
} from '@/lib/anatomy/types';
import {
  CAMERA_PRESETS,
  CameraPreset,
  CameraPresetName,
} from './cameraPresets';
import {
  ANATOMICAL_PALETTE,
  HIGHLIGHT_COLORS,
  createAnatomicalMaterial,
} from './materialPresentation';
import {
  SurfacePresentationMode,
  filterRaycastHit,
} from './pickingPolicy';

export interface ViewportPerformanceStats {
  loadTimeMs: number;
  meshCount: number;
  triangleCount: number;
  vertexCount: number;
  fps: number;
}

export interface ProjectedAnchor {
  structureId: string;
  screenX: number;
  screenY: number;
  visible: boolean;
}

export interface AnatomyViewportOptions {
  container: HTMLDivElement;
  structures: AnatomyStructure[];
  onSelectStructure: (structureId: string, meshName: string) => void;
  onHoverStructure?: (structureId: string | null) => void;
  onAnchorUpdate?: (anchor: ProjectedAnchor | null) => void;
  onLoadComplete?: (stats: ViewportPerformanceStats) => void;
  onError?: (errorMsg: string) => void;
  reducedMotion?: boolean;
}

export class AnatomyViewport {
  private container: HTMLDivElement;
  private structures: AnatomyStructure[];
  private onSelectStructure: (structureId: string, meshName: string) => void;
  private onHoverStructure?: (structureId: string | null) => void;
  private onAnchorUpdate?: (anchor: ProjectedAnchor | null) => void;
  private onLoadComplete?: (stats: ViewportPerformanceStats) => void;
  private onError?: (errorMsg: string) => void;
  private reducedMotion: boolean;

  // Three.js Core
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private animationFrameId: number | null = null;

  // Scene Registries
  private meshMap: Map<string, THREE.Mesh> = new Map();
  private structureToMeshes: Map<string, THREE.Mesh[]> = new Map();
  private meshToStructureId: Map<string, string> = new Map();
  private baseMaterials: Map<string, THREE.Material> = new Map();
  private structureVisibility: Map<string, boolean> = new Map();

  public getScene(): THREE.Scene { return this.scene; }
  public getMeshMap(): Map<string, THREE.Mesh> { return this.meshMap; }

  // State
  private surfaceMode: SurfacePresentationMode = 'SURFACE';
  private isolatedStructureId: string | null = null;
  private selectedStructureId: string | null = null;
  private hoveredStructureId: string | null = null;
  private emphasizedStructureId: string | null = null;

  // Drag threshold tracking
  private pointerDownPos: { x: number; y: number } = { x: 0, y: 0 };
  private isPointerDown = false;
  private dragThreshold = 6; // px

  // Lighting & Environment References
  private keyLight!: THREE.DirectionalLight;
  private fillLight!: THREE.DirectionalLight;
  private ambientLight!: THREE.AmbientLight;
  private envTexture: THREE.Texture | null = null;

  // Medical Cutaway Plane
  // Calibrated anatomical coronal plane matching the kidney tilt (superior pole tilted posteriorly).
  // Normal (-0.06, -0.28, -0.96) cleanly opens the anterior shell across the full organ height
  // while preserving the entire posterior cortex bed, lateral border, and poles as anatomical context.
  private cutawayPlane: THREE.Plane = new THREE.Plane(
    new THREE.Vector3(-0.06, -0.28, -0.96).normalize(),
    0.200 // Default constant for SURFACE mode (outside organ, nothing clipped)
  );
  private isCutawayActive = false;
  private cutawayAnimation: {
    active: boolean;
    startTime: number;
    duration: number;
    startConstant: number;
    targetConstant: number;
    onComplete?: () => void;
  } | null = null;

  // Selective Guided Pathway Focus (Didactic collecting pathway mode)
  private isGuidedPathwayMode = false;
  private guidedPathwayId = 'f';

  // Smooth Camera Transitions
  private isTransitioning = false;
  private transitionStartTime = 0;
  private transitionDuration = 600; // ms
  private startCameraPos = new THREE.Vector3();
  private targetCameraPos = new THREE.Vector3();
  private startControlsTarget = new THREE.Vector3();
  private targetControlsTarget = new THREE.Vector3();

  // Performance Telemetry
  private frameCount = 0;
  private lastFpsTime = performance.now();
  private currentFps = 60;

  constructor(options: AnatomyViewportOptions) {
    this.container = options.container;
    this.structures = options.structures;
    this.onSelectStructure = options.onSelectStructure;
    this.onHoverStructure = options.onHoverStructure;
    this.onAnchorUpdate = options.onAnchorUpdate;
    this.onLoadComplete = options.onLoadComplete;
    this.onError = options.onError;
    this.reducedMotion = options.reducedMotion ?? false;

    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 600;

    // 1. Scene with subtle medical radial depth stage background
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0f1722); // Deep clinical slate stage

    // 2. Camera with default KIDNEY_OVERVIEW preset
    const defaultPreset = CAMERA_PRESETS.KIDNEY_OVERVIEW;
    this.camera = new THREE.PerspectiveCamera(defaultPreset.fov, width / height, 0.01, 50);
    this.camera.position.copy(defaultPreset.position);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
      alpha: false,
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.02;
    this.renderer.localClippingEnabled = true;
    this.container.appendChild(this.renderer.domElement);

    // 4. Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.target.copy(defaultPreset.target);
    this.controls.minDistance = defaultPreset.minDistance;
    this.controls.maxDistance = defaultPreset.maxDistance;

    // Cancel transition when user initiates manual orbit/pan
    this.controls.addEventListener('start', () => {
      this.isTransitioning = false;
    });

    // 5. Studio Lighting & Neutral Environment
    this.setupStudioLighting();
    this.setupEnvironment();

    // 6. Raycaster
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // 7. Event Listeners
    this.renderer.domElement.addEventListener('pointerdown', this.onPointerDown);
    this.renderer.domElement.addEventListener('pointerup', this.onPointerUp);
    this.renderer.domElement.addEventListener('pointermove', this.onPointerMove);
    window.addEventListener('resize', this.onWindowResize);

    // 8. Build mapping index
    this.buildStructureIndices();

    // 9. Start render loop
    this.animate();

    // 10. Load verified HRA renal models
    this.loadRenalAssets();
  }

  /**
   * Studio lighting setup designed for natural medical atlas tissue readability:
   * - Key light: soft upper/front-left (warm soft daylight)
   * - Fill light: soft opposite lower lateral (neutral soft fill)
   * - Separation light: subtle rear separation light (neutral soft, NO cyan glowing rim)
   */
  private setupStudioLighting(): void {
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.44);
    this.scene.add(this.ambientLight);

    // Key Light: soft upper/front-left (gentle biological warmth)
    this.keyLight = new THREE.DirectionalLight(0xfff8f2, 1.15);
    this.keyLight.position.set(-0.5, 1.1, 1.2);
    this.scene.add(this.keyLight);

    // Fill Light: soft opposite lower lateral (diffuses deep internal cavities)
    this.fillLight = new THREE.DirectionalLight(0xeef3f8, 0.70);
    this.fillLight.position.set(0.9, 0.3, 0.9);
    this.scene.add(this.fillLight);

    // Rear Separation Light: subtle, neutral soft, NO cyan glowing rim
    const rimLight = new THREE.DirectionalLight(0xdfe5ec, 0.25);
    rimLight.position.set(0.1, 0.6, -1.3);
    this.scene.add(rimLight);
  }

  /**
   * Generates a neutral, low-contrast medical studio environment map (<5ms, zero network requests).
   * Provides gentle diffuse light wrap so soft biological tissue exhibits natural form
   * without artificial mirror-like highlights or synthetic glossy reflections.
   */
  private setupEnvironment(): void {
    if (!this.renderer) return;
    try {
      const pmremGenerator = new THREE.PMREMGenerator(this.renderer);
      pmremGenerator.compileEquirectangularShader();

      const envScene = new THREE.Scene();
      envScene.background = new THREE.Color(0x141f2d);

      const hemi = new THREE.HemisphereLight(0xfff6ee, 0x141f2d, 0.75);
      envScene.add(hemi);

      const ceilingBox = new THREE.DirectionalLight(0xfff0e4, 0.60);
      ceilingBox.position.set(0, 2, 0);
      envScene.add(ceilingBox);

      this.envTexture = pmremGenerator.fromScene(envScene, 0.04).texture;
      this.scene.environment = this.envTexture;
      pmremGenerator.dispose();
    } catch (e) {
      console.warn('Environment generation skipped:', e);
    }
  }

  private buildStructureIndices(): void {
    this.meshToStructureId.clear();
    for (const struct of this.structures) {
      this.structureVisibility.set(struct.structure_id, true);
      for (const nodeName of struct.mesh_node_names) {
        this.meshToStructureId.set(nodeName, struct.structure_id);
      }
    }

    // Ground real HuBMAP HRA renal nodes to canonical structures:
    // Arterial tree (ipsilateral vessel entering left kidney)
    this.meshToStructureId.set('VH_M_right_renal_artery', 'renal_artery_left');
    this.meshToStructureId.set('VH_M_left_renal_artery', 'renal_artery_left');

    // Venous tree
    this.meshToStructureId.set('VH_M_renal_vein_L', 'renal_vein_left');
    this.meshToStructureId.set('VH_M_left_renal_vein', 'renal_vein_left');

    // Renal pelvis & calyces (collecting system)
    this.meshToStructureId.set('VH_M_renal_pelvis_L', 'renal_pelvis_left');
    this.meshToStructureId.set('VH_M_major_calyx_L_a', 'renal_pelvis_left');
    this.meshToStructureId.set('VH_M_major_calyx_L_b', 'renal_pelvis_left');
    this.meshToStructureId.set('VH_M_major_calyx_L_c', 'renal_pelvis_left');
    for (const s of ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']) {
      this.meshToStructureId.set(`VH_M_minor_calyx_L_${s}`, 'renal_pelvis_left');
    }

    // Cortex & Columns
    this.meshToStructureId.set('VH_M_outer_cortex_of_kidney_L', 'renal_cortex_left');
    this.meshToStructureId.set('VH_M_renal_column_L', 'renal_cortex_left');
    this.meshToStructureId.set('VH_M_cortex_of_kidney_L', 'renal_cortex_left');

    // Medullary Pyramids & Papillae
    for (const s of ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']) {
      this.meshToStructureId.set(`VH_M_renal_pyramid_L_${s}`, 'renal_medulla_left');
      this.meshToStructureId.set(`VH_M_renal_papilla_L_${s}`, 'renal_medulla_left');
    }

    // Capsule & Hilum & Ureter
    this.meshToStructureId.set('VH_M_kidney_capsule_L', 'kidney_capsule_left');
    this.meshToStructureId.set('VH_M_hilum_of_kidney_L', 'hilum_of_kidney_left');
    this.meshToStructureId.set('VH_M_ureter_L', 'ureter_left');
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
        loader.load(url, (gltf) => resolve(gltf.scene), undefined, (err) => reject(err));
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

            if (mesh.geometry) {
              const pos = mesh.geometry.attributes.position;
              const idx = mesh.geometry.index;
              totalVertices += pos.count;
              totalTriangles += idx ? idx.count / 3 : pos.count / 3;
            }

            // HRA Contralateral Right-Side Filtering:
            // In the bilateral HRA vascular asset, the right renal vein and contralateral artery
            // float in empty space without a right kidney. Hide them so only ipsilateral left
            // renal vasculature is shown.
            if (name === 'VH_M_renal_vein_R' || name === 'VH_M_left_renal_artery') {
              mesh.visible = false;
              return;
            }

            // Map node name to canonical structureId
            const mappedId = this.meshToStructureId.get(name);
            if (mappedId) {
              const list = this.structureToMeshes.get(mappedId) || [];
              list.push(mesh);
              this.structureToMeshes.set(mappedId, list);

              // Apply illustrative anatomical material with tuned roughness and muted palette
              const mat = createAnatomicalMaterial(mappedId, name);
              if (name === 'VH_M_outer_cortex_of_kidney_L') {
                mat.side = THREE.DoubleSide;
                mat.clipShadows = true;
              }
              mesh.material = mat;
              this.baseMaterials.set(mesh.uuid, mat);
            }
          }
        });

        this.scene.add(group);
      }

      // Initialize default camera position
      this.applyCameraPreset('KIDNEY_OVERVIEW', false);

      const loadDuration = Math.round(performance.now() - startTime);
      if (this.onLoadComplete) {
        this.onLoadComplete({
          loadTimeMs: loadDuration,
          meshCount: totalMeshes,
          triangleCount: Math.round(totalTriangles),
          vertexCount: Math.round(totalVertices),
          fps: this.currentFps,
        });
      }
    } catch (err) {
      console.error('Failed to load HRA renal assets:', err);
      if (this.onError) {
        this.onError(`Asset loading failed: ${String(err)}`);
      }
    }
  }

  // Pointer Interaction Handlers (Click vs Drag threshold)
  private onPointerDown = (event: MouseEvent): void => {
    this.isPointerDown = true;
    this.pointerDownPos = { x: event.clientX, y: event.clientY };
  };

  private onPointerUp = (event: MouseEvent): void => {
    if (!this.isPointerDown) return;
    this.isPointerDown = false;

    const dx = Math.abs(event.clientX - this.pointerDownPos.x);
    const dy = Math.abs(event.clientY - this.pointerDownPos.y);

    // If movement is under threshold, consider it an intentional physical selection
    if (dx < this.dragThreshold && dy < this.dragThreshold) {
      this.handlePhysicalSelection(event);
    }
  };

  private onPointerMove = (event: MouseEvent): void => {
    // Raycast for hover state
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.scene.children, true);

    let hoveredId: string | null = null;
    for (const hit of intersects) {
      const filtered = filterRaycastHit(hit, {
        surfaceMode: this.surfaceMode,
        isolatedStructureId: this.isolatedStructureId,
        meshToStructureId: this.meshToStructureId,
        structureVisibility: this.structureVisibility,
        clippingPlane: this.isCutawayActive ? this.cutawayPlane : null,
      });

      if (filtered) {
        hoveredId = filtered.structureId;
        break;
      }
    }

    if (hoveredId !== this.hoveredStructureId) {
      this.hoveredStructureId = hoveredId;
      this.updateMaterialStates();
      if (this.onHoverStructure) {
        this.onHoverStructure(hoveredId);
      }
    }
  };

  private handlePhysicalSelection(event: MouseEvent): void {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.scene.children, true);

    for (const hit of intersects) {
      const filtered = filterRaycastHit(hit, {
        surfaceMode: this.surfaceMode,
        isolatedStructureId: this.isolatedStructureId,
        meshToStructureId: this.meshToStructureId,
        structureVisibility: this.structureVisibility,
        clippingPlane: this.isCutawayActive ? this.cutawayPlane : null,
      });

      if (filtered) {
        this.selectStructure(filtered.structureId);
        this.onSelectStructure(filtered.structureId, filtered.mesh.name);
        return;
      }
    }
  }

  // Public Camera Controls
  public applyCameraPreset(presetName: CameraPresetName, smooth = true): void {
    const preset = CAMERA_PRESETS[presetName];
    if (!preset) return;

    if (!smooth || this.reducedMotion) {
      this.camera.fov = preset.fov;
      this.camera.position.copy(preset.position);
      this.controls.target.copy(preset.target);
      this.controls.minDistance = preset.minDistance;
      this.controls.maxDistance = preset.maxDistance;
      this.camera.updateProjectionMatrix();
      this.controls.update();
      return;
    }

    // Initiate smooth interpolation
    this.startCameraPos.copy(this.camera.position);
    this.targetCameraPos.copy(preset.position);
    this.startControlsTarget.copy(this.controls.target);
    this.targetControlsTarget.copy(preset.target);
    this.transitionStartTime = performance.now();
    this.transitionDuration = 550;
    this.isTransitioning = true;
  }

  public focusStructure(structureId: string): void {
    const meshes = this.structureToMeshes.get(structureId);
    if (!meshes || meshes.length === 0) return;

    const box = new THREE.Box3();
    for (const m of meshes) {
      box.expandByObject(m);
    }

    const center = new THREE.Vector3();
    box.getCenter(center);

    // Smooth transition camera target to the structure center
    this.startControlsTarget.copy(this.controls.target);
    this.targetControlsTarget.copy(center);
    this.startCameraPos.copy(this.camera.position);

    // Move camera towards target maintaining reasonable distance
    const offset = this.camera.position.clone().sub(this.controls.target).normalize().multiplyScalar(0.20);
    this.targetCameraPos.copy(center).add(offset);

    this.transitionStartTime = performance.now();
    this.transitionDuration = 500;
    this.isTransitioning = true;
  }

  /**
   * Retrieves the exterior shell meshes that encapsulate the internal renal morphology.
   * Both the outer fibrous capsule (VH_M_kidney_capsule_L) and outer cortical shell
   * (VH_M_outer_cortex_of_kidney_L) form the surface envelope.
   */
  public getOuterShellMeshes(): THREE.Mesh[] {
    const meshes: THREE.Mesh[] = [];
    const capsule = this.structureToMeshes.get('kidney_capsule_left') || [];
    meshes.push(...capsule);
    const outerCortex = this.meshMap.get('VH_M_outer_cortex_of_kidney_L');
    if (outerCortex && !meshes.includes(outerCortex)) {
      meshes.push(outerCortex);
    }
    return meshes;
  }

  public transitionToInternalView(): void {
    this.applyCameraPreset('INTERNAL_CUTAWAY', true);
  }

  /**
   * Retrieves all meshes participating in the cutaway section view:
   * outer cortex, hilum margin collar, renal columns, and medullary pyramids.
   * Applying the cutaway plane to all these structures ensures the section is flush,
   * with no pyramids or hilum margins awkwardly jutting forward into space.
   */
  private getCutawayMeshes(): THREE.Mesh[] {
    const meshes: THREE.Mesh[] = [];
    const outerCortex = this.meshMap.get('VH_M_outer_cortex_of_kidney_L');
    if (outerCortex) meshes.push(outerCortex);
    const hilum = this.meshMap.get('VH_M_hilum_of_kidney_L');
    if (hilum) meshes.push(hilum);
    const column = this.meshMap.get('VH_M_renal_column_L');
    if (column) meshes.push(column);
    const medulla = this.structureToMeshes.get('renal_medulla_left') || [];
    for (const m of medulla) {
      if (!meshes.includes(m)) meshes.push(m);
    }
    return meshes;
  }

  // Surface & Layer Modes
  public setSurfaceMode(mode: SurfacePresentationMode, smooth = true): void {
    this.surfaceMode = mode;
    const isCut = mode === 'CUTAWAY' || mode === 'REVEAL';
    this.isCutawayActive = isCut;

    const cutMeshes = this.getCutawayMeshes();
    const capsuleMeshes = this.structureToMeshes.get('kidney_capsule_left') || [];

    if (isCut) {
      this.applyCameraPreset('INTERNAL_CUTAWAY', smooth);
    } else {
      this.applyCameraPreset('KIDNEY_OVERVIEW', smooth);
    }

    const startConstant = this.cutawayPlane.constant;
    const targetConstant = isCut ? 0.075 : 0.200;

    // Apply clipping planes to all relevant meshes for cutaway presentation
    for (const mesh of cutMeshes) {
      const mat = mesh.material as THREE.MeshPhysicalMaterial;
      if (isCut) {
        mat.clippingPlanes = [this.cutawayPlane];
        mat.clipShadows = true;
        if (mesh.name === 'VH_M_outer_cortex_of_kidney_L') {
          mat.side = THREE.DoubleSide;
        }
      }
    }

    if (!smooth || this.reducedMotion) {
      this.cutawayPlane.constant = targetConstant;
      for (const cap of capsuleMeshes) {
        cap.visible = !isCut;
      }
      if (!isCut) {
        for (const mesh of cutMeshes) {
          const mat = mesh.material as THREE.MeshPhysicalMaterial;
          mat.clippingPlanes = [];
        }
      }
      if (this.fillLight) {
        this.fillLight.intensity = isCut ? 0.88 : 0.70;
      }
      if (this.ambientLight) {
        this.ambientLight.intensity = isCut ? 0.50 : 0.44;
      }
      return;
    }

    // Set initial visibility for transition
    if (isCut) {
      for (const cap of capsuleMeshes) {
        const mat = cap.material as THREE.Material & { opacity?: number; transparent?: boolean };
        mat.transparent = true;
      }
    } else {
      for (const cap of capsuleMeshes) {
        cap.visible = true;
      }
    }

    this.cutawayAnimation = {
      active: true,
      startTime: performance.now(),
      duration: 400,
      startConstant,
      targetConstant,
      onComplete: () => {
        if (isCut) {
          for (const cap of capsuleMeshes) {
            cap.visible = false;
          }
        } else {
          for (const cap of capsuleMeshes) {
            const mat = cap.material as THREE.Material & { transparent?: boolean; opacity?: number };
            mat.transparent = false;
            mat.opacity = 1.0;
          }
          for (const mesh of cutMeshes) {
            const mat = mesh.material as THREE.MeshPhysicalMaterial;
            mat.clippingPlanes = [];
          }
        }
        if (this.fillLight) {
          this.fillLight.intensity = isCut ? 0.88 : 0.70;
        }
        if (this.ambientLight) {
          this.ambientLight.intensity = isCut ? 0.50 : 0.44;
        }
      },
    };
  }

  public setStructureOpacity(structureId: string, opacity: number): void {
    const meshes = this.structureToMeshes.get(structureId);
    if (!meshes) return;
    for (const m of meshes) {
      const mat = m.material as THREE.MeshStandardMaterial;
      mat.transparent = opacity < 1.0;
      mat.opacity = Math.max(0, Math.min(1, opacity));
      mat.depthWrite = opacity > 0.6;
    }
  }

  public isolateStructure(structureId: string | null): void {
    this.isolatedStructureId = structureId;
    this.updateMaterialStates();
  }

  public selectStructure(structureId: string | null): void {
    this.selectedStructureId = structureId;
    this.updateMaterialStates();
    this.updateProjectedAnchor();
  }

  public highlightStructure(structureId: string | null): void {
    this.emphasizedStructureId = structureId;
    this.updateMaterialStates();
    this.updateProjectedAnchor();
  }

  public setGuidedPathwayMode(enabled: boolean, pathwayId = 'f'): void {
    this.isGuidedPathwayMode = enabled;
    this.guidedPathwayId = pathwayId;
    this.updateMaterialStates();
  }

  public getGuidedPathwayMode(): boolean {
    return this.isGuidedPathwayMode;
  }

  public resetScene(): void {
    this.selectedStructureId = null;
    this.hoveredStructureId = null;
    this.emphasizedStructureId = null;
    this.isolatedStructureId = null;
    this.isGuidedPathwayMode = false;
    this.setSurfaceMode('SURFACE');

    for (const [, meshes] of this.structureToMeshes) {
      for (const m of meshes) {
        m.visible = true;
      }
    }

    this.updateMaterialStates();
    this.applyCameraPreset('KIDNEY_OVERVIEW', true);
    if (this.onAnchorUpdate) {
      this.onAnchorUpdate(null);
    }
  }

  /**
   * Updates emissive & opacity states across all structures cleanly without leaking.
   */
  private updateMaterialStates(): void {
    for (const [sid, meshes] of this.structureToMeshes) {
      const isSelected = sid === this.selectedStructureId;
      const isHovered = sid === this.hoveredStructureId && !isSelected;
      const isEmphasized = sid === this.emphasizedStructureId;
      const isIsolated = this.isolatedStructureId !== null;
      const isTargetIsolated = isIsolated && sid === this.isolatedStructureId;

      for (const m of meshes) {
        const mat = m.material as THREE.Material & {
          opacity?: number;
          transparent?: boolean;
          depthWrite?: boolean;
          needsUpdate?: boolean;
          emissive?: THREE.Color;
          emissiveIntensity?: number;
        };

        const prevTransparent = mat.transparent;
        const prevDepthWrite = mat.depthWrite;

        // Selective Guided Pathway Focus (Internal cutaway didactic lesson)
        if (this.isGuidedPathwayMode && !isIsolated) {
          const pathwayNodes = [
            `VH_M_renal_pyramid_L_${this.guidedPathwayId}`,
            `VH_M_renal_papilla_L_${this.guidedPathwayId}`,
            `VH_M_minor_calyx_L_${this.guidedPathwayId}`,
            this.guidedPathwayId === 'f' || this.guidedPathwayId === 'e' ? 'VH_M_major_calyx_L_b' : 'VH_M_major_calyx_L_a',
            'VH_M_renal_pelvis_L',
            'VH_M_ureter_L',
          ];

          const isPathwayNode = pathwayNodes.includes(m.name);

          if (isPathwayNode) {
            // PRIMARY: Representative collecting pathway (100% opaque, sharp, prominent)
            mat.opacity = 1.0;
            mat.transparent = false;
            mat.depthWrite = true;
          } else if (m.name === 'VH_M_outer_cortex_of_kidney_L') {
            // SECONDARY: Retained posterior cortical bed for anatomical context
            mat.opacity = 0.85;
            mat.transparent = true;
            mat.depthWrite = true;
          } else if (sid === 'kidney_capsule_left') {
            // Capsule hidden in cutaway
            mat.opacity = 0.0;
            mat.transparent = true;
            mat.depthWrite = false;
          } else if (sid === 'renal_vein_left' || sid === 'renal_artery_left') {
            // TERTIARY: Soft translucent vessels (in-situ landmark without occluding pelvis)
            mat.opacity = 0.16;
            mat.transparent = true;
            mat.depthWrite = false;
          } else {
            // TERTIARY: Non-pathway pyramids, papillae, calyces, columns de-emphasized
            mat.opacity = 0.10;
            mat.transparent = true;
            mat.depthWrite = false;
          }

          // Subtle pathway illumination
          if (mat.emissive && !isEmphasized && !isSelected && !isHovered) {
            if (isPathwayNode) {
              if (m.name.includes('pyramid') || m.name.includes('papilla')) {
                mat.emissive.setHex(0x3a1410);
                mat.emissiveIntensity = 0.30;
              } else {
                mat.emissive.setHex(0x221c14);
                mat.emissiveIntensity = 0.18;
              }
            } else {
              mat.emissive.setHex(0x000000);
              mat.emissiveIntensity = 0.0;
            }
          }
        } else if (isIsolated) {
          if (isTargetIsolated) {
            mat.opacity = 1.0;
            mat.transparent = false;
            mat.depthWrite = true;
          } else {
            mat.opacity = 0.12;
            mat.transparent = true;
            mat.depthWrite = false;
          }
        } else if (
          (this.surfaceMode === 'CUTAWAY' || this.surfaceMode === 'REVEAL') &&
          sid === 'kidney_capsule_left'
        ) {
          // In Cutaway mode, capsule is hidden leaving the continuous cortical shell wall
          mat.opacity = 0.0;
          mat.transparent = true;
          mat.depthWrite = false;
        } else {
          mat.opacity = 1.0;
          mat.transparent = false;
          mat.depthWrite = true;
        }

        if (mat.transparent !== prevTransparent || mat.depthWrite !== prevDepthWrite) {
          mat.needsUpdate = true;
        }

        // Emissive state priority: Emphasized/Tutor > Selected > Hover
        // Restrained clinical highlights that preserve anatomical base color
        if (mat.emissive) {
          if (isEmphasized) {
            mat.emissive.setHex(HIGHLIGHT_COLORS.TUTOR_PULSE);
            mat.emissiveIntensity = 0.38;
          } else if (isSelected) {
            mat.emissive.setHex(HIGHLIGHT_COLORS.SELECTED);
            mat.emissiveIntensity = 0.32;
          } else if (isHovered) {
            mat.emissive.setHex(HIGHLIGHT_COLORS.HOVER);
            mat.emissiveIntensity = 0.12;
          } else if (!this.isGuidedPathwayMode) {
            mat.emissive.setHex(0x000000);
            mat.emissiveIntensity = 0.0;
          }
        }
      }
    }
  }

  /**
   * Computes screen-space 2D coordinates for the active structure to position sparse DOM labels.
   */
  private updateProjectedAnchor(): void {
    if (!this.onAnchorUpdate) return;
    const activeId = this.selectedStructureId || this.emphasizedStructureId;
    if (!activeId) {
      this.onAnchorUpdate(null);
      return;
    }

    const meshes = this.structureToMeshes.get(activeId);
    if (!meshes || meshes.length === 0) {
      this.onAnchorUpdate(null);
      return;
    }

    const box = new THREE.Box3();
    for (const m of meshes) {
      box.expandByObject(m);
    }

    const center = new THREE.Vector3();
    box.getCenter(center);

    // Project world coordinate to normalized device coordinates [-1, 1]
    const projected = center.clone().project(this.camera);

    // If point is behind camera, hide anchor
    if (projected.z > 1.0) {
      this.onAnchorUpdate(null);
      return;
    }

    const rect = this.renderer.domElement.getBoundingClientRect();
    const screenX = ((projected.x + 1) / 2) * rect.width;
    const screenY = ((-projected.y + 1) / 2) * rect.height;

    this.onAnchorUpdate({
      structureId: activeId,
      screenX,
      screenY,
      visible: true,
    });
  }

  // Action Dispatcher for Validated Scene Actions
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

      case 'SET_STRUCTURE_OPACITY':
        if (sid && action.opacity !== undefined && action.opacity !== null) {
          this.setStructureOpacity(sid, action.opacity);
        }
        break;

      case 'SHOW_STRUCTURE':
        if (sid) {
          this.structureVisibility.set(sid, true);
          const meshes = this.structureToMeshes.get(sid) || [];
          for (const m of meshes) m.visible = true;
        }
        break;

      case 'HIDE_STRUCTURE':
        if (sid) {
          this.structureVisibility.set(sid, false);
          const meshes = this.structureToMeshes.get(sid) || [];
          for (const m of meshes) m.visible = false;
        }
        break;

      case 'SHOW_RELATION':
        if (sid) {
          this.setSurfaceMode('REVEAL');
          this.highlightStructure(sid);
        }
        break;
    }
  }

  // Animation & Rendering Loop
  private animate = (): void => {
    this.animationFrameId = requestAnimationFrame(this.animate);

    // Handle smooth camera interpolation
    if (this.isTransitioning) {
      const elapsed = performance.now() - this.transitionStartTime;
      const t = Math.min(1.0, elapsed / this.transitionDuration);
      // Smooth cubic ease-out
      const ease = 1 - Math.pow(1 - t, 3);

      this.camera.position.lerpVectors(this.startCameraPos, this.targetCameraPos, ease);
      this.controls.target.lerpVectors(this.startControlsTarget, this.targetControlsTarget, ease);

      if (t >= 1.0) {
        this.isTransitioning = false;
      }
    }

    // Handle cutaway plane animation (Surface <-> Cutaway)
    if (this.cutawayAnimation && this.cutawayAnimation.active) {
      const elapsed = performance.now() - this.cutawayAnimation.startTime;
      const t = Math.min(1.0, elapsed / this.cutawayAnimation.duration);
      // Smooth cubic ease-out
      const ease = 1 - Math.pow(1 - t, 3);
      this.cutawayPlane.constant =
        this.cutawayAnimation.startConstant +
        (this.cutawayAnimation.targetConstant - this.cutawayAnimation.startConstant) * ease;

      const isCut = this.surfaceMode === 'CUTAWAY' || this.surfaceMode === 'REVEAL';
      const capsuleMeshes = this.structureToMeshes.get('kidney_capsule_left') || [];
      for (const cap of capsuleMeshes) {
        const mat = cap.material as THREE.Material & { opacity?: number; transparent?: boolean };
        mat.transparent = true;
        mat.opacity = isCut ? Math.max(0, 1.0 - ease) : Math.min(1, ease);
      }

      if (t >= 1.0) {
        this.cutawayAnimation.active = false;
        if (this.cutawayAnimation.onComplete) {
          this.cutawayAnimation.onComplete();
        }
      }
    }

    this.controls.update();
    this.renderer.render(this.scene, this.camera);

    // Periodically update DOM anchor projection
    if (this.selectedStructureId || this.emphasizedStructureId) {
      this.updateProjectedAnchor();
    }

    // Telemetry calculation
    this.frameCount++;
    const now = performance.now();
    if (now - this.lastFpsTime >= 1000) {
      this.currentFps = Math.round((this.frameCount * 1000) / (now - this.lastFpsTime));
      this.frameCount = 0;
      this.lastFpsTime = now;
    }
  };

  private onWindowResize = (): void => {
    if (!this.container) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  };

  public dispose(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
    }

    if (this.envTexture) {
      this.envTexture.dispose();
      this.envTexture = null;
    }

    this.renderer.domElement.removeEventListener('pointerdown', this.onPointerDown);
    this.renderer.domElement.removeEventListener('pointerup', this.onPointerUp);
    this.renderer.domElement.removeEventListener('pointermove', this.onPointerMove);
    window.removeEventListener('resize', this.onWindowResize);

    this.controls.dispose();
    this.renderer.dispose();

    if (this.renderer.domElement && this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
  }
}
