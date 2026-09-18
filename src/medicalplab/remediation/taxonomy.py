"""Taxonomy registry for Reasoning Pattern and Learning Gap Detection.

Loads and manages the declarative taxonomy of cognitive reasoning patterns,
pedagogical categories, Socratic strategies, and evidence references.

CRITICAL INVARIANT:
Zero medical truth storage in taxonomy. No medical facts, claims, or physiological
truths are stored here. All factual knowledge is dynamically retrieved from the
frozen Evidence Engine using the referenced document/chunk IDs.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from medicalplab.remediation.models import (
    DistractorMapping,
    ReasoningPatternCategory,
    ReasoningPatternTaxonomyItem,
    SocraticStrategyType,
)

logger = logging.getLogger(__name__)

DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "Data"
    / "taxonomy"
    / "reasoning_patterns.v1.json"
)
FALLBACK_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "tests"
    / "plab"
    / "fixtures"
    / "reasoning_patterns.v1.json"
)


class TaxonomyValidationError(Exception):
    """Raised when taxonomy violates safety or structural constraints."""
    pass


class ReasoningPatternTaxonomyRegistry:
    """In-memory registry for reasoning patterns and question distractor mappings."""

    def __init__(self, taxonomy_path: Path | str | None = None) -> None:
        if taxonomy_path:
            self.path = Path(taxonomy_path)
        else:
            data_root = os.environ.get("MEDICALPLAB_DATA_ROOT")
            if data_root and (Path(data_root) / "taxonomy" / "reasoning_patterns.v1.json").exists():
                self.path = Path(data_root) / "taxonomy" / "reasoning_patterns.v1.json"
            elif DEFAULT_TAXONOMY_PATH.exists():
                self.path = DEFAULT_TAXONOMY_PATH
            elif FALLBACK_FIXTURE_PATH.exists():
                self.path = FALLBACK_FIXTURE_PATH
            else:
                self.path = DEFAULT_TAXONOMY_PATH
        self._patterns: Dict[str, ReasoningPatternTaxonomyItem] = {}
        self._mappings: Dict[Tuple[str, str], DistractorMapping] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            logger.warning("Taxonomy file not found at %s; registry starting empty", self.path)
            return

        try:
            raw_text = self.path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except Exception as exc:
            raise TaxonomyValidationError(f"Failed to read taxonomy file at {self.path}: {exc}") from exc

        # Parse and validate patterns
        for item in data.get("patterns", []):
            try:
                pattern = ReasoningPatternTaxonomyItem(
                    pattern_id=item["pattern_id"],
                    topic=item["topic"],
                    category=ReasoningPatternCategory(item["category"]),
                    reasoning_pattern=item["reasoning_pattern"],
                    recommended_strategy=SocraticStrategyType(item["recommended_strategy"]),
                    evidence_references=item.get("evidence_references", []),
                )
                self._patterns[pattern.pattern_id] = pattern
            except Exception as exc:
                raise TaxonomyValidationError(f"Invalid pattern definition {item}: {exc}") from exc

        # Parse and validate distractor mappings
        for m in data.get("distractor_mappings", []):
            try:
                mapping = DistractorMapping(
                    question_id=m["question_id"],
                    distractor_option=m["distractor_option"],
                    pattern_id=m["pattern_id"],
                    confidence_weight=float(m.get("confidence_weight", 0.85)),
                    detection_rationale=m.get("detection_rationale", m.get("diagnostic_rationale", "")),
                )
                if mapping.pattern_id not in self._patterns:
                    logger.warning(
                        "Mapping for %s option %s references unknown pattern %s",
                        mapping.question_id,
                        mapping.distractor_option,
                        mapping.pattern_id,
                    )
                self._mappings[(mapping.question_id, mapping.distractor_option)] = mapping
            except Exception as exc:
                raise TaxonomyValidationError(f"Invalid distractor mapping {m}: {exc}") from exc

        logger.info(
            "Loaded ReasoningPatternTaxonomyRegistry: %d patterns, %d distractor mappings from %s",
            len(self._patterns),
            len(self._mappings),
            self.path,
        )

    def get_pattern(self, pattern_id: str) -> Optional[ReasoningPatternTaxonomyItem]:
        """Retrieve pattern by ID."""
        return self._patterns.get(pattern_id)

    def get_mapping(self, question_id: str, distractor_option: str) -> Optional[DistractorMapping]:
        """Retrieve distractor mapping for (question_id, option)."""
        return self._mappings.get((question_id, distractor_option))

    def get_patterns_for_topic(self, topic: str) -> List[ReasoningPatternTaxonomyItem]:
        """Retrieve all patterns associated with a topic."""
        return [p for p in self._patterns.values() if p.topic.lower() == topic.lower()]

    def all_patterns(self) -> List[ReasoningPatternTaxonomyItem]:
        """List all registered reasoning patterns."""
        return list(self._patterns.values())

    def all_mappings(self) -> List[DistractorMapping]:
        """List all registered distractor mappings."""
        return list(self._mappings.values())


_global_registry: Optional[ReasoningPatternTaxonomyRegistry] = None


def get_taxonomy_registry(reload_if_empty: bool = True) -> ReasoningPatternTaxonomyRegistry:
    """Singleton provider for the taxonomy registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ReasoningPatternTaxonomyRegistry()
    elif reload_if_empty and (not _global_registry.all_patterns() or not _global_registry.all_mappings()):
        _global_registry = ReasoningPatternTaxonomyRegistry()
    return _global_registry
