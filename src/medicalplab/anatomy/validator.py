"""Strict validation boundary for generated 3D scene actions and agent responses."""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from .commands import AnatomyAction, AnatomyCommand
from .manifest import valid_structure_ids
from .models import (
    AnatomyActionType,
    AnatomyAgentResponse,
    InteractionRequest,
    InteractionRequestType,
    SceneAction,
)
from .ontology import resolve_structure as legacy_resolve_structure

logger = logging.getLogger(__name__)

# Security guardrails against prompt injection / arbitrary script injection
SUSPICIOUS_SCRIPT_PATTERNS = [
    re.compile(r"<\s*script[^>]*>", re.I),
    re.compile(r"javascript\s*:", re.I),
    re.compile(r"eval\s*\(", re.I),
    re.compile(r"Function\s*\(", re.I),
    re.compile(r"window\.", re.I),
    re.compile(r"document\.", re.I),
    re.compile(r"process\.", re.I),
    re.compile(r"fetch\s*\(", re.I),
]


class AnatomyCommandError(ValueError):
    """Raised when a scene command targets an unknown or unsafe structure/action."""
    pass


def validate_anatomy_command(command: AnatomyCommand) -> AnatomyCommand:
    """Validate structure IDs and return a canonicalized command for legacy cardiovascular API."""
    if not isinstance(command, AnatomyCommand):
        raise AnatomyCommandError("command must be an AnatomyCommand")

    if command.action == AnatomyAction.RESET:
        return command

    canonical_ids: list[str] = []
    unknown: list[str] = []

    for raw_id in command.structure_ids:
        structure = legacy_resolve_structure(raw_id)
        if structure is None:
            unknown.append(raw_id)
            continue
        if structure.structure_id not in canonical_ids:
            canonical_ids.append(structure.structure_id)

    if unknown:
        raise AnatomyCommandError(
            "Unknown anatomy structure(s): " + ", ".join(unknown)
        )

    if not canonical_ids:
        raise AnatomyCommandError("No valid anatomy structures remain after validation")

    return AnatomyCommand(
        action=command.action,
        structure_ids=tuple(canonical_ids),
        opacity=command.opacity,
        schema_version=command.schema_version,
    )


class AnatomyValidationError(ValueError):
    """Raised when an action or agent output fails safety verification."""
    pass


def validate_scene_action(action: SceneAction, allowed_ids: Optional[tuple[str, ...]] = None) -> SceneAction:
    """Validate a single scene action against allowed types and manifest structures."""
    if allowed_ids is None:
        allowed_ids = valid_structure_ids()

    # 1. Action type check
    if not isinstance(action.action, AnatomyActionType):
        try:
            action.action = AnatomyActionType(str(action.action))
        except (ValueError, KeyError) as exc:
            raise AnatomyValidationError(f"UNKNOWN_ACTION: '{action.action}' is not a permitted scene action.") from exc

    # 2. Reset action must not target individual structures
    if action.action == AnatomyActionType.RESET_SCENE:
        if action.structure_id is not None:
            raise AnatomyValidationError("RESET_SCENE must not specify a target structure_id.")
        return action

    # 3. Structure targeting actions require a valid structure_id from manifest
    if action.action in (
        AnatomyActionType.FOCUS_STRUCTURE,
        AnatomyActionType.HIGHLIGHT_STRUCTURE,
        AnatomyActionType.ISOLATE_STRUCTURE,
        AnatomyActionType.SHOW_STRUCTURE,
        AnatomyActionType.HIDE_STRUCTURE,
        AnatomyActionType.SET_STRUCTURE_OPACITY,
        AnatomyActionType.SHOW_RELATION,
    ):
        if not action.structure_id:
            raise AnatomyValidationError(f"Action '{action.action.value}' requires a target structure_id.")

        clean_id = action.structure_id.strip().casefold()
        if clean_id not in allowed_ids:
            raise AnatomyValidationError(
                f"UNKNOWN_STRUCTURE: Structure '{action.structure_id}' is not in the verified anatomy manifest."
            )
        action.structure_id = clean_id

    # 4. Opacity validation
    if action.opacity is not None:
        if not (0.0 <= action.opacity <= 1.0):
            raise AnatomyValidationError(f"Opacity {action.opacity} must be bounded between 0.0 and 1.0.")

    return action


def sanitize_text(text: str) -> str:
    """Check and sanitize agent text for script injection attempts."""
    for pattern in SUSPICIOUS_SCRIPT_PATTERNS:
        if pattern.search(text):
            raise AnatomyValidationError("SECURITY_VIOLATION: Unsafe script execution pattern detected in tutor text.")
    return text.strip()


def validate_agent_response(
    raw_response: dict[str, Any] | AnatomyAgentResponse,
    allowed_ids: Optional[tuple[str, ...]] = None,
) -> AnatomyAgentResponse:
    """Strictly validate agent output. If invalid, fails closed with a safe fallback response."""
    if allowed_ids is None:
        allowed_ids = valid_structure_ids()

    try:
        if isinstance(raw_response, dict):
            raw_msg = str(raw_response.get("tutor_message", ""))
            clean_msg = sanitize_text(raw_msg)

            validated_actions: list[SceneAction] = []
            for act_dict in raw_response.get("scene_actions", []):
                act_model = SceneAction(**act_dict)
                validated_actions.append(validate_scene_action(act_model, allowed_ids))

            interaction = None
            if raw_response.get("interaction_request"):
                ir = raw_response["interaction_request"]
                target_id = ir.get("target_structure_id")
                if target_id and target_id.strip().casefold() not in allowed_ids:
                    raise AnatomyValidationError(f"Interaction target '{target_id}' not in manifest.")
                interaction = InteractionRequest(
                    type=InteractionRequestType(ir.get("type", InteractionRequestType.IDENTIFY_STRUCTURE.value)),
                    target_structure_id=target_id.strip().casefold() if target_id else None,
                    prompt=sanitize_text(ir.get("prompt", "")),
                )

            return AnatomyAgentResponse(
                tutor_message=clean_msg,
                scene_actions=validated_actions,
                interaction_request=interaction,
                fallback_applied=False,
            )

        elif isinstance(raw_response, AnatomyAgentResponse):
            sanitize_text(raw_response.tutor_message)
            validated_actions = [
                validate_scene_action(act, allowed_ids) for act in raw_response.scene_actions
            ]
            if raw_response.interaction_request and raw_response.interaction_request.target_structure_id:
                if raw_response.interaction_request.target_structure_id not in allowed_ids:
                    raise AnatomyValidationError("Interaction target not in manifest.")
            raw_response.scene_actions = validated_actions
            return raw_response

        raise AnatomyValidationError("Unsupported response type.")

    except Exception as exc:
        logger.warning("Anatomy agent response validation failed; applying fail-closed fallback: %s", exc)
        return AnatomyAgentResponse(
            tutor_message=(
                "I am focusing on our verified renal anatomy learning objective. "
                "Please inspect the kidney model in the viewport, and click any vessel or parenchymal region to explore."
            ),
            scene_actions=[],  # NO scene mutation on validation failure
            interaction_request=None,
            fallback_applied=True,
        )
