"""Read-only persistence repository for Phase 3 Learning Intelligence.

CRITICAL INVARIANTS:
1. Zero mutation of Phase 2B persistence tables (remediation_sessions, remediation_learning_evidence).
2. Reads existing SQLite records safely; skips corrupted rows without crashing.
3. Serves deterministic, clearly labeled demo data for demo cohorts.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Dict, List, Optional, Set

from medicalplab.learning_intelligence.demo_data import (
    DEMO_COHORT_ID,
    DEMO_COHORT_NAME,
    get_demo_sessions,
)
from medicalplab.learning_intelligence.models import EvidenceSummaryItem
from medicalplab.remediation.models import RemediationSessionState

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = ROOT_DIR / "Data" / "persistence" / "remediation.sqlite3"
QUESTIONS_BANK_PATH = ROOT_DIR / "Data" / "university" / "questions.json"
MANIFEST_PATH = ROOT_DIR / "Data" / "metadata" / "tutor_source_rights_manifest_v1.json"

DEMO_ENABLED_ENV_VAR = "MEDICALPLAB_PHASE_3_DEMO_ENABLED"
ALLOWED_COHORTS: Set[str] = {
    DEMO_COHORT_ID,
}


class UnknownCohortError(Exception):
    """Raised when an unknown or unregistered cohort ID is requested."""
    pass


class DemoCohortDisabledError(Exception):
    """Raised when a demo cohort is accessed in a runtime where demo data is disabled."""
    pass


def is_demo_enabled() -> bool:
    """Determine whether Phase 3 synthetic demo cohorts are accessible.

    1. Explicit MEDICALPLAB_PHASE_3_DEMO_ENABLED env var takes absolute precedence.
    2. Strict runtime modes (production, pilot) disable demo cohorts by default.
    3. Development, demo, and test modes permit demo cohorts.
    """
    flag = os.getenv(DEMO_ENABLED_ENV_VAR)
    if flag is not None:
        return flag.strip().lower() in ("true", "1", "yes")

    runtime_mode = os.getenv("MEDICALPLAB_RUNTIME_MODE", "demo").strip().lower()
    if runtime_mode in ("production", "pilot"):
        return False
    return True


class LearningIntelligenceRepository:
    """Read-only repository for learner remediation sessions and evidence reference resolution."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        questions_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        allowed_cohorts: Optional[Set[str]] = None,
    ) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.questions_path = questions_path or QUESTIONS_BANK_PATH
        self.manifest_path = manifest_path or MANIFEST_PATH
        self.allowed_cohorts: Set[str] = set(allowed_cohorts) if allowed_cohorts is not None else set(ALLOWED_COHORTS)
        self._evidence_cache: Dict[str, EvidenceSummaryItem] = {}
        self._load_evidence_registry()

    def _load_evidence_registry(self) -> None:
        """Load genuine evidence metadata from questions bank and manifest."""
        # 1. Load from questions bank (has full titles, URLs, and licenses)
        if self.questions_path.exists():
            try:
                rows = json.loads(self.questions_path.read_text(encoding="utf-8"))
                for q in rows:
                    ev = q.get("evidence")
                    if isinstance(ev, dict) and ev.get("document_id"):
                        doc_id = ev["document_id"]
                        chunk_id = ev.get("chunk_id")
                        item = EvidenceSummaryItem(
                            document_id=doc_id,
                            chunk_id=chunk_id,
                            title=ev.get("title"),
                            source_url=ev.get("url"),
                            license=ev.get("license"),
                        )
                        self._evidence_cache[doc_id] = item
                        if chunk_id:
                            self._evidence_cache[chunk_id] = item
                            # Also cache colon-formatted "doc_id:chunk_id"
                            self._evidence_cache[f"{doc_id}:{chunk_id}"] = item
            except Exception as exc:
                logger.warning("Could not read questions bank for evidence resolution: %s", exc)

        # 2. Load supplemental rights metadata
        if self.manifest_path.exists():
            try:
                manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                for doc in manifest.get("documents", []):
                    doc_id = doc.get("document_id")
                    if doc_id and doc_id not in self._evidence_cache:
                        pmcid = doc.get("pmcid", "")
                        url = f"https://europepmc.org/article/PMC/{pmcid}" if pmcid else None
                        self._evidence_cache[doc_id] = EvidenceSummaryItem(
                            document_id=doc_id,
                            title=f"Open-Access Biomedical Source ({doc_id})",
                            source_url=url,
                            license=doc.get("license", "Open-Access"),
                        )
            except Exception as exc:
                logger.warning("Could not read source rights manifest: %s", exc)

    def resolve_evidence(self, ref: str) -> Optional[EvidenceSummaryItem]:
        """Resolve a taxonomy or session evidence reference string to a verified summary item."""
        if not ref or not ref.strip():
            return None
        clean_ref = ref.strip()
        # Strictly reject safety fallback, fabricated, or unknown citation markers
        if any(marker in clean_ref.upper() for marker in ("FALLBACK", "SAFETY", "UNKNOWN")):
            return None
        if clean_ref in self._evidence_cache:
            return self._evidence_cache[clean_ref]

        # Check by splitting doc_id:chunk_id or prefix
        if ":" in clean_ref:
            doc_id, chunk_id = clean_ref.split(":", 1)
            if doc_id in self._evidence_cache:
                base = self._evidence_cache[doc_id]
                return EvidenceSummaryItem(
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    title=base.title,
                    source_url=base.source_url,
                    license=base.license,
                )
        return None

    def get_cohort_sessions(
        self,
        cohort_id: str,
        topic: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> tuple[List[RemediationSessionState], bool]:
        """Retrieve completed sessions for an allowlisted cohort.

        Returns:
            (sessions_list, is_demo_data)

        Raises:
            UnknownCohortError: If cohort_id is not in ALLOWED_COHORTS.
            DemoCohortDisabledError: If cohort_id is demo cohort but demo mode is disabled in production.
        """
        # Cohort access boundary: reject arbitrary unknown cohort identifiers
        if cohort_id not in self.allowed_cohorts:
            raise UnknownCohortError(f"Cohort '{cohort_id}' is not a registered cohort.")

        # Synthetic demo data boundary: check runtime enablement
        if cohort_id == DEMO_COHORT_ID:
            if not is_demo_enabled():
                raise DemoCohortDisabledError(
                    "Phase 3 synthetic demo cohorts are disabled in this runtime "
                    "unless explicitly enabled via MEDICALPLAB_PHASE_3_DEMO_ENABLED=true."
                )
            sessions = get_demo_sessions()
            if topic:
                sessions = [s for s in sessions if s.topic == topic or (s.detected_gap and s.detected_gap.topic == topic)]
            return sessions, True

        # Read-only query from SQLite database
        if not self.db_path.exists():
            return [], False

        sessions: list[RemediationSessionState] = []
        try:
            # Open read-only SQLite URI connection
            conn_uri = f"file:{self.db_path.as_posix()}?mode=ro"
            with closing(sqlite3.connect(conn_uri, uri=True, timeout=5.0)) as conn:
                conn.row_factory = sqlite3.Row
                query = "SELECT session_state_json FROM remediation_sessions WHERE 1=1"
                params: list[str] = []
                if topic:
                    query += " AND topic = ?"
                    params.append(topic)
                cur = conn.execute(query, params)
                for row in cur.fetchall():
                    raw_json = row["session_state_json"]
                    try:
                        session_state = RemediationSessionState.model_validate_json(raw_json)
                        sessions.append(session_state)
                    except Exception as parse_exc:
                        logger.warning("Skipping corrupted remediation session record: %s", parse_exc)
        except Exception as db_exc:
            logger.warning("Error reading remediation sessions from %s: %s", self.db_path, db_exc)
            return [], False

        return sessions, False
