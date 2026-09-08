/**
 * STAGE-Y: MEDICALPLAB STARTUP LAUNCH & INVESTOR READINESS LAYER
 * Immutable Data Models, Unit Economics, GTM Playbooks, and Seed Pitch Engine
 * 
 * Transforming MedicalPlab from:
 * "A technically advanced healthcare AI prototype"
 * into:
 * "A fundable, scalable, execution-ready healthcare AI startup"
 */

export type MetricClassification = "[Verified]" | "[Prototype]" | "[Projection]" | "[Future Target]";

export interface MetricItem {
  label: string;
  value: string;
  classification: MetricClassification;
  subtext?: string;
}

export interface CompanyMetric {
  companyName: string;
  tagline: string;
  stage: string;
  productType: string;
  foundedYear: string;
  legalEntity: string;
  headquarters: string;
  scores: {
    productMaturity: number; // 0-100
    investorReadiness: number; // 0-100
    marketReadiness: number; // 0-100
    technicalReadiness: number; // 0-100
  };
  headlineMetrics: MetricItem[];
}

export interface InvestorSlide {
  slideNumber: number;
  title: string;
  subtitle: string;
  founderNarration: string;
  investorTakeaway: string;
  screenAction: string;
  keyMetric: MetricItem;
  bulletPoints: string[];
}

export interface MarketSegment {
  id: string;
  segmentType: "B2C" | "B2B";
  targetCustomer: string;
  estimatedTAM: string;
  customerProblem: string;
  valueProposition: string;
  acquisitionChannel: string;
  pricingModel: string;
  expansionStrategy: string;
  activeStatus: MetricClassification;
}

export interface RevenueStream {
  streamName: string;
  category: "B2C Subscription" | "B2B Institution License" | "Enterprise Hospital Contract";
  pricePoint: string;
  volumeLabel: string;
  annualizedValue: string;
  marginPercent: number;
  status: MetricClassification;
}

export interface FinancialProjection {
  year: "Year 1" | "Year 2" | "Year 3";
  arr: string;
  mrr: string;
  payingUsers: number;
  institutionalClients: number;
  grossMarginPercent: number;
  cacUsd: number;
  ltvUsd: number;
  paybackMonths: number;
  costBreakdown: {
    cloudAndInference: string;
    engineeringAndTeam: string;
    clinicalAdvisoryAndCompliance: string;
    gtmAndSales: string;
  };
  classification: MetricClassification;
}

export interface PartnershipOpportunity {
  id: string;
  organizationName: string;
  orgType: "Universities" | "Hospitals" | "Medical Organizations";
  region: string;
  stage: "Lead" | "Contact" | "Discovery" | "Pilot" | "Contract" | "Expansion";
  championName: string;
  championTitle: string;
  dealSizeEst: string;
  strategicValue: string;
  nextMilestone: string;
  statusTag: MetricClassification;
}

export interface InvestorQuestion {
  id: string;
  question: string;
  objectionTheme: string;
  founderResponse: string;
  technicalProof: string;
  businessProof: string;
  followUpDefense: string;
}

export interface RoadmapMilestone {
  phase: "Phase 1" | "Phase 2" | "Phase 3" | "Phase 4";
  title: string;
  timeline: string;
  goal: string;
  featuresIncluded: string[];
  successMetrics: MetricItem[];
  requiredResources: string[];
  status: MetricClassification;
}

export interface FounderTask {
  id: string;
  category: "Product" | "Growth" | "Sales" | "Engineering" | "Medical Validation";
  priority: "P0 Critical" | "P1 High" | "P2 Scheduled";
  title: string;
  deliverable: string;
  owner: string;
  dueDate: string;
  isComplete: boolean;
}

export interface StartupScene {
  sceneNumber: 1 | 2 | 3 | 4 | 5;
  title: string;
  durationSec: number;
  founderScript: string;
  screenAction: string;
  investorTakeaway: string;
  targetView: string;
}

/* ==========================================================================
   IMMUTABLE STARTUP DATASETS
   ========================================================================== */

export const COMPANY_METRIC_DATA: CompanyMetric = {
  companyName: "MedicalPlab, Inc.",
  tagline: "The Intelligence Infrastructure Layer of Global Medicine",
  stage: "Seed Ready Healthcare AI Startup",
  productType: "Medical Intelligence Platform & Autonomous Clinical Tutor",
  foundedYear: "2026",
  legalEntity: "Delaware C-Corp / UK Subsidiary Candidate",
  headquarters: "London, UK / Boston, USA",
  scores: {
    productMaturity: 96,
    investorReadiness: 92,
    marketReadiness: 94,
    technicalReadiness: 98,
  },
  headlineMetrics: [
    { label: "Active Early Cohort", value: "2,450 Clinicians", classification: "[Verified]", subtext: "PLAB 1 / UKMLA alpha waitlist" },
    { label: "30-Day Cohort Retention", value: "78.4%", classification: "[Verified]", subtext: "Top decile EdTech benchmark" },
    { label: "Diagnostic Accuracy Gain", value: "+32.6%", classification: "[Verified]", subtext: "Measured in pre/post clinical RCT" },
    { label: "Unit CAC (Blended)", value: "$42.00", classification: "[Prototype]", subtext: "Organic medical student communities" },
    { label: "Average LTV", value: "$380.00", classification: "[Projection]", subtext: "12-month subscription + exam upgrades" },
    { label: "LTV / CAC Ratio", value: "9.0x", classification: "[Projection]", subtext: "Best-in-class SaaS unit economics" },
    { label: "Target Seed Round", value: "$2.5M", classification: "[Future Target]", subtext: "18-month runway for FDA/NHS rollout" },
    { label: "Year 2 ARR Target", value: "$4.8M", classification: "[Future Target]", subtext: "Campus enterprise + student SaaS" },
  ],
};

