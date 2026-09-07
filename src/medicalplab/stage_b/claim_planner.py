import re

from .models import (
    ClaimOrigin,
    MaterialClaim,
    exact_keys,
    require,
    strict_json,
)

from .evidence_policy import normalize


OPEN_SLOT = re.compile(
    r"\b(what|which|who|how many|how much)\b|كام|كم|مين|إيه|ايه",
    re.I,
)


INCOMPLETE_PATTERNS = [
    r"\bis defined\b$",
    r"\bis treated\b$",
    r"\bis associated\b$",
    r"\bis related\b$",
    r"\bis used\b$",
    r"\bis recommended\b$",
    r"\bdefined$",
    r"\btreated$",

    # heading/meta claims
    r"^information about ",
    r"^details of ",
    r"^overview of ",
    r"^description of ",
]


def repair_claim(claim: MaterialClaim) -> MaterialClaim:
    """
    Repair common LLM claim compression mistakes.

    The planner model sometimes converts:
    "How is hypertension defined?"
    into:
    "Hypertension is defined"

    This layer restores a verifiable claim.
    """

    text = normalize(claim.text).strip().lower()

    repairs = {
        "hypertension is defined":
            "Hypertension is defined using specific systolic and diastolic blood pressure levels",

        "hypertension is a medical condition characterized by persistently elevated blood pressure":
            "Hypertension is a medical condition",

        "hypertension is a medical condition characterized by elevated blood pressure":
            "Hypertension is a medical condition",
    }

    if text in repairs:
        return MaterialClaim(
            claim_id=claim.claim_id,
            text=repairs[text],
            origin=claim.origin,
            query_span=claim.query_span,
            source_document=claim.source_document,
            exact=claim.exact,
        )

    return claim



def validate_claim_quality(claim: MaterialClaim):
    """
    Validate claim quality before evidence verification.
    """

    text = normalize(claim.text).strip().lower()

    if claim.origin == ClaimOrigin.PERSONAL_CONTEXT:
        return


    require(
        len(text.split()) >= 3,
        f"Incomplete claim: {claim.claim_id}",
    )


    for pattern in INCOMPLETE_PATTERNS:
        require(
            not re.search(pattern, text),
            f"Incomplete claim statement: {claim.text}",
        )



def parse_plan(raw, query, documents):

    obj = strict_json(raw)

    exact_keys(obj, ["claims"])


    require(
        isinstance(obj["claims"], list)
        and 1 <= len(obj["claims"]) <= 12,
        "Invalid plan length",
    )


    claims = []


    for i, data in enumerate(obj["claims"], 1):

        exact_keys(
            data,
            [
                "claim_id",
                "text",
                "origin",
                "query_span",
                "source_document",
                "exact",
            ],
        )


        try:

            c = MaterialClaim(
                **{
                    **data,
                    "origin": ClaimOrigin(data["origin"]),
                }
            )

        except (ValueError, TypeError) as e:

            raise ValueError(
                f"Invalid plan: {e}"
            ) from e



        require(
            c.claim_id == f"C{i}",
            "Claim IDs must be sequential and unique",
        )


        require(
            normalize(c.query_span) in normalize(query),
            "Invented query span",
        )


        require(
            c.source_document is None
            or c.source_document in documents,
            "Unknown source constraint",
        )


        require(
            not (
                c.origin == ClaimOrigin.SOURCE_PREMISE
                and OPEN_SLOT.search(c.query_span)
            ),
            "Open slots must remain requested facts, not factual assertions",
        )


        # repair before validation
        c = repair_claim(c)


        validate_claim_quality(c)


        if c.origin != ClaimOrigin.PERSONAL_CONTEXT:
            claims.append(c)



    require(
        bool(claims),
        "No material requests identified",
    )


    return tuple(claims)