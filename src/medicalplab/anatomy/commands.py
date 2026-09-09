"""Typed Anatomy AI scene commands."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AnatomyAction(str, Enum):
    FOCUS = "focus"
    HIGHLIGHT = "highlight"
    ISOLATE = "isolate"
    GHOST = "ghost"
    RESET = "reset"
    SHOW = "show"
    HIDE = "hide"


@dataclass(frozen=True)
class AnatomyCommand:
    action: AnatomyAction
    structure_ids: tuple[str, ...] = ()
    opacity: float | None = None
    schema_version: str = "anatomy-command-v1"

    def __post_init__(self) -> None:
        if self.action == AnatomyAction.RESET:
            if self.structure_ids:
                raise ValueError("reset command must not include structure_ids")
        elif not self.structure_ids:
            raise ValueError(f"{self.action.value} command requires at least one structure_id")

        if len(self.structure_ids) > 16:
            raise ValueError("anatomy command cannot target more than 16 structures")

        if self.opacity is not None and not 0.05 <= self.opacity <= 1.0:
            raise ValueError("opacity must be between 0.05 and 1.0")

        if self.action not in (AnatomyAction.GHOST, AnatomyAction.HIDE) and self.opacity is not None:
            raise ValueError("opacity is only valid for ghost or hide commands")
