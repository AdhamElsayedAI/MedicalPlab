from __future__ import annotations
import argparse, gc, json, math, time
from pathlib import Path
import numpy as np
from qwen4b_adaptation_common import load_config, root_path, resolve_corpus_dir, load_chunks, verify_product_dev_sha, atomic_json, sha256_file, sha256_tree, stat, sha256_bytes, canonical_json_bytes

def dcg(rel): return sum((2**r-1)/math.log2(i+2) for i,r in enumerate(rel))
def ndcg(ids,golds,k=10):
    rel=[1 if x in golds else 0 for x in ids[:k]]; a=dcg(rel); ideal=dcg(sorted(rel,reverse=True)); return a/ideal if ideal else 0.0
def load_adapted(cfg):
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import BitsAndBytesConfig
    from peft import PeftModel
    m=cfg['model']; b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    st=SentenceTransformer(m['id'],revision=m['revision'],model_kwargs={'quantization_config':b,'device_map':{'':'cuda:0'},'torch_dtype':torch.float16},trust_remote_code=True); st.max_seq_length=m['max_seq_length']; st[0].auto_model=PeftModel.from_pretrained(st[0].auto_model,str(root_path(cfg['outputs']['adapter'])),is_trainable=False); st.eval(); return st
def main_eval(cfg):
    import torch, psutil
    if not torch.cuda.is_available(): raise RuntimeError('CUDA_NOT_AVAILABLE')
    product_sha=verify_product_dev_sha(cfg); items=json.loads(root_path(cfg['data']['product_dev_v3']).read_text(encoding='utf-8'))
    if len(items)!=100: raise RuntimeError(f'PRODUCT_DEV_V3_N_MISMATCH {len(items)}')
    chunks,ordered=load_chunks(resolve_corpus_dir(cfg)); st=load_adapted(cfg); prompt=cfg['model']['prompt']
    try:
        from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor
        proc=ClinicalQueryProcessor(); qtexts=[]
        for it in items:
            q=proc.process_query(it['query']); qtexts.append(q.neutral_target or q.canonical_query or q.original_query)
    except Exception:
        qtexts=[it['query'] for it in items]
    corpus=[chunks[c].get('text','') for c in ordered]; torch.cuda.reset_peak_memory_stats(); t0=time.perf_counter(); cemb=np.asarray(st.encode(corpus,batch_size=2,normalize_embeddings=True,show_progress_bar=True),dtype=np.float32); qlat=[]; qrows=[]
    for qt in qtexts:
        q0=time.perf_counter(); qe=st.encode([qt],prompt=prompt,batch_size=1,normalize_embeddings=True,show_progress_bar=False); torch.cuda.synchronize(); qlat.append((time.perf_counter()-q0)*1000.0); qrows.append(qe[0])
    qemb=np.asarray(qrows,dtype=np.float32); eval_start=time.perf_counter()
    depths=[1,5,10,20,50,100,200]; sem={k:0 for k in depths}; exact={k:0 for k in depths}; ranks=[]; mrr=0.; nd=0.; failure_rows=[]
    for it,qv in zip(items,qemb):
        idx=np.argsort(cemb@qv)[::-1]; ids=[ordered[i] for i in idx]; sg=set(it.get('semantic_support_chunk_ids',it.get('exact_gold_chunk_ids',[]))); eg=set(it.get('exact_gold_chunk_ids',[])); rs=next((i for i,c in enumerate(ids,1) if c in sg),None); re=next((i for i,c in enumerate(ids,1) if c in eg),None)
        ranks.append(rs if rs else len(ids)+1); mrr+=0 if rs is None else 1/rs; nd+=ndcg(ids,sg)
        for k in depths:
            sem[k]+=int(rs is not None and rs<=k); exact[k]+=int(re is not None and re<=k)
        if rs is None or rs>50:
            if not sg: cat='CORPUS_COVERAGE'
            elif any(g not in chunks for g in sg): cat='INDEX_OR_CHUNK_REPRESENTATION'
            elif rs and rs<=200: cat='QUERY_REPRESENTATION'
            else: cat='GENUINE_MODEL_SEMANTIC_LIMIT'
            failure_rows.append({'query_id':it['query_id'],'rank':rs,'category':cat})
    n=len(items); after={'semantic_recall':{f'recall_at_{k}':stat(sem[k],n) for k in depths},'exact_recall':{f'recall_at_{k}':stat(exact[k],n) for k in depths},'mrr':round(mrr/n,4),'ndcg_at_10':round(nd/n,4),'rank_distribution':{'median':float(np.median(ranks)),'p75':float(np.percentile(ranks,75)),'p90':float(np.percentile(ranks,90)),'max':int(max(ranks))}}
    base=json.loads(root_path(cfg['data']['baseline_report']).read_text(encoding='utf-8'))['configurations']['DENSE_ONLY']; passed=after['semantic_recall']['recall_at_20']['rate']>=cfg['gate']['semantic_recall_at_20'] and after['semantic_recall']['recall_at_50']['rate']>=cfg['gate']['semantic_recall_at_50']; verdict='RETRIEVAL_DEVELOPMENT_GATE_PASSED' if passed else 'RETRIEVAL_DEVELOPMENT_GATE_FAILED'
    from collections import Counter; tax=Counter(r['category'] for r in failure_rows)
    report={'benchmark':'PRODUCT_DEV_V3','n_queries':n,'product_dev_v3_sha256':product_sha,'base_model':cfg['model']['id'],'base_revision':cfg['model']['revision'],'tokenizer_revision':cfg['model']['tokenizer_revision'],'adapter_sha256':sha256_tree(root_path(cfg['outputs']['adapter'])),'train_sha256':sha256_file(root_path(cfg['data']['train_output'])),'evaluation_config_sha256':sha256_bytes(canonical_json_bytes({'model':cfg['model'],'gate':cfg['gate'],'benchmark_sha':product_sha})),'before':base,'after':after,'performance':{'evaluation_wall_clock_seconds':round(time.perf_counter()-eval_start,2),'corpus_plus_query_encoding_seconds':round(time.perf_counter()-t0,2),'query_latency_p50_ms':round(float(np.percentile(qlat,50)),2),'query_latency_p95_ms':round(float(np.percentile(qlat,95)),2),'peak_vram_allocated_mb':round(torch.cuda.max_memory_allocated()/2**20,1),'peak_vram_reserved_mb':round(torch.cuda.max_memory_reserved()/2**20,1),'system_ram_total_gb':round(psutil.virtual_memory().total/2**30,2)},'gate':{'status':verdict,'passed':passed,'thresholds':cfg['gate']},'residual_failure_taxonomy':{k:{'count':v,'pct_of_failures':round(100*v/max(1,len(failure_rows)),2)} for k,v in tax.items()},'residual_failures':failure_rows}
    atomic_json(root_path(cfg['outputs']['evaluation_report']),report); atomic_json(root_path(cfg['outputs']['gate_result']),report['gate'])
    md=f"# Qwen3-Embedding-4B Domain Adaptation\n\n**Gate:** {verdict}\n\n- Semantic Recall@20: {after['semantic_recall']['recall_at_20']['pct']}\n- Semantic Recall@50: {after['semantic_recall']['recall_at_50']['pct']}\n- MRR: {after['mrr']}\n- nDCG@10: {after['ndcg_at_10']}\n- PRODUCT_DEV_V3 SHA256: `{product_sha}`\n- Adapter SHA256: `{report['adapter_sha256']}`\n"
    root_path(cfg['outputs']['evaluation_markdown']).write_text(md,encoding='utf-8'); print(verdict); return report
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--config'); a=ap.parse_args(); main_eval(load_config(a.config))
