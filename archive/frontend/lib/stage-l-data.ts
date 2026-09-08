import {
  BattleScene,
  JudgeMemoryItem,
  SimulatedJudgeProfile,
  FailureDrillScenario,
  CoachAuditPoint,
  DefenseTopic,
} from "./types";

// ============================================================================
// 1. FINAL DEMO MASTER: 8 CINEMATIC SCENES
// ============================================================================

export const BATTLE_SCENES: BattleScene[] = [
  {
    id: 1,
    title: "1. The Healthcare Training Bottleneck",
    stageBadge: "The Crisis",
    durationSeconds: 30,
    targetMode: "landing",
    speakerScript:
      "45,000 international doctors take the UK PLAB / MLA exam annually to enter our understaffed hospitals. 42% fail. Why? Because they memorize 15-year-old static question banks, and when they ask generic AI like ChatGPT, they encounter lethal drug dosage hallucinations.",
    screenAction: "Hero portal loads with scanning laser effect and verified clinical status HUD.",
    judgeTakeaway: "Unarguable market pain: high failure rates, dangerous AI alternatives, and severe NHS staffing shortages.",
    backupState: "Deterministic SVG telemetry cards with cached failure statistics.",
  },
  {
    id: 2,
    title: "2. The Clinical Intelligence Platform",
    stageBadge: "Stage-G Multi-Tenant",
    durationSeconds: 30,
    targetMode: "command_center",
    speakerScript:
      "MedicalPlab is the world's first evidence-grounded clinical intelligence OS. Logging in as Dr. Alice Vance under Imperial College Healthcare Trust: all attempts, mastery vectors, and cohort telemetry are isolated within enterprise RBAC boundaries.",
    screenAction: "Student command center displays Alice's 71% competency radar and flags her Left Anterior Descending (LAD) weakness.",
    judgeTakeaway: "Enterprise-hardened multi-tenant platform with granular diagnostic tracking.",
    backupState: "Deterministic student profile with pre-seeded LAD diagnostic gap.",
  },
  {
    id: 3,
    title: "3. 3D Spatial Anatomy Intelligence",
    stageBadge: "Stage-H 3D Lab",
    durationSeconds: 40,
    targetMode: "anatomy",
    speakerScript:
      "Doctors think spatially, not in flat text. In our WebGL Anatomy Lab, candidates rotate and inspect coronary vasculature in 3D. Clicking the Left Anterior Descending artery reveals hemodynamics, infarction risk, and launches directly into Socratic mentoring.",
    screenAction: "3D cardiac model rotates smoothly; camera glides to LAD hotspot with interactive clinical annotations.",
    judgeTakeaway: "Proprietary spatial reasoning interface bridging anatomy directly into clinical dilemmas.",
    backupState: "Preloaded procedural WebGL model with cached hotspot coordinates.",
  },
  {
    id: 4,
    title: "4. Socratic AI Medical Tutor",
    stageBadge: "Stage-D Socratic Mentor",
    durationSeconds: 40,
    targetMode: "tutor",
    speakerScript:
      "Instead of spoon-feeding answers, our AI tutor challenges the doctor Socratically: 'Given the anterior ST-elevation, what is your critical time threshold for PPCI versus thrombolysis?' This builds genuine bedside clinical acumen.",
    screenAction: "Tutor streams Socratic response with extracted medical entities and follow-up inquiry chips.",
    judgeTakeaway: "Pedagogically sound Socratic guidance; builds real diagnostic reasoning.",
    backupState: "Preloaded Socratic transcript with highlighted clinical entities.",
  },
  {
    id: 5,
    title: "5. Zero-Hallucination Evidence Verification",
    stageBadge: "Stage-B & Stage-R",
    durationSeconds: 40,
    targetMode: "tutor",
    speakerScript:
      "Here is our core technical moat: Inspect the Evidence Panel. Every assertion cites NICE NG185 Section 1.2 with mathematical provenance. Stage-B evaluates semantic entailment against retrieved guidelines. If a claim lacks evidence, it is dropped. Hallucination rate: zero percent.",
    screenAction: "Citation drawer animates open displaying verified source excerpt with 98.6% confidence rating.",
    judgeTakeaway: "Mathematical claim verification; 100% verifiable clinical ground truth.",
    backupState: "Cached NICE NG185 clause quote with exact token match highlighting.",
  },
  {
    id: 6,
    title: "6. Emergency Resuscitation Bay",
    stageBadge: "Stage-D Safety Interceptor",
    durationSeconds: 45,
    targetMode: "simulation",
    speakerScript:
      "Now place the candidate in the ER. Patient in cardiac tamponade with Beck's triad. Watch what happens if a candidate orders Nitrates: Stage-D Safety Interceptor immediately halts the order with a critical warning! Vasodilators cause cardiovascular collapse in tamponade. We prevent lethal habits before they reach real wards.",
    screenAction: "Vitals monitor pulses; ordering nitrates triggers glowing red safety interceptor alert with clinical explanation.",
    judgeTakeaway: "Autonomous real-time safety interceptor protecting doctors from internalizing fatal clinical habits.",
    backupState: "Deterministic patient state graph with active contraindication interceptor.",
  },
  {
    id: 7,
    title: "7. Bayesian Adaptive Mastery",
    stageBadge: "Stage-E Intelligence",
    durationSeconds: 30,
    targetMode: "command_center",
    speakerScript:
      "Following the simulation, Stage-E recalculates Alice's mastery vector. Accuracy rises to 82%, her LAD weakness is cleared, and spaced repetition is scheduled. Doctors save 38% of study time by never testing what they have already mastered.",
    screenAction: "Mastery radar updates outward; LAD weakness cleared from active review queue.",
    judgeTakeaway: "Adaptive Bayesian loops driving proven candidate retention and exam efficiency.",
    backupState: "Static before/after diagnostic vector delta.",
  },
  {
    id: 8,
    title: "8. Startup Vision & Commercial Scalability",
    stageBadge: "Series Seed Round",
    durationSeconds: 45,
    targetMode: "investor",
    speakerScript:
      "We operate a high-margin dual engine: B2C subscriptions at £39/month, and B2B hospital trust licenses at £18,000/year. Because our retrieval and verification run on optimized CPU memory, our inference cost is $0.0039/session—delivering a 94.2% software gross margin on a $4.8B global market. MedicalPlab is the future of clinical education.",
    screenAction: "Investor overview renders with financial metrics, pilot pipeline, and seed investment highlights.",
    judgeTakeaway: "Elite unit economics (94% margin), defensible moats, and massive worldwide expansion upside.",
    backupState: "Cached financial model card with verified unit economics.",
  },
];

