/**
 * STAGE-X: MEDICALPLAB GLOBAL INTELLIGENCE & HEALTHCARE LEGACY LAYER
 * Immutable Data Models, Enterprise Telemetry, and Executive Demo Scenarios
 * 
 * Positioning MedicalPlab as:
 * "The Intelligence Infrastructure Layer of Global Medicine"
 */

export interface GlobalMedicalNode {
  id: string;
  name: string;
  category: "disease" | "symptom" | "investigation" | "treatment" | "evidence" | "outcome";
  stageStep: 1 | 2 | 3 | 4 | 5 | 6; // 1: Disease, 2: Symptoms, 3: Investigations, 4: Treatment, 5: Evidence, 6: Clinical Outcomes
  description: string;
  confidenceScore: number; // 0-100
  sourceProvenance: string;
  clinicalNotes: string;
  status: "established" | "emerging" | "high-priority";
  connectedNodeIds: string[];
  metrics?: { label: string; value: string };
}

export interface MedicalModule {
  id: string;
  title: string;
  providerType: "Universities" | "Hospitals" | "Researchers" | "Medical educators";
  providerName: string;
  category: "AI Agents" | "Simulation Modules" | "Medical Courses" | "Clinical Packages";
  status: "Verified" | "Prototype" | "Future Vision";
  description: string;
  rating: number;
  installsOrUsers: string;
  tags: string[];
  pricing: string;
  verificationAudit: string;
  complianceLevel: string;
}

export interface ResearchInsight {
  id: string;
  researchQuestion: string;
  hypothesis: string;
  meshTerms: string[];
  literatureDiscoveryCount: number;
  topJournals: string[];
  evidenceRanking: {
    grade: "Grade A" | "Grade B" | "Grade C";
    score: number;
    metaAnalysesCount: number;
    rctCount: number;
  };
  synthesisSummary: string;
  researchOpportunity: string;
  impactScore: number; // 0-100
  knowledgeGaps: string[];
  aiRecommendedStudyDesign: string;
}

export interface SimulationScenario {
  id: string;
  title: string;
  environment: "Emergency Department" | "ICU" | "Surgical Ward";
  patientName: string;
  patientAge: number;
  gender: string;
  chiefComplaint: string;
  baselineVitals: {
    hr: number;
    bp: string;
    spo2: number;
    rr: number;
    temp: number;
    gcs: number;
  };
  criticalDecisions: Array<{
    id: string;
    action: string;
    outcomeEffect: string;
    safe: boolean;
    feedback: string;
    timePenaltySec: number;
  }>;
  simulationState: "INITIALIZING" | "RUNNING" | "STABILIZED" | "CRITICAL";
  safetyWarnings: string[];
  isDemoMode: boolean;
  clinicalObjectives: string[];
}

export interface PhysicianProfile {
  id: string;
  name: string;
  specialty: "Emergency Medicine" | "Cardiology" | "Intensive Care" | "Acute Medicine";
  subspecialty: string;
  hospitalAffiliation: string;
  reasoningScore: number; // e.g. 92
  guidelineAwareness: number; // e.g. 88
  simulationPerformance: number; // e.g. 94
  learningProgress: number; // e.g. 89
  radarSkills: Array<{ axis: string; score: number; benchmark: number }>;
  knowledgeGaps: Array<{
    topic: string;
    severity: "High" | "Medium" | "Low";
    recommendation: string;
    evidenceTarget: string;
  }>;
  recentCasesCompleted: number;
  certificationStatus: string;
  lastActive: string;
}

export interface HealthcareMetric {
  id: string;
  hospitalName: string;
  region: "UK NHS Trust" | "US Health System" | "EU Academic Medical Center" | "Global Health Hub";
  country: string;
  bedCapacity: number;
  overallDiagnosticAccuracy: number;
  trainingGapIndex: number;
  clinicalWorkforceTrained: number;
  annualAdverseEventReduction: string;
  regionalRank: number;
  departmentalKPIs: Array<{
    department: string;
    throughput: string;
    protocolAdherence: number;
    costSavingsEst: string;
  }>;
}

export interface GovernanceMetric {
  id: string;
  title: string;
  category: "Evidence Coverage" | "Safety Validation" | "Audit History" | "Human Oversight" | "AI Risk Monitoring";
  status: "Optimal" | "Compliant" | "Active Monitoring";
  metricValue: string;
  benchmark: string;
  auditTrailCount: number;
  lastCertifiedDate: string;
  safetyDetails: string;
  humanInterventionRate: string;
  riskVectorScores: Array<{
    vector: string;
    riskLevel: "Minimal" | "Low" | "Managed";
    score: number;
  }>;
}

export interface APIProduct {
  id: string;
  endpoint: "/clinical_reasoning" | "/evidence_search" | "/simulation_engine" | "/learning_analysis";
  name: string;
  version: string;
  method: "POST" | "GET";
  description: string;
  latencyMs: number;
  uptimePercent: number;
  monthlyCalls: string;
  curlSnippet: string;
  responseSchemaSample: string;
  enterpriseUseCases: string[];
  authentication: string;
}

export interface KnowledgeSyncEvent {
  id: string;
  timestamp: string;
  stage: "New Medical Evidence" | "Validation Engine" | "Knowledge Graph Update" | "Question Bank Update" | "Tutor Update" | "Simulation Update";
  title: string;
  source: string;
  status: "Synchronized" | "Validated" | "Propagating";
  deltaItems: number;
  trustScore: number;
}

export interface AcademyProgram {
  id: string;
  title: string;
  certificateType: "Clinical Reasoning" | "Emergency Medicine" | "AI Assisted Medicine";
  partnerName: string;
  partnerType: "Universities" | "Hospitals" | "Training Centers";
  accreditationBody: string;
  durationWeeks: number;
  creditsEcts: number;
  enrolledScholars: number;
  curriculumModules: string[];
  alumniPassRate: number;
}

export interface StageXDemoScene {
  sceneNumber: 1 | 2 | 3 | 4 | 5;
  title: string;
  subtitle: string;
  durationSec: number;
  screenAction: string;
  presenterScript: string;
  investorTakeaway: string;
  targetModuleId: string;
  visualHighlights: string[];
}

/* ==========================================================================
   IMMUTABLE DATASETS
   ========================================================================== */

