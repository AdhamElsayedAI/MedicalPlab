import hashlib
import json
import re
from pathlib import Path
import numpy as np

ROOT = Path(".")
TRAIN_EXT_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-v5-extended.json"
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
DEV_B_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-b-v5.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"

train_items = json.loads(TRAIN_EXT_PATH.read_bytes())
dev_a_items = json.loads(DEV_A_PATH.read_bytes())
dev_b_items = json.loads(DEV_B_PATH.read_bytes())

print("=" * 70)
print(f"COMPREHENSIVE TRAIN FIREWALL AUDIT (N={len(train_items)})")
print("=" * 70)

# 1. 23rd Document Explanation
reg = json.loads(REGISTRY_PATH.read_bytes())
active_docs = {d["document_id"]: d for d in reg.get("documents", []) if d.get("v2_active")}
train_docs = set(item["gold_doc_id"] for item in train_items)
missing_docs = set(active_docs.keys()) - train_docs

print(f"1. Active Corpus Documents: {len(active_docs)}")
print(f"   Represented in TRAIN:    {len(train_docs)}")
print(f"   Missing from TRAIN:      {missing_docs}")
for doc_id in missing_docs:
    d = active_docs[doc_id]
    print(f"   Details for {doc_id}:")
    print(f"     Title: {d['title']}")
    print(f"     Educational Class: {d.get('educational_classification')}")
    print(f"     Evidence Type: {d.get('evidence_type')}")
    print(f"     Topic Tags: {d.get('topic_tags')}")

# 2. Section Identity Overlap
def normalize_path(path):
    if not path:
        return ""
    if isinstance(path, list):
        return " > ".join(s.strip().lower() for s in path)
    return str(path).strip().lower()

train_sections = set((item["gold_doc_id"], normalize_path(item.get("gold_section_path", []))) for item in train_items)
dev_a_sections = set((item["gold_doc_id"], normalize_path(item.get("gold_section_path", []))) for item in dev_a_items)
dev_b_sections = set((item["gold_doc_id"], normalize_path(item.get("gold_section_path", []))) for item in dev_b_items)

sec_leak_a = train_sections & dev_a_sections
sec_leak_b = train_sections & dev_b_sections

print(f"\n2. Section Identity Overlap:")
print(f"   Unique (Doc, SectionPath) in TRAIN: {len(train_sections)}")
print(f"   Section Overlap TRAIN vs DEV-A:     {len(sec_leak_a)}")
if sec_leak_a:
    for s in list(sec_leak_a)[:5]:
        print(f"     Shared Section (DEV-A): {s}")
print(f"   Section Overlap TRAIN vs DEV-B:     {len(sec_leak_b)}")
if sec_leak_b:
    for s in list(sec_leak_b)[:5]:
        print(f"     Shared Section (DEV-B): {s}")

# 3. Gold Chunk ID Overlap
train_cids = set(cid for item in train_items for cid in item.get("gold_chunk_ids", []))
dev_a_cids = set(cid for item in dev_a_items for cid in item.get("gold_chunk_ids", []))
dev_b_cids = set(cid for item in dev_b_items for cid in item.get("gold_chunk_ids", []))

cid_overlap_a = train_cids & dev_a_cids
cid_overlap_b = train_cids & dev_b_cids

print(f"\n3. Gold Chunk ID Overlap:")
print(f"   Total Gold Chunks in TRAIN: {len(train_cids)}")
print(f"   Gold Chunk Overlap TRAIN vs DEV-A: {len(cid_overlap_a)}")
print(f"   Gold Chunk Overlap TRAIN vs DEV-B: {len(cid_overlap_b)}")
assert len(cid_overlap_a) == 0, f"Gold chunk overlap with DEV-A: {cid_overlap_a}"
assert len(cid_overlap_b) == 0, f"Gold chunk overlap with DEV-B: {cid_overlap_b}"

# 4. Evidence-Span Family Overlap
# Check if any chunk in TRAIN is directly adjacent (+/- 1 chunk) to a DEV-A / DEV-B gold chunk
def get_chunk_num(cid):
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_chunk_prefix(cid):
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

dev_a_expanded_cids = set()
for cid in dev_a_cids:
    pfx = get_chunk_prefix(cid)
    num = get_chunk_num(cid)
    if num != -1:
        dev_a_expanded_cids.add(f"{pfx}-C{num:04d}")
        dev_a_expanded_cids.add(f"{pfx}-C{num-1:04d}")
        dev_a_expanded_cids.add(f"{pfx}-C{num+1:04d}")

dev_b_expanded_cids = set()
for cid in dev_b_cids:
    pfx = get_chunk_prefix(cid)
    num = get_chunk_num(cid)
    if num != -1:
        dev_b_expanded_cids.add(f"{pfx}-C{num:04d}")
        dev_b_expanded_cids.add(f"{pfx}-C{num-1:04d}")
        dev_b_expanded_cids.add(f"{pfx}-C{num+1:04d}")

adjacent_overlap_a = train_cids & dev_a_expanded_cids
adjacent_overlap_b = train_cids & dev_b_expanded_cids