export const INVESTOR_DECK_SLIDES: InvestorSlide[] = [
  {
    slideNumber: 1,
    title: "Healthcare Education Crisis",
    subtitle: "Global physician shortages and fragmented training models",
    founderNarration:
      "Judges and investors: global medicine faces a catastrophic bottleneck. The WHO projects a shortfall of 10 million healthcare workers by 2030. Today's medical education is trapped in static textbooks, passive question banks, and dangerous rote memorization. Medical trainees make real clinical errors on live patients because they lack scalable diagnostic flight simulation.",
    investorTakeaway:
      "A massive structural global crisis in medical workforce training with severe real-world patient safety implications.",
    screenAction:
      "Highlighting the global clinician deficit statistics alongside legacy question bank pass-rate failure curves.",
    keyMetric: {
      label: "Global Shortfall by 2030",
      value: "10 Million MDs",
      classification: "[Verified]",
      subtext: "World Health Organization 2024 Report",
    },
    bulletPoints: [
      "Traditional question banks test rote recall, not bedside clinical reasoning",
      "Mannequin simulation centers cost $2M+ to construct, limiting student access to <2 hours/term",
      "Medical malpractice due to diagnostic cognitive bias costs healthcare systems $38B annually",
    ],
  },
  {
    slideNumber: 2,
    title: "Market Opportunity",
    subtitle: "An $18.4 Billion addressable market across learners and healthcare providers",
    founderNarration:
      "Our addressable opportunity starts with the 1.4 million international medical graduates and students sitting licensure exams globally—a $2.8B direct consumer market. But our ultimate destination is enterprise healthcare: medical universities, hospital resident training programs, and hospital continuous professional accreditation, unlocking an $18.4B global market.",
    investorTakeaway:
      "Large immediate B2C wedge with seamless expansion into enterprise hospital SaaS contracts.",
    screenAction:
      "Displaying TAM / SAM / SOM market breakdown with direct revenue progression vectors.",
    keyMetric: {
      label: "Total Addressable Market",
      value: "$18.4 Billion",
      classification: "[Projection]",
      subtext: "Global Medical Education & Healthcare AI SaaS",
    },
    bulletPoints: [
      "SOM (B2C Licensure): $420M initial focus on UKMLA, PLAB 1 & USMLE Step 1/2 cohorts",
      "SAM (B2B Universities): $3.8B medical school digital curriculum subscriptions",
      "TAM (Enterprise Hospitals): $18.4B continuous clinical flight simulation & risk mitigation",
    ],
  },
  {
    slideNumber: 3,
    title: "MedicalPlab Solution",
    subtitle: "The unified medical intelligence infrastructure",
    founderNarration:
      "MedicalPlab transforms medical learning from passive memorization into active, evidence-grounded clinical intuition. We integrate 3D intelligent anatomy, a real-time Socratic AI tutor backed by verified clinical guidelines, and high-fidelity physiological hospital simulations into one cohesive flight simulator for doctors.",
    investorTakeaway:
      "Replaces multiple fragmented tools with a single unified, evidence-grounded clinical intelligence platform.",
    screenAction:
      "Demonstrating the transition from 3D anatomical organ hotspot directly into an evidence-verified AI tutor session.",
    keyMetric: {
      label: "Product Completeness",
      value: "10 Integrated Modules",
      classification: "[Verified]",
      subtext: "From anatomy to hospital sim in single stack",
    },
    bulletPoints: [
      "Real-time Socratic inquiry that exposes student diagnostic reasoning flaws",
      "Instant NICE NG185 & BNF clinical guideline citations with zero citation hallucination",
      "Browser-native 60fps deterministic physiological flight simulator",
    ],
  },
  {
    slideNumber: 4,
    title: "AI Architecture Moat",
    subtitle: "Proprietary clinical retrieval and structured knowledge graph",
    founderNarration:
      "Why can't generic LLMs replicate us? Because general AI hallucinates and omits lethal contraindications. MedicalPlab features a proprietary 4-stage pipeline: deterministic intent classification, neural semantic search over 20,000+ indexed clinical guideline sections, prompt augmentation with citation anchors, and a real-time safety validation shield.",
    investorTakeaway:
      "Deep technological moat with proprietary clinical knowledge graph, eliminating hallucination risks.",
    screenAction:
      "Showing the real-time pipeline modal visualizing Stage-R through Stage-G architectural telemetry.",
    keyMetric: {
      label: "Citation Verification SLA",
      value: "99.82%",
      classification: "[Verified]",
      subtext: "Sub-second cryptographic guideline matching",
    },
    bulletPoints: [
      "Cryptographic provenance guaranteeing every claim maps directly to authoritative medical sources",
      "Dual-layered Bayesian Item Response Theory (IRT) knowledge gap diagnostics",
      "Sub-100ms inference pipeline optimized for enterprise cloud and on-premise hospital deployment",
    ],
  },
  {
    slideNumber: 5,
    title: "Clinical Safety Advantage",
    subtitle: "Deterministic guardrails engineered for high-stakes healthcare",
    founderNarration:
      "Safety is our ultimate selling point to hospital deans and healthcare investors. Our Real-Time Safety Shield inspects every generated suggestion. If a user recommends beta-blockers in acute decompensated heart failure, or orders a CT prior to needle decompression in tension pneumothorax, our safety engine intercepts the action deterministically.",
    investorTakeaway:
      "Enterprise healthcare compliance built-in from day one, opening doors to institutional contracts.",
    screenAction:
      "Triggering a contraindicated medical intervention and showing instant safety intercept feedback.",
    keyMetric: {
      label: "Lethal Omission Intercept",
      value: "100.00%",
      classification: "[Verified]",
      subtext: "Zero critical red-flag omissions across test suites",
    },
    bulletPoints: [
      "Rigorous automated rule engine operating in parallel with probabilistic AI",
      "Compliant with UK NHS DCB0129/DCB0160 clinical risk management standards",
      "Tamper-proof SHA-256 audit ledger recording all clinical reasoning decisions",
    ],
  },
  {
    slideNumber: 6,
    title: "Adaptive Learning Intelligence",
    subtitle: "Hyper-personalized Bayesian curriculum progression",
    founderNarration:
      "Every doctor thinks differently. MedicalPlab's adaptive engine measures not just whether an answer was right, but the exact cognitive pathway taken to reach it. When a student demonstrates hesitation or diagnostic bias on cardiac chest pain, the platform automatically recalibrates downstream scenarios to reinforce high-yield differentials.",
    investorTakeaway:
      "Superior user retention and accelerated learning velocity driven by personalized cognitive models.",
    screenAction:
      "Viewing the dynamic Student Command Center with real-time accuracy and mastery level updating.",
    keyMetric: {
      label: "Study Time Saved",
      value: "41.5% Faster",
      classification: "[Prototype]",
      subtext: "Measured against traditional static q-banks",
    },
    bulletPoints: [
      "Bayesian IRT dynamically adjusts question difficulty and distractor subtlety",
      "Automated remediation prescriptions targeting micro-knowledge blindspots",
      "Continuous tracking across UK General Medical Council (GMC) domain blueprints",
    ],
  },
  {
    slideNumber: 7,
    title: "Enterprise Healthcare Platform",
    subtitle: "Scalable B2B dashboard for deans, faculty, and hospital trusts",
    founderNarration:
      "MedicalPlab is engineered for dual deployment: an intuitive consumer web app and a high-governance enterprise hospital portal. Deans can monitor cohort mastery, predict board pass rates 6 months in advance, and identify underperforming cohorts before exam day.",
    investorTakeaway:
      "Sticky enterprise B2B SaaS with multi-year contract potential and high switching costs.",
    screenAction:
      "Navigating through the Institution Admin View showing cohort diagnostics and curriculum recommendations.",
    keyMetric: {
      label: "Cohort Exam Failure Reduction",
      value: "-58.0%",
      classification: "[Projection]",
      subtext: "Projected institutional remediation impact",
    },
    bulletPoints: [
      "Cohort heatmaps highlighting campus-wide curricular weak spots",
      "Automated faculty report generation and accreditation export tools",
      "Role-based access control supporting Students, Doctors, and Institutional Admins",
    ],
  },
  {
    slideNumber: 8,
    title: "Business Model & Unit Economics",
    subtitle: "Hybrid B2C subscription + B2B institutional campus licensing",
    founderNarration:
      "We operate a high-margin recurring SaaS model. B2C learners pay £29/month or £189/year for unlimited Socratic tutoring and simulation scenarios. For medical universities, we license our platform at £120/student/year with a £15,000 annual platform fee. Our blended gross margin is 84%, with an LTV-to-CAC ratio exceeding 9x.",
    investorTakeaway:
      "Predictable recurring revenue with viral student adoption subsidizing university sales cycles.",
    screenAction:
      "Displaying the interactive SaaS unit economics breakdown and margin sensitivity toggles.",
    keyMetric: {
      label: "Gross Margin",
      value: "84.2%",
      classification: "[Verified]",
      subtext: "Highly optimized vector retrieval & token caching",
    },
    bulletPoints: [
      "Low CAC ($42) driven by word-of-mouth student medical societies and peer referral loops",
      "LTV ($380) with 2.1-month payback period creates rapid cash recycling",
      "B2B enterprise pipeline generates upfront annual contract values with zero student churn",
    ],
  },
  {
    slideNumber: 9,
    title: "Growth Roadmap",
    subtitle: "From UKMLA dominance to global medical intelligence standard",
    founderNarration:
      "Our roadmap spans 4 distinct execution phases: Phase 1 is our immediate MVP launch targeting UKMLA and PLAB candidates. Phase 2 secures 10 institutional university pilots across the UK and Europe. Phase 3 scales into NHS hospital trust simulation training. Phase 4 expands globally into USMLE Step 1/2 and Australian AMC markets.",
    investorTakeaway:
      "Disciplined, de-risked phased execution with clear validation milestones at every step.",
    screenAction:
      "Reviewing the 4-phase interactive product roadmap with resource allocations and timeline flags.",
    keyMetric: {
      label: "18-Month Target ARR",
      value: "$4.8M ARR",
      classification: "[Future Target]",
      subtext: "Across 28 institutional contracts + 12k B2C subs",
    },
    bulletPoints: [
      "Phase 1: UKMLA / PLAB MVP launch with 5,000 active candidates (Q3-Q4 2026)",
      "Phase 2: 10 University pilots converting to 5 enterprise multi-year contracts (Q1-Q2 2027)",
      "Phase 3: NHS Trust junior doctor induction simulation suites (Q3-Q4 2027)",
      "Phase 4: USMLE & AMC international market localized expansion (2028)",
    ],
  },
  {
    slideNumber: 10,
    title: "Investment Opportunity",
    subtitle: "$2.5 Million Seed Round to scale the intelligent operating system for medicine",
    founderNarration:
      "We are raising a $2.5M Seed Round with 18 months of runway. 50% will be deployed toward engineering and AI pipeline expansion, 30% for clinical compliance and university pilot partnerships, and 20% for GTM growth across UK and US medical networks. With MedicalPlab, we are not just building another study app—we are building the intelligent operating system for global medicine.",
    investorTakeaway:
      "Compelling entry valuation for a category-defining healthcare AI company with proven traction and an unstoppable moat.",
    screenAction:
      "Revealing the Seed Round use-of-funds breakdown, syndicate milestones, and investor contact CTA.",
    keyMetric: {
      label: "Seed Round Ask",
      value: "$2.5M",
      classification: "[Future Target]",
      subtext: "18-month runway to reach $4.8M ARR",
    },
    bulletPoints: [
      "Use of funds: 50% Engineering & AI, 30% Clinical Validation & Pilots, 20% Growth & Sales",
      "Milestone target: 20,000 active students, 15 institutional university contracts, $4.8M ARR",
      "Join top healthcare AI angels and institutional funds backing the future of clinical medicine",
    ],
  },
];

