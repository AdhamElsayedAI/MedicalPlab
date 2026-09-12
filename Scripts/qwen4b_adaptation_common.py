from __future__ import annotations
import hashlib, json, math, os, re, shutil, tempfile
from pathlib import Path
from typing import Any, Iterable
import sys

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "qwen4b_domain_adaptation.json"
AUTHORIZED_REVISION = "5cf2132abc99cad020ac570b19d031efec650f2b"
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_CONFIG
    if not p.is_absolute(): p = ROOT / p
    cfg = json.loads(p.read_text(encoding="utf-8"))
    if cfg["model"]["id"] != "Qwen/Qwen3-Embedding-4B":
        raise ValueError("AUTHORIZED_MODEL_MISMATCH")
    if cfg["model"]["revision"] != AUTHORIZED_REVISION:
        raise ValueError("AUTHORIZED_MODEL_REVISION_MISMATCH")
    if cfg["model"].get("tokenizer_revision") != AUTHORIZED_REVISION:
        raise ValueError("AUTHORIZED_TOKENIZER_REVISION_MISMATCH")
    return cfg


def root_path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()
def canonical_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
def atomic_json(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data=canonical_json_bytes(obj); tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_bytes(data); os.replace(tmp,path); return sha256_bytes(data)
def normalize_text(text: str) -> str:
    text=re.sub(r"[^a-z0-9%./+-]+"," ",(text or "").lower())
    return re.sub(r"\s+"," ",text).strip()
def token_set(text: str) -> set[str]: return {t for t in re.findall(r"[a-z0-9]+", normalize_text(text)) if len(t) > 1}
def jaccard(a: str,b: str) -> float:
    x,y=token_set(a),token_set(b)
    return len(x&y)/len(x|y) if x and y else 0.0

def wilson(successes:int,total:int,z:float=1.96)->list[float]:
    if not total:return [0.0,0.0]
    p=successes/total; d=1+z*z/total
    c=(p+z*z/(2*total))/d; s=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [round(max(0,c-s),4),round(min(1,c+s),4)]
def stat(count:int,total:int)->dict[str,Any]:
    return {"count":count,"total":total,"rate":round(count/total,4) if total else 0.0,"pct":f"{100*count/total:.2f}%" if total else "0.00%","ci_95_wilson":wilson(count,total)}

def resolve_corpus_dir(cfg:dict[str,Any])->Path:
    data = cfg.get("data", {})
    if data.get("corpus_lock_policy") != "EXACT_PATH_NO_FALLBACK":
        raise RuntimeError("CORPUS_LOCK_POLICY_REQUIRED")
    configured = data.get("corpus_dir")
    if not configured:
        raise RuntimeError("CORPUS_DIR_MUST_BE_EXPLICIT")
    p = root_path(configured)
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(f"LOCKED_CORPUS_DIRECTORY_NOT_FOUND path={p}")
    if not any(p.glob("*.chunks.json")):
        raise FileNotFoundError(f"LOCKED_CORPUS_HAS_NO_CHUNK_FILES path={p}")
    for legacy in data.get("legacy_corpus_dirs", []):
        if p.resolve() == root_path(legacy).resolve():
            raise RuntimeError(f"LEGACY_CORPUS_FORBIDDEN path={p}")
    expected = data.get("corpus_sha256_tree")
    if expected and sha256_tree(p) != expected:
        raise RuntimeError("LOCKED_CORPUS_SHA_MISMATCH")
    return p

def load_chunks(corpus_dir:Path)->tuple[dict[str,dict[str,Any]],list[str]]:
    chunks={}; ordered=[]
    for p in sorted(corpus_dir.glob("*.chunks.json")):
        obj=json.loads(p.read_text(encoding="utf-8")); title=obj.get("document_title") or obj.get("title") or obj.get("document_id")
        for ch in obj.get("chunks",[]):
            cid=ch["chunk_id"]
            if not isinstance(cid, str) or not cid.strip():
                raise ValueError(f"INVALID_CHUNK_ID file={p.name}")
            if cid in chunks:
                raise ValueError(f"DUPLICATE_CHUNK_ID id={cid}")
            ch=dict(ch); ch.setdefault("document_id",obj.get("document_id")); ch.setdefault("document_title",title)
            if not isinstance(ch.get("text"), str) or not ch["text"].strip():
                raise ValueError(f"EMPTY_CHUNK_TEXT id={cid}")
            if not isinstance(ch.get("document_id"), str) or not ch["document_id"].strip():
                raise ValueError(f"MISSING_CHUNK_DOCUMENT id={cid}")
            chunks[cid]=ch; ordered.append(cid)
    if not chunks: raise ValueError("EMPTY_CORPUS")
    return chunks,ordered


def literal_span_in_text(span: str, text: str) -> bool:
    """Whitespace-only normalization; preserve signs, punctuation and negation."""
    normalized_span = " ".join(span.split())
    normalized_text = " ".join(text.split())
    return bool(normalized_span and normalized_text and normalized_span in normalized_text)

def verify_product_dev_sha(cfg:dict[str,Any])->str:
    p=root_path(cfg["data"]["product_dev_v3"]); actual=sha256_file(p); expected=cfg["data"]["product_dev_v3_sha256"]
    if actual!=expected: raise RuntimeError(f"PRODUCT_DEV_V3_SHA_MISMATCH expected={expected} actual={actual}")
    return actual

def atomic_replace_dir(tmp:Path,dst:Path)->None:
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists(): shutil.rmtree(dst)
    os.replace(tmp,dst)

def sha256_tree(path: Path) -> str:
    h=hashlib.sha256()
    for p in sorted(x for x in path.rglob('*') if x.is_file()):
        h.update(str(p.relative_to(path)).replace('\\','/').encode()); h.update(b'\0'); h.update(p.read_bytes()); h.update(b'\0')
    return h.hexdigest()