print(f"\n4. Adjacent Evidence-Span Window (+/- 1 chunk) Overlap:")
print(f"   TRAIN vs DEV-A Adjacent Overlap: {len(adjacent_overlap_a)}")
if adjacent_overlap_a:
    print(f"     Adjacent chunks: {adjacent_overlap_a}")
print(f"   TRAIN vs DEV-B Adjacent Overlap: {len(adjacent_overlap_b)}")
if adjacent_overlap_b:
    print(f"     Adjacent chunks: {adjacent_overlap_b}")

# 5. Query Family Overlap
train_qf = set(item.get("query_family") for item in train_items if item.get("query_family"))
dev_a_qf = set(item.get("query_family") for item in dev_a_items if item.get("query_family"))
dev_b_qf = set(item.get("query_family") for item in dev_b_items if item.get("query_family"))

print(f"\n5. Query Family Overlap:")
print(f"   Unique Query Families in TRAIN: {len(train_qf)}")
print(f"   Query Family Overlap TRAIN vs DEV-A: {len(train_qf & dev_a_qf)}")
print(f"   Query Family Overlap TRAIN vs DEV-B: {len(train_qf & dev_b_qf)}")
assert len(train_qf & dev_a_qf) == 0, "Query family overlap with DEV-A!"
assert len(train_qf & dev_b_qf) == 0, "Query family overlap with DEV-B!"

# 6. Lexical and N-Gram Similarity Review (Beyond Cosine)
def tokenize(s):
    return re.findall(r"\w+", s.lower())

def ngrams(words, n):
    return set(tuple(words[i:i+n]) for i in range(len(words)-n+1))

def jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def compute_lexical_overlap(items1, items2):
    max_word_jaccard = 0.0
    max_bigram_jaccard = 0.0
    top_pairs = []
    for it1 in items1:
        w1 = tokenize(it1["query"])
        bg1 = ngrams(w1, 2)
        for it2 in items2:
            w2 = tokenize(it2["query"])
            bg2 = ngrams(w2, 2)
            wj = jaccard(set(w1), set(w2))
            bj = jaccard(bg1, bg2)
            if wj > max_word_jaccard:
                max_word_jaccard = wj
            if bj > max_bigram_jaccard:
                max_bigram_jaccard = bj
            if wj >= 0.65 or bj >= 0.50:
                top_pairs.append((it1["query_id"], it2["query_id"], wj, bj, it1["query"], it2["query"]))
    return max_word_jaccard, max_bigram_jaccard, top_pairs

max_wj_a, max_bj_a, top_a = compute_lexical_overlap(train_items, dev_a_items)
max_wj_b, max_bj_b, top_b = compute_lexical_overlap(train_items, dev_b_items)

print(f"\n6. Lexical & N-gram Near-Duplicate Review:")
print(f"   TRAIN vs DEV-A Max Word Jaccard:   {max_wj_a:.4f}, Max Bigram Jaccard: {max_bj_a:.4f}")
print(f"   High Lexical Overlap Pairs (TRAIN vs DEV-A, J>=0.65 or Bigram>=0.50): {len(top_a)}")
for p in top_a[:5]:
    print(f"     [{p[0]} vs {p[1]}] WordJ={p[2]:.3f}, BiJ={p[3]:.3f}\n       T: {p[4]}\n       D: {p[5]}")

print(f"   TRAIN vs DEV-B Max Word Jaccard:   {max_wj_b:.4f}, Max Bigram Jaccard: {max_bj_b:.4f}")
print(f"   High Lexical Overlap Pairs (TRAIN vs DEV-B, J>=0.65 or Bigram>=0.50): {len(top_b)}")
for p in top_b[:5]:
    print(f"     [{p[0]} vs {p[1]}] WordJ={p[2]:.3f}, BiJ={p[3]:.3f}\n       T: {p[4]}\n       D: {p[5]}")

# 7. Check Historical Heldouts Firewall
heldout_files = [
    ROOT / "evaluation" / "renal" / "v1" / "renal-heldout-gold-v1.json",
    ROOT / "evaluation" / "renal" / "v2" / "renal-heldout-v2.json",
    ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3.json",
    ROOT / "evaluation" / "renal" / "v4" / "renal-heldout-v4.json",
]
heldout_queries = set()
for hf in heldout_files:
    if hf.exists():
        try:
            hdata = json.loads(hf.read_bytes())
            if isinstance(hdata, list):
                for h in hdata:
                    q = h.get("query") or h.get("question")
                    if q:
                        heldout_queries.add(q.strip().lower())
            elif isinstance(hdata, dict):
                for h in hdata.get("queries", hdata.get("questions", [])):
                    q = h.get("query") or h.get("question")
                    if q:
                        heldout_queries.add(q.strip().lower())
        except Exception as e:
            pass

train_queries = set(item["query"].strip().lower() for item in train_items)
heldout_overlap = train_queries & heldout_queries
print(f"\n7. Historical Heldouts Firewall (V1, V2, V3, V4 heldouts):")
print(f"   Total Historical Heldout Queries: {len(heldout_queries)}")
print(f"   Overlap TRAIN vs Historical Heldouts: {len(heldout_overlap)}")
assert len(heldout_overlap) == 0, f"Leakage into historical heldout: {heldout_overlap}"
