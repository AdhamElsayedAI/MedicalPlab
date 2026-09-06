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


def parse_verification(raw, claims):
    obj = strict_json(raw)
    exact_keys(obj, ["claims"])
    require(
        isinstance(obj["claims"], list) and len(obj["claims"]) == len(claims),
        "Claim count changed",
    )
    result = []
    for data, claim in zip(obj["claims"], claims):
        exact_keys(
            data, ["claim_id", "text", "status", "citations", "bindings", "reason"]
        )
        require(
            isinstance(data["citations"], list) and isinstance(data["bindings"], list),
            "Invalid evidence lists",
        )
        try:
            citations = tuple(Citation(**c) for c in data["citations"])
            bindings = tuple(ExactBinding(**b) for b in data["bindings"])
            row = VerifierResult(
                data["claim_id"],
                data["text"],
                ClaimSupport(data["status"]),
                citations,
                bindings,
                data["reason"],
            )
        except (TypeError, ValueError) as e:
            raise ContractError(str(e)) from e
        require(
            row.claim_id == claim.claim_id and row.text == claim.text,
            "Fixed claims modified",
        )
        result.append(row)
    return tuple(result)