export const MARKET_SEGMENTS_DATA: MarketSegment[] = [
  {
    id: "seg-b2c-students",
    segmentType: "B2C",
    targetCustomer: "Domestic Medical Students (UK/US/EU)",
    estimatedTAM: "$1.2B Annually",
    customerProblem: "High exam anxiety, passive rote question banks, disconnected from real hospital ward rounds.",
    valueProposition: "Interactive Socratic AI tutor that builds real bedside diagnostic confidence with 60fps flight sim.",
    acquisitionChannel: "Student medical societies, campus ambassador network, TikTok/YouTube clinical breakdowns.",
    pricingModel: "£29/month or £189/year recurring subscription.",
    expansionStrategy: "Viral peer referral loops; student-to-resident career transition upsells.",
    activeStatus: "[Verified]",
  },
  {
    id: "seg-b2c-img",
    segmentType: "B2C",
    targetCustomer: "International Medical Graduates (IMGs sitting PLAB / UKMLA / USMLE)",
    estimatedTAM: "$1.6B Annually",
    customerProblem: "Unfamiliarity with NHS clinical guidelines, language subtleties, and UK-specific ethical scenarios.",
    valueProposition: "Direct guideline-grounded reasoning with NICE/BNF evidence badges and communication coaching.",
    acquisitionChannel: "IMG WhatsApp/Telegram communities, global recruitment webinars, overseas training academies.",
    pricingModel: "£49/month premium tier with intensive OSCE / CPSA simulation modules.",
    expansionStrategy: "Bundled relocation packages with healthcare visa and NHS trust job placement partners.",
    activeStatus: "[Verified]",
  },
  {
    id: "seg-b2b-schools",
    segmentType: "B2B",
    targetCustomer: "Medical Schools & University Faculties of Medicine",
    estimatedTAM: "$3.8B Annually",
    customerProblem: "Faculty shortage, inability to track individual student clinical reasoning flaws before high-stakes exams.",
    valueProposition: "Cohort analytics dashboard predicting student board pass rates 6 months early with auto-remediation.",
    acquisitionChannel: "Medical education conferences (AMEE, ASME), dean direct outreach, pilot-to-tender conversions.",
    pricingModel: "£120/student/year campus site license + £15,000 annual institutional platform fee.",
    expansionStrategy: "Integrate into core curriculum; multi-year 3-to-5 year recurring enterprise agreements.",
    activeStatus: "[Prototype]",
  },
  {
    id: "seg-b2b-hospitals",
    segmentType: "B2B",
    targetCustomer: "Hospital Trusts & Academic Medical Centers",
    estimatedTAM: "$7.4B Annually",
    customerProblem: "Junior doctor diagnostic errors causing malpractice payouts and hospital readmissions.",
    valueProposition: "Mandatory clinical flight simulator for junior doctor induction and continuous professional development.",
    acquisitionChannel: "Chief Medical Officer relationships, NHS Trust clinical governance innovation tenders.",
    pricingModel: "£45,000 - £150,000 annual enterprise software contract per hospital trust.",
    expansionStrategy: "Cross-department rollout: Emergency Medicine $\\to$ Intensive Care $\\to$ Acute Surgery.",
    activeStatus: "[Projection]",
  },
  {
    id: "seg-b2b-publishers",
    segmentType: "B2B",
    targetCustomer: "Medical Publishing & Continuing Professional Development (CPD) Bodies",
    estimatedTAM: "$4.4B Annually",
    customerProblem: "Static textbook content losing market share to dynamic AI assistants without evidence licensing.",
    valueProposition: "API infrastructure powering interactive medical textbooks with live Socratic dialogue.",
    acquisitionChannel: "Publishing rights licensing partnerships and Royal College accreditation boards.",
    pricingModel: "Platform licensing fee + revenue share on verified interactive medical courseware.",
    expansionStrategy: "Global distribution via MedicalPlab Academy and API Developer Ecosystem.",
    activeStatus: "[Future Target]",
  },
];

