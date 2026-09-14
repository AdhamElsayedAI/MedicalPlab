"""Verification script for MedicalPlab Production Cloud API."""
import sys, os
sys.path.insert(0, os.path.abspath("."))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 1. Health check
h = client.get('/health')
assert h.status_code == 200
print('HEALTH CHECK:', h.json())
assert 'x-process-time-ms' in [k.lower() for k in h.headers.keys()]
print('LATENCY HEADER:', h.headers.get('X-Process-Time-Ms'), 'ms')

# 2. Canonical Evidence Engine Query Endpoint
ev = client.post('/api/v1/evidence/query', json={
    'query': 'glomerular filtration barrier',
    'top_candidates': 5,
    'rerank_top_k': 3,
    'mode': 'UNIVERSITY'
})
assert ev.status_code == 200
ev_data = ev.json()
print('EVIDENCE ENGINE QUERY:', ev_data.get('query'), '| routed docs:', len(ev_data.get('routed_document_ids', [])))
assert len(ev_data.get('candidates', [])) > 0 or len(ev_data.get('routed_document_ids', [])) > 0
print('CANDIDATES / ROUTED:', len(ev_data.get('candidates', [])), len(ev_data.get('routed_document_ids', [])))

# 3. AI Chat Fail-Closed Abstention on Unsupported Query
c_unsupp = client.post('/ai/chat', json={'query': 'What is the stock price of Apple on NASDAQ in 2026?'})
assert c_unsupp.status_code == 200
data_unsupp = c_unsupp.json()
assert data_unsupp.get('abstain') is True
assert data_unsupp.get('intent') == 'abstain'
print('AI CHAT ABSTENTION (UNSUPPORTED):', data_unsupp.get('intent'), '->', data_unsupp.get('abstain_reason'))

# 4. University Learning Track API
uni_subj = client.get('/api/v1/university/subjects')
assert uni_subj.status_code == 200
print('UNIVERSITY SUBJECTS:', uni_subj.json().get('items'))
assert len(uni_subj.json().get('items', [])) > 0

# 5. Student Analytics
sa = client.get('/student/analytics')
assert sa.status_code == 200
print('STUDENT ANALYTICS:', sa.json())

# 6. Student Attempt
att = client.post('/student/attempts', json={'topic': 'Renal physiology', 'is_correct': True, 'time_spent_seconds': 20.0})
assert att.status_code in (200, 201)
print('STUDENT ATTEMPT:', att.json())

# 7. CORS
opt = client.options('/health', headers={'Origin': 'https://medical-plab.vercel.app', 'Access-Control-Request-Method': 'GET'})
assert opt.status_code == 200
assert 'access-control-allow-origin' in opt.headers
print('CORS ORIGIN ALLOWED:', opt.headers.get('access-control-allow-origin'))

print('\n>>> ALL PRODUCTION ENDPOINTS VERIFIED SUCCESSFULLY! <<<')
