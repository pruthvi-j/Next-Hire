import urllib.request
import json
import http.cookiejar
import os
from import_questions import import_questions_from_excel
from database import fetch_all, fetch_one

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
base_url = 'http://127.0.0.1:5000'

print('==================================================')
print('       NEXT HIRE - PHASES 5 & 6 INTEGRATION TEST   ')
print('==================================================')

# Test 1 & 2: Excel Question Import & Count Verification
print('\n--- TEST 1 & 2: Excel Question Import & Count ---')
count_1 = import_questions_from_excel()
print(f'[OK] Questions Imported: {count_1}')
assert count_1 == 75, f'Expected 75 valid questions, got {count_1}'

# Test 3: Duplicate Prevention / Idempotence
print('\n--- TEST 3: Duplicate Prevention & Idempotence ---')
count_2 = import_questions_from_excel()
print(f'[OK] Second Import Result: {count_2} total active questions (No duplicates added)')
assert count_2 == 75, f'Duplicate questions were created! Total count: {count_2}'

# Test 4: Question Filtering by Language and Difficulty
print('\n--- TEST 4: Question Filtering in Database ---')
python_easy = fetch_all("SELECT question_code, language, difficulty, question_text FROM questions WHERE language = 'Python' AND difficulty = 'Easy'")
print(f'[OK] Filtered Python + Easy: {len(python_easy)} questions found')
for q in python_easy[:3]:
    print(f'     [{q["question_code"]}] {q["question_text"][:55]}...')
assert len(python_easy) > 0

sql_questions = fetch_all("SELECT question_code, language, topic, difficulty FROM questions WHERE language = 'SQL'")
print(f'[OK] Filtered SQL Questions: {len(sql_questions)} questions found')
assert len(sql_questions) == 15

# Login candidate for API tests
print('\n--- Candidate Authentication for Interview Session ---')
login_payload = json.dumps({'email': 'priya.sharma@mca.edu', 'password': 'StrongPassword123'}).encode('utf-8')
req = urllib.request.Request(f'{base_url}/api/login', data=login_payload, headers={'Content-Type': 'application/json'})
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] Logged in as: {res["user"]["name"]}')

# Test 5 & 6 & 7: Create Interview, Question Selection, Duplicate Prevention
print('\n--- TEST 5, 6 & 7: Create Interview & Select Questions ---')
start_payload = json.dumps({
    'role_id': 1,               # Python Developer
    'difficulty': 'Medium',
    'num_questions': 5
}).encode('utf-8')
req = urllib.request.Request(f'{base_url}/api/interview/start', data=start_payload, headers={'Content-Type': 'application/json'})
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] Interview Started: HTTP {resp.status}')
    interview_data = res['data']
    interview_id = interview_data['interview_id']
    questions = interview_data['questions']
    print(f'[OK] Interview Session ID: #{interview_id}')
    print(f'[OK] Questions Assigned ({len(questions)}):')
    q_ids = []
    for q in questions:
        q_ids.append(q['id'])
        print(f'     * [{q["question_code"]}] {q["language"]} ({q["difficulty"]}) - {q["question_text"][:50]}...')

    assert len(questions) == 5, 'Must have exactly 5 questions'
    assert len(q_ids) == len(set(q_ids)), 'Duplicate questions detected in single interview session!'
    print('[OK] Zero duplicates in interview session verified.')

# Test 8: Display / Retrieve Question State via GET /api/interview/<id>
print('\n--- TEST 8: Retrieve Question & State via API ---')
req = urllib.request.Request(f'{base_url}/api/interview/{interview_id}')
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    state = res['data']
    print(f'[OK] Retrieved State: Current Question #{state["current_order"]} ({state["current_question"]["question_code"]})')
    assert state['current_question']['question_text'] is not None

# Test 9, 10, 11, 12, 13: Save Answers & Progress through Questions
print('\n--- TEST 9-13: Voice/Text Answers & Progression ---')
sample_answers = [
    "Python is an interpreted, object-oriented language known for clean syntax and rich standard library.",
    "A variable stores a reference to a memory object in Python dynamically without explicit type declaration.",
    "A list is mutable whereas a tuple is immutable in Python, making tuples faster and hashable.",
    "Primary key uniquely identifies each row in a relational SQL table and cannot be null.",
    "ACID stands for Atomicity, Consistency, Isolation, and Durability ensuring transaction reliability."
]

for idx, q in enumerate(questions):
    ans_text = sample_answers[idx]
    ans_payload = json.dumps({
        'question_id': q['id'],
        'answer_text': ans_text
    }).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/api/interview/{interview_id}/answer', data=ans_payload, headers={'Content-Type': 'application/json'})
    with opener.open(req) as resp:
        ans_res = json.loads(resp.read().decode('utf-8'))
        print(f'     [OK] Saved Answer {idx+1}/{len(questions)} for [{q["question_code"]}]: {ans_res["data"]["answered_count"]} answered (Completed: {ans_res["data"]["is_completed"]})')

# Test 14: Complete Interview & Verification
print('\n--- TEST 14: Complete Interview & Database Verification ---')
req = urllib.request.Request(f'{base_url}/api/interview/{interview_id}/complete', data=b'{}', headers={'Content-Type': 'application/json'})
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] Complete Interview Response: {res["message"]}')

# Check database records
interview_rec = fetch_one("SELECT * FROM interviews WHERE id = %s", (interview_id,))
print(f'[OK] Database Interview Record: ID={interview_rec["id"]}, Status={interview_rec["status"]}, Completed At={interview_rec["completed_at"]}')
assert interview_rec['status'] == 'completed'

answers_recs = fetch_all("SELECT * FROM answers WHERE interview_id = %s", (interview_id,))
print(f'[OK] Total Answers Persisted in MySQL/SQLite: {len(answers_recs)}')
assert len(answers_recs) == 5

# Verify dashboard reflects completed interview
req = urllib.request.Request(f'{base_url}/api/dashboard')
with opener.open(req) as resp:
    dash = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] Dashboard Completed Interviews Count: {dash["data"]["stats"]["interviews_completed"]}')
    assert dash['data']['stats']['interviews_completed'] >= 1

print('\n==================================================')
print('  *** ALL 14 PHASE 5 & PHASE 6 TESTS PASSED! ***   ')
print('==================================================')
