"""Check V4 evaluation set metadata and query family names (no content inspection)."""
import json, pathlib, hashlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# V4 spent query families — to determine what topic families are spent
v4_dir = ROOT / "evaluation/renal/v4"

# We can only look at metadata, not individual query content
for fname in sorted(v4_dir.glob("*.json")):
    data = json.loads(fname.read_bytes())
    sha = hashlib.sha256(fname.read_bytes()).hexdigest()
    if isinstance(data, list):
        queries = data
        print(f"{fname.name}: N={len(queries)}, SHA={sha[:16]}...")
        # Inspect structural keys only
        if queries:
            print(f"  Keys: {list(queries[0].keys())}")
            # Topic families (not content of queries)
            if "curriculum_topic" in queries[0]:
                topics = {}
                for q in queries:
                    t = q.get("curriculum_topic", "?")
                    topics[t] = topics.get(t, 0) + 1
                print(f"  Topic distribution: {dict(sorted(topics.items()))}")
            if "query_style" in queries[0]:
                styles = {}
                for q in queries:
                    s = q.get("query_style", "?")
                    styles[s] = styles.get(s, 0) + 1
                print(f"  Style distribution: {dict(sorted(styles.items()))}")
    elif isinstance(data, dict):
        queries = data.get("queries", [])
        print(f"{fname.name}: N={len(queries)}, SHA={sha[:16]}...")
        if queries:
            print(f"  Keys: {list(queries[0].keys())}")
            if "curriculum_topic" in queries[0]:
                topics = {}
                for q in queries:
                    t = q.get("curriculum_topic", "?")
                    topics[t] = topics.get(t, 0) + 1
                print(f"  Topic distribution: {dict(sorted(topics.items()))}")
            if "query_style" in queries[0]:
                styles = {}
                for q in queries:
                    s = q.get("query_style", "?")
                    styles[s] = styles.get(s, 0) + 1
                print(f"  Style distribution: {dict(sorted(styles.items()))}")

# V3 evaluation sets
v3_dir = ROOT / "evaluation/renal/v3"
print("\n--- V3 ---")
for fname in sorted(v3_dir.glob("*.json")):
    data = json.loads(fname.read_bytes())
    sha = hashlib.sha256(fname.read_bytes()).hexdigest()
    queries = data if isinstance(data, list) else data.get("queries", [])
    print(f"{fname.name}: N={len(queries)}, SHA={sha[:16]}...")
    if queries and isinstance(queries[0], dict):
        print(f"  Keys: {list(queries[0].keys())[:8]}")

# Earlier spent sets
print("\n--- ROOT renal eval ---")
for fname in sorted((ROOT / "evaluation/renal").glob("*.json")):
    data = json.loads(fname.read_bytes())
    sha = hashlib.sha256(fname.read_bytes()).hexdigest()
    queries = data if isinstance(data, list) else data.get("queries", [])
    print(f"{fname.name}: N={len(queries)}, SHA={sha[:16]}...")
