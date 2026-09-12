"""Archive the original freeze and version the already-existing AI repair checkpoint.

No clinical text is generated or approved. Every destination is create-only.
This one-time migration preserves the original batch, manifest and review queue.
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VERSION = "cardiorespiratory_batch_1_source_audit_v2"
ORIGINAL_COMMIT = "46adef39"
ORIGINAL_SHA = "7fbf3183de74df9490c9a2ce5f7b837099b536d76a2365e73abe0c0809104879"
REPAIR_SHA_LF = "b0ecc1ac63cf3f51eba44fbaa94301a3369e5e66bb891a1916c8f080423f1f8e"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def main():
    relative = "Data/questions/cardiorespiratory_batch_1.json"
    original = subprocess.check_output(["git", "show", f"{ORIGINAL_COMMIT}:{relative}"], cwd=ROOT)
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise RuntimeError("ORIGINAL_FREEZE_BYTES_MISMATCH")
    repair_bytes = (ROOT / relative).read_bytes()
    if hashlib.sha256(repair_bytes.replace(b"\r\n", b"\n")).hexdigest() != REPAIR_SHA_LF:
        raise RuntimeError("REPAIR_CHECKPOINT_CHANGED")
    batch = json.loads(repair_bytes)
    batch["batch_version"] = VERSION
    batch["lineage"] = {
        "original_batch_sha256": ORIGINAL_SHA,
        "repair_checkpoint_sha256_lf": REPAIR_SHA_LF,
        "repair_checkpoint_commit": "3f0faf89",
        "ai_review_status": "HISTORICAL_ENGINEERING_AUDIT_ONLY",
        "clinician_review_status": "PENDING",
        "golden_dataset_status": False,
    }
    batch_bytes = encoded(batch)
    manifest = {
        "batch_version": VERSION,
        "batch_file": f"Data/questions/versions/{VERSION}.json",
        "batch_file_sha256": hashlib.sha256(batch_bytes).hexdigest(),
        "total_questions": len(batch["questions"]),
        "question_ids": [q["question_id"] for q in batch["questions"]],
        "human_review_status": "PENDING", "golden_dataset_status": False,
        "source_status_counts": batch["repair_audit"]["status_counts"],
        "lineage": batch["lineage"],
        "historical_freeze_manifest": "Data/metadata/cardiorespiratory_batch_1_v1.manifest.json",
        "historical_frozen_batch": "Data/questions/versions/cardiorespiratory_batch_1_frozen_v1.json",
        "interpretation": "Versioned engineering checkpoint, not a clinician-approved or evidence-ready release.",
    }
    destinations = {
        ROOT / "Data/questions/versions/cardiorespiratory_batch_1_frozen_v1.json": original,
        ROOT / manifest["batch_file"]: batch_bytes,
        ROOT / f"Data/metadata/{VERSION}.manifest.json": encoded(manifest),
    }
    for path in destinations:
        if path.exists():
            raise FileExistsError(f"VERSION_ALREADY_EXISTS: {path}")
    for path, data in destinations.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
