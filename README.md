# NEXT HIRE &bull; AI Mock Interview & Evaluation Platform
**Master of Computer Applications (MCA) Academic Project &bull; Phases 1 through 8**

NextHire is a modern full-stack web application engineered to bridge the gap between academic preparation and industry technical hiring standards. It provides automated candidate profiling, resume entity extraction (PDF/DOCX), target job role benchmarking, an authoritative 75-question MySQL Question Bank, an interactive Voice Mock Technical Interview Chamber (STT/TTS), and an AI Answer Analysis and Evaluation Scorecard Engine.

---

## 🌟 Architecture & Tech Stack

* **Backend Language:** Python 3.10+
* **Backend Framework:** Flask 3.1
* **Database Engine:** MySQL (`nexthire_db`) via `PyMySQL` (with automatic zero-friction fallback to SQLite for environments without an active MySQL service)
* **Resume Parsing Engine:** `PyMuPDF` (PDF text extraction) & `python-docx` (Word document parsing)
* **Question Engine:** Authority Question Bank (75 questions across Python, Java, C, JavaScript, SQL) imported from Excel via `openpyxl` with idempotent duplicate prevention.
* **Voice Mock Interview:** Browser Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition` for STT and `SpeechSynthesis` for TTS) with typed-answer fallback.
* **AI Evaluation Engine (Phase 7 & 8):** Multi-dimensional answer evaluation via Google Gemini / OpenAI with an Academic Heuristic NLP Fallback evaluator, weighted scoring formula, and personalized diagnostic feedback.
* **Frontend:** Semantic HTML5, Vanilla CSS3 (Liquid Glass Design System), Modular Vanilla JavaScript (ES6+ with `fetch` API)
* **Authentication:** Salted Cryptographic Password Hashing (`werkzeug.security`) & Server-Side HTTP-only Session Management
* **Design Aesthetic:** Liquid Glass / Glassmorphism with floating ambient orbs, translucent glass cards, backdrop-filter blur, and high-contrast visible form inputs.

---

## 📁 Project Directory Structure

```text
NextHire/
│
├── backend/
│   ├── app.py              # Flask server, static router & REST API routes
│   ├── database.py         # MySQL connection manager & auto-table initializer
│   ├── auth.py             # User registration, login verification & auth decorators
│   ├── resume_parser.py    # PyMuPDF & python-docx resume parsing & entity extraction
│   ├── role_analyzer.py    # Target role matching & missing skill identification engine
│   ├── import_questions.py # Excel Question Bank importer (idempotent, validates columns)
│   ├── question_engine.py  # Question selection engine & answer persistence manager
│   ├── answer_analyzer.py  # Phase 7 AI Answer Analyzer & Phase 8 Result Generator
│   ├── test_phase3_4.py    # Automated test suite for Phases 3 & 4
│   ├── test_phase5_6.py    # Automated test suite for Phases 5 & 6
│   ├── test_phase7_8.py    # Automated test suite for Phases 7 & 8
│   ├── uploads/            # Secure upload storage for candidate resumes
│   ├── .env.example        # Environment variables template
│   ├── .env                # Local active environment configuration
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── index.html          # 1. Landing page & platform architecture roadmap
│   ├── login.html          # 2. Candidate login portal with visible input fields
│   ├── register.html       # 3. Candidate registration with password strength meter
│   ├── dashboard.html      # 4. Protected candidate dashboard with readiness metrics
│   ├── upload.html         # 5. Resume upload (PDF/DOCX) & Role matching analyzer
│   ├── interview.html      # 6. Mock technical voice interview chamber (Phases 5 & 6)
│   ├── result.html         # 7. Candidate readiness scorecard & competency breakdown (Phase 8)
│   ├── history.html        # 8. Historical session archive with search & filter
│   │
│   ├── css/
│   │   └── style.css       # Complete Liquid Glass design system & responsive styling
│   │
│   └── js/
│       ├── main.js         # Session guard, toast notifications & global utilities
│       ├── login.js        # Login form handler with AJAX fetch
│       ├── register.js     # Registration form validation & strength meter
│       ├── dashboard.js    # Dashboard API consumer & metrics renderer
│       ├── upload.js       # Resume upload, entity display & role matching handler
│       ├── interview.js    # Voice Mock Interview controller (STT, TTS, state machine)
│       └── result.js       # Phase 8 Scorecard controller & question audit renderer
│
├── database/
│   ├── schema.sql          # Complete MySQL database schema (Phases 1-8)
│   └── NextHire Question Bank.xlsx # Source Excel Question Bank (75 valid questions)
│
└── README.md               # Project documentation & academic report guide
```

---

## 🗄️ Database Tables (Phases 1 through 8)

| Table | Phase | Purpose | Key Columns |
|---|---|---|---|
| `users` | 1 & 2 | Candidate accounts & secure password hashes | `id`, `name`, `email`, `password`, `created_at` |
| `resumes` | 3 | Stored candidate CVs with extracted text & contact info | `id`, `user_id`, `filename`, `file_path`, `raw_text`, `candidate_name`, `email`, `phone`, `education`, `experience` |
| `resume_skills` | 3 | Extracted candidate skills with categories | `id`, `resume_id`, `skill_name`, `category` |
| `resume_projects` | 3 | Extracted academic & personal projects | `id`, `resume_id`, `project_title`, `description` |
| `resume_certifications` | 3 | Extracted certifications & courses | `id`, `resume_id`, `certification_name` |
| `roles` | 4 | Benchmark industry job roles | `id`, `role_name`, `description` |
| `role_skills` | 4 | Role prerequisites & recommended skills | `id`, `role_id`, `skill_name`, `is_required` |
| `user_selected_roles` | 4 | Candidate chosen target role & match % | `id`, `user_id`, `role_id`, `resume_id`, `match_percentage` |
| `questions` | 5 | Source-of-truth questions from Excel bank | `id`, `question_code`, `language`, `topic`, `difficulty`, `question_text`, `active` |
| `interviews` | 5 | Mock interview sessions & progress tracking | `id`, `user_id`, `resume_id`, `role_id`, `difficulty`, `total_questions`, `status` |
| `interview_questions` | 5 | Ordered mapping of selected questions to session | `id`, `interview_id`, `question_id`, `question_order` |
| `answers` | 6 & 7 | Candidate answers with AI 1-5 multi-dimensional scores | `id`, `interview_id`, `question_id`, `answer_text`, `technical_score`, `communication_score`, `quality_score`, `confidence_score`, `feedback`, `strength`, `improvement`, `answered_at` |
| `interview_results` | 8 | Overall evaluation scorecard & personalized feedback | `id`, `interview_id`, `overall_score`, `technical_score`, `communication_score`, `quality_score`, `confidence_score`, `strengths`, `weaknesses`, `recommendations`, `created_at` |

---

## 📊 Question Bank & Import Statistics

* **Source File:** `database/NextHire Question Bank.xlsx`
* **Total Evaluated Rows:** 79 rows (1 sheet header, 74 data rows + 4 internal repeated language headers)
* **Valid Questions Imported:** Exactly **75 questions** (`PL001` through `PL075`).
* **Languages in Bank:**
  - Python: 15 questions
  - Java: 15 questions
  - C: 15 questions
  - JavaScript: 15 questions
  - SQL: 15 questions
* **Difficulties in Bank:**
  - Easy: 38 questions
  - Medium: 29 questions
  - Hard: 8 questions
* **Idempotence Verified:** Multiple executions of `import_questions.py` update existing records without creating duplicates.

---

## 🎙️ Voice Mock Interview Technology (Phase 6)

1. **Text-to-Speech (TTS):**
   - Implemented via `window.speechSynthesis` with `SpeechSynthesisUtterance`.
   - Reads question aloud at an academic 0.95x pace when the candidate clicks **🔊 Listen**.
   - Animates real-time visualizer wave bars during speech.
2. **Speech-to-Text (STT):**
   - Implemented via the browser `Web Speech API` (`SpeechRecognition` / `webkitSpeechRecognition`).
   - Supports continuous listening with live interim transcript updates.
   - Distinct 4-state visual indicator pill:
     - ⚪ **Ready**
     - 🔴 **Listening** (Pulsing waveform)
     - 🟡 **Processing**
     - 🟢 **Answer captured**
3. **Resilient Typing Fallback:**
   - If microphone permissions are denied, or speech recognition is unsupported, candidate can edit and type their answers directly into the high-contrast transcript textarea without application failure.

---

## 📡 REST API Documentation

| Method | Endpoint | Phase | Description |
|---|---|---|---|
| `POST` | `/api/register` | 1 & 2 | Candidate registration |
| `POST` | `/api/login` | 1 & 2 | Candidate login & session issuance |
| `POST` | `/api/logout` | 1 & 2 | Terminate session |
| `GET` | `/api/user` | 1 & 2 | Current candidate session profile |
| `GET` | `/api/dashboard` | 1 & 2 | Dynamic statistics (resumes, interviews completed, target role) |
| `POST` | `/api/resume/upload` | 3 | Upload & parse PDF/DOCX resume file |
| `GET` | `/api/resume` | 3 | Retrieve candidate's latest parsed resume |
| `GET` | `/api/roles` | 4 | List all benchmark roles & required skills |
| `POST` | `/api/roles/analyze` | 4 | Compare resume skills against role & calculate match |
| `GET` | `/api/roles/current` | 4 | Retrieve active selected role analysis |
| `GET` | `/api/interview/setup-options` | 5 | Get setup parameters (roles, difficulties, counts) |
| `POST` | `/api/interview/start` | 5 | Launch mock interview session & select unique questions |
| `GET` | `/api/interview/<id>` | 5 & 6 | Fetch interview state, current question, and answers |
| `POST` | `/api/interview/<id>/answer` | 6 & 7 | Save candidate speech/text answer and run AI evaluation |
| `POST` | `/api/interview/<id>/complete` | 6 & 8 | Finalize session, calculate final score, generate feedback |
| `GET` | `/api/interview/<id>/result` | 8 | Retrieve candidate readiness scorecard & audit breakdown |
| `GET` | `/api/interview/latest-result` | 8 | Retrieve scorecard for latest completed interview |
| `GET` | `/api/interviews/history` | 8 | Historical sessions archive with scores |

---

## 🚀 Setup & Execution Guide

```powershell
# 1. Install Python dependencies
pip install -r backend/requirements.txt

# 2. Import Question Bank from Excel
python backend/import_questions.py

# 3. Start Flask Web Server
python backend/app.py

# 4. Access Application in Browser
http://127.0.0.1:5000/

# 5. Run Automated Tests for Phases 7 & 8
python backend/test_phase7_8.py
```