export const GLOBAL_MEDICAL_NODES: GlobalMedicalNode[] = [
  // Pathway 1: Acute Coronary Syndrome (STEMI / NSTEMI)
  {
    id: "dis-acs",
    name: "Acute Coronary Syndrome (STEMI/NSTEMI)",
    category: "disease",
    stageStep: 1,
    description: "Acute myocardial ischaemia secondary to coronary plaque rupture or thrombosis.",
    confidenceScore: 99,
    sourceProvenance: "NICE NG185 / ESC Guidelines 2023",
    clinicalNotes: "Requires immediate differentiation between ST-elevation and non-ST elevation ACS.",
    status: "established",
    connectedNodeIds: ["sym-cp", "sym-dyspnea", "inv-ecg", "inv-trop"],
    metrics: { label: "Global Prevalence", value: "3.8M annual admissions" }
  },
  {
    id: "sym-cp",
    name: "Crushing Retrosternal Chest Pain",
    category: "symptom",
    stageStep: 2,
    description: "Radiation to left arm, neck, or jaw; accompanied by diaphoresis and nausea.",
    confidenceScore: 96,
    sourceProvenance: "AHA/ACC Circulation 2022",
    clinicalNotes: "Atypical presentations frequent in diabetic, female, and elderly cohorts.",
    status: "established",
    connectedNodeIds: ["dis-acs", "inv-ecg"],
    metrics: { label: "Sensitivity", value: "88.4%" }
  },
  {
    id: "sym-dyspnea",
    name: "Acute Dyspnoea & Diaphoresis",
    category: "symptom",
    stageStep: 2,
    description: "Secondary to left ventricular diastolic dysfunction or acute pulmonary congestion.",
    confidenceScore: 94,
    sourceProvenance: "European Heart Journal 2023",
    clinicalNotes: "Key anginal equivalent flag.",
    status: "established",
    connectedNodeIds: ["dis-acs", "inv-cxr"],
    metrics: { label: "Clinical Weight", value: "High Yield" }
  },
  {
    id: "inv-ecg",
    name: "12-Lead ECG within 10 Minutes",
    category: "investigation",
    stageStep: 3,
    description: "Evaluates for ST-segment elevation ≥1mm in limb leads or ≥2mm in precordial leads.",
    confidenceScore: 98,
    sourceProvenance: "NICE QS68 / Resuscitation Council UK",
    clinicalNotes: "Mandatory serial ECGs if high clinical index of suspicion with normal baseline.",
    status: "established",
    connectedNodeIds: ["dis-acs", "trt-pci", "ev-nice-ng185"],
    metrics: { label: "Target Door-to-ECG", value: "<10 mins" }
  },
  {
    id: "inv-trop",
    name: "High-Sensitivity Cardiac Troponin I/T",
    category: "investigation",
    stageStep: 3,
    description: "0h/1h or 0h/2h rapid rule-in/rule-out protocol for acute myocardial necrosis.",
    confidenceScore: 99,
    sourceProvenance: "ESC 0h/1h Algorithm 2023",
    clinicalNotes: "Significant delta required to distinguish acute injury from chronic baseline elevation.",
    status: "established",
    connectedNodeIds: ["dis-acs", "trt-antiplatelet", "ev-esc-2023"],
    metrics: { label: "NPV", value: "99.2%" }
  },
  {
    id: "trt-pci",
    name: "Primary Percutaneous Coronary Intervention (pPCI)",
    category: "treatment",
    stageStep: 4,
    description: "Emergency reperfusion therapy for STEMI within 120 minutes of first medical contact.",
    confidenceScore: 97,
    sourceProvenance: "British Cardiovascular Intervention Society (BCIS)",
    clinicalNotes: "Door-to-balloon time benchmark is under 90 minutes from hospital arrival.",
    status: "established",
    connectedNodeIds: ["inv-ecg", "out-stemi-survival", "ev-cochrane-pci"],
    metrics: { label: "Target FMC-to-Wire", value: "<120 mins" }
  },
  {
    id: "trt-antiplatelet",
    name: "Dual Antiplatelet Therapy (DAPT) + Anticoagulation",
    category: "treatment",
    stageStep: 4,
    description: "Aspirin 300mg loading + Ticagrelor 180mg or Prasugrel 60mg plus Fondaparinux/Heparin.",
    confidenceScore: 98,
    sourceProvenance: "NICE NG185 Section 1.2",
    clinicalNotes: "Assess bleeding risk with PRECISE-DAPT score prior to long-term regime.",
    status: "established",
    connectedNodeIds: ["inv-trop", "out-stemi-survival", "ev-nice-ng185"],
    metrics: { label: "Ischaemic MACE Reduction", value: "-34%" }
  },
  {
    id: "ev-nice-ng185",
    name: "NICE Guideline NG185 (2024 Revision)",
    category: "evidence",
    stageStep: 5,
    description: "Rigorous systematic review and health-economic evaluation for acute coronary syndromes.",
    confidenceScore: 99,
    sourceProvenance: "National Institute for Health and Care Excellence",
    clinicalNotes: "Grade A systematic reviews across 42 multi-center randomised trials.",
    status: "established",
    connectedNodeIds: ["trt-antiplatelet", "out-stemi-survival"],
    metrics: { label: "Evidence Strength", value: "Grade A" }
  },
  {
    id: "ev-esc-2023",
    name: "ESC 2023 Acute Coronary Syndrome Consensus",
    category: "evidence",
    stageStep: 5,
    description: "Unified guideline covering both STEMI and NSTEMI clinical management pathways.",
    confidenceScore: 96,
    sourceProvenance: "European Society of Cardiology",
    clinicalNotes: "Synthesized from 125,000 patient registry datasets across 32 nations.",
    status: "established",
    connectedNodeIds: ["inv-trop", "trt-pci"],
    metrics: { label: "Sample Cohort", value: "n=125,480" }
  },
  {
    id: "out-stemi-survival",
    name: "30-Day All-Cause Mortality Reduction to <4.2%",
    category: "outcome",
    stageStep: 6,
    description: "Optimal algorithmic adherence demonstrates 68% reduction in secondary cardiogenic shock.",
    confidenceScore: 97,
    sourceProvenance: "MINAP Registry 2024 / Lancet Cardiology",
    clinicalNotes: "Correlates directly with AI decision-support protocol compliance in emergency triaging.",
    status: "established",
    connectedNodeIds: ["trt-pci", "trt-antiplatelet"],
    metrics: { label: "Relative Risk Reduction", value: "68% p<0.001" }
  },

  // Pathway 2: Sepsis & Septic Shock (Sepsis-6)
  {
    id: "dis-sepsis",
    name: "Severe Sepsis & Septic Shock",
    category: "disease",
    stageStep: 1,
    description: "Life-threatening organ dysfunction caused by a dysregulated host response to infection.",
    confidenceScore: 98,
    sourceProvenance: "Surviving Sepsis Campaign 2023 / NICE NG51",
    clinicalNotes: "qSOFA / NEWS2 score ≥ 5 prompts immediate Sepsis-6 resuscitation protocol.",
    status: "established",
    connectedNodeIds: ["sym-fever-hypo", "inv-lactate", "trt-sepsis6"],
    metrics: { label: "Global Burden", value: "48.9M cases/yr" }
  },
  {
    id: "sym-fever-hypo",
    name: "Hypotension (MAP <65), Tachycardia & Altered Mentation",
    category: "symptom",
    stageStep: 2,
    description: "Systemic vasodilation and tissue hypoperfusion causing organ microvascular ischemia.",
    confidenceScore: 95,
    sourceProvenance: "Intensive Care Medicine 2023",
    clinicalNotes: "Altered mental state often earliest sign in frailty or geriatric presentations.",
    status: "established",
    connectedNodeIds: ["dis-sepsis", "inv-lactate"],
    metrics: { label: "Organ Risk", value: "Critical Tier 1" }
  },
  {
    id: "inv-lactate",
    name: "Serum Lactate & Blood Cultures x2 Prior to Antibiotics",
    category: "investigation",
    stageStep: 3,
    description: "Serum lactate >2 mmol/L indicates cellular dysoxia; >4 mmol/L indicates severe shock.",
    confidenceScore: 97,
    sourceProvenance: "NICE NG51 / UK Sepsis Trust",
    clinicalNotes: "Do not delay broad-spectrum antimicrobials if blood cultures encounter venous access delays.",
    status: "established",
    connectedNodeIds: ["dis-sepsis", "trt-sepsis6", "ev-ssc-2023"],
    metrics: { label: "Diagnostic SLA", value: "<45 mins" }
  },
  {
    id: "trt-sepsis6",
    name: "The Sepsis Six Bundle (within 1 Hour)",
    category: "treatment",
    stageStep: 4,
    description: "Deliver: High-flow O2, Blood cultures, IV Antibiotics, IV Fluid bolus (30ml/kg), Lactate, Urine output.",
    confidenceScore: 98,
    sourceProvenance: "UK Sepsis Trust / Royal College of Emergency Medicine",
    clinicalNotes: "Every 1-hour delay in antimicrobial administration increases mortality by 7.6%.",
    status: "established",
    connectedNodeIds: ["inv-lactate", "out-sepsis-survival", "ev-ssc-2023"],
    metrics: { label: "Golden Hour Target", value: "100% within 60m" }
  },
  {
    id: "ev-ssc-2023",
    name: "Surviving Sepsis Campaign International Guidelines 2023",
    category: "evidence",
    stageStep: 5,
    description: "Consensus recommendations from 55 international clinical experts across 24 global societies.",
    confidenceScore: 99,
    sourceProvenance: "Society of Critical Care Medicine (SCCM)",
    clinicalNotes: "Recommends balanced crystalloids over saline and norepinephrine as first-line vasopressor.",
    status: "established",
    connectedNodeIds: ["trt-sepsis6", "out-sepsis-survival"],
    metrics: { label: "Methodology", value: "GRADE Systematic" }
  },
  {
    id: "out-sepsis-survival",
    name: "In-Hospital Mortality Reduction by 46.5%",
    category: "outcome",
    stageStep: 6,
    description: "Rapid bundle completion within 60 minutes prevents progression to refractory vasoplegic shock.",
    confidenceScore: 96,
    sourceProvenance: "NEJM Critical Care Review 2024",
    clinicalNotes: "Validates digital clinical decision support integration at hospital triage.",
    status: "established",
    connectedNodeIds: ["trt-sepsis6", "ev-ssc-2023"],
    metrics: { label: "Odds Ratio", value: "0.535 (95% CI)" }
  }
];

export const MEDICAL_MODULES: MedicalModule[] = [
  {
    id: "mod-neuro-agent",
    title: "NeuroVigil: Acute Ischaemic Stroke AI Agent",
    providerType: "Universities",
    providerName: "Oxford University Institute of Biomedical Engineering",
    category: "AI Agents",
    status: "Verified",
    description: "Autonomous multimodal agent providing ASPECTS scoring on non-contrast CT and tenecteplase eligibility calculation in real-time.",
    rating: 4.95,
    installsOrUsers: "1,420 Hospitals",
    tags: ["Stroke", "Neuroimaging", "ASPECTS", "Emergency"],
    pricing: "Enterprise Open Protocol",
    verificationAudit: "ISO 13485 & CE MDR Class IIb Certified",
    complianceLevel: "FDA Breakthrough Designation"
  },
  {
    id: "mod-icu-twin",
    title: "CardioResusc: Hemodynamic Crisis Simulation Universe",
    providerType: "Hospitals",
    providerName: "Royal Brompton & Harefield NHS Trust",
    category: "Simulation Modules",
    status: "Verified",
    description: "High-fidelity physiological digital twin reproducing ECMO, impella, and acute RV failure scenarios with real-time pharmacology dynamics.",
    rating: 4.92,
    installsOrUsers: "8,900 Fellows",
    tags: ["Critical Care", "Hemodynamics", "ECMO", "Shock"],
    pricing: "Tier-1 Academic License",
    verificationAudit: "NICE Clinical Validation Standard v4.2",
    complianceLevel: "NHS Digital DTAC Passed"
  },
  {
    id: "mod-oncology-curriculum",
    title: "Precision Immuno-Oncology Decision Protocol",
    providerType: "Researchers",
    providerName: "Karolinska Institutet Cancer Center",
    category: "Medical Courses",
    status: "Verified",
    description: "Interactive clinical masterclass on next-generation sequencing genomic variant analysis and personalized CAR-T / checkpoint therapy.",
    rating: 4.88,
    installsOrUsers: "14,300 Specialists",
    tags: ["Oncology", "Genomics", "Immunotherapy", "Biomarkers"],
    pricing: "Accredited CME / ECTS",
    verificationAudit: "ESMO Quality Assurance Seal 2024",
    complianceLevel: "EACCME 18 Credits"
  },
  {
    id: "mod-pediatric-triage",
    title: "PediSafe: Pediatric Resuscitation Intelligence Agent",
    providerType: "Medical educators",
    providerName: "Great Ormond Street Hospital Institute of Child Health",
    category: "AI Agents",
    status: "Verified",
    description: "Weight-adjusted Broselow predictive dosing assistant with voice HUD integration for pediatric status epilepticus and septic shock.",
    rating: 4.97,
    installsOrUsers: "4,600 Resus Bays",
    tags: ["Pediatrics", "Dosing Safety", "Resuscitation", "PALS"],
    pricing: "Global Pediatric Safety Pledge",
    verificationAudit: "RCPCH Validated Clinical Matrix",
    complianceLevel: "DCB0129 / DCB0160 Compliant"
  },
  {
    id: "mod-surgical-robotics",
    title: "HoloSurg: Autonomous Laparoscopic Tele-Mentoring Engine",
    providerType: "Hospitals",
    providerName: "Johns Hopkins Medicine Center for Surgical Innovation",
    category: "Simulation Modules",
    status: "Prototype",
    description: "Sub-millimeter anatomical boundary detection and procedural guidance for minimally invasive bariatric and colorectal procedures.",
    rating: 4.79,
    installsOrUsers: "32 Pilot Centers",
    tags: ["Surgery", "Robotics", "Computer Vision", "Spatial"],
    pricing: "Beta Consortium Only",
    verificationAudit: "Investigational Device Exemption (IDE)",
    complianceLevel: "Phase II Clinical Trial"
  },
  {
    id: "mod-quantum-drug",
    title: "PharmaSynthetica: In-Silico Target Toxicity Predictor",
    providerType: "Researchers",
    providerName: "Cambridge Molecular Intelligence Laboratory",
    category: "Clinical Packages",
    status: "Future Vision",
    description: "Generative quantum chemistry models screening off-target cardiotoxicity (hERG channel blocking) in novel pharmacophores.",
    rating: 4.85,
    installsOrUsers: "18 BioLabs",
    tags: ["Pharmacology", "Drug Discovery", "In-Silico", "Toxicology"],
    pricing: "Research Grant Tier",
    verificationAudit: "Pre-clinical Validation in Progress",
    complianceLevel: "OECD QSAR Guidelines"
  }
];

