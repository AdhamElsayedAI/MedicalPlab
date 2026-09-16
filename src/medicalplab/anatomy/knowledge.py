"""Verified renal anatomy knowledge base for grounded tutoring.

All facts are paraphrased scientific anatomical facts referenced to open,
auditable sources (HuBMAP Human Reference Atlas, OBO Foundry UBERON, OpenStax A&P 2e).
Zero textbook quotations are included.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RenalKnowledgeFact:
    fact_id: str
    subject_id: str
    predicate: str
    object_id: str
    statement: str
    spatial_orientation: Optional[str]
    evidence_citation: str


RENAL_KNOWLEDGE_BASE: tuple[RenalKnowledgeFact, ...] = (
    RenalKnowledgeFact(
        fact_id="FACT_RENAL_ARTERY_SUPPLY",
        subject_id="renal_artery_left",
        predicate="SUPPLIES",
        object_id="renal_cortex_left",
        statement="The left renal artery branches from the abdominal aorta to provide oxygenated blood supply to the renal parenchyma.",
        spatial_orientation="Traverses the renal hilum intermediate between the anteriorly placed renal vein and the posteriorly located renal pelvis.",
        evidence_citation="HuBMAP HRA ASCT+B Kidney Table (CC BY 4.0); OBO Foundry UBERON:0001186; OpenStax Anatomy and Physiology 2e, Section 25.3 (CC BY 4.0).",
    ),
    RenalKnowledgeFact(
        fact_id="FACT_RENAL_VEIN_DRAINAGE",
        subject_id="renal_vein_left",
        predicate="DRAINS",
        object_id="renal_cortex_left",
        statement="The left renal vein conveys filtered, deoxygenated blood from the kidney across the midline anterior to the aorta to drain into the inferior vena cava.",
        spatial_orientation="Occupies the most anterior position of the three major hilum structures, conforming to the anterior-to-posterior rule: Vein, Artery, Pelvis (V-A-P).",
        evidence_citation="HuBMAP HRA ASCT+B Kidney Table (CC BY 4.0); OBO Foundry UBERON:0001142; OpenStax Anatomy and Physiology 2e, Section 25.3 (CC BY 4.0).",
    ),
    RenalKnowledgeFact(
        fact_id="FACT_HILUM_ORIENTATION_VAP",
        subject_id="hilum_of_kidney_left",
        predicate="TRANSMITS",
        object_id="renal_artery_left",
        statement="At the medial renal hilum, the major neurovascular and collecting structures are organized from anterior to posterior in the canonical sequence: Renal Vein, Renal Artery, and Renal Pelvis.",
        spatial_orientation="The clinical spatial orientation rule V-A-P identifies the vein anteriorly, artery centrally, and pelvis posteriorly.",
        evidence_citation="HuBMAP CCF 3D Reference Object Library v1.3; OBO Foundry UBERON:0008716; OpenStax Anatomy and Physiology 2e, Section 25.3 (CC BY 4.0).",
    ),
    RenalKnowledgeFact(
        fact_id="FACT_RENAL_PELVIS_CONTINUITY",
        subject_id="renal_pelvis_left",
        predicate="CONTINUOUS_WITH",
        object_id="ureter_left",
        statement="The renal pelvis represents the primary funnel-shaped urine convergence chamber at the hilum that tapers inferiorly to become continuous with the ureter.",
        spatial_orientation="Emerges from the most posterior aspect of the renal hilum and transitions into the left ureter descending toward the pelvis.",
        evidence_citation="HuBMAP HRA ASCT+B Kidney Table (CC BY 4.0); OBO Foundry UBERON:0001224; OBO Foundry UBERON:0001223.",
    ),
    RenalKnowledgeFact(
        fact_id="FACT_CORTEX_VS_MEDULLA",
        subject_id="renal_cortex_left",
        predicate="ENCLOSES",
        object_id="renal_medulla_left",
        statement="The outer renal cortex encloses the inner renal medulla, housing renal corpuscles and convoluted tubules while projecting renal columns between adjacent medullary pyramids.",
        spatial_orientation="The cortex forms the outer subcapsular perimeter, whereas the triangular medullary pyramids have their bases oriented towards the cortex and apices pointing medially.",
        evidence_citation="HuBMAP HRA ASCT+B Kidney Table (CC BY 4.0); OBO Foundry UBERON:0001225; OBO Foundry UBERON:0000362.",
    ),
    RenalKnowledgeFact(
        fact_id="FACT_CAPSULE_PROTECTION",
        subject_id="kidney_capsule_left",
        predicate="SURROUNDS",
        object_id="renal_cortex_left",
        statement="The fibrous renal capsule is a tough external collagenous membrane that intimately encases the renal cortex, shielding parenchymal tissues from mechanical trauma.",
        spatial_orientation="Forms the outermost anatomical boundary directly enveloping the cortical surface.",
        evidence_citation="HuBMAP CCF 3D Reference Object Library v1.3; OBO Foundry UBERON:0002015; OpenStax Anatomy and Physiology 2e, Section 25.3 (CC BY 4.0).",
    ),
)

_FACTS_BY_SUBJECT: dict[str, list[RenalKnowledgeFact]] = {}
for fact in RENAL_KNOWLEDGE_BASE:
    _FACTS_BY_SUBJECT.setdefault(fact.subject_id, []).append(fact)


def get_facts_for_structure(structure_id: str) -> list[RenalKnowledgeFact]:
    """Retrieve verified factual statements concerning a given structure."""
    return _FACTS_BY_SUBJECT.get(structure_id, [])


def get_all_facts() -> tuple[RenalKnowledgeFact, ...]:
    """Retrieve complete verified knowledge base."""
    return RENAL_KNOWLEDGE_BASE
