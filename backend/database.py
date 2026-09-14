import os
import sqlite3
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# Load environment variables from .env file
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME', 'nexthire_db')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

_USE_SQLITE_FALLBACK = False
_SQLITE_DB_PATH = os.path.join(base_dir, f'{DB_NAME}.sqlite')


def get_db_connection():
    """
    Establishes and returns a connection to MySQL database.
    If MySQL server is unavailable, falls back to local SQLite database
    to ensure zero-friction demonstration and testing.
    """
    global _USE_SQLITE_FALLBACK

    if not _USE_SQLITE_FALLBACK:
        try:
            connection = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            return connection
        except pymysql.MySQLError as err:
            print(f"[WARNING] MySQL connection failed ({err}). Engaging SQLite fallback engine at '{_SQLITE_DB_PATH}'.")
            _USE_SQLITE_FALLBACK = True

    conn = sqlite3.connect(_SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_roles_and_skills(cursor, is_sqlite=False):
    """Populates standard benchmark roles and associated skills."""
    roles_data = [
        (1, 'Python Developer', 'Specialized backend engineer developing scalable web services, APIs, and data automation scripts using Python.'),
        (2, 'Data Analyst', 'Analytical specialist interpreting complex datasets, preparing visual dashboards, and executing SQL pipelines for business decisions.'),
        (3, 'Full Stack Developer', 'End-to-end software engineer capable of delivering responsive modern frontends and robust scalable backend services.'),
        (4, 'Software Engineer', 'Core engineering professional with solid foundations in algorithms, system design, object-oriented principles, and scalable architectures.')
    ]

    skills_data = [
        # Python Developer (role_id 1)
        (1, 'Python', 1), (1, 'Flask', 1), (1, 'MySQL', 1), (1, 'REST API', 1), (1, 'Git', 1),
        (1, 'Django', 0), (1, 'Docker', 0), (1, 'PostgreSQL', 0), (1, 'Linux', 0),
        # Data Analyst (role_id 2)
        (2, 'Python', 1), (2, 'SQL', 1), (2, 'Excel', 1), (2, 'Pandas', 1), (2, 'Tableau', 1),
        (2, 'Power BI', 0), (2, 'NumPy', 0), (2, 'Statistics', 1), (2, 'Data Visualization', 1),
        # Full Stack Developer (role_id 3)
        (3, 'JavaScript', 1), (3, 'HTML', 1), (3, 'CSS', 1), (3, 'Python', 1), (3, 'Flask', 1),
        (3, 'MySQL', 1), (3, 'React', 0), (3, 'Node.js', 0), (3, 'REST API', 1), (3, 'Git', 1),
        # Software Engineer (role_id 4)
        (4, 'Python', 1), (4, 'Java', 0), (4, 'Data Structures', 1), (4, 'Algorithms', 1),
        (4, 'SQL', 1), (4, 'Git', 1), (4, 'System Design', 1), (4, 'OOP', 1), (4, 'Linux', 0)
    ]

    for role_id, name, desc in roles_data:
        if is_sqlite:
            cursor.execute("INSERT OR IGNORE INTO roles (id, role_name, description) VALUES (?, ?, ?)", (role_id, name, desc))
        else:
            cursor.execute("INSERT INTO roles (id, role_name, description) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE role_name=VALUES(role_name)", (role_id, name, desc))

    for r_id, s_name, req in skills_data:
        if is_sqlite:
            cursor.execute("SELECT id FROM role_skills WHERE role_id = ? AND skill_name = ?", (r_id, s_name))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO role_skills (role_id, skill_name, is_required) VALUES (?, ?, ?)", (r_id, s_name, req))
        else:
            cursor.execute("SELECT id FROM role_skills WHERE role_id = %s AND skill_name = %s", (r_id, s_name))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO role_skills (role_id, skill_name, is_required) VALUES (%s, %s, %s)", (r_id, s_name, req))


def init_db():
    """
    Initializes database and creates all tables for Phases 1 through 6.
    Handles both MySQL and SQLite fallback modes.
    """
    global _USE_SQLITE_FALLBACK

    try:
        server_conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        with server_conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        server_conn.close()

        db_conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with db_conn.cursor() as cursor:
            # Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(150) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Resumes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    raw_text LONGTEXT,
                    candidate_name VARCHAR(100),
                    email VARCHAR(150),
                    phone VARCHAR(50),
                    education TEXT,
                    experience TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_resume_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Resume Skills
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resume_skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    resume_id INT NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) DEFAULT 'General',
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
                    INDEX idx_skill_resume (resume_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Resume Projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resume_projects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    resume_id INT NOT NULL,
                    project_title VARCHAR(200) NOT NULL,
                    description TEXT,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Resume Certifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resume_certifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    resume_id INT NOT NULL,
                    certification_name VARCHAR(255) NOT NULL,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Roles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    role_name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Role Skills
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS role_skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    role_id INT NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    is_required BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # User Selected Roles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_selected_roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    role_id INT NOT NULL,
                    resume_id INT,
                    matched_skills_count INT DEFAULT 0,
                    missing_skills_count INT DEFAULT 0,
                    match_percentage INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Questions (Phase 5)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_code VARCHAR(50) NOT NULL UNIQUE,
                    language VARCHAR(100) NOT NULL,
                    topic VARCHAR(100) NOT NULL,
                    difficulty VARCHAR(50) NOT NULL,
                    question_text TEXT NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_q_lang (language),
                    INDEX idx_q_diff (difficulty),
                    INDEX idx_q_code (question_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Interviews (Phase 5)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interviews (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    resume_id INT,
                    role_id INT,
                    difficulty VARCHAR(50) DEFAULT 'Medium',
                    total_questions INT DEFAULT 5,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    status VARCHAR(50) DEFAULT 'in_progress',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Interview Questions (Phase 5)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    interview_id INT NOT NULL,
                    question_id INT NOT NULL,
                    question_order INT NOT NULL,
                    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            # Answers (Phases 6 & 7 AI Answer Analysis)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    interview_id INT NOT NULL,
                    question_id INT NOT NULL,
                    answer_text TEXT,
                    technical_score INT DEFAULT NULL,
                    communication_score INT DEFAULT NULL,
                    quality_score INT DEFAULT NULL,
                    confidence_score INT DEFAULT NULL,
                    feedback TEXT,
                    strength TEXT,
                    improvement TEXT,
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Migrate answers columns if table was created previously without them
            cursor.execute("SHOW COLUMNS FROM answers LIKE 'technical_score'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE answers ADD COLUMN technical_score INT DEFAULT NULL")
                cursor.execute("ALTER TABLE answers ADD COLUMN communication_score INT DEFAULT NULL")
                cursor.execute("ALTER TABLE answers ADD COLUMN quality_score INT DEFAULT NULL")
                cursor.execute("ALTER TABLE answers ADD COLUMN confidence_score INT DEFAULT NULL")
                cursor.execute("ALTER TABLE answers ADD COLUMN feedback TEXT DEFAULT NULL")
                cursor.execute("ALTER TABLE answers ADD COLUMN strength TEXT DEFAULT NULL")
                cursor.execute("ALTER TABLE answers ADD COLUMN improvement TEXT DEFAULT NULL")

            # Interview Results (Phase 8 Final Result & Personalized Feedback)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    interview_id INT NOT NULL UNIQUE,
                    overall_score FLOAT NOT NULL,
                    technical_score FLOAT NOT NULL,
                    communication_score FLOAT NOT NULL,
                    quality_score FLOAT NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    strengths TEXT,
                    weaknesses TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            _seed_roles_and_skills(cursor, is_sqlite=False)
            db_conn.commit()

        db_conn.close()
        _USE_SQLITE_FALLBACK = False
        print(f"[SUCCESS] Connected to MySQL successfully. All tables ready.")
        return "mysql"

    except Exception as err:
        print(f"[NOTICE] MySQL initialization check: {err}")
        print(f"[INFO] Initializing fallback database engine for seamless testing...")
        _USE_SQLITE_FALLBACK = True

        conn = sqlite3.connect(_SQLITE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                raw_text TEXT,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                education TEXT,
                experience TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                project_title TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_certifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                certification_name TEXT NOT NULL,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                is_required INTEGER DEFAULT 1,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_selected_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                resume_id INTEGER,
                matched_skills_count INTEGER DEFAULT 0,
                missing_skills_count INTEGER DEFAULT 0,
                match_percentage INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_code TEXT NOT NULL UNIQUE,
                language TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                question_text TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_q_lang ON questions(language);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_q_diff ON questions(difficulty);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_q_code ON questions(question_code);")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resume_id INTEGER,
                role_id INTEGER,
                difficulty TEXT DEFAULT 'Medium',
                total_questions INTEGER DEFAULT 5,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'in_progress',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                question_order INTEGER NOT NULL,
                FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                technical_score INTEGER,
                communication_score INTEGER,
                quality_score INTEGER,
                confidence_score INTEGER,
                feedback TEXT,
                strength TEXT,
                improvement TEXT,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
        """)

        # Check and migrate columns in answers table if existing
        cursor.execute("PRAGMA table_info(answers);")
        existing_cols = [c[1] for c in cursor.fetchall()]
        sqlite_new_cols = [
            ('technical_score', 'INTEGER'),
            ('communication_score', 'INTEGER'),
            ('quality_score', 'INTEGER'),
            ('confidence_score', 'INTEGER'),
            ('feedback', 'TEXT'),
            ('strength', 'TEXT'),
            ('improvement', 'TEXT')
        ]
        for col_name, col_type in sqlite_new_cols:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE answers ADD COLUMN {col_name} {col_type};")

        # Interview Results (Phase 8 Final Result & Personalized Feedback)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL UNIQUE,
                overall_score REAL NOT NULL,
                technical_score REAL NOT NULL,
                communication_score REAL NOT NULL,
                quality_score REAL NOT NULL,
                confidence_score REAL NOT NULL,
                strengths TEXT,
                weaknesses TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
            );
        """)

        _seed_roles_and_skills(cursor, is_sqlite=True)
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Fallback database initialized at '{_SQLITE_DB_PATH}' with all Phase 1-8 tables.")
        return "sqlite"


def execute_query(query, params=None, commit=True):
    conn = get_db_connection()
    if _USE_SQLITE_FALLBACK:
        sqlite_query = query.replace('%s', '?')
        cursor = conn.cursor()
        try:
            cursor.execute(sqlite_query, params or ())
            if commit:
                conn.commit()
            last_id = cursor.lastrowid
            return last_id
        finally:
            cursor.close()
            conn.close()
    else:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if commit:
                    conn.commit()
                last_id = cursor.lastrowid
                return last_id
        finally:
            conn.close()


def fetch_one(query, params=None):
    conn = get_db_connection()
    if _USE_SQLITE_FALLBACK:
        sqlite_query = query.replace('%s', '?')
        cursor = conn.cursor()
        try:
            cursor.execute(sqlite_query, params or ())
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()
            conn.close()
    else:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                return row
        finally:
            conn.close()


def fetch_all(query, params=None):
    conn = get_db_connection()
    if _USE_SQLITE_FALLBACK:
        sqlite_query = query.replace('%s', '?')
        cursor = conn.cursor()
        try:
            cursor.execute(sqlite_query, params or ())
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            cursor.close()
            conn.close()
    else:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                rows = cursor.fetchall()
                return rows
        finally:
            conn.close()


if __name__ == '__main__':
    print("Testing Database Configuration...")
    mode = init_db()
    print(f"Database initialized in mode: {mode}")
