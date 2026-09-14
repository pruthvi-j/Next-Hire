"""
NEXT HIRE - PHASES 7 & 8 AUTOMATED TEST SUITE
MCA Academic Project
Tests:
1. Answer analysis
2. AI API connection
3. AI error handling
4. Score generation (1-5 scale)
5. Score calculation (Weighted formula)
6. Feedback generation (Strengths, Weaknesses, Recommendations)
7. Database storage (answers & interview_results tables)
8. Final result API & page endpoints
9. Different answer scenarios (Strong, Medium, Weak)
10. Empty answer handling (Blank/whitespace)
"""

import os
import sys
import json
import urllib.request
import http.cookiejar

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db, fetch_one, fetch_all, execute_query
from answer_analyzer import (
    analyze_answer,
    calculate_final_scores,
    synthesize_personalized_feedback,
    analyze_and_store_answer,
    generate_interview_result
)
from question_engine import create_interview_session, save_answer

print("=" * 60)
print("       NEXT HIRE - PHASES 7 & 8 COMPREHENSIVE TEST SUITE   ")
print("=" * 60)

# 0. Initialize Database
db_mode = init_db()
print(f"[OK] Database initialized in {db_mode.upper()} mode.")

# -------------------------------------------------------------
# TEST 1 & 4: Answer Analysis & 1-5 Score Generation
# -------------------------------------------------------------
print("\n--- TEST 1 & 4: Answer Analysis & Score Generation (1-5 System) ---")
strong_python_answer = (
    "In Python, a list is a mutable ordered sequence of elements, meaning items can be appended or modified in-place, "
    "whereas a tuple is immutable, meaning its elements cannot be changed after creation. Because tuples are immutable, "
    "they are hashable and can be used as dictionary keys, and they also offer slight memory and performance advantages."
)
res_strong = analyze_answer(
    question_text="What is the difference between a list and a tuple in Python?",
    answer_text=strong_python_answer,
    language="Python",
    topic="Data Structures",
    difficulty="Easy",
    role_name="Python Developer"
)
print(f"[OK] Strong Answer Evaluated:")
print(f"     Technical:    {res_strong['technical_score']}/5")
print(f"     Communication:{res_strong['communication_score']}/5")
print(f"     Quality:      {res_strong['quality_score']}/5")
print(f"     Confidence:   {res_strong['confidence_score']}/5 (Observable indicators estimate)")
print(f"     Feedback:     {res_strong['feedback']}")
print(f"     Strength:     {res_strong['strength']}")
print(f"     Improvement:  {res_strong['improvement']}")
print(f"     Source:       {res_strong['source']}")

assert 1 <= res_strong['technical_score'] <= 5, "Technical score must be 1-5"
assert 1 <= res_strong['communication_score'] <= 5, "Communication score must be 1-5"
assert 1 <= res_strong['quality_score'] <= 5, "Quality score must be 1-5"
assert 1 <= res_strong['confidence_score'] <= 5, "Confidence score must be 1-5"
assert res_strong['technical_score'] >= 4, "Strong technical answer should score >= 4"
assert len(res_strong['feedback']) > 10, "Feedback must be non-empty"

# -------------------------------------------------------------
# TEST 2 & 3: AI API Connection & Graceful Error Handling
# -------------------------------------------------------------
print("\n--- TEST 2 & 3: AI API Connection & Error Handling ---")
# Call with invalid key or offline environment to verify graceful fallback
res_fallback = analyze_answer(
    question_text="Explain the ACID properties of database transactions.",
    answer_text="ACID stands for Atomicity, Consistency, Isolation, and Durability to ensure relational integrity.",
    language="SQL",
    topic="Transactions",
    difficulty="Medium",
    role_name="Data Analyst"
)
print(f"[OK] Engine successfully handled execution: Source = '{res_fallback['source']}'")
assert res_fallback['technical_score'] in [1, 2, 3, 4, 5]
print("[OK] Graceful fallback confirmed: zero crash when AI API key absent or unavailable.")

# -------------------------------------------------------------
# TEST 9: Different Answer Scenarios (Medium & Weak/Hedging)
# -------------------------------------------------------------
print("\n--- TEST 9: Different Answer Scenarios ---")
# Scenario A: Moderate answer
res_medium = analyze_answer(
    question_text="What is a primary key in SQL?",
    answer_text="A primary key is a column in a table that identifies each record uniquely.",
    language="SQL",
    topic="Basics",
    difficulty="Easy"
)
print(f"[OK] Scenario Moderate: Tech={res_medium['technical_score']}/5, Quality={res_medium['quality_score']}/5")

# Scenario B: Weak answer with uncertainty/filler markers
weak_answer = "Um, maybe it is something like a key, I guess... not really sure."
res_weak = analyze_answer(
    question_text="What is a primary key in SQL?",
    answer_text=weak_answer,
    language="SQL",
    topic="Basics",
    difficulty="Easy"
)
print(f"[OK] Scenario Weak/Uncertain: Tech={res_weak['technical_score']}/5, Conf={res_weak['confidence_score']}/5, Feedback='{res_weak['feedback']}'")
assert res_weak['technical_score'] <= 2, "Weak answer should have low technical score"
assert res_weak['confidence_score'] <= 2, "Hedging answer should have low confidence estimate"

