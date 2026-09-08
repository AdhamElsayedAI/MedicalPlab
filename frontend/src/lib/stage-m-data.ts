import {
  JourneyPhase,
  OutcomeMetricItem,
  InstitutionCohortAnalytics,
  ImpactStoryItem,
  JudgeImpactDefenseItem,
} from "./types";

// =========================================================================
// 1. STUDENT JOURNEY SIMULATOR (4-Phase Transformation)
// =========================================================================

export const JOURNEY_PHASES: JourneyPhase[] = [
  {
    id: 1,
    phaseNumber: 1,
    phaseTitle: "Baseline Diagnostic Assessment",
    userState: {
      persona: "Dr. Tariq Al-Mansoor (International Medical Graduate - IMG)",
      clinicalConfidence: "Low (Anxious / 42% PLAB 1 Mock Readiness)",
      diagnosticScore: 54,
      errorState: "Administered nitrates to right-ventricular inferior STEMI (Hypotension risk)",
      sentiment: "Overwhelmed by rote memorization in traditional 2D question banks",
    },
    aiAction: {
      stage: "Stage-F & Stage-C Diagnostic Engine",
      algorithm: "Adaptive Item Response Theory (IRT) + Distractor Error Profiling",
      intervention: "Captured hemodynamic diagnostic blindspot and misattribution of ECG leads V3R-V4R",
      runtimeLatency: "38ms (Deterministic Local Scoring)",
    },
    medicalObjective: {
      condition: "Acute Coronary Syndrome & Right Ventricular Myocardial Infarction",
      guidelineRef: "NICE Guideline NG185 (Section 1.2: Nitrate Contraindications)",
      learningGoal: "Recognize acute inferior STEMI with right ventricular extension and avoid preload reduction",
      safetyRule: "CRITICAL: Nitrates & diuretics are strictly contraindicated in right-ventricular preload-dependent infarction",
    },
    visualTransition: {
      fromColor: "from-red-500/20 to-rose-950/40",
      toColor: "border-red-500/40",
      animationKey: "pulse-red",
      hudBadge: "CRITICAL ERROR DETECTED",
    },
  },
  {
    id: 2,
    phaseNumber: 2,
    phaseTitle: "AI Knowledge Gap Detection",
    userState: {
      persona: "Dr. Tariq Al-Mansoor",
      clinicalConfidence: "Analytical / Alerted to Specific Defect",
      diagnosticScore: 61,
      errorState: "Spatial misorientation: Unable to correlate lead V1-V4 ST elevations with proximal LAD occlusion",
      sentiment: "Surprised that mistake wasn't memory loss, but lack of 3D vascular spatial intuition",
    },
    aiAction: {
      stage: "Stage-B & Stage-E Knowledge Tracing Engine",
      algorithm: "Bayesian Knowledge Tracing (BKT) + Topological Semantic Graph Mapping",
      intervention: "Isolated root misconception: Candidate memorizes lead letters without visualizing coronary perfusion territories",
      runtimeLatency: "44ms (Cosine Similarity 0.88 to NICE Corpus)",
    },
    medicalObjective: {
      condition: "Left Anterior Descending (LAD) Coronary Perfusion Anatomy",
      guidelineRef: "GMC PLAB 1 Clinical Blueprint (Cardiovascular System Core)",
      learningGoal: "Establish spatial anchor between anteroseptal myocardium and coronary tree branching",
      safetyRule: "Do not guess ECG leads without cross-referencing anatomical ventricular wall territory",
    },
    visualTransition: {
      fromColor: "from-amber-500/20 to-yellow-950/40",
      toColor: "border-amber-500/40",
      animationKey: "scan-amber",
      hudBadge: "GAP ISOLATED: SPATIAL VASCULAR DEFICIT",
    },
  },
  {
    id: 3,
    phaseNumber: 3,
    phaseTitle: "Personalized Adaptive Remediation",
    userState: {
      persona: "Dr. Tariq Al-Mansoor",
      clinicalConfidence: "High Engagement / Deep Clinical Absorption",
      diagnosticScore: 76,
      errorState: "Active remediation via 3D Hologram + Socratic Mentor + Ward Interceptor",
      sentiment: "Finally connecting spatial anatomy with emergency bedside decision making",
    },
    aiAction: {
      stage: "Stage-D & Stage-F Active Interceptor",
      algorithm: "Socratic Dialogic Loop with Hard Safety Guardrails",
      intervention: "Engaged candidate in interactive 3D LAD occlusion simulator; challenged with RV infarct nitrate trap",
      runtimeLatency: "62ms (0-latency safety block triggered on nitrate attempt)",
    },
    medicalObjective: {
      condition: "Emergency Reperfusion Protocols & Fluid Resuscitation",
      guidelineRef: "NICE NG185 & Resuscitation Council UK (ALS 2025)",
      learningGoal: "Execute intravenous fluid challenge instead of nitrates to maintain RV preload",
      safetyRule: "Stage-D safety barrier actively intercepts lethal nitrate administration during sim",
    },
    visualTransition: {
      fromColor: "from-cyan-500/20 to-blue-950/40",
      toColor: "border-cyan-500/40",
      animationKey: "glow-cyan",
      hudBadge: "SAFETY INTERCEPTOR ACTIVE: REMEDIATION IN PROGRESS",
    },
  },
  {
    id: 4,
    phaseNumber: 4,
    phaseTitle: "Improvement Visualization & Mastery",
    userState: {
      persona: "Dr. Tariq Al-Mansoor (Post-Intervention Candidate)",
      clinicalConfidence: "Exam-Ready & Ward Safe (88% PLAB 1 Mastery)",
      diagnosticScore: 88,
      errorState: "ZERO Contraindication Violations across 24 subsequent emergency scenarios",
      sentiment: "Calm, precise, and clinically grounded in NICE guidelines",
    },
    aiAction: {
      stage: "Stage-G Platform Telemetry & Stage-E Mastery Update",
      algorithm: "Exponential Moving Average Bayesian Mastery Convergence",
      intervention: "Certified candidate as 'CLINICALLY COMPETENT' in Acute Cardiology & Hemodynamic Safety",
      runtimeLatency: "29ms (State Synchronized to Deanery Dashboard)",
    },
    medicalObjective: {
      condition: "Full Comprehensive PLAB 1 Cardiology Domain Mastery",
      guidelineRef: "GMC Good Medical Practice & NICE NG185 / NG128",
      learningGoal: "Demonstrate instinctive contraindication recognition under acute time constraints",
      safetyRule: "Zero tolerance for hemodynamic contraindications achieved",
    },
    visualTransition: {
      fromColor: "from-emerald-500/20 to-teal-950/40",
      toColor: "border-emerald-500/40",
      animationKey: "burst-green",
      hudBadge: "CLINICAL MASTERY CERTIFIED: 88% READINESS",
    },
  },
];

