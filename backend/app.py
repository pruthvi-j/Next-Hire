import os
import time
from datetime import timedelta, datetime
from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from database import init_db, fetch_one, fetch_all, execute_query
from auth import register_user, authenticate_user, get_user_by_id, login_required
from resume_parser import parse_resume_file
from role_analyzer import get_all_roles, get_role_by_id, analyze_resume_against_role, get_user_selected_role
from question_engine import create_interview_session, get_current_interview_state, save_answer
from answer_analyzer import generate_interview_result, analyze_answer
from pdf_generator import generate_interview_pdf_report

# Load environment configuration
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

frontend_dir = os.path.abspath(os.path.join(base_dir, '..', 'frontend'))
upload_folder = os.path.join(base_dir, 'uploads')
os.makedirs(upload_folder, exist_ok=True)

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nexthire_mca_project_secure_session_secret_2026')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB limit

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------------------------------------------
# CORS — must use explicit origins (not wildcard) when
# supports_credentials=True, otherwise browsers block cookies.
# ---------------------------------------------------------------
ALLOWED_ORIGINS = [
    'http://localhost:5500',
    'http://127.0.0.1:5500',
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS(app,
     supports_credentials=True,
     resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
     expose_headers=["Content-Type", "Authorization"])


# =========================================================
# FRONTEND STATIC ROUTES
# =========================================================

@app.route('/')
def serve_index():
    return send_from_directory(frontend_dir, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    file_path = os.path.join(frontend_dir, filename)
    if os.path.isfile(file_path):
        return send_from_directory(frontend_dir, filename)
    html_file = os.path.join(frontend_dir, f"{filename}.html")
    if os.path.isfile(html_file):
        return send_from_directory(frontend_dir, f"{filename}.html")
    return send_from_directory(frontend_dir, 'index.html')


# =========================================================
# AUTHENTICATION & USER APIS (Phase 1 & 2)
# =========================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or request.form
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    success, message, user_data = register_user(name, email, password)
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400

    return jsonify({
        'status': 'success',
        'message': message,
        'user': user_data
    }), 201


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or request.form
    email = data.get('email')
    password = data.get('password')

    success, message, user_data = authenticate_user(email, password)
    if not success:
        return jsonify({'status': 'error', 'message': message}), 401

    session.permanent = True
    session['user_id'] = user_data['id']
    session['user_name'] = user_data['name']
    session['user_email'] = user_data['email']

    return jsonify({
        'status': 'success',
        'message': message,
        'user': user_data
    }), 200


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully.'
    }), 200


@app.route('/api/user', methods=['GET'])
def api_get_user():
    if 'user_id' not in session:
        return jsonify({
            'authenticated': False,
            'message': 'No active session found.'
        }), 401

    user = get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return jsonify({
            'authenticated': False,
            'message': 'User record no longer exists.'
        }), 401

    return jsonify({
        'authenticated': True,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'created_at': str(user['created_at']) if user.get('created_at') else None
        }
    }), 200


# =========================================================
# RESUME UPLOAD & PARSING APIS (Phase 3)
# =========================================================