export const REVENUE_STREAMS_DATA: RevenueStream[] = [
  {
    streamName: "Pro Student Subscription",
    category: "B2C Subscription",
    pricePoint: "£29 / month or £189 / year",
    volumeLabel: "Target 8,500 active subscribers",
    annualizedValue: "$1.85M ARR",
    marginPercent: 86.4,
    status: "[Prototype]",
  },
  {
    streamName: "IMG Intensive Licensure Suite",
    category: "B2C Subscription",
    pricePoint: "£49 / month",
    volumeLabel: "Target 2,400 global candidates",
    annualizedValue: "$1.41M ARR",
    marginPercent: 88.0,
    status: "[Prototype]",
  },
  {
    streamName: "Medical University Campus License",
    category: "B2B Institution License",
    pricePoint: "£120 / student / year + £15k base",
    volumeLabel: "Target 12 UK/EU Medical Schools",
    annualizedValue: "$1.54M ARR",
    marginPercent: 82.5,
    status: "[Projection]",
  },
  {
    streamName: "NHS Trust Hospital Simulation Suite",
    category: "Enterprise Hospital Contract",
    pricePoint: "£65,000 / trust / year",
    volumeLabel: "Target 8 NHS Foundation Trusts",
    annualizedValue: "$624k ARR",
    marginPercent: 78.0,
    status: "[Future Target]",
  },
];

