import importlib.util, json, sys
from collections.abc import Mapping
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; S=ROOT/'Scripts'; sys.path.insert(0,str(S))
from qwen4b_adaptation_common import normalize_text, jaccard, canonical_json_bytes, sha256_bytes
from build_qwen4b_retrieval_train import FORBIDDEN_SOURCE_TOKENS, negative_category

def test_product_dev_is_forbidden_as_train_source():
    assert 'product_dev' in FORBIDDEN_SOURCE_TOKENS
    assert any(t in 'product_dev_v3.json' for t in FORBIDDEN_SOURCE_TOKENS)
def test_normalization_and_hash_deterministic():
    assert normalize_text(' CKD:  eGFR < 60 ')=='ckd egfr 60'
    obj=[{'b':2,'a':1}]; assert sha256_bytes(canonical_json_bytes(obj))==sha256_bytes(canonical_json_bytes(obj))
def test_hard_negative_same_document_category():
    item={'query':'How is CKD diagnosed?','canonical_claim':'diagnosis','curriculum_stratum':'STR'}
    pos={'document_id':'D','section_path':['A']}; cand={'document_id':'D','section_path':['B'],'text':'other proposition'}
    assert negative_category(item,pos,cand,None)=='same_document_wrong_proposition'
def test_lexical_similarity_bounds():
    assert jaccard('a kidney disease','kidney disease')==1.0
    assert 0 <= jaccard('dialysis treatment','screening test') <= 1
def test_config_pins_authorized_model_and_revision():
    cfg=json.loads((ROOT/'configs'/'qwen4b_domain_adaptation.json').read_text())
    assert cfg['model']['id']=='Qwen/Qwen3-Embedding-4B'
    assert cfg['model']['revision']=='5cf2132abc99cad020ac570b19d031efec650f2b'
    assert cfg['data']['product_dev_v3_sha256']=='dfed4a3c3ddeaa3b854317089747ce5bd2ad482867195cb0ce14c68620578746'
def test_runner_dry_run_parses_without_cuda():
    import subprocess
    p=subprocess.run([sys.executable,str(S/'run_qwen4b_domain_adaptation.py'),'--dry-run'],cwd=ROOT,text=True,capture_output=True)
    assert p.returncode==0, p.stderr
    assert 'DRY_RUN_OK' in p.stdout

def test_adjacent_chunk_detection():
    from validate_qwen4b_train_firewall import adjacent_ids
    assert 'DOC-X-B-C0004' in adjacent_ids('DOC-X-B-C0005')
    assert 'DOC-X-B-C0006' in adjacent_ids('DOC-X-B-C0005')

def test_report_schema_accepts_minimal_valid_shape():
    import jsonschema
    schema=json.loads((ROOT/'schemas'/'qwen4b_domain_adaptation_report.schema.json').read_text())
    sample={'benchmark':'PRODUCT_DEV_V3','n_queries':100,'product_dev_v3_sha256':'a'*64,'base_model':'Qwen/Qwen3-Embedding-4B','base_revision':'b'*40,'adapter_sha256':'c'*64,'train_sha256':'d'*64,'before':{},'after':{},'performance':{},'gate':{'status':'RETRIEVAL_DEVELOPMENT_GATE_FAILED','passed':False,'thresholds':{}}}
    jsonschema.validate(sample,schema)

def test_latest_checkpoint_requires_complete_marker(tmp_path):
    from train_qwen4b_retrieval_lora import latest_checkpoint
    base=tmp_path/'checkpoints'; (base/'checkpoint-step-000001').mkdir(parents=True); good=base/'checkpoint-step-000002'; good.mkdir(); (good/'COMPLETE').write_text('ok')
    cfg={'outputs':{'checkpoints':str(base)}}
    assert latest_checkpoint(cfg)==good

def test_mocked_no_gpu_path_is_hard_stop(capsys):
    from run_qwen4b_domain_adaptation import require_cuda
    class Cuda:
        @staticmethod
        def is_available(): return False
    class FakeTorch: cuda=Cuda()
    import pytest
    with pytest.raises(SystemExit) as e: require_cuda(FakeTorch())
    assert e.value.code==85
    assert 'CUDA_NOT_AVAILABLE' in capsys.readouterr().out

