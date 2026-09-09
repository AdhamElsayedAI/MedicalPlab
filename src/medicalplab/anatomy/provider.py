"""Anatomy 3D asset provider and external generative organ model adapter layer.

Mentor specification:
- ASTRA_ORGAN_MODEL: External generative 3D model status.
- AnatomyAssetProvider: Abstract provider boundary decoupling MedicalPlab from 3D model sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .ontology import MVP_STRUCTURES, get_structure, resolve_structure

# Mandatory mentor specification flag:
# Searched repository, docs, and git history; no public repository URL or identifier found.
ASTRA_ORGAN_MODEL: str = "NOT VERIFIED"


class AnatomyAssetFormat(str, Enum):
    GLTF = "gltf"
    GLB = "glb"
    PROCEDURAL_THREEJS = "procedural_threejs"


@dataclass(frozen=True)
class AnatomyAssetDescriptor:
    structure_id: str
    name: str
    system: str
    format: AnatomyAssetFormat
    asset_uri: str | None
    camera_target: tuple[float, float, float]
    default_zoom: float
    educational_summary: str
    related_structures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["format"] = self.format.value
        return data


CARDIOVASCULAR_SUMMARIES: dict[str, tuple[str, tuple[float, float, float], float]] = {
    "heart": (
        "Muscular organ pumping blood through systemic and pulmonary circulation. Divided into four chambers.",
        (0.0, 0.0, 0.0),
        1.0,
    ),
    "lad": (
        "Left Anterior Descending Artery: courses down the anterior interventricular groove, perfusing anterior myocardium and septum. Crucial in anterior STEMI.",
        (0.1, 0.2, 0.3),
        1.8,
    ),
    "rca": (
        "Right Coronary Artery: courses in the right atrioventricular groove, supplying right ventricle, inferior wall of LV, and SA/AV nodes.",
        (-0.2, 0.1, 0.2),
        1.8,
    ),
    "lcx": (
        "Left Circumflex Artery: curves around the left side of the heart in the coronary sulcus, supplying posterolateral LV myocardium.",
        (0.3, 0.1, -0.1),
        1.8,
    ),
    "aorta": (
        "Primary systemic trunk carrying oxygenated blood from left ventricle to systemic arterial branches.",
        (0.0, 0.6, 0.0),
        1.4,
    ),
    "left_atrium": (
        "Chamber receiving oxygenated pulmonary venous return and channeling blood to left ventricle via mitral valve.",
        (0.2, 0.3, -0.2),
        1.6,
    ),
    "right_atrium": (
        "Chamber receiving deoxygenated systemic venous return from venae cavae; houses sinoatrial nodal pacemaker tissue.",
        (-0.3, 0.2, 0.0),
        1.6,
    ),
    "left_ventricle": (
        "Primary high-pressure systemic pump delivering blood to systemic organs across the aortic valve.",
        (0.2, -0.2, 0.1),
        1.6,
    ),
    "right_ventricle": (
        "Lower-pressure chamber pumping venous return across pulmonary valve into pulmonary circulation for gas exchange.",
        (-0.1, -0.2, 0.2),
        1.6,
    ),
    "mitral_valve": (
        "Dual-cusp atrioventricular valve between left atrium and left ventricle preventing systolic retrograde regurgitation.",
        (0.1, 0.0, 0.0),
        2.2,
    ),
    "aortic_valve": (
        "Tricuspid semilunar valve situated between left ventricular outflow tract and ascending aorta.",
        (0.0, 0.2, 0.1),
        2.2,
    ),
}


class AnatomyAssetProvider(ABC):
    """Abstract adapter boundary for 3D organ mesh providers."""

    @abstractmethod
    def get_asset_descriptor(self, structure_id: str) -> AnatomyAssetDescriptor | None:
        pass

    @abstractmethod
    def list_available_assets(self) -> list[AnatomyAssetDescriptor]:
        pass

    @abstractmethod
    def is_external_model_active(self) -> bool:
        pass


class StaticCardiovascularAssetProvider(AnatomyAssetProvider):
    """Default production provider supporting 11 verified cardiovascular structures."""

    def __init__(self) -> None:
        self._descriptors: dict[str, AnatomyAssetDescriptor] = {}
        for s in MVP_STRUCTURES:
            summary, target, zoom = CARDIOVASCULAR_SUMMARIES.get(
                s.structure_id,
                (f"Anatomical structure: {s.name}.", (0.0, 0.0, 0.0), 1.0),
            )
            self._descriptors[s.structure_id] = AnatomyAssetDescriptor(
                structure_id=s.structure_id,
                name=s.name,
                system=s.system,
                format=AnatomyAssetFormat.PROCEDURAL_THREEJS,
                asset_uri=None,
                camera_target=target,
                default_zoom=zoom,
                educational_summary=summary,
                related_structures=s.related_structure_ids,
            )

    def get_asset_descriptor(self, structure_id: str) -> AnatomyAssetDescriptor | None:
        resolved = resolve_structure(structure_id)
        if not resolved:
            return None
        return self._descriptors.get(resolved.structure_id)

    def list_available_assets(self) -> list[AnatomyAssetDescriptor]:
        return list(self._descriptors.values())

    def is_external_model_active(self) -> bool:
        return False
