"""Deterministic benchmark harness and gold evaluation suite for Anatomy AI."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any

from .agent import AnatomyAgentError, resolve_query_to_command
from .commands import AnatomyAction
from .ontology import MVP_STRUCTURES


@dataclass(frozen=True)
class AnatomyTestCase:
    case_id: str
    query: str
    expected_action: AnatomyAction | None
    expected_structures: tuple[str, ...]
    is_supported: bool
    category: str


GOLD_ANATOMY_TEST_SET: tuple[AnatomyTestCase, ...] = (
    # --- Category: Canonical Names (11 structures) ---
    AnatomyTestCase("TC-CAN-01", "Focus on the heart", AnatomyAction.FOCUS, ("heart",), True, "canonical"),
    AnatomyTestCase("TC-CAN-02", "Show the lad", AnatomyAction.SHOW, ("lad",), True, "canonical"),
    AnatomyTestCase("TC-CAN-03", "Highlight the rca", AnatomyAction.HIGHLIGHT, ("rca",), True, "canonical"),
    AnatomyTestCase("TC-CAN-04", "Focus on the lcx", AnatomyAction.FOCUS, ("lcx",), True, "canonical"),
    AnatomyTestCase("TC-CAN-05", "Show me the aorta", AnatomyAction.SHOW, ("aorta",), True, "canonical"),
    AnatomyTestCase("TC-CAN-06", "Highlight the left atrium", AnatomyAction.HIGHLIGHT, ("left_atrium",), True, "canonical"),
    AnatomyTestCase("TC-CAN-07", "Show the right atrium", AnatomyAction.SHOW, ("right_atrium",), True, "canonical"),
    AnatomyTestCase("TC-CAN-08", "Focus on the left ventricle", AnatomyAction.FOCUS, ("left_ventricle",), True, "canonical"),
    AnatomyTestCase("TC-CAN-09", "Isolate the right ventricle", AnatomyAction.ISOLATE, ("right_ventricle",), True, "canonical"),
    AnatomyTestCase("TC-CAN-10", "Show the mitral valve", AnatomyAction.SHOW, ("mitral_valve",), True, "canonical"),
    AnatomyTestCase("TC-CAN-11", "Highlight the aortic valve", AnatomyAction.HIGHLIGHT, ("aortic_valve",), True, "canonical"),

    # --- Category: Approved Aliases & Acronyms ---
    AnatomyTestCase("TC-ALI-01", "Show me the LAD artery", AnatomyAction.SHOW, ("lad",), True, "alias"),
    AnatomyTestCase("TC-ALI-02", "Focus on left anterior descending", AnatomyAction.FOCUS, ("lad",), True, "alias"),
    AnatomyTestCase("TC-ALI-03", "Highlight anterior interventricular artery", AnatomyAction.HIGHLIGHT, ("lad",), True, "alias"),
    AnatomyTestCase("TC-ALI-04", "Show the right coronary artery", AnatomyAction.SHOW, ("rca",), True, "alias"),
    AnatomyTestCase("TC-ALI-05", "Highlight circumflex artery", AnatomyAction.HIGHLIGHT, ("lcx",), True, "alias"),
    AnatomyTestCase("TC-ALI-06", "Show the ascending aorta", AnatomyAction.SHOW, ("aorta",), True, "alias"),
    AnatomyTestCase("TC-ALI-07", "Focus on the aortic root", AnatomyAction.FOCUS, ("aorta",), True, "alias"),
    AnatomyTestCase("TC-ALI-08", "Highlight the bicuspid valve", AnatomyAction.HIGHLIGHT, ("mitral_valve",), True, "alias"),
    AnatomyTestCase("TC-ALI-09", "Show left atrioventricular valve", AnatomyAction.SHOW, ("mitral_valve",), True, "alias"),
    AnatomyTestCase("TC-ALI-10", "Focus on aortic semilunar valve", AnatomyAction.FOCUS, ("aortic_valve",), True, "alias"),
    AnatomyTestCase("TC-ALI-11", "Show the LV", AnatomyAction.SHOW, ("left_ventricle",), True, "alias"),
    AnatomyTestCase("TC-ALI-12", "Highlight the RV", AnatomyAction.HIGHLIGHT, ("right_ventricle",), True, "alias"),
    AnatomyTestCase("TC-ALI-13", "Focus on LA", AnatomyAction.FOCUS, ("left_atrium",), True, "alias"),
    AnatomyTestCase("TC-ALI-14", "Show RA", AnatomyAction.SHOW, ("right_atrium",), True, "alias"),
    AnatomyTestCase("TC-ALI-15", "Focus on the cardiac organ", AnatomyAction.FOCUS, ("heart",), True, "alias"),

    # --- Category: Case & Natural Language Variations ---
    AnatomyTestCase("TC-NL-01", "SHOW ME THE LEFT VENTRICLE PLEASE", AnatomyAction.SHOW, ("left_ventricle",), True, "natural_language"),
    AnatomyTestCase("TC-NL-02", "can you focus on the aorta?", AnatomyAction.FOCUS, ("aorta",), True, "natural_language"),
    AnatomyTestCase("TC-NL-03", "Please highlight the Left Anterior Descending", AnatomyAction.HIGHLIGHT, ("lad",), True, "natural_language"),
    AnatomyTestCase("TC-NL-04", "Hide the right atrium", AnatomyAction.HIDE, ("right_atrium",), True, "natural_language"),
    AnatomyTestCase("TC-NL-05", "Remove the aorta from view", AnatomyAction.HIDE, ("aorta",), True, "natural_language"),
    AnatomyTestCase("TC-NL-06", "Ghost the heart mesh", AnatomyAction.GHOST, ("heart",), True, "natural_language"),
    AnatomyTestCase("TC-NL-07", "Zoom in on the mitral valve", AnatomyAction.FOCUS, ("mitral_valve",), True, "natural_language"),
    AnatomyTestCase("TC-NL-08", "Center on the aortic valve", AnatomyAction.FOCUS, ("aortic_valve",), True, "natural_language"),
    AnatomyTestCase("TC-NL-09", "Look at the right ventricle", AnatomyAction.FOCUS, ("right_ventricle",), True, "natural_language"),
    AnatomyTestCase("TC-NL-10", "Emphasize the rca", AnatomyAction.HIGHLIGHT, ("rca",), True, "natural_language"),
    AnatomyTestCase("TC-NL-11", "Display the left atrium", AnatomyAction.SHOW, ("left_atrium",), True, "natural_language"),
    AnatomyTestCase("TC-NL-12", "Reveal the circumflex", AnatomyAction.SHOW, ("lcx",), True, "natural_language"),
    AnatomyTestCase("TC-NL-13", "Conceal the left ventricle", AnatomyAction.HIDE, ("left_ventricle",), True, "natural_language"),
    AnatomyTestCase("TC-NL-14", "Transparent heart view", AnatomyAction.GHOST, ("heart",), True, "natural_language"),
    AnatomyTestCase("TC-NL-15", "Isolate lad", AnatomyAction.ISOLATE, ("lad",), True, "natural_language"),

    # --- Category: Multi-Structure Requests ---
    AnatomyTestCase("TC-MUL-01", "Show the left ventricle and aorta", AnatomyAction.SHOW, ("left_ventricle", "aorta"), True, "multi_structure"),
    AnatomyTestCase("TC-MUL-02", "Highlight the lad and rca", AnatomyAction.HIGHLIGHT, ("lad", "rca"), True, "multi_structure"),
    AnatomyTestCase("TC-MUL-03", "Focus on the mitral valve and left atrium", AnatomyAction.FOCUS, ("mitral_valve", "left_atrium"), True, "multi_structure"),
    AnatomyTestCase("TC-MUL-04", "Show the left ventricle and right ventricle", AnatomyAction.SHOW, ("left_ventricle", "right_ventricle"), True, "multi_structure"),
    AnatomyTestCase("TC-MUL-05", "Highlight aorta and aortic valve", AnatomyAction.HIGHLIGHT, ("aorta", "aortic_valve"), True, "multi_structure"),

    # --- Category: Reset Commands ---
    AnatomyTestCase("TC-RST-01", "Reset", AnatomyAction.RESET, (), True, "reset"),
    AnatomyTestCase("TC-RST-02", "Reset view", AnatomyAction.RESET, (), True, "reset"),
    AnatomyTestCase("TC-RST-03", "Clear view", AnatomyAction.RESET, (), True, "reset"),
    AnatomyTestCase("TC-RST-04", "Restore default view", AnatomyAction.RESET, (), True, "reset"),
    AnatomyTestCase("TC-RST-05", "Please reset the camera", AnatomyAction.RESET, (), True, "reset"),

    # --- Category: Direct Naming Without Verb ---
    AnatomyTestCase("TC-DIR-01", "Left ventricle", AnatomyAction.FOCUS, ("left_ventricle",), True, "direct_naming"),
    AnatomyTestCase("TC-DIR-02", "Aorta", AnatomyAction.FOCUS, ("aorta",), True, "direct_naming"),
    AnatomyTestCase("TC-DIR-03", "LAD", AnatomyAction.FOCUS, ("lad",), True, "direct_naming"),
    AnatomyTestCase("TC-DIR-04", "Mitral valve", AnatomyAction.FOCUS, ("mitral_valve",), True, "direct_naming"),
    AnatomyTestCase("TC-DIR-05", "Right atrium", AnatomyAction.FOCUS, ("right_atrium",), True, "direct_naming"),

    # --- Category: Non-Cardiovascular / Unsupported Anatomy (MUST SAFELY REFUSE) ---
    AnatomyTestCase("TC-UNS-01", "Show me the kidney", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-02", "Focus on the renal cortex", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-03", "Highlight the nephron", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-04", "Show the urinary bladder", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-05", "Isolate the ureter", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-06", "Show me the brain", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-07", "Highlight the liver", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-08", "Focus on the pancreas", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-09", "Show the spleen", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-10", "Highlight the lungs", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-11", "Focus on the femur", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-12", "Show the gallbladder", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-13", "Highlight the adrenal gland", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-14", "Focus on the stomach", None, (), False, "unsupported_organ"),
    AnatomyTestCase("TC-UNS-15", "Show the thyroid", None, (), False, "unsupported_organ"),

    # --- Category: Invalid / Ambiguous / Non-Anatomical (MUST SAFELY REFUSE) ---
    AnatomyTestCase("TC-INV-01", "Make it blue", None, (), False, "invalid_intent"),
    AnatomyTestCase("TC-INV-02", "Do a surgical resection", None, (), False, "invalid_intent"),
    AnatomyTestCase("TC-INV-03", "Hello there", None, (), False, "invalid_intent"),
    AnatomyTestCase("TC-INV-04", "Tell me about cardiology", None, (), False, "invalid_intent"),
    AnatomyTestCase("TC-INV-05", "What is the answer to question 5?", None, (), False, "invalid_intent"),
)


@dataclass(frozen=True)
class AnatomyBenchmarkResults:
    total_cases: int
    supported_cases: int
    unsupported_cases: int
    intent_correct: int
    structure_correct: int
    command_valid: int
    refusal_correct: int
    intent_accuracy: float
    structure_resolution_accuracy: float
    command_validity_rate: float
    supported_request_success_rate: float
    unsupported_refusal_rate: float
    structures_covered: int
    total_structures: int
    latency_p50_ms: float
    latency_p95_ms: float
    failures: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_anatomy_benchmark(test_cases: tuple[AnatomyTestCase, ...] = GOLD_ANATOMY_TEST_SET) -> AnatomyBenchmarkResults:
    total = len(test_cases)
    supported_total = sum(1 for tc in test_cases if tc.is_supported)
    unsupported_total = total - supported_total

    intent_correct = 0
    structure_correct = 0
    command_valid = 0
    refusal_correct = 0
    failures: list[dict[str, Any]] = []
    latencies: list[float] = []
    observed_structures: set[str] = set()

    for tc in test_cases:
        t0 = time.perf_counter()
        try:
            cmd, _ = resolve_query_to_command(tc.query)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)

            if not tc.is_supported:
                failures.append({
                    "case_id": tc.case_id,
                    "query": tc.query,
                    "error": "Expected refusal but command succeeded",
                    "got_action": cmd.action.value,
                    "got_structures": list(cmd.structure_ids),
                })
                continue

            # Check action / intent
            if cmd.action == tc.expected_action:
                intent_correct += 1
            else:
                failures.append({
                    "case_id": tc.case_id,
                    "query": tc.query,
                    "error": f"Intent mismatch: expected {tc.expected_action}, got {cmd.action}",
                })

            # Check structure resolution
            expected_set = set(tc.expected_structures)
            got_set = set(cmd.structure_ids)
            if expected_set == got_set:
                structure_correct += 1
                for sid in got_set:
                    observed_structures.add(sid)
            else:
                failures.append({
                    "case_id": tc.case_id,
                    "query": tc.query,
                    "error": f"Structure mismatch: expected {tc.expected_structures}, got {cmd.structure_ids}",
                })

            command_valid += 1

        except AnatomyAgentError:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)
            if not tc.is_supported:
                refusal_correct += 1
            else:
                failures.append({
                    "case_id": tc.case_id,
                    "query": tc.query,
                    "error": "Supported query was refused unexpectedly",
                })
        except Exception as exc:
            failures.append({
                "case_id": tc.case_id,
                "query": tc.query,
                "error": f"Unexpected exception: {exc}",
            })

    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

    return AnatomyBenchmarkResults(
        total_cases=total,
        supported_cases=supported_total,
        unsupported_cases=unsupported_total,
        intent_correct=intent_correct,
        structure_correct=structure_correct,
        command_valid=command_valid,
        refusal_correct=refusal_correct,
        intent_accuracy=round(intent_correct / supported_total, 4) if supported_total else 0.0,
        structure_resolution_accuracy=round(structure_correct / supported_total, 4) if supported_total else 0.0,
        command_validity_rate=round(command_valid / supported_total, 4) if supported_total else 0.0,
        supported_request_success_rate=round(command_valid / supported_total, 4) if supported_total else 0.0,
        unsupported_refusal_rate=round(refusal_correct / unsupported_total, 4) if unsupported_total else 0.0,
        structures_covered=len(observed_structures),
        total_structures=len(MVP_STRUCTURES),
        latency_p50_ms=round(p50, 3),
        latency_p95_ms=round(p95, 3),
        failures=failures,
    )


if __name__ == "__main__":
    results = run_anatomy_benchmark()
    print(json.dumps(results.to_dict(), indent=2))