// =========================================================================
// 2. OUTCOME METRICS ENGINE (Strict Compliance Labeled)
// =========================================================================

export const OUTCOME_METRICS: OutcomeMetricItem[] = [
  {
    id: "metric-pass-rate",
    metricName: "First-Attempt PLAB Exam Pass Rate",
    category: "Exam Performance",
    legacyBaseline: "58.4%",
    medicalPlabValue: "89.2%",
    deltaGain: "+30.8% Absolute Gain",
    isPositive: true,
    complianceBadge: "[Prototype Projection]",
    calculationSource: "Based on Bayesian Knowledge Tracing pilot model (N=250 simulated cohort) vs GMC published historical pass rates for international medical graduates (2022-2024 cohort).",
    clinicalImpactSummary: "Reduces candidate resit cycles from 2.4 attempts down to 1.1 attempts, accelerating clinical ward deployment by 9 months.",
  },
  {
    id: "metric-safety-errors",
    metricName: "Bedside Contraindication Error Rate",
    category: "Clinical Safety",
    legacyBaseline: "14.2%",
    medicalPlabValue: "0.4%",
    deltaGain: "-97.2% Error Reduction",
    isPositive: true,
    complianceBadge: "[Demo Simulation]",
    calculationSource: "Observed frequency of fatal medication contraindication triggers (e.g. nitrates in RV infarct, beta-blockers in acute asthma) in simulated emergency ward scenarios.",
    clinicalImpactSummary: "Near-total elimination of preventable pharmacotherapy errors before candidates step foot on NHS clinical wards.",
  },
  {
    id: "metric-study-time",
    metricName: "Average Hours to Full Syllabus Mastery",
    category: "Study Efficiency",
    legacyBaseline: "280 Hours",
    medicalPlabValue: "145 Hours",
    deltaGain: "-48.2% Time Saved",
    isPositive: true,
    complianceBadge: "[Prototype Projection]",
    calculationSource: "Computed by comparing sequential linear question bank grinding (avg 3,500 questions at 4.8 min/question) against MedicalPlab adaptive targeted gap-remediation.",
    clinicalImpactSummary: "Saves 135 hours of high-stress study per doctor, freeing capacity for practical clinical observerships and bedside training.",
  },
  {
    id: "metric-retention-30d",
    metricName: "30-Day Complex Spatial Anatomy Retention",
    category: "Knowledge Retention",
    legacyBaseline: "42.0%",
    medicalPlabValue: "86.5%",
    deltaGain: "+105.9% Retention Boost",
    isPositive: true,
    complianceBadge: "[Demo Simulation]",
    calculationSource: "Standardized delayed recall testing at day 30 on coronary arterial territories and cranial nerve pathways after 3D WebGL exploration vs static 2D textbook atlas.",
    clinicalImpactSummary: "Spatial vascular memory prevents anatomical confusion during acute catheterization lab interventions.",
  },
  {
    id: "metric-case-latency",
    metricName: "Diagnostic Case Decision Latency",
    category: "Study Efficiency",
    legacyBaseline: "4.8 Minutes",
    medicalPlabValue: "1.9 Minutes",
    deltaGain: "-60.4% Latency Reduction",
    isPositive: true,
    complianceBadge: "[Prototype Projection]",
    calculationSource: "Average elapsed time from clinical vignette presentation to correct guideline-backed management selection in timed exam simulations.",
    clinicalImpactSummary: "Translates directly to faster triage times in high-pressure NHS Emergency Departments.",
  },
  {
    id: "metric-institutional-roi",
    metricName: "Trust Economic Value per 100 Doctors",
    category: "Clinical Safety",
    legacyBaseline: "£0 (Loss: £340k resits)",
    medicalPlabValue: "£462,800 Net Value",
    deltaGain: "+8.5x ROI Multiplier",
    isPositive: true,
    complianceBadge: "[Future Target]",
    calculationSource: "Health economics synthesis incorporating locum replacement vacancy avoidance (£6,200/mo), faculty teaching hours saved (18h/doctor), and eliminated exam resit fees (£4,500/candidate).",
    clinicalImpactSummary: "Provides hospital trusts with an ironclad business case to sponsor full junior doctor cohort licenses.",
  },
];

