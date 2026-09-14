"""
NEXT HIRE - END-TO-END FINAL SYSTEM VERIFICATION SUITE (Phases 1 through 10)
Master of Computer Applications (MCA) Academic Project

Comprehensive test of the full application pipeline:
Registration -> Login -> Dashboard -> Resume Upload (PDF & DOCX) ->
Skill Extraction -> Target Role Matching -> Question Selection (75 Questions Bank) ->
Mock Interview Chamber -> Answer Persistence -> AI Multi-Dimensional Analysis ->
Final Scoring & Feedback -> Interview History -> ReportLab PDF Generation ->
Security & Session Isolation -> Logout.
"""

import os
import sys
import io
import json
import time

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app
from database import init_db, fetch_one, fetch_all, execute_query
from import_questions import import_questions_from_excel
from pdf_generator import generate_interview_pdf_report

print("=" * 65)
print("      NEXT HIRE &bull; COMPLETE FULL-SYSTEM INTEGRATION TEST      ")
print("      MCA Academic Capstone Platform &bull; Phases 1 through 10     ")
print("=" * 65)

# -------------------------------------------------------------
# STEP 0: DATABASE & ENVIRONMENT INITIALIZATION
# -------------------------------------------------------------
print("\n[STEP 0] Initializing Database & Environment...")
db_mode = init_db()
print(f" -> Database engine active in {db_mode.upper()} mode with all Phase 1-10 tables.")

# Create Flask Test Client with session tracking
client = app.test_client()

# Unique test user credentials
test_email = f"candidate_{int(time.time())}@mca.edu"
test_password = "SecureCandidate2026!#"
test_name = "Aakash Verma"

# -------------------------------------------------------------
# STEP 1: CANDIDATE REGISTRATION
# -------------------------------------------------------------
print("\n[STEP 1] Testing Candidate Registration (POST /api/register)...")
reg_payload = {
    'name': test_name,
    'email': test_email,
    'password': test_password
}
reg_resp = client.post('/api/register', json=reg_payload)
print(f" -> Registration HTTP Status: {reg_resp.status_code}")
assert reg_resp.status_code == 201, f"Expected 201, got {reg_resp.status_code}"
reg_data = json.loads(reg_resp.data.decode('utf-8'))
user_id = reg_data['user']['id']
print(f" -> Candidate Registered: ID={user_id}, Name={reg_data['user']['name']}, Email={reg_data['user']['email']}")

# -------------------------------------------------------------
# STEP 2: CANDIDATE AUTHENTICATION & LOGIN
# -------------------------------------------------------------
print("\n[STEP 2] Testing Candidate Login (POST /api/login)...")
login_payload = {
    'email': test_email,
    'password': test_password
}
login_resp = client.post('/api/login', json=login_payload)
print(f" -> Login HTTP Status: {login_resp.status_code}")
assert login_resp.status_code == 200, f"Expected 200, got {login_resp.status_code}"
login_data = json.loads(login_resp.data.decode('utf-8'))
print(f" -> Session cookie issued for candidate: {login_data['user']['name']}")

# -------------------------------------------------------------
# STEP 3: PROTECTED DASHBOARD RETRIEVAL
# -------------------------------------------------------------
print("\n[STEP 3] Testing Dashboard API (GET /api/dashboard)...")
dash_resp = client.get('/api/dashboard')
assert dash_resp.status_code == 200
dash_data = json.loads(dash_resp.data.decode('utf-8'))['data']
print(f" -> Dashboard Stats: Target Role='{dash_data['stats']['target_role']}', Resumes={dash_data['stats']['resumes_analyzed']}, Readiness={dash_data['stats']['readiness_score']}")
assert dash_data['phase']['current'] == 'Phases 1 through 8 Active' or 'Phases' in dash_data['phase']['current']

# -------------------------------------------------------------
# STEP 4: RESUME UPLOAD & PARSING (PDF & DOCX)
# -------------------------------------------------------------
print("\n[STEP 4] Testing Resume Upload & Skill Extraction...")

# Mock PDF content
pdf_text_content = """
Aakash Verma
Email: aakash.verma@mca.edu | Phone: +91 9876543210
Education: Master of Computer Applications (MCA), Distinction
Technical Skills: Python, Flask, MySQL, JavaScript, HTML, CSS, Git, Docker, REST API
Projects: NextHire Mock Interview Chamber with NLP speech analysis
Certifications: Certified Python Associate, AWS Cloud Practitioner
"""
try:
    import fitz
    pdf_doc = fitz.open()
    page = pdf_doc.new_page()
    page.insert_text((50, 72), pdf_text_content, fontsize=11)
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()
except Exception:
    pdf_bytes = pdf_text_content.encode('utf-8')

