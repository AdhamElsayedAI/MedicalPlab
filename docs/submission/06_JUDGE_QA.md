# Startup & Technical Judge Q&A

> **Direct, evidence-backed answers to 31 common questions across Product, AI, Learning Science, Medical Safety, Anatomy, Governance, Engineering, and Business.**

---

## 1. Product & Vision

### Q1: Why not just use ChatGPT or Claude?
**A:** Generic LLMs give fluent answers but have no model of learning. They cannot track cumulative student mastery, they treat mistakes as binary errors without diagnosing underlying reasoning patterns, they do not verify transfer through unprompted challenges, and they lack verifiable clinical literature grounding with fail-closed safety boundaries. MedicalPlab wraps AI inside an evidence-grounded cognitive tutoring framework.

### Q2: Who is the core target user?
**A:** Our primary users are medical undergraduates studying preclinical sciences and international medical graduates preparing for standardized licensing exams (such as the UK PLAB / MLA and USMLE Step 1). Secondarily, our institutional stakeholders are medical faculties and training academies seeking cohort reasoning analytics.

### Q3: What specific problem are you solving?
**A:** Medical students spend hours passive-reading or chatting with unverified bots that foster an illusion of competence. When exam day arrives, they struggle to apply principles to novel scenarios. MedicalPlab turns passive memorization into active, verified cognitive mastery.

### Q4: What is MedicalPlab's single strongest differentiator?
**A:** **Independent Transfer Verification**. We never award mastery simply because a student read or agreed with an AI explanation. The learner must independently solve an unprompted, held-out clinical challenge (`UNI-RENAL-001-T`) to demonstrate genuine transfer of knowledge.

---

## 2. Generative AI & Architecture

### Q5: Where exactly is Generative AI used in the platform?
**A:** GenAI is used in three strictly defined areas:
1. Conducting bounded Socratic dialogue during remediation.
2. Generating conversational clinical explanations in the Grounded Tutor.
3. Translating natural language anatomical requests into structured Three.js scene actions.

### Q6: Why do you need an LLM if so much is deterministic?
**A:** LLMs excel at conversational adaptation—rephrasing clinical concepts in response to learner confusion, adjusting tone, and formulating probing Socratic questions. Deterministic software provides the guardrails (retrieval, licensing, scoring, safe fallback), while the LLM provides pedagogical flexibility.

### Q7: What happens if the generative model hallucinates?
**A:** Our Shared Evidence Engine operates on a fail-closed architecture. All explanations are retrieved from PubMed Central CC-BY open-access literature and verified via Natural Language Inference (NLI) entailment. If the retrieved context does not support the statement, the system refuses to generate speculative facts and issues a safe abstention notice (`SAFE_FALLBACK`).

### Q8: Can you swap or upgrade model providers?
**A:** Yes. The platform uses a modular provider interface. In local-first mode, it runs on deterministic stub providers requiring $0 API cost. In production, providers like Google Gemini, Anthropic Claude, or local Ollama endpoints can be configured via environment variables without altering the core safety harness.

---

## 3. Learning Science & Remediation

### Q9: How do you know a student has a misconception?
**A:** We explicitly avoid claiming a student has a "proven misconception." Selecting a distractor generates a **provisional, heuristic reasoning-pattern signal** (e.g., `RP-RENAL-RENIN-ANGIOTENSIN`). It is treated as an educational hypothesis to be tested through Socratic inquiry and independent transfer, not a diagnostic label.

### Q10: How do you measure student improvement?
**A:** Improvement is measured by the delta between initial unassisted attempts, performance in Socratic remediation, and accuracy on independent held-out transfer items. This feeds a calibrated topic mastery vector in the learner's persistent state profile.

### Q11: Why is independent transfer so critical?
**A:** In cognitive science, understanding an explanation is passive recognition; applying that principle to a novel vignette is active transfer. Without independent transfer, students experience the "fluency heuristic"—mistaking the clarity of the AI's explanation for their own understanding.

### Q12: How is Socratic remediation bounded?
**A:** Remediation dialogues are strictly capped at 3 conversational turns. The model is instructed never to leak the correct answer option. If the learner does not resolve the gap within 3 turns, the system terminates the dialogue cleanly with a structured evidence summary to prevent open-ended confusion.

---

## 4. Medical AI Safety & Governance

### Q13: Is MedicalPlab a clinical diagnostic tool?
**A:** No. MedicalPlab is strictly an educational learning platform for medical students. It does not provide clinical patient diagnoses, treatment recommendations, or real-time clinical decision support.

### Q14: How do you validate medical content accuracy?
**A:** Medical content originates from curated question fixtures and peer-reviewed PubMed Central literature. Generative responses are strictly bounded by retrieved literature chunks, and exam questions require clinician sign-off before golden release.

