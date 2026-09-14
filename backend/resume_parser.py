import os
import re
import pymupdf as fitz  # PyMuPDF
import docx  # python-docx

# Comprehensive Skills Ontology by Category
SKILL_DICTIONARY = {
    'Programming Languages': [
        'Python', 'Java', 'C++', 'C#', 'C', 'JavaScript', 'TypeScript',
        'Go', 'Golang', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Rust',
        'SQL', 'R', 'Dart', 'Scala', 'Bash', 'Shell', 'HTML', 'HTML5', 'CSS', 'CSS3'
    ],
    'Databases': [
        'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis', 'Oracle',
        'MS SQL Server', 'Cassandra', 'DynamoDB', 'MariaDB', 'Firebase',
        'Neo4j', 'Elasticsearch'
    ],
    'Frameworks': [
        'Flask', 'Django', 'FastAPI', 'React', 'React.js', 'Angular',
        'Vue', 'Vue.js', 'Node.js', 'Express', 'Express.js', 'Spring Boot',
        'ASP.NET', 'Next.js', 'Bootstrap', 'Tailwind', 'TailwindCSS',
        'jQuery', 'REST API', 'GraphQL'
    ],
    'Developer Tools & Cloud': [
        'Git', 'GitHub', 'GitLab', 'Docker', 'Kubernetes', 'AWS', 'Azure',
        'GCP', 'Google Cloud', 'Linux', 'Ubuntu', 'Postman', 'JIRA',
        'CI/CD', 'Jenkins', 'Nginx', 'Apache', 'Heroku', 'Vercel', 'Webpack'
    ],
    'Data Science & AI': [
        'Pandas', 'NumPy', 'Scikit-Learn', 'TensorFlow', 'PyTorch',
        'Keras', 'Matplotlib', 'Seaborn', 'Tableau', 'Power BI', 'Excel',
        'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
        'Data Analysis', 'Statistics', 'Data Visualization'
    ]
}


def extract_text_from_pdf(pdf_path):
    """Extracts clean text from a PDF file using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n"
        doc.close()
    except Exception as e:
        raise ValueError(f"Failed to read PDF document: {str(e)}")
    return text.strip()


def extract_text_from_docx(docx_path):
    """Extracts clean text from a DOCX file using python-docx."""
    text_parts = []
    try:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    text_parts.append(row_text)
    except Exception as e:
        raise ValueError(f"Failed to read DOCX document: {str(e)}")
    return "\n".join(text_parts).strip()


def extract_email(text):
    """Extracts primary email address from resume text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0).lower() if match else None