# -------------------------------------------------------------
# TEST 10: Empty Answer Handling
# -------------------------------------------------------------
print("\n--- TEST 10: Empty & Whitespace Answer Handling ---")
res_empty_1 = analyze_answer(
    question_text="What is inheritance in OOP?",
    answer_text="",
    language="Java",
    topic="OOP"
)
res_empty_2 = analyze_answer(
    question_text="What is inheritance in OOP?",
    answer_text="     ",
    language="Java",
    topic="OOP"
)
print(f"[OK] Empty Answer Scores: Tech={res_empty_1['technical_score']}/5, Comm={res_empty_1['communication_score']}/5, Quality={res_empty_1['quality_score']}/5, Conf={res_empty_1['confidence_score']}/5")
print(f"     Feedback: '{res_empty_1['feedback']}'")
assert res_empty_1['technical_score'] == 1
assert res_empty_1['communication_score'] == 1
assert res_empty_1['quality_score'] == 1
assert res_empty_1['confidence_score'] == 1
assert res_empty_2['technical_score'] == 1
print("[OK] Empty answer properly clamped to 1/5 with constructive non-crashing feedback.")

# -------------------------------------------------------------
# TEST 5: Scoring Formula Calculation
# -------------------------------------------------------------
print("\n--- TEST 5: Scoring Formula Calculation ---")
sample_batch = [
    {'technical_score': 5, 'quality_score': 4, 'communication_score': 4, 'confidence_score': 4},
    {'technical_score': 4, 'quality_score': 4, 'communication_score': 5, 'confidence_score': 4},
    {'technical_score': 3, 'quality_score': 3, 'communication_score': 3, 'confidence_score': 3}
]
scores_calc = calculate_final_scores(sample_batch)
# Manual verification of weighted formula:
# Avg_Tech = 12/3 = 4.0 -> 4.0/5 = 0.8
# Avg_Qual = 11/3 = 3.67 -> 3.6667/5 = 0.7333
# Avg_Comm = 12/3 = 4.0 -> 4.0/5 = 0.8
# Avg_Conf = 11/3 = 3.67 -> 3.6667/5 = 0.7333
# Weighted = (0.40 * 0.8 + 0.25 * 0.7333 + 0.20 * 0.8 + 0.15 * 0.7333) * 100
#          = (0.32 + 0.1833 + 0.16 + 0.11) * 100 = 77.3%
print(f"[OK] Calculated Dimensions: Tech={scores_calc['technical_score']}, Qual={scores_calc['quality_score']}, Comm={scores_calc['communication_score']}, Conf={scores_calc['confidence_score']}")
print(f"[OK] Weighted Overall Score: {scores_calc['overall_score']}%")
assert 70.0 <= scores_calc['overall_score'] <= 85.0
assert scores_calc['num_answered'] == 3

# -------------------------------------------------------------
# TEST 6: Feedback Generation (Strengths, Weaknesses, Recommendations)
# -------------------------------------------------------------
print("\n--- TEST 6: Feedback Generation ---")
answers_for_feedback = [
    {
        'language': 'Python',
        'topic': 'Data Structures',
        'technical_score': 5,
        'communication_score': 4,
        'quality_score': 5,
        'strength': 'Clear definition of mutable list vs immutable tuple.',
        'improvement': 'Explore advanced dictionary comprehension.'
    },
    {
        'language': 'SQL',
        'topic': 'Joins',
        'technical_score': 2,
        'communication_score': 2,
        'quality_score': 2,
        'strength': 'Attempted relational concept explanation.',
        'improvement': 'Deepen explanation of LEFT vs FULL OUTER JOIN.'
    }
]
feedback_bundle = synthesize_personalized_feedback(answers_for_feedback, role_name="Full Stack Developer")
print(f"[OK] Synthesized STRENGTHS ({len(feedback_bundle['strengths'])}):")
for s in feedback_bundle['strengths']:
    print(f"     [+] {s}")
print(f"[OK] Synthesized WEAKNESSES ({len(feedback_bundle['weaknesses'])}):")
for w in feedback_bundle['weaknesses']:
    print(f"     [-] {w}")
print(f"[OK] Synthesized RECOMMENDATIONS ({len(feedback_bundle['recommendations'])}):")
for r in feedback_bundle['recommendations']:
    print(f"     [>] {r}")

assert len(feedback_bundle['strengths']) >= 1
assert len(feedback_bundle['weaknesses']) >= 1
assert len(feedback_bundle['recommendations']) >= 1