### Q15: How does the system handle unsupported or controversial queries?
**A:** When literature retrieval yields low semantic relevance or conflicting evidence, the system activates its safe abstention gate (`SAFE_FALLBACK`). It explicitly informs the student that verified open-access literature is unavailable for that specific inquiry.

### Q16: How do you handle medical literature copyright and licensing?
**A:** Our retrieval pipeline checks the rights and licensing status of every ingested passage, restricting automated ingestion to open-access corpora with Creative Commons Attribution (CC-BY) licenses. Every response maintains direct PMCID provenance.

---

## 5. Cognitive 3D Anatomy

### Q17: Is AI generating the 3D meshes?
**A:** No. AI never generates geometry, Three.js shaders, or mesh data. All anatomical assets are validated, pre-authored 3D models mapped to standardized biological ontologies (such as UBERON).

### Q18: How is challenge correctness scored in 3D?
**A:** Correctness is calculated deterministically. When a student clicks the 3D model, Three.js casts a ray from the camera position through the screen coordinates. If the intersected mesh ID matches the target anatomical structure (e.g. `renal_artery_left`), the attempt is scored as correct. AI plays zero role in scoring.

### Q19: Why integrate 3D anatomy into a question bank?
**A:** Anatomy and pathology are inherently spatial. A student who understands renal physiology conceptually often fails to map it to vascular structures. Connecting Socratic remediation directly to 3D anatomy anchors abstract physiological pathways to physical structures (*"Structure carries signal"*).

---

## 6. PLAB Governance

### Q20: Are the PLAB questions in this repo officially validated?
**A:** The repository includes 36 candidate preview questions used to validate the examination engine. They are explicitly designated as candidate preview items and are NOT presented as official clinician-approved exam materials.

### Q21: What does "Golden Promotion" mean?
**A:** MedicalPlab requires a formal two-key clinical sign-off before candidate items can be promoted to the "Golden" exam bank (`PLAB_GOLDEN_PROMOTION_REQUIRED = YES`). In standard production mode, the exam engine fails closed to prevent unreviewed questions from reaching students.

---

## 7. Engineering & Architecture

### Q22: Why did you prioritize a local-first architecture?
**A:** Local-first engineering guarantees reproducibility and accessibility. Any judge, student, or researcher can clone the repo and run the full stack with zero cloud secrets, zero credit cards, and zero expensive GPU dependencies.

### Q23: Does MedicalPlab require a GPU?
**A:** No. The standard local runtime is optimized for standard CPU execution. Optional heavy dependencies (such as PyTorch or local Qwen weights) are partitioned into optional extras.

### Q24: How does mobile integration work?
**A:** The backend exposes a certified OpenAPI 3.1.0 contract (43 endpoints, 44 operations). We provide pre-configured Postman collections for localhost, Android emulator (`10.0.2.2:8000`), and physical devices on local Wi-Fi (`0.0.0.0:8000`).

### Q25: Is production authentication implemented?
**A:** Not in this prototype. Currently, `X-User-Id` headers provide deterministic client partitioning across sessions. Enterprise OAuth2/OIDC authentication is documented as the immediate next step in our engineering roadmap.

### Q26: Can this architecture scale?
**A:** Yes. FastAPI handles stateless async requests, the SQLite storage can be cleanly transitioned to PostgreSQL, and the retrieval engine interfaces with modern vector databases (e.g., Qdrant, Milvus) for multi-tenant institutional loads.

---

## 8. Startup & Business Model

### Q27: Who pays for this?
**A:** In the B2C segment: medical students pay a monthly or annual subscription for personalized exam preparation. In the B2B segment: medical schools and teaching hospitals purchase department seat licenses for curriculum support and student progress tracking.

### Q28: What is the go-to-market strategy?
**A:** Our beachhead is direct-to-student adoption for high-stakes licensing exams (UK PLAB / USMLE). As student cohorts adopt the platform, we leverage student performance data to pitch university deans on institutional licenses featuring cohort reasoning analytics.

### Q29: What is your moat? What stops OpenAI from doing this?
**A:** Commodity LLMs focus on general conversation, not specialized learning loops. Our moat lies in the **system around the model**:
1. Proprietary reasoning-pattern mappings linked to clinical distractors.
2. Verified held-out transfer item pairs.
3. CC-BY medical evidence retrieval with NLI verification.
4. Integrated 3D anatomical ontology mapping.
5. Privacy-preserving educator cohort analytics ($N \ge 3$).

### Q30: What are your milestones for the next 6 months?
**A:** 
- **Month 1–2:** Native Flutter/React Native mobile client release and production OAuth2 integration.
- **Month 3–4:** Clinician review and golden promotion of 500+ PLAB/USMLE question sets.
- **Month 5–6:** University pilot deployment with educator reasoning-gap dashboard.
