-- =========================================================
-- NEXT HIRE - Database Schema
-- MCA Academic Project - Phases 1, 2, 3, 4, 5 & 6
-- =========================================================

CREATE DATABASE IF NOT EXISTS nexthire_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE nexthire_db;

-- 1. Users Table (Phase 1 & 2)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Resumes Table (Phase 3)
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

-- 3. Resume Skills Table (Phase 3)
CREATE TABLE IF NOT EXISTS resume_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) DEFAULT 'General',
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
    INDEX idx_skill_resume (resume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Resume Projects Table (Phase 3)
CREATE TABLE IF NOT EXISTS resume_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_id INT NOT NULL,
    project_title VARCHAR(200) NOT NULL,
    description TEXT,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
    INDEX idx_project_resume (resume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Resume Certifications Table (Phase 3)
CREATE TABLE IF NOT EXISTS resume_certifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_id INT NOT NULL,
    certification_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
    INDEX idx_cert_resume (resume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Roles Table (Phase 4)
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Role Skills Table (Phase 4)
CREATE TABLE IF NOT EXISTS role_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    is_required BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    INDEX idx_role_skill (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. User Selected Roles (Phase 4)
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
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    INDEX idx_user_role (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Questions Table (Phase 5 Question Bank + Phase 9 Concept-Based Evaluation)
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_code VARCHAR(50) NOT NULL UNIQUE,
    language VARCHAR(100) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    difficulty VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    expected_answer TEXT DEFAULT NULL,
    key_concepts TEXT DEFAULT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_q_lang (language),
    INDEX idx_q_diff (difficulty),
    INDEX idx_q_code (question_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Interviews Table (Phase 5)
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
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL,
    INDEX idx_interview_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Interview Questions Table (Phase 5)
CREATE TABLE IF NOT EXISTS interview_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL,
    question_id INT NOT NULL,
    question_order INT NOT NULL,
    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    INDEX idx_iq_interview (interview_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Answers Table (Phases 6 & 7 AI Answer Analysis)
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
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    INDEX idx_ans_interview (interview_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Interview Results Table (Phase 8 Final Result & Personalized Feedback)
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
    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
    INDEX idx_res_interview (interview_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- Initial Seed Roles & Skills (Phase 4)
-- =========================================================
INSERT INTO roles (id, role_name, description) VALUES
(1, 'Python Developer', 'Specialized backend engineer developing scalable web services, APIs, and data automation scripts using Python.'),
(2, 'Data Analyst', 'Analytical specialist interpreting complex datasets, preparing visual dashboards, and executing SQL pipelines for business decisions.'),
(3, 'Full Stack Developer', 'End-to-end software engineer capable of delivering responsive modern frontends and robust scalable backend services.'),
(4, 'Software Engineer', 'Core engineering professional with solid foundations in algorithms, system design, object-oriented principles, and scalable architectures.')
ON DUPLICATE KEY UPDATE role_name = VALUES(role_name);

INSERT INTO role_skills (role_id, skill_name, is_required) VALUES
(1, 'Python', TRUE), (1, 'Flask', TRUE), (1, 'MySQL', TRUE), (1, 'REST API', TRUE), (1, 'Git', TRUE),
(1, 'Django', FALSE), (1, 'Docker', FALSE), (1, 'PostgreSQL', FALSE), (1, 'Linux', FALSE),
(2, 'Python', TRUE), (2, 'SQL', TRUE), (2, 'Excel', TRUE), (2, 'Pandas', TRUE), (2, 'Tableau', TRUE),
(2, 'Power BI', FALSE), (2, 'NumPy', FALSE), (2, 'Statistics', TRUE), (2, 'Data Visualization', TRUE),
(3, 'JavaScript', TRUE), (3, 'HTML', TRUE), (3, 'CSS', TRUE), (3, 'Python', TRUE), (3, 'Flask', TRUE),
(3, 'MySQL', TRUE), (3, 'React', FALSE), (3, 'Node.js', FALSE), (3, 'REST API', TRUE), (3, 'Git', TRUE),
(4, 'Python', TRUE), (4, 'Java', FALSE), (4, 'Data Structures', TRUE), (4, 'Algorithms', TRUE),
(4, 'SQL', TRUE), (4, 'Git', TRUE), (4, 'System Design', TRUE), (4, 'OOP', TRUE), (4, 'Linux', FALSE)
ON DUPLICATE KEY UPDATE skill_name = VALUES(skill_name);
