"""AI anatomy command planner with manifest/ontology validation."""

from __future__ import annotations

import json
import re
from typing import Any

from medicalplab.stage_b.models import strict_json

from .commands import AnatomyAction, AnatomyCommand
from .ontology import MVP_STRUCTURES, get_structure, resolve_structure
from .provider import StaticCardiovascularAssetProvider
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
- show: display or reveal target structures
- hide: hide target structures

CRITICAL SAFETY RULE:
You may use ONLY structure_id values present in the supplied structure inventory.
Never invent an ID. If the user query refers to an unsupported structure (e.g. kidney, liver, brain),
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
    """Deterministic natural-language parser and ontology resolver.

    Maps student text directly into validated typed scene commands with
    associated educational context. Rejects unsupported or hallucinated organs.
    """
    if not isinstance(query, str) or not query.strip():
        raise AnatomyAgentError("Anatomy query must be a non-empty string")

    clean_query = " " + " ".join(re.findall(r"[a-zA-Z0-9_]+", query.casefold())) + " "

    # 1. Check for reset
    if any(k in clean_query for k in [" reset ", " clear view ", " restore default ", " default view ", " reset view "]):
        cmd = AnatomyCommand(action=AnatomyAction.RESET)
        return cmd, {
            "status": "success",
            "action": "reset",
            "message": "Viewport reset to canonical anatomical orientation.",
        }

    # 2. Check for explicit unsupported anatomical organs
    for kw in UNSUPPORTED_ANATOMY_KEYWORDS:
        if f" {kw} " in clean_query or f" {kw}s " in clean_query:
            raise AnatomyAgentError(
                f"UNSUPPORTED_STRUCTURE: Structure '{kw}' is outside the verified cardiovascular anatomy ontology (11 structures supported)."
            )

    # 3. Detect action intent
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

    # 4. Resolve target structures
    matched_ids: list[str] = []

    # Map candidate search phrases sorted by length descending to match multi-word phrases first
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
    """Convert natural language into validated viewport commands."""

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

        # Deterministic offline resolution
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
