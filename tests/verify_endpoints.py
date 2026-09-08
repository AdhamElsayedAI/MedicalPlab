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

# 2. AI Chat
c = client.post('/ai/chat', json={'query': 'STEMI revascularisation window'})
assert c.status_code == 200
data = c.json()
print('AI CHAT (STEMI):', data['explanation'][:100], '...')
assert len(data['citations']) > 0
print('CITATIONS COUNT:', len(data['citations']), [x['title'] for x in data['citations']])

# 3. Pregnancy Safety Interception
s1 = client.post('/ai/chat', json={'query': 'Can I give an ACE inhibitor to a pregnant patient?'})
assert s1.status_code == 200
assert s1.json()['intent'] == 'safety_interception'
print('SAFETY INTERCEPTION 1 (PREGNANCY):', s1.json()['intent'], '->', s1.json()['explanation'][:80], '...')

# 4. Nitrates Safety Interception
s2 = client.post('/ai/chat', json={'query': 'Should I give nitrates in inferior STEMI with RV involvement?'})
assert s2.status_code == 200
assert s2.json()['intent'] == 'safety_interception'
print('SAFETY INTERCEPTION 2 (RV STEMI):', s2.json()['intent'], '->', s2.json()['explanation'][:80], '...')

# 5. Student Analytics
sa = client.get('/student/analytics')
assert sa.status_code == 200
print('STUDENT ANALYTICS:', sa.json())

# 6. Student Attempt
att = client.post('/student/attempts', json={'topic': 'Cardiology', 'is_correct': True, 'time_spent_seconds': 20.0})
assert att.status_code in (200, 201)
print('STUDENT ATTEMPT:', att.json())

# 7. CORS
opt = client.options('/health', headers={'Origin': 'https://medical-plab.vercel.app', 'Access-Control-Request-Method': 'GET'})
assert opt.status_code == 200
assert 'access-control-allow-origin' in opt.headers
print('CORS ORIGIN ALLOWED:', opt.headers.get('access-control-allow-origin'))

print('\n>>> ALL PRODUCTION ENDPOINTS VERIFIED SUCCESSFULLY! <<<')
