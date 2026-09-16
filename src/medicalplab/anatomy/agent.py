"""AI anatomy tutor agent and command planner with manifest/ontology validation."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from medicalplab.stage_b.models import strict_json

from .commands import AnatomyAction, AnatomyCommand
from .knowledge import get_all_facts, get_facts_for_structure
from .manifest import get_renal_manifest, get_structure_by_id, resolve_query_to_structure, valid_structure_ids
from .models import (
    AnatomyActionType,
    AnatomyAgentResponse,
    InteractionRequest,
    InteractionRequestType,
    LessonState,
    SceneAction,
)
from .ontology import MVP_STRUCTURES, get_structure as legacy_get_structure, resolve_structure as legacy_resolve_structure
from .provider import StaticCardiovascularAssetProvider
from .validator import validate_agent_response, validate_anatomy_command

logger = logging.getLogger(__name__)

# ============================================================================
# Phase 5 — Structured AI Anatomy Tutor Agent (Renal MVP)
# ============================================================================

ANATOMY_AGENT_SYSTEM_PROMPT = """You are the MedicalPlab AI Anatomy Tutor Agent.
You control an educational 3D anatomical viewport and teach UK PLAB medical anatomy.
You emit STRICT JSON with validated scene actions and clinical explanations.

Allowed scene actions:
- FOCUS_STRUCTURE: focus viewport camera on structure_id
- HIGHLIGHT_STRUCTURE: visually highlight structure_id
- ISOLATE_STRUCTURE: dim or hide everything except structure_id
- SHOW_STRUCTURE: reveal structure_id
- HIDE_STRUCTURE: hide structure_id
- SHOW_RELATION: emphasize relationship between structures
- SET_STRUCTURE_OPACITY: set opacity (0.0 - 1.0) on structure_id (e.g. kidney_capsule_left)
- RESET_SCENE: restore canonical scene state (structure_id must be null)

