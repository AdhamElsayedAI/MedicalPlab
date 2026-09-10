"""Print registry summary."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

reg = json.loads((ROOT / 'Data/metadata/renal_source_registry_v2.json').read_text())
print('Registry ID:', reg.get('registry_id'))
docs = reg.get('documents', [])
print('Documents total:', len(docs))
active = [d for d in docs if d.get('v2_active', True)]
print('V2 active:', len(active))
print()
for d in active:
    doc_id = d.get('document_id', '?')
    title = d.get('title', '?')[:55]
    lic = d.get('license_name') or d.get('license', '?')
    role = d.get('educational_classification', '?')
    print(f"  {doc_id}: {title}  lic={lic} role={role}")
