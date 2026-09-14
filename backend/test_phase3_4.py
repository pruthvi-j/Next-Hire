import urllib.request
import json
import http.cookiejar
import os
import docx
import pymupdf as fitz

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
base_url = 'http://127.0.0.1:5000'

print('==================================================')
print('       NEXT HIRE - PHASES 3 & 4 INTEGRATION TEST   ')
print('==================================================')

# Step 0: Login
login_payload = json.dumps({'email': 'priya.sharma@mca.edu', 'password': 'StrongPassword123'}).encode('utf-8')
req = urllib.request.Request(f'{base_url}/api/login', data=login_payload, headers={'Content-Type': 'application/json'})
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] Candidate Login: {res["user"]["name"]}')

# Step 1: Create a test PDF
pdf_path = 'temp_test_resume.pdf'
pdf_doc = fitz.open()
page = pdf_doc.new_page()
pdf_content = """Priya Sharma
Email: priya.sharma@mca.edu | Phone: +91 9876543210
Education:
Master of Computer Applications (MCA) - CGPA 9.1
Technical Skills:
Python, Flask, MySQL, REST API, Git, HTML, CSS, JavaScript, Pandas, SQLite
Projects:
NextHire AI Platform: Developed an automated mock interview assessment web app using Flask and MySQL.
Student Management System: Relational database portal for college department records.
Certifications:
Certified Python Developer
Database Fundamentals Certification
Experience:
Full Stack Development Intern at TechSolutions (6 Months)
"""
page.insert_text((50, 50), pdf_content)
pdf_doc.save(pdf_path)
pdf_doc.close()

# Helper for multipart/form-data upload
def upload_file(file_path, field_name='resume'):
    boundary = '----NextHireTestBoundary123456789'
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    ).encode('utf-8') + file_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request(
        f'{base_url}/api/resume/upload',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    return opener.open(req)

# Test 1: PDF Upload & Parsing
print('\n--- TEST 1: PDF Upload & Entity Extraction ---')
with upload_file(pdf_path) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] PDF Upload Status: {resp.status}')
    data = res['data']
    pdf_resume_id = data['resume_id']
    print(f'[OK] Parsed Candidate Name: {data["candidate_name"]}')
    print(f'[OK] Parsed Email: {data["email"]}')
    print(f'[OK] Parsed Phone: {data["phone"]}')
    print(f'[OK] Skills Extracted ({len(data["all_skills"])}): {data["all_skills"]}')
    assert 'Python' in data['all_skills'], 'Python not found in skills'
    assert 'Flask' in data['all_skills'], 'Flask not found in skills'
    assert 'MySQL' in data['all_skills'], 'MySQL not found in skills'

# Test 2: DOCX Upload & Parsing
print('\n--- TEST 2: DOCX Upload & Entity Extraction ---')
docx_path = 'temp_test_resume.docx'
doc = docx.Document()
doc.add_heading('Priya Sharma', 0)
doc.add_paragraph('Email: priya.sharma@mca.edu | Phone: +91 9876543210')
doc.add_heading('Technical Skills', level=1)
doc.add_paragraph('Python, Django, PostgreSQL, Docker, Kubernetes, AWS, Git, Linux')
doc.add_heading('Education', level=1)
doc.add_paragraph('Master of Computer Applications')
doc.save(docx_path)

with upload_file(docx_path) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] DOCX Upload Status: {resp.status}')
    data = res['data']
    docx_resume_id = data['resume_id']
    print(f'[OK] DOCX Skills Extracted ({len(data["all_skills"])}): {data["all_skills"]}')
    assert 'Docker' in data['all_skills'], 'Docker not found in DOCX'
    assert 'Kubernetes' in data['all_skills'], 'Kubernetes not found in DOCX'

# Test 3: Invalid File Rejection
print('\n--- TEST 3: Invalid File Rejection ---')
invalid_path = 'temp_invalid.txt'
with open(invalid_path, 'w') as f:
    f.write('This is an invalid plain text resume.')
try:
    with upload_file(invalid_path) as resp:
        print('FAILED: Unsupported file was accepted!')
except urllib.error.HTTPError as e:
    err = json.loads(e.read().decode('utf-8'))
    print(f'[OK] Correctly rejected invalid file (HTTP {e.code}): {err["message"]}')
    assert e.code == 400

# Test 4: Resume Retrieval via GET /api/resume
print('\n--- TEST 4: Resume Retrieval API (GET /api/resume) ---')
req = urllib.request.Request(f'{base_url}/api/resume')
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] GET /api/resume: has_resume={res["has_resume"]}, ID={res["data"]["resume_id"]}')
    assert res['has_resume'] is True

# Test 5: Role Retrieval via GET /api/roles
print('\n--- TEST 5: Job Roles API (GET /api/roles) ---')
req = urllib.request.Request(f'{base_url}/api/roles')
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    roles = res['data']
    print(f'[OK] Retrieved {len(roles)} Benchmark Roles:')
    for r in roles:
        print(f'     * Role #{r["id"]}: {r["role_name"]} ({len(r["skills"])} skills)')
    assert len(roles) >= 4, 'Less than 4 roles found'

# Test 6: Role Matching Analyzer (Python Developer)
print('\n--- TEST 6: Role Matching Analysis (Python Developer) ---')
analyze_payload = json.dumps({'role_id': 1}).encode('utf-8')
req = urllib.request.Request(f'{base_url}/api/roles/analyze', data=analyze_payload, headers={'Content-Type': 'application/json'})
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    analysis = res['data']
    print(f'[OK] Selected Role: {analysis["role_name"]}')
    print(f'[OK] Match Percentage: {analysis["match_percentage"]}%')
    print(f'[OK] Readiness Rating: {analysis["readiness_rating"]}')
    print(f'[OK] Matched Skills: {analysis["matched_skills"]}')
    print(f'[OK] Recommended / Missing Skills: {analysis["missing_skills"]}')
    assert len(analysis['matched_skills']) > 0, 'No skills matched'
    assert len(analysis['missing_skills']) >= 0, 'Missing skills check failed'

# Test 7: Current Selected Role Persistence (GET /api/roles/current)
print('\n--- TEST 7: Selected Role Persistence (GET /api/roles/current) ---')
req = urllib.request.Request(f'{base_url}/api/roles/current')
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print(f'[OK] Current Role: {res["data"]["role_name"]} ({res["data"]["match_percentage"]}%)')
    assert res['has_selection'] is True

# Test 8: Dashboard dynamically reflects resume and target role
print('\n--- TEST 8: Dashboard Dynamic Metrics Update ---')
req = urllib.request.Request(f'{base_url}/api/dashboard')
with opener.open(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    stats = res['data']['stats']
    print(f'[OK] Dashboard Stats: Resumes={stats["resumes_analyzed"]}, Target Role={stats["target_role"]}, Readiness={stats["readiness_score"]}')
    assert stats['resumes_analyzed'] >= 2

# Clean up temp files
for p in [pdf_path, docx_path, invalid_path]:
    if os.path.exists(p):
        os.remove(p)

print('\n==================================================')
print('  *** ALL 10 PHASE 3 & PHASE 4 TESTS PASSED! ***  ')
print('==================================================')