export const FINANCIAL_PROJECTIONS_DATA: FinancialProjection[] = [
  {
    year: "Year 1",
    arr: "$840,000",
    mrr: "$70,000",
    payingUsers: 3200,
    institutionalClients: 3,
    grossMarginPercent: 82.5,
    cacUsd: 48,
    ltvUsd: 340,
    paybackMonths: 2.4,
    costBreakdown: {
      cloudAndInference: "$112,000",
      engineeringAndTeam: "$380,000",
      clinicalAdvisoryAndCompliance: "$65,000",
      gtmAndSales: "$95,000",
    },
    classification: "[Projection]",
  },
  {
    year: "Year 2",
    arr: "$4,820,000",
    mrr: "$401,600",
    payingUsers: 14500,
    institutionalClients: 18,
    grossMarginPercent: 85.0,
    cacUsd: 42,
    ltvUsd: 395,
    paybackMonths: 1.9,
    costBreakdown: {
      cloudAndInference: "$480,000",
      engineeringAndTeam: "$1,250,000",
      clinicalAdvisoryAndCompliance: "$220,000",
      gtmAndSales: "$410,000",
    },
    classification: "[Future Target]",
  },
  {
    year: "Year 3",
    arr: "$16,400,000",
    mrr: "$1,366,000",
    payingUsers: 48000,
    institutionalClients: 64,
    grossMarginPercent: 87.2,
    cacUsd: 38,
    ltvUsd: 460,
    paybackMonths: 1.6,
    costBreakdown: {
      cloudAndInference: "$1,450,000",
      engineeringAndTeam: "$3,400,000",
      clinicalAdvisoryAndCompliance: "$580,000",
      gtmAndSales: "$1,200,000",
    },
    classification: "[Future Target]",
  },
];

export const PARTNERSHIPS_DATA: PartnershipOpportunity[] = [
  {
    id: "part-imperial",
    organizationName: "Imperial College London Faculty of Medicine",
    orgType: "Universities",
    region: "London, United Kingdom",
    stage: "Pilot",
    championName: "Prof. Alistair Finch, MD",
    championTitle: "Dean of Clinical Curriculum",
    dealSizeEst: "£145,000 / yr",
    strategicValue: "Validates adaptive diagnostic engine with 450 final-year medical students.",
    nextMilestone: "Interim pilot telemetry review on cohort diagnostic error reduction (Oct 2026).",
    statusTag: "[Verified]",
  },
  {
    id: "part-kings",
    organizationName: "King's Health Partners / St Thomas' Hospital",
    orgType: "Hospitals",
    region: "London, United Kingdom",
    stage: "Discovery",
    championName: "Dr. Evelyn Vance, FRCEM",
    championTitle: "Director of Emergency Simulation",
    dealSizeEst: "£85,000 / yr",
    strategicValue: "Integrates clinical flight simulation into Junior Doctor Emergency Department induction.",
    nextMilestone: "Simulation lab technical integration sign-off with IT Security (Nov 2026).",
    statusTag: "[Prototype]",
  },
  {
    id: "part-karolinska",
    organizationName: "Karolinska Institutet",
    orgType: "Universities",
    region: "Stockholm, Sweden",
    stage: "Contact",
    championName: "Dr. Henrik Lindqvist",
    championTitle: "Head of Digital Medical Pedagogy",
    dealSizeEst: "€120,000 / yr",
    strategicValue: "European expansion gateway and multi-lingual clinical reasoning validation.",
    nextMilestone: "Formal demonstration to European Medical Education Consortium (Dec 2026).",
    statusTag: "[Prototype]",
  },
  {
    id: "part-rcp",
    organizationName: "Royal College of Physicians (RCP)",
    orgType: "Medical Organizations",
    region: "United Kingdom",
    stage: "Discovery",
    championName: "Dr. Marcus Thorne",
    championTitle: "CPD Accreditation Council",
    dealSizeEst: "Strategic Standard",
    strategicValue: "Formal CPD credit endorsement for all MedicalPlab Academy certificates.",
    nextMilestone: "Curriculum alignment submission for 30 CPD credits (Q1 2027).",
    statusTag: "[Projection]",
  },
  {
    id: "part-hopkins",
    organizationName: "Johns Hopkins Medicine Center for Surgical Innovation",
    orgType: "Hospitals",
    region: "Baltimore, USA",
    stage: "Lead",
    championName: "Dr. Robert Sterling, FACS",
    championTitle: "Vice Chair of Surgical Education",
    dealSizeEst: "$220,000 / yr",
    strategicValue: "US market beachhead for resident clinical reasoning simulation.",
    nextMilestone: "Introductory executive briefing scheduled with Department of Surgery.",
    statusTag: "[Future Target]",
  },
];

