"""Small, fail-closed educational bank and independent SQLite attempt store."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

from medicalplab.stage_e.performance_tracker import determine_mastery_level

ROOT = Path(__file__).resolve().parents[3]
BANK = ROOT / "Data/university/questions.json"


class UniversityError(ValueError):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


def normalized(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold()))


def audit_bank(rows: list[dict]) -> list[dict]:
    """Reject all members of duplicate groups; never infer medical corrections."""
    ids = Counter(str(q.get("id", "")) for q in rows)
    stems = Counter(normalized(str(q.get("stem", ""))) for q in rows)
    results = []
    for q in rows:
        reasons = []
        for field in ("id", "stem", "subject", "topic", "explanation", "review_reason"):
            if not isinstance(q.get(field), str) or not q[field].strip():
                reasons.append(f"Missing {field}")
        if not str(q.get("id", "")).startswith("UNI-") or q.get("track") != "university":
            reasons.append("Invalid track or ID")
        if ids[str(q.get("id", ""))] > 1 or stems[normalized(str(q.get("stem", "")))] > 1:
            reasons.append("Duplicate ID or stem")
        options = q.get("options")
        if (not isinstance(options, dict) or not 2 <= len(options) <= 5
                or any(k not in "ABCDE" or len(k) != 1 for k in options)
                or any(not isinstance(v, str) or not v.strip() for v in options.values())
                or len({normalized(str(v)) for v in options.values()}) != len(options)):
            reasons.append("Invalid options")
        if not isinstance(options, dict) or q.get("correct_answer") not in options:
            reasons.append("Invalid answer")
        if q.get("difficulty") not in {"easy", "medium", "hard"}:
            reasons.append("Invalid difficulty")
        if q.get("content_kind") not in {"EDUCATIONAL_BASIC_SCIENCE", "CLINICAL_DECISION_CONTENT"}:
            reasons.append("Invalid content kind")
        if q.get("status") not in {"VERIFIED_EDUCATIONAL", "REVIEW_REQUIRED", "QUARANTINED"}:
            reasons.append("Invalid status")
        # This MVP intentionally has no clinical decision serving pathway.
        if q.get("content_kind") == "CLINICAL_DECISION_CONTENT":
            reasons.append("Clinical decisions require separate evidence review")
        evidence = q.get("evidence", {})
        if not isinstance(evidence, dict) or not all(isinstance(evidence.get(k), str) and evidence[k].strip()
                for k in ("document_id", "chunk_id", "title", "url", "license", "excerpt", "excerpt_sha256")):
            reasons.append("Incomplete evidence")
        elif (not evidence["url"].startswith("https://") or
              hashlib.sha256(evidence["excerpt"].encode()).hexdigest() != evidence["excerpt_sha256"]):
            reasons.append("Invalid evidence integrity")
        text = json.dumps(q, ensure_ascii=False)
        if any(c in text for c in ("\ufffd", "Ã", "Â", "â€")):
            reasons.append("Broken encoding")
        results.append({"id": q.get("id"), "subject": q.get("subject"), "topic": q.get("topic"),
                        "status": "QUARANTINED" if reasons else q["status"],
                        "reasons": reasons or [q["review_reason"]]})
    return results


class UniversityService:
    def __init__(self, bank: Path = BANK, db: Path | None = None):
        self.db = db or ROOT / "Data/persistence/university.sqlite3"
        try:
            rows = json.loads(bank.read_text(encoding="utf-8"))
            if not isinstance(rows, list) or any(not isinstance(q, dict) for q in rows):
                raise ValueError("Invalid bank")
            self.audit = audit_bank(rows)
            self.questions = {q["id"]: q for q, a in zip(rows, self.audit)
                              if a["status"] == "VERIFIED_EDUCATIONAL"}
        except (OSError, ValueError, TypeError) as exc:
            raise UniversityError("University content is unavailable. Please try again later.", 503) from exc

    def connect(self):
        self.db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE IF NOT EXISTS university_attempts (
            user_id TEXT NOT NULL, attempt_key TEXT NOT NULL, question_id TEXT NOT NULL,
            subject TEXT NOT NULL, topic TEXT NOT NULL, selected TEXT NOT NULL,
            correct INTEGER NOT NULL, PRIMARY KEY(user_id, attempt_key))""")
        return conn

    def subjects(self):
        return [{"name": s, "count": sum(q["subject"] == s for q in self.questions.values())}
                for s in sorted({q["subject"] for q in self.questions.values()})]

    def topics(self, subject: str):
        if subject not in {s["name"] for s in self.subjects()}:
            raise UniversityError("Subject is unavailable. Choose an available subject.", 404)
        return [{"name": t, "count": sum(q["subject"] == subject and q["topic"] == t
                                          for q in self.questions.values())}
                for t in sorted({q["topic"] for q in self.questions.values() if q["subject"] == subject})]

    def question(self, question_id: str):
        if question_id not in self.questions:
            raise UniversityError("Question is unavailable. Return to topics.", 404)
        return self.questions[question_id]

    def select(self, subject: str, topic: str, after: str | None = None):
        if topic not in {t["name"] for t in self.topics(subject)}:
            raise UniversityError("Topic is unavailable. Choose an available topic.", 404)
        pool = [q for q in self.questions.values() if q["subject"] == subject and q["topic"] == topic]
        if after and after not in {q["id"] for q in pool}:
            raise UniversityError("Previous question does not belong to this topic.", 422)
        index = next((i + 1 for i, q in enumerate(pool) if q["id"] == after), 0)
        if index >= len(pool):
            return {"question": None, "next_action": "review_topic"}
        q = pool[index]
        return {"question": {k: q[k] for k in ("id", "track", "stem", "subject", "topic", "options", "difficulty")},
                "position": index + 1, "total": len(pool)}

    def progress(self, user: str, conn=None):
        if conn is None:
            with closing(self.connect()) as own:
                return self.progress(user, own)
        rows = conn.execute("SELECT * FROM university_attempts WHERE user_id = ?", (user,)).fetchall()
        topics = []
        for subject in self.subjects():
            for topic in self.topics(subject["name"]):
                attempts = [r for r in rows if r["subject"] == subject["name"] and r["topic"] == topic["name"]]
                n = len(attempts)
                correct = sum(r["correct"] for r in attempts)
                accuracy = round(correct / n, 4) if n else None
                topics.append({"subject": subject["name"], "topic": topic["name"], "attempted": n,
                               "correct": correct, "accuracy": accuracy,
                               "mastery": determine_mastery_level(accuracy or 0, n).value if n else "not_started"})
        weak = sorted([t for t in topics if t["attempted"] and t["accuracy"] < .6],
                      key=lambda t: (t["accuracy"], -t["attempted"], t["topic"]))
        next_topics = weak or sorted(topics, key=lambda t: (t["attempted"], t["topic"]))
        correct = sum(r["correct"] for r in rows)
        return {"track": "university", "attempted": len(rows), "correct": correct,
                "accuracy": round(correct / len(rows), 4) if rows else None,
                "topics": topics, "weak_topics": weak,
                "recommendation": next_topics[0] if next_topics else None}

    def answer(self, user: str, question_id: str, selected: str, key: str):
        q = self.question(question_id)
        if selected not in q["options"]:
            raise UniversityError("Choose one of the available answers.")
        with closing(self.connect()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            previous = conn.execute("SELECT * FROM university_attempts WHERE user_id=? AND attempt_key=?",
                                    (user, key)).fetchone()
            if previous and (previous["question_id"] != question_id or previous["selected"] != selected):
                raise UniversityError("This attempt was already submitted with another answer.", 409)
            if not previous:
                conn.execute("INSERT INTO university_attempts VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (user, key, question_id, q["subject"], q["topic"], selected,
                              int(selected == q["correct_answer"])))
            return {"question_id": question_id, "is_correct": selected == q["correct_answer"],
                    "correct_answer": q["correct_answer"], "explanation": q["explanation"],
                    "subject": q["subject"], "topic": q["topic"],
                    "source": {k: q["evidence"][k] for k in ("title", "url", "license")},
                    "next_action": "next_question", "progress": self.progress(user, conn)}
