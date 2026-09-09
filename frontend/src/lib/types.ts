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
  | "battle"
  | "validation"
  | "grand_championship"
  | "global_intelligence"
  | "startup_execution";




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

/** Student-safe API contract. It deliberately cannot contain answers or explanations. */
export interface PLABQuestionPublic {
  question_id: string;
  stem: string;
  options: { id: "A" | "B" | "C" | "D" | "E"; text: string }[];
  topic: string;
  specialty?: string;
  difficulty: "easy" | "medium" | "hard";
  question_version: number;
  content_mode: "GOLDEN" | "PREVIEW_QA";
  warning: string | null;
}

export interface PLABEvaluationResult {
  attempt_id: string;
  correct: boolean;
  selected_answer: "A" | "B" | "C" | "D" | "E";
  correct_answer: "A" | "B" | "C" | "D" | "E";
  explanation: string;
  citations: { document_id: string; reference: string }[];
  topic: string;
  learning_feedback: string;
  question_version: number;
  content_mode: "GOLDEN" | "PREVIEW_QA";
}

export interface PLABProgress {
  user_id: string;
  question_count: number;
  total_attempts?: number;
  correct_attempts?: number;
  overall_accuracy: number | null;
  recent_accuracy: number | null;
  first_attempt_accuracy?: number | null;
  question_completion?: number;
  topic_accuracy: Record<string, number>;
  weak_topics: string[];
  strongest_topics: string[];
  mastery_model: "descriptive_attempt_metrics";
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

// ===================================================
// STAGE-M: REAL-WORLD VALIDATION & IMPACT LAYER
// ===================================================

export type ValidationSubTab =
  | "journey"
  | "outcomes"
  | "institution"
  | "roi"
  | "story"
  | "defense"
  | "safe_mode";

export type MetricComplianceBadge =
  | "[Demo Simulation]"
  | "[Prototype Projection]"
  | "[Future Target]";

export interface JourneyPhase {
  id: number;
  phaseNumber: number;
  phaseTitle: string;
  userState: {
    persona: string;
    clinicalConfidence: string;
    diagnosticScore: number;
    errorState: string;
    sentiment: string;
  };
  aiAction: {
    stage: string;
    algorithm: string;
    intervention: string;
    runtimeLatency: string;
  };
  medicalObjective: {
    condition: string;
    guidelineRef: string;
    learningGoal: string;
    safetyRule: string;
  };
  visualTransition: {
    fromColor: string;
    toColor: string;
    animationKey: string;
    hudBadge: string;
  };
}

export interface OutcomeMetricItem {
  id: string;
  metricName: string;
  category: "Clinical Safety" | "Exam Performance" | "Study Efficiency" | "Knowledge Retention";
  legacyBaseline: string;
  medicalPlabValue: string;
  deltaGain: string;
  isPositive: boolean;
  complianceBadge: MetricComplianceBadge;
  calculationSource: string;
  clinicalImpactSummary: string;
}

export interface InstitutionCohortAnalytics {
  deaneryName: string;
  activeCandidates: number;
  examReadyPct: number;
  developingPct: number;
  criticalRemediationPct: number;
  averageStudyHours: number;
  highRiskTopics: {
    topic: string;
    failureRate: number;
    guidelineRef: string;
    suggestedIntervention: string;
  }[];
  curriculumRecommendations: {
    priority: "HIGH" | "MEDIUM" | "ROUTINE";
    title: string;
    targetCandidates: number;
    actionPlan: string;
  }[];
  engagementIndicators: {
    dailyActivePct: number;
    avgSimulationsPerUser: number;
    tutorQuestionsLogged: number;
    safetyIncidentsIntercepted: number;
  };
}

export interface ImpactStoryItem {
  id: string;
  dimension: "Student Transformation" | "Clinical Safety Interception" | "Institutional Scaling";
  title: string;
  heroQuote: string;
  protagonist: string;
  clinicalContext: string;
  crisisProblem: string;
  medicalPlabIntervention: string;
  expectedOutcome: string;
  complianceBadge: MetricComplianceBadge;
  outcomeStats: { label: string; value: string }[];
}

export interface JudgeImpactDefenseItem {
  id: string;
  question: string;
  founderResponse: string;
  technicalExplanation: string;
  honestLimitation: string;
  futureValidationRoadmap: string;
  complianceBadge: MetricComplianceBadge;
}




