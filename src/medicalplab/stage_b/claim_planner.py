import re
from .models import ClaimOrigin, MaterialClaim, exact_keys, require, strict_json
from .evidence_policy import normalize

OPEN_SLOT = re.compile(
    r"\b(what|which|who|how many|how much)\b|كام|كم|مين|إيه|ايه", re.I
)


def parse_plan(raw, query, documents):
    obj = strict_json(raw)
    exact_keys(obj, ["claims"])
    require(
        isinstance(obj["claims"], list) and 1 <= len(obj["claims"]) <= 12,
        "Invalid plan length",
    )
    claims = []
    for i, data in enumerate(obj["claims"], 1):
        exact_keys(
            data,
            ["claim_id", "text", "origin", "query_span", "source_document", "exact"],
        )
        try:
            c = MaterialClaim(**{**data, "origin": ClaimOrigin(data["origin"])})
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid plan: {e}") from e
        require(c.claim_id == f"C{i}", "Claim IDs must be sequential and unique")
        require(normalize(c.query_span) in normalize(query), "Invented query span")
        require(
            c.source_document is None or c.source_document in documents,
            "Unknown source constraint",
        )
        require(
            not (
                c.origin == ClaimOrigin.SOURCE_PREMISE
                and OPEN_SLOT.search(c.query_span)
            ),
            "Open slots must remain requested facts, not factual assertions",
        )
        if c.origin != ClaimOrigin.PERSONAL_CONTEXT:
            claims.append(c)
    require(bool(claims), "No material requests identified")
    return tuple(claims)