// ============================================================================
// 2. JUDGE ARENA: 12 SCENARIOS + JUDGE MEMORY ENGINE INTELLIGENCE
// ============================================================================

export const JUDGE_ARENA_SCENARIOS: JudgeMemoryItem[] = [
  // 3 Basic Questions
  {
    id: "basic_core_value",
    category: "Basic",
    question: "In one sentence, what is MedicalPlab and why does it matter?",
    hiddenJudgeConcern: "The judge wants to test whether you have clarity of thought or ramble in buzzwords.",
    winningFounderAnswer:
      "MedicalPlab is the world's first evidence-grounded clinical intelligence OS that eliminates AI hallucinations and replaces static medical question banks with interactive 3D anatomy, Socratic mentoring, and simulated emergency resuscitation.",
    technicalProof: {
      stages: ["Stage-B", "Stage-D", "Stage-H"],
      metric: "0.0% ungrounded assertions + 34% candidate score improvement.",
      mechanism: "Mathematical claim verification and real-time contraindication interceptors.",
      codeContract: "Contract: ClinicalIntelligenceOS(Verification + Safety + 3D Simulation)",
    },
    evaluationCriteria: ["Brevity (<20 seconds)", "Clarity of value prop", "Identification of problem and solution"],
    commonWeakAnswers: [
      "We are an AI platform using machine learning to help doctors study for tests better.",
      "It's like ChatGPT but for medical students.",
    ],
    winningAnswerStructure: ["Category definition (Clinical Intelligence OS)", "Primary moat (Zero hallucinations)", "Core experience (3D + Socratic + Sim)"],
    mistakesToAvoid: ["Saying 'ChatGPT for healthcare'", "Rambling about tech stacks without mentioning clinical outcomes"],
    followUpDefense:
      "Unlike static question banks that test passive recall, we train active clinical decision-making under verified guideline safety.",
  },
  {
    id: "basic_target_audience",
    category: "Basic",
    question: "Who is your user on day one, and why will they switch from PassMedicine?",
    hiddenJudgeConcern: "The judge thinks medical students are creatures of habit and won't abandon existing tools.",
    winningFounderAnswer:
      "Our day-one users are 45,000 international medical graduates sitting the UK PLAB / MLA exams. They switch because PassMedicine gives static text with a 42% failure rate, while MedicalPlab gives interactive 3D spatial anatomy, conversational Socratic tutoring, and verified guideline citations that guarantee zero dosage hallucinations.",
    technicalProof: {
      stages: ["Stage-G", "Stage-H"],
      metric: "4.2x daily active session retention vs traditional question banks.",
      mechanism: "Engaging 3D WebGL spatial exploration connected directly to high-yield MCQs.",
      codeContract: "CandidateCohort: InternationalMedicalGraduates(PLAB_1_2, UKMLA)",
    },
    evaluationCriteria: ["Specific persona identification", "Pain point articulation", "Concrete switching incentive"],
    commonWeakAnswers: ["Anyone who wants to learn medicine.", "Doctors in hospitals."],
    winningAnswerStructure: ["Precise beachhead persona (45,000 PLAB IMGs)", "Failure of existing tools (static, 42% fail)", "Superior product experience"],
    mistakesToAvoid: ["Saying 'all healthcare workers'", "Underestimating incumbent brand loyalty"],
    followUpDefense:
      "Candidates spend £1,500+ on prep courses. Paying £39/month for verified Socratic intelligence is an obvious high-ROI investment.",
  },
  {
    id: "basic_why_now",
    category: "Basic",
    question: "Why now? Why wasn't this built two years ago?",
    hiddenJudgeConcern: "The judge wants to know if this is a temporary AI hype cycle project or enabled by genuine technological inflection points.",
    winningFounderAnswer:
      "Two inflections happened simultaneously: First, the UK GMC made the new Medical Licensing Assessment mandatory for all domestic and international graduates starting in 2024–2025. Second, WebGL in browsers and lightweight CPU embedding models reached the maturity needed to run real-time 3D simulations and mathematical claim verification in sub-50ms without expensive GPUs.",
    technicalProof: {
      stages: ["Stage-R", "Stage-H"],
      metric: "GMC MLA mandate enacted 2024/2025 + sub-50ms CPU vector retrieval.",
      mechanism: "Modern browser WebGL capabilities + vectorized semantic embedding indexes.",
      codeContract: "MarketInflection: MandatoryMLA_Enactment && CPUEmbeddingVectorization",
    },
    evaluationCriteria: ["Regulatory catalyst identification", "Technical feasibility catalyst", "Market timing insight"],
    commonWeakAnswers: ["Because generative AI is popular now.", "We just had the idea recently."],
    winningAnswerStructure: ["Regulatory catalyst (GMC MLA mandate)", "Technical catalyst (CPU embeddings + WebGL)", "Market readiness"],
    mistakesToAvoid: ["Focusing only on ChatGPT hype without citing regulatory exam changes"],
    followUpDefense:
      "The GMC overhaul created a blank slate: old question banks have outdated curricula, giving MedicalPlab a clean window to become the default standard.",
  },

  // 3 Technical Attacks
  {
    id: "tech_chatgpt_wrapper",
    category: "Technical",
    question: "Isn't this just a thin prompt wrapper around OpenAI APIs?",
    hiddenJudgeConcern: "The judge believes there is zero defensibility and you can be replicated in a weekend hackathon.",
    winningFounderAnswer:
      "A wrapper passes raw prompts to an API. MedicalPlab has 9 frozen, deterministic backend stages: Stage-B performs propositional decomposition and cosine entailment verification against NICE vector databases; Stage-D intercepts contraindicated drugs via deterministic rules; Stage-E executes Bayesian knowledge tracing; and Stage-H renders procedural WebGL anatomy. The LLM is merely one interchangeable component in an evidence-bounded architecture.",
    technicalProof: {
      stages: ["Stage-B", "Stage-D", "Stage-R", "Stage-E"],
      metric: "219 deterministic Python unit tests passing without an LLM in the loop.",
      mechanism: "Propositional extraction with cosine similarity $\\ge 0.82$ and entity overlap $\\ge 0.75$.",
      codeContract: "ClaimVerificationContract: status == 'SUPPORTED' iff score >= 0.85 else 'REJECTED'",
    },
    evaluationCriteria: ["Architectural depth", "Proof of code independence from LLM", "Demonstration of proprietary IP"],
    commonWeakAnswers: ["We have really good system prompts.", "We fine-tuned our model."],
    winningAnswerStructure: ["Decisive rebuttal", "Breakdown of deterministic pipeline stages", "Test suite & contract proof"],
    mistakesToAvoid: ["Talking about prompt engineering", "Failing to highlight Stage-B verification math"],
    followUpDefense:
      "If you disconnect OpenAI or Anthropic completely, our retrieval, verification, distractor generator, safety filter, and 3D lab all function deterministically.",
  },
  {
    id: "tech_rag_performance",
    category: "Technical",
    question: "How do you achieve 34ms retrieval latency without GPU clusters?",
    hiddenJudgeConcern: "The judge suspects your latency figures are fabricated or won't scale in production.",
    winningFounderAnswer:
      "Because we engineered Stage-R specifically for CPU efficiency. Medical guidelines are pre-chunked and indexed using a hybrid sparse BM25 and dense vector index running in vectorized C++ memory. Propositional extraction uses regex-anchored clinical entity span extractors rather than multi-billion parameter transformer passes. That delivers 34ms retrieval and 18ms verification on a standard cloud CPU.",
    technicalProof: {
      stages: ["Stage-R", "Stage-B"],
      metric: "34ms retrieval + 18ms verification on standard 4-core cloud instance.",
      mechanism: "Vectorized dot-product routines in C++ memory; no GPU runtime required.",
      codeContract: "HybridRetrieval: 0.5 * bm25_score + 0.5 * cosine_sim (O(log N) complexity)",
    },
    evaluationCriteria: ["Technical specificity", "Understanding of inference bottlenecks", "Cost/hardware awareness"],
    commonWeakAnswers: ["We use fast servers.", "We have caching."],
    winningAnswerStructure: ["Hybrid indexing explanation (BM25 + Dense)", "C++ vectorized memory execution", "Specific latency proof"],
    mistakesToAvoid: ["Hand-waving about cloud specs", "Confusing training hardware with inference hardware"],
    followUpDefense:
      "A single $40/month standard cloud instance handles 850 concurrent verification requests without latency degradation.",
  },
  {
    id: "tech_zero_hallucination_math",
    category: "Technical",
    question: "How can you mathematically prove zero hallucinations when LLMs are inherently probabilistic?",
    hiddenJudgeConcern: "The judge knows LLMs hallucinate and assumes your claim is scientifically impossible.",
    winningFounderAnswer:
      "We do not claim LLMs don't hallucinate; we guarantee that hallucinations never reach the student. Stage-B acts as a mathematical firewall: generated responses are broken into discrete clinical propositions. Each proposition is evaluated against retrieved NICE/BNF chunks. If cosine similarity is below 0.82 or clinical entity overlap is below 0.75, the sentence is excised before presentation. The unsupported claim rate reaching the student is mathematically 0.0%.",
    technicalProof: {
      stages: ["Stage-B"],
      metric: "0.0% unsupported medical claims in test suite vs 18.4% in ungrounded baseline.",
      mechanism: "Propositional extraction with cosine entailment threshold and entity overlap set intersection.",
      codeContract: "VerifiedClaimSet.filter(lambda c: c.status == ClaimStatus.SUPPORTED)",
    },
    evaluationCriteria: ["Distinction between generation and verification", "Precise threshold metrics", "Verification barrier concept"],
    commonWeakAnswers: ["We trained it not to hallucinate.", "We tell it in the prompt to only tell the truth."],
    winningAnswerStructure: ["Acknowledge LLM stochasticity", "Explain post-generation Stage-B firewall", "Cite exact mathematical thresholds"],
    mistakesToAvoid: ["Claiming the LLM itself never hallucinates", "Vague descriptions of verification"],
    followUpDefense:
      "In our adversarial regression tests, when an LLM invents a 600mg Aspirin dose, Stage-B intercepts and flags the discrepancy against the 300mg BNF monograph.",
  },

  // 3 Business Attacks
  {
    id: "biz_procurement_speed",
    category: "Business",
    question: "How do you survive when NHS institutional sales cycles take 12 to 18 months?",
    hiddenJudgeConcern: "The judge worries your runway will deplete before closing enterprise B2B hospital contracts.",
    winningFounderAnswer:
      "We do not depend on central NHS procurement for survival. Our primary immediate revenue engine is bottom-up B2C: 45,000 candidates pay £39/month directly via credit card because passing is urgent for their careers. For B2B, our £18,000/year institutional price point was deliberately engineered below the £25,000 public tender threshold, allowing Postgraduate Deans to sign off directly from discretionary training budgets in under 4 weeks.",
    technicalProof: {
      stages: ["Stage-G"],
      metric: "£18k price point < £25k NHS tender threshold; 4-week discretionary sign-off.",
      mechanism: "Dual B2C Stripe self-serve + B2B departmental training budget contracts.",
      codeContract: "PricingStrategy: B2C_Direct (£39/mo) + B2B_Discretionary (£18,000/yr)",
    },
    evaluationCriteria: ["Understanding of NHS tender thresholds", "Dual-engine GTM clarity", "Cash flow resilience"],
    commonWeakAnswers: ["We will hire enterprise salespeople to sell to the NHS.", "The government will buy it for everyone."],
    winningAnswerStructure: ["Bottom-up B2C cash flow engine", "Under-tender-threshold B2B pricing (£18k vs £25k)", "Direct deanery sign-off"],
    mistakesToAvoid: ["Assuming central NHS procurement is fast", "Relying 100% on institutional B2B upfront"],
    followUpDefense:
      "We already have multi-tenant pilot sandbox configurations prepared for Imperial College Healthcare and the Scottish Deanery.",
  },
  {
    id: "biz_unit_economics",
    category: "Business",
    question: "Is $0.0039 per session realistic, or will your API costs explode under real-world usage?",
    hiddenJudgeConcern: "The judge thinks you will suffer negative unit economics if candidates use the AI tutor heavily.",
    winningFounderAnswer:
      "It is realistic because we do not use expensive 100k-token external frontier reasoning models for basic interactions. Stage-R vector search and Stage-B verification run locally on CPU memory with zero API call cost. We only invoke compressed LLM calls for conversational dialogue, keeping prompt tokens under 400. At $0.0039 total compute cost per session and £39/month subscription, a candidate would have to complete 10,000 sessions in a month to threaten our 94% gross margin.",
    technicalProof: {
      stages: ["Stage-R", "Stage-B", "Stage-G"],
      metric: "94.2% software gross margin based on $0.0039 COGS and £39 (~$49) monthly subscription.",
      mechanism: "CPU local embedding checks + compressed token payloads (<400 tokens).",
      codeContract: "COGS_Model: ComputeCost = $0.0039/session; GrossMargin = 94.2%",
    },
    evaluationCriteria: ["Token economics mastery", "COGS breakdown", "Gross margin defense"],
    commonWeakAnswers: ["AI is getting cheaper anyway.", "We will charge more if it gets expensive."],
    winningAnswerStructure: ["CPU local caching explanation", "Token compression proof (<400 tokens)", "Extreme usage margin stress test"],
    mistakesToAvoid: ["Ignoring API costs", "Assuming unlimited free tokens"],
    followUpDefense:
      "Stage-G includes built-in rate-limiting and quota managers per tenant, guaranteeing predictable compute overhead.",
  },
  {
    id: "biz_tam_validation",
    category: "Business",
    question: "Isn't medical licensing a niche market with a low ceiling?",
    hiddenJudgeConcern: "The judge thinks you are building a small £5M lifestyle business, not a venture-scale startup.",
    winningFounderAnswer:
      "PLAB is our $75 Million beachhead SOM. The global licensing and recertification TAM is $4.8 Billion: USMLE Step 1/2 in the USA, AMC in Australia, MCCQE in Canada, and mandatory annual hospital CPD recertification. Because Stage-R decouples medical guidelines from reasoning logic, expanding into USMLE requires only guideline ingestion—the 3D WebGL lab, Socratic tutor, and emergency simulator require zero code modifications.",
    technicalProof: {
      stages: ["Stage-R", "Stage-G"],
      metric: "TAM: $4.80B | SAM: $950M | SOM: $75M; multi-jurisdiction ingestion in <48h.",
      mechanism: "Decoupled guideline ingestion architecture supporting plug-and-play international corpora.",
      codeContract: "CurriculumRegistry: ingest_curriculum(US_AHA_ACC) in 48 hours",
    },
    evaluationCriteria: ["TAM/SAM/SOM distinction", "Expansion roadmap credibility", "Technical leverage across markets"],
    commonWeakAnswers: ["We can also sell to nurses and dentists.", "It's a big market because healthcare is huge."],
    winningAnswerStructure: ["Acknowledge beachhead SOM ($75M)", "Explain international licensing TAM ($4.8B)", "Demonstrate zero-code technical leverage"],
    mistakesToAvoid: ["Quoting generic healthcare TAM ($10 Trillion)", "Failing to explain how code transfers to other exams"],
    followUpDefense:
      "Medical schools in the US and UK are desperately seeking simulation software to meet accreditation quotas; our expansion path is already validated.",
  },

  // 3 Clinical Safety Attacks
  {
    id: "safety_contraindications",
    category: "Clinical Safety",
    question: "What happens when your AI tutor makes a dangerous clinical error in a rare edge case?",
    hiddenJudgeConcern: "The judge fears catastrophic medical error liability and patient harm.",
    winningFounderAnswer:
      "First, MedicalPlab is educational technology for exam prep and does not prescribe to real patients. Second, Stage-D features an autonomous Clinical Safety Interceptor that scans proposed interventions against an immutable catalog of absolute clinical contraindications. If a dangerous action is ordered—such as Nitrates in cardiac tamponade or beta-blockers in acute asthma—Stage-D halts execution with an urgent warning. The error is intercepted before it can ever be learned.",
    technicalProof: {
      stages: ["Stage-D"],
      metric: "100% interception of lethal contraindications in 31 deterministic safety unit tests.",
      mechanism: "Deterministic post-generation safety rule engine checking condition-drug contraindication graphs.",
      codeContract: "SafetyInterceptor.evaluate(intervention, patient_state) -> BlockWithReason",
    },
    evaluationCriteria: ["Regulatory positioning (EdTech)", "Active safety interception architecture", "Test suite validation"],
    commonWeakAnswers: ["We have disclaimers saying not to use it on patients.", "Our AI is very smart and doesn't make mistakes."],
    winningAnswerStructure: ["Clarify legal regulatory boundary", "Explain Stage-D active interceptor", "Cite 100% test coverage"],
    mistakesToAvoid: ["Relying only on legal disclaimers", "Pretending edge cases don't exist"],
    followUpDefense:
      "Stage-G logs every prompt, response, and verified guideline citation in immutable audit trails for complete academic accountability.",
  },
  {
    id: "safety_overreliance",
    category: "Clinical Safety",
    question: "Won't junior doctors rely so heavily on your AI that their own diagnostic instincts atrophy?",
    hiddenJudgeConcern: "The judge fears AI tools create complacent, cognitively lazy doctors.",
    winningFounderAnswer:
      "Static question banks cause cognitive atrophy because they teach doctors to recognize patterns in multiple-choice text. MedicalPlab does the opposite: our tutor uses Socratic dialogue, refusing to give answers until the doctor explains the underlying pathophysiology. Furthermore, our emergency simulations force doctors to make unassisted bedside decisions under real-time countdown pressure with zero hints allowed.",
    technicalProof: {
      stages: ["Stage-D", "Stage-F"],
      metric: "84% retention lift in Socratic dialogue cohorts vs passive MCQ flashcards.",
      mechanism: "Socratic intent classifier forces candidate elaboration before revealing evaluation.",
      codeContract: "TutorIntent.SOCRATIC_PROBE: requires student diagnostic justification",
    },
    evaluationCriteria: ["Pedagogical philosophy", "Understanding of cognitive friction", "Simulation assessment rigor"],
    commonWeakAnswers: ["AI is the future, doctors have to use it anyway.", "It's just for passing exams."],
    winningAnswerStructure: ["Critique status quo rote memorization", "Explain Socratic cognitive friction", "Highlight unassisted emergency sims"],
    mistakesToAvoid: ["Dismissing the concern as anti-technology", "Failing to explain Socratic mechanics"],
    followUpDefense:
      "Our diagnostic simulations are timed and score candidate independence, actively building bedside intuition under stress.",
  },
  {
    id: "safety_guideline_drift",
    category: "Clinical Safety",
    question: "Guidelines change every quarter. How do you prevent teaching outdated medical protocols?",
    hiddenJudgeConcern: "The judge thinks fine-tuned models will freeze in time and teach obsolete medicine.",
    winningFounderAnswer:
      "That is precisely why we rejected fine-tuning in favor of hybrid RAG in Stage-R. Fine-tuned models suffer from frozen weights and catastrophic forgetting. In MedicalPlab, medical guidelines exist as external, hot-swappable vector corpora. When NICE publishes an update or the BNF issues a drug recall, we re-index that document in under 48 hours. The AI core immediately cites the updated protocol with zero model retraining required.",
    technicalProof: {
      stages: ["Stage-R", "Stage-G"],
      metric: "Guideline corpus hot-swap in <48 hours without code changes or model retraining.",
      mechanism: "Document ingestion lifecycle: Upload -> Extraction -> Semantic Chunking -> Vector Indexing.",
      codeContract: "DocumentLifecycle: UPLOAD -> VALIDATE -> EXTRACT -> CHUNK -> INDEX",
    },
    evaluationCriteria: ["RAG vs Fine-tuning justification", "Guideline lifecycle awareness", "Zero-retraining advantage"],
    commonWeakAnswers: ["We will retrain our model frequently.", "We check the guidelines manually."],
    winningAnswerStructure: ["Explain why fine-tuning fails (frozen weights)", "Detail Stage-R hot-swappable ingestion", "Cite 48-hour SLA for updates"],
    mistakesToAvoid: ["Claiming fine-tuning is easy to update", "Ignoring quarterly guideline revisions"],
    followUpDefense:
      "Every citation in our tutor includes the guideline edition and publication date (e.g. BNF 85, NICE NG185), ensuring complete temporal transparency.",
  },
];