// =========================================================================
// 3. INSTITUTION DASHBOARD DATA (B2B Multi-Hospital Deanery)
// =========================================================================

export const INSTITUTION_DATA: InstitutionCohortAnalytics = {
  deaneryName: "Imperial College Healthcare & North West Thames NHS Foundation Deanery",
  activeCandidates: 342,
  examReadyPct: 68,
  developingPct: 24,
  criticalRemediationPct: 8,
  averageStudyHours: 112.4,
  highRiskTopics: [
    {
      topic: "Acute Coronary Syndromes (RV STEMI Preload)",
      failureRate: 31.4,
      guidelineRef: "NICE NG185 Section 1.2",
      suggestedIntervention: "Assign 15-minute 3D interactive LAD/RCA perfusion lab drill before ward rotation.",
    },
    {
      topic: "Sepsis-3 Resuscitation & Lactate Clearance",
      failureRate: 24.8,
      guidelineRef: "NICE NG51 / Surviving Sepsis 2024",
      suggestedIntervention: "Schedule emergency ward simulation with fluid bolus vs vasopressor decision tree.",
    },
    {
      topic: "Acute Anaphylaxis Intramuscular Epinephrine Dosing",
      failureRate: 18.2,
      guidelineRef: "BNF 85 & Resuscitation Council UK",
      suggestedIntervention: "Trigger zero-tolerance medication safety challenge targeting 1:1,000 dilution recognition.",
    },
    {
      topic: "Diabetic Ketoacidosis Potassium Replacement Thresholds",
      failureRate: 15.6,
      guidelineRef: "JBDS-IP Guidelines / NICE NG17",
      suggestedIntervention: "Deploy electrolyte monitoring telemetry quiz module to all FY1 candidates.",
    },
  ],
  curriculumRecommendations: [
    {
      priority: "HIGH",
      title: "Urgent Cardiology Preload Contraindication Seminar",
      targetCandidates: 28,
      actionPlan: "28 candidates flagged with recurring nitrate administration during inferior STEMI. Mandate completion of Stage-F Resuscitation Sim by Friday 17:00.",
    },
    {
      priority: "MEDIUM",
      title: "Sepsis Fluid Challenge Micro-Drill",
      targetCandidates: 46,
      actionPlan: "Automate adaptive question delivery on initial 30ml/kg crystalloid resuscitation for candidates with <70% sepsis mastery.",
    },
    {
      priority: "ROUTINE",
      title: "Fast-Track PLAB 1 Mock Exam for High Performers",
      targetCandidates: 84,
      actionPlan: "84 candidates have sustained >85% Bayesian mastery across all domains; unlock advanced clinical OSCE scenario pack.",
    },
  ],
  engagementIndicators: {
    dailyActivePct: 84.6,
    avgSimulationsPerUser: 14.2,
    tutorQuestionsLogged: 12840,
    safetyIncidentsIntercepted: 412,
  },
};

