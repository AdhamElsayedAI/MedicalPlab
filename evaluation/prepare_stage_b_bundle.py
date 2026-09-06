"""Build an explicit allowlist bundle. No credentials, caches or old experiments."""

import argparse
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from stage_b_inputs import FROZEN, digest, load_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _, _, corpus = load_inputs(ROOT)
    paths = [
        ROOT / p
        for p in [
            *FROZEN,
            *corpus,
            "requirements-benchmark.txt",
            "notebooks/stage_b_colab.ipynb",
            "docs/stage_b.md",
        ]
    ]
    paths += sorted((ROOT / "src/medicalplab").rglob("*.py"))
    paths += sorted((ROOT / "evaluation").glob("*stage_b*.py"))
    paths += sorted((ROOT / "tests").rglob("*.py"))
    paths += sorted((ROOT / "tests/stage_b/fixtures").glob("*.json"))
    manifest = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("stage_b_bundle_manifest.json", json.dumps(manifest, indent=2))
    print(f"Created {args.output}; {len(paths)} allowlisted files")


if __name__ == "__main__":
    main()