export const RESEARCH_INSIGHTS: ResearchInsight[] = [
  {
    id: "res-hfpef",
    researchQuestion: "Does early SGLT2i introduction in acute heart failure with preserved ejection fraction (HFpEF) reduce 90-day readmissions?",
    hypothesis: "Empagliflozin/Dapagliflozin initiates proximal tubular natriuresis without triggering neurohormonal renin-angiotensin activation.",
    meshTerms: ["Heart Failure, Diastolic", "Sodium-Glucose Transporter 2 Inhibitors", "Patient Readmission", "Clinical Outcomes"],
    literatureDiscoveryCount: 1482,
    topJournals: ["New England Journal of Medicine", "Lancet", "Circulation", "European Heart Journal"],
    evidenceRanking: {
      grade: "Grade A",
      score: 96,
      metaAnalysesCount: 14,
      rctCount: 38
    },
    synthesisSummary: "Pooled meta-analysis across EMPEROR-Preserved and DELIVER indicates a 21% relative risk reduction (HR 0.79, 95% CI 0.69-0.90) in cardiovascular death and HF hospitalization without excess renal risk.",
    researchOpportunity: "Evaluate combined SGLT2i + GLP-1RA synergistic metabolic cardioprotection in obese diabetic HFpEF cohorts.",
    impactScore: 94,
    knowledgeGaps: [
      "Inpatient acute decompensation safety in eGFR 20-25 ml/min/1.73m²",
      "Long-term impact on functional exercise capacity via cardiopulmonary exercise testing (CPET)"
    ],
    aiRecommendedStudyDesign: "Double-blind, international multicenter randomized controlled trial (Target n=2,400, 18-month primary endpoint)."
  },
  {
    id: "res-sepsis-subphenotypes",
    researchQuestion: "Can transcriptomic host-response subphenotyping guide personalized corticosteroid administration in refractory septic shock?",
    hypothesis: "Endotype A (hyperinflammatory with suppressed adaptive immunity) derives mortality benefit from hydrocortisone, whereas Endotype B experiences increased secondary bacteremia.",
    meshTerms: ["Sepsis", "Septic Shock", "Transcriptome", "Hydrocortisone", "Precision Medicine"],
    literatureDiscoveryCount: 894,
    topJournals: ["Lancet Respiratory Medicine", "JAMA", "American Journal of Respiratory and Critical Care Medicine"],
    evidenceRanking: {
      grade: "Grade B",
      score: 89,
      metaAnalysesCount: 6,
      rctCount: 19
    },
    synthesisSummary: "Clustering algorithms delineate two reproducible transcriptional endotypes. Retrospective ADRENAL trial analysis confirms differential treatment response.",
    researchOpportunity: "Deploy 45-minute point-of-care PCR multiplex classifier to guide real-time steroid initiation in intensive care units.",
    impactScore: 91,
    knowledgeGaps: [
      "Point-of-care turn-around time feasibility in peripheral hospitals",
      "Dynamic trajectory shifting between endotypes over 72 hours"
    ],
    aiRecommendedStudyDesign: "Biomarker-stratified adaptive Bayesian trial with interim futility monitoring."
  }
];

export const SIMULATION_SCENARIOS: SimulationScenario[] = [
  {
    id: "sim-ed-trauma",
    title: "High-Velocity Polytrauma with Tension Hemopneumothorax",
    environment: "Emergency Department",
    patientName: "James Callaghan",
    patientAge: 34,
    gender: "Male",
    chiefComplaint: "Motorcycle collision at 55 mph; severe respiratory distress, tracheal deviation to right.",
    baselineVitals: {
      hr: 138,
      bp: "82/48",
      spo2: 84,
      rr: 36,
      temp: 36.1,
      gcs: 10
    },
    criticalDecisions: [
      {
        id: "dec-1",
        action: "Immediate Left-Sided Needle Decompression (2nd Intercostal or 5th Intercostal AAL)",
        outcomeEffect: "Decompresses tension; venous return restored; BP rises to 105/65, SpO2 rises to 92%.",
        safe: true,
        feedback: "Life-saving intervention executed prior to diagnostic imaging as per ATLS guidelines.",
        timePenaltySec: 0
      },
      {
        id: "dec-2",
        action: "Order Immediate CT Polytrauma Before Thoracostomy",
        outcomeEffect: "Patient arrests in scanner due to complete vascular collapse from obstructive shock.",
        safe: false,
        feedback: "CRITICAL ERROR: Never transfer an unstable tension pneumothorax to the radiology suite.",
        timePenaltySec: 90
      },
      {
        id: "dec-3",
        action: "Initiate Massive Transfusion Protocol (1:1:1 PRBC, FFP, Platelets) + IV Tranexamic Acid 1g",
        outcomeEffect: "Arrests hemorrhagic coagulopathy; lactate down-trending from 6.8 to 3.4.",
        safe: true,
        feedback: "Adheres to CRASH-2 and PR4 trauma protocol benchmarks.",
        timePenaltySec: 0
      }
    ],
    simulationState: "RUNNING",
    safetyWarnings: [
      "Obstructive Shock Detected: High intrathoracic pressure impeding preload",
      "Hypothermia alert: Warm fluids and active patient re-warming indicated"
    ],
    isDemoMode: true,
    clinicalObjectives: [
      "Recognize clinical signs of tension pneumothorax without chest radiograph delay",
      "Perform surgical finger thoracostomy / chest drain placement",
      "Execute balanced damage-control resuscitation"
    ]
  },
  {
    id: "sim-icu-storm",
    title: "Post-Infarction Cardiogenic Shock with Ventricular Septal Rupture",
    environment: "ICU",
    patientName: "Eleanor Vance",
    patientAge: 68,
    gender: "Female",
    chiefComplaint: "Day 4 post-STEMI; sudden harsh pansystolic murmur, pulmonary edema, cold mottled extremities.",
    baselineVitals: {
      hr: 118,
      bp: "74/42",
      spo2: 89,
      rr: 30,
      temp: 36.8,
      gcs: 13
    },
    criticalDecisions: [
      {
        id: "dec-icu-1",
        action: "Emergency Bedside Echocardiography + Urgent Cardiothoracic Surgical Consult",
        outcomeEffect: "Confirms 14mm muscular VSR with left-to-right shunt; surgical team mobilised for mechanical support.",
        safe: true,
        feedback: "Prompt anatomical confirmation prevents catastrophic multiorgan failure.",
        timePenaltySec: 0
      },
      {
        id: "dec-icu-2",
        action: "High-Dose Peripheral Phenylephrine Infusion",
        outcomeEffect: "Increases left ventricular afterload, worsening left-to-right shunt fraction and pulmonary edema.",
        safe: false,
        feedback: "CONTRAINDICATED: Vasoconstrictors increase afterload in post-infarct VSR, worsening shunting.",
        timePenaltySec: 60
      },
      {
        id: "dec-icu-3",
        action: "Deploy Intra-Aortic Balloon Pump (IABP) / Impella for Afterload Reduction",
        outcomeEffect: "Reduces afterload, improves coronary perfusion, stabilizes hemodynamics bridge-to-surgery.",
        safe: true,
        feedback: "Guideline-directed mechanical circulatory support bridging to emergent operative repair.",
        timePenaltySec: 0
      }
    ],
    simulationState: "CRITICAL",
    safetyWarnings: [
      "Pulmonary Capillary Wedge Pressure >28 mmHg: Acute pulmonary flooding",
      "Cardiac Index 1.4 L/min/m²: Severe hypoperfusion state"
    ],
    isDemoMode: true,
    clinicalObjectives: [
      "Distinguish mechanical complications of MI (VSR vs acute MR)",
      "Manage mechanical afterload reduction without increasing shunting",
      "Expedite urgent cardiothoracic surgical intervention"
    ]
  },
  {
    id: "sim-surg-leak",
    title: "Post-Operative Anastomotic Leak with Feculent Peritonitis",
    environment: "Surgical Ward",
    patientName: "Arthur King",
    patientAge: 59,
    gender: "Male",
    chiefComplaint: "Post-op Day 5 anterior resection; sudden severe abdominal rigidity, fever 39.2°C, oliguria.",
    baselineVitals: {
      hr: 126,
      bp: "88/54",
      spo2: 95,
      rr: 26,
      temp: 39.2,
      gcs: 14
    },
    criticalDecisions: [
      {
        id: "dec-surg-1",
        action: "Immediate Fluid Resuscitation + IV Piperacillin/Tazobactam + Urgent Re-laparotomy Booking",
        outcomeEffect: "Stabilizes hemodynamic deficit; operative theater booked for source control wash-out.",
        safe: true,
        feedback: "Source control is the definitive determinant of survival in anastomotic breakdown.",
        timePenaltySec: 0
      },
      {
        id: "dec-surg-2",
        action: "Prescribe Oral Analgesia and Re-evaluate at Morning Ward Round (12 hours)",
        outcomeEffect: "Patient deteriorates into refractory septic shock with DIC and metabolic acidosis.",
        safe: false,
        feedback: "FATAL ERROR: Acute surgical abdomen with fever and tachycardia mandates immediate intervention.",
        timePenaltySec: 120
      }
    ],
    simulationState: "INITIALIZING",
    safetyWarnings: [
      "Peritoneal Rigidity: Involuntary guarding indicates visceral catastrophe",
      "Urine Output <0.3 ml/kg/hr for 3 hours: Acute kidney injury stage 2"
    ],
    isDemoMode: true,
    clinicalObjectives: [
      "Detect early subtle signs of anastomotic leakage on post-operative ward",
      "Institute urgent fluid resuscitation and broad-spectrum antimicrobial coverage",
      "Coordinate emergency re-exploration"
    ]
  }
];

