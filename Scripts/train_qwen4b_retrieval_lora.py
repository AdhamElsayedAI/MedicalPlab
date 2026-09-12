from __future__ import annotations
import argparse, gc, json, math, os, platform, random, shutil, time, traceback
from collections.abc import Mapping
from pathlib import Path
import numpy as np
from qwen4b_adaptation_common import load_config, root_path, atomic_json, sha256_file, sha256_tree

def _imports():
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import BitsAndBytesConfig
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training, PeftModel
    return torch,SentenceTransformer,BitsAndBytesConfig,LoraConfig,TaskType,get_peft_model,prepare_model_for_kbit_training,PeftModel

def _require_peft_model(st):
    from peft import PeftModel
    direct=getattr(st[0],'auto_model',None)
    if isinstance(direct,PeftModel): return direct
    found=[]
    for module in st.modules():
        if isinstance(module,PeftModel) and all(module is not x for x in found): found.append(module)
    if len(found)!=1:
        raise RuntimeError(f'PEFT_WRAPPER_NOT_FOUND_OR_AMBIGUOUS count={len(found)} direct_type={type(direct).__name__}')
    return found[0]

def _verify_peft_adapter_dir(path:Path):
    path=Path(path)
    cfg=path/'adapter_config.json'
    weights=[path/'adapter_model.safetensors',path/'adapter_model.bin']
    if not cfg.is_file(): raise RuntimeError(f'PEFT_ADAPTER_CONFIG_MISSING path={path}')
    existing=[p for p in weights if p.is_file()]
    if len(existing)!=1: raise RuntimeError(f'PEFT_ADAPTER_WEIGHTS_INVALID path={path} count={len(existing)}')
    return path

def _save_peft_adapter(st,path:Path):
    from peft import PeftModel
    path=Path(path); shutil.rmtree(path,ignore_errors=True)
    peft_model=_require_peft_model(st)
    adapter_names=list(peft_model.peft_config.keys())
    if adapter_names!=['default']:
        raise RuntimeError(f'UNEXPECTED_PEFT_ADAPTER_NAMES names={adapter_names}')
    PeftModel.save_pretrained(
        peft_model,
        str(path),
        safe_serialization=True,
        selected_adapters=['default'],
        save_embedding_layers=False,
    )
    return _verify_peft_adapter_dir(path)

