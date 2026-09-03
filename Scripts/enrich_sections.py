import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON object."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    """Save JSON using UTF-8."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def normalize_folder_name(value: str) -> str:
    """Normalize specialty folder name."""
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def sha256_text(text: str) -> str:
    """Create SHA-256 fingerprint for text."""
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def build_block_content(
    section: dict[str, Any],
) -> str:
    """
    Create a stable representation of heading + body text.

    This is used only for integrity verification.
    """
    heading = str(
        section.get(
            "heading",
            "",
        )
    ).strip()

    text = str(
        section.get(
            "text",
            "",
        )
    ).strip()

    parts = []

    if heading:
        parts.append(heading)

    if text:
        parts.append(text)

    return "\n".join(parts)


def heading_without_number(
    heading: str,
    section_number: str | None,
) -> str:
    """Remove the section number from a heading."""
    if not section_number:
        return heading.strip()

    prefix = f"{section_number} "

    if heading.startswith(prefix):
        return heading[
            len(prefix):
        ].strip()

    return heading.strip()


def enrich_sections(
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Add hierarchy metadata without changing source content.

    Numbered sections:
        - inherit the nearest higher-level numbered section
        - then become the active section for following blocks

    Semantic blocks:
        - inherit the deepest currently active numbered section
    """
    enriched: list[dict[str, Any]] = []

    hierarchy: dict[
        int,
        dict[str, Any],
    ] = {}

    for section in sections:
        item = dict(section)

        original_content = build_block_content(
            section
        )

        original_hash = sha256_text(
            original_content
        )

        block_type = item.get(
            "block_type"
        )

        parent_section = None

        if block_type == "numbered_section":
            level = item.get(
                "section_level",
                0,
            )

            section_number = item.get(
                "section_number"
            )

            heading = str(
                item.get(
                    "heading",
                    "",
                )
            )

            if not isinstance(level, int):
                raise ValueError(
                    f"Invalid section level in block "
                    f"{item.get('block_index')}"
                )

            if level <= 0:
                raise ValueError(
                    f"Numbered section has invalid level "
                    f"in block {item.get('block_index')}"
                )

            # Remove the previous section at this level
            # and every deeper level.
            for existing_level in list(
                hierarchy.keys()
            ):
                if existing_level >= level:
                    hierarchy.pop(
                        existing_level
                    )

            # Parent must be an already-active higher level,
            # never the current section itself.
            higher_levels = [
                existing_level
                for existing_level
                in hierarchy.keys()
                if existing_level < level
            ]

            if higher_levels:
                nearest_parent_level = max(
                    higher_levels
                )

                parent_section = hierarchy[
                    nearest_parent_level
                ]

            # Current numbered section becomes active
            # only after its parent has been resolved.
            hierarchy[level] = {
                "section_number": (
                    section_number
                ),
                "heading": heading,
            }

        else:
            # Semantic block belongs to the deepest
            # currently active numbered section.
            if hierarchy:
                deepest_level = max(
                    hierarchy.keys()
                )

                parent_section = hierarchy[
                    deepest_level
                ]

        section_path = [
            hierarchy[level]["heading"]
            for level in sorted(
                hierarchy.keys()
            )
        ]

        item[
            "parent_section_number"
        ] = (
            parent_section[
                "section_number"
            ]
            if parent_section
            else None
        )

        item[
            "parent_section_heading"
        ] = (
            heading_without_number(
                parent_section[
                    "heading"
                ],
                parent_section[
                    "section_number"
                ],
            )
            if parent_section
            else None
        )

        item[
            "section_path"
        ] = section_path

        item[
            "content_sha256"
        ] = original_hash

        enriched.append(
            item
        )

    return enriched

def validate_enrichment(
    original: list[dict[str, Any]],
    enriched: list[dict[str, Any]],
) -> list[str]:
    """
    Ensure hierarchy enrichment changed metadata only,
    never source content.
    """
    errors: list[str] = []

    if len(original) != len(enriched):
        errors.append(
            "Block count changed during enrichment."
        )

        return errors

    for old, new in zip(
        original,
        enriched,
    ):
        old_index = old.get(
            "block_index"
        )

        new_index = new.get(
            "block_index"
        )

        if old_index != new_index:
            errors.append(
                f"Block index changed: "
                f"{old_index} -> {new_index}"
            )

        old_content = build_block_content(
            old
        )

        new_content = build_block_content(
            new
        )

        if old_content != new_content:
            errors.append(
                f"Content changed in block "
                f"{old_index}."
            )

        expected_hash = sha256_text(
            old_content
        )

        actual_hash = new.get(
            "content_sha256"
        )

        if expected_hash != actual_hash:
            errors.append(
                f"Content hash mismatch "
                f"in block {old_index}."
            )

    return errors


def build_report(
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build hierarchy metadata statistics."""
    semantic_blocks = [
        section
        for section in sections
        if section.get(
            "block_type"
        )
        != "numbered_section"
    ]

    missing_parent = [
        section.get(
            "block_index"
        )
        for section in semantic_blocks
        if not section.get(
            "parent_section_number"
        )
    ]

    path_lengths = [
        len(
            section.get(
                "section_path",
                [],
            )
        )
        for section in sections
    ]

    return {
        "total_blocks": len(
            sections
        ),
        "semantic_blocks": len(
            semantic_blocks
        ),
        "semantic_blocks_without_parent": (
            missing_parent
        ),
        "semantic_blocks_without_parent_count": (
            len(missing_parent)
        ),
        "maximum_hierarchy_depth": (
            max(path_lengths)
            if path_lengths
            else 0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Add hierarchy metadata to parsed "
            "MedicalPlab sections."
        )
    )

    parser.add_argument(
        "document_id",
    )

    parser.add_argument(
        "--specialty",
        default="Cardiology",
    )

    args = parser.parse_args()

    specialty = normalize_folder_name(
        args.specialty
    )

    input_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.sections.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Sections file not found: "
            f"{input_path}"
        )

    document = load_json(
        input_path
    )

    sections = document.get(
        "sections",
        [],
    )

    if not isinstance(
        sections,
        list,
    ):
        raise ValueError(
            "Document sections must be a list."
        )

    enriched_sections = enrich_sections(
        sections
    )

    errors = validate_enrichment(
        sections,
        enriched_sections,
    )

    report = build_report(
        enriched_sections
    )

    passed = (
        not errors
        and report[
            "semantic_blocks_without_parent_count"
        ]
        == 0
    )

    output = {
        **{
            key: value
            for key, value
            in document.items()
            if key != "sections"
        },
        "enrichment": {
            "pipeline_version": "v1",
            "strategy": (
                "section_hierarchy_metadata"
            ),
            "enriched_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
        "sections": enriched_sections,
    }

    output_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".sections.enriched.json"
        )
    )

    report_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".sections.enrichment.json"
        )
    )

    report_output = {
        "document_id": (
            args.document_id
        ),
        "status": (
            "pass"
            if passed
            else "needs_review"
        ),
        **report,
        "validation_errors": errors,
    }

    save_json(
        output_path,
        output,
    )

    save_json(
        report_path,
        report_output,
    )

    print(
        "\nMedicalPlab Section Hierarchy Enrichment"
    )
    print("=" * 48)

    print(
        f"Document                    : "
        f"{args.document_id}"
    )

    print(
        f"Total blocks                : "
        f"{report['total_blocks']}"
    )

    print(
        f"Semantic blocks             : "
        f"{report['semantic_blocks']}"
    )

    print(
        f"Semantic blocks no parent   : "
        f"{report['semantic_blocks_without_parent_count']}"
    )

    print(
        f"Maximum hierarchy depth     : "
        f"{report['maximum_hierarchy_depth']}"
    )

    print(
        f"Content integrity           : "
        f"{'PASS ✅' if not errors else 'FAIL ❌'}"
    )

    print(
        f"Hierarchy validation        : "
        f"{'PASS ✅' if passed else 'NEEDS REVIEW ❌'}"
    )

    print(
        "\nRecommendation/Evidence Samples"
    )
    print("-" * 100)

    sample_count = 0

    for section in enriched_sections:
        if section.get(
            "block_type"
        ) not in {
            "recommendation",
            "evidence_rationale",
            "evidence_to_decision",
        }:
            continue

        print(
            f"#{section['block_index']:>2} "
            f"[{section['block_type']}]"
        )

        print(
            f"    Parent : "
            f"{section.get('parent_section_number')} "
            f"{section.get('parent_section_heading')}"
        )

        print(
            "    Path   : "
            + " > ".join(
                section.get(
                    "section_path",
                    [],
                )
            )
        )

        sample_count += 1

        if sample_count >= 10:
            break

    print(
        f"\nOutput                      : "
        f"{output_path}"
    )

    print(
        f"Report                      : "
        f"{report_path}"
    )


if __name__ == "__main__":
    main()