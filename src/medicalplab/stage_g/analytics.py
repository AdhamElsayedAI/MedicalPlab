"""Analytics aggregation service for Stage-G.

Provides dual-tier learning and operational analytics:
1. Student: mastery, progress, weak topics, and improvement rate.
2. Institution: cohort accuracy, engagement metrics, difficult topics, and AI activity.
"""

from collections import Counter
import time
from typing import Any

from medicalplab.stage_b.models import require, strings
from .database import DatabaseService
from .models import (
    InstitutionAnalyticsRecord,
    StudentAnalyticsRecord,
    UserRole,
)


class PlatformAnalyticsService:
    """Computes deterministic individual and institutional analytics."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def compute_student_analytics(
        self,
        student_id: str,
        tenant_id: str,
    ) -> StudentAnalyticsRecord:
        """Calculate learning analytics and mastery progression for a student."""
        strings(student_id, tenant_id)
        clean_student = student_id.strip()
        clean_tenant = tenant_id.strip()

        # Enforce tenant isolation for the student
        user = self.db.users.get_by_id(clean_student)
        if user:
            require(
                user.tenant_id == clean_tenant,
                f"Cross-tenant access forbidden: Student '{clean_student}' belongs to '{user.tenant_id}', not '{clean_tenant}'",
            )

        attempts = self.db.attempts.list_by_student(clean_student)
        total = len(attempts)

        if total == 0:
            record = StudentAnalyticsRecord(
                student_id=clean_student,
                tenant_id=clean_tenant,
                total_attempts=0,
                overall_accuracy=0.0,
                mastery_level="UNRATED",
                weak_topics=(),
                improvement_rate=0.0,
                updated_at=time.time(),
            )
            self.db.analytics.save_student(record)
            return record

        # Extract correctness and topics
        correct_count = 0
        topic_attempts: dict[str, list[bool]] = {}

        for att in attempts:
            if isinstance(att, dict):
                is_corr = att.get("is_correct")
                if is_corr is None:
                    is_corr = att.get("correct", False)
                topic = att.get("topic", "General Medicine")
            elif isinstance(att, (tuple, list)) and len(att) >= 4:
                topic = att[2]
                is_corr = att[3]
            else:
                is_corr = getattr(att, "is_correct", None)
                if is_corr is None:
                    is_corr = getattr(att, "correct", False)
                topic = getattr(att, "topic", "General Medicine")

            is_corr = bool(is_corr)
            topic = str(topic or "General Medicine")

            if is_corr:
                correct_count += 1

            if topic not in topic_attempts:
                topic_attempts[topic] = []
            topic_attempts[topic].append(is_corr)

        overall_acc = round(correct_count / total, 4)

        # Identify weak topics (< 60% accuracy)
        weak_topics = []
        for t, results in topic_attempts.items():
            t_acc = sum(1 for r in results if r) / len(results)
            if t_acc < 0.60:
                weak_topics.append(t)

        # Calculate improvement rate (second half accuracy vs first half accuracy)
        if total >= 4:
            mid = total // 2
            first_half = attempts[:mid]
            second_half = attempts[mid:]

            def _get_corr(a: Any) -> bool:
                if isinstance(a, dict):
                    return bool(a.get("is_correct", a.get("correct", False)))
                if isinstance(a, (tuple, list)) and len(a) >= 4:
                    return bool(a[3])
                return bool(getattr(a, "is_correct", getattr(a, "correct", False)))

            first_acc = sum(1 for a in first_half if _get_corr(a)) / len(first_half)
            second_acc = sum(1 for a in second_half if _get_corr(a)) / len(second_half)
            improvement_rate = round(second_acc - first_acc, 4)
        else:
            improvement_rate = 0.0

        if overall_acc >= 0.85:
            mastery_level = "MASTERY"
        elif overall_acc >= 0.70:
            mastery_level = "COMPETENT"
        elif overall_acc >= 0.50:
            mastery_level = "DEVELOPING"
        else:
            mastery_level = "NOVICE"

        record = StudentAnalyticsRecord(
            student_id=clean_student,
            tenant_id=clean_tenant,
            total_attempts=total,
            overall_accuracy=overall_acc,
            mastery_level=mastery_level,
            weak_topics=tuple(sorted(weak_topics)),
            improvement_rate=improvement_rate,
            updated_at=time.time(),
        )

        self.db.analytics.save_student(record)
        return record

    def compute_institution_analytics(
        self,
        tenant_id: str,
        cohort_id: str = "cohort-all",
    ) -> InstitutionAnalyticsRecord:
        """Aggregate institutional cohort performance and engagement statistics."""
        strings(tenant_id)
        clean_tenant = tenant_id.strip()

        users = self.db.users.list_by_tenant(clean_tenant)
        students = [u for u in users if u.role in (UserRole.STUDENT, "STUDENT", "student")]
        total_students = len(students)

        # Aggregate attempts across all students or direct tenant attempts
        all_tenant_attempts = list(self.db.attempts.list_by_tenant(clean_tenant))
        if not all_tenant_attempts:
            for s in students:
                all_tenant_attempts.extend(self.db.attempts.list_by_student(s.user_id))

        def _get_corr(a: Any) -> bool:
            if isinstance(a, dict):
                return bool(a.get("is_correct", a.get("correct", False)))
            if isinstance(a, (tuple, list)) and len(a) >= 4:
                return bool(a[3])
            return bool(getattr(a, "is_correct", getattr(a, "correct", False)))

        def _get_topic(a: Any) -> str:
            if isinstance(a, dict):
                return str(a.get("topic", "General"))
            if isinstance(a, (tuple, list)) and len(a) >= 3:
                return str(a[2])
            return str(getattr(a, "topic", "General"))

        if all_tenant_attempts:
            correct_count = sum(1 for a in all_tenant_attempts if _get_corr(a))
            cohort_acc = round(correct_count / len(all_tenant_attempts), 4)
        else:
            cohort_acc = 0.0

        # Difficult topics across cohort (where misses occurred)
        topic_misses = Counter()
        for a in all_tenant_attempts:
            if not _get_corr(a):
                topic_misses[_get_topic(a)] += 1

        top_difficult = tuple(t for t, _ in topic_misses.most_common(3))

        # Query total AI requests logged for this tenant
        ai_records = self.db.usage.list_by_tenant(clean_tenant)
        total_ai_reqs = len(ai_records)

        record = InstitutionAnalyticsRecord(
            tenant_id=clean_tenant,
            cohort_id=cohort_id.strip(),
            total_students=total_students,
            active_students_7d=total_students,
            cohort_accuracy=cohort_acc,
            difficult_topics=top_difficult,
            total_ai_requests=total_ai_reqs,
            updated_at=time.time(),
        )

        self.db.analytics.save_institution(record)
        return record
