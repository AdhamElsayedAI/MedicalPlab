from __future__ import annotations


def local_validate(
    output: dict[str, Any],
    schema_validator: Draft202012Validator,
    allowed_refs: set[str],
) -> list[str]:
    errors: list[str] = []
    for error in sorted(
        schema_validator.iter_errors(output), key=lambda item: list(item.absolute_path)
    ):
        location = "$"
        for part in error.absolute_path:
            if isinstance(part, int):
                location += f"[{part}]"
            else:
                location += f".{part}"
        errors.append(f"schema:{location}: {error.message}")
    claims = output.get("claims", [])
    if isinstance(claims, list):
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            refs = claim.get("evidence_refs", [])
            if not isinstance(refs, list):
                continue
            for ref in refs:
                if isinstance(ref, str) and ref not in allowed_refs:
                    errors.append(f"evidence_ref_not_in_packet:{ref}")
    return errors
