"""Strict immutable runtime contracts.
Gold data has no runtime representation.
"""

from dataclasses import dataclass, fields
from enum import Enum
import json


class ContractError(ValueError):
    pass



class ClaimOrigin(str, Enum):
    SOURCE_PREMISE = "source_premise"
    REQUESTED_FACT = "requested_fact"
    PERSONAL_CONTEXT = "personal_context"



class ClaimSupport(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"



def require(condition, message):
    if not condition:
        raise ContractError(message)



def strings(*values):
    require(
        all(
            isinstance(v, str)
            and v.strip()
            for v in values
        ),
        "Expected nonempty strings",
    )



def strict_json(text):

    def pairs(items):
        result = {}

        for k, v in items:

            require(
                k not in result,
                f"Duplicate JSON key: {k}",
            )

            result[k] = v

        return result


    require(
        isinstance(text, str),
        "JSON input must be string",
    )


    text = text.strip()


    if "```" in text:

        text = (
            text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )


    start = text.find("{")
    end = text.rfind("}")


    require(
        start != -1 and end != -1,
        "No JSON object found",
    )


    text = text[start:end + 1]


    try:

        return json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda s:
                require(
                    False,
                    f"Invalid JSON constant: {s}",
                ),
        )


    except json.JSONDecodeError as e:

        raise ContractError(
            f"Invalid JSON: {e}"
        ) from e



def exact_keys(value, keys):

    require(
        isinstance(value, dict)
        and set(value) == set(keys),
        f"Expected fields: {keys}",
    )



@dataclass(frozen=True)
class EvidenceBlock:

    ref: str
    document_id: str
    source: str
    heading: str
    section: str
    text: str
    block_type: str = "text"


    def __post_init__(self):

        strings(
            self.ref,
            self.document_id,
            self.source,
            self.text,
        )


        require(
            self.ref.startswith(
                self.document_id + ":B"
            ),
            "Reference/document mismatch",
        )



@dataclass(frozen=True)
class MaterialClaim:

    claim_id: str
    text: str
    origin: ClaimOrigin
    query_span: str
    source_document: str | None
    exact: bool


    def __post_init__(self):

        strings(
            self.claim_id,
            self.text,
            self.query_span,
        )


        require(
            isinstance(
                self.origin,
                ClaimOrigin,
            ),
            "Invalid claim origin",
        )


        require(
            type(self.exact) is bool,
            "exact must be boolean",
        )


        require(
            self.source_document is None
            or isinstance(
                self.source_document,
                str,
            ),
            "Invalid source constraint",
        )



@dataclass(frozen=True)
class Citation:

    ref: str
    quote: str


    def __post_init__(self):

        strings(
            self.ref,
            self.quote,
        )



@dataclass(frozen=True)
class ExactBinding:

    """Literal spans from ONE cited context."""

    ref: str
    context: str
    entity: str
    relation: str
    quantity: str
    unit: str
    role: str


    def __post_init__(self):

        strings(
            *(
                getattr(self, f.name)
                for f in fields(self)
            )
        )


        require(
            self.role
            in {
                "interval",
                "visit_count",
                "duration",
                "threshold",
                "dose",
                "equivalence",
                "percentage",
                "score",
                "count",
                "other",
            },
            "Invalid quantitative role",
        )



@dataclass(frozen=True)
class VerifierResult:

    claim_id: str
    text: str
    status: ClaimSupport
    citations: tuple[Citation, ...]
    bindings: tuple[ExactBinding, ...]
    reason: str


    def __post_init__(self):

        strings(
            self.claim_id,
            self.text,
            self.reason,
        )


        require(
            isinstance(
                self.status,
                ClaimSupport,
            ),
            "Invalid claim support",
        )


        require(
            isinstance(
                self.citations,
                tuple,
            )
            and all(
                isinstance(c, Citation)
                for c in self.citations
            ),
            "Invalid citations",
        )


        require(
            isinstance(
                self.bindings,
                tuple,
            )
            and all(
                isinstance(
                    b,
                    ExactBinding,
                )
                for b in self.bindings
            ),
            "Invalid bindings",
        )


        require(
            self.status != ClaimSupport.SUPPORTED
            or len(self.citations) > 0,
            "Supported claim requires evidence",
        )



@dataclass(frozen=True)
class ModelRunMetadata:

    model: str
    revision: str
    quantization: str
    input_tokens: int
    output_tokens: int
    planner_seconds: float
    verifier_seconds: float
    total_seconds: float
    peak_vram_bytes: int | None


    def __post_init__(self):

        strings(
            self.model,
            self.revision,
            self.quantization,
        )


        require(
            self.input_tokens >= 0,
            "Invalid input token count",
        )

        require(
            self.output_tokens >= 0,
            "Invalid output token count",
        )

        require(
            self.total_seconds >= 0,
            "Invalid runtime",
        )



@dataclass(frozen=True)
class StageBResult:

    claims: tuple[VerifierResult, ...]
    policy_downgrades: tuple[str, ...]
    metadata: ModelRunMetadata


    @property
    def verdict(self):

        from .aggregator import aggregate

        return aggregate(self.claims)
    