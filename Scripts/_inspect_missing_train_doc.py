import json
from pathlib import Path

# Load registry
with open('Data/metadata/renal_source_registry_v2.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)

active_docs = {d['document_id']: d for d in reg.get('documents', []) if d.get('v2_active')}
print(f"Active docs in registry: {len(active_docs)}")

# Load extended train
with open('evaluation/renal/v5/renal-rerank-train-v5-extended.json', 'r', encoding='utf-8') as f:
    train_ext = json.load(f)

train_docs = set(item['gold_doc_id'] for item in train_ext)
print(f"Docs in extended train: {len(train_docs)}")

missing_from_train = set(active_docs.keys()) - train_docs
print(f"Missing doc(s) from train: {missing_from_train}")
for doc_id in missing_from_train:
    d = active_docs[doc_id]
    print(f"Doc {doc_id}: title='{d['title']}', type={d.get('evidence_type')}, class={d.get('educational_classification')}, topics={d.get('topic_tags')}")