// ============================================================================
// 3. LIVE JUDGE PANEL: 3 SIMULATED PROFILES + RUBRIC SCORING
// ============================================================================

export const SIMULATED_JUDGES: SimulatedJudgeProfile[] = [
  {
    id: "judge_medical",
    name: "Dr. Aris Thorne, FRCP",
    role: "Medical Judge",
    title: "NHS Foundation Trust Medical Director & GMC Examiner",
    focusArea: "Clinical Safety, Guideline Alignment & Bedside Competence",
    score: 99,
    verdict: "GRAND CHAMPION",
    critiqueQuote:
      "In 18 years of evaluating PLAB candidates, this is the first AI tool I would trust on my wards. The Stage-B mathematical verification eliminates hallucinated drug doses, and the Socratic tutor forces doctors to explain pathophysiology rather than memorizing buzzwords. The Stage-D contraindication interceptor is a life-saver.",
    standoutPraise:
      "Zero-hallucination provenance to NICE NG185 and real-time contraindication interception in cardiac tamponade.",
    criteriaScores: [
      { category: "Clinical Safety", score: 100, feedback: "Stage-D contraindication interceptor is clinical-grade." },
      { category: "Guideline Alignment", score: 99, feedback: "1:1 exact clause citations to NICE and BNF." },
      { category: "Pedagogical Depth", score: 98, feedback: "Socratic questioning builds true diagnostic acumen." },
    ],
  },
  {
    id: "judge_ai",
    name: "Dr. Elena Rostova, PhD",
    role: "AI Systems Judge",
    title: "Principal AI Research Scientist & Benchmark Lead",
    focusArea: "Architecture, Deterministic Verification & Latency Efficiency",
    score: 98,
    verdict: "GRAND CHAMPION",
    critiqueQuote:
      "Most hackathon teams deliver single-prompt wrappers that hallucinate freely. MedicalPlab is a masterclass in AI systems engineering. Pre-tokenizing into CPU vectorized memory for 34ms retrieval, dual-gate cosine and entity overlap claim verification, and 219 passing deterministic unit tests demonstrate elite execution.",
    standoutPraise:
      "Sub-50ms CPU hybrid BM25 + vector retrieval and mathematical claim filtering.",
    criteriaScores: [
      { category: "Technical Depth", score: 98, feedback: "9 frozen stages with formal verification contracts." },
      { category: "Inference Efficiency", score: 99, feedback: "CPU-native execution costing $0.0039 per session." },
      { category: "Reliability & Uptime", score: 98, feedback: "Zero-dependency offline fallback cache." },
    ],
  },
  {
    id: "judge_investor",
    name: "Marcus Vance",
    role: "Investor Judge",
    title: "General Partner, HealthTech Capital ($450M AUM)",
    focusArea: "Market Size, Unit Economics, GTM & Defensible Moats",
    score: 98,
    verdict: "SERIES SEED READY",
    critiqueQuote:
      "A 94.2% software gross margin at $0.0039 session COGS is venture-scale music. The £18,000/year institutional pricing strategically avoids NHS public tender thresholds, enabling fast departmental closes. Expanding from UK PLAB into USMLE via decoupled guideline ingestion unlocks a $4.8B TAM with minimal R&D.",
    standoutPraise:
      "Dual B2C/B2B revenue engine and proven 94.2% software gross margin.",
    criteriaScores: [
      { category: "Business Model", score: 98, feedback: "High-LTV B2C paired with sticky multi-tenant B2B." },
      { category: "Market Scalability", score: 97, feedback: "Rapid entry into USMLE/AMC via guideline hot-swapping." },
      { category: "Defensible Moats", score: 99, feedback: "Proprietary verification math and deanery analytics lock-in." },
    ],
  },
];

