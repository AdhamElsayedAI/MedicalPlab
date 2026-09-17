# Security Policy

MedicalPlab is an educational platform designed for medical students and clinicians in training. We take data integrity, evidence provenance, and AI safety seriously.

---

## 1. Supported Versions

| Version | Supported | Security Maintenance |
| :--- | :--- | :--- |
| `1.0.x` | ✅ Yes | Current pilot/demo baseline |
| `< 1.0.0` | ❌ No | Historical prototype phases |

---

## 2. Reporting a Vulnerability

If you identify a security issue, sensitive data leak, or safety breach:

1. **Do not create a public GitHub issue.**
2. Email the maintainers directly at `security@medicalplab.internal` (or submit a private security advisory via GitHub Security Advisories).
3. Include:
   - A detailed description of the vulnerability.
   - Steps to reproduce or proof-of-concept payload.
   - Impact assessment on learner data or evidence verification pipelines.
4. The team will acknowledge receipt within 48 hours and provide a timeline for triage and remediation.

---

## 3. Educational & AI Safety Guardrails

- **Fail-Closed Evidence Gating:** MedicalPlab treats AI hallucinations as safety-critical events. Any generated response lacking verifiable attribution to licensed literature must fail-closed to `SAFE_FALLBACK`.
- **Identity Isolation (Pilot / Demo):** The current API utilizes the `X-User-Id` header for synthetic learner partitioning. This is designed for pilot and demonstration environments and does **not** constitute production-grade cryptographic authentication (`MOBILE_PRODUCTION_AUTH_READY = NO`).
- **No Protected Health Information (PHI/PII):** MedicalPlab contains exclusively synthetic medical scenarios, curricular questions, and open-access literature. No clinical patient data is stored or processed.
- **Authoritative Anatomy Geometry:** 3D anatomy assets are licensed from the HuBMAP Human Reference Atlas (HRA) and served statically. Dynamic AI geometry deformation is explicitly blocked.