@app.route('/api/resume/upload', methods=['POST'])
@login_required
def api_resume_upload():
    """
    POST /api/resume/upload
    Validates uploaded file, extracts text, identifies resume entities,
    and stores structured data in MySQL linked to candidate.
    """
    user_id = session['user_id']

    if 'resume' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No resume file uploaded. Please attach a PDF or DOCX file.'
        }), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No file selected. Please choose a resume document.'
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            'status': 'error',
            'message': 'Invalid file format. Supported file formats: PDF (.pdf) and Word (.docx).'
        }), 400

    # Secure filename and unique timestamp prefix
    original_filename = secure_filename(file.filename)
    unique_filename = f"user_{user_id}_{int(time.time())}_{original_filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to store file on server: {str(e)}'
        }), 500

    # Extract resume content
    try:
        parsed_data = parse_resume_file(file_path, original_filename)
    except Exception as parse_err:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({
            'status': 'error',
            'message': f'Resume parsing error: {str(parse_err)}'
        }), 422

    # Persist to database
    try:
        resume_id = execute_query(
            """
            INSERT INTO resumes 
            (user_id, filename, file_path, raw_text, candidate_name, email, phone, education, experience)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                original_filename,
                file_path,
                parsed_data['raw_text'],
                parsed_data['candidate_name'],
                parsed_data['email'],
                parsed_data['phone'],
                parsed_data['education'],
                parsed_data['experience']
            )
        )

        # Store skills
        for category, skills in parsed_data['categorized_skills'].items():
            for skill in skills:
                execute_query(
                    "INSERT INTO resume_skills (resume_id, skill_name, category) VALUES (%s, %s, %s)",
                    (resume_id, skill, category)
                )

        # Store projects
        for proj in parsed_data['projects']:
            execute_query(
                "INSERT INTO resume_projects (resume_id, project_title, description) VALUES (%s, %s, %s)",
                (resume_id, proj['title'], proj['description'])
            )

        # Store certifications
        for cert in parsed_data['certifications']:
            execute_query(
                "INSERT INTO resume_certifications (resume_id, certification_name) VALUES (%s, %s)",
                (resume_id, cert)
            )

        # Store latest resume_id in session
        session['latest_resume_id'] = resume_id

        return jsonify({
            'status': 'success',
            'message': 'Resume successfully uploaded and parsed.',
            'data': {
                'resume_id': resume_id,
                'filename': original_filename,
                'candidate_name': parsed_data['candidate_name'],
                'email': parsed_data['email'],
                'phone': parsed_data['phone'],
                'all_skills': parsed_data['all_skills'],
                'categorized_skills': parsed_data['categorized_skills'],
                'education': parsed_data['education'],
                'experience': parsed_data['experience'],
                'projects': parsed_data['projects'],
                'certifications': parsed_data['certifications']
            }
        }), 201

    except Exception as db_err:
        return jsonify({
            'status': 'error',
            'message': f'Database persistence failure: {str(db_err)}'
        }), 500


@app.route('/api/resume', methods=['GET'])
@login_required
def api_get_latest_resume():
    """
    GET /api/resume
    Retrieves candidate's most recent uploaded resume with all skills, projects, and certifications.
    """
    user_id = session['user_id']
    resume = fetch_one(
        "SELECT * FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    if not resume:
        return jsonify({
            'status': 'success',
            'has_resume': False,
            'message': 'No resume uploaded yet.'
        }), 200

    resume_id = resume['id']
    skills = fetch_all("SELECT skill_name, category FROM resume_skills WHERE resume_id = %s", (resume_id,))
    projects = fetch_all("SELECT project_title, description FROM resume_projects WHERE resume_id = %s", (resume_id,))
    certs = fetch_all("SELECT certification_name FROM resume_certifications WHERE resume_id = %s", (resume_id,))

    categorized_skills = {}
    all_skills = []
    for s in skills:
        cat = s.get('category', 'General')
        name = s['skill_name']
        all_skills.append(name)
        if cat not in categorized_skills:
            categorized_skills[cat] = []
        categorized_skills[cat].append(name)

    return jsonify({
        'status': 'success',
        'has_resume': True,
        'data': {
            'resume_id': resume['id'],
            'filename': resume['filename'],
            'candidate_name': resume['candidate_name'],
            'email': resume['email'],
            'phone': resume['phone'],
            'education': resume['education'],
            'experience': resume['experience'],
            'created_at': str(resume['created_at']) if resume.get('created_at') else None,
            'all_skills': all_skills,
            'categorized_skills': categorized_skills,
            'projects': [{'title': p['project_title'], 'description': p['description']} for p in projects],
            'certifications': [c['certification_name'] for c in certs]
        }
    }), 200


@app.route('/api/resume/<int:resume_id>', methods=['GET'])
@login_required
def api_get_resume_by_id(resume_id):
    """
    GET /api/resume/<id>
    Retrieves specific resume by ID for the logged-in candidate.
    """
    user_id = session['user_id']
    resume = fetch_one(
        "SELECT * FROM resumes WHERE id = %s AND user_id = %s",
        (resume_id, user_id)
    )
    if not resume:
        return jsonify({
            'status': 'error',
            'message': 'Resume record not found or unauthorized.'
        }), 404

    skills = fetch_all("SELECT skill_name, category FROM resume_skills WHERE resume_id = %s", (resume_id,))
    projects = fetch_all("SELECT project_title, description FROM resume_projects WHERE resume_id = %s", (resume_id,))
    certs = fetch_all("SELECT certification_name FROM resume_certifications WHERE resume_id = %s", (resume_id,))

    categorized_skills = {}
    all_skills = []
    for s in skills:
        cat = s.get('category', 'General')
        name = s['skill_name']
        all_skills.append(name)
        if cat not in categorized_skills:
            categorized_skills[cat] = []
        categorized_skills[cat].append(name)

    return jsonify({
        'status': 'success',
        'data': {
            'resume_id': resume['id'],
            'filename': resume['filename'],
            'candidate_name': resume['candidate_name'],
            'email': resume['email'],
            'phone': resume['phone'],
            'education': resume['education'],
            'experience': resume['experience'],
            'created_at': str(resume['created_at']) if resume.get('created_at') else None,
            'all_skills': all_skills,
            'categorized_skills': categorized_skills,
            'projects': [{'title': p['project_title'], 'description': p['description']} for p in projects],
            'certifications': [c['certification_name'] for c in certs]
        }
    }), 200


# =========================================================
# JOB ROLE SELECTION & RESUME MATCHING APIS (Phase 4)
# =========================================================

@app.route('/api/roles', methods=['GET'])
def api_get_roles():
    """
    GET /api/roles
    Returns all benchmark job roles and their required/recommended skills.
    """
    roles = get_all_roles()
    return jsonify({
        'status': 'success',
        'data': roles
    }), 200


@app.route('/api/roles/analyze', methods=['POST'])
@login_required
def api_analyze_role():
    """
    POST /api/roles/analyze
    Analyzes resume skills against target job role skills.
    Identifies matched skills and missing/recommended skills.
    Stores selected role for the candidate's interview session.
    Payload: { role_id, resume_id (optional) }
    """
    user_id = session['user_id']
    data = request.get_json(silent=True) or request.form
    role_id = data.get('role_id')

    if not role_id:
        return jsonify({
            'status': 'error',
            'message': 'Role ID is required for skill matching analysis.'
        }), 400

    try:
        role_id = int(role_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid role ID parameter.'
        }), 400

    # Obtain skills from specified resume or user's latest resume
    resume_id = data.get('resume_id')
    if resume_id:
        skills_records = fetch_all(
            "SELECT skill_name FROM resume_skills WHERE resume_id = %s",
            (resume_id,)
        )
    else:
        latest_resume = fetch_one(
            "SELECT id FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        if not latest_resume:
            return jsonify({
                'status': 'error',
                'message': 'Please upload your resume before performing role matching analysis.'
            }), 400
        resume_id = latest_resume['id']
        skills_records = fetch_all(
            "SELECT skill_name FROM resume_skills WHERE resume_id = %s",
            (resume_id,)
        )

    resume_skills = [s['skill_name'] for s in skills_records]

    try:
        analysis = analyze_resume_against_role(resume_skills, role_id, user_id=user_id, resume_id=resume_id)
        
        # Persist selected role in session
        session['selected_role_id'] = role_id
        session['selected_role_name'] = analysis['role_name']
        session['match_percentage'] = analysis['match_percentage']

        return jsonify({
            'status': 'success',
            'message': f"Role matching complete for '{analysis['role_name']}'.",
            'data': analysis
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Analysis error: {str(e)}'
        }), 400


@app.route('/api/roles/current', methods=['GET'])
@login_required
def api_get_current_role():
    """
    GET /api/roles/current
    Returns candidate's currently active selected role analysis.
    """
    user_id = session['user_id']
    selected = get_user_selected_role(user_id)

    if not selected:
        return jsonify({
            'status': 'success',
            'has_selection': False,
            'message': 'No target role selected yet.'
        }), 200

    # Fetch latest skills analysis for this role
    skills_records = fetch_all(
        "SELECT skill_name FROM resume_skills WHERE resume_id = %s",
        (selected['resume_id'],)
    ) if selected.get('resume_id') else []
    
    resume_skills = [s['skill_name'] for s in skills_records]
    analysis = analyze_resume_against_role(resume_skills, selected['role_id'])

    return jsonify({
        'status': 'success',
        'has_selection': True,
        'data': analysis
    }), 200


# =========================================================
# VOICE MOCK INTERVIEW & QUESTION ENGINE APIS (Phases 5 & 6)
# =========================================================

@app.route('/api/interview/setup-options', methods=['GET'])
@login_required
def api_interview_setup_options():
    """
    GET /api/interview/setup-options
    Provides setup parameters for the mock interview chamber:
    benchmark roles, difficulty levels, question quantity options,
    and candidate's current selected role.
    """
    user_id = session['user_id']
    roles = get_all_roles()
    selected_role = get_user_selected_role(user_id)
    latest_resume = fetch_one("SELECT id, filename FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))

    return jsonify({
        'status': 'success',
        'data': {
            'roles': roles,
            'selected_role': selected_role,
            'has_resume': latest_resume is not None,
            'resume_info': latest_resume,
            'difficulty_options': ['Easy', 'Medium', 'Hard'],
            'num_questions_options': [3, 5, 10]
        }
    }), 200


@app.route('/api/interview/start', methods=['POST'])
@login_required
def api_interview_start():
    """
    POST /api/interview/start
    Launches a new mock technical interview chamber.
    Selects non-repeating questions from MySQL based on role, resume skills, and difficulty.
    Payload: { role_id, difficulty, num_questions }
    """
    user_id = session['user_id']
    data = request.get_json(silent=True) or request.form

    role_id = data.get('role_id')
    try:
        role_id = int(role_id) if role_id else 1
    except ValueError:
        role_id = 1

    difficulty = data.get('difficulty', 'Medium')
    if difficulty not in ['Easy', 'Medium', 'Hard']:
        difficulty = 'Medium'

    try:
        num_questions = int(data.get('num_questions', 5))
        if num_questions < 1 or num_questions > 20:
            num_questions = 5
    except ValueError:
        num_questions = 5

    try:
        session_info = create_interview_session(
            user_id=user_id,
            role_id=role_id,
            difficulty=difficulty,
            num_questions=num_questions
        )

        return jsonify({
            'status': 'success',
            'message': 'Mock interview chamber initialized.',
            'data': session_info
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to initialize interview: {str(e)}'
        }), 500


@app.route('/api/interview/<int:interview_id>', methods=['GET'])
@login_required
def api_get_interview_state(interview_id):
    """
    GET /api/interview/<id>
    Fetches the current progression, assigned questions, and candidate answers.
    """
    user_id = session['user_id']
    state = get_current_interview_state(interview_id, user_id)
    if not state:
        return jsonify({
            'status': 'error',
            'message': 'Interview session not found or unauthorized.'
        }), 404

    return jsonify({
        'status': 'success',
        'data': state
    }), 200


@app.route('/api/interview/<int:interview_id>/answer', methods=['POST'])
@login_required
def api_save_interview_answer(interview_id):
    """
    POST /api/interview/<id>/answer
    Stores Speech-to-Text or typed answer for a specific question.
    Payload: { question_id, answer_text }
    """
    user_id = session['user_id']
    data = request.get_json(silent=True) or request.form

    question_id = data.get('question_id')
    answer_text = (data.get('answer_text') or '').strip()
    status = data.get('status', 'answered')

    if not question_id:
        return jsonify({
            'status': 'error',
            'message': 'question_id is required.'
        }), 400

    try:
        result = save_answer(interview_id, int(question_id), answer_text, user_id, status=status)
        return jsonify({
            'status': 'success',
            'message': 'Answer recorded in database.',
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to save answer: {str(e)}'
        }), 500


@app.route('/api/interview/<int:interview_id>/complete', methods=['POST'])
@login_required
def api_complete_interview(interview_id):
    """
    POST /api/interview/<id>/complete
    Finalizes the interview session, calculates final multi-dimensional scores,
    and generates personalized feedback (Phases 7 & 8).
    """
    user_id = session['user_id']
    interview = fetch_one("SELECT id FROM interviews WHERE id = %s AND user_id = %s", (interview_id, user_id))
    if not interview:
        return jsonify({'status': 'error', 'message': 'Interview session not found or unauthorized.'}), 404

    try:
        result_data = generate_interview_result(interview_id, user_id)
        return jsonify({
            'status': 'success',
            'message': 'Interview session concluded and scored successfully.',
            'data': result_data
        }), 200
    except Exception as e:
        execute_query("UPDATE interviews SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = %s", (interview_id,))
        return jsonify({
            'status': 'success',
            'message': f'Interview concluded (evaluation notice: {str(e)})',
            'data': {'interview_id': interview_id}
        }), 200


@app.route('/api/interview/<int:interview_id>/result', methods=['GET'])
@login_required
def api_get_interview_result(interview_id):
    """
    GET /api/interview/<id>/result
    Retrieves full evaluation scorecard, multi-dimensional scores,
    personalized feedback (strengths, weaknesses, recommendations),
    and per-question breakdown for Phase 8 Liquid Glass scorecard.
    """
    user_id = session['user_id']
    interview = fetch_one("SELECT id FROM interviews WHERE id = %s AND user_id = %s", (interview_id, user_id))
    if not interview:
        return jsonify({'status': 'error', 'message': 'Interview session not found or unauthorized.'}), 404

    try:
        result_data = generate_interview_result(interview_id, user_id)
        return jsonify({
            'status': 'success',
            'data': result_data
        }), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate or retrieve interview results: {str(err)}'
        }), 500


@app.route('/api/interview/latest-result', methods=['GET'])
@login_required
def api_get_latest_interview_result():
    """
    GET /api/interview/latest-result
    Convenience route: retrieves evaluation scorecard for candidate's latest interview.
    """
    user_id = session['user_id']
    latest = fetch_one(
        "SELECT id FROM interviews WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    if not latest:
        return jsonify({
            'status': 'error',
            'has_result': False,
            'message': 'No interview sessions found. Please launch an interview first.'
        }), 404

    try:
        result_data = generate_interview_result(latest['id'], user_id)
        return jsonify({
            'status': 'success',
            'has_result': True,
            'data': result_data
        }), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve latest interview result: {str(err)}'
        }), 500


@app.route('/api/interview/<int:interview_id>/pdf', methods=['GET'])
@login_required
def api_download_interview_pdf(interview_id):
    """
    GET /api/interview/<id>/pdf
    Generates and streams a professional ReportLab PDF assessment report.
    Enforces strict candidate session ownership.
    """
    user_id = session['user_id']
    interview = fetch_one("SELECT id FROM interviews WHERE id = %s AND user_id = %s", (interview_id, user_id))
    if not interview:
        return jsonify({'status': 'error', 'message': 'Interview session not found or unauthorized.'}), 404

    try:
        user = get_user_by_id(user_id)
        candidate_name = user['name'] if user else session.get('user_name', 'Candidate')
        result_data = generate_interview_result(interview_id, user_id)
        pdf_buffer = generate_interview_pdf_report(candidate_name, result_data)

        filename = f"NextHire_Interview_Report_NH_{interview_id:03d}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate PDF report: {str(err)}'
        }), 500


@app.route('/api/interviews/history', methods=['GET'])
@login_required
def api_interviews_history():
    """
    GET /api/interviews/history
    Fetches past mock interview sessions for the logged-in candidate with
    interview date, target role, question count, 1-5 overall score, and status.
    Only allows users to view their own interview history.
    """
    user_id = session['user_id']
    interviews = fetch_all(
        """
        SELECT i.id, i.difficulty, i.total_questions, i.started_at, i.completed_at, i.status,
               r.role_name,
               ir.overall_score,
               (SELECT COUNT(*) FROM answers a WHERE a.interview_id = i.id AND a.status != 'skipped') as answered_count
        FROM interviews i
        LEFT JOIN roles r ON i.role_id = r.id
        LEFT JOIN interview_results ir ON ir.interview_id = i.id
        WHERE i.user_id = %s
        ORDER BY i.id DESC
        """,
        (user_id,)
    )

    formatted = []
    for item in interviews:
        overall = item.get('overall_score')
        score_5 = round(overall / 20.0, 1) if overall is not None else None
        score_str = f"Score: {score_5} / 5" if score_5 is not None else "In Progress"

        raw_date = item.get('started_at')
        if raw_date:
            try:
                dt = datetime.strptime(str(raw_date)[:19], "%Y-%m-%d %H:%M:%S")
                date_formatted = dt.strftime("%d %B %Y")
            except Exception:
                date_formatted = str(raw_date)[:10]
        else:
            date_formatted = "Today"

        formatted.append({
            'id': item['id'],
            'session_code': f"#NH-2026-{item['id']:03d}",
            'role_name': item['role_name'] or 'Software Engineer',
            'difficulty': item['difficulty'] or 'Medium',
            'total_questions': item['total_questions'],
            'answered_count': item['answered_count'],
            'overall_score': overall,
            'score_5': score_5,
            'score_display': score_str,
            'date': date_formatted,
            'raw_date': str(raw_date)[:16] if raw_date else 'Today',
            'status': item['status']
        })

    return jsonify({
        'status': 'success',
        'data': formatted
    }), 200


# =========================================================
# DASHBOARD API (Updated for Phases 1-6)
# =========================================================

@app.route('/api/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    """
    GET /api/dashboard
    Returns summary statistics, real-time resume counts, completed interviews,
    target role, and recent activity.
    """
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)

    # Dynamic resume count
    resume_count_row = fetch_one("SELECT COUNT(*) as cnt FROM resumes WHERE user_id = %s", (user_id,))
    resumes_count = resume_count_row['cnt'] if resume_count_row else 0

    # Dynamic completed interviews count
    interviews_count_row = fetch_one("SELECT COUNT(*) as cnt FROM interviews WHERE user_id = %s AND status = 'completed'", (user_id,))
    interviews_completed = interviews_count_row['cnt'] if interviews_count_row else 0

    # Dynamic selected role
    selected_role = get_user_selected_role(user_id)
    target_role_name = selected_role['role_name'] if selected_role else session.get('selected_role_name', 'Full Stack Developer')

    # Dynamic readiness score from real evaluated interviews (Phase 8) or role match
    latest_result = fetch_one(
        """
        SELECT ir.overall_score
        FROM interview_results ir
        JOIN interviews i ON ir.interview_id = i.id
        WHERE i.user_id = %s
        ORDER BY ir.id DESC LIMIT 1
        """,
        (user_id,)
    )
    if latest_result:
        readiness_score = f"{round(latest_result['overall_score'], 1)}%"
    elif selected_role:
        readiness_score = f"{selected_role['match_percentage']}%"
    else:
        readiness_score = "Pending"

    recent_activities = [
        {
            'id': 'ACT-101',
            'title': 'Account Setup & Verification',
            'category': 'Onboarding',
            'date': 'Today',
            'status': 'Completed'
        }
    ]

    if resumes_count > 0:
        latest_res = fetch_one("SELECT filename, created_at FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        recent_activities.insert(0, {
            'id': 'ACT-102',
            'title': f"Resume Parsed: {latest_res['filename']}",
            'category': 'Resume NLP',
            'date': str(latest_res['created_at'])[:10] if latest_res.get('created_at') else 'Today',
            'status': 'Analyzed'
        })

    if selected_role:
        recent_activities.insert(0, {
            'id': 'ACT-103',
            'title': f"Role Matched: {selected_role['role_name']} ({selected_role['match_percentage']}%)",
            'category': 'Role Analysis',
            'date': 'Today',
            'status': 'Benchmarked'
        })

    if interviews_completed > 0:
        recent_activities.insert(0, {
            'id': 'ACT-104',
            'title': f"Mock Voice Interview & AI Evaluation ({target_role_name})",
            'category': 'Voice Interview',
            'date': 'Today',
            'status': 'Evaluated'
        })

    dashboard_data = {
        'user': {
            'id': user['id'] if user else user_id,
            'name': user['name'] if user else session.get('user_name', 'Candidate'),
            'email': user['email'] if user else session.get('user_email', '')
        },
        'stats': {
            'interviews_completed': interviews_completed,
            'resumes_analyzed': resumes_count,
            'readiness_score': readiness_score,
            'target_role': target_role_name
        },
        'phase': {
            'current': 'Phases 1 through 8 Active',
            'details': 'Auth, Resume Parsing, Role Analyzer, Question Bank, Voice Mock Chamber, AI Answer Scoring & Readiness Scorecard'
        },
        'recent_activity': recent_activities
    }

    return jsonify({
        'status': 'success',
        'data': dashboard_data
    }), 200


# =========================================================
# APPLICATION INITIALIZATION
# =========================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"==================================================")
    print(f"       NEXT HIRE - Full Stack Web Application     ")
    print(f"       MCA Academic Project (Phases 1 through 8)  ")
    print(f"==================================================")
    
    db_mode = init_db()
    print(f"[STATUS] Database engine initialized in {db_mode.upper()} mode.")
    print(f"[STATUS] Server running at: http://127.0.0.1:{port}/")
    print(f"==================================================")
    
    app.run(host='0.0.0.0', port=port, debug=True)
