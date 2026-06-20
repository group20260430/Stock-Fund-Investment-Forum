import os, pathlib, sys

os.environ['DATABASE_URL'] = 'sqlite:///./test_e2e.db'

pathlib.Path('test_e2e.db').unlink(missing_ok=True)

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401
Base.metadata.create_all(bind=engine)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

passed = 0
failed = 0

def check(label, expect, response, show_key=None):
    global passed, failed
    j = response.json()
    ok = response.status_code == expect
    if ok:
        passed += 1
        marker = "OK"
    else:
        failed += 1
        marker = "FAIL"
    msg = j.get('message', j.get('detail', ''))
    print(f'{marker} | {label}: HTTP {response.status_code} | {msg}')
    if not ok:
        print(f'     EXPECTED {expect}, GOT {response.status_code}')
        print(f'     Full response: {j}')
    if show_key and ok and 'data' in j:
        d = j['data']
        if isinstance(d, dict) and show_key in d:
            print(f'     {show_key}={d[show_key]}')
    return j

# 1. Health
r = client.get('/api/health')
check('1. Health', 200, r)

# 2. Register
r = client.post('/api/auth/register', json={
    'phone': '13800138000', 'password': 'Abc@123456', 'nickname': 'test_user'
})
j = check('2. Register', 201, r, 'user_id')
reg = j['data']
access = reg['token']
refresh = reg['refresh_token']

# 3. Duplicate
r = client.post('/api/auth/register', json={
    'phone': '13800138000', 'password': 'Abc@123456'
})
check('3. Dup Reg', 409, r)

# 4. Login
r = client.post('/api/auth/login', json={
    'phone': '13800138000', 'password': 'Abc@123456', 'login_type': 'password'
})
check('4. Login', 200, r)

# 5. Wrong password
r = client.post('/api/auth/login', json={
    'phone': '13800138000', 'password': 'WrongPw1', 'login_type': 'password'
})
check('5. Bad pw', 401, r)

# 6. Get me
r = client.get('/api/auth/me', headers={'Authorization': f'Bearer {access}'})
check('6. Me', 200, r)

# 7. Update profile
r = client.put('/api/auth/profile', json={
    'nickname': 'new_nick', 'bio': 'hello bio'
}, headers={'Authorization': f'Bearer {access}'})
check('7. Update', 200, r)

# 8. Refresh
r = client.post('/api/auth/refresh', headers={'Authorization': f'Bearer {refresh}'})
check('8. Refresh', 200, r)

# 9. Certification
r = client.post('/api/auth/certification', json={
    'id_card_front': 'base64_front_mock', 'id_card_back': 'base64_back_mock',
    'real_name': 'Zhang San', 'id_number': '110101199001011234'
}, headers={'Authorization': f'Bearer {access}'})
check('9. Cert', 200, r)

# 10. Risk assessment
r = client.post('/api/auth/risk-assessment', json={
    'answers': [
        {'question_id': 1, 'answer': 'C'}, {'question_id': 2, 'answer': 'D'},
        {'question_id': 3, 'answer': 'B'}, {'question_id': 4, 'answer': 'A'},
        {'question_id': 5, 'answer': 'E'}
    ]
}, headers={'Authorization': f'Bearer {access}'})
check('10. Risk', 200, r)

# 10b. Get risk questions (authenticated)
r = client.get('/api/auth/risk-assessment/questions',
               headers={'Authorization': f'Bearer {access}'})
j = check('10b. Get Qs', 200, r)
if r.status_code == 200 and 'data' in j:
    q_count = len(j['data']) if isinstance(j['data'], list) else 'N/A'
    print(f'     questions returned: {q_count}')

# 10c. Get risk questions (unauthenticated)
r = client.get('/api/auth/risk-assessment/questions')
check('10c. Get Qs noauth', 403, r)

# 10d. Risk assessment with invalid answer
r = client.post('/api/auth/risk-assessment', json={
    'answers': [
        {'question_id': 1, 'answer': 'X'},
        {'question_id': 2, 'answer': 'C'}
    ]
}, headers={'Authorization': f'Bearer {access}'})
check('10d. Bad answer', 400, r)

# 10e. Risk assessment with mismatched total_questions
r = client.post('/api/auth/risk-assessment', json={
    'answers': [
        {'question_id': 1, 'answer': 'A'},
        {'question_id': 2, 'answer': 'B'}
    ],
    'total_questions': 15
}, headers={'Authorization': f'Bearer {access}'})
check('10e. Mismatch', 400, r)

# 10f. Risk assessment with total_questions field (full 15 questions)
full_answers = [{'question_id': i, 'answer': chr(65 + (i % 5))} for i in range(1, 16)]
r = client.post('/api/auth/risk-assessment', json={
    'answers': full_answers,
    'total_questions': 15
}, headers={'Authorization': f'Bearer {access}'})
check('10f. Full assessment', 200, r)

# 10g. Get risk assessment history (should have 2 records now)
r = client.get('/api/auth/risk-assessment/history',
               headers={'Authorization': f'Bearer {access}'})
j = check('10g. History', 200, r)
if r.status_code == 200 and 'data' in j:
    d = j['data']
    if isinstance(d, dict) and 'total' in d:
        print(f'     total records: {d["total"]}')

# 10h. Get risk assessment history with pagination
r = client.get('/api/auth/risk-assessment/history?page=1&size=1',
               headers={'Authorization': f'Bearer {access}'})
j = check('10h. Hist page', 200, r)
if r.status_code == 200 and 'data' in j:
    d = j['data']
    if isinstance(d, dict):
        items = d.get('items', [])
        print(f'     page items: {len(items)}, total: {d.get("total", "N/A")}')

# 11. No token
r = client.get('/api/auth/me')
check('11. No token', 403, r)

# 12. Bad token
r = client.get('/api/auth/me', headers={'Authorization': 'Bearer bad_token_xyz'})
check('12. Bad tok', 401, r)

# 13. Send code
r = client.post('/api/auth/send-code', json={'phone': '13800138001', 'type': 'register'})
check('13. Send code', 200, r)

# 14. Refresh reuse
r = client.post('/api/auth/refresh', headers={'Authorization': f'Bearer {refresh}'})
check('14. Reuse ref', 401, r)

# 15. Profile post-risk
r = client.get('/api/auth/me', headers={'Authorization': f'Bearer {access}'})
check('15. Profile', 200, r)

# Cleanup
engine.dispose()
pathlib.Path('test_e2e.db').unlink(missing_ok=True)

print()
print(f'{"="*50}')
print(f'RESULTS: {passed} passed, {failed} failed')
if failed == 0:
    print('ALL END-TO-END TESTS PASSED')
    sys.exit(0)
else:
    print('SOME TESTS FAILED')
    sys.exit(1)
