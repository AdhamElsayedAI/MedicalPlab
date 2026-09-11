"""Phase 1 corpus audit for V5 forensic inspection."""
import json
import pathlib
import hashlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Corpus: chunk count, doc distribution
chunks_dir = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
all_chunks = []
doc_chunk_count = {}
for p in sorted(chunks_dir.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    chs = payload.get("chunks", [])
    all_chunks.extend(chs)
    for ch in chs:
        did = ch.get("document_id", "?")
        doc_chunk_count[did] = doc_chunk_count.get(did, 0) + 1

print(f"Total chunks (B_400_overlap): {len(all_chunks)}")
print(f"Documents with chunks: {len(doc_chunk_count)}")
if doc_chunk_count:
    vals = list(doc_chunk_count.values())
    print(f"Chunks per doc - min={min(vals)} max={max(vals)} mean={sum(vals)/len(vals):.1f}")

# Section structure from V4 metadata
sec_meta_path = ROOT / "Data/experiments/renal_v4/cache/sections_metadata.json"
sec_meta = json.loads(sec_meta_path.read_bytes())
print(f"Section metadata top-level keys: {list(sec_meta.keys())[:8]}")
sections_key = None
for k in ["sections", "section_metadata", "section_list"]:
    if k in sec_meta:
        sections_key = k
        break
if sections_key:
    print(f"Total sections ({sections_key}): {len(sec_meta[sections_key])}")
else:
    # chunk_to_section mapping
    c2s = sec_meta.get("chunk_to_section", [])
    unique_sec = len(set(c2s)) if c2s else 0
    print(f"chunk_to_section entries: {len(c2s)}, unique section indices: {unique_sec}")

# Registry
reg_path = ROOT / "Data/metadata/renal_source_registry_v2.json"
reg = json.loads(reg_path.read_bytes())
accepted = [d for d in reg.get("documents", []) if d.get("status") == "accepted"]
print(f"\nRegistry accepted docs: {len(accepted)}")
for d in accepted:
    print(f"  {d['document_id']}: {d.get('title','')[:70]} | {d.get('topic_tags',[])}")

# Corpus SHA for firewall
corpus_sha = hashlib.sha256(chunks_dir.__str__().encode()).hexdigest()[:16]
print(f"\nCorpus dir (B_400_overlap) - files: {len(list(chunks_dir.glob('*.chunks.json')))}")

# Embedding cache SHAs
cache_v3 = ROOT / "Data/experiments/renal_v3/cache"
for f in sorted(cache_v3.iterdir()):
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    print(f"  {f.name}: {sha}")
