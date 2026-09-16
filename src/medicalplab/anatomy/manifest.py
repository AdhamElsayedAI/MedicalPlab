"""Authoritative deterministic renal anatomy manifest grounded in HuBMAP HRA CCF.

Every structure in this manifest satisfies all Phase 5 hardening invariants:
1. Actual mesh node(s) verified in committed HuBMAP HRA GLB binaries.
2. Deterministic Three.js raycasting resolution.
3. Verified anatomical identity and canonical UBERON ontology mappings.
4. Auditable, open provenance references.
"""
from __future__ import annotations

from typing import Optional
from .models import AnatomyStructure

RENAL_STRUCTURES: tuple[AnatomyStructure, ...] = (
    AnatomyStructure(
        structure_id="renal_artery_left",
        display_name="Left Renal Artery",
        source_system="HRA",
        source_structure_id="UBERON:0001186",
        ontology_id="UBERON:0001186",
        mesh_node_names=["VH_M_left_renal_artery"],
        aliases=["left renal artery", "renal artery left", "arteria renalis sinistra", "renal artery"],
        region="renal_vasculature",
        relationships=[
            {"type": "SUPPLIES", "target": "renal_cortex_left"},
            {"type": "ENTERS_THROUGH", "target": "hilum_of_kidney_left"},
            {"type": "POSTERIOR_TO", "target": "renal_vein_left"},
            {"type": "ANTERIOR_TO", "target": "renal_pelvis_left"},
        ],
        learning_objectives=["RENAL_BLOOD_FLOW_AND_HILUM"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0001186",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:14753",
    ),
    AnatomyStructure(
        structure_id="renal_vein_left",
        display_name="Left Renal Vein",
        source_system="HRA",
        source_structure_id="UBERON:0001142",
        ontology_id="UBERON:0001142",
        mesh_node_names=["VH_M_renal_vein_L", "VH_M_left_renal_vein"],
        aliases=["left renal vein", "renal vein left", "vena renalis sinistra", "renal vein"],
        region="renal_vasculature",
        relationships=[
            {"type": "DRAINS", "target": "renal_cortex_left"},
            {"type": "EXITS_THROUGH", "target": "hilum_of_kidney_left"},
            {"type": "ANTERIOR_TO", "target": "renal_artery_left"},
            {"type": "ANTERIOR_TO", "target": "renal_pelvis_left"},
        ],
        learning_objectives=["RENAL_BLOOD_FLOW_AND_HILUM"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0001142",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:14336",
    ),
    AnatomyStructure(
        structure_id="kidney_capsule_left",
        display_name="Left Renal Fibrous Capsule",
        source_system="HRA",
        source_structure_id="UBERON:0002015",
        ontology_id="UBERON:0002015",
        mesh_node_names=["VH_M_kidney_capsule_L"],
        aliases=["fibrous capsule", "renal capsule", "capsule of kidney", "kidney capsule"],
        region="renal_envelope",
        relationships=[
            {"type": "SURROUNDS", "target": "renal_cortex_left"},
            {"type": "ADJACENT_TO", "target": "hilum_of_kidney_left"},
        ],
        learning_objectives=["RENAL_INTERNAL_ORGANIZATION"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0002015",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:15629",
    ),
    AnatomyStructure(
        structure_id="hilum_of_kidney_left",
        display_name="Hilum of Left Kidney",
        source_system="HRA",
        source_structure_id="UBERON:0008716",
        ontology_id="UBERON:0008716",
        mesh_node_names=["VH_M_hilum_of_kidney_L"],
        aliases=["renal hilum", "hilum", "hilus of kidney", "left renal hilum"],
        region="renal_hilum",
        relationships=[
            {"type": "ENTRY_EXIT_POINT_FOR", "target": "renal_artery_left"},
            {"type": "ENTRY_EXIT_POINT_FOR", "target": "renal_vein_left"},
            {"type": "ENTRY_EXIT_POINT_FOR", "target": "renal_pelvis_left"},
        ],
        learning_objectives=["RENAL_BLOOD_FLOW_AND_HILUM"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0008716",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:15632",
    ),
    AnatomyStructure(
        structure_id="renal_cortex_left",
        display_name="Left Renal Cortex",
        source_system="HRA",
        source_structure_id="UBERON:0001225",
        ontology_id="UBERON:0001225",
        mesh_node_names=[
            "VH_M_outer_cortex_of_kidney_L",
            "VH_M_renal_column_L",
            "VH_M_cortex_of_kidney_L",
        ],
        aliases=["kidney cortex", "cortex renalis", "renal cortex", "outer cortex"],
        region="renal_parenchyma",
        relationships=[
            {"type": "SURROUNDS", "target": "renal_medulla_left"},
            {"type": "INTERNAL_TO", "target": "kidney_capsule_left"},
        ],
        learning_objectives=["RENAL_INTERNAL_ORGANIZATION"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0001225",
            "http://purl.obolibrary.org/obo/UBERON_0002189",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:15637",
    ),
    AnatomyStructure(
        structure_id="renal_medulla_left",
        display_name="Left Renal Medulla",
        source_system="HRA",
        source_structure_id="UBERON:0000362",
        ontology_id="UBERON:0000362",
        mesh_node_names=[
            "VH_M_renal_medulla_L",
            "VH_M_renal_pyramid_L",
            "VH_M_renal_papilla_L",
            "VH_M_renal_pyramid_L_a",
            "VH_M_renal_papilla_L_a",
        ],
        aliases=["kidney medulla", "medulla renalis", "renal medulla", "medullary pyramids", "renal pyramids"],
        region="renal_parenchyma",
        relationships=[
            {"type": "INTERNAL_TO", "target": "renal_cortex_left"},
            {"type": "DRAINS_TO", "target": "renal_pelvis_left"},
        ],
        learning_objectives=["RENAL_INTERNAL_ORGANIZATION"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0000362",
            "http://purl.obolibrary.org/obo/UBERON_0004200",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:15640",
    ),
    AnatomyStructure(
        structure_id="renal_pelvis_left",
        display_name="Left Renal Pelvis",
        source_system="HRA",
        source_structure_id="UBERON:0001224",
        ontology_id="UBERON:0001224",
        mesh_node_names=["VH_M_renal_pelvis_L"],
        aliases=["left renal pelvis", "pelvis of kidney", "pelvis renalis", "renal pelvis"],
        region="renal_collecting_system",
        relationships=[
            {"type": "RECEIVES_URINE_FROM", "target": "renal_medulla_left"},
            {"type": "CONTINUOUS_WITH", "target": "ureter_left"},
            {"type": "EXITS_THROUGH", "target": "hilum_of_kidney_left"},
            {"type": "POSTERIOR_TO", "target": "renal_artery_left"},
            {"type": "POSTERIOR_TO", "target": "renal_vein_left"},
        ],
        learning_objectives=["RENAL_BLOOD_FLOW_AND_HILUM", "RENAL_INTERNAL_ORGANIZATION"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0001224",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:15643",
    ),
    AnatomyStructure(
        structure_id="ureter_left",
        display_name="Left Ureter",
        source_system="HRA",
        source_structure_id="UBERON:0001223",
        ontology_id="UBERON:0001223",
        mesh_node_names=["VH_M_ureter_L"],
        aliases=["left ureter", "ureter left", "ureter"],
        region="renal_collecting_system",
        relationships=[
            {"type": "CONTINUOUS_WITH", "target": "renal_pelvis_left"},
        ],
        learning_objectives=["RENAL_BLOOD_FLOW_AND_HILUM"],
        evidence_refs=[
            "http://purl.obolibrary.org/obo/UBERON_0001223",
            "http://purl.obolibrary.org/obo/UBERON_0000056",
            "https://hubmapconsortium.github.io/ccf-asct-reporter/",
        ],
        fma_crosswalk="FMA:15572",
    ),
)

_STRUCTURES_BY_ID = {s.structure_id: s for s in RENAL_STRUCTURES}
_ALIAS_TO_ID: dict[str, str] = {}
_MESH_NODE_TO_ID: dict[str, str] = {}

for s in RENAL_STRUCTURES:
    _ALIAS_TO_ID[s.structure_id.casefold()] = s.structure_id
    _ALIAS_TO_ID[s.display_name.casefold()] = s.structure_id
    for alias in s.aliases:
        _ALIAS_TO_ID[" ".join(alias.casefold().split())] = s.structure_id
    for node_name in s.mesh_node_names:
        _MESH_NODE_TO_ID[node_name] = s.structure_id


def get_renal_manifest() -> tuple[AnatomyStructure, ...]:
    """Return all verified renal anatomy structures."""
    return RENAL_STRUCTURES


def get_structure_by_id(structure_id: str) -> Optional[AnatomyStructure]:
    """Retrieve an anatomy structure by canonical ID."""
    if not structure_id:
        return None
    return _STRUCTURES_BY_ID.get(structure_id.strip().casefold())


def resolve_mesh_node(node_name: str) -> Optional[AnatomyStructure]:
    """Resolve a Three.js GLB scene mesh name to its canonical AnatomyStructure."""
    if not node_name:
        return None
    clean_name = node_name.strip()
    sid = _MESH_NODE_TO_ID.get(clean_name)
    if sid:
        return _STRUCTURES_BY_ID.get(sid)
    # Prefix matching for pyramid, papilla, column sub-instances
    if clean_name.startswith("VH_M_renal_pyramid_L") or clean_name.startswith("VH_M_renal_papilla_L"):
        return _STRUCTURES_BY_ID.get("renal_medulla_left")
    if clean_name.startswith("VH_M_outer_cortex_of_kidney_L") or clean_name.startswith("VH_M_renal_column_L"):
        return _STRUCTURES_BY_ID.get("renal_cortex_left")
    return None


def resolve_query_to_structure(query: str) -> Optional[AnatomyStructure]:
    """Fuzzy resolve student text or query string to canonical AnatomyStructure."""
    if not isinstance(query, str) or not query.strip():
        return None
    normalized = " ".join(query.casefold().split())
    sid = _ALIAS_TO_ID.get(normalized)
    if sid:
        return _STRUCTURES_BY_ID.get(sid)
    for alias, s_id in _ALIAS_TO_ID.items():
        if alias in normalized:
            return _STRUCTURES_BY_ID.get(s_id)
    return None


def valid_structure_ids() -> tuple[str, ...]:
    """Return tuple of all valid structure IDs in manifest."""
    return tuple(_STRUCTURES_BY_ID.keys())
