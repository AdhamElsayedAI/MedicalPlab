# Product & Engineering Roadmap

> **Pragmatic execution horizons taking MedicalPlab from a verified local prototype to an enterprise medical learning platform.**

---

## 1. Execution Horizons

```
[ HORIZON 1: NOW ]  -->  [ HORIZON 2: NEXT ]  -->  [ HORIZON 3: THEN ]  -->  [ HORIZON 4: LATER ]
Verified Prototype         Production Core           Curriculum Expansion      Ecosystem Platform
```

### Horizon 1: NOW (Current Verified Milestone)
- **Status:** **Completed & Certified**
- **Core Deliverables:**
  - Local-first reproducible runtime ($0 cloud, 0 GPU, 0 API keys required).
  - Canonical Adaptive Learning loop with heuristic reasoning-pattern signals.
  - Bounded 3-turn Socratic remediation with strict answer concealment.
  - Independent held-out transfer testing (`UNI-RENAL-001-T`).
  - Evidence-grounded TutorService with PubMed Central CC-BY open-access retrieval and NLI entailment verification.
  - Cognitive 3D Anatomy Lab with deterministic raycast challenge scoring.
  - Unified learner progress synchronization across all modules.
  - Frozen OpenAPI 3.1.0 contract (43 paths, 44 operations, 12/12 mobile tests passing).
  - Clean checkout release gate certified via 8/8 passing GitHub Actions CI jobs.

---

### Horizon 2: NEXT (Production Hardening & Mobile Release)
- **Target Focus:** Transition from verified prototype to user-facing beta.
- **Key Deliverables:**
  - **Native Mobile Client:** Develop and release cross-platform mobile client (Flutter / React Native) consuming the certified OpenAPI contract.
  - **Cryptographic Authentication:** Implement production OAuth2 / OIDC authentication (e.g. Auth0 / Supabase) replacing demo `X-User-Id` headers.
  - **Durable Database Persistence:** Transition from local SQLite storage to managed PostgreSQL with connection pooling.
  - **Golden PLAB Content Promotion:** Conduct formal multi-clinician review to promote candidate question items to verified golden status.
  - **Containerized Cloud Deployment:** Release audited Docker images and infrastructure-as-code scripts for one-click deployment on Google Cloud Run or AWS ECS.

---

### Horizon 3: THEN (Curriculum Breadth & Educator Analytics)
- **Target Focus:** Broaden educational scope and pilot with academic faculty.
- **Key Deliverables:**
  - **Expanded Medical Disciplines:** Ingest vetted curricula for Cardiology, Neurology, Gastroenterology, Endocrine, and Musculoskeletal medicine.
  - **Educator Dashboard:** Launch the dedicated faculty portal for the **Reasoning-Gap Radar**, providing aggregate cohort analytics ($N \ge 3$).
  - **LMS Integration:** Implement LTI 1.3 / SCORM standards for turnkey integration with university learning management systems (Canvas, Blackboard).
  - **Longitudinal Cognitive Mastery:** Introduce spaced repetition scheduling driven by individual forgetting curves and historical transfer failure rates.

---

### Horizon 4: LATER (Enterprise Platform & Multi-Institution Scale)
- **Target Focus:** Institutional scale, intelligent routing, and advanced spatial interaction.
- **Key Deliverables:**
  - **Intelligent Model Routing:** Deploy a multi-model router dynamically assigning prompts to cost-effective small models (for structured parsing) or frontier models (for complex Socratic dialogues).
  - **Multi-Institution Deployments:** Multi-tenant enterprise architecture with role-based access control (RBAC), tenant data isolation, and GDPR/FERPA compliance.
  - **Full-Body Spatial Anatomy:** Expand from regional organ models to multi-system anatomical atlases mapped to complete ontological hierarchies.
  - **Custom Question Authoring Suite:** Provide medical faculty with an interactive workbench to author questions, annotate distractor reasoning patterns, and create paired transfer items.

---

## 2. Technical Scaling Architecture

```
[ Mobile / Web Clients ]
           │
           ▼
[ API Gateway / Cloudflare ]  --> DDoS protection & static asset caching
           │
           ▼
[ FastAPI Application Pods ]  --> Stateless, horizontally autoscaling
      ├── Learner State Engine
      ├── Socratic Orchestrator
      └── Anatomy Scene Coordinator
           │
     ┌─────┴────────────────────────┐
     ▼                              ▼
[ PostgreSQL / Redis ]       [ Vector Search / PMC Index ]
Session & Mastery State      Qdrant / Milvus Semantic Store
```

### Cost & Resource Profile:
1. **Compute:** Asynchronous FastAPI endpoints are lightweight. Standard workloads run comfortably on shared micro-instances (under 512 MB RAM per instance).
2. **Retrieval:** Pre-indexed PubMed Central embeddings provide rapid semantic search without needing continuous runtime fine-tuning.
3. **Inference:** Bounding Socratic dialogues to 3 turns caps inference token costs per remediation session.