SAFETY & TRUTH RULES:
1. ONLY use structure_id values present in the verified anatomy inventory.
2. NEVER write arbitrary JavaScript, Three.js code, HTML, or URLs.
3. Every clinical anatomical statement must be grounded in the supplied verified facts.
4. Output MUST conform strictly to this JSON format and nothing else:
{
  "tutor_message": "...",
  "scene_actions": [
    {"action": "HIGHLIGHT_STRUCTURE", "structure_id": "renal_artery_left", "opacity": null, "duration_ms": null}
  ],
  "interaction_request": {
    "type": "IDENTIFY_STRUCTURE",
    "target_structure_id": "renal_vein_left",
    "prompt": "Click the vessel that lies most anteriorly at the renal hilum."
  }
}
"""


class StructuredAnatomyAgent:
    """Anatomy tutor agent directing 3D scene composition and Socratic dialogue."""

    def __init__(self, backend: Optional[Any] = None):
        self.backend = backend

    def plan_interaction(
        self,
        user_query: Optional[str],
        lesson_state: LessonState,
        selected_structure_id: Optional[str] = None,
        target_structure_id: Optional[str] = None,
        hint_level: int = 0,
    ) -> AnatomyAgentResponse:
        """Produce an educational tutor response with validated 3D scene actions."""
        if self.backend is not None:
            try:
                allowed_ids = valid_structure_ids()
                facts = [f.statement for f in get_all_facts()]
                payload = {
                    "query": user_query or "",
                    "lesson_state": lesson_state.value,
                    "selected_structure_id": selected_structure_id,
                    "target_structure_id": target_structure_id,
                    "hint_level": hint_level,
                    "allowed_structures": list(allowed_ids),
                    "verified_facts": facts,
                }
                user_prompt = json.dumps(payload)
                if hasattr(self.backend, "generate_structured"):
                    response_schema = {
                        "type": "object",
                        "properties": {
                            "tutor_message": {"type": "string"},
                            "scene_actions": {"type": "array"},
                            "interaction_request": {"type": "object"},
                        },
                        "required": ["tutor_message", "scene_actions"],
                    }
                    resp = self.backend.generate_structured(
                        system_prompt=ANATOMY_AGENT_SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                        response_schema=response_schema,
                    )
                    raw_dict = resp.structured_json if hasattr(resp, "structured_json") and resp.structured_json else json.loads(resp.raw_text)
                    return validate_agent_response(raw_dict, allowed_ids)
                elif hasattr(self.backend, "generate"):
                    raw = self.backend.generate(ANATOMY_AGENT_SYSTEM_PROMPT, user_prompt)
                    if isinstance(raw, dict) and "text" in raw:
                        parsed = json.loads(str(raw["text"]).strip())
                        return validate_agent_response(parsed, allowed_ids)
            except Exception as exc:
                logger.warning("Generative backend failed; falling back to deterministic grounded planner: %s", exc)

        return self._deterministic_plan(
            user_query=user_query,
            lesson_state=lesson_state,
            selected_structure_id=selected_structure_id,
            target_structure_id=target_structure_id,
            hint_level=hint_level,
        )

    def _deterministic_plan(
        self,
        user_query: Optional[str],
        lesson_state: LessonState,
        selected_structure_id: Optional[str],
        target_structure_id: Optional[str],
        hint_level: int,
    ) -> AnatomyAgentResponse:
        query_text = (user_query or "").casefold()

        # Guided Lesson: Renal Blood Flow & Hilum Orientation
        if lesson_state in (LessonState.INTRO, LessonState.GUIDED_VESSELS) or "blood flow" in query_text or "hilum" in query_text:
            return AnatomyAgentResponse(
                tutor_message=(
                    "Welcome to the Renal Anatomy Lab. Let us investigate renal blood flow and hilum spatial organization. "
                    "The Left Renal Artery branches directly from the abdominal aorta to supply oxygenated blood to the kidney. "
                    "Notice its orientation relative to the renal vein and pelvis: from anterior to posterior, the structures lie Vein, Artery, Pelvis (V-A-P). "
                    "Please physically click the vessel that lies most ANTERIORLY at the renal hilum."
                ),
                scene_actions=[
                    SceneAction(action=AnatomyActionType.RESET_SCENE),
                    SceneAction(action=AnatomyActionType.FOCUS_STRUCTURE, structure_id="hilum_of_kidney_left"),
                    SceneAction(action=AnatomyActionType.SET_STRUCTURE_OPACITY, structure_id="kidney_capsule_left", opacity=0.35),
                    SceneAction(action=AnatomyActionType.HIGHLIGHT_STRUCTURE, structure_id="renal_artery_left"),
                ],
                interaction_request=InteractionRequest(
                    type=InteractionRequestType.IDENTIFY_STRUCTURE,
                    target_structure_id="renal_vein_left",
                    prompt="Click the most anterior vessel at the renal hilum on the 3D model.",
                ),
            )

        # Independent Challenge State: Scene reset, translucent capsule, no target leakage
        if lesson_state == LessonState.CHALLENGE_ACTIVE or (selected_structure_id and target_structure_id and selected_structure_id == target_structure_id):
            challenge_target = "renal_artery_left" if target_structure_id == "renal_vein_left" else (target_structure_id or "renal_artery_left")
            return AnatomyAgentResponse(
                tutor_message=(
                    "Excellent! You accurately identified the Left Renal Vein. "
                    "As you observed, it lies anterior to the renal artery at the hilum and empties into the IVC. "
                    "Now let us test your spatial understanding with an independent 3D identification challenge."
                ),
                scene_actions=[
                    SceneAction(action=AnatomyActionType.RESET_SCENE),
                    SceneAction(action=AnatomyActionType.SET_STRUCTURE_OPACITY, structure_id="kidney_capsule_left", opacity=0.35),
                ],
                interaction_request=InteractionRequest(
                    type=InteractionRequestType.IDENTIFY_STRUCTURE,
                    target_structure_id=challenge_target,
                    prompt="Independent Challenge: Click the vessel that supplies oxygenated blood to the kidney from the abdominal aorta.",
                ),
            )

        # Socratic Hint Progression on Incorrect Physical Selection
        if selected_structure_id and target_structure_id and selected_structure_id != target_structure_id:
            sel_struct = get_structure_by_id(selected_structure_id)
            sel_name = sel_struct.display_name if sel_struct else selected_structure_id

            if hint_level == 1:
                return AnatomyAgentResponse(
                    tutor_message=(
                        f"You selected the {sel_name}. [Hint 1 - Functional Clue]: Consider the difference in function: "
                        "the vessel we are looking for is responsible for returning venous drainage back to the inferior vena cava (IVC), "
                        "not supplying arterial blood or collecting urine."
                    ),
                    scene_actions=[
                        SceneAction(action=AnatomyActionType.FOCUS_STRUCTURE, structure_id="hilum_of_kidney_left"),
                    ],
                    interaction_request=InteractionRequest(
                        type=InteractionRequestType.IDENTIFY_STRUCTURE,
                        target_structure_id=target_structure_id,
                        prompt="Try again: click the vessel draining blood from the kidney.",
                    ),
                )
            elif hint_level == 2:
                return AnatomyAgentResponse(
                    tutor_message=(
                        f"[Hint 2 - Spatial Orientation]: Remember the classic anatomical mnemonic V-A-P (Anterior to Posterior). "
                        "The Vein is situated in FRONT (most anterior), the Artery is in the MIDDLE, and the Pelvis is BEHIND (most posterior). "
                        "Rotate the model to view the anterior surface."
                    ),
                    scene_actions=[
                        SceneAction(action=AnatomyActionType.FOCUS_STRUCTURE, structure_id="hilum_of_kidney_left"),
                        SceneAction(action=AnatomyActionType.SET_STRUCTURE_OPACITY, structure_id="kidney_capsule_left", opacity=0.2),
                    ],
                    interaction_request=InteractionRequest(
                        type=InteractionRequestType.IDENTIFY_STRUCTURE,
                        target_structure_id=target_structure_id,
                        prompt="Identify the anterior-most vessel in front of the renal artery.",
                    ),
                )
            else:
                return AnatomyAgentResponse(
                    tutor_message=(
                        f"[Hint 3 - Near-Target Guidance]: Look directly at the hilum from the ventral view. "
                        f"The {target_structure_id.replace('_', ' ').title()} is the wide vessel crossing anterior to the renal artery."
                    ),
                    scene_actions=[
                        SceneAction(action=AnatomyActionType.FOCUS_STRUCTURE, structure_id=target_structure_id),
                    ],
                    interaction_request=InteractionRequest(
                        type=InteractionRequestType.IDENTIFY_STRUCTURE,
                        target_structure_id=target_structure_id,
                        prompt="Select the target vessel.",
                    ),
                )

        return AnatomyAgentResponse(
            tutor_message=(
                "You are inspecting the 3D Renal Model. Click any anatomical structure (renal artery, renal vein, pelvis, cortex, pyramids) "
                "or request a lesson on renal blood flow or internal parenchymal organization."
            ),
            scene_actions=[SceneAction(action=AnatomyActionType.RESET_SCENE)],
            interaction_request=None,
        )


# ============================================================================
# Legacy Cardiovascular Prototype Support (Preserves Stage-G & Prior Tests)
# ============================================================================

ANATOMY_AGENT_PROMPT = """
You control an educational 3D cardiovascular anatomy viewport.
Return ONE scene command as JSON and nothing else.

