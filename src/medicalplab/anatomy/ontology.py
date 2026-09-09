"""MVP cardiovascular anatomy ontology.

Only registered structures may be targeted by Anatomy AI commands. This is the
safety boundary that prevents a model from inventing viewport identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnatomyStructure:
    structure_id: str
    name: str
    aliases: tuple[str, ...]
    system: str
    parent_id: str | None = None
    related_structure_ids: tuple[str, ...] = ()


MVP_STRUCTURES: tuple[AnatomyStructure, ...] = (
    AnatomyStructure("heart", "Heart", ("cardiac organ",), "cardiovascular"),
    AnatomyStructure("lad", "Left Anterior Descending Artery", ("left anterior descending", "lad artery", "anterior interventricular artery"), "cardiovascular", "heart", ("left_ventricle",)),
    AnatomyStructure("rca", "Right Coronary Artery", ("right coronary", "rca artery"), "cardiovascular", "heart", ("right_ventricle",)),
    AnatomyStructure("lcx", "Left Circumflex Artery", ("circumflex", "circumflex artery", "left circumflex", "lcx artery"), "cardiovascular", "heart", ("left_atrium", "left_ventricle")),
    AnatomyStructure("aorta", "Aorta", ("ascending aorta", "aortic root"), "cardiovascular", "heart"),
    AnatomyStructure("left_atrium", "Left Atrium", ("la",), "cardiovascular", "heart", ("mitral_valve",)),
    AnatomyStructure("right_atrium", "Right Atrium", ("ra",), "cardiovascular", "heart", ("right_ventricle",)),
    AnatomyStructure("left_ventricle", "Left Ventricle", ("lv",), "cardiovascular", "heart", ("mitral_valve", "aortic_valve")),
    AnatomyStructure("right_ventricle", "Right Ventricle", ("rv",), "cardiovascular", "heart", ("right_atrium",)),
    AnatomyStructure("mitral_valve", "Mitral Valve", ("bicuspid valve", "left atrioventricular valve"), "cardiovascular", "heart", ("left_atrium", "left_ventricle")),
    AnatomyStructure("aortic_valve", "Aortic Valve", ("aortic semilunar valve",), "cardiovascular", "heart", ("left_ventricle", "aorta")),
)


_BY_ID = {structure.structure_id: structure for structure in MVP_STRUCTURES}
_ALIAS_TO_ID: dict[str, str] = {}

for structure in MVP_STRUCTURES:
    names = (structure.structure_id, structure.name, *structure.aliases)
    for name in names:
        _ALIAS_TO_ID[" ".join(name.casefold().split())] = structure.structure_id


def get_structure(structure_id: str) -> AnatomyStructure | None:
    return _BY_ID.get(structure_id.strip().casefold())


def resolve_structure(value: str) -> AnatomyStructure | None:
    """Resolve canonical ID, English name, or approved alias to a structure."""
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = " ".join(value.casefold().split())
    structure_id = _ALIAS_TO_ID.get(normalized)
    return _BY_ID.get(structure_id) if structure_id else None


def valid_structure_ids() -> tuple[str, ...]:
    return tuple(structure.structure_id for structure in MVP_STRUCTURES)
