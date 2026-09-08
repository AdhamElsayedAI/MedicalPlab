"""Validation and canonicalization for Anatomy AI commands."""

from __future__ import annotations

from .commands import AnatomyAction, AnatomyCommand
from .ontology import resolve_structure


class AnatomyCommandError(ValueError):
    """Raised when a scene command targets an unknown or unsafe structure/action."""


def validate_anatomy_command(command: AnatomyCommand) -> AnatomyCommand:
    """Validate structure IDs and return a canonicalized command.

    Every target must resolve against the loaded MVP ontology. Unknown IDs are
    rejected rather than forwarded to the Three.js viewport.
    """
    if not isinstance(command, AnatomyCommand):
        raise AnatomyCommandError("command must be an AnatomyCommand")

    if command.action == AnatomyAction.RESET:
        return command

    canonical_ids: list[str] = []
    unknown: list[str] = []

    for raw_id in command.structure_ids:
        structure = resolve_structure(raw_id)
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
