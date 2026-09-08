export type UserRole = "STUDENT" | "DOCTOR" | "INSTITUTION_ADMIN";

export type NavigationMode =
  | "landing"
  | "anatomy"
  | "tutor"
  | "quiz"
  | "simulation"
  | "command_center"
  | "admin"
  | "investor"
  | "founder";


export interface OrganHotspot {
  id: string;
  name: string;
  position: [number, number, number];
  clinicalSignificance: string;
  relatedCondition: string;
  recommendedTutorQuery: string;
  highYieldMcqId: string;
  niceGuidelineRef: string;
}

export interface AnatomicalSystem {
  id: string;
  name: string;
  description: string;
  hotspots: OrganHotspot[];
  clinicalFocus: string;
}

export interface EvidenceCitation {
  ref: string;
  guideline: string;
  section: string;
  quote: string;
  confidence: number;
  status: "supported" | "partial" | "unsupported";
}

export interface ChatMessage {
  id: string;
  sender: "user" | "ai" | "system";
  content: string;
  timestamp: string;
  intent?: string;
  confidenceScore?: number;
  citations?: EvidenceCitation[];
  safetyValidated?: boolean;
  suggestedActions?: string[];
}

export interface PLABQuestion {
  id: string;
  topic: string;
  specialty: string;
  vignette: string;
  options: {
    key: string;
    text: string;
    isCorrect: boolean;
    eliminationRationale: string;
  }[];
  explanation: string;
  evidenceRef: string;
  difficulty: "Novice" | "Developing" | "Competent" | "Mastery";
}

export interface PatientCase {
  id: string;
  title: string;
  patient: {
    name: string;
    age: number;
    gender: string;
    occupation: string;
    presentingComplaint: string;
    onset: string;
    pastHistory: string[];
    allergies: string[];
    medications: string[];
  };
  vitals: {
    heartRate: number;
    bloodPressure: string;
    oxygenSat: number;
    respiratoryRate: number;
    temperature: number;
    ecgRhythm: "Sinus Tachycardia" | "ST-Elevation (V1-V4)" | "Atrial Fibrillation" | "Sinus Bradycardia";
  };
  symptomsTimeline: {
    time: string;
    event: string;
    severity: "low" | "moderate" | "critical";
  }[];
  criticalContraindications: string[];
  availableInterventions: {
    id: string;
    name: string;
    type: "investigation" | "medication" | "procedure" | "referral";
    isContraindicated?: boolean;
    contraindicationReason?: string;
    isOptimal?: boolean;
    aiFeedback: string;
  }[];
}

export interface StudentMasteryProfile {
  studentId: string;
  studentName: string;
  overallAccuracy: number;
  masteryLevel: "NOVICE" | "DEVELOPING" | "COMPETENT" | "MASTERY";
  totalAttempts: number;
  specialtyMastery: {
    specialty: string;
    accuracy: number;
    status: "strong" | "neutral" | "weak";
  }[];
  weakTopics: string[];
  activeRecommendations: {
    id: string;
    title: string;
    reason: string;
    priority: "HIGH" | "MEDIUM" | "LOW";
    actionType: NavigationMode;
  }[];
}

export interface PipelineStageInfo {
  id: string;
  name: string;
  code: string;
  purpose: string;
  status: "ONLINE" | "FROZEN_SECURE";
  latencyMs: number;
  inputContract: string;
  outputContract: string;
}

// ==========================================
// STAGE-J: FOUNDER MODE & COMPETITION LAYER
// ==========================================

export type MetricLabel = "Verified metric" | "Demo projection" | "Future target";

export interface PitchMetric {
  label: string;
  value: string;
  tag: MetricLabel;
  detail: string;
}

export interface PitchSlide {
  id: number;
  title: string;
  subtitle: string;
  category: "Problem" | "Solution" | "Product" | "Market" | "Business" | "Vision";
  bulletPoints: string[];
  metrics: PitchMetric[];
  speakerNotes: string;
  targetDurationSeconds: number;
}

export interface JudgeQAItem {
  id: string;
  category: "Technical" | "Business";
  question: string;
  tags: string[];
  executiveSummary: string; // 20-40s crisp spoken response in confident founder voice
  technicalDeepDive: {
    architecture: string;
    activeStages: string[];
    proofMetric: string;
    codeContractOrLogic: string;
  };
  sampleJudgeFollowUp: string;
  followUpDefense: string;
}

export interface CompetitiveDimension {
  dimension: string;
  description: string;
  genericAI: { status: "fail" | "partial" | "pass"; details: string };
  traditionalBanks: { status: "fail" | "partial" | "pass"; details: string };
  medicalPlab: { status: "pass"; details: string };
}

export interface PreloadedDemoScenario {
  id: string;
  name: string;
  condition: string;
  system: string;
  vitals: { hr: number; bp: string; spo2: number; rr: number; ecg: string };
  interventions: { name: string; safe: boolean; feedback: string }[];
  evidenceCitations: { source: string; quote: string; verified: boolean }[];
}

export type FounderSubTab =
  | "pitch"
  | "judge_qa"
  | "demo_controller"
  | "competitive"
  | "business"
  | "telemetry";

