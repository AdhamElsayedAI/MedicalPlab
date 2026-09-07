"""JSON parser and generator layer for Stage-C question generation.
"""

from typing import Sequence

from medicalplab.stage_b.models import (
    ContractError,
    exact_keys,
    require,
    strict_json,
)
from .models import (
    Citation,
    GeneratedQuestion,
    QuestionType,
    VALID_OPTION_KEYS,
)


REQUIRED_QUESTION_FIELDS = [
    "question_id",
    "question_type",
    "question",
    "options",
    "correct_answer",
    "explanation",
    "difficulty",
    "topic",
    "citations",
]


def normalize_options(raw_options: Sequence[str]) -> tuple[str, ...]:
    """Normalize options to ensure uniform 'A. text', 'B. text' prefixes."""
    require(
        isinstance(raw_options, (list, tuple)) and len(raw_options) == 4,
        "Must have exactly 4 options",
    )

    cleaned = []
    for idx, (expected_key, opt) in enumerate(zip(VALID_OPTION_KEYS, raw_options)):
        require(isinstance(opt, str) and opt.strip(), "Option must be non-empty string")
        s = opt.strip()
        # If already formatted with 'A.' or 'A)', normalize spacing to 'A. '
        if s.startswith(f"{expected_key}.") or s.startswith(f"{expected_key})"):
            prefix_len = 2
            if len(s) > 2 and s[2] == " ":
                prefix_len = 3
            content = s[prefix_len:].strip()
            cleaned.append(f"{expected_key}. {content}")
        else:
            # If the model emitted just the content without prefix, add it
            cleaned.append(f"{expected_key}. {s}")

    return tuple(cleaned)


def parse_generated_questions(raw: str) -> tuple[GeneratedQuestion, ...]:
    """Parse raw JSON output from model and return immutable GeneratedQuestion objects."""
    obj = strict_json(raw)

    require(isinstance(obj, dict), "Output must be a JSON object")
    exact_keys(obj, ["questions"])

    require(isinstance(obj["questions"], list), "'questions' must be a list")
    require(len(obj["questions"]) >= 1, "At least one question must be generated")

    questions = []

    for idx, q_data in enumerate(obj["questions"], 1):
        require(isinstance(q_data, dict), f"Question {idx} must be a JSON object")
        exact_keys(q_data, REQUIRED_QUESTION_FIELDS)

        # Normalize options
        options = normalize_options(q_data["options"])

        # Parse citations
        require(
            isinstance(q_data["citations"], list) and len(q_data["citations"]) >= 1,
            f"Question {idx} requires a list of citations",
        )
        citations = []
        for c_idx, c_data in enumerate(q_data["citations"], 1):
            require(isinstance(c_data, dict), f"Citation {c_idx} must be an object")
            exact_keys(c_data, ["ref", "quote"])
            citations.append(Citation(ref=c_data["ref"], quote=c_data["quote"]))

        correct_ans = str(q_data["correct_answer"]).strip().upper()
        # Strip trailing dot if present (e.g. 'A.' -> 'A')
        if correct_ans.endswith("."):
            correct_ans = correct_ans[:-1].strip()

        question = GeneratedQuestion(
            question_id=str(q_data["question_id"]).strip(),
            question_type=str(q_data["question_type"]).strip().lower(),
            question=str(q_data["question"]).strip(),
            options=options,
            correct_answer=correct_ans,
            explanation=str(q_data["explanation"]).strip(),
            difficulty=str(q_data["difficulty"]).strip().lower(),
            topic=str(q_data["topic"]).strip(),
            citations=tuple(citations),
        )
        questions.append(question)

    return tuple(questions)