Allowed actions:
- focus: move attention/camera to one or more structures
- highlight: visually emphasize structures
- isolate: show only target structures
- ghost: make target structures transparent; include opacity 0.05-1.0
- reset: restore default view; structure_ids must be []
- show: display or reveal target structures
- hide: hide target structures

CRITICAL SAFETY RULE:
You may use ONLY structure_id values present in the supplied structure inventory.
Never invent an ID. If the user query refers to an unsupported structure (e.g. liver, brain),
return an error object instead of a command.

Successful JSON:
{"action":"focus","structure_ids":["lad"],"opacity":null}

Unable to resolve:
{"error":"structure_not_resolved","message":"..."}
"""


class AnatomyAgentError(RuntimeError):
    pass


UNSUPPORTED_ANATOMY_KEYWORDS = (
    "kidney", "nephron", "bladder", "ureter", "renal", "brain", "cerebrum",
    "liver", "pancreas", "spleen", "lung", "lungs", "pulmonary parenchyma",
    "stomach", "gallbladder", "adrenal", "femur", "bone", "spine", "eye",
    "ear", "thyroid", "appendix", "colon", "esophagus", "trachea", "prostate",
)


def resolve_query_to_command(query: str) -> tuple[AnatomyCommand, dict[str, Any]]:
    if not isinstance(query, str) or not query.strip():
        raise AnatomyAgentError("Anatomy query must be a non-empty string")

    clean_query = " " + " ".join(re.findall(r"[a-zA-Z0-9_]+", query.casefold())) + " "

    if any(k in clean_query for k in [" reset ", " clear view ", " restore default ", " default view ", " reset view "]):
        cmd = AnatomyCommand(action=AnatomyAction.RESET)
        return cmd, {
            "status": "success",
            "action": "reset",
            "message": "Viewport reset to canonical anatomical orientation.",
        }

    for kw in UNSUPPORTED_ANATOMY_KEYWORDS:
        if f" {kw} " in clean_query or f" {kw}s " in clean_query:
            raise AnatomyAgentError(
                f"UNSUPPORTED_STRUCTURE: Structure '{kw}' is outside the verified cardiovascular anatomy ontology (11 structures supported)."
            )

    action = AnatomyAction.FOCUS
    if any(k in clean_query for k in [" highlight ", " glow ", " emphasize ", " select "]):
        action = AnatomyAction.HIGHLIGHT
    elif any(k in clean_query for k in [" hide ", " remove ", " conceal ", " vanish "]):
        action = AnatomyAction.HIDE
    elif any(k in clean_query for k in [" isolate ", " show only "]):
        action = AnatomyAction.ISOLATE
    elif any(k in clean_query for k in [" ghost ", " transparent ", " translucent "]):
        action = AnatomyAction.GHOST
    elif any(k in clean_query for k in [" show ", " display ", " reveal ", " view "]):
        action = AnatomyAction.SHOW
    elif any(k in clean_query for k in [" focus ", " zoom ", " center ", " look at "]):
        action = AnatomyAction.FOCUS

    matched_ids: list[str] = []
    candidates: list[tuple[str, str]] = []
    for s in MVP_STRUCTURES:
        candidates.append((s.structure_id, s.structure_id))
        candidates.append((s.name.casefold(), s.structure_id))
        for alias in s.aliases:
            candidates.append((alias.casefold(), s.structure_id))

    candidates.sort(key=lambda x: len(x[0]), reverse=True)

    for phrase, sid in candidates:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        if re.search(pattern, clean_query):
            if sid not in matched_ids:
                matched_ids.append(sid)

    if not matched_ids:
        raise AnatomyAgentError(
            f"STRUCTURE_NOT_RESOLVED: Could not resolve target anatomy structure from query: '{query.strip()}'."
        )

    cmd = AnatomyCommand(action=action, structure_ids=tuple(matched_ids))
    validated = validate_anatomy_command(cmd)

    provider = StaticCardiovascularAssetProvider()
    descriptor = provider.get_asset_descriptor(validated.structure_ids[0])
    edu_context = descriptor.to_dict() if descriptor else {
        "structure_id": validated.structure_ids[0],
        "system": "cardiovascular",
    }

    return validated, edu_context


class AnatomyCommandAgent:
    def __init__(self, backend=None):
        self.backend = backend
        self.trace: list[dict[str, Any]] = []

    def plan(self, query: str) -> AnatomyCommand:
        if not isinstance(query, str) or not query.strip():
            raise AnatomyAgentError("Anatomy query must be a non-empty string")

        if self.backend is not None:
            inventory = [
                {
                    "structure_id": structure.structure_id,
                    "name": structure.name,
                    "aliases": list(structure.aliases),
                    "system": structure.system,
                }
                for structure in MVP_STRUCTURES
            ]
            user_payload = json.dumps(
                {
                    "query": query.strip(),
                    "structure_inventory": inventory,
                },
                ensure_ascii=False,
            )

            result = self.backend.generate(ANATOMY_AGENT_PROMPT, user_payload)
            if not isinstance(result, dict) or "text" not in result:
                raise AnatomyAgentError("Backend response must contain text")

            text = str(result["text"]).strip()
            strict_json(text)
            payload = json.loads(text)

            if payload.get("error"):
                raise AnatomyAgentError(
                    f"{payload.get('error')}: {payload.get('message', 'Unable to resolve anatomy command')}"
                )

            try:
                command = AnatomyCommand(
                    action=AnatomyAction(str(payload["action"])),
                    structure_ids=tuple(str(item) for item in payload.get("structure_ids", [])),
                    opacity=(
                        float(payload["opacity"])
                        if payload.get("opacity") is not None
                        else None
                    ),
                )
                validated = validate_anatomy_command(command)
            except (KeyError, TypeError, ValueError) as exc:
                raise AnatomyAgentError(f"Invalid anatomy command output: {exc}") from exc

            self.trace.append(
                {
                    "query": query.strip(),
                    "action": validated.action.value,
                    "structure_ids": list(validated.structure_ids),
                    "backend_model": getattr(self.backend, "model", None),
                }
            )
            return validated

        cmd, _ = resolve_query_to_command(query)
        self.trace.append(
            {
                "query": query.strip(),
                "action": cmd.action.value,
                "structure_ids": list(cmd.structure_ids),
                "backend_model": "deterministic_ontology_resolver",
            }
        )
        return cmd
