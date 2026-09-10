"""Phase 12: Controlled coherent child chunking strategy (F_coherent_child_180).

Per Mission Section 24 and Phase 12:
- Target words: 180 (bounds ~150-220)
- Strictly sentence-boundary aware
- 1-sentence overlap
- Filters out non-content blocks (references, acknowledgments)
- Output: Data/experiments/renal_v3/chunking/F_coherent_child_180/{doc_id}.chunks.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "Data" / "processed" / "renal_v2"
OUTPUT_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "chunking" / "F_coherent_child_180"


def role_for(block: dict) -> str:
    heading = " ".join(block.get("section_path", [])).casefold()
    if any(term in heading for term in ("references", "acknowledg", "author contribution", "supplement", "funding", "conflict of interest")):
        return "EXCLUDED_FROM_SEARCH"
    if any(term in heading for term in ("methods", "materials and methods", "statistical analysis", "results")):
        return "LOW_PRIORITY"
    if any(term in heading for term in ("introduction", "discussion", "conclusion", "physiology", "mechanism", "management", "diagnosis", "guideline")):
        return "CORE"
    return "SUPPORTING"


def sentence_window_180(document: dict, target_words: int = 180, overlap_sentences: int = 1) -> list[dict]:
    chunks = []
    doc_id = document["document_id"]
    for block in document["sections"]:
        role = role_for(block)
        if role == "EXCLUDED_FROM_SEARCH":
            continue
            
        raw_text = block.get("text", "").strip()
        if len(raw_text.split()) < 30:
            continue
            
        sentences = re.split(r"(?<=[.!?])\s+", raw_text)
        p_id = f"{doc_id}-P{int(block['block_index']):04d}"
        current_sentences = []
        current_words = 0
        
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            w = len(s.split())
            if current_words + w > target_words and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append({
                    "chunk_id": f"{doc_id}-F-C{len(chunks)+1:04d}",
                    "child_chunk_id": f"{doc_id}-F-C{len(chunks)+1:04d}",
                    "document_id": doc_id,
                    "parent_section_id": p_id,
                    "text": chunk_text,
                    "heading": block.get("heading", ""),
                    "section_path": block.get("section_path", []),
                    "source_block_index": block["block_index"],
                    "word_count": len(chunk_text.split()),
                    "retrieval_role": role,
                })
                current_sentences = current_sentences[-overlap_sentences:] if overlap_sentences > 0 else []
                current_words = sum(len(x.split()) for x in current_sentences)
            current_sentences.append(s)
            current_words += w
            
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            # If tiny trailing piece and chunks already exist for this block, merge with previous
            if len(chunk_text.split()) < 40 and chunks and chunks[-1]["parent_section_id"] == p_id:
                chunks[-1]["text"] += " " + chunk_text
                chunks[-1]["word_count"] = len(chunks[-1]["text"].split())
            else:
                chunks.append({
                    "chunk_id": f"{doc_id}-F-C{len(chunks)+1:04d}",
                    "child_chunk_id": f"{doc_id}-F-C{len(chunks)+1:04d}",
                    "document_id": doc_id,
                    "parent_section_id": p_id,
                    "text": chunk_text,
                    "heading": block.get("heading", ""),
                    "section_path": block.get("section_path", []),
                    "source_block_index": block["block_index"],
                    "word_count": len(chunk_text.split()),
                    "retrieval_role": role,
                })
    return chunks


def main():
    print("=" * 70)
    print("PHASE 12: GENERATING F_coherent_child_180 CHUNKS")
    print("=" * 70)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    enriched_files = sorted(PROCESSED_DIR.glob("*.sections.enriched.json"))
    print(f"Found {len(enriched_files)} enriched document files.")
    
    total_chunks = 0
    all_word_counts = []
    
    for f in enriched_files:
        doc_data = json.loads(f.read_text(encoding="utf-8"))
        doc_id = doc_data.get("document_id") or f.name.replace(".sections.enriched.json", "")
        doc_chunks = sentence_window_180(doc_data, target_words=180, overlap_sentences=1)
        
        out_file = OUTPUT_DIR / f"{doc_id}.chunks.json"
        out_file.write_text(json.dumps({
            "document_id": doc_id,
            "chunk_strategy": "F_coherent_child_180",
            "target_words": 180,
            "n_chunks": len(doc_chunks),
            "chunks": doc_chunks
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        
        total_chunks += len(doc_chunks)
        all_word_counts.extend([c["word_count"] for c in doc_chunks])
        
    print(f"\nGenerated {total_chunks} total chunks across {len(enriched_files)} documents.")
    print(f"Mean words per chunk: {sum(all_word_counts) / len(all_word_counts):.1f}")
    print(f"Min words: {min(all_word_counts)}, Max words: {max(all_word_counts)}")
    print(f"Target range (150-220 words) fraction: {sum(1 for w in all_word_counts if 140 <= w <= 220) / len(all_word_counts)*100:.1f}%")
    print(f"Wrote chunks to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
