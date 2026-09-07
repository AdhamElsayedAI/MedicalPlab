from .models import (
    Citation,
    ClaimSupport,
    ExactBinding,
    VerifierResult,
    exact_keys,
    require,
    strict_json,
    ContractError,
)


REQUIRED_FIELDS = [
    "claim_id",
    "text",
    "status",
    "citations",
    "bindings",
    "reason",
]


def parse_verification(raw, claims):

    obj = strict_json(raw)

    exact_keys(
        obj,
        ["claims"],
    )

    require(
        isinstance(obj["claims"], list),
        "Claims must be list",
    )

    require(
        len(obj["claims"]) == len(claims),
        "Claim count changed",
    )


    results = []


    for data, original_claim in zip(
        obj["claims"],
        claims,
    ):

        require(
            isinstance(data, dict),
            "Invalid verifier claim object",
        )


        exact_keys(
            data,
            REQUIRED_FIELDS,
        )


        require(
            data["claim_id"] == original_claim.claim_id,
            "Claim id modified",
        )


        require(
            data["text"] == original_claim.text,
            "Claim text modified",
        )


        require(
            isinstance(data["citations"], list),
            "Invalid citations",
        )


        require(
            isinstance(data["bindings"], list),
            "Invalid bindings",
        )


        try:

            citations = tuple(
                Citation(**item)
                for item in data["citations"]
            )


            bindings = tuple(
                ExactBinding(**item)
                for item in data["bindings"]
            )


            status = ClaimSupport(
                data["status"]
            )


        except (
            TypeError,
            ValueError,
        ) as e:

            raise ContractError(
                str(e)
            ) from e



        if (
            status == ClaimSupport.SUPPORTED
            and not citations
        ):
            raise ContractError(
                "Supported claim requires citation"
            )


        result = VerifierResult(
            claim_id=data["claim_id"],
            text=data["text"],
            status=status,
            citations=citations,
            bindings=bindings,
            reason=data["reason"],
        )


        results.append(result)


    return tuple(results)