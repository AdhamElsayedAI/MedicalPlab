## Description

Provide a concise overview of the changes in this pull request and the rationale behind them.

---

## Type of Change

- [ ] Documentation update
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] Performance or test improvement
- [ ] Refactoring (no functional/contract changes)
- [ ] New feature (aligned with frozen architecture)

---

## Architectural & Clinical Safety Checklist

Please confirm that this pull request complies with all core MedicalPlab invariants:

- [ ] **Evidence Bounding:** Generative AI responses remain strictly bounded by retrieved evidence; no unconstrained LLM generation has been introduced.
- [ ] **Verification Integrity:** Claim verification and `SAFE_FALLBACK` paths remain intact and fail-closed.
- [ ] **Heuristic Reasoning Signals:** Distractor feedback represents heuristic educational hypotheses, not confirmed learner deficiencies.
- [ ] **Anatomy Separation:** AI generates only structured scene actions; scientific HuBMAP HRA geometry is unchanged.
- [ ] **PLAB Governance:** Candidate questions remain isolated under Preview QA and do not self-promote to released status.
- [ ] **Zero Contract Drift:** If API endpoints or schemas were touched, `Scripts/verify_mobile_contract_drift.py` passes with zero drift.
- [ ] **No Secret Exposure:** No API keys, credentials, or private patient data are committed.

---

## Verification & Test Results

- [ ] Integration tests pass: `pytest tests/integration/ -q -p no:cacheprovider`
- [ ] Mobile contract tests pass: `pytest tests/integration/test_mobile_api_contract.py -q`
- [ ] Frontend build succeeds: `npm run build`
- [ ] Link verification passes: `python Scripts/verify_repository_handoff.py`