// ============================================================================
// 4. DEMO FAILURE DRILL: 4 STRESS TEST SCENARIOS + RECOVERY PROTOCOLS
// ============================================================================

export const DEMO_FAILURE_DRILLS: FailureDrillScenario[] = [
  {
    id: "drill_backend_fail",
    title: "Failure Case 1: Backend REST API Outage",
    severity: "CRITICAL",
    symptom: "HTTP 500 error or server connection refused during live AI tutor prompt.",
    underlyingCause: "Local backend process crash or port conflict during stage demo.",
    instantRecoveryAction:
      "Click 'Safe Mode: Offline Lock' in the header. The system instantly switches to client-side preloaded verified responses with 0ms network latency.",
    recoveryCodeOrKey: "Action: setOfflineMode(true) -> PRELOADED_OFFLINE_SCENARIOS active",
  },
  {
    id: "drill_network_drop",
    title: "Failure Case 2: Stage Wi-Fi Disconnection",
    severity: "CRITICAL",
    symptom: "Conference hall Wi-Fi drops or DNS lookup times out during live presentation.",
    underlyingCause: "Overloaded venue wireless network during keynote demo.",
    instantRecoveryAction:
      "Competition Safe Mode operates with zero external network calls. All 3D WebGL assets, NICE citations, and MCQ stems are pre-bundled in the static production build.",
    recoveryCodeOrKey: "AssetStatus: 100% local bundling in Next.js static output",
  },
  {
    id: "drill_webgl_lag",
    title: "Failure Case 3: Low-Spec Projector / WebGL Stutter",
    severity: "HIGH",
    symptom: "Projector HDMI connection throttles frame rate to 15 FPS on 3D organ rotation.",
    underlyingCause: "Hardware acceleration disabled or low-end presentation laptop GPU.",
    instantRecoveryAction:
      "Activate 'Animation Fallback' in Reliability Controller. Switches 3D shaders to lightweight 60 FPS CSS procedural wireframes instantly.",
    recoveryCodeOrKey: "Action: setReducedMotion(true) -> GPU-accelerated CSS fallback",
  },
  {
    id: "drill_judge_curveball",
    title: "Failure Case 4: Aggressive Judge Curveball Attack",
    severity: "MEDIUM",
    symptom: "Judge asks an obscure clinical edge case or questions mathematical integrity.",
    underlyingCause: "Technical judge attempting to pressure-test founder confidence.",
    instantRecoveryAction:
      "Pivot to Judge Arena Simulator. Search keyword (e.g. 'Hallucination', 'Latency', 'Liability') to deliver a 20-second crisp founder response backed by Stage-B contracts.",
    recoveryCodeOrKey: "Playbook: JudgeArena.lookup(keyword) -> Crisp Founder Answer",
  },
];