// =========================================================================
// 4. IMPACT STORIES (Cinematic Real-World Scenarios)
// =========================================================================

export const IMPACT_STORIES: ImpactStoryItem[] = [
  {
    id: "story-student",
    dimension: "Student Transformation",
    title: "From 3rd-Time PLAB Failure to St. Mary's NHS Registrar",
    heroQuote: "I spent 18 months memorizing static question banks and failed twice by 3 points. In MedicalPlab, seeing the LAD artery in 3D and having the Socratic tutor challenge my reasoning made everything click in 3 weeks.",
    protagonist: "Dr. Tariq Al-Mansoor (Alexandria University Graduate → NHS Trust Registrar)",
    clinicalContext: "International Medical Graduate navigating the high-stakes UK PLAB licensing pathway while working full-time shifts.",
    crisisProblem: "Severe test anxiety, cognitive overload from memorizing 4,000 isolated question stems without clinical spatial intuition, resulting in repeated 42% benchmark scores.",
    medicalPlabIntervention: "AI Bayesian Knowledge Tracing identified a 78% deficit in spatial coronary hemodynamics. Guided through 3D Anatomy Lab and targeted Socratic clinical drills with NICE NG185 verification.",
    expectedOutcome: "Passed PLAB 1 with an 84% score on the subsequent sitting; secured clinical fellowship at Imperial College Healthcare NHS Trust 4 months ahead of schedule.",
    complianceBadge: "[Prototype Projection]",
    outcomeStats: [
      { label: "Mock Exam Score", value: "54% → 84% (+30%)" },
      { label: "Study Duration", value: "3 Weeks Adaptive" },
      { label: "Current Role", value: "NHS Registrar" },
    ],
  },
  {
    id: "story-safety",
    dimension: "Clinical Safety Interception",
    title: "The Intercepted Nitrate: Preventing Bedside Cardiovascular Collapse",
    heroQuote: "In the resuscitation bay, seconds count. A trainee doctor's instinct was to administer sublingual GTN for severe chest pain. MedicalPlab's safety engine trained their reflex to immediately check V4R first.",
    protagonist: "Emergency Resuscitation Team, St. Thomas' Hospital A&E",
    clinicalContext: "A 64-year-old male presents with acute diaphoresis, bradycardia (HR 44), and ST elevation in leads II, III, aVF. Blood pressure is borderline at 98/62 mmHg.",
    crisisProblem: "Inferior STEMI frequently involves right ventricular infarction (preload dependency). Standard reflexive administration of nitrates drops preload, triggering catastrophic refractory cardiogenic shock.",
    medicalPlabIntervention: "Trainee had completed MedicalPlab's Stage-D Safety Interceptor, where an interactive drill forcefully intercepted nitrate administration and taught lead V4R verification.",
    expectedOutcome: "Trainee withheld nitrates, obtained right-sided ECG confirming RV involvement, and administered 500ml IV crystalloid bolus, stabilizing blood pressure prior to primary PCI.",
    complianceBadge: "[Demo Simulation]",
    outcomeStats: [
      { label: "Error Intercepted", value: "Lethal GTN Preload Drop" },
      { label: "Patient Outcome", value: "Successful Primary PCI" },
      { label: "Clinical Protocol", value: "100% NICE NG185 Adherence" },
    ],
  },
  {
    id: "story-institution",
    dimension: "Institutional Scaling",
    title: "Closing the NHS Junior Doctor Vacancy Gap 4 Months Early",
    heroQuote: "Hiring locum doctors to cover rota vacancies was draining £450,000 quarterly from our trust budget. MedicalPlab accelerated our incoming IMG onboarding and licensing pass rates dramatically.",
    protagonist: "Director of Medical Education, North West Thames NHS Deanery",
    clinicalContext: "Regional NHS Deanery managing 350+ incoming international doctors and Foundation Year 1 trainees facing acute winter hospital pressures.",
    crisisProblem: "42% historical exam failure rate left critical rota gaps, requiring expensive agency locums at £95/hour and creating high clinical burnout among existing senior registrars.",
    medicalPlabIntervention: "Deployed MedicalPlab B2B Deanery Command Center. Faculty gained instant real-time telemetry into high-risk topics, triggering targeted cohort remediation 3 weeks before exams.",
    expectedOutcome: "Cohort first-time pass rate improved from 58% to 89% in pilot simulation; 14 critical junior doctor vacancies filled 4 months ahead of schedule, generating £384,000 net savings.",
    complianceBadge: "[Future Target]",
    outcomeStats: [
      { label: "Trust Net Savings", value: "£384,000 / Year" },
      { label: "Rota Vacancies Closed", value: "14 Positions" },
      { label: "Time-to-Licensure", value: "Reduced by 9 Months" },
    ],
  },
];

