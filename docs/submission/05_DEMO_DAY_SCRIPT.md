# Demo Day Pitch Scripts

> **"MedicalPlab does not only answer students. It learns how students learn."**

This document provides three spoken pitch scripts for Hackathon Demo Day and Startup Track evaluations:
- **Version A:** 60-Second Elevator Pitch *(Quick introductions, networking, lightning rounds)*
- **Version B:** 3-Minute Demo Pitch *(**PRIMARY** — Hackathon Demo Day & standard judging)*
- **Version C:** 5-Minute Full Judge Presentation *(In-depth technical review, Q&A transitions)*

---

## Version A: 60-Second Elevator Pitch

> *"Every medical student today uses ChatGPT to study. The problem? Generic AI gives fluent answers, but it doesn't teach.*
>
> *It treats every question in isolation, conflates wrong answers with permanent failure, and hallucinates without accountability.*
>
> *We built **MedicalPlab**—an adaptive, evidence-grounded medical learning platform.*
>
> *Instead of spitting out answers, MedicalPlab monitors student attempts, detects underlying reasoning patterns, and initiates bounded Socratic remediation to guide the student toward discovery.*
>
> *Crucially, we don't award mastery just because a student read an explanation. We test them with an independent, held-out transfer scenario, connect their learning to 3D Cognitive Anatomy, and ground every clinical explanation in peer-reviewed literature.*
>
> *MedicalPlab doesn't replace the medical curriculum—it provides the cognitive scaffolding that turns AI into safe, verifiable medical learning."*

---

## Version B: 3-Minute Demo Pitch (PRIMARY)

*(Recommended setup: Browser open to `http://localhost:3000` with local backend running)*

### 0:00 – 0:25 | The Problem
> *"Good afternoon, judges. Today, medical students across the globe are using AI chatbots to prepare for clinical exams. But generic AI has a fundamental flaw: it gives answers, but it doesn't understand learning.*
>
> *When a student picks a wrong answer, a generic chatbot simply tells them what was right. It doesn't track their cognitive trajectory, it doesn't diagnose why they were misled, and it cannot prove whether the student actually learned."*

### 0:25 – 0:50 | What MedicalPlab Is
> *"That’s why we built **MedicalPlab**. MedicalPlab does not only answer students. It learns how students learn.*
>
> *It’s an adaptive, evidence-grounded learning engine where AI is wrapped inside strict educational and medical safety boundaries. Let’s see it in action."*

### 0:50 – 1:20 | Step 1: Question Attempt & Reasoning Signal
> *(Click into **University Mode** $\rightarrow$ Question `UNI-RENAL-001`)*
>
> *"Here’s a renal physiology question on renin-angiotensin hemodynamics. Notice what happens when our learner selects distractor **B — Angiotensin I**.*
>
> *A standard quiz app just marks this red. But MedicalPlab analyzes the cognitive distractor. Selecting Angiotensin I reveals a specific heuristic signal: `RP-RENAL-RENIN-ANGIOTENSIN`—the student is confusing the precursor cleavage step with active downstream vasoconstriction.*
>
> *Notice our core safety principle: a wrong answer is NOT a proven misconception. It is a provisional hypothesis to explore."*

### 1:20 – 1:45 | Step 2: Bounded Socratic Remediation
> *(Transition to **Socratic Remediation**)*
>
> *"Instead of immediately giving away the answer, MedicalPlab launches bounded Socratic remediation.*
>
> *The AI acts as an attending tutor. In a strictly bounded 3-turn dialogue, it asks: 'What is the direct enzymatic substrate of renin produced by the liver?'*
>
> *The student interacts, exploring their own logic without the AI leaking the correct answer. The guardrails ensure that if the student gets stuck, the system safely resolves with verified clinical facts."*

### 1:45 – 2:05 | Step 3: Independent Held-Out Transfer
> *(Navigate to **Transfer Challenge**)*
>
> *"Here is our biggest differentiator: **Independent Transfer**.*
>
> *Generic AI assumes you learned because you read the explanation. MedicalPlab refuses to award mastery until the student passes an unprompted, held-out clinical transfer item: `UNI-RENAL-001-T`.*
>
> *(Select option **A — Angiotensinogen**)*
>
> *The student correctly identifies Angiotensinogen in a fresh clinical vignette. Only now is cognitive transfer certified and recorded in their learner state."*

### 2:05 – 2:30 | Step 4: Grounded Tutor & Evidence Engine
> *(Click into **Grounded Tutor**)*
>
> *"When students need deep clinical explanations, they ask the Grounded Tutor. But our AI is never the source of medical truth.*
>
> *Behind every response is our Shared Evidence Engine. It retrieves open-access literature from PubMed Central, enforces CC-BY licensing, and runs NLI entailment checks.*
>
> *If the evidence supports the answer, we generate the explanation with direct PMCID attribution. If evidence is lacking, the model safely abstains."*

### 2:30 – 2:45 | Step 5: Cognitive 3D Anatomy Lab
> *(Open **Cognitive Anatomy Lab**)*
>
> *"Learning doesn't stop at text. In our 3D lab, **structure carries signal**.*
>
> *During guided review, the tutor highlights `renal_vein_left`. In challenge mode, the student must interactively locate `renal_artery_left`. The AI does not generate geometry; scoring is computed deterministically via 3D raycasting against standard anatomical ontologies."*

### 2:45 – 3:00 | Conclusion & Startup Value
> *(Switch to **Progress Dashboard**)*
>
> *"All of this synchronizes into a unified progress profile. MedicalPlab turns fragmented, unmonitored AI chats into a structured, verified learning asset.*
>
> *Everything you saw today runs 100% locally with zero cloud dependencies, verified across 23 backend tests and a frozen mobile contract.*
>
> *MedicalPlab is the future of verifiable, adaptive medical education. Thank you, and we welcome your questions."*

---

## Version C: 5-Minute Full Judge Presentation

*(Use for expanded panel reviews. Follows the 3-minute flow, expanding on technical moats, business model, and safety governance)*

### Outline Additions:
1. **0:00–1:00 Problem & Regulatory Context:** Why medical schools cannot endorse commercial chatbots due to hallucination liability and zero learning analytics.
2. **1:00–3:00 Live Interactive Demo:** (University Question $\rightarrow$ Socratic Remediation $\rightarrow$ Transfer $\rightarrow$ Grounded Tutor $\rightarrow$ Cognitive Anatomy).
3. **3:00–3:45 PLAB Candidate Governance Workflow:** Explain the distinction between candidate preview questions (36 items in demo) and clinician-approved golden content (`PLAB_GOLDEN_PROMOTION_REQUIRED = YES`). Show how the platform fails closed to preserve exam integrity.
4. **3:45–4:30 Business Model & Beachhead:** Student subscription B2C + Medical School B2B institutional licenses ($N \ge 3$ cohort privacy radar).
5. **4:30–5:00 Engineering Rigor:** 43 API endpoints, 12/12 mobile contract certification, reproducible clone-and-run local deployment.