export const PHYSICIAN_PROFILES: PhysicianProfile[] = [
  {
    id: "dr-sarah-jenkins",
    name: "Dr. Sarah Jenkins, MBBS, FRCEM",
    specialty: "Emergency Medicine",
    subspecialty: "Major Trauma & Resuscitation",
    hospitalAffiliation: "St Thomas' Hospital & King's Health Partners, London",
    reasoningScore: 92,
    guidelineAwareness: 88,
    simulationPerformance: 94,
    learningProgress: 89,
    radarSkills: [
      { axis: "Diagnostic Accuracy", score: 93, benchmark: 82 },
      { axis: "Guideline Compliance", score: 88, benchmark: 79 },
      { axis: "Time-to-Intervention", score: 95, benchmark: 75 },
      { axis: "Rare Case Recognition", score: 78, benchmark: 70 },
      { axis: "Communication & Safety", score: 96, benchmark: 84 },
      { axis: "Resource Stewardship", score: 87, benchmark: 80 }
    ],
    knowledgeGaps: [
      {
        topic: "Rare Trauma Cases: Blast Lung & Blast Compartment Syndromes",
        severity: "Medium",
        recommendation: "Complete the 3D Blast Injury Pressure Wave Simulation Module",
        evidenceTarget: "Lancet Military Medicine 2023 Guidelines"
      },
      {
        topic: "Toxicology: Complex Multi-Drug Antidepressant Overdose with Sodium Channel Blockade",
        severity: "Low",
        recommendation: "Review High-Dose Insulin Euglycemia Protocol & Sodium Bicarbonate titrated infusion",
        evidenceTarget: "NPIS Clinical Toxicology Consensus"
      }
    ],
    recentCasesCompleted: 142,
    certificationStatus: "MedicalPlab Certified Master Diagnostician (Level IV)",
    lastActive: "Active Now (Real-time Clinical Shift Sync)"
  },
  {
    id: "dr-marcus-vance",
    name: "Dr. Marcus Vance, MD, FACC",
    specialty: "Cardiology",
    subspecialty: "Interventional Electrophysiology",
    hospitalAffiliation: "Charité – Universitätsmedizin Berlin",
    reasoningScore: 95,
    guidelineAwareness: 94,
    simulationPerformance: 96,
    learningProgress: 91,
    radarSkills: [
      { axis: "Diagnostic Accuracy", score: 97, benchmark: 85 },
      { axis: "Guideline Compliance", score: 94, benchmark: 82 },
      { axis: "Time-to-Intervention", score: 92, benchmark: 78 },
      { axis: "Rare Case Recognition", score: 91, benchmark: 74 },
      { axis: "Communication & Safety", score: 93, benchmark: 85 },
      { axis: "Resource Stewardship", score: 89, benchmark: 81 }
    ],
    knowledgeGaps: [
      {
        topic: "Infiltrative Cardiomyopathies: Advanced Amyloidosis Strain Imaging",
        severity: "Low",
        recommendation: "Review apical sparing longitudinal strain pattern and 99mTc-DPD bone scintigraphy",
        evidenceTarget: "ESC Cardiomyopathy Guidelines 2023"
      }
    ],
    recentCasesCompleted: 218,
    certificationStatus: "MedicalPlab Fellow in AI-Augmented Cardiology",
    lastActive: "14 mins ago"
  }
];

