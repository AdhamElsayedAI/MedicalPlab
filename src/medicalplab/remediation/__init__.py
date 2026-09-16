"""MedicalPlab Phase 2B Intelligent Socratic Remediation Engine."""
from medicalplab.remediation.models import (
    DetectedLearningGap,
    ReasoningPatternCategory,
    ReasoningTimelineItem,
    RemediationSessionState,
    RemediationStatus,
    RemediationTurnResponse,
    SocraticStrategyType,
    StartRemediationRequest,
    TurnRemediationRequest,
    CANONICAL_SAFETY_FALLBACK_MESSAGE,
)
from medicalplab.remediation.taxonomy import (
    ReasoningPatternTaxonomyRegistry,
    get_taxonomy_registry,
)
from medicalplab.remediation.detector import ReasoningPatternDetectionEngine
from medicalplab.remediation.strategy import SocraticStrategyEngine
from medicalplab.remediation.controller import RemediationLoopController
from medicalplab.remediation.bridge import RemediationTutorBridge
from medicalplab.remediation.api import router as remediation_router

__all__ = [
    "DetectedLearningGap",
    "ReasoningPatternCategory",
    "ReasoningPatternTaxonomyRegistry",
    "ReasoningPatternDetectionEngine",
    "ReasoningTimelineItem",
    "RemediationSessionState",
    "RemediationStatus",
    "RemediationTurnResponse",
    "RemediationLoopController",
    "RemediationTutorBridge",
    "SocraticStrategyType",
    "SocraticStrategyEngine",
    "StartRemediationRequest",
    "TurnRemediationRequest",
    "CANONICAL_SAFETY_FALLBACK_MESSAGE",
    "get_taxonomy_registry",
    "remediation_router",
]
