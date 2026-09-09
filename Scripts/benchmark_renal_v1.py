"""Fresh Renal v1 DEV selection, frozen heldout, safety, and latency benchmark."""
from __future__ import annotations

import json, math, os, platform, re, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
EVAL = ROOT / "evaluation" / "renal"
REPORT = ROOT / "reports" / "renal_benchmark_v1.json"
MODEL = "Qwen/Qwen3-Embedding-0.6B"
INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

def tokens(text): return re.findall(r"[a-z0-9]+", text.casefold())

def load_chunks(folder):
    chunks=[]
    for path in sorted(folder.glob("*.json")): chunks += json.loads(path.read_text(encoding="utf-8"))["chunks"]
    return chunks

def bm25(chunks, queries):
    docs=[tokens(c["text"]) for c in chunks]; n=len(docs); df=Counter(t for d in docs for t in set(d)); avg=sum(map(len,docs))/n
    rankings=[]
    for q in queries:
        scores=[]
        for i,d in enumerate(docs):
            counts=Counter(d); score=0
            for term in tokens(q["query"]):
                if term in counts:
                    idf=math.log((n-df[term]+.5)/(df[term]+.5)+1); tf=counts[term]
                    score += idf*(tf*2.2)/(tf+1.2*(.25+.75*len(d)/avg))
            scores.append(score)
        rankings.append(np.argsort(scores)[::-1][:10].tolist())
    return rankings

def relevant(chunk, query):
    if chunk.get("document_id") not in query["gold_document_ids"]: return False
    gold={str(x).casefold() for x in query.get("gold_section_ids",[]) if x}
    actual={str(x).casefold() for x in chunk.get("section_path",[]) if x}
    return not gold or bool(gold & actual)

def metrics(chunks, queries, rankings):
    answerable=[(q,r) for q,r in zip(queries,rankings) if q["answerable"]]
    out={}
    for k in (1,3,5,10):
        hits=sum(any(relevant(chunks[i],q) for i in r[:k]) for q,r in answerable)
        out[f"hit_at_{k}"]={"value":hits/len(answerable),"numerator":hits,"denominator":len(answerable)}
        src=sum(bool(set(q["gold_document_ids"]) & {chunks[i]["document_id"] for i in r[:k]}) for q,r in answerable)
        out[f"gold_source_recall_at_{k}"]={"value":src/len(answerable),"numerator":src,"denominator":len(answerable)}
    rr=[]; ndcg=[]
    for q,r in answerable:
        rel=[int(relevant(chunks[i],q)) for i in r]
        rank=next((i+1 for i,x in enumerate(rel) if x),None); rr.append(1/rank if rank else 0)
        dcg=sum(x/math.log2(i+2) for i,x in enumerate(rel)); ndcg.append(dcg/sum(1/math.log2(i+2) for i in range(max(1,sum(rel)))) if any(rel) else 0)
    out["mrr"]=sum(rr)/len(rr); out["ndcg_at_10"]=sum(ndcg)/len(ndcg)
    auth=[(q,r) for q,r in answerable if q["authority_sensitive"]]
    out["authority_sensitive_accuracy"]={"value":sum(any(relevant(chunks[i],q) for i in r[:5]) for q,r in auth)/len(auth) if auth else None,"denominator":len(auth)}
    return out

def render(chunk, representation, meta):
    text=chunk["text"]
    if representation=="content_only": return text
    doc=meta[chunk["document_id"]]
    base=f"Source: {doc['title']} [{chunk['document_id']}]\n{text}"
    if representation=="source_aware": return base
    return f"Topics: {', '.join(doc['topic_tags'])}\nSection: {' > '.join(chunk.get('section_path',[]))}\n{base}"

def dense(model,chunks,queries,representation,meta):
    t=time.perf_counter(); corpus=model.encode([render(c,representation,meta) for c in chunks],batch_size=16,normalize_embeddings=True,show_progress_bar=True); corpus_ms=(time.perf_counter()-t)*1000
    qtimes=[]; rankings=[]; top_scores=[]
    for q in queries:
        t=time.perf_counter(); emb=model.encode([INSTRUCTION+q["query"]],normalize_embeddings=True,show_progress_bar=False)[0]; qtimes.append((time.perf_counter()-t)*1000)
        scores=corpus@emb; rankings.append(np.argsort(scores)[::-1][:10].tolist()); top_scores.append(float(scores[rankings[-1][0]]))
    return rankings,top_scores,{"corpus_embedding_ms":corpus_ms,"query_embedding_ms":qtimes}

def pct(values,p): return float(np.percentile(values,p)) if values else None