def test_builder_synthetic_source_grounded_pipeline(tmp_path, monkeypatch):
    import build_qwen4b_retrieval_train as b
    source=tmp_path/'train.json'; corpus=tmp_path/'corpus'; corpus.mkdir()
    source.write_text(json.dumps([
      {'query_id':'T1','query':'What is the CKD hallmark?','canonical_claim':'decreased filtration','source_document_id':'D1','parent_section_path':['Intro'],'evidence_span_text':'decreased filtration','gold_chunk_ids':['D1-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF1','split_group_key':'G1','source':'TRAIN'},
      {'query_id':'T2','query':'What transporter is present?','canonical_claim':'transporter x','source_document_id':'D2','parent_section_path':['Sec'],'evidence_span_text':'transporter x','gold_chunk_ids':['D2-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF2','split_group_key':'G2','source':'TRAIN'},
      {'query_id':'T3','query':'What causes acidosis?','canonical_claim':'acid retention','source_document_id':'D3','parent_section_path':['Sec'],'evidence_span_text':'acid retention','gold_chunk_ids':['D3-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF3','split_group_key':'G3','source':'TRAIN'},
      {'query_id':'T4','query':'How is sodium handled?','canonical_claim':'sodium handling','source_document_id':'D4','parent_section_path':['Sec'],'evidence_span_text':'sodium handling','gold_chunk_ids':['D4-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF4','split_group_key':'G4','source':'TRAIN'},
      {'query_id':'T5','query':'What raises potassium?','canonical_claim':'potassium rises','source_document_id':'D5','parent_section_path':['Sec'],'evidence_span_text':'potassium rises','gold_chunk_ids':['D5-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF5','split_group_key':'G5','source':'TRAIN'},
      {'query_id':'T6','query':'What lowers GFR?','canonical_claim':'GFR falls','source_document_id':'D6','parent_section_path':['Sec'],'evidence_span_text':'GFR falls','gold_chunk_ids':['D6-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF6','split_group_key':'G6','source':'TRAIN'},
      {'query_id':'T7','query':'What treats edema?','canonical_claim':'diuretic treatment','source_document_id':'D7','parent_section_path':['Sec'],'evidence_span_text':'diuretic treatment','gold_chunk_ids':['D7-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF7','split_group_key':'G7','source':'TRAIN'},
      {'query_id':'T8','query':'What prevents stones?','canonical_claim':'stone prevention','source_document_id':'D8','parent_section_path':['Sec'],'evidence_span_text':'stone prevention','gold_chunk_ids':['D8-B-C0001'],'verification_status':'VERIFIED_SAFE_UNSPENT','query_family':'QF8','split_group_key':'G8','source':'TRAIN'}
    ]))
    chunks=[]
    for i in range(1,9): chunks.append({'chunk_id':f'D{i}-B-C0001','document_id':f'D{i}','text':['decreased filtration','transporter x','acid retention','sodium handling','potassium rises','GFR falls','diuretic treatment','stone prevention'][i-1],'section_path':['Sec']})
    (corpus/'all.chunks.json').write_text(json.dumps({'document_id':'MULTI','chunks':chunks}))
    output=tmp_path/'out.json'; cfg={'data':{'source_pool':str(source),'required_source_status':'VERIFIED_SAFE_UNSPENT','train_output':str(output)}}
    monkeypatch.setattr(b,'resolve_corpus_dir',lambda cfg:corpus)
    rep=b.build(cfg)
    assert rep['n']==8
    data=json.loads(output.read_text()); assert all(r['hard_negative_ids'] for r in data)

def test_qwen4b_feature_device_move_preserves_non_tensor_metadata():
    import torch
    from train_qwen4b_retrieval_lora import _move_features_to_device
    features={
        'input_ids':torch.tensor([[1,2,3]]),
        'attention_mask':torch.tensor([[1,1,1]]),
        'modality':'text',
        'nested':{'task':'retrieval','tensor':torch.tensor([1])},
        'labels':['a','b'],
    }
    moved=_move_features_to_device(features,'cpu')
    assert moved['input_ids'].device.type=='cpu'
    assert moved['attention_mask'].device.type=='cpu'
    assert moved['modality']=='text'
    assert moved['nested']['task']=='retrieval'
    assert moved['nested']['tensor'].device.type=='cpu'
    assert moved['labels']==['a','b']

def test_qwen4b_preprocess_path_preserves_metadata_and_query_prompt(monkeypatch):
    import torch
    import train_qwen4b_retrieval_lora as t
    calls={}
    class FakeST:
        def preprocess(self,texts,prompt=None):
            calls['texts']=texts; calls['prompt']=prompt
            return {'input_ids':torch.tensor([[1]]),'modality':'text'}
    monkeypatch.setattr(t,'_move_features_to_device',lambda value,device:value)
    cfg={'model':{'prompt':'PROMPT: '}}
    out=t._preprocess_features(FakeST(),'kidney query',True,cfg)
    assert calls=={'texts':['kidney query'],'prompt':'PROMPT: '}
    assert out['modality']=='text'

def test_qwen4b_preprocess_accepts_batchencoding_like_mapping(monkeypatch):
    import torch
    import train_qwen4b_retrieval_lora as t
    class BatchEncodingLike(Mapping):
        def __init__(self,data): self.data=data
        def __getitem__(self,key): return self.data[key]
        def __iter__(self): return iter(self.data)
        def __len__(self): return len(self.data)
    class FakeST:
        def preprocess(self,texts,prompt=None):
            return BatchEncodingLike({'input_ids':torch.tensor([[1,2]]),'attention_mask':torch.tensor([[1,1]]),'modality':'text'})
    monkeypatch.setattr(t,'_move_features_to_device',lambda value,device:dict(value))
    out=t._preprocess_features(FakeST(),'kidney query',False,{'model':{'prompt':'PROMPT: '}})
    assert out['modality']=='text'
    assert out['input_ids'].shape==(1,2)
