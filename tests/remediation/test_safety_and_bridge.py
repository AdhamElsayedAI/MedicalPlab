"""Safety Invariant and Phase 1 Protection Tests for Remediation Engine."""
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from medicalplab.remediation.bridge import RemediationTutorBridge
from medicalplab.remediation.models import (
    DetectedLearningGap,
    ReasoningPatternCategory,
    SocraticStrategyType,
)
from medicalplab.tutor.models import TutorChatRequest, TutorChatResponse, TutorCitationDTO
from medicalplab.tutor.service import TutorService


def test_bridge_routes_only_to_tutor_service_chat():
    """Verify that RemediationTutorBridge delegates strictly to TutorService.chat."""
    mock_tutor_service = MagicMock(spec=TutorService)
    mock_tutor_service.chat.return_value = TutorChatResponse(
        response_id="RESP-TEST",
        session_id="SESS-TEST",
        mode="misconception_diagnosis",
        message="Verified grounded remediation probe.",
        socratic_question="What role does renin play?",
        citations=[
            TutorCitationDTO(
                ref="PMC3997861",
                quote="Renin cleaves angiotensinogen...",
                document_id="DOC-PMC-RENAL-0001",
                pmcid="PMC3997861",
                title="Renin-Angiotensin System",
                license="CC-BY",
                chunk_id="DOC-PMC-RENAL-0001-B0003-C01",
            )
        ],
    )

    bridge = RemediationTutorBridge(tutor_service=mock_tutor_service)
    gap = DetectedLearningGap(
        pattern_id="PATTERN-RAAS-SUB-01",
        topic="RAAS mechanisms",
        category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
        reasoning_pattern="Substrate versus product role inversion",
        recommended_strategy=SocraticStrategyType.CONTRAST_CASE,
        confidence=0.95,
        detection_rationale="Selected Angiotensin II",
    )

    response = bridge.invoke_tutor_turn(
        user_id="learner_001",
        question_id="UNI-RENAL-001",
        topic="RAAS mechanisms",
        selected_option="B",
        turn_number=1,
        pedagogical_query="Test query",
        gap=gap,
        session_id="REM-SESSION-001",
    )

    assert mock_tutor_service.chat.call_count == 1
    call_args, call_kwargs = mock_tutor_service.chat.call_args
    req: TutorChatRequest = call_args[0]
    assert req.mode == "misconception_diagnosis"
    assert req.question_id == "UNI-RENAL-001"
    assert req.selected_option == "B"
    assert req.hint_level == 1
    assert len(response.citations) == 1
    assert response.citations[0].pmcid == "PMC3997861"


def test_zero_direct_llm_imports_in_remediation_codebase():
    """Verify that no file in src/medicalplab/remediation/ imports LLM clients directly."""
    remediation_dir = Path(__file__).resolve().parents[2] / "src" / "medicalplab" / "remediation"
    assert remediation_dir.exists()

    forbidden_patterns = [
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
        "google.generativeai",
        "import cohere",
    ]

    for py_file in remediation_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for forbidden in forbidden_patterns:
            assert forbidden not in content, (
                f"SAFETY VIOLATION: Direct LLM import '{forbidden}' found in {py_file.name}. "
                "All generations must route through Phase 1 TutorService."
            )