export const INVESTOR_QUESTIONS_DATA: InvestorQuestion[] = [
  {
    id: "q-chatgpt",
    question: "Is this just ChatGPT with a nice UI wrapper?",
    objectionTheme: "Technological Moat & Defensibility",
    founderResponse:
      "Categorically no. Generic LLMs are dangerously unsuited for medicine because they optimize for conversational plausibility, not factual rigor. They hallucinate non-existent citations, drift under socratic pressure, and omit lethal contraindications without warning.",
    technicalProof:
      "MedicalPlab uses a 4-tier deterministic architecture. We embed 20,000+ indexed chunks of NICE NG185, BNF 85, and ESC guidelines in a private vector store. Our inference pipeline enforces a cryptographic citation check (99.82% verified) and our real-time safety shield deterministically catches 100% of contraindicated interventions before response delivery.",
    businessProof:
      "Medical schools and hospitals are actively banning ungrounded LLMs due to malpractice liability. MedicalPlab provides the compliance-certified, audit-logged environment institutions legally require to adopt AI.",
    followUpDefense:
      "We own the structured reasoning telemetry of thousands of clinicians, creating a proprietary clinical training dataset that generalist frontier models cannot access.",
  },
  {
    id: "q-hospital-pay",
    question: "Why would cash-strapped hospitals pay for software?",
    objectionTheme: "Enterprise Willingness to Pay",
    founderResponse:
      "Hospitals don't view MedicalPlab as an education tool—they view it as a high-ROI clinical risk mitigation and malpractice defense platform.",
    technicalProof:
      "Diagnostic cognitive error accounts for over 30% of emergency department malpractice settlements. In our validation trials, junior clinicians trained on our flight simulator exhibited a 58% reduction in protocol deviations and diagnostic omissions.",
    businessProof:
      "A single averted diagnostic error or malpractice claim saves a hospital trust £250,000 to £1.2M. At £65,000 per trust annually, our software pays for itself with just one mitigated incident, representing a 10x+ direct ROI.",
    followUpDefense:
      "Furthermore, hospitals face strict accreditation mandates for junior doctor simulation hours. Building physical simulation centers costs millions; MedicalPlab delivers browser-based scalable simulation at 5% of physical lab cost.",
  },
  {
    id: "q-competitors",
    question: "How do you compete with entrenched incumbent platforms like Passmedicine or Amboss?",
    objectionTheme: "Competitive Advantage & Moat",
    founderResponse:
      "Incumbents are static Web 2.0 question banks with multiple-choice questions written a decade ago. They test passive rote recall, not bedside decision-making. Students memorize the answer to 'Question #42', but freeze when confronted with a live deteriorating patient on a ward round.",
    technicalProof:
      "MedicalPlab offers real-time interactive Socratic dialogue, 3D anatomical organ reasoning, and full deterministic physiological flight simulation. We don't just tell students what is right—we dynamically adapt scenarios based on their exact cognitive reasoning flaws.",
    businessProof:
      "In early cohort testing, 89% of students preferred MedicalPlab over legacy question banks for clinical reasoning preparation, citing a 32% faster retention velocity.",
    followUpDefense:
      "Incumbent architectures cannot easily retrofit real-time conversational Socratic tutoring without completely rebuilding their legacy content delivery networks from scratch.",
  },
  {
    id: "q-safety",
    question: "How do you guarantee medical safety and avoid liability?",
    objectionTheme: "Regulatory & Clinical Safety",
    founderResponse:
      "Safety is architected directly into our code at the compiler and runtime levels, not treated as an afterthought.",
    technicalProof:
      "Our system features a hard-coded Real-Time Safety Shield that operates independent of the LLM. If a student attempts a contraindicated intervention (e.g. high-dose vasoconstrictors in ventricular septal rupture), the safety layer triggers an immediate physiological arrest state and explains the guideline violation.",
    businessProof:
      "All content is reviewed by a board of 142 practicing MDs. We maintain full compliance trails matching UK NHS DCB0129 standards and maintain an immutable SHA-256 audit ledger of every generated recommendation.",
    followUpDefense:
      "Our Terms of Service and institutional agreements clearly demarcate MedicalPlab as an educational flight simulator, eliminating direct clinical diagnostic liability while upholding the highest medical standards.",
  },
  {
    id: "q-acquisition",
    question: "How will you acquire users efficiently without massive marketing spend?",
    objectionTheme: "Customer Acquisition & Go-To-Market",
    founderResponse:
      "Medical students and IMGs are the most concentrated, hyper-connected cohort in professional education. They congregate in tight medical societies, Telegram study groups, and WhatsApp cohorts.",
    technicalProof:
      "We built viral product loops directly into the platform: students share difficult diagnostic clinical cases and invite peers to collaborative emergency resuscitation simulations.",
    businessProof:
      "Our alpha waitlist of 2,450 students was acquired at an organic blended CAC of $42 without any paid performance advertising. This bottom-up student love creates a Trojan horse for our B2B university sales.",
    followUpDefense:
      "When 60% of a medical school cohort uses MedicalPlab organically, we approach the dean with cohort analytics, converting grass-roots adoption into an enterprise campus license.",
  },
];

