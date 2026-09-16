import * as THREE from 'three';

export interface AnatomicalMaterialConfig {
  color: number;
  roughness: number;
  metalness: number;
  sheen?: number;
  sheenColor?: number;
  sheenRoughness?: number;
  transparent?: boolean;
  opacity?: number;
}

/**
 * Natural medical atlas palette for Renal Anatomy.
 * Calibrated against standard verified anatomical references (Netter, Gray's, BioDigital).
 * Colors are muted, believable, and grounded in biological tissue appearance:
 * - Kidney exterior: Natural muted renal red / warm parenchyma tone
 * - Cortex: Slightly lighter differentiated tissue rose
 * - Medulla / Pyramids: Deep red-brown tone
 * - Artery: Muted arterial crimson
 * - Vein: Desaturated venous slate-blue (never electric cyan/blue)
 * - Pelvis / Calyces / Ureter: Warm ivory / tissue cream
 * - Hilum: Neutral anatomical warm grey/beige
 *
 * PBR Principles:
 * - metalness = 0.0 across all soft tissue
 * - zero transmission, zero clearcoat, no synthetic wet gloss
 * - diffuse form defined by geometry, soft shading, and conservative tissue sheen
 */
export const ANATOMICAL_PALETTE: Record<string, AnatomicalMaterialConfig> = {
  // Kidney fibrous capsule: natural muted renal red / warm living tissue tone
  kidney_capsule_left: {
    color: 0xa04b47,
    roughness: 0.68,
    metalness: 0.0,
    sheen: 0.20,
    sheenColor: 0xb5635e,
    sheenRoughness: 0.70,
    transparent: true,
    opacity: 1.0,
  },

  // Outer renal cortex & columns: slightly lighter differentiated renal tissue
  renal_cortex_left: {
    color: 0xb25852,
    roughness: 0.70,
    metalness: 0.0,
    sheen: 0.20,
    sheenColor: 0xc5736e,
    sheenRoughness: 0.70,
  },

  // Medullary pyramids: deep red-brown striated medullary tone
  renal_medulla_left: {
    color: 0x6e2622,
    roughness: 0.68,
    metalness: 0.0,
    sheen: 0.16,
    sheenColor: 0x85322e,
    sheenRoughness: 0.65,
  },

  // Renal artery: natural educational arterial crimson (muscular wall tone, not plastic red)
  renal_artery_left: {
    color: 0xa82d2b,
    roughness: 0.64,
    metalness: 0.0,
    sheen: 0.15,
    sheenColor: 0xc44543,
  },

  // Renal vein: desaturated anatomical venous slate-blue (restrained, does NOT overpower the kidney)
  renal_vein_left: {
    color: 0x385777,
    roughness: 0.66,
    metalness: 0.0,
    sheen: 0.14,
    sheenColor: 0x4d7196,
  },

  // Renal pelvis: clear, defined collecting-system ivory funnel
  renal_pelvis_left: {
    color: 0xd8ccb0,
    roughness: 0.60,
    metalness: 0.0,
    sheen: 0.15,
    sheenColor: 0xebd9b4,
  },

  // Descending ureter: continuous with pelvis, matching ivory tone
  ureter_left: {
    color: 0xdcd0b6,
    roughness: 0.64,
    metalness: 0.0,
    sheen: 0.14,
    sheenColor: 0xe6dcce,
  },

  // Renal hilum connective margin: tissue-related neutral tone (eliminates harsh grey/beige ring)
  hilum_of_kidney_left: {
    color: 0xa85650,
    roughness: 0.72,
    metalness: 0.0,
  },
};

export const HIGHLIGHT_COLORS = {
  HOVER: 0xffffff,
  SELECTED: 0xf59e0b,      // Warm amber emphasis
  TUTOR_PULSE: 0x06b6d4,   // Clinical teal emphasis
  CORRECT: 0x10b981,       // Medical emerald
  INCORRECT: 0xf43f5e,     // Rose
};

/**
 * Creates an authentic educational MeshPhysicalMaterial for a given anatomical structure.
 * Strictly avoids synthetic procedural textures, bumps, or fake microscopic morphology.
 * Form is derived entirely from verified geometry, diffuse wrap, and soft biological sheen.
 */
export function createAnatomicalMaterial(
  structureId: string,
  nodeName: string
): THREE.MeshPhysicalMaterial {
  const config = ANATOMICAL_PALETTE[structureId] || {
    color: 0x94a3b8,
    roughness: 0.68,
    metalness: 0.0,
  };

  let finalColor = config.color;
  let finalRoughness = config.roughness;
  let finalSheen = config.sheen ?? 0.0;
  let finalSheenColor = config.sheenColor;

  // Granular anatomical sub-component hierarchy for clear didactic readability:
  if (nodeName.includes('renal_papilla')) {
    // 3. Papillae: slightly differentiated transitional medullary tone entering minor calyx
    finalColor = 0x8e423d;
    finalRoughness = 0.64;
    finalSheen = 0.18;
    finalSheenColor = 0xa4524c;
  } else if (nodeName.includes('minor_calyx')) {
    // 4. Minor calyces: warm cream / light ochre cupping each papilla
    finalColor = 0xede4cd;
    finalRoughness = 0.56;
    finalSheen = 0.18;
    finalSheenColor = 0xdfd4bc;
  } else if (nodeName.includes('major_calyx')) {
    // 5. Major calyces: warm cream infundibula converging into renal pelvis
    finalColor = 0xe4d9c0;
    finalRoughness = 0.58;
    finalSheen = 0.16;
    finalSheenColor = 0xd8cca8;
  } else if (nodeName.includes('renal_pelvis')) {
    // 6. Renal pelvis: clear, defined collecting-system ivory funnel
    finalColor = 0xd8ccb0;
    finalRoughness = 0.60;
    finalSheen = 0.15;
    finalSheenColor = 0xebd9b4;
  } else if (nodeName.includes('ureter')) {
    // 7. Ureter: continuous with pelvis, matching ivory tone
    finalColor = 0xdcd0b6;
    finalRoughness = 0.64;
    finalSheen = 0.14;
    finalSheenColor = 0xe6dcce;
  } else if (nodeName.includes('renal_pyramid')) {
    // 2. Medullary pyramids: deep warm red-brown
    finalColor = 0x6e2622;
    finalRoughness = 0.68;
    finalSheen = 0.16;
    finalSheenColor = 0x85322e;
  } else if (nodeName.includes('renal_column')) {
    // Renal columns of Bertin: cortical tissue running between pyramids
    finalColor = 0xaf554f;
    finalRoughness = 0.70;
  } else if (nodeName.includes('hilum_of_kidney')) {
    // Presentation section boundary around hilum: tissue-related neutral tone, no harsh grey
    finalColor = 0xa85650;
    finalRoughness = 0.72;
  }

  const mat = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(finalColor),
    roughness: finalRoughness,
    metalness: 0.0,
    sheen: finalSheen,
    sheenColor: finalSheenColor ? new THREE.Color(finalSheenColor) : undefined,
    transparent: true,
    opacity: config.opacity ?? 1.0,
    depthWrite: !(config.transparent && (config.opacity ?? 1.0) < 0.6),
  });

  return mat;
}