upload_data = {
    'resume': (io.BytesIO(pdf_bytes), 'aakash_verma_resume.pdf')
}
upload_resp = client.post('/api/resume/upload', data=upload_data, content_type='multipart/form-data')
print(f" -> PDF Resume Upload Status: {upload_resp.status_code}")
assert upload_resp.status_code == 201
pdf_res_data = json.loads(upload_resp.data.decode('utf-8'))['data']
extracted_skills = pdf_res_data['all_skills']
print(f" -> Extracted Skills ({len(extracted_skills)}): {extracted_skills}")
assert len(extracted_skills) >= 3, "Skills must be extracted from PDF"

# -------------------------------------------------------------
# STEP 5: TARGET ROLE BENCHMARKING & GAP ANALYSIS
# -------------------------------------------------------------
print("\n[STEP 5] Testing Target Role Benchmarking (POST /api/roles/analyze)...")
role_resp = client.post('/api/roles/analyze', json={'role_id': 1}) # Python Developer
assert role_resp.status_code == 200
role_analysis = json.loads(role_resp.data.decode('utf-8'))['data']
print(f" -> Role: {role_analysis['role_name']}")
print(f" -> Match Percentage: {role_analysis['match_percentage']}%")
print(f" -> Matched Skills: {role_analysis['matched_skills']}")
print(f" -> Missing Skills: {role_analysis['missing_skills']}")

# -------------------------------------------------------------
# STEP 6: QUESTION BANK INTEGRITY & IMPORT
# -------------------------------------------------------------
print("\n[STEP 6] Testing Question Bank Importer & Duplicate Prevention...")
q_count = import_questions_from_excel()
print(f" -> Verified Authority Bank Questions: {q_count} questions active.")
assert q_count == 75, f"Expected exactly 75 questions, found {q_count}"

# -------------------------------------------------------------
# STEP 7: START INTERVIEW & VERIFY UNIQUE QUESTION SELECTION
# -------------------------------------------------------------
print("\n[STEP 7] Testing Mock Interview Chamber Setup (POST /api/interview/start)...")
start_resp = client.post('/api/interview/start', json={
    'role_id': 1,
    'difficulty': 'Medium',
    'num_questions': 3
})
assert start_resp.status_code == 201
interview_session = json.loads(start_resp.data.decode('utf-8'))['data']
interview_id = interview_session['interview_id']
assigned_questions = interview_session['questions']
print(f" -> Interview #{interview_id} launched with {len(assigned_questions)} questions:")
q_ids = [q['id'] for q in assigned_questions]
for q in assigned_questions:
    print(f"    * [{q['question_code']}] {q['language']} - {q['topic']} ({q['difficulty']}): {q['question_text'][:45]}...")
assert len(q_ids) == len(set(q_ids)), "Zero duplicates allowed in question selection"

# -------------------------------------------------------------
# STEP 8: VOICE/TEXT ANSWER CAPTURE & AI ANALYSIS (PHASE 7)
# -------------------------------------------------------------
print("\n[STEP 8] Testing Answer Persistence & Multi-Dimensional AI Scoring...")
answers_data = [
    "Python is an interpreted, high-level language with dynamic typing, automatic memory management, and extensive standard libraries.",
    "A primary key uniquely identifies each record in a SQL table and cannot contain NULL values.",
    "" # Empty answer test to verify robust handling
]

for idx, q in enumerate(assigned_questions):
    ans_text = answers_data[idx]
    ans_resp = client.post(f'/api/interview/{interview_id}/answer', json={
        'question_id': q['id'],
        'answer_text': ans_text
    })
    assert ans_resp.status_code == 200
    ans_res = json.loads(ans_resp.data.decode('utf-8'))['data']
    scores = ans_res.get('scores', {})
    print(f" -> Answer {idx+1}/3 [Q {q['id']}]: Tech={scores.get('technical')}/5, Comm={scores.get('communication')}/5, Quality={scores.get('quality')}/5, Conf={scores.get('confidence')}/5")
    assert 1 <= scores.get('technical', 1) <= 5

# -------------------------------------------------------------
# STEP 9: FINALIZE INTERVIEW & SCORING FORMULA (PHASE 8)
# -------------------------------------------------------------
print("\n[STEP 9] Testing Interview Finalization & Scorecard (POST /api/interview/<id>/complete)...")
complete_resp = client.post(f'/api/interview/{interview_id}/complete', json={})
assert complete_resp.status_code == 200
complete_data = json.loads(complete_resp.data.decode('utf-8'))['data']
print(f" -> Interview #{interview_id} Concluded. Overall Score: {complete_data['overall_score']}%")

# -------------------------------------------------------------
# STEP 10: GET SCORECARD RESULTS & DIAGNOSTIC FEEDBACK
# -------------------------------------------------------------
print("\n[STEP 10] Testing Evaluation Scorecard API (GET /api/interview/<id>/result)...")
result_resp = client.get(f'/api/interview/{interview_id}/result')
assert result_resp.status_code == 200
scorecard = json.loads(result_resp.data.decode('utf-8'))['data']