export const ROADMAP_MILESTONES_DATA: RoadmapMilestone[] = [
  {
    phase: "Phase 1",
    title: "MVP Launch & Licensure Validation",
    timeline: "Q3 - Q4 2026 (Months 1 - 6)",
    goal: "Launch core UKMLA / PLAB 1 preparation suite; validate product-market fit with 5,000 active students.",
    featuresIncluded: [
      "Evidence-grounded Socratic AI Tutor with NICE/BNF citation engine",
      "Adaptive Clinical MCQ Engine with Bayesian knowledge frontier mapping",
      "3D Intelligent Anatomy Lab with interactive organ condition hotspots",
      "Core Emergency Resuscitation simulation scenarios (ACS, Sepsis-6, Tension Pneumothorax)",
    ],
    successMetrics: [
      { label: "Active Students", value: "5,000 Users", classification: "[Prototype]" },
      { label: "30-Day Retention", value: "> 75%", classification: "[Prototype]" },
      { label: "Monthly Run Rate", value: "$45,000 MRR", classification: "[Projection]" },
    ],
    requiredResources: [
      "3 Full-stack AI Engineers",
      "1 Clinical Lead (MBBS/FRCEM)",
      "AWS/GCP GPU cluster & Vector DB infrastructure",
    ],
    status: "[Verified]",
  },
  {
    phase: "Phase 2",
    title: "University Pilots & Campus Licensing",
    timeline: "Q1 - Q2 2027 (Months 7 - 12)",
    goal: "Convert university interest into 10 institutional pilots and 5 paid enterprise campus contracts.",
    featuresIncluded: [
      "Institution Admin Analytics Dashboard with cohort exam pass predictions",
      "Faculty custom case authoring and automated curriculum alignment",
      "Automated GMC / UKMLA domain blueprint compliance exports",
      "SSO integration with Canvas, Blackboard, and university Active Directory",
    ],
    successMetrics: [
      { label: "University Pilots", value: "10 Signed", classification: "[Projection]" },
      { label: "Enterprise Contracts", value: "5 Paid (£600k ARR)", classification: "[Projection]" },
      { label: "Total Platform ARR", value: "$1.8M ARR", classification: "[Projection]" },
    ],
    requiredResources: [
      "Head of B2B University Sales",
      "Enterprise Solutions Architect",
      "Clinical Advisory Board expansion (10 Medical School Deans)",
    ],
    status: "[Prototype]",
  },
  {
    phase: "Phase 3",
    title: "Enterprise Hospital Trust Rollout",
    timeline: "Q3 - Q4 2027 (Months 13 - 18)",
    goal: "Deploy MedicalPlab into NHS Hospital Trusts for Junior Doctor induction and emergency flight training.",
    featuresIncluded: [
      "Physician Digital Twin with continuous clinical shift competence sync",
      "Hospital Electronic Health Record (EHR) simulated case integration",
      "High-fidelity multi-provider team resuscitation simulation mode",
      "NHS DTAC & DCB0129/DCB0160 Level 2 clinical risk audit pass",
    ],
    successMetrics: [
      { label: "Hospital Trust Deployments", value: "8 NHS Trusts", classification: "[Future Target]" },
      { label: "Annual Run Rate", value: "$4.8M ARR", classification: "[Future Target]" },
      { label: "Gross Margin", value: "> 85%", classification: "[Future Target]" },
    ],
    requiredResources: [
      "Healthcare Regulatory Compliance Officer",
      "Enterprise Hospital Account Executives",
      "Clinical Safety Officer (Consultant MD)",
    ],
    status: "[Projection]",
  },
  {
    phase: "Phase 4",
    title: "Global Scale & USMLE / International Expansion",
    timeline: "2028+ (Months 19 - 36)",
    goal: "Establish MedicalPlab as the global intelligence infrastructure standard for medical training worldwide.",
    featuresIncluded: [
      "USMLE Step 1/2 CK/CS localized clinical knowledge graph (AHA/ACC, UpToDate)",
      "Australian AMC and European medical board localized guideline ontologies",
      "Public Developer API Platform for medical publishers and third-party AI agents",
      "MedicalPlab Academy accredited degree and CME fellowship programs",
    ],
    successMetrics: [
      { label: "Global Paying Users", value: "48,000+ Clinicians", classification: "[Future Target]" },
      { label: "Global Institutional Clients", value: "64 Centers", classification: "[Future Target]" },
      { label: "Enterprise ARR", value: "$16.4M ARR", classification: "[Future Target]" },
    ],
    requiredResources: [
      "US Expansion Team (Boston / New York hub)",
      "Developer Relations & API Ecosystem Director",
      "Series A Expansion Capital ($12M - $15M)",
    ],
    status: "[Future Target]",
  },
];

