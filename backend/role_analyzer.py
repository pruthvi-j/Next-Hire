from database import fetch_all, fetch_one, execute_query


def get_all_roles():
    """
    Fetches all available job roles along with their required/recommended skills.
    """
    roles = fetch_all("SELECT id, role_name, description FROM roles ORDER BY id ASC")
    if not roles:
        return []

    roles_list = []
    for r in roles:
        skills = fetch_all(
            "SELECT skill_name, is_required FROM role_skills WHERE role_id = %s ORDER BY is_required DESC, skill_name ASC",
            (r['id'],)
        )
        roles_list.append({
            'id': r['id'],
            'role_name': r['role_name'],
            'description': r['description'],
            'skills': [s['skill_name'] for s in skills],
            'required_skills': [s['skill_name'] for s in skills if s.get('is_required')]
        })
    return roles_list


def get_role_by_id(role_id):
    """Fetches single role details by ID."""
    role = fetch_one("SELECT id, role_name, description FROM roles WHERE id = %s", (role_id,))
    if not role:
        return None

    skills = fetch_all(
        "SELECT skill_name, is_required FROM role_skills WHERE role_id = %s ORDER BY is_required DESC, skill_name ASC",
        (role_id,)
    )
    role['skills'] = [s['skill_name'] for s in skills]
    role['required_skills'] = [s['skill_name'] for s in skills if s.get('is_required')]
    return role


def normalize_skill(skill):
    """Cleans and standardizes skill names for fuzzy semantic matching."""
    s = skill.lower().strip()
    s = s.replace('.js', '').replace('css3', 'css').replace('html5', 'html')
    # Standard synonyms
    synonyms = {
        'postgres': 'postgresql',
        'reactjs': 'react',
        'nodejs': 'node',
        'restful api': 'rest api',
        'restful apis': 'rest api',
        'rest apis': 'rest api',
        'tailwindcss': 'tailwind',
        'powerbi': 'power bi'
    }
    return synonyms.get(s, s)


def analyze_resume_against_role(resume_skills, role_id, user_id=None, resume_id=None):
    """
    Compares resume skills against target job role skills.
    Identifies matched skills, missing/recommended skills, and match percentage.
    Stores the candidate's selected role in the database.
    """
    role = get_role_by_id(role_id)
    if not role:
        raise ValueError(f"Target role ID {role_id} does not exist.")

    role_skills = role.get('skills', [])
    if not role_skills:
        return {
            'role_id': role['id'],
            'role_name': role['role_name'],
            'matched_skills': [],
            'missing_skills': [],
            'match_percentage': 0,
            'readiness_rating': 'Not Assessed'
        }

    # Normalize resume skills set
    norm_resume_skills = {normalize_skill(s): s for s in resume_skills}

    matched_skills = []
    missing_skills = []

    for r_skill in role_skills:
        norm_r_skill = normalize_skill(r_skill)
        
        # Direct or normalized match
        is_matched = False
        if norm_r_skill in norm_resume_skills:
            is_matched = True
        elif any(norm_r_skill in norm_cand or norm_cand in norm_r_skill for norm_cand in norm_resume_skills):
            is_matched = True

        if is_matched:
            matched_skills.append(r_skill)
        else:
            missing_skills.append(r_skill)

    # Calculate match percentage
    total_role_skills = len(role_skills)
    match_percentage = int(round((len(matched_skills) / total_role_skills) * 100)) if total_role_skills > 0 else 0

    # Categorize readiness
    if match_percentage >= 80:
        readiness_rating = "Strong Candidate Readiness &bull; Optimal Fit"
        readiness_badge = "success"
    elif match_percentage >= 50:
        readiness_rating = "Moderate Readiness &bull; Recommended Skill Additions"
        readiness_badge = "warning"
    else:
        readiness_rating = "Foundational Readiness &bull; Targeted Upskilling Advised"
        readiness_badge = "danger"

    # Save to user_selected_roles if user_id is provided
    if user_id:
        try:
            # Delete previous user selection for this role or keep history
            execute_query(
                """
                INSERT INTO user_selected_roles 
                (user_id, role_id, resume_id, matched_skills_count, missing_skills_count, match_percentage)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, role['id'], resume_id, len(matched_skills), len(missing_skills), match_percentage)
            )
        except Exception as e:
            print(f"[NOTICE] Could not persist user_selected_roles: {e}")

    return {
        'role_id': role['id'],
        'role_name': role['role_name'],
        'description': role['description'],
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'matched_count': len(matched_skills),
        'missing_count': len(missing_skills),
        'total_skills': total_role_skills,
        'match_percentage': match_percentage,
        'readiness_rating': readiness_rating,
        'readiness_badge': readiness_badge
    }


def get_user_selected_role(user_id):
    """Retrieves the candidate's most recently selected role and benchmark scores."""
    record = fetch_one(
        """
        SELECT usr.*, r.role_name, r.description 
        FROM user_selected_roles usr
        JOIN roles r ON usr.role_id = r.id
        WHERE usr.user_id = %s
        ORDER BY usr.id DESC LIMIT 1
        """,
        (user_id,)
    )
    return record