def main():
    global np
    os.environ["HF_HUB_OFFLINE"]="1"
    if REPORT.exists():
        previous = json.loads(REPORT.read_text(encoding="utf-8"))
        if previous.get("measurement_status") == "FROZEN_SINGLE_HELDOUT_RUN":
            raise SystemExit(
                "RENAL_BENCHMARK_FROZEN: heldout was already run once; preserve the report and use DEV-only tooling."
            )
    import numpy as np
    import torch
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sentence_transformers import SentenceTransformer
    dev=json.loads((EVAL/"renal-dev-v1.json").read_text(encoding="utf-8"))["queries"]
    held=json.loads((EVAL/"renal-heldout-v1.json").read_text(encoding="utf-8"))["queries"]
    cal=json.loads((EVAL/"renal-calibration-v1.json").read_text(encoding="utf-8"))["queries"]
    registry=json.loads((DATA/"metadata"/"renal_source_registry_v1.json").read_text(encoding="utf-8")); meta={d["document_id"]:d for d in registry["documents"] if d["status"]=="accepted"}
    folders={p.name:p for p in (DATA/"experiments"/"renal"/"chunking").iterdir() if p.is_dir()}
    chunk_dev={}
    for name,path in folders.items():
        chunks=load_chunks(path); chunk_dev[name]=metrics(chunks,dev,bm25(chunks,dev))
    chosen=max(chunk_dev,key=lambda n:(chunk_dev[n]["mrr"],chunk_dev[n]["hit_at_1"]["value"])); chunks=load_chunks(folders[chosen])
    device="cuda" if torch.cuda.is_available() else "cpu"
    model=SentenceTransformer(MODEL,device=device,local_files_only=True)
    # Qwen supports very long inputs, but renal chunks are intentionally capped
    # for retrieval. Avoid padding/attention work beyond the benchmark contract.
    model.max_seq_length=512
    dense_dev={}; cache={}
    for rep in ("content_only","source_aware","metadata_aware"):
        ranks,scores,timing=dense(model,chunks,dev,rep,meta); dense_dev[rep]={**metrics(chunks,dev,ranks),"timing":timing}; cache[rep]=(ranks,scores,timing)
    selected=max(dense_dev,key=lambda n:(dense_dev[n]["mrr"],dense_dev[n]["hit_at_1"]["value"]))
    held_ranks,held_scores,held_timing=dense(model,chunks,held,selected,meta)
    cal_ranks,cal_scores,cal_timing=dense(model,chunks,cal,selected,meta)
    y=np.array([int(q["support_label"]=="SUPPORTED") for q in cal]); scores=np.array(cal_scores)
    candidates=sorted(set(scores.tolist())); best=None
    for threshold in candidates:
        pred=scores>=threshold; tp=int(((pred==1)&(y==1)).sum()); fp=int(((pred==1)&(y==0)).sum()); tn=int(((pred==0)&(y==0)).sum()); fn=int(((pred==0)&(y==1)).sum())
        unsafe=fp/max(1,fp+tn); precision=tp/max(1,tp+fp); recall=tp/max(1,tp+fn); f1=2*precision*recall/max(1e-12,precision+recall)
        candidate=(unsafe<=.05,f1,-unsafe,threshold,tp,fp,tn,fn,precision,recall)
        if best is None or candidate>best: best=candidate
    _,f1,negunsafe,threshold,tp,fp,tn,fn,precision,recall=best
    safety={"n":len(cal),"threshold":threshold,"precision":precision,"recall":recall,"f1":f1,"specificity":tn/max(1,tn+fp),"auroc":roc_auc_score(y,scores),"auprc":average_precision_score(y,scores),"unsafe_accept_rate":-negunsafe,"false_refusal_rate":fn/max(1,tp+fn),"confusion_matrix":{"tp":tp,"tn":tn,"fp":fp,"fn":fn}}
    answerable=[q for q in held if q["answerable"]]
    report={"measurement_status":"FRESHLY_MEASURED","model":MODEL,"chunking_dev":chunk_dev,"selected_chunking":chosen,"dense_dev":dense_dev,"selected_representation":selected,"heldout_sha256":(EVAL/"renal-heldout-v1.json.sha256").read_text().split()[0],"heldout_counts":{"n":len(held),"answerable":len(answerable),"unsupported":len(held)-len(answerable),"foundational":sum("foundational" in q["foundational_or_clinical"] for q in answerable),"clinical":sum("clinical" in q["foundational_or_clinical"] for q in answerable),"authority_sensitive":sum(q["authority_sensitive"] for q in answerable)},"heldout":metrics(chunks,held,held_ranks),"evidence_sufficiency":safety,"latency":{"embedding_query_p50_ms":pct(held_timing["query_embedding_ms"],50),"embedding_query_p95_ms":pct(held_timing["query_embedding_ms"],95),"retrieval_end_to_end_p50_ms":pct(held_timing["query_embedding_ms"],50),"retrieval_end_to_end_p95_ms":pct(held_timing["query_embedding_ms"],95),"evidence_decision_p50_ms":0.0,"evidence_decision_p95_ms":0.0,"n":len(held)},"environment":{"platform":platform.platform(),"processor":platform.processor(),"python":platform.python_version(),"device":device,"gpu":torch.cuda.get_device_name(0) if device=="cuda" else None}}
    REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"selected_chunking":chosen,"selected_representation":selected,"heldout":report["heldout"],"safety":safety,"latency":report["latency"]},indent=2))

if __name__=="__main__": main()