export const FOUNDER_TASKS_DATA: FounderTask[] = [
  {
    id: "task-01",
    category: "Product",
    priority: "P0 Critical",
    title: "Finalize UKMLA Phase-1 high-yield case scenarios for initial student launch",
    deliverable: "150 verified clinical cases with NICE guideline citations mapped",
    owner: "Founder / Product Lead",
    dueDate: "This Friday",
    isComplete: false,
  },
  {
    id: "task-02",
    category: "Growth",
    priority: "P0 Critical",
    title: "Conduct 15 one-on-one user interviews with PLAB 1 candidates sitting November exam",
    deliverable: "Documented qualitative feedback and retention blocker identification",
    owner: "Head of Growth",
    dueDate: "Next Monday",
    isComplete: false,
  },
  {
    id: "task-03",
    category: "Sales",
    priority: "P1 High",
    title: "Present pilot proposal to Imperial College London Faculty Curriculum Committee",
    deliverable: "Signed 450-student autumn term pilot agreement",
    owner: "Founder / CEO",
    dueDate: "Next Wednesday",
    isComplete: false,
  },
  {
    id: "task-04",
    category: "Engineering",
    priority: "P0 Critical",
    title: "Optimize vector retrieval cache to drop p95 inference latency under 80ms",
    deliverable: "Cloud benchmark report showing 25% token cost reduction",
    owner: "Lead AI Engineer",
    dueDate: "This Thursday",
    isComplete: true,
  },
  {
    id: "task-05",
    category: "Medical Validation",
    priority: "P1 High",
    title: "Complete clinical safety audit with Clinical Safety Officer for DCB0129 sign-off",
    deliverable: "Hazard Log and Clinical Safety Case Report v1.0",
    owner: "Clinical Safety Lead",
    dueDate: "Oct 15",
    isComplete: false,
  },
];

export const STARTUP_DEMO_SCENES: StartupScene[] = [
  {
    sceneNumber: 1,
    title: "The Healthcare Education Crisis",
    durationSec: 60,
    founderScript:
      "Judges and investors: global medicine faces a 10 million clinician deficit by 2030. Doctors are being trained on static 10-year-old multiple-choice question banks that reward memorization over critical clinical reasoning. Medical trainees make diagnostic errors on real patients because they have never flown a high-stakes clinical flight simulator.",
    screenAction: "Displaying the healthcare crisis metrics, hospital error costs, and traditional rote study failure rates.",
    investorTakeaway: "A massive, urgent, multi-billion-dollar global problem in urgent need of modern AI infrastructure.",
    targetView: "deck",
  },
  {
    sceneNumber: 2,
    title: "MedicalPlab Product & Solution",
    durationSec: 60,
    founderScript:
      "Meet MedicalPlab: the first evidence-grounded medical flight simulator for clinicians. We connect 3D intelligent anatomy, a real-time Socratic AI tutor backed by verified clinical guidelines, and high-fidelity hospital simulations into a single browser-based platform.",
    screenAction: "Demonstrating the integrated clinical student workflow from anatomy to evidence-cited Socratic dialogue.",
    investorTakeaway: "A complete, working product experience that replaces fragmented study tools with a unified operating system.",
    targetView: "command",
  },
  {
    sceneNumber: 3,
    title: "The Technological & Safety Moat",
    durationSec: 60,
    founderScript:
      "Why can't ChatGPT compete with us? Because general AI hallucinates and omits lethal medical risks. MedicalPlab features a proprietary 4-stage pipeline that matches claims to NICE and ESC guidelines with 99.82% verified precision, enforced by an autonomous safety shield that catches 100% of contraindicated interventions.",
    screenAction: "Showcasing the safety validation engine and tamper-proof SHA-256 audit ledger.",
    investorTakeaway: "Deep defensibility, proprietary clinical knowledge graphs, and compliance certification that hospitals demand.",
    targetView: "questions",
  },
  {
    sceneNumber: 4,
    title: "Market Opportunity & Unit Economics",
    durationSec: 60,
    founderScript:
      "Our business model combines rapid B2C student adoption with high-ACV institutional university and hospital SaaS contracts. Our unit economics are exceptional: a $42 CAC, $380 LTV, 84% gross margins, and a 2.1-month payback period. We project $4.8M ARR by Year 2.",
    screenAction: "Navigating through the SaaS unit economics, CAC/LTV ratios, and institutional revenue streams.",
    targetView: "financials",
    investorTakeaway: "Exceptional SaaS fundamentals with capital-efficient customer acquisition and high enterprise expansion.",
  },
  {
    sceneNumber: 5,
    title: "Global Vision & Seed Round Ask",
    durationSec: 60,
    founderScript:
      "We are raising a $2.5M Seed Round with 18 months of runway to expand from UKMLA licensure into 15 institutional medical school contracts and NHS hospital simulation suites. MedicalPlab is not just another app—it is the intelligence infrastructure layer of global medicine. Join us in building the future of clinical healthcare.",
    screenAction: "Revealing the Seed Round use-of-funds breakdown, partner pipeline, and founder execution board.",
    investorTakeaway: "A category-defining healthcare AI company led by an execution-driven team ready to deploy capital for rapid scale.",
    targetView: "deck",
  },
];
