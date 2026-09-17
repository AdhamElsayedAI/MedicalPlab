#!/usr/bin/env python3
"""Automated link and handoff integrity verifier for MedicalPlab.

Verifies that all internal links, anchors, and referenced documentation assets
in README.md and docs/ exist on disk with zero broken links.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
IMAGE_PATTERN = re.compile(r'<img\s+[^>]*src="([^"]+)"')


def check_file_links(file_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    text = file_path.read_text(encoding="utf-8", errors="ignore")

    # Check markdown links
    for match in LINK_PATTERN.finditer(text):
        target = match.group(2).strip()
        # Skip external web URLs, anchors, mailto, badges
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Strip anchor from target
        clean_target = target.split("#")[0].strip()
        if not clean_target:
            continue

        # Resolve path relative to current file or repo root
        rel_to_file = (file_path.parent / clean_target).resolve()
        rel_to_root = (repo_root / clean_target).resolve()

        if not rel_to_file.exists() and not rel_to_root.exists():
            errors.append(f"{file_path.relative_to(repo_root)}: broken link to '{target}'")

    # Check HTML image tags
    for match in IMAGE_PATTERN.finditer(text):
        src = match.group(1).strip()
        if src.startswith(("http://", "https://")):
            continue
        rel_to_file = (file_path.parent / src).resolve()
        rel_to_root = (repo_root / src).resolve()
        if not rel_to_file.exists() and not rel_to_root.exists():
            errors.append(f"{file_path.relative_to(repo_root)}: broken image src '{src}'")

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
    print("============================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
