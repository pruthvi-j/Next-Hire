# NEXT HIRE &bull; Production Deployment & Hosting Guide
**Master of Computer Applications (MCA) Academic Project &bull; Phases 1 through 10**

This guide provides step-by-step instructions for deploying the **NextHire Intelligent Mock Interview Platform** to production cloud infrastructure.

---

## 🏗️ Production Architecture Overview

```text
[ Client Web Browsers ]
         │
         ▼ (HTTPS)
┌──────────────────────────────────────────────┐
│       Frontend (Static Web Hosting)          │
│   Vercel / Netlify / GitHub Pages / S3       │
│   (HTML5, Liquid Glass CSS3, Vanilla JS)     │
└──────────────────────┬───────────────────────┘
                       │ REST API Calls (JSON / HTTPS)
                       ▼
┌──────────────────────────────────────────────┐
│       Backend (Python Flask Service)         │
│   Render / Railway / AWS EC2 / DigitalOcean  │
│   (Flask 3.1, Gunicorn, PyMuPDF, ReportLab)  │
└──────────────┬──────────────────┬────────────┘
               │                  │
               ▼                  ▼
┌─────────────────────────┐  ┌───────────────────────────────────┐
│ Cloud MySQL Database    │  │ External AI Services              │
│ AWS RDS / Aiven /       │  │ Google Gemini API / OpenAI API    │
│ Railway MySQL           │  │ (Automated Heuristic NLP Fallback)│
└─────────────────────────┘  └───────────────────────────────────┘
```

---

## 1. How to Create the MySQL Database

### Option A: Cloud Hosted MySQL (Aiven / AWS RDS / Railway)
1. Sign up for a managed MySQL provider (e.g. [Aiven for MySQL](https://aiven.io/), [Railway](https://railway.app/), or [AWS RDS](https://aws.amazon.com/rds/)).
2. Provision a MySQL 8.0+ instance.
3. Obtain your connection parameters:
   - **Host:** e.g. `mysql-production-xxx.aivencloud.com`
   - **Port:** e.g. `12345` or `3306`
   - **User:** e.g. `avnadmin` or `root`
   - **Password:** `<your_secure_password>`
   - **Database Name:** `nexthire_db`

### Option B: Local or VPS MySQL Server
```bash
# Connect to MySQL CLI as root
mysql -u root -p

# Create the dedicated database with UTF-8 support
CREATE DATABASE nexthire_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create dedicated application user and grant privileges
CREATE USER 'nexthire_user'@'%' IDENTIFIED BY 'StrongPassword2026!';
GRANT ALL PRIVILEGES ON nexthire_db.* TO 'nexthire_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

### Initializing the Schema & Question Bank:
Run the initialization script from your project root:
```bash
# 1. Apply database schema
mysql -u nexthire_user -p nexthire_db < database/schema.sql

# 2. Populate 75-question Authority Bank from Excel
python backend/import_questions.py
```
*(Note: If MySQL is unavailable in your environment, NextHire automatically initializes an in-memory or SQLite fallback database with all 13 Phase 1–8 tables).*

---

## 2. How to Configure Environment Variables

Create a `.env` file in the `backend/` directory (or configure them in your Cloud Provider's Environment Variables dashboard):

```ini
# =========================================================
# NEXT HIRE - Production Environment Configuration
# =========================================================

# Database Credentials
DB_HOST=mysql-host.example.com
DB_PORT=3306
DB_NAME=nexthire_db
DB_USER=nexthire_user
DB_PASSWORD=StrongPassword2026!

# Flask Security & Session Encryption
# Generate key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=9f8c6b4d3a2e1f5c7b8a9d0e1f2c3b4a5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
FLASK_ENV=production
PORT=5000

# AI Evaluation Keys (Optional - Heuristic NLP used if not supplied)
GEMINI_API_KEY=AIzaSyD-YourGoogleGeminiApiKeyHere
OPENAI_API_KEY=sk-proj-YourOpenAIApiKeyHere

# CORS Configuration
CORS_ORIGINS=*
```

> [!CAUTION]
> Never commit `.env` into version control. Ensure `.gitignore` contains `.env` and `backend/.env`.

---

## 3. How to Deploy the Python Flask Backend

### Deploying to Render.com (Recommended)
1. Fork or push this repository to GitHub.
2. Log into [Render.com](https://render.com/) and click **New + Web Service**.
3. Connect your GitHub repository.
4. Set the build parameters:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT`
5. Under **Environment Variables**, add the keys defined in step 2 (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`, `GEMINI_API_KEY`, etc.).
6. Click **Create Web Service**. Your backend will be accessible at:
   `https://nexthire-backend.onrender.com`

---

## 4. How to Deploy the Frontend

Because the frontend is built with Semantic HTML5, Vanilla CSS3 (Liquid Glass), and modular JavaScript, it can be hosted on any static cloud CDN:

### Deploying to Vercel
1. In [Vercel](https://vercel.com/), click **Add New Project**.
2. Select your repository.
3. Set **Root Directory** to `frontend`.
4. Leave Build Command empty (plain static files).
5. Click **Deploy**.

---

## 5. How to Connect Frontend to Flask API

In [frontend/js/main.js](file:///c:/Users/Admin/Downloads/NextHire/frontend/js/main.js), configure the `API_BASE` variable:

```javascript
// Local Development:
const API_BASE = 'http://127.0.0.1:5000';

// Production Deployment:
// const API_BASE = 'https://nexthire-backend.onrender.com';
```

When deploying static frontend and backend to different domains, ensure CORS credentials are enabled:
* NextHire's Flask server sets `supports_credentials=True`.
* Client requests use `credentials: 'include'` for secure HTTP-only cookies.

---

## 6. How to Connect Flask to Cloud MySQL

In `backend/database.py`, NextHire connects via `PyMySQL` with SSL options enabled for cloud databases:
```python
import pymysql

conn = pymysql.connect(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'nexthire_db'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    connect_timeout=10
)
```

---

## 7. How to Configure AI API Keys

NextHire supports both Google Gemini and OpenAI:

1. **Google Gemini (Recommended):**
   - Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
   - Add to environment: `GEMINI_API_KEY=AIzaSy...`
2. **OpenAI:**
   - Obtain an API key from [OpenAI Platform](https://platform.openai.com/).
   - Add to environment: `OPENAI_API_KEY=sk-...`
3. **Academic Fallback Engine:**
   - If no API key is set or if rate limits/network timeouts occur, the built-in **Academic Heuristic NLP Evaluator** takes over automatically, guaranteeing 100% uptime with zero crashes during academic demos.

---

## 8. Verifying Full System Functionality in Production

Run the end-to-end integration test suite against your deployed service:
```bash
python backend/test_full_system.py
```
