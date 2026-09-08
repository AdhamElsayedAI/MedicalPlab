"""AI anatomy command planner with manifest/ontology validation."""

from __future__ import annotations

import json

from medicalplab.stage_b.models import strict_json

from .commands import AnatomyAction, AnatomyCommand
from .ontology import MVP_STRUCTURES
from .validator import validate_anatomy_command


ANATOMY_AGENT_PROMPT = """
You control an educational 3D cardiovascular anatomy viewport.
Return ONE scene command as JSON and nothing else.

Allowed actions:
- focus: move attention/camera to one or more structures
- highlight: visually emphasize structures
- isolate: show only target structures
- ghost: make target structures transparent; include opacity 0.05-1.0
- reset: restore default view; structure_ids must be []

CRITICAL SAFETY RULE:
You may use ONLY structure_id values present in the supplied structure inventory.
Never invent an ID. If the user's wording is ambiguous, choose the closest exact
inventory structure only when the inventory clearly supports it. Otherwise
return an error object instead of a command.

Successful JSON:
{"action":"focus","structure_ids":["lad"],"opacity":null}

Unable to resolve:
{"error":"structure_not_resolved","message":"..."}
"""


class AnatomyAgentError(RuntimeError):
    pass


class AnatomyCommandAgent:
    """Convert natural language into validated viewport commands."""

    def __init__(self, backend):
        self.backend = backend
        self.trace: list[dict] = []

    def plan(self, query: str) -> AnatomyCommand:
        if not isinstance(query, str) or not query.strip():
            raise AnatomyAgentError("Anatomy query must be a non-empty string")

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
