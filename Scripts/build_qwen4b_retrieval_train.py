from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path
from qwen4b_adaptation_common import load_config, root_path, resolve_corpus_dir, load_chunks, atomic_json, sha256_file, jaccard

FORBIDDEN_SOURCE_TOKENS=("product_dev","heldout","ood","external-eval","final_product","select-val","selector-validation","safety-test")
INTENTS={
 "screening":("screen","screening"),"confirmatory_diagnosis":("confirm","biopsy","diagnos"),"risk_factor":("risk","predispos"),
 "treatment":("treat","therapy","drug","dialysis"),"prevention":("prevent","prophyl"),"contraindication":("contraindicat","avoid"),
}

def _intent(text:str)->set[str]:
    t=text.lower(); return {k for k,words in INTENTS.items() if any(w in t for w in words)}
def _numbers(text:str)->set[str]: return set(re.findall(r"\b\d+(?:\.\d+)?\b",text))
def _units(text:str)->set[str]: return set(re.findall(r"\b(?:mg|g|kg|ml|l|mmol/l|mg/dl|mmhg|ml/min|%|cm|mm)\b",text.lower()))

def negative_category(item:dict, pos:dict, cand:dict, cand_owner:dict|None)->str:
    qclaim=f"{item.get('query','')} {item.get('canonical_claim','')}"; ctext=cand.get("text","")
    if cand.get("document_id")==pos.get("document_id"):
        if cand.get("section_path")==pos.get("section_path"): return "same_section_wrong_claim"
        return "same_document_wrong_proposition"
    qi,ci=_intent(qclaim),_intent(ctext)
    pairs=[("screening","confirmatory_diagnosis","screening_vs_confirmatory_diagnosis"),("confirmatory_diagnosis","risk_factor","diagnosis_vs_risk_factor"),("treatment","prevention","treatment_vs_prevention"),("treatment","contraindication","treatment_vs_contraindication")]
    for a,b,label in pairs:
        if (a in qi and b in ci) or (b in qi and a in ci): return label
    qn,cn=_numbers(qclaim),_numbers(ctext); qu,cu=_units(qclaim),_units(ctext)
    if qn and cn and qn!=cn and (qu&cu): return "correct_concept_wrong_numeric_threshold"
    if qn&cn and qu and cu and not (qu&cu): return "correct_number_wrong_unit"
    if cand_owner and cand_owner.get("curriculum_stratum")==item.get("curriculum_stratum"):
        if jaccard(qclaim,ctext)>=0.18: return "lexical_false_friend"
        return "semantic_false_friend"
    if any(w in qclaim.lower() for w in ("drug","medication","therapy")) and any(w in ctext.lower() for w in ("mg","tablet","drug","therapy")): return "correct_disease_wrong_drug"
    return "same_disease_different_clinical_question"

def build(cfg:dict)->dict:
    src=root_path(cfg["data"]["source_pool"])
    if any(tok in src.name.lower() for tok in FORBIDDEN_SOURCE_TOKENS): raise RuntimeError("FORBIDDEN_EVALUATION_SOURCE_FOR_TRAIN")
    items=json.loads(src.read_text(encoding="utf-8")); required=cfg["data"]["required_source_status"]
    items=[x for x in items if x.get("verification_status")==required]
    if not items: raise RuntimeError("NO_VERIFIED_SAFE_UNSPENT_SOURCE_ITEMS")
    chunks,ordered=load_chunks(resolve_corpus_dir(cfg))
    owner={cid:x for x in items for cid in x.get("gold_chunk_ids",[]) }
    out=[]; category_counts=Counter()
    for x in items:
        golds=[c for c in x.get("gold_chunk_ids",[]) if c in chunks]
        if not golds: continue
        pid=golds[0]; pos=chunks[pid]
        span=re.sub(r"\s+"," ",x.get("evidence_span_text","").lower()).strip(); ptxt=re.sub(r"\s+"," ",pos.get("text","").lower())
        if span and span not in ptxt: continue
        candidates=[]
        for cid in ordered:
            if cid in golds: continue
            c=chunks[cid]
            score=jaccard(f"{x.get('query','')} {x.get('canonical_claim','')}",c.get("text",""))
            same_doc=c.get("document_id")==pos.get("document_id"); same_sec=same_doc and c.get("section_path")==pos.get("section_path")
            candidates.append((1 if same_sec else 0,1 if same_doc else 0,score,cid))
        candidates.sort(reverse=True)
        selected=[]; seen_cat=set()
        for _,__,___,cid in candidates:
            c=chunks[cid]; cat=negative_category(x,pos,c,owner.get(cid))
            if cat in seen_cat and len(selected)<2: continue
            selected.append((cid,c,cat)); seen_cat.add(cat); category_counts[cat]+=1
            if len(selected)>=4: break
        if not selected: continue
        rec={
          "query_id":x["query_id"],"query":x["query"],"positive_passage_id":pid,"positive_passage":pos["text"],
          "document_id":pos.get("document_id") or x.get("source_document_id"),"document_title":pos.get("document_title") or x.get("source_document_id"),
          "section_path":pos.get("section_path") or x.get("parent_section_path",[]),"claim_family":x.get("query_family") or x.get("canonical_claim"),
          "atomic_claim":x.get("canonical_claim"),"source_family":x.get("source","V5_TRAIN_CLEAN_V1"),"split_group_key":x.get("split_group_key") or x.get("query_family"),
          "hard_negative_ids":[a[0] for a in selected],"hard_negative_passages":[a[1].get("text","") for a in selected],"hard_negative_categories":[a[2] for a in selected],
          "source_evidence_span":x.get("evidence_span_text","")
        }
        out.append(rec)
    if len(out)<8: raise RuntimeError(f"INSUFFICIENT_LEAKAGE_SAFE_SOURCE_POOL_BUILT N={len(out)}")
    output=root_path(cfg["data"]["train_output"]); train_sha=atomic_json(output,out)
    return {"status":"BUILT","n":len(out),"train_sha256":train_sha,"source_pool_sha256":sha256_file(src),"hard_negative_category_counts":dict(category_counts),"output":str(output)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config"); args=ap.parse_args(); cfg=load_config(args.config); print(json.dumps(build(cfg),indent=2))
if __name__=="__main__": main()
