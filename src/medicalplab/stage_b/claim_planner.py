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


DOCUMENT_ID_PATTERN = re.compile(
    r"\bDOC-[A-Z0-9-]+\b",
    re.I,
)


def normalize_claim_text(claim: MaterialClaim) -> MaterialClaim:

    text = claim.text.strip()

    replacements = {
        "information about ": "Requested ",
        "details of ": "Requested ",
        "overview of ": "Requested ",
        "description of ": "Requested ",
    }


    lowered = text.lower()

    for old, new in replacements.items():

        if lowered.startswith(old):

            text = (
                new
                + text[len(old):]
            )

            break


    if text == claim.text:
        return claim


    return MaterialClaim(
        claim_id=claim.claim_id,
        text=text,
        origin=claim.origin,
        query_span=claim.query_span,
        source_document=claim.source_document,
        exact=claim.exact,
    )



def normalize_source_document(
    claim: MaterialClaim,
    query: str,
):

    """
    Source document is only allowed
    when explicitly requested by user.
    """

    if not claim.source_document:
        return claim


    if not DOCUMENT_ID_PATTERN.search(query):

        return MaterialClaim(
            claim_id=claim.claim_id,
            text=claim.text,
            origin=claim.origin,
            query_span=claim.query_span,
            source_document=None,
            exact=claim.exact,
        )


    return claim



def validate_claim_quality(claim: MaterialClaim):

    if claim.origin == ClaimOrigin.PERSONAL_CONTEXT:
        return


    text = normalize(
        claim.text
    ).strip()


    require(
        len(text.split()) >= 2,
        f"Claim too short: {claim.claim_id}",
    )


    require(
        not text.endswith("?"),
        f"Claim cannot be question: {claim.text}",
    )


    forbidden = [

        r"^the answer is ",

        r"^according to evidence ",

        r"^therefore ",

        r"^the patient has ",

        r"^treatment is ",

        r"^drug .* is recommended",

        r"^hypertension is ",

        r"^diabetes is ",

    ]


    lowered = text.lower()


    for pattern in forbidden:

        require(
            not re.search(
                pattern,
                lowered,
            ),
            f"Answer leakage detected: {claim.text}",
        )



def parse_plan(raw, query, documents):

    obj = strict_json(raw)


    exact_keys(
        obj,
        ["claims"],
    )


    require(
        isinstance(obj["claims"], list)
        and 1 <= len(obj["claims"]) <= 12,
        "Invalid claim count",
    )


    claims = []


    for index, data in enumerate(
        obj["claims"],
        1
    ):


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

            claim = MaterialClaim(
                **{
                    **data,
                    "origin": ClaimOrigin(
                        data["origin"]
                    ),
                }
            )


        except (
            ValueError,
            TypeError,
        ) as e:

            raise ValueError(
                f"Invalid claim: {e}"
            ) from e



        require(
            claim.claim_id == f"C{index}",
            "Claim IDs must be sequential",
        )


        require(
            normalize(claim.query_span)
            in normalize(query),
            "Query span not found in query",
        )


        claim = normalize_source_document(
            claim,
            query,
        )


        require(
            claim.source_document is None
            or claim.source_document in documents,
            "Unknown source document",
        )



        require(
            not (
                claim.origin == ClaimOrigin.SOURCE_PREMISE
                and OPEN_SLOT.search(
                    claim.query_span
                )
            ),
            "Question cannot be source premise",
        )



        claim = normalize_claim_text(
            claim
        )


        validate_claim_quality(
            claim
        )


        if claim.origin != ClaimOrigin.PERSONAL_CONTEXT:

            claims.append(
                claim
            )



    require(
        len(claims) > 0,
        "No valid claims generated",
    )


    return tuple(claims)