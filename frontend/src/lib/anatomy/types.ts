/**
 * TypeScript types and action contracts for MedicalPlab 3D Anatomy Lab.
 */

export type AnatomyActionType =
  | 'FOCUS_STRUCTURE'
  | 'HIGHLIGHT_STRUCTURE'
  | 'ISOLATE_STRUCTURE'
  | 'SHOW_STRUCTURE'
  | 'HIDE_STRUCTURE'
  | 'SHOW_RELATION'
  | 'SET_STRUCTURE_OPACITY'
  | 'RESET_SCENE';

export interface SceneAction {
  action: AnatomyActionType;
  structure_id?: string | null;
  opacity?: number | null;
  duration_ms?: number | null;
}

export type InteractionRequestType = 'IDENTIFY_STRUCTURE' | 'EXPLORE_SCENE';

export interface InteractionRequest {
  type: InteractionRequestType;
  target_structure_id?: string | null;
  prompt: string;
}

export interface AnatomyStructure {
  structure_id: string;
  display_name: string;
  source_system: string;
  source_structure_id: string;
  ontology_id: string;
  mesh_node_names: string[];
  aliases?: string[];
  region?: string;
  relationships?: Array<{ type: string; target: string }>;
  learning_objectives?: string[];
  evidence_refs?: string[];
  fma_crosswalk?: string | null;
}

export type LessonState =
  | 'INTRO'
  | 'GUIDED_VESSELS'
  | 'GUIDED_IDENTIFICATION'
  | 'CHALLENGE_READY'
  | 'CHALLENGE_ACTIVE'
  | 'COMPLETED';

export type ChallengeResult = 'PENDING' | 'CORRECT' | 'INCORRECT';

export interface AnatomySession {
  session_id: string;
  learner_id: string;
  learning_objective: string;
  lesson_state: LessonState;
  current_target_structure_id?: string | null;
  selected_structure_ids: string[];
  hint_level: number;
  challenge_state: string;
  challenge_result?: ChallengeResult | null;
  created_at: number;
  updated_at: number;
}

export interface AnatomyAgentResponse {
  tutor_message: string;
  scene_actions: SceneAction[];
  interaction_request?: InteractionRequest | null;
  fallback_applied?: boolean;
}

export interface AnatomyManifest {
  structures: AnatomyStructure[];
  provenance: {
    dataset: string;
    license: string;
    attribution: string;
    version: string;
    coordinate_framework: string;
    verified_assets: string[];
  };
  learning_objectives: string[];
}
