"""One runner for full calibration and explicitly labeled model regression."""

from dataclasses import asdict
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from medicalplab.stage_b.backend import GENERATION, MODEL, QwenBackend, preflight
from medicalplab.stage_b.pipeline import StageBPipeline
from medicalplab.stage_b.models import ContractError
from stage_b_inputs import FROZEN, digest, load_inputs
from stage_b_metrics import metrics

REGRESSION = {
    f"ESCAL-V1-{i:03d}" for i in [2, 11, 12, 26, 27, 29, 32, 35, 41, 42, 43, 48]
}


def atomic(path, obj):
    if "rows" in obj:
        obj["rows_sha256"] = hashlib.sha256(
            json.dumps(obj["rows"], sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as f:
            tmp = Path(f.name)
            json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def fingerprint(root, corpus, revision, mode):
    paths = sorted((root / "src/medicalplab/stage_b").glob("*.py")) + sorted(
        (root / "evaluation").glob("*stage_b*.py")
    )
    return {
        "frozen": FROZEN,
        "corpus": corpus,
        "code": {p.relative_to(root).as_posix(): digest(p) for p in paths},
        "model": MODEL,
        "revision": revision,
        "generation": GENERATION,
        "mode": mode,
    }


def validate_resume(saved, signature, cases):
    if saved["signature"] != signature:
        raise ValueError("Resume fingerprint mismatch")
    if saved.get("complete"):
        raise ValueError("Output already complete; refusing overwrite")
    expected_hash = hashlib.sha256(
        json.dumps(saved["rows"], sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    if saved.get("rows_sha256") != expected_hash:
        raise ValueError("Checkpoint row integrity mismatch")
    expected = [c["case_id"] for c in cases]
    actual = [r["case_id"] for r in saved["rows"]]
    if actual != expected[: len(actual)]:
        raise ValueError("Checkpoint is not a unique ordered prefix")
    for r, c in zip(saved["rows"], cases):
        if r["gold_label"] != c["support_label"] or r["status"] not in {
            "ok",
            "model_failure",
            "contract_failure",
        }:
            raise ValueError("Invalid checkpoint row")
        if r["status"] == "ok" and r["prediction"] not in {
            "supported",
            "partial",
            "unsupported",
        }:
            raise ValueError("Invalid checkpoint prediction")


def execute(cases, packets, backend, path, saved):
    pipeline = StageBPipeline(backend)
    for case in cases[len(saved["rows"]) :]:
        start = time.perf_counter()
        row = {
            k: case.get(k)
            for k in [
                "case_id",
                "language",
                "claim_type",
                "negative_type",
                "contrast_group_id",
            ]
        }
        row.update(
            gold_label=case["support_label"],
            prediction=None,
            retrieval_input={
                "query": case["query"],
                "evidence": [asdict(b) for b in packets[case["case_id"]]],
            },
        )
        try:
            result = pipeline.run(case["query"], packets[case["case_id"]])
            row.update(status="ok", prediction=result.verdict, result=asdict(result))
        except (ContractError, ValueError, TypeError, KeyError) as e:
            row.update(
                status="contract_failure", error_type=type(e).__name__, error=str(e)
            )
        except Exception as e:
            row.update(
                status="model_failure", error_type=type(e).__name__, error=str(e)
            )
        row["trace"] = pipeline.trace.copy()
        row["latency_seconds"] = time.perf_counter() - start
        saved["rows"].append(row)
        saved["metrics"] = metrics(saved["rows"])
        atomic(path, saved)
        print(f"{row['case_id']}: {row['status']} {row['prediction']}", flush=True)
    saved.update(complete=True, metrics=metrics(saved["rows"]))
    atomic(path, saved)
    return saved


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    p.add_argument("--revision", help="Immutable 40-character Hugging Face commit SHA")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--regression", action="store_true")
    p.add_argument("--audit-inputs", action="store_true")
    p.add_argument("--preflight", action="store_true")
    args = p.parse_args()
    cases, packets, corpus = load_inputs(ROOT)
    if args.audit_inputs:
        print(
            json.dumps(
                {
                    "frozen_verified": FROZEN,
                    "corpus": corpus,
                    "cases": len(cases),
                    "top_k": 10,
                },
                indent=2,
            )
        )
        return
    if args.preflight:
        print(json.dumps(preflight(), indent=2))
        return
    if not args.output or not args.revision:
        p.error("--output and --revision are required")
    if args.regression:
        cases = [c for c in cases if c["case_id"] in REGRESSION]
    mode = (
        "calibration_regression_debug"
        if args.regression
        else "calibration_not_held_out"
    )
    signature = fingerprint(ROOT, corpus, args.revision, mode)
    path = args.output.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive run lock prevents competing writers; a crash leaves a visible lock.
    lock = path.with_suffix(path.suffix + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    try:
        if path.exists():
            if not args.resume:
                raise ValueError(
                    "Output exists; use --resume for incomplete identical run"
                )
            saved = json.loads(path.read_text(encoding="utf-8"))
            validate_resume(saved, signature, cases)
        else:
            if args.resume:
                raise ValueError("Resume output does not exist")
            saved = {"signature": signature, "complete": False, "rows": []}
        backend = QwenBackend(args.revision)
        if "hardware" in saved:
            for key in ["gpu", "total_vram", "packages", "torch", "cuda"]:
                if saved["hardware"][key] != backend.hardware[key]:
                    raise ValueError(f"Resume environment mismatch: {key}")
        saved["hardware"] = backend.hardware
        atomic(path, saved)
        result = execute(cases, packets, backend, path, saved)
        print(json.dumps(result["metrics"], indent=2))
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