export const HEALTHCARE_METRICS: HealthcareMetric[] = [
  {
    id: "hosp-guy-stthomas",
    hospitalName: "Guy's and St Thomas' NHS Foundation Trust",
    region: "UK NHS Trust",
    country: "United Kingdom",
    bedCapacity: 1250,
    overallDiagnosticAccuracy: 94.6,
    trainingGapIndex: 12.4, // lower is better
    clinicalWorkforceTrained: 3420,
    annualAdverseEventReduction: "-38.2%",
    regionalRank: 1,
    departmentalKPIs: [
      { department: "Emergency Department", throughput: "4.2 hrs avg", protocolAdherence: 96.2, costSavingsEst: "£2.4M/yr" },
      { department: "Acute Medical Unit", throughput: "1.8 days avg", protocolAdherence: 94.1, costSavingsEst: "£1.8M/yr" },
      { department: "Critical Care Unit", throughput: "92% ICU survival", protocolAdherence: 98.4, costSavingsEst: "£3.1M/yr" },
      { department: "General Surgery", throughput: "0.8% readmission", protocolAdherence: 93.7, costSavingsEst: "£1.2M/yr" }
    ]
  },
  {
    id: "hosp-mass-general",
    hospitalName: "Massachusetts General Hospital Health Network",
    region: "US Health System",
    country: "United States",
    bedCapacity: 1011,
    overallDiagnosticAccuracy: 95.8,
    trainingGapIndex: 9.8,
    clinicalWorkforceTrained: 4890,
    annualAdverseEventReduction: "-42.1%",
    regionalRank: 2,
    departmentalKPIs: [
      { department: "Emergency Services", throughput: "3.8 hrs avg", protocolAdherence: 97.5, costSavingsEst: "$5.8M/yr" },
      { department: "Cardiac ICU", throughput: "94% optimal discharge", protocolAdherence: 98.9, costSavingsEst: "$4.6M/yr" },
      { department: "Neurosciences", throughput: "91% thrombolysis SLA", protocolAdherence: 96.8, costSavingsEst: "$3.9M/yr" },
      { department: "Internal Medicine", throughput: "3.2 days LOS", protocolAdherence: 95.2, costSavingsEst: "$3.2M/yr" }
    ]
  },
  {
    id: "hosp-karolinska",
    hospitalName: "Karolinska University Hospital",
    region: "EU Academic Medical Center",
    country: "Sweden",
    bedCapacity: 1300,
    overallDiagnosticAccuracy: 96.2,
    trainingGapIndex: 8.4,
    clinicalWorkforceTrained: 2950,
    annualAdverseEventReduction: "-44.0%",
    regionalRank: 1,
    departmentalKPIs: [
      { department: "Trauma Center", throughput: "99.2% ATLS adherence", protocolAdherence: 99.1, costSavingsEst: "€3.4M/yr" },
      { department: "Cardiovascular", throughput: "42 min door-to-balloon", protocolAdherence: 98.5, costSavingsEst: "€2.9M/yr" },
      { department: "Oncology Unit", throughput: "100% molecular profiling", protocolAdherence: 97.3, costSavingsEst: "€2.7M/yr" }
    ]
  }
];

export const GOVERNANCE_METRICS: GovernanceMetric[] = [
  {
    id: "gov-evidence",
    title: "Clinical Evidence Coverage & Provenance",
    category: "Evidence Coverage",
    status: "Optimal",
    metricValue: "99.82%",
    benchmark: "Target >98.0%",
    auditTrailCount: 48920,
    lastCertifiedDate: "2026-09-01 (Continuous CI/CD Audit)",
    safetyDetails: "Every diagnostic claim links cryptographically to indexed NICE, SIGN, ESC, AHA or Cochrane systematic reviews.",
    humanInterventionRate: "0.04% flag rate",
    riskVectorScores: [
      { vector: "Citation Hallucination Vulnerability", riskLevel: "Minimal", score: 99.4 },
      { vector: "Guideline Stale-Data Risk", riskLevel: "Minimal", score: 98.8 },
      { vector: "Conflicting Recommendation Resolution", riskLevel: "Low", score: 95.6 }
    ]
  },
  {
    id: "gov-safety",
    title: "Real-Time Clinical Safety Shield",
    category: "Safety Validation",
    status: "Optimal",
    metricValue: "100.00% Zero-Omission",
    benchmark: "Zero Critical Failures",
    auditTrailCount: 128450,
    lastCertifiedDate: "2026-09-07",
    safetyDetails: "Automated verification layer guarantees life-critical red flags (e.g. anaphylaxis, spinal cord compression) cannot be omitted.",
    humanInterventionRate: "0.01%",
    riskVectorScores: [
      { vector: "Lethal Omission Filter", riskLevel: "Minimal", score: 100.0 },
      { vector: "Dosage Boundary Protection", riskLevel: "Minimal", score: 99.9 },
      { vector: "Contraindication Collision Engine", riskLevel: "Minimal", score: 99.7 }
    ]
  },
  {
    id: "gov-audit",
    title: "Cryptographic Tamper-Proof Audit History",
    category: "Audit History",
    status: "Compliant",
    metricValue: "SHA-256 Immutable Ledger",
    benchmark: "100% Traceability",
    auditTrailCount: 382900,
    lastCertifiedDate: "2026-09-08T05:00:00Z",
    safetyDetails: "All tutor generation prompts, reasoning chains, and student decisions logged to an append-only verifiable chain.",
    humanInterventionRate: "Automated Hash Verification",
    riskVectorScores: [
      { vector: "State Tampering Resistance", riskLevel: "Minimal", score: 100.0 },
      { vector: "Forensic Replay Fidelity", riskLevel: "Minimal", score: 99.8 },
      { vector: "GDPR / HIPAA Anonymization Integrity", riskLevel: "Minimal", score: 100.0 }
    ]
  },
  {
    id: "gov-oversight",
    title: "Senior Clinician-In-The-Loop Oversight",
    category: "Human Oversight",
    status: "Active Monitoring",
    metricValue: "142 Board-Certified MD Reviewers",
    benchmark: "100% Complex Cases Peer Reviewed",
    auditTrailCount: 18230,
    lastCertifiedDate: "2026-09-06",
    safetyDetails: "Multidisciplinary Clinical Advisory Board with power to pull, freeze, or hot-patch any AI node in real-time.",
    humanInterventionRate: "Human Sign-off Mandatory",
    riskVectorScores: [
      { vector: "Expert Consensus Agreement", riskLevel: "Low", score: 96.4 },
      { vector: "Disagreement Arbitration Latency", riskLevel: "Low", score: 94.2 }
    ]
  }
];

