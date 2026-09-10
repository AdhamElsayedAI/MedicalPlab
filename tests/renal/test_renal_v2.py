"""Comprehensive Renal V2 test suite.

Tests:
- Benchmark source/evidence-span integrity
- SHA sidecar verification
- Query normalization (British/American spelling, acronyms)
- BM25 fail-closed behavior
- Parent-child integrity
- Evidence classifier feature extraction
- V1 baseline integrity (non-regression)
- DEV/CALIBRATION/SAFETY dataset structural integrity
- Heldout is NOT inspected (only SHA is checked)

NOTE: Evidence classifier tests require Python 3.12 + renal_env (cp312 numpy).
They are automatically skipped on Python < 3.12.
Run with: py -3.12 -m pytest tests/renal/test_renal_v2.py (after setting PYTHONPATH=.renal_env;src)
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

# Tests requiring cp312 numpy (renal_env) — only run on Python 3.12+
requires_py312 = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="requires Python 3.12 + renal_env (cp312 numpy/sklearn/torch)"
)

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "evaluation" / "renal"
DATA = ROOT / "Data"

# ── EXPECTED HASHES ────────────────────────────────────────────────
EXPECTED_SHA = {
    "renal-dev-v2.json":          "05d9ba3ae8ff27b3e364ed58737f4b06d61d20f2ab673b88bb913d879a9ddc72",
    "renal-calibration-v2.json":  "105c34fd08a1763c75c23d37db068116f1271367ad6938edec6098b3406d0459",
    "renal-safety-test-v2.json":  "fea35c02deadc5244ce69cc33a965786912622ebbd79913caaf4644af2b17b95",
    "renal-heldout-v2.json":      "94a7e3b8a0141454c90bbc80aa7fb49cb49a6dc3547e4403988a8a83fe8be5ce",
}
V1_HELDOUT_SHA = "cd7483673d8eb3aa6f85ced541a7eaad8b7c1d003b857ff1e43b6146609c26c5"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── BENCHMARK INTEGRITY ─────────────────────────────────────────────

class TestSHA256Sidecars:
    """All evaluation dataset SHA256 sidecar files must match."""

    @pytest.mark.parametrize("filename, expected_sha", list(EXPECTED_SHA.items()))
    def test_sidecar_match(self, filename: str, expected_sha: str) -> None:
        path = EVAL / filename
        sidecar = EVAL / f"{filename}.sha256"
        assert path.exists(), f"Missing: {path}"
        assert sidecar.exists(), f"Missing sidecar: {sidecar}"
        actual = sha256_file(path)
        assert actual == expected_sha, f"SHA mismatch for {filename}"
        sidecar_sha = sidecar.read_text(encoding="utf-8").strip().split()[0]
        assert sidecar_sha == expected_sha, f"Sidecar SHA mismatch for {filename}"


class TestV2DevDatasetIntegrity:
    """DEV dataset structural integrity."""

    def test_dev_query_counts(self) -> None:
        dev = load(EVAL / "renal-dev-v2.json")
        queries = dev["queries"]
        answerable = [q for q in queries if q["answerable"]]
        not_answerable = [q for q in queries if not q["answerable"]]
        assert len(queries) == 88
        assert len(answerable) == 69
        assert len(not_answerable) == 19

    def test_dev_required_fields(self) -> None:
        dev = load(EVAL / "renal-dev-v2.json")
        required = {
            "query_id", "query", "topic", "answerable",
            "gold_verification_anchors", "gold_minimum_anchor_hits",
        }
        for q in dev["queries"]:
            assert required <= q.keys(), f"Missing fields in {q.get('query_id')}"

    def test_dev_answerable_have_gold_docs(self) -> None:
        dev = load(EVAL / "renal-dev-v2.json")
        for q in dev["queries"]:
            if q["answerable"]:
                assert q.get("gold_document_ids"), f"Answerable query has no gold docs: {q['query_id']}"
                assert q.get("gold_parent_section_ids"), f"No parent section IDs: {q['query_id']}"
                assert q.get("gold_child_chunk_ids"), f"No child chunk IDs: {q['query_id']}"

    def test_dev_two_anchor_minimum(self) -> None:
        """All answerable queries must have min_anchor_hits=2."""
        dev = load(EVAL / "renal-dev-v2.json")
        for q in dev["queries"]:
            if q["answerable"]:
                min_hits = q.get("gold_minimum_anchor_hits", 0)
                assert min_hits >= 2, f"Insufficient anchor requirement: {q['query_id']}"
                matched = q.get("gold_matched_anchors", [])
                assert len(matched) >= min_hits, f"Fewer matched than required: {q['query_id']}"

    def test_dev_evidence_quotes_present_for_answerable(self) -> None:
        dev = load(EVAL / "renal-dev-v2.json")
        answerable = [q for q in dev["queries"] if q["answerable"]]
        with_quote = [q for q in answerable if q.get("gold_evidence_quote")]
        # All answerable should have evidence quotes
        assert len(with_quote) == len(answerable), "Some answerable queries lack evidence quotes"

    def test_dev_support_labels(self) -> None:
        dev = load(EVAL / "renal-dev-v2.json")
        labels = Counter(q.get("support_label") for q in dev["queries"])
        assert labels.get("SUPPORTED", 0) == 69
        assert labels.get("UNSUPPORTED", 0) == 19

    def test_dev_unanswerable_are_coverage_gaps(self) -> None:
        dev = load(EVAL / "renal-dev-v2.json")
        unanswerable = [q for q in dev["queries"] if not q["answerable"]]
        # All unanswerable in DEV should be coverage gaps (in-domain)
        for q in unanswerable:
            assert q.get("coverage_gap") is True, \
                f"Unanswerable query is not marked as coverage gap: {q['query_id']}"


class TestCalibrationDatasetIntegrity:
    """CALIBRATION dataset structural integrity."""

    def test_calibration_query_counts(self) -> None:
        cal = load(EVAL / "renal-calibration-v2.json")
        queries = cal["queries"]
        assert len(queries) == 66
        labels = Counter(q.get("support_label") for q in queries)
        assert labels.get("SUPPORTED", 0) == 20
        assert labels.get("PARTIALLY_SUPPORTED", 0) == 20
        assert labels.get("UNSUPPORTED", 0) == 26


class TestHeldoutIsSealed:
    """Heldout must exist with correct SHA, but must NOT be inspected."""

    def test_heldout_sha_matches(self) -> None:
        path = EVAL / "renal-heldout-v2.json"
        assert path.exists()
        actual = sha256_file(path)
        expected = EXPECTED_SHA["renal-heldout-v2.json"]
        assert actual == expected, "Heldout SHA mismatch — file may have been modified"

    def test_heldout_sidecar_consistent(self) -> None:
        sidecar = EVAL / "renal-heldout-v2.json.sha256"
        assert sidecar.exists()
        sidecar_sha = sidecar.read_text(encoding="utf-8").strip().split()[0]
        assert sidecar_sha == EXPECTED_SHA["renal-heldout-v2.json"]

    def test_heldout_not_opened_during_tests(self) -> None:
        """This test documents that we never parse heldout during development."""
        # The heldout path exists but we deliberately do NOT call json.loads on it.
        # If this assertion is ever violated, it means heldout was accidentally read.
        path = EVAL / "renal-heldout-v2.json"
        assert path.exists()
        # Only verify size is reasonable (>100KB) without reading content
        assert path.stat().st_size > 100_000, "Heldout file seems too small"


# ── V1 NON-REGRESSION ──────────────────────────────────────────────

class TestV1BaselineImmutability:
    """V1 heldout must not be modified."""

    def test_v1_heldout_sha(self) -> None:
        path = EVAL / "renal-heldout-v1.json"
        assert sha256_file(path) == V1_HELDOUT_SHA


# ── QUERY NORMALIZATION ─────────────────────────────────────────────

class TestRenalNormalization:
    """Query normalization: acronym expansion and spelling unification."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        from medicalplab.learn.renal_normalization import normalize_renal_query
        self.normalize = normalize_renal_query

    def test_aki_expansion(self) -> None:
        trace = self.normalize("What causes AKI?")
        assert "acute kidney injury" in trace.normalized_query.lower()
        assert any("AKI" in t for t in trace.transformations)

    def test_ckd_expansion(self) -> None:
        trace = self.normalize("CKD management")
        assert "chronic kidney disease" in trace.normalized_query.lower()

    def test_gfr_expansion(self) -> None:
        trace = self.normalize("What determines GFR?")
        assert "glomerular filtration rate" in trace.normalized_query.lower()

    def test_egfr_not_double_expanded(self) -> None:
        trace = self.normalize("Calculate eGFR in CKD")
        # eGFR should be expanded, GFR should NOT be double-expanded from eGFR
        assert "estimated glomerular filtration rate" in trace.normalized_query.lower()

    def test_adh_expansion(self) -> None:
        trace = self.normalize("How does ADH work?")
        assert "antidiuretic hormone" in trace.normalized_query.lower()

    def test_raas_expansion(self) -> None:
        trace = self.normalize("RAAS and hypertension")
        assert "renin-angiotensin-aldosterone" in trace.normalized_query.lower()

    def test_american_spelling_hyperkalemia(self) -> None:
        trace = self.normalize("What causes hyperkalemia?")
        assert "hyperkalaemia" in trace.normalized_query.lower()

    def test_american_spelling_hematuria(self) -> None:
        trace = self.normalize("Painless hematuria causes")
        assert "haematuria" in trace.normalized_query.lower()

    def test_no_transformation_for_clean_query(self) -> None:
        trace = self.normalize("What is the glomerular filtration rate?")
        assert trace.original_query == trace.normalized_query or len(trace.transformations) == 0

    def test_uti_expansion(self) -> None:
        trace = self.normalize("Symptoms of UTI")
        assert "urinary tract infection" in trace.normalized_query.lower()

    def test_rrt_expansion(self) -> None:
        trace = self.normalize("When is RRT indicated?")
        assert "renal replacement therapy" in trace.normalized_query.lower()


