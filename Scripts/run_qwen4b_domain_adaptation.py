from __future__ import annotations
import argparse, importlib, json, os, platform, shutil, subprocess, sys
from pathlib import Path
from qwen4b_adaptation_common import ROOT, load_config, root_path, verify_product_dev_sha, atomic_json

def require_cuda(torch):
    if not torch.cuda.is_available():
        print('CUDA_NOT_AVAILABLE')
        raise SystemExit(85)

def env_report(cfg):
    import torch
    if not (sys.version_info[:2] >= (3,11) and sys.version_info[:2] < (3,13)):
        raise RuntimeError(f'UNSUPPORTED_PYTHON {platform.python_version()}')
    require_cuda(torch)
    missing=[]; versions={'torch':getattr(torch,'__version__','unknown')}
    for name in ('transformers','sentence_transformers','bitsandbytes','peft','accelerate','psutil','safetensors'):
        try:
            m=importlib.import_module(name); versions[name]=getattr(m,'__version__','unknown')
        except Exception as e: missing.append(f'{name}: {e}')
    if missing: raise RuntimeError('MISSING_DEPENDENCIES\n'+'\n'.join(missing))
    gpu=torch.cuda.get_device_name(0); prop=torch.cuda.get_device_properties(0); disk=shutil.disk_usage(ROOT)
    if prop.total_memory < 5*2**30: raise RuntimeError(f'INSUFFICIENT_GPU_VRAM {prop.total_memory/2**30:.2f} GiB')
    product_sha=verify_product_dev_sha(cfg)
    return {'python':platform.python_version(),'versions':versions,'cuda_available':True,'cuda_version':torch.version.cuda,'gpu':gpu,'vram_total_gb':round(prop.total_memory/2**30,2),'disk_free_gb':round(disk.free/2**30,2),'product_dev_v3_sha256':product_sha,'model_id':cfg['model']['id'],'model_revision':cfg['model']['revision'],'tokenizer_revision':cfg['model']['tokenizer_revision']}

def run(script,cfg,*extra):
    cmd=[sys.executable,str(ROOT/'Scripts'/script),'--config',str(ROOT/'configs'/'qwen4b_domain_adaptation.json'),*extra]
    print('\n>>>',' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config'); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(); cfg=load_config(a.config)
    out=root_path(cfg['outputs']['root']); out.mkdir(parents=True,exist_ok=True)
    if a.dry_run:
        print(json.dumps({'status':'DRY_RUN_OK','model':cfg['model'],'train_source':cfg['data']['source_pool'],'product_dev_v3':cfg['data']['product_dev_v3']},indent=2)); return
    rep=env_report(cfg); atomic_json(out/'environment_report.json',rep); print(json.dumps(rep,indent=2))
    run('build_qwen4b_retrieval_train.py',cfg)
    run('validate_qwen4b_train_firewall.py',cfg)
    fw=json.loads(root_path(cfg['data']['firewall_report']).read_text(encoding='utf-8'))
    if fw['status']!='PASS': raise RuntimeError('LEAKAGE_FIREWALL_FAILED')
    run('train_qwen4b_retrieval_lora.py',cfg)
    run('evaluate_qwen4b_adapted_product_dev_v3.py',cfg)
    gate=json.loads(root_path(cfg['outputs']['gate_result']).read_text(encoding='utf-8'))
    print('\n'+'='*72); print(gate['status'])
    if gate['passed']: print('NEXT_SCIENTIFIC_STATE=QWEN3_RERANKER_4B_CANDIDATE_STAGE')
    else: print('NEXT_SCIENTIFIC_STATE=RETRIEVAL_RESIDUAL_FAILURE_REVIEW_NO_ARCHITECTURE_CHANGE')
if __name__=='__main__': main()
