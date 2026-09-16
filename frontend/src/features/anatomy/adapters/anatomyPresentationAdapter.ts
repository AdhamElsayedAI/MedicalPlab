import {
  AnatomyManifest,
  AnatomySession,
  AnatomyStructure,
  LessonState,
} from '../../../lib/anatomy/types';

export type LearningMode = 'EXPLORE' | 'GUIDED_LESSON' | 'CHALLENGE';

export interface StructurePresentation {
  structureId: string;
  displayName: string;
  category: 'vessel' | 'capsule' | 'parenchyma' | 'collecting_system';
  shortDescription: string;
  clinicalRelevance: string;
  ontologyId: string;
  meshNodeNames: string[];
  relationships: Array<{ type: string; target: string }>;
  sourceSystem: string;
}

const DESCRIPTIONS: Record<string, { desc: string; clinical: string; category: StructurePresentation['category'] }> = {
  kidney_capsule_left: {
    desc: 'Dense, fibrous connective tissue envelope enclosing and protecting the renal parenchyma from trauma.',
    clinical: 'Non-distensible; acute renal swelling (e.g. acute pyelonephritis) stretches the capsule, causing severe costovertebral flank pain.',
    category: 'capsule',
  },
  renal_artery_left: {
    desc: 'Major vascular trunk branching laterally from the abdominal aorta at L1–L2 to supply oxygenated blood to the left kidney.',
    clinical: 'Left renal artery is shorter than the right; divides into anterior and posterior segmental arteries before entering parenchyma.',
    category: 'vessel',
  },
  renal_vein_left: {
    desc: 'Large venous trunk draining deoxygenated blood from the left kidney across the aorta to the inferior vena cava (IVC).',
    clinical: 'Longer than right renal vein; passes anterior to abdominal aorta and posterior to SMA (susceptible to Nutcracker syndrome).',
    category: 'vessel',
  },
  renal_pelvis_left: {
    desc: 'Funnel-shaped superior expansion of the ureter that collects urine from the major calyces at the renal hilum.',
    clinical: 'Forms the pelviureteric junction (PUJ), a primary clinical site for congenital stenosis or nephrolithiasis impaction.',
    category: 'collecting_system',
  },
  ureter_left: {
    desc: 'Muscular conduit that propels urine from the renal pelvis to the urinary bladder via rhythmic peristalsis.',
    clinical: 'Crosses over the common/external iliac vessels; common site of ureteric colic from calculus obstruction.',
    category: 'collecting_system',
  },
  renal_cortex_left: {
    desc: 'Outer layer of the renal parenchyma containing glomeruli, convoluted tubules, and cortical collecting ducts.',
    clinical: 'Site of ultrafiltration and primary target in glomerulonephritis and acute cortical necrosis.',
    category: 'parenchyma',
  },
  renal_medulla_left: {
    desc: 'Inner renal region organized into renal pyramids containing loops of Henle and collecting tubules.',
    clinical: 'Crucial for hyperosmolar urine concentration; prone to papillary necrosis in sickle cell disease or NSAID nephropathy.',
    category: 'parenchyma',
  },
};

export function adaptStructure(struct: AnatomyStructure): StructurePresentation {
  const meta = DESCRIPTIONS[struct.structure_id] || {
    desc: struct.display_name,
    clinical: 'Integral component of the renal functional unit.',
    category: 'parenchyma' as const,
  };

  return {
    structureId: struct.structure_id,
    displayName: struct.display_name,
    category: meta.category,
    shortDescription: meta.desc,
    clinicalRelevance: meta.clinical,
    ontologyId: struct.ontology_id,
    meshNodeNames: struct.mesh_node_names,
    relationships: struct.relationships || [],
    sourceSystem: struct.source_system,
  };
}

export function determineInitialLearningMode(session: AnatomySession | null): LearningMode {
  if (!session) return 'GUIDED_LESSON';
  if (session.challenge_state === 'ACTIVE' || session.lesson_state === 'CHALLENGE_ACTIVE') {
    return 'CHALLENGE';
  }
  return 'GUIDED_LESSON';
}

export function isChallengeReady(session: AnatomySession | null): boolean {
  if (!session) return false;
  return (
    session.lesson_state === 'CHALLENGE_READY' ||
    session.lesson_state === 'CHALLENGE_ACTIVE' ||
    session.lesson_state === 'COMPLETED'
  );
}

export function formatRelationshipSummary(relationships?: Array<{ type: string; target: string }>): string[] {
  if (!relationships || relationships.length === 0) return [];
  return relationships.map((rel) => {
    const cleanTarget = rel.target.replace(/_/g, ' ');
    switch (rel.type.toUpperCase()) {
      case 'BRANCH_OF':
        return `Branches from ${cleanTarget}`;
      case 'DRAINS_INTO':
        return `Drains into ${cleanTarget}`;
      case 'CONTINUOUS_WITH':
        return `Continuous with ${cleanTarget}`;
      case 'LOCATED_IN':
        return `Located in ${cleanTarget}`;
      case 'SURROUNDS':
        return `Surrounds ${cleanTarget}`;
      default:
        return `${rel.type.toLowerCase()} ${cleanTarget}`;
    }
  });
}
