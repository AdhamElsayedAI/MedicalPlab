"""Medical exam engine for Stage-F.

Manages practice, exam, and review assessment modes with deterministic scoring
and generates standardized attempt analytics that directly feed Stage-E learning profiles.
"""

from typing import Any, Sequence
import uuid

from medicalplab.stage_b.models import require, strings
from .models import (
    ExamAnalytics,
    ExamConfig,
    ExamMode,
    ExamQuestion,
    ExamSubmission,
    PlatformDifficulty,
)


class MedicalExamEngine:
    """Deterministic assessment engine for MedicalPlab."""

    def create_exam_config(
        self,
        student_id: str,
        topic: str,
        question_count: int,
        mode: ExamMode = ExamMode.PRACTICE,
        time_limit_minutes: int = 30,
        pass_percentage: float = 0.70,
    ) -> ExamConfig:
        """Create a new exam session configuration."""
        strings(student_id, topic)
        require(question_count >= 1, "'question_count' must be >= 1")
        exam_id = f"EXAM-{uuid.uuid4().hex[:8].upper()}"

        return ExamConfig(
            exam_id=exam_id,
            student_id=student_id.strip(),
            mode=mode,
            topic=topic.strip(),
            question_count=question_count,
            time_limit_minutes=time_limit_minutes,
            pass_percentage=pass_percentage,
        )

    def grade_submission(
        self,
        config: ExamConfig,
        questions: Sequence[ExamQuestion],
        submission: ExamSubmission,
    ) -> ExamAnalytics:
        """Grade exam submission deterministically and compile Stage-E compatible attempt records."""
        require(isinstance(config, ExamConfig), "config must be an ExamConfig instance")
        require(isinstance(submission, ExamSubmission), "submission must be an ExamSubmission instance")
        require(config.exam_id == submission.exam_id, "Submission exam_id does not match config")
        require(len(questions) >= 1, "Questions sequence cannot be empty")

        q_map = {q.question_id: q for q in questions}
        submission_map = dict(submission.answers)

        score = 0
        total = len(questions)
        results: list[tuple[str, bool, str, str]] = []
        attempt_records: list[tuple[str, str, str, bool, str]] = []

        for q in questions:
            qid = q.question_id
            selected = submission_map.get(qid, "").strip().upper()
            correct = q.correct_answer.strip().upper()
            is_correct = bool(selected and selected == correct)

            if is_correct:
                score += 1

            results.append((qid, is_correct, selected, correct))

            # Generate Stage-E QuestionAttempt tuple:
            # (attempt_id, question_id, topic, correct, difficulty)
            att_id = f"ATT-{uuid.uuid4().hex[:8].upper()}"
            attempt_records.append(
                (att_id, qid, q.topic, is_correct, q.difficulty.value)
            )

        percentage = round(score / total, 4)
        passed = percentage >= config.pass_percentage

        return ExamAnalytics(
            exam_id=config.exam_id,
            student_id=config.student_id,
            topic=config.topic,
            score=score,
            total_questions=total,
            percentage=percentage,
            passed=passed,
            mode=config.mode,
            question_results=tuple(results),
            attempt_records=tuple(attempt_records),
        )

    def generate_review_breakdown(
        self,
        questions: Sequence[ExamQuestion],
        analytics: ExamAnalytics,
    ) -> dict[str, Any]:
        """Generate human-readable review report with full explanations and citations."""
        q_map = {q.question_id: q for q in questions}
        items = []

        for qid, is_correct, selected, correct in analytics.question_results:
            q = q_map.get(qid)
            if q:
                items.append(
                    {
                        "question_id": qid,
                        "question": q.question,
                        "is_correct": is_correct,
                        "student_answer": selected,
                        "correct_answer": correct,
                        "explanation": q.explanation,
                        "citations": list(q.citations),
                        "difficulty": q.difficulty.value,
                    }
                )

        return {
            "exam_id": analytics.exam_id,
            "topic": analytics.topic,
            "score": f"{analytics.score}/{analytics.total_questions}",
            "percentage": f"{int(analytics.percentage * 100)}%",
            "passed": analytics.passed,
            "review_items": items,
        }