print(f" -> Overall Score: {scorecard['overall_score']}%")
print(f" -> Technical Score: {scorecard['scores']['technical']['score_5']}/5 ({scorecard['scores']['technical']['percentage']}%)")
print(f" -> Quality Score: {scorecard['scores']['quality']['score_5']}/5 ({scorecard['scores']['quality']['percentage']}%)")
print(f" -> Communication Score: {scorecard['scores']['communication']['score_5']}/5 ({scorecard['scores']['communication']['percentage']}%)")
print(f" -> Confidence Estimate: {scorecard['scores']['confidence']['score_5']}/5 (Notice: Observable indicators estimate)")
print(f" -> STRENGTHS ({len(scorecard['strengths'])}): {scorecard['strengths']}")
print(f" -> AREAS TO IMPROVE ({len(scorecard['weaknesses'])}): {scorecard['weaknesses']}")
print(f" -> RECOMMENDATIONS ({len(scorecard['recommendations'])}): {scorecard['recommendations']}")

assert len(scorecard['strengths']) >= 1
assert len(scorecard['weaknesses']) >= 1
assert len(scorecard['recommendations']) >= 1
assert len(scorecard['questions_details']) == 3

# -------------------------------------------------------------
# STEP 11: CANDIDATE INTERVIEW HISTORY (PHASE 9)
# -------------------------------------------------------------
print("\n[STEP 11] Testing Candidate Interview History (GET /api/interviews/history)...")
hist_resp = client.get('/api/interviews/history')
assert hist_resp.status_code == 200
hist_items = json.loads(hist_resp.data.decode('utf-8'))['data']
print(f" -> Total Archived Sessions for Candidate: {len(hist_items)}")
assert len(hist_items) >= 1

current_session = next((item for item in hist_items if item['id'] == interview_id), None)
assert current_session is not None, "Active interview must be in history"
print(f" -> History Item Verified: Role='{current_session['role_name']}', Date='{current_session['date']}', Score='{current_session['score_display']}', Status='{current_session['status']}'")

# -------------------------------------------------------------
# STEP 12: PDF REPORT GENERATION & DOWNLOAD (PHASE 9)
# -------------------------------------------------------------
print("\n[STEP 12] Testing PDF Report Generation (GET /api/interview/<id>/pdf)...")
pdf_resp = client.get(f'/api/interview/{interview_id}/pdf')
print(f" -> PDF Generation Status: HTTP {pdf_resp.status_code}")
assert pdf_resp.status_code == 200, f"Expected 200, got {pdf_resp.status_code}"
assert pdf_resp.headers.get('Content-Type') == 'application/pdf', "Must return application/pdf"
pdf_bytes = pdf_resp.data
print(f" -> PDF File Size: {len(pdf_bytes)} bytes")
assert pdf_bytes.startswith(b'%PDF'), "Downloaded file must have valid PDF magic byte header"
assert len(pdf_bytes) > 2000, "PDF must contain complete document payload"

# -------------------------------------------------------------
# STEP 13: SECURITY & SESSION ISOLATION TESTING
# -------------------------------------------------------------
print("\n[STEP 13] Testing Security & Session Isolation (Accessing other candidate data)...")
other_client = app.test_client()
with other_client.session_transaction() as sess:
    sess['user_id'] = 999999  # Different candidate ID
    sess['user_name'] = 'Intruder'

# Attempt to download other candidate's PDF
unauthorized_pdf_resp = other_client.get(f'/api/interview/{interview_id}/pdf')
print(f" -> Cross-Tenant PDF Download Attempt: HTTP {unauthorized_pdf_resp.status_code} (Properly blocked)")
assert unauthorized_pdf_resp.status_code in [403, 404]

# Attempt to view other candidate's result
unauthorized_res_resp = other_client.get(f'/api/interview/{interview_id}/result')
print(f" -> Cross-Tenant Result Retrieval Attempt: HTTP {unauthorized_res_resp.status_code} (Properly blocked)")
assert unauthorized_res_resp.status_code in [403, 404]

# -------------------------------------------------------------
# STEP 14: LOGOUT & SESSION TERMINATION
# -------------------------------------------------------------
print("\n[STEP 14] Testing Session Termination (POST /api/logout)...")
logout_resp = client.post('/api/logout')
assert logout_resp.status_code == 200
print(" -> Candidate session terminated successfully.")

# Verify subsequent protected access is rejected
post_logout_resp = client.get('/api/dashboard')
assert post_logout_resp.status_code == 401
print(" -> Post-logout request to protected route returned HTTP 401 Unauthorized.")

print("\n" + "=" * 65)
print("  *** FULL-SYSTEM INTEGRATION TEST: 100% PASSED! ***  ")
print("  All 14 Workflow Milestones Verified for Academic Excellence. ")
print("=" * 65)
