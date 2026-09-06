from .models import ClaimSupport, require


def aggregate(claims):
    require(bool(claims), "Cannot aggregate an empty plan")
    require(len({c.claim_id for c in claims}) == len(claims), "Duplicate claim IDs")
    supported = sum(c.status == ClaimSupport.SUPPORTED for c in claims)
    return (
        "supported"
        if supported == len(claims)
        else "partial"
        if supported
        else "unsupported"
    )