def load_model(cfg, adapter:Path|None=None, trainable=True):
    torch,ST,BnB,LoraConfig,TaskType,get_peft,prepare,PeftModel=_imports(); m=cfg['model']
    bnb=BnB(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    st=ST(m['id'],revision=m['revision'],model_kwargs={'quantization_config':bnb,'device_map':{'':'cuda:0'},'torch_dtype':torch.float16},trust_remote_code=True)
    st.max_seq_length=int(m['max_seq_length']); base=st[0].auto_model; base.config.use_cache=False
    if trainable:
        base=prepare(base,use_gradient_checkpointing=True)
        if hasattr(base,'gradient_checkpointing_enable'): base.gradient_checkpointing_enable()
    if adapter:
        adapter=_verify_peft_adapter_dir(Path(adapter))
        base=PeftModel.from_pretrained(base,str(adapter),is_trainable=trainable)
    else:
        lc=LoraConfig(r=int(m['lora']['r']),lora_alpha=int(m['lora']['alpha']),lora_dropout=float(m['lora']['dropout']),bias=m['lora']['bias'],target_modules=m['lora']['target_modules'],task_type=TaskType.FEATURE_EXTRACTION)
        base=get_peft(base,lc)
    st[0].auto_model=base; st.train(trainable)
    _require_peft_model(st)
    return st

def _move_features_to_device(value,device):
    import torch
    if torch.is_tensor(value): return value.to(device)
    if isinstance(value,Mapping): return {k:_move_features_to_device(v,device) for k,v in value.items()}
    if isinstance(value,list): return [_move_features_to_device(v,device) for v in value]
    if isinstance(value,tuple): return tuple(_move_features_to_device(v,device) for v in value)
    return value

def _preprocess_features(st,text,query,cfg):
    prompt=cfg['model']['prompt'] if query else None
    if hasattr(st,'preprocess'):
        feats=st.preprocess([text],prompt=prompt)
    else:
        if prompt: text=prompt+text
        feats=st.tokenize([text])
    if not isinstance(feats,Mapping): raise RuntimeError(f"SENTENCE_TRANSFORMER_PREPROCESS_INVALID type={type(feats).__name__}")
    return _move_features_to_device(feats,'cuda:0')

def emb(st,text,query=False,cfg=None):
    import torch
    feats=_preprocess_features(st,text,query,cfg)
    out=st(feats)['sentence_embedding']; return torch.nn.functional.normalize(out.float(),p=2,dim=-1)
def loss_one(st,r,neg_index,cfg):
    import torch
    q=emb(st,r['query'],True,cfg); p=emb(st,r['positive_passage'],False,cfg); n=emb(st,r['hard_negative_passages'][neg_index%len(r['hard_negative_passages'])],False,cfg)
    logits=torch.cat([(q*p).sum(-1,keepdim=True),(q*n).sum(-1,keepdim=True)],dim=1)/float(cfg['training']['temperature'])
    loss=torch.nn.functional.cross_entropy(logits,torch.zeros(1,dtype=torch.long,device='cuda:0'))
    return loss,float(logits[0,0].detach()),float(logits[0,1].detach()),q,p,n

def gpu_snapshot(torch):
    prop=torch.cuda.get_device_properties(0)
    return {'gpu':torch.cuda.get_device_name(0),'vram_total_mb':round(prop.total_memory/2**20,1),'peak_allocated_mb':round(torch.cuda.max_memory_allocated()/2**20,1),'peak_reserved_mb':round(torch.cuda.max_memory_reserved()/2**20,1)}
def blocker(cfg,exc,trainable=0):
    import torch
    rep={'status':'LOCAL_GPU_MEMORY_BLOCKER_CONFIRMED','error':repr(exc),'traceback':traceback.format_exc(),'base_model':cfg['model']['id'],'base_revision':cfg['model']['revision'],'quantization':cfg['model']['quantization'],'lora':cfg['model']['lora'],'micro_batch_size':cfg['training']['micro_batch_size'],'sequence_length':cfg['model']['max_seq_length'],'gradient_accumulation':cfg['training']['gradient_accumulation_steps'],'trainable_parameter_count':trainable}
    if torch.cuda.is_available(): rep.update(gpu_snapshot(torch))
    atomic_json(root_path(cfg['outputs']['training_report']),rep); print('LOCAL_GPU_MEMORY_BLOCKER_CONFIRMED'); return 86

def sanity(cfg,train):
    import torch
    torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(); st=load_model(cfg,trainable=True)
    trainable=[(n,p) for n,p in st.named_parameters() if p.requires_grad]; names=[n for n,_ in trainable]
    if not trainable or any('lora_' not in n for n in names): raise RuntimeError('UNINTENDED_TRAINABLE_PARAMETERS')
    peft_model=_require_peft_model(st); candidates=[peft_model,getattr(peft_model,'base_model',None),getattr(getattr(peft_model,'base_model',None),'model',None)]
    if not any(bool(getattr(x,'is_loaded_in_4bit',False)) for x in candidates if x is not None): raise RuntimeError('EXPECTED_4BIT_QUANTIZATION_NOT_ACTIVE')
    if not any(('q_proj' in n or 'v_proj' in n) and 'lora_' in n for n in names): raise RuntimeError('EXPECTED_LORA_TARGETS_NOT_ATTACHED')
    trainable_count=sum(p.numel() for _,p in trainable)
    opt=torch.optim.AdamW([p for _,p in trainable],lr=float(cfg['training']['learning_rate']))
    r=train[0]; vals=[]
    for i in range(2):
        opt.zero_grad(set_to_none=True); loss,ps,ns,q,p,n=loss_one(st,r,i,cfg)
        if not torch.isfinite(loss): raise RuntimeError('NONFINITE_SANITY_LOSS')
        loss.backward(); grads=[p.grad for _,p in trainable if p.grad is not None]
        if not grads or not all(torch.isfinite(g).all() for g in grads): raise RuntimeError('NONFINITE_SANITY_GRADIENT')
        if not all(torch.isfinite(x).all() for x in (q,p,n)): raise RuntimeError('NONFINITE_SANITY_EMBEDDING')
        opt.step(); vals.append({'loss':float(loss.detach()),'positive_logit':ps,'negative_logit':ns})
    with torch.no_grad(): _,ps,ns,*_=loss_one(st,r,0,cfg)
    if not ps>ns: raise RuntimeError(f'SANITY_DISCRIMINATION_FAILED positive={ps} negative={ns}')
    tmp=root_path(cfg['outputs']['root'])/'sanity_adapter_tmp'; _save_peft_adapter(st,tmp)
    adapter_sha=sha256_tree(tmp); snap=gpu_snapshot(torch); del st,opt,trainable; gc.collect(); torch.cuda.empty_cache()
    reload_st=load_model(cfg,tmp,trainable=False)
    with torch.no_grad(): e=emb(reload_st,r['query'],True,cfg)
    if not torch.isfinite(e).all(): raise RuntimeError('NONFINITE_RELOADED_EMBEDDING')
    del reload_st; gc.collect(); torch.cuda.empty_cache(); shutil.rmtree(tmp,ignore_errors=True)
    rep={'status':'PASS','cuda_active':True,'model_id':cfg['model']['id'],'revision':cfg['model']['revision'],'tokenizer_revision':cfg['model']['tokenizer_revision'],'quantization':cfg['model']['quantization'],'lora':cfg['model']['lora'],'trainable_parameter_count':trainable_count,'only_lora_trainable':True,'steps':vals,'post_step_positive_logit':ps,'post_step_negative_logit':ns,'save_reload_verified':True,'sanity_adapter_sha256':adapter_sha,**snap}
    atomic_json(root_path(cfg['outputs']['sanity_report']),rep); return rep

def split_grouped(train,cfg):
    import hashlib
    groups={}
    for r in train: groups.setdefault(r.get('split_group_key') or r['claim_family'],[]).append(r)
    ordered=sorted(groups,key=lambda g:hashlib.sha256((str(cfg['seed'])+g).encode()).hexdigest()); nval=max(1,round(len(ordered)*float(cfg['training']['validation_fraction'])))
    vg=set(ordered[:nval]); return [r for r in train if (r.get('split_group_key') or r['claim_family']) not in vg],[r for r in train if (r.get('split_group_key') or r['claim_family']) in vg]
def checkpoint(st,opt,state,cfg):
    base=root_path(cfg['outputs']['checkpoints']); base.mkdir(parents=True,exist_ok=True); dst=base/f"checkpoint-step-{state['optimizer_step']:06d}"; tmp=base/(dst.name+'.tmp'); shutil.rmtree(tmp,ignore_errors=True); tmp.mkdir()
    _save_peft_adapter(st,tmp/'adapter'); import torch; torch.save(opt.state_dict(),tmp/'optimizer.pt'); atomic_json(tmp/'trainer_state.json',state); (tmp/'COMPLETE').write_text('ok\n')
    if dst.exists(): shutil.rmtree(dst)
    os.replace(tmp,dst)
    return dst
def latest_checkpoint(cfg):
    base=root_path(cfg['outputs']['checkpoints']); cands=sorted([p for p in base.glob('checkpoint-step-*') if (p/'COMPLETE').exists() and (p/'adapter'/'adapter_config.json').is_file()]) if base.exists() else []; return cands[-1] if cands else None

def train_full(cfg,train):
    import torch
    random.seed(cfg['seed']); np.random.seed(cfg['seed']); torch.manual_seed(cfg['seed']); torch.cuda.manual_seed_all(cfg['seed']); torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
    tr,val=split_grouped(train,cfg); ck=latest_checkpoint(cfg); state={'micro_step':0,'optimizer_step':0,'epoch':0}
    st=load_model(cfg,ck/'adapter' if ck else None,trainable=True); params=[p for p in st.parameters() if p.requires_grad]; trainable_count=sum(p.numel() for p in params); opt=torch.optim.AdamW(params,lr=float(cfg['training']['learning_rate']),weight_decay=float(cfg['training']['weight_decay']))
    if ck:
        state=json.loads((ck/'trainer_state.json').read_text()); opt.load_state_dict(torch.load(ck/'optimizer.pt',map_location='cuda:0'))
    order=list(range(len(tr))); random.Random(cfg['seed']).shuffle(order); start=state['micro_step']; accum=int(cfg['training']['gradient_accumulation_steps']); opt.zero_grad(set_to_none=True); losses=[]; t0=time.perf_counter()
    for micro in range(start,len(order)):
        r=tr[order[micro]]; loss,*_=loss_one(st,r,micro,cfg); (loss/accum).backward(); losses.append(float(loss.detach())); state['micro_step']=micro+1
        if (micro+1)%accum==0 or micro+1==len(order):
            torch.nn.utils.clip_grad_norm_(params,float(cfg['training']['max_grad_norm'])); opt.step(); opt.zero_grad(set_to_none=True); state['optimizer_step']+=1
            if state['optimizer_step']%int(cfg['training']['checkpoint_every_optimizer_steps'])==0: checkpoint(st,opt,state,cfg)
    state['epoch']=1; final_ck=checkpoint(st,opt,state,cfg); adapter=root_path(cfg['outputs']['adapter']); _save_peft_adapter(st,adapter); adapter_sha=sha256_tree(adapter)
    st.eval(); v=[]
    with torch.no_grad():
        for i,r in enumerate(val): v.append(float(loss_one(st,r,i,cfg)[0]))
    snap=gpu_snapshot(torch); wall=time.perf_counter()-t0; rep={'status':'TRAINING_COMPLETE','train_n':len(tr),'validation_n':len(val),'epochs':1,'optimizer_steps':state['optimizer_step'],'mean_train_loss':float(np.mean(losses)) if losses else None,'mean_validation_loss':float(np.mean(v)) if v else None,'wall_clock_seconds':round(wall,2),'trainable_parameter_count':trainable_count,'adapter_sha256':adapter_sha,'checkpoint_sha256':sha256_tree(final_ck),'checkpoint_path':str(final_ck),'optimizer_state_available':(final_ck/'optimizer.pt').exists(),'adapter_size_bytes':sum(p.stat().st_size for p in adapter.rglob('*') if p.is_file()),'train_sha256':sha256_file(root_path(cfg['data']['train_output'])),'base_model':cfg['model']['id'],'base_revision':cfg['model']['revision'],'tokenizer_revision':cfg['model']['tokenizer_revision'],'config':cfg['training'],**snap}
    atomic_json(root_path(cfg['outputs']['training_report']),rep); return rep

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config'); a=ap.parse_args(); cfg=load_config(a.config)
    import torch
    if not torch.cuda.is_available(): print('CUDA_NOT_AVAILABLE'); raise SystemExit(85)
    train=json.loads(root_path(cfg['data']['train_output']).read_text(encoding='utf-8'))
    try:
        s=sanity(cfg,train); print(json.dumps({'sanity':s['status']},indent=2)); rep=train_full(cfg,train); print(json.dumps(rep,indent=2))
    except (torch.cuda.OutOfMemoryError,RuntimeError) as e:
        if isinstance(e,torch.cuda.OutOfMemoryError) or 'out of memory' in str(e).lower(): raise SystemExit(blocker(cfg,e))
        raise
if __name__=='__main__': main()
