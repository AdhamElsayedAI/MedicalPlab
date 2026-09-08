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
  | "founder"
  | "championship"
  | "battle";




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

// ===================================================
// STAGE-K: CHAMPIONSHIP & SUBMISSION INTELLIGENCE
// ===================================================

export type ChampionshipSubTab =
  | "demo_engine"
  | "founder_narrative"
  | "judge_attack"
  | "submission"
  | "impact_story"
  | "safety_showcase"
  | "reliability";

export interface ChampionshipScene {
  id: number;
  title: string;
  stageBadge: string;
  durationSeconds: number;
  targetMode: NavigationMode;
  keyMessage: string;
  spokenScript: string;
  transitionInstruction: string;
  presenterAction: string;
  screenAction: string;
  judgeTakeaway: string;
  fallbackState: string;
}

export interface JudgeAttackItem {
  id: string;
  category: "Technical" | "Business" | "Clinical Safety";
  question: string;
  hiddenJudgeConcern: string;
  founderAnswer: string;
  technicalProof: {
    stages: string[];
    metric: string;
    mechanism: string;
    contractOrCode: string;
  };
  followUpDefense: string;
}

export interface SubmissionSection {
  id: string;
  title: string;
  summary: string;
  contentMarkdown: string;
}

export interface SubmissionChecklistItem {
  id: string;
  criteria: string;
  proofInProduct: string;
  isVerified: boolean;
}

export interface ImpactComparisonDimension {
  dimension: string;
  traditionalWay: {
    title: string;
    description: string;
    painPoint: string;
  };
  medicalPlabWay: {
    title: string;
    description: string;
    clinicalAdvantage: string;
  };
  deltaImpact: string;
}

// ===================================================
// STAGE-L: FINAL BATTLE & JUDGE MASTERY LAYER
// ===================================================

export type BattleSubTab =
  | "demo_master"
  | "pitch_trainer"
  | "judge_arena"
  | "judge_panel"
  | "founder_coach"
  | "defense_library"
  | "failure_drills"
  | "submission_pro"
  | "presentation_analytics"
  | "safe_mode";

export interface BattleScene {
  id: number;
  title: string;
  stageBadge: string;
  durationSeconds: number;
  targetMode: NavigationMode;
  speakerScript: string;
  screenAction: string;
  judgeTakeaway: string;
  backupState: string;
}

export interface JudgeMemoryItem {
  id: string;
  category: "Basic" | "Technical" | "Business" | "Clinical Safety";
  question: string;
  hiddenJudgeConcern: string;
  winningFounderAnswer: string;
  technicalProof: {
    stages: string[];
    metric: string;
    mechanism: string;
    codeContract: string;
  };
  evaluationCriteria: string[];
  commonWeakAnswers: string[];
  winningAnswerStructure: string[];
  mistakesToAvoid: string[];
  followUpDefense: string;
}

export interface SimulatedJudgeProfile {
  id: string;
  name: string;
  role: "Medical Judge" | "AI Systems Judge" | "Investor Judge";
  title: string;
  focusArea: string;
  score: number;
  verdict: "STRONG ADVANCE" | "GRAND CHAMPION" | "SERIES SEED READY";
  critiqueQuote: string;
  standoutPraise: string;
  criteriaScores: {
    category: string;
    score: number;
    feedback: string;
  }[];
}

export interface FailureDrillScenario {
  id: string;
  title: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  symptom: string;
  underlyingCause: string;
  instantRecoveryAction: string;
  recoveryCodeOrKey: string;
}

export interface CoachAuditPoint {
  area: "Pitch Weakness" | "Timing Bottleneck" | "Business Proof" | "Technical Balance";
  observation: string;
  coachingAdvice: string;
  status: "OPTIMIZED" | "RESOLVED";
}

export interface DefenseTopic {
  id: string;
  title: string;
  category: "AI Technology" | "Clinical Safety" | "Business & Scale";
  summary: string;
  architecturalDetails: string[];
  keyQuotesOrFormulas: string;
  counterPunch: string;
}



