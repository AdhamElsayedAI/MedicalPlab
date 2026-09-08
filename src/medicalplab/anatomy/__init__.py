"""MedicalPlab AI Anatomy command and ontology layer."""

from .commands import AnatomyAction, AnatomyCommand
from .ontology import MVP_STRUCTURES, AnatomyStructure, get_structure, resolve_structure
from .validator import validate_anatomy_command

__all__ = [
    "AnatomyAction",
    "AnatomyCommand",
    "AnatomyStructure",
    "MVP_STRUCTURES",
    "get_structure",
    "resolve_structure",
    "validate_anatomy_command",
]