export const API_PRODUCTS: APIProduct[] = [
  {
    id: "api-reasoning",
    endpoint: "/clinical_reasoning",
    name: "Autonomous Clinical Reasoning Engine",
    version: "v3.2-enterprise",
    method: "POST",
    description: "Accepts patient presentation, vitals, biomarkers, and returns differential diagnosis with confidence rankings and NICE guideline citations.",
    latencyMs: 142,
    uptimePercent: 99.98,
    monthlyCalls: "14.2M calls/mo",
    curlSnippet: `curl -X POST https://api.medicalplab.com/v3/clinical_reasoning \\
  -H "Authorization: Bearer med_live_79f182c..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "presentation": "62yo male, central crushing chest pain, radiating to left jaw, diaphoresis",
    "vitals": {"hr": 104, "bp": "94/62", "spo2": 95},
    "investigations": {"ecg": "ST elevation >2mm in leads II, III, aVF"}
  }'`,
    responseSchemaSample: `{
  "primary_diagnosis": "Inferior ST-Elevation Myocardial Infarction (STEMI)",
  "confidence": 0.984,
  "guideline_provenance": "NICE NG185 Section 1.1",
  "recommended_urgent_action": "Emergency primary PCI transfer within 120m",
  "contraindicated": ["Nitrates if RV involvement suspected (V4R check)"],
  "differential": [
    {"condition": "Acute Aortic Dissection", "probability": 0.012},
    {"condition": "Acute Pericarditis", "probability": 0.004}
  ]
}`,
    enterpriseUseCases: [
      "Hospital Electronic Health Record (EHR) triage ambient co-pilot",
      "Telehealth real-time second opinion validation",
      "Pre-hospital ambulance paramedic decision support tablets"
    ],
    authentication: "mTLS + Bearer JWT + Organization HSM Signature"
  },
  {
    id: "api-evidence",
    endpoint: "/evidence_search",
    name: "Semantic Evidence & Provenance Search",
    version: "v2.8-fast",
    method: "POST",
    description: "Neural vector retrieval over curated medical consensus bodies (NICE, SIGN, PubMed, Cochrane, ESC, AHA) with citation provenance scoring.",
    latencyMs: 88,
    uptimePercent: 99.99,
    monthlyCalls: "28.5M calls/mo",
    curlSnippet: `curl -X POST https://api.medicalplab.com/v3/evidence_search \\
  -H "Authorization: Bearer med_live_79f182c..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "threshold for urgent decompression in tension pneumothorax",
    "guidelines_filter": ["NICE", "ATLS", "BTS"],
    "max_results": 3
  }'`,
    responseSchemaSample: `{
  "query_intent": "EMERGENCY_DECOMPRESSION_THRESHOLD",
  "evidence_results": [
    {
      "source": "ATLS 10th Edition / BTS Pleural Guidelines",
      "confidence": 0.992,
      "recommendation": "Clinical diagnosis mandates immediate needle thoracostomy prior to chest radiography.",
      "level_of_evidence": "Class 1 Level A"
    }
  ]
}`,
    enterpriseUseCases: [
      "Medical education software citation backbones",
      "Clinical audit automation platforms",
      "Pharmaceutical scientific affair queries"
    ],
    authentication: "API Key + Domain IP Whitelist"
  },
  {
    id: "api-simulation",
    endpoint: "/simulation_engine",
    name: "High-Fidelity Patient State Simulator",
    version: "v4.0-physio",
    method: "POST",
    description: "Deterministic physiological simulation step engine computing multi-compartmental PK/PD, gas exchange, and hemodynamics per intervention.",
    latencyMs: 35,
    uptimePercent: 99.96,
    monthlyCalls: "6.8M calls/mo",
    curlSnippet: `curl -X POST https://api.medicalplab.com/v3/simulation_engine/step \\
  -H "Authorization: Bearer med_live_79f182c..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "scenario_id": "sim-ed-trauma",
    "intervention": "needle_thoracostomy_left_5th_aal",
    "elapsed_seconds": 180
  }'`,
    responseSchemaSample: `{
  "patient_status": "STABILIZING",
  "vitals_delta": {
    "hr": {"before": 138, "after": 102},
    "bp": {"before": "82/48", "after": "112/70"},
    "spo2": {"before": 84, "after": 94}
  },
  "physiological_mechanisms": "Intrathoracic pressure resolved from 24 to 4 cmH2O, restoring vena cava preload.",
  "time_elapsed_penalty": 0
}`,
    enterpriseUseCases: [
      "Virtual Reality / Augmented Reality medical simulation headsets",
      "Nursing and resident simulation labs",
      "Medical device user-interface human factors evaluation"
    ],
    authentication: "WebSocket Session Token / REST Bearer"
  },
  {
    id: "api-learning",
    endpoint: "/learning_analysis",
    name: "Cognitive Knowledge Gap & Skill Diagnostic API",
    version: "v2.1-edu",
    method: "POST",
    description: "Computes Bayesian IRT (Item Response Theory) knowledge frontier, detecting hidden clinical reasoning flaws and prescribing remediation.",
    latencyMs: 110,
    uptimePercent: 99.97,
    monthlyCalls: "11.1M calls/mo",
    curlSnippet: `curl -X POST https://api.medicalplab.com/v3/learning_analysis \\
  -H "Authorization: Bearer med_live_79f182c..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_session_logs": [{"case_id": "trauma_01", "actions": ["ecg_ordered", "needle_delayed"], "time_ms": 42000}]
  }'`,
    responseSchemaSample: `{
  "reasoning_theta": 1.84,
  "percentile_rank": 92.4,
  "critical_flaw_detected": "Delayed procedural intervention under emergency shock conditions",
  "targeted_curriculum": ["ATLS Rapid Primary Survey Drills", "Obstructive Shock Micro-Cases"]
}`,
    enterpriseUseCases: [
      "Medical school dean examination telemetry",
      "National residency matching analytics",
      "Hospital continuous professional development (CPD) accreditation"
    ],
    authentication: "OAuth2 Provider / JWT"
  }
];

export const KNOWLEDGE_SYNC_EVENTS: KnowledgeSyncEvent[] = [
  {
    id: "sync-1",
    timestamp: "10 mins ago",
    stage: "New Medical Evidence",
    title: "NEJM: New SGLT2i Cardioprotection Trial Published",
    source: "New England Journal of Medicine (DOI: 10.1056/NEJMoa26019)",
    status: "Synchronized",
    deltaItems: 14,
    trustScore: 99.6
  },
  {
    id: "sync-2",
    timestamp: "24 mins ago",
    stage: "Validation Engine",
    title: "Automated NICE NG185 Guideline Discrepancy Check",
    source: "Clinical AI Integrity Engine v4.2",
    status: "Validated",
    deltaItems: 42,
    trustScore: 99.9
  },
  {
    id: "sync-3",
    timestamp: "45 mins ago",
    stage: "Knowledge Graph Update",
    title: "Ontology Triplet Linkage: Sepsis-6 Phenotype Updates",
    source: "MedicalPlab Unified Graph Store",
    status: "Synchronized",
    deltaItems: 128,
    trustScore: 98.9
  },
  {
    id: "sync-4",
    timestamp: "1 hour ago",
    stage: "Question Bank Update",
    title: "High-Yield Scenario Distractor Recalibration",
    source: "PLAB 1 / UKMLA Assessment Engine",
    status: "Synchronized",
    deltaItems: 65,
    trustScore: 99.2
  },
  {
    id: "sync-5",
    timestamp: "2 hours ago",
    stage: "Tutor Update",
    title: "Socratic Dialog Weights Adjusted for Pediatric Sepsis",
    source: "AI Tutor Multimodal Core",
    status: "Propagating",
    deltaItems: 19,
    trustScore: 99.4
  },
  {
    id: "sync-6",
    timestamp: "3 hours ago",
    stage: "Simulation Update",
    title: "ECMO Cannulation Pressure Response Model Updated",
    source: "PhysioSim Hemodynamics Engine",
    status: "Synchronized",
    deltaItems: 31,
    trustScore: 98.7
  }
];