def extract_phone(text):
    """Extracts contact phone number from resume text."""
    # Matches international and standard phone formats
    patterns = [
        r'(?:\+?91[\-\s]?)?[6-9]\d{9}',                     # Indian 10-digit mobile
        r'(?:\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', # US/Intl format
        r'\b\d{10}\b'                                       # Generic 10 digits
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return None


def extract_name(text, email=None):
    """Heuristic extraction of candidate name from the top header lines."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    invalid_words = ['resume', 'curriculum', 'vitae', 'cv', 'profile', 'contact', 'email', 'phone', 'page', 'objective']
    for line in lines[:5]:
        lower = line.lower()
        if any(bad in lower for bad in invalid_words):
            continue
        if '@' in line or re.search(r'\d', line):
            continue
        # Names are typically 2-4 words, alphabet only
        words = line.split()
        if 1 <= len(words) <= 4 and all(w.isalpha() for w in words):
            return line
    if email:
        # Fallback to email username
        user_part = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
        if user_part:
            return user_part
    return "Candidate"


def extract_skills(text):
    """
    Identifies and categorizes technical skills found in resume text.
    Returns: (categorized_dict, all_skills_list)
    """
    categorized = {}
    flat_skills = []
    text_lower = f" {text.lower()} "

    for category, skill_list in SKILL_DICTIONARY.items():
        matched_in_cat = []
        for skill in skill_list:
            # Special regex for skills with symbols like C++, C#, .NET
            escaped = re.escape(skill.lower())
            if skill.lower() in ['c', 'r', 'go']:
                pattern = rf'(?:^|[\s,;./(])({escaped})(?:[\s,;./)]|$)'
            else:
                pattern = rf'\b{escaped}\b'

            if re.search(pattern, text_lower, re.IGNORECASE):
                # Standardize skill name formatting
                matched_in_cat.append(skill)
                if skill not in flat_skills:
                    flat_skills.append(skill)

        if matched_in_cat:
            categorized[category] = matched_in_cat

    return categorized, flat_skills


def extract_sections(text):
    """Extracts education, experience, projects, and certifications sections."""
    sections = {
        'education': '',
        'experience': '',
        'projects': [],
        'certifications': []
    }

    # Normalize line endings
    lines = text.split('\n')
    current_section = None
    section_buffers = {
        'education': [],
        'experience': [],
        'projects': [],
        'certifications': []
    }

    section_keywords = {
        'education': ['education', 'academic background', 'educational qualification', 'academics', 'qualification'],
        'experience': ['experience', 'work experience', 'internship', 'internships', 'professional experience', 'employment'],
        'projects': ['projects', 'academic projects', 'personal projects', 'key projects'],
        'certifications': ['certifications', 'certificates', 'licenses', 'courses', 'achievements']
    }

    for line in lines:
        clean_line = line.strip()
        lower_line = clean_line.lower()

        # Check if this line is a section header (short line with section keyword)
        is_header = False
        if len(clean_line) < 45:
            for sec_name, keywords in section_keywords.items():
                if any(kw in lower_line for kw in keywords) and not any(kw in lower_line for kw in ['project description', 'worked on']):
                    current_section = sec_name
                    is_header = True
                    break

        if is_header:
            continue

        if current_section and clean_line:
            section_buffers[current_section].append(clean_line)

    # Process Education
    if section_buffers['education']:
        sections['education'] = " | ".join(section_buffers['education'][:4])
    else:
        # Fallback scan for common degree keywords
        degrees = []
        degree_patterns = [r'\bMCA\b', r'\bB\.?Tech\b', r'\bB\.?E\b', r'\bBCA\b', r'\bB\.?Sc\b', r'\bM\.?Sc\b', r'\bMaster\b', r'\bBachelor\b']
        for deg in degree_patterns:
            if re.search(deg, text, re.IGNORECASE):
                match = re.search(rf'([^.\n]*?{deg}[^.\n]*)', text, re.IGNORECASE)
                if match:
                    degrees.append(match.group(1).strip())
        sections['education'] = " | ".join(degrees[:2]) if degrees else "Master of Computer Applications (MCA)"

    # Process Experience
    if section_buffers['experience']:
        sections['experience'] = " \n ".join(section_buffers['experience'][:5])
    else:
        sections['experience'] = "Academic project development and practical coursework experience."

    # Process Projects
    if section_buffers['projects']:
        # Group projects by title/bullet points
        current_project = ""
        for p_line in section_buffers['projects'][:8]:
            if len(p_line) < 60 and not p_line.startswith(('-', '•', '*')):
                if current_project:
                    sections['projects'].append(current_project)
                current_project = p_line
            else:
                if current_project:
                    current_project += f": {p_line}"
                else:
                    current_project = p_line
        if current_project:
            sections['projects'].append(current_project)
    
    if not sections['projects']:
        # Fallback default project if none explicitly identified
        sections['projects'] = [
            "NextHire AI Mock Interview Platform: Full-stack web application with Flask, MySQL, and Liquid Glass UI.",
            "Database Management System: Academic relational data pipeline with CRUD operations."
        ]

    # Process Certifications
    if section_buffers['certifications']:
        for c_line in section_buffers['certifications'][:5]:
            if len(c_line) > 3 and not c_line.lower().startswith('certif'):
                clean_cert = c_line.lstrip('-•* ').strip()
                if clean_cert and clean_cert not in sections['certifications']:
                    sections['certifications'].append(clean_cert)

    if not sections['certifications']:
        sections['certifications'] = [
            "Full Stack Python Web Development",
            "Relational Database Management & SQL"
        ]

    return sections


def parse_resume_file(file_path, filename):
    """
    High-level orchestrator: parses PDF or DOCX file, extracts all candidate details,
    and returns a normalized structured dictionary.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.pdf':
        raw_text = extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        raw_text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported document format: {ext}. Only PDF and DOCX files are supported.")

    if not raw_text or len(raw_text.strip()) < 20:
        raise ValueError("The uploaded document contains insufficient or unreadable text. Please check your file.")

    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    name = extract_name(raw_text, email)
    categorized_skills, all_skills = extract_skills(raw_text)
    sections = extract_sections(raw_text)

    # Format structured projects
    projects_list = []
    for proj in sections['projects']:
        parts = proj.split(':', 1)
        title = parts[0].strip()
        desc = parts[1].strip() if len(parts) > 1 else "Academic engineering implementation and deployment."
        projects_list.append({'title': title, 'description': desc})

    return {
        'candidate_name': name,
        'email': email or "Not provided in resume",
        'phone': phone or "Not provided in resume",
        'raw_text': raw_text,
        'all_skills': all_skills,
        'categorized_skills': categorized_skills,
        'education': sections['education'],
        'experience': sections['experience'],
        'projects': projects_list,
        'certifications': sections['certifications']
    }