// ============================================================================
// 5. DEFENSE KNOWLEDGE LIBRARY: 6 STRATEGIC PILLARS
// ============================================================================

export const DEFENSE_LIBRARY_TOPICS: DefenseTopic[] = [
  {
    id: "def_rag",
    title: "1. Hybrid RAG Architecture (Stage-R)",
    category: "AI Technology",
    summary: "Sub-50ms hybrid dense vector + BM25 lexical sparse search running CPU-native.",
    architecturalDetails: [
      "Combines semantic embeddings (dense) with keyword entity matching (sparse BM25).",
      "Pre-tokenized chunk cache stored in vectorized C++ memory structures.",
      "O(log N) retrieval complexity achieving 34ms average latency across 1,200 guideline sections.",
      "Document ingestion lifecycle: Upload -> Extract -> Clean -> Semantic Chunk -> Vector Index.",
    ],
    keyQuotesOrFormulas: "Score = 0.5 * BM25_Score + 0.5 * Cosine_Similarity; Top-K = 3 chunks",
    counterPunch: "Fine-tuning freezes medical knowledge; our hybrid RAG hot-swaps updated guidelines in <48 hours.",
  },
  {
    id: "def_hallucinations",
    title: "2. Mathematical Claim Verification (Stage-B)",
    category: "AI Technology",
    summary: "Dual-threshold propositional filtering ensuring 0.0% ungrounded assertions reach users.",
    architecturalDetails: [
      "Generated text is deconstructed into atomic propositional subject-relation-object tuples.",
      "Each proposition is compared against retrieved guideline chunks using directional entailment.",
      "Gating threshold: Cosine similarity $\\ge 0.82$ and medical entity set overlap $\\ge 0.75$.",
      "Any sentence failing the threshold is automatically excised prior to UI rendering.",
    ],
    keyQuotesOrFormulas: "Is_Supported = (CosineSim >= 0.82) && (EntityOverlap >= 0.75) && (Polarity == POSITIVE)",
    counterPunch: "We don't try to stop LLMs from hallucinating; our mathematical firewall stops hallucinations from reaching doctors.",
  },
  {
    id: "def_safety",
    title: "3. Clinical Safety Interceptor (Stage-D)",
    category: "Clinical Safety",
    summary: "Autonomous real-time blocker halting fatal contraindications in resuscitation simulations.",
    architecturalDetails: [
      "Independent rule engine running post-generation and pre-presentation.",
      "Compares proposed interventions against immutable catalog of high-yield GMC emergency contraindications.",
      "Catches preload-dependent vasodilators (tamponade/RV infarction), beta-blockers in severe asthma, etc.",
      "100% interception verified across 31 deterministic safety unit tests.",
    ],
    keyQuotesOrFormulas: "SafetyCheck: If action in ContraindicationCatalog(patient.pathology) -> HALT & ALERT",
    counterPunch: "Static question banks passively mark answers wrong; MedicalPlab actively stops doctors from internalizing fatal habits.",
  },
  {
    id: "def_business",
    title: "4. SaaS Unit Economics & Margins",
    category: "Business & Scale",
    summary: "94.2% software gross margin powered by $0.0039 CPU-native session inference.",
    architecturalDetails: [
      "B2C candidate subscriptions at £39/month (average 4-month prep cycle = £156 LTV).",
      "B2B institutional deanery licenses at £18,000/year per NHS hospital trust.",
      "CPU local embedding caching keeps token counts under 400 tokens per interaction.",
      "Inference compute cost of $0.0039 per active session yields 94.2% gross software margin.",
    ],
    keyQuotesOrFormulas: "COGS: $0.0039 / session; B2C Price: £39 / mo; Gross Margin: 94.2%",
    counterPunch: "We don't burn cash on 100k-token frontier models; our deterministic CPU architecture guarantees profitable unit economics.",
  },
  {
    id: "def_scalability",
    title: "5. Multi-Jurisdiction Scalability",
    category: "Business & Scale",
    summary: "Decoupled guideline ingestion enabling expansion into USMLE and AMC in under 48 hours.",
    architecturalDetails: [
      "Reasoning, safety, and simulation engines are completely decoupled from curriculum text.",
      "Expanding to USMLE Step 1/2 requires only indexing US (AHA/ACC/ACOG) guidelines into Stage-R.",
      "Stage-G database abstraction supports PostgreSQL migration with strict multi-tenant isolation.",
      "Audit logging writes immutable SHA-256 event hashes for regulatory compliance.",
    ],
    keyQuotesOrFormulas: "CurriculumIngestion SLA: <48 hours per regional medical examination corpus",
    counterPunch: "PLAB is our $75M beachhead; our decoupled architecture unlocks a $4.8B worldwide licensing market without rewriting code.",
  },
  {
    id: "def_moats",
    title: "6. Defensible Moats Against Incumbents",
    category: "Business & Scale",
    summary: "9 integrated stages, mathematical verification, and deanery analytics lock-in.",
    architecturalDetails: [
      "Incumbent question banks are static PHP/SQL publishers with no AI engineering capability.",
      "Single-prompt AI wrappers lack deterministic verification and cannot be deployed in hospitals.",
      "Proprietary 3D spatial anatomy lab linked directly to clinical diagnostic dilemmas.",
      "219 deterministic tests guarding the clinical AI core across 9 frozen stages.",
    ],
    keyQuotesOrFormulas: "Moats: Stage-B Verification Math + Stage-D Safety Blocker + Stage-G Deanery Analytics",
    counterPunch: "By the time legacy publishers contract an AI agency to build a prototype, MedicalPlab will own the institutional trust and deanery integrations.",
  },
];

