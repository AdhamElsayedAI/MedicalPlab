from __future__ import annotations
import argparse, fnmatch, json, re
from pathlib import Path
from typing import Any
from qwen4b_adaptation_common import ROOT, load_config, root_path, normalize_text, jaccard, atomic_json, sha256_file

def walk_records(obj:Any):
    if isinstance(obj,dict):
        if any(k in obj for k in ("query","question","stem","canonical_claim","atomic_claim","gold_chunk_ids","exact_gold_chunk_ids","semantic_support_chunk_ids")): yield obj
        for v in obj.values(): yield from walk_records(v)
    elif isinstance(obj,list):
        for v in obj: yield from walk_records(v)
def eval_files(cfg):
    files=set()
    for pat in cfg["data"]["forbidden_eval_globs"]:
        files.update(ROOT.glob(pat))
    return sorted(p for p in files if p.is_file() and p.suffix==".json")
def extract_eval(cfg):
    queries=[]; claims=[]; spans=[]; passage_ids=set(); sources=[]
    for p in eval_files(cfg):
        try: obj=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        sources.append(str(p.relative_to(ROOT)))
        for r in walk_records(obj):
            for k in ("query","question","stem"):
                if isinstance(r.get(k),str): queries.append((r[k],sources[-1]))
            for k in ("canonical_claim","atomic_claim","claim"):
                if isinstance(r.get(k),str): claims.append((r[k],sources[-1]))
            for k in ("evidence_span_text","evidence_span","gold_passage","positive_passage"):
                if isinstance(r.get(k),str): spans.append((r[k],sources[-1]))
            for k in ("gold_chunk_ids","exact_gold_chunk_ids","semantic_support_chunk_ids","gold_passage_ids"):
                v=r.get(k,[]); passage_ids.update(v if isinstance(v,list) else [v])
    return queries,claims,spans,{str(x) for x in passage_ids if x},sources

def adjacent_ids(cid:str)->set[str]:
    m=re.match(r"(.+-C)(\d+)$",cid)
    if not m:return set()
    n=int(m.group(2)); width=len(m.group(2)); return {f"{m.group(1)}{i:0{width}d}" for i in (n-1,n+1) if i>=0}
def lexical_firewall(train, cfg):
    eq,ec,es,eids,sources=extract_eval(cfg); nq={normalize_text(q):(q,s) for q,s in eq}; nc={normalize_text(c):(c,s) for c,s in ec}; ns={normalize_text(s):(s,src) for s,src in es}
    threshold=cfg["data"]["near_duplicate_threshold"]; excluded=[]; clean=[]
    for r in train:
        reasons=[]; qn=normalize_text(r["query"]); cn=normalize_text(r.get("atomic_claim","") or ""); pn=normalize_text(r["positive_passage"])
        if qn in nq: reasons.append({"type":"exact_or_normalized_query_overlap","source":nq[qn][1]})
        if cn and cn in nc: reasons.append({"type":"same_atomic_claim","source":nc[cn][1]})
        if pn in ns: reasons.append({"type":"same_evidence_span","source":ns[pn][1]})
        pid=r["positive_passage_id"]
        if pid in eids: reasons.append({"type":"same_passage_or_gold","passage_id":pid})
        if adjacent_ids(pid)&eids: reasons.append({"type":"adjacent_evidence_leakage","passage_id":pid})
        for hid,htext in zip(r.get("hard_negative_ids",[]),r.get("hard_negative_passages",[])):
            if hid in eids: reasons.append({"type":"hard_negative_overlaps_eval_gold","passage_id":hid})
            if adjacent_ids(hid)&eids: reasons.append({"type":"hard_negative_adjacent_eval_gold","passage_id":hid})
            hnorm=normalize_text(htext)
            if hnorm and hnorm in ns: reasons.append({"type":"hard_negative_same_evidence_span","passage_id":hid})
        if not reasons:
            best=max(((jaccard(r["query"],q),src,q) for q,src in eq),default=(0.0,"",""),key=lambda x:x[0])
            if best[0]>=threshold: reasons.append({"type":"near_duplicate_query","score":round(best[0],4),"source":best[1]})
        if reasons: excluded.append({"query_id":r["query_id"],"reasons":reasons})
        else: clean.append(r)
    return clean,excluded,sources

def semantic_check(clean,cfg):
    import numpy as np, torch
    from sentence_transformers import SentenceTransformer
    from transformers import BitsAndBytesConfig
    if not torch.cuda.is_available(): raise RuntimeError("CUDA_NOT_AVAILABLE")
    eq,_,_,_,_=extract_eval(cfg); texts=[q for q,_ in eq]
    if not texts:return clean,[]
    mcfg=cfg["model"]; bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    model=SentenceTransformer(mcfg["id"],revision=mcfg["revision"],model_kwargs={"quantization_config":bnb,"device_map":{"":"cuda:0"},"torch_dtype":torch.float16},trust_remote_code=True)
    prompt=mcfg["prompt"]; tq=np.asarray(model.encode([r["query"] for r in clean],prompt=prompt,batch_size=4,normalize_embeddings=True,show_progress_bar=False)); eqe=np.asarray(model.encode(texts,prompt=prompt,batch_size=4,normalize_embeddings=True,show_progress_bar=False))
    sims=tq@eqe.T; threshold=cfg["data"]["semantic_near_duplicate_threshold"]; keep=[]; excluded=[]
    for i,r in enumerate(clean):
        j=int(sims[i].argmax()); score=float(sims[i,j])
        if score>=threshold: excluded.append({"query_id":r["query_id"],"reasons":[{"type":"semantic_near_duplicate","score":round(score,4),"eval_query":texts[j]}]})
        else: keep.append(r)
    del model; torch.cuda.empty_cache(); return keep,excluded

def run(cfg,skip_semantic=False):
    train_path=root_path(cfg["data"]["train_output"]); train=json.loads(train_path.read_text(encoding="utf-8")); before=sha256_file(train_path)
    clean,excluded,sources=lexical_firewall(train,cfg)
    semantic_ex=[]
    if not skip_semantic: clean,semantic_ex=semantic_check(clean,cfg); excluded.extend(semantic_ex)
    from qwen4b_adaptation_common import atomic_json
    clean_sha=atomic_json(train_path,clean)
    report={"status":"PASS" if clean else "FAIL","input_n":len(train),"clean_n":len(clean),"excluded_n":len(excluded),"excluded":excluded,"eval_sources":sources,"input_train_sha256":before,"train_sha256":clean_sha,"semantic_check":"SKIPPED" if skip_semantic else "QWEN4B_COSINE"}
    atomic_json(root_path(cfg["data"]["firewall_report"]),report)
    if not clean: raise RuntimeError("FIREWALL_REMOVED_ALL_TRAIN_ITEMS")
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config"); ap.add_argument("--skip-semantic",action="store_true"); a=ap.parse_args(); print(json.dumps(run(load_config(a.config),a.skip_semantic),indent=2))
if __name__=="__main__": main()