// =========================================================================
// 5. JUDGE IMPACT DEFENSE SYSTEM (Adversarial Q&A)
// =========================================================================

export const JUDGE_IMPACT_DEFENSES: JudgeImpactDefenseItem[] = [
  {
    id: "defense-validation",
    question: "Do you have clinical validation, or are these numbers simulated?",
    founderResponse: "We are 100% transparent: our current validation metrics are derived from a simulated pilot cohort (N=250) utilizing Bayesian Knowledge Tracing and historical GMC datasets, not prospective randomized controlled trials. All metrics are explicitly tagged as [Prototype Projection] or [Demo Simulation]. However, our clinical safety guardrails are deterministically hard-coded against published NICE NG185, NG128, and BNF 85 guidelines.",
    technicalExplanation: "Our Stage-B and Stage-D verifiers evaluate candidate clinical responses against mathematical cosine similarity thresholds (>= 0.82) and exact medical ontology entity overlap (>= 0.75). The -97.2% contraindication error reduction reflects deterministic interceptor firings in emergency simulation runs.",
    honestLimitation: "We have not yet completed a prospective, double-blinded multi-center clinical trial comparing MedicalPlab directly against PassMedicine or Pastest in actual hospital exam settings.",
    futureValidationRoadmap: "Phase 1 (Q3 2026): 50-doctor observational pilot with Imperial College Healthcare NHS Trust. Phase 2 (Q1 2027): Multi-center prospective study tracking GMC PLAB 1 scores and first-year clinical incident reports.",
    complianceBadge: "[Prototype Projection]",
  },
  {
    id: "defense-metrics-calculation",
    question: "How exactly were your impact metrics and ROI calculations derived?",
    founderResponse: "Every metric is grounded in published NHS economic models: GMC annual education reports for baseline pass rates (58.4%), National Audit Office benchmarks for locum agency costs (£6,200/month/vacant post), and GMC exam resit tariffs (£4,500/candidate). Our ROI calculator models direct savings from resit avoidance and accelerated clinical deployment.",
    technicalExplanation: "The ROI formula computes: Gross Savings = (Candidates * Delta PassRate * ResitCost) + (VacanciesAvoided * LocumCost * MonthsSaved) + (FacultyHoursSaved * HourlyRate). At a conservative 200-doctor tier, this yields £925,600 in economic value against a £108,000 SaaS license (8.5x ROI).",
    honestLimitation: "Actual hospital savings depend heavily on trust-specific procurement cycles, individual locum rates, and local deanery exam resit subsidies.",
    futureValidationRoadmap: "Deploying an automated telemetry connector in Stage-G to ingest anonymized real-time trust HR vacancy and exam clearing house data for dynamic ROI reconciliation.",
    complianceBadge: "[Prototype Projection]",
  },
  {
    id: "defense-adoption",
    question: "Why would risk-averse NHS hospital trusts and medical colleges adopt this over incumbents?",
    founderResponse: "Legacy incumbents like PassMedicine and Pastest are single-player, static consumer products. They provide zero visibility to hospital deaneries, zero multi-tenancy, and zero patient safety guardrails. MedicalPlab is an institutional Clinical Intelligence OS that gives Directors of Medical Education live telemetry into cohort risk before exams, while providing an ironclad safety interceptor that protects hospital patients.",
    technicalExplanation: "Our multi-tenant Stage-G architecture isolates deanery sub-domains (e.g. imperial.medicalplab.nhs.uk), provides RBAC role separation (Student vs Deanery Faculty), and automatically generates targeted remediation cohorts without requiring manual faculty grading.",
    honestLimitation: "NHS procurement cycles are notoriously bureaucratic (typically 9 to 14 months for software tenders over £100k).",
    futureValidationRoadmap: "Launching on G-Cloud 14 Digital Marketplace for streamlined NHS direct-award procurement under £150k threshold, supported by departmental pilot budgets.",
    complianceBadge: "[Future Target]",
  },
  {
    id: "defense-qbank-diff",
    question: "How is this fundamentally different from a static question bank like PassMedicine?",
    founderResponse: "Question banks are passive text catalogs where candidates memorize 4,000 isolated questions and guess blindly. MedicalPlab is an integrated spatial and clinical intelligence system: candidates rotate real 3D anatomical coronary vessels, engage with an evidence-grounded Socratic tutor citing NICE guidelines, and make high-stakes resuscitation decisions where a safety interceptor actively halts fatal errors.",
    technicalExplanation: "PassMedicine has zero spatial reasoning and zero clinical safety verification. MedicalPlab integrates WebGL spatial models with a frozen 7-stage Python pipeline (Stages B through G) that verifies mathematical grounding (>= 98.6% confidence) and prevents hallucinations deterministically.",
    honestLimitation: "Question banks have 15+ years of brand recognition among medical students and extensive question repositories.",
    futureValidationRoadmap: "Expanding our deterministic question generator (Stage-C & Stage-E) to auto-synthesize 10,000+ verified PLAB Single Best Answer questions grounded directly in updated NICE guidelines.",
    complianceBadge: "[Demo Simulation]",
  },
];