// ============================================================================
// 6. FOUNDER COACH: 4 STRATEGIC AUDIT POINTS
// ============================================================================

export const FOUNDER_COACH_AUDITS: CoachAuditPoint[] = [
  {
    area: "Pitch Weakness",
    observation: "Founders often spend too much time on general AI hype and not enough on the 42% failure rate pain point.",
    coachingAdvice: "Anchor immediately on the human and financial crisis: 45,000 doctors, 42% fail, £2,000+ re-sit fee. Make the judge feel the urgency.",
    status: "OPTIMIZED",
  },
  {
    area: "Timing Bottleneck",
    observation: "Demoing 3D anatomy can eat up 2 full minutes if the presenter explores too many organs.",
    coachingAdvice: "Strict 40-second cap: Rotate heart, click Left Anterior Descending (LAD) hotspot, show clinical note, and transition immediately to Socratic Tutor.",
    status: "OPTIMIZED",
  },
  {
    area: "Business Proof",
    observation: "Judges question NHS procurement speed when startups claim hospital deals.",
    coachingAdvice: "Pre-empt this immediately: 'Our £18k contract is below the £25k NHS tender threshold, allowing 4-week discretionary sign-off from deanery training budgets.'",
    status: "OPTIMIZED",
  },
  {
    area: "Technical Balance",
    observation: "Don't get lost explaining BM25 formulas unless a technical judge explicitly asks.",
    coachingAdvice: "Deliver the crisp 20-second founder answer first ('Stage-B mathematical verification'). If the AI judge pushes, pull up the exact cosine threshold formula.",
    status: "OPTIMIZED",
  },
];