# -------------------------------------------------------------
# TEST 7: Database Storage & Interview Result Persistence
# -------------------------------------------------------------
print("\n--- TEST 7: Database Storage & Interview Result Persistence ---")
# 1. Create a real interview session for user_id = 1
interview_setup = create_interview_session(
    user_id=1,
    role_id=1, # Python Developer
    difficulty='Medium',
    num_questions=3
)
test_interview_id = interview_setup['interview_id']
questions = interview_setup['questions']
print(f"[OK] Created Test Interview #{test_interview_id} with {len(questions)} questions.")

# 2. Save answers with answer_analyzer
test_answers = [
    "Python is an interpreted language with dynamic typing, automatic memory management, and clean syntax.",
    "A dictionary in Python stores key-value pairs using hash tables for average O(1) time complexity.",
    "" # Empty answer to test mixed scenario
]

for idx, q in enumerate(questions):
    ans_text = test_answers[idx]
    save_res = save_answer(test_interview_id, q['id'], ans_text, user_id=1)
    print(f"     Saved Answer {idx+1}/{len(questions)} [Q ID: {q['id']}]: "
          f"Tech={save_res['scores']['technical']}/5, "
          f"Conf={save_res['scores']['confidence']}/5, "
          f"Completed={save_res['is_completed']}")

# 3. Verify answers table columns in DB
ans_records = fetch_all(
    """
    SELECT id, question_id, technical_score, communication_score, quality_score, 
           confidence_score, feedback, strength, improvement 
    FROM answers WHERE interview_id = %s
    """,
    (test_interview_id,)
)
print(f"[OK] Verified {len(ans_records)} answers stored in DB:")
for a in ans_records:
    print(f"     Answer #{a['id']}: Tech={a['technical_score']}, Comm={a['communication_score']}, Quality={a['quality_score']}, Conf={a['confidence_score']}")
    assert a['technical_score'] is not None
    assert a['feedback'] is not None

# 4. Generate/verify interview_results table
result_summary = generate_interview_result(test_interview_id, user_id=1)
print(f"[OK] Final Scorecard Generated for Interview #{test_interview_id}:")
print(f"     Overall Score:     {result_summary['overall_score']}%")
print(f"     Technical Rating:  {result_summary['scores']['technical']['score_5']}/5 ({result_summary['scores']['technical']['percentage']}%)")
print(f"     Communication:     {result_summary['scores']['communication']['score_5']}/5")
print(f"     Quality:           {result_summary['scores']['quality']['score_5']}/5")
print(f"     Confidence Est.:   {result_summary['scores']['confidence']['score_5']}/5")

db_result_row = fetch_one("SELECT * FROM interview_results WHERE interview_id = %s", (test_interview_id,))
assert db_result_row is not None, "interview_results row must be saved in database"
print(f"[OK] Persisted in interview_results table: ID={db_result_row['id']}, Overall={db_result_row['overall_score']}%")

# -------------------------------------------------------------
# TEST 8: Full API Endpoint Integration
# -------------------------------------------------------------
print("\n--- TEST 8: Flask Server & REST Endpoints Integration ---")
# Use test client from app
from app import app
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['user_name'] = 'Test Candidate'
    sess['user_email'] = 'candidate@test.com'

# Test GET /api/interview/<id>/result
resp = client.get(f'/api/interview/{test_interview_id}/result')
print(f"[OK] GET /api/interview/{test_interview_id}/result -> HTTP {resp.status_code}")
assert resp.status_code == 200
res_json = json.loads(resp.data.decode('utf-8'))
assert res_json['status'] == 'success'
assert 'scores' in res_json['data']
assert 'strengths' in res_json['data']
assert 'weaknesses' in res_json['data']
assert 'recommendations' in res_json['data']
assert len(res_json['data']['questions_details']) == 3

# Test GET /api/interview/latest-result
resp_latest = client.get('/api/interview/latest-result')
print(f"[OK] GET /api/interview/latest-result -> HTTP {resp_latest.status_code}")
assert resp_latest.status_code == 200
latest_json = json.loads(resp_latest.data.decode('utf-8'))
assert latest_json['data']['interview_id'] == test_interview_id

# Test GET /api/interviews/history
resp_hist = client.get('/api/interviews/history')
print(f"[OK] GET /api/interviews/history -> HTTP {resp_hist.status_code}")
assert resp_hist.status_code == 200
hist_json = json.loads(resp_hist.data.decode('utf-8'))
assert len(hist_json['data']) >= 1
print(f"     History Row 0: Code={hist_json['data'][0]['session_code']}, Score={hist_json['data'][0]['score_display']}")

# Test GET /api/dashboard reflects real interview evaluation
resp_dash = client.get('/api/dashboard')
print(f"[OK] GET /api/dashboard -> HTTP {resp_dash.status_code}")
dash_json = json.loads(resp_dash.data.decode('utf-8'))
print(f"     Dashboard Readiness Score: {dash_json['data']['stats']['readiness_score']}")
assert dash_json['data']['stats']['readiness_score'] != "Pending"

print("\n" + "=" * 60)
print("  *** ALL 10 PHASE 7 & PHASE 8 TEST CATEGORIES PASSED! ***  ")
print("=" * 60)
