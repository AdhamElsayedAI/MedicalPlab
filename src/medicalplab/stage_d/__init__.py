"""Stage-D: Medical Tutor Reasoning Layer.
"""

from .models import (
    ConfidenceLevel,
    EvidenceBlock,
    TutorCitation,
    TutorMode,
    TutorRequest,
    TutorResponse,
    TutorSection,
)
from .intent import (
    classify_intent,
    rule_based_intent,
)
from .tutor import parse_tutor_response
from .validator import (
    is_valid_tutor_response,
    validate_citation_provenance,
    validate_clinical_safety,
    validate_semantic_grounding,
    validate_tutor_response,
)
from .pipeline import (
    ModelFailure,
    StageDPipeline,
)

__all__ = [
    "ConfidenceLevel",
    "EvidenceBlock",
    "TutorCitation",
    "TutorMode",
    "TutorRequest",
    "TutorResponse",
    "TutorSection",
    "classify_intent",
    "rule_based_intent",
    "parse_tutor_response",
    "is_valid_tutor_response",
    "validate_citation_provenance",
    "validate_clinical_safety",
    "validate_semantic_grounding",
    "validate_tutor_response",
    "ModelFailure",
    "StageDPipeline",
]