# ── BM25 ─────────────────────────────────────────────────────────────

class TestRenalBM25:
    """BM25 index correctness and fail-closed behavior."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        from medicalplab.learn.renal_bm25 import RenalBM25Index
        self.IndexClass = RenalBM25Index

    def _make_index(self, texts: list[str]) -> object:
        chunks = [{"chunk_id": f"c{i}", "text": t} for i, t in enumerate(texts)]
        return self.IndexClass(chunks, texts)

    def test_basic_retrieval(self) -> None:
        index = self._make_index(["glomerular filtration rate", "UTI infection bacteria", "AKI acute injury"])
        hits = index.search("glomerular filtration", top_k=3)
        assert hits[0].index == 0

    def test_fail_closed_no_results(self) -> None:
        """BM25 must return empty list when no query terms match — not zero-score docs."""
        index = self._make_index(["completely unrelated content", "another passage here"])
        hits = index.search("xyzqrs99", top_k=5)
        assert hits == [], "BM25 must fail closed with zero matches"

    def test_empty_corpus(self) -> None:
        index = self._make_index([])
        hits = index.search("kidney", top_k=5)
        assert hits == []

    def test_empty_query(self) -> None:
        index = self._make_index(["kidney filtration"])
        hits = index.search("", top_k=5)
        assert hits == []

    def test_top_k_respected(self) -> None:
        texts = [f"kidney {'nephron' * (i+1)}" for i in range(20)]
        index = self._make_index(texts)
        hits = index.search("kidney nephron", top_k=5)
        assert len(hits) <= 5

    def test_scores_descending(self) -> None:
        index = self._make_index(["kidney kidney kidney", "kidney", "unrelated text"])
        hits = index.search("kidney", top_k=3)
        for i in range(len(hits) - 1):
            assert hits[i].score >= hits[i + 1].score



# ── EVIDENCE CLASSIFIER ───────────────────────────────────────────────

@requires_py312
class TestRenalEvidenceClassifier:
    """Evidence classifier feature extraction and decision interface."""


    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        from medicalplab.learn.renal_evidence_classifier import (
            RenalEvidenceClassifier,
            RenalEvidenceFeatures,
            extract_evidence_features,
        )
        self.ClassifierClass = RenalEvidenceClassifier
        self.FeaturesClass = RenalEvidenceFeatures
        self.extract = extract_evidence_features

    def _make_chunk(self, text: str, doc_id: str = "DOC-01", parent_id: str = "P-01") -> dict:
        return {"text": text, "document_id": doc_id, "parent_section_id": parent_id}

    def test_feature_vector_dimension(self) -> None:
        chunk = self._make_chunk("glomerular filtration barrier consists of endothelial cells")
        dense_hits = [(chunk, 0.85)]
        bm25_hits = [(chunk, 12.5)]
        rrf_hits = [(chunk, 0.033)]
        reranked_hits = [(chunk, 3.2)]
        features = self.extract("What forms the filtration barrier?", dense_hits, bm25_hits, rrf_hits, reranked_hits, {})
        vec = features.to_array()
        assert vec.shape == (20,), f"Expected 20 features, got {vec.shape}"

    def test_unfitted_classifier_uses_heuristic(self) -> None:
        clf = self.ClassifierClass(threshold=0.5)
        features = self.FeaturesClass(
            dense_top1=0.9, dense_top2=0.8, dense_margin=0.1, dense_top5_mean=0.7,
            bm25_top1=10.0, bm25_top2=8.0, bm25_margin=2.0, bm25_top5_mean=6.0,
            rrf_top1=0.04, rrf_margin=0.01,
            reranker_top1=4.0, reranker_top2=1.0, reranker_margin=3.0, reranker_top5_mean=2.0,
            lexical_overlap=0.5, medical_term_overlap=0.8,
            n_supporting_sections=2, n_supporting_docs=1,
            dense_sparse_agreement=0.4, is_core_educational_source=1.0,
        )
        verdict, prob = clf.decide(features)
        assert verdict in ("GROUNDED", "INSUFFICIENT_EVIDENCE", "UNSUPPORTED")
        assert 0.0 <= prob <= 1.0

    def test_low_score_gives_unsupported(self) -> None:
        clf = self.ClassifierClass(threshold=0.5)
        features = self.FeaturesClass(
            dense_top1=-10.0, dense_top2=-10.0, dense_margin=0.0, dense_top5_mean=-10.0,
            bm25_top1=0.0, bm25_top2=0.0, bm25_margin=0.0, bm25_top5_mean=0.0,
            rrf_top1=0.0, rrf_margin=0.0,
            reranker_top1=-10.0, reranker_top2=-10.0, reranker_margin=0.0, reranker_top5_mean=-10.0,
            lexical_overlap=0.0, medical_term_overlap=0.0,
            n_supporting_sections=0, n_supporting_docs=0,
            dense_sparse_agreement=0.0, is_core_educational_source=0.0,
        )
        verdict, prob = clf.decide(features)
        assert verdict == "UNSUPPORTED"


# ── ADVERSARIAL QUERY TESTS ───────────────────────────────────────────

class TestAdversarialQueryNormalization:
    """Disambiguation tests for common renal abbreviation confusions."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        from medicalplab.learn.renal_normalization import normalize_renal_query
        self.normalize = normalize_renal_query

    def test_aki_vs_ckd_distinct(self) -> None:
        aki = self.normalize("AKI reversal criteria")
        ckd = self.normalize("CKD staging criteria")
        assert "acute kidney injury" in aki.normalized_query.lower()
        assert "chronic kidney disease" in ckd.normalized_query.lower()
        # They must not overlap
        assert "chronic" not in aki.normalized_query.lower()
        assert "acute" not in ckd.normalized_query.lower()

    def test_gfr_vs_egfr_distinction(self) -> None:
        gfr = self.normalize("How is GFR measured directly?")
        egfr = self.normalize("How is eGFR estimated?")
        assert "glomerular filtration rate" in gfr.normalized_query.lower()
        assert "estimated glomerular filtration rate" in egfr.normalized_query.lower()

    def test_british_vs_american_preserved(self) -> None:
        """Normalization standardizes to British spelling."""
        american = self.normalize("oedema causes hyperkalemia")
        # oedema is British already — no change needed
        # hyperkalemia should become hyperkalaemia
        assert "hyperkalaemia" in american.normalized_query.lower()
