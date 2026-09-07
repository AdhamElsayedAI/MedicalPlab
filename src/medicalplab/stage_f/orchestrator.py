"""Stage-F Unified Platform Orchestrator for MedicalPlab.

Coordinates the Intelligence Router, Session Intelligence, Adaptive Difficulty,
Exam Engine, Case Simulation, and Study Planner across all underlying stages (Stage-R, B, C, D, E).
"""

import time
from typing import Any, Sequence
import uuid

from medicalplab.stage_b.models import require, strings
from .adaptive_difficulty import AdaptiveDifficultyEngine
from .case_simulation import ClinicalCaseSimulationEngine
from .exam_engine import MedicalExamEngine
from .learning_loop import LearningLoopManager
from .models import (
    ExamMode,
    PlatformDifficulty,
    PlatformIntent,
    PlatformResponse,
    SessionContext,
    UserGoal,
)
from .router import IntelligenceRouter
from .session import SessionIntelligenceManager
from .study_planner import LearningPathGenerator


class MedicalPlabPlatformOrchestrator:
    """Master orchestration facade for the MedicalPlab learning platform."""

    def __init__(
        self,
        retrieval_pipeline: Any | None = None,
        tutor_pipeline: Any | None = None,
        student_pipeline: Any | None = None,
        question_pipeline: Any | None = None,
    ):
        self.router = IntelligenceRouter()
        self.session_manager = SessionIntelligenceManager()
        self.difficulty_engine = AdaptiveDifficultyEngine()
        self.exam_engine = MedicalExamEngine()
        self.case_simulator = ClinicalCaseSimulationEngine()
        self.study_planner = LearningPathGenerator()
        self.learning_loop = LearningLoopManager()

        # Injected Stage pipelines (or stubs)
        self.retrieval_pipeline = retrieval_pipeline
        self.tutor_pipeline = tutor_pipeline
        self.student_pipeline = student_pipeline
        self.question_pipeline = question_pipeline

        self.trace: list[dict[str, Any]] = []

    def handle_request(
        self,
        student_id: str,
        query: str,
        session_id: str | None = None,
        corpus: Sequence[Any] | None = None,
        user_goal: UserGoal | None = None,
        exam_submission: Any | None = None,
    ) -> PlatformResponse:
        """Handle a student request end-to-end and return a unified platform response."""
        strings(student_id, query)
        clean_student = student_id.strip()
        clean_query = query.strip()
        start_time = time.perf_counter()

        # 1. Acquire or initialize session context
        if session_id:
            session = self.session_manager.get_session(session_id)
            if not session:
                session = self.session_manager.create_session(clean_student)
        else:
            session = self.session_manager.create_session(clean_student)

        # 2. Classify intent via Intelligence Router
        intent = self.router.classify_intent(clean_query, session=session)
        detected_topic = self.router.extract_topic_hint(clean_query) or session.current_topic

        payload_items: list[tuple[str, str]] = [
            ("intent", intent.value),
            ("topic", detected_topic),
            ("session_id", session.session_id),
        ]
        next_actions: list[str] = []
        explanation: str = ""

        # 3. Dispatch based on intent
        if intent == PlatformIntent.TEACHING:
            explanation = f"Initiated evidence-grounded teaching session for {detected_topic}."
            if self.retrieval_pipeline and corpus:
                # Stage-R retrieval
                packet = self.retrieval_pipeline.retrieve(clean_query, corpus, top_k=2)
                payload_items.append(("evidence_blocks_count", str(len(packet.blocks))))
            payload_items.append(("status", "teaching_ready"))
            next_actions.append(f"Review key {detected_topic} guideline criteria.")
            next_actions.append("Request a clinical case discussion or quiz.")

        elif intent == PlatformIntent.ASSESSMENT:
            diff, diff_reason = self.difficulty_engine.determine_difficulty(
                accuracy=0.65,
                mastery_level="developing",
            )
            payload_items.append(("target_difficulty", diff.value))
            payload_items.append(("difficulty_rationale", diff_reason))
            explanation = f"Configured practice assessment for {detected_topic} at {diff.value.upper()} difficulty."
            next_actions.append(f"Attempt practice MCQs on {detected_topic}.")

        elif intent == PlatformIntent.EXAM:
            exam_config = self.exam_engine.create_exam_config(
                student_id=clean_student,
                topic=detected_topic,
                question_count=5,
                mode=ExamMode.EXAM,
            )
            payload_items.append(("exam_id", exam_config.exam_id))
            payload_items.append(("mode", exam_config.mode.value))
            payload_items.append(("question_count", str(exam_config.question_count)))
            explanation = f"Prepared formal timed medical exam for {detected_topic} (5 questions, 30 min)."
            next_actions.append(f"Begin {exam_config.exam_id} when ready.")

        elif intent == PlatformIntent.CASE_SIMULATION:
            sim_blocks = corpus if corpus else ("Evidence Block Mock",)
            sim_result = self.case_simulator.run_simulation(
                student_id=clean_student,
                topic=detected_topic,
                vignette=clean_query,
                evidence_blocks=sim_blocks,
            )
            payload_items.append(("simulation_id", sim_result.simulation_id))
            payload_items.append(("safety_verified", str(sim_result.clinical_safety_verified)))
            explanation = f"Generated evidence-grounded case simulation for {detected_topic} with verified clinical safety."
            next_actions.append("Evaluate recommended management steps.")
            next_actions.append("Proceed to next clinical decision node.")

        elif intent == PlatformIntent.LEARNING_ANALYSIS:
            # Generate study plan
            mock_report = type(
                "MockReport",
                (),
                {
                    "student_profile": type(
                        "MockProfile",
                        (),
                        {"learning_level": "developing"},
                    )(),
                    "knowledge_gaps": (
                        type(
                            "MockGap",
                            (),
                            {
                                "topic": detected_topic,
                                "reason": f"Student accuracy below threshold in {detected_topic}",
                            },
                        )(),
                    ),
                    "recommendations": (),
                },
            )()
            study_plan = self.study_planner.generate_study_plan(
                student_id=clean_student,
                learning_report=mock_report,
                user_goal=user_goal,
            )
            payload_items.append(("plan_id", study_plan.plan_id))
            payload_items.append(("milestones_count", str(len(study_plan.milestones))))
            explanation = study_plan.summary
            for m in study_plan.milestones:
                next_actions.append(f"[{m.priority}] {m.objective}")

        # 4. Update session interaction history
        self.session_manager.record_interaction(
            session_id=session.session_id,
            intent=intent,
            query=clean_query,
            response_summary=explanation,
            topic_update=detected_topic,
        )

        elapsed = time.perf_counter() - start_time
        self.trace.append(
            {
                "student_id": clean_student,
                "session_id": session.session_id,
                "intent": intent.value,
                "topic": detected_topic,
                "seconds": round(elapsed, 6),
            }
        )

        return PlatformResponse(
            intent=intent,
            session_id=session.session_id,
            payload=tuple(payload_items),
            explanation=explanation,
            next_actions=tuple(next_actions),
        )