export const ACADEMY_PROGRAMS: AcademyProgram[] = [
  {
    id: "acad-prog-reasoning",
    title: "Executive Fellowship in Advanced Clinical Reasoning & Diagnostic AI",
    certificateType: "Clinical Reasoning",
    partnerName: "Imperial College London Faculty of Medicine",
    partnerType: "Universities",
    accreditationBody: "Royal College of Physicians (RCP) 30 CPD Credits",
    durationWeeks: 12,
    creditsEcts: 15,
    enrolledScholars: 2140,
    curriculumModules: [
      "Cognitive Biases in Emergency Triage & Diagnostic Error Mitigation",
      "Bayesian Likelihood Modeling in Complex Multimorbidity",
      "AI Co-pilot Symbiosis in Ambulatory & Acute Settings",
      "Evidence Provenance & Algorithmic Safety Oversight"
    ],
    alumniPassRate: 98.4
  },
  {
    id: "acad-prog-emergency",
    title: "Global Diploma in Acute Resuscitation & Disaster Response",
    certificateType: "Emergency Medicine",
    partnerName: "King's Health Partners / London Ambulance Service",
    partnerType: "Hospitals",
    accreditationBody: "European Society for Emergency Medicine (EUSEM)",
    durationWeeks: 16,
    creditsEcts: 20,
    enrolledScholars: 3890,
    curriculumModules: [
      "Damage-Control Resuscitation in Penetrating & Blast Trauma",
      "Vasoactive Hemodynamic Rescue in Toxic Shock",
      "Point-of-Care Ultrasound (POCUS) Multimodal Interpretation",
      "High-Fidelity Virtual Reality Resus Leadership"
    ],
    alumniPassRate: 97.2
  },
  {
    id: "acad-prog-ai",
    title: "Certified Healthcare AI Systems Architect & Safety Officer",
    certificateType: "AI Assisted Medicine",
    partnerName: "World Health Organization Collaborating Centers",
    partnerType: "Training Centers",
    accreditationBody: "International Medical Informatics Association (IMIA)",
    durationWeeks: 8,
    creditsEcts: 10,
    enrolledScholars: 1560,
    curriculumModules: [
      "Clinical AI Ethics, Bias Detection & Health Equity",
      "Software as a Medical Device (SaMD) Regulatory Pathways (FDA/MDR)",
      "Continuous Model Drift Monitoring & Retraining Infrastructure",
      "Fail-Safe Human-in-the-Loop Clinical Protocols"
    ],
    alumniPassRate: 99.1
  }
];

export const STAGE_X_DEMO_SCENES: StageXDemoScene[] = [
  {
    sceneNumber: 1,
    title: "The Global Medical Knowledge Brain",
    subtitle: "Medical knowledge becomes connected intelligence",
    durationSec: 60,
    screenAction: "Explore the live multidimensional diagnostic flow: Disease -> Symptoms -> Investigations -> Treatment -> Evidence -> Clinical Outcomes. Show instant citation provenance.",
    presenterScript: "Judges and investors: today medicine is trapped in static textbooks and fragmented PDF guidelines. With MedicalPlab's Global Knowledge Brain, medical science becomes a living, computable neural graph. Every disease connects to its exact evidence pedigree with sub-second provenance.",
    investorTakeaway: "MedicalPlab owns the structured knowledge graph layer of global healthcare, creating an insurmountable proprietary data moat.",
    targetModuleId: "brain",
    visualHighlights: [
      "Dynamic 6-tier medical pathway graph",
      "Cryptographic NICE/ESC evidence badges",
      "Real-time relationship highlighting & metric telemetry"
    ]
  },
  {
    sceneNumber: 2,
    title: "AI Medical Ecosystem & Marketplace",
    subtitle: "MedicalPlab becomes infrastructure",
    durationSec: 60,
    screenAction: "Navigate the global provider marketplace showcasing AI Agents, Simulation Modules, and Clinical Packages authored by top universities and hospitals.",
    presenterScript: "We are not building a single point tool. MedicalPlab is the App Store and Operating System of clinical medicine. Top teaching hospitals, researchers, and universities publish their clinical agents directly onto our verified infrastructure.",
    investorTakeaway: "Two-sided network effects: universities and hospital systems distribute clinical IP directly through MedicalPlab, unlocking enterprise SaaS marketplace revenue.",
    targetModuleId: "marketplace",
    visualHighlights: [
      "Verified / Prototype / Future Vision classification badges",
      "Multi-institutional contributor network",
      "Enterprise licensing & compliance telemetry"
    ]
  },
  {
    sceneNumber: 3,
    title: "Virtual Healthcare Simulation Universe",
    subtitle: "Train without risking patients",
    durationSec: 60,
    screenAction: "Trigger an active Emergency Department crisis (polytrauma tension pneumothorax) with live hemodynamics, time penalties, and physiological safety warnings.",
    presenterScript: "Every clinical decision carries life-or-death consequences. In our Simulation Universe, clinicians make high-stakes resuscitation decisions in an exact deterministic physiological twin before ever touching a human patient.",
    investorTakeaway: "Replaces multi-million dollar mannequin simulation labs with scalable, browser-native 60fps clinical flight simulation.",
    targetModuleId: "simulation",
    visualHighlights: [
      "Live physiological patient vitals (HR, BP, SpO2, Lactate)",
      "Instant feedback on safe vs contraindicated interventions",
      "Clear regulatory demo & simulation safety markings"
    ]
  },
  {
    sceneNumber: 4,
    title: "Physician Digital Twin & Lifelong Intelligence",
    subtitle: "Continuous clinical improvement",
    durationSec: 60,
    screenAction: "Examine a real-world Emergency Physician's digital cognitive profile: 92% clinical reasoning, 88% guideline awareness, radar competencies, and targeted rare-case remediation.",
    presenterScript: "Meet the Physician Digital Twin. For the first time, a doctor's clinical competencies, diagnostic instincts, and knowledge gaps are quantified continuously throughout their 30-year medical career, delivering surgical precision remediation.",
    investorTakeaway: "High-retention B2B credentialing and workforce optimization platform for national health ministries and hospital groups.",
    targetModuleId: "twin",
    visualHighlights: [
      "Multi-axis diagnostic radar chart",
      "AI-identified micro-knowledge gaps with targeted paper citations",
      "Lifelong credentialing and clinical shift sync telemetry"
    ]
  },
  {
    sceneNumber: 5,
    title: "Global Healthcare Operating System",
    subtitle: "Medical intelligence everywhere",
    durationSec: 60,
    screenAction: "Showcase the enterprise multi-hospital analytics dashboard and the public developer API suite (/clinical_reasoning, /evidence_search, /simulation_engine).",
    presenterScript: "This is our endgame. MedicalPlab is the intelligence infrastructure layer powering modern medicine. From bedside hospital EHRs to ambulance tablets and global university credentialing, our APIs deliver trusted medical intelligence everywhere on Earth.",
    investorTakeaway: "Massive TAM expansion from medical education into hospital clinical operations, pharma trials, and enterprise AI co-pilot infrastructure.",
    targetModuleId: "analytics",
    visualHighlights: [
      "NHS Trust & US Health System operational KPI cards",
      "Developer API portal with live cURL code snippets and response latency",
      "Autonomous continuous knowledge sync pipeline"
    ]
  }
];
