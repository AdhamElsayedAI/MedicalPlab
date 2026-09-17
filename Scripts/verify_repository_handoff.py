#!/usr/bin/env python3
"""Automated link and handoff integrity verifier for MedicalPlab.

Verifies that all internal links, anchors, and referenced documentation assets
in README.md and docs/ exist on disk with zero broken links.

Anchor validation: Checks that #section-id references resolve to an actual
heading in the target markdown file (slug-matched: lowercase, spaces→hyphens,
punctuation stripped).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
IMAGE_PATTERN = re.compile(r'<img\s+[^>]*src="([^"]+)"')
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def _slug(heading: str) -> str:
    """Convert a markdown heading to a GitHub-compatible anchor slug."""
    heading = heading.strip()
    # Remove inline code backticks, bold/italic markers
    heading = re.sub(r"[`*_]", "", heading)
    # Lowercase
    heading = heading.lower()
    # Replace spaces and hyphens with single hyphen
    heading = re.sub(r"[\s]+", "-", heading)
    # Remove all non-alphanumeric, non-hyphen characters
    heading = re.sub(r"[^\w\-]", "", heading)
    # Collapse multiple hyphens
    heading = re.sub(r"-+", "-", heading)
    return heading.strip("-")


def _extract_anchors(file_path: Path) -> set[str]:
    """Extract all valid anchor slugs from headings in a markdown file."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()
    anchors: set[str] = set()
    slug_count: dict[str, int] = {}
    for match in HEADING_PATTERN.finditer(text):
        slug = _slug(match.group(1))
        count = slug_count.get(slug, 0)
        if count == 0:
            anchors.add(slug)
        else:
            # GitHub appends -N for duplicate headings
            anchors.add(f"{slug}-{count}")
        slug_count[slug] = count + 1
    return anchors


def check_file_links(file_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    text = file_path.read_text(encoding="utf-8", errors="ignore")

    # Check markdown links
    for match in LINK_PATTERN.finditer(text):
        target = match.group(2).strip()
        # Skip external web URLs, mailto, badges
        if target.startswith(("http://", "https://", "mailto:")):
            continue

        # Separate path and anchor
        if "#" in target:
            path_part, anchor_part = target.split("#", 1)
        else:
            path_part, anchor_part = target, None

        path_part = path_part.strip()

        # Pure anchor reference (same-file) — validate against current file
        if not path_part:
            if anchor_part:
                anchors = _extract_anchors(file_path)
                if anchor_part not in anchors:
                    errors.append(
                        f"{file_path.relative_to(repo_root)}: broken anchor '#{anchor_part}' (not found in same file)"
                    )
            continue

        # Resolve file path
        rel_to_file = (file_path.parent / path_part).resolve()
        rel_to_root = (repo_root / path_part).resolve()

        if rel_to_file.exists():
            resolved = rel_to_file
        elif rel_to_root.exists():
            resolved = rel_to_root
        else:
            errors.append(
                f"{file_path.relative_to(repo_root)}: broken link to '{target}'"
            )
            continue

        # Validate anchor in target file
        if anchor_part and resolved.suffix == ".md":
            anchors = _extract_anchors(resolved)
            if anchor_part not in anchors:
                errors.append(
                    f"{file_path.relative_to(repo_root)}: broken anchor '#{anchor_part}' "
                    f"in '{path_part}' (valid anchors: {sorted(anchors)[:8]}...)"
                )

    # Check HTML image tags
    for match in IMAGE_PATTERN.finditer(text):
        src = match.group(1).strip()
        if src.startswith(("http://", "https://")):
            continue
        rel_to_file = (file_path.parent / src).resolve()
        rel_to_root = (repo_root / src).resolve()
        if not rel_to_file.exists() and not rel_to_root.exists():
            errors.append(
                f"{file_path.relative_to(repo_root)}: broken image src '{src}'"
            )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    files_to_check: list[Path] = [repo_root / "README.md"]

    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        for root, _, files in os.walk(docs_dir):
            for f in files:
                if f.endswith(".md"):
                    files_to_check.append(Path(root) / f)

    total_errors: list[str] = []
    print("============================================================")
    print("      MEDICALPLAB HANDOFF & LINK INTEGRITY AUDIT")
    print("============================================================")
    print(f"Auditing {len(files_to_check)} markdown documentation files...")
    print("  (includes anchor resolution validation for internal #links)")

    for md_file in sorted(files_to_check):
        errs = check_file_links(md_file, repo_root)
        total_errors.extend(errs)

    if total_errors:
        print(f"FAILED: Found {len(total_errors)} broken internal links/images:", file=sys.stderr)
        for err in total_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("  RESULT: ZERO BROKEN INTERNAL LINKS (0 errors)")
    print("  BROKEN_INTERNAL_LINKS = 0")
    print("  ANCHOR_RESOLUTION = VERIFIED")
    print("============================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())

