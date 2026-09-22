import random
from database import fetch_all, fetch_one, execute_query

# Mapping roles to primary languages present in the question bank
# Question Bank Languages: Python, Java, C, JavaScript, SQL
ROLE_LANGUAGE_MAP = {
    1: ['Python', 'SQL'],                     # Python Developer
    2: ['SQL', 'Python'],                     # Data Analyst
    3: ['JavaScript', 'Python', 'SQL'],       # Full Stack Developer
    4: ['Python', 'Java', 'C', 'SQL']         # Software Engineer
}


def get_resume_skills_for_user(user_id, resume_id=None):
    """Fetches detected skills from the candidate's active or specified resume."""
    if resume_id:
        rows = fetch_all("SELECT skill_name FROM resume_skills WHERE resume_id = %s", (resume_id,))
    else:
        latest = fetch_one("SELECT id FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        if not latest:
            return []
        rows = fetch_all("SELECT skill_name FROM resume_skills WHERE resume_id = %s", (latest['id'],))
    return [r['skill_name'] for r in rows] if rows else []


def select_questions_for_interview(role_id, resume_skills=None, difficulty='Medium', num_questions=5, existing_question_ids=None):
    """
    Selects balanced, non-repeating questions from MySQL based on:
    1. Selected job role
    2. Resume skills
    3. Language affinity
    4. Topic
    5. Difficulty
    With a graceful fallback to other active questions if exact criteria are exhausted.
    """
    resume_skills = resume_skills or []
    existing_question_ids = set(existing_question_ids or [])
    selected_questions = []

    # 1. Determine target languages
    target_languages = ROLE_LANGUAGE_MAP.get(role_id, ['Python', 'SQL', 'JavaScript'])
    
    # Check if resume skills contain additional specific languages from question bank
    bank_languages = ['Python', 'Java', 'C', 'JavaScript', 'SQL']
    for skill in resume_skills:
        for bl in bank_languages:
            if bl.lower() == skill.lower() and bl not in target_languages:
                target_languages.append(bl)

    # 2. Query matching questions by target languages
    # Match primary difficulty first
    norm_diff = difficulty.capitalize() if difficulty and difficulty != 'All' else None

    # Step A: High-priority pool (matching target languages & requested difficulty)
    if norm_diff:
        placeholders = ', '.join(['%s'] * len(target_languages))
        query_a = f"""
            SELECT id, question_code, language, topic, difficulty, question_text 
            FROM questions 
            WHERE active = 1 AND language IN ({placeholders}) AND difficulty = %s
            ORDER BY id ASC
        """
        params_a = list(target_languages) + [norm_diff]
        pool_a = fetch_all(query_a, tuple(params_a))
    else:
        pool_a = []

    # Filter out already selected
    candidates_a = [q for q in pool_a if q['id'] not in existing_question_ids]
    random.seed(role_id + len(resume_skills) + num_questions)
    random.shuffle(candidates_a)

    for q in candidates_a:
        if len(selected_questions) < num_questions:
            selected_questions.append(q)
            existing_question_ids.add(q['id'])

    # Step B: Moderate-priority pool (matching target languages, any difficulty)
    if len(selected_questions) < num_questions:
        placeholders = ', '.join(['%s'] * len(target_languages))
        query_b = f"""
            SELECT id, question_code, language, topic, difficulty, question_text 
            FROM questions 
            WHERE active = 1 AND language IN ({placeholders})
            ORDER BY id ASC
        """
        pool_b = fetch_all(query_b, tuple(target_languages))
        candidates_b = [q for q in pool_b if q['id'] not in existing_question_ids]
        random.shuffle(candidates_b)

        for q in candidates_b:
            if len(selected_questions) < num_questions:
                selected_questions.append(q)
                existing_question_ids.add(q['id'])

    # Step C: Graceful Fallback (any active question from the bank to fulfill the question quota)
    if len(selected_questions) < num_questions:
        all_pool = fetch_all("SELECT id, question_code, language, topic, difficulty, question_text FROM questions WHERE active = 1 ORDER BY id ASC")
        fallback_candidates = [q for q in all_pool if q['id'] not in existing_question_ids]
        random.shuffle(fallback_candidates)

        for q in fallback_candidates:
            if len(selected_questions) < num_questions:
                selected_questions.append(q)
                existing_question_ids.add(q['id'])

    return selected_questions


def create_interview_session(user_id, role_id=1, resume_id=None, difficulty='Medium', num_questions=5):
    """
    Creates an interview record and links selected questions in order.
    Guarantees no duplicate questions are chosen.
    """
    # Verify role
    role = fetch_one("SELECT id, role_name FROM roles WHERE id = %s", (role_id,))
    if not role:
        role_id = 1

    # Verify latest resume if not passed
    if not resume_id:
        latest_res = fetch_one("SELECT id FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        if latest_res:
            resume_id = latest_res['id']

    resume_skills = get_resume_skills_for_user(user_id, resume_id)

    # 1. Insert into interviews table
    interview_id = execute_query(
        """
        INSERT INTO interviews (user_id, resume_id, role_id, difficulty, total_questions, status)
        VALUES (%s, %s, %s, %s, %s, 'in_progress')
        """,
        (user_id, resume_id, role_id, difficulty, num_questions)
    )

    # 2. Select appropriate non-repeating questions
    selected_questions = select_questions_for_interview(
        role_id=role_id,
        resume_skills=resume_skills,
        difficulty=difficulty,
        num_questions=num_questions
    )

    # 3. Insert into interview_questions with order
    for idx, q in enumerate(selected_questions, start=1):
        execute_query(
            """
            INSERT INTO interview_questions (interview_id, question_id, question_order)
            VALUES (%s, %s, %s)
            """,
            (interview_id, q['id'], idx)
        )

    return {
        'interview_id': interview_id,
        'role_id': role_id,
        'role_name': role['role_name'] if role else 'Python Developer',
        'difficulty': difficulty,
        'total_questions': len(selected_questions),
        'questions': selected_questions
    }


def get_current_interview_state(interview_id, user_id):
    """
    Retrieves the interview progress: questions list, current question index,
    and any previously saved answers.
    """
    interview = fetch_one(
        """
        SELECT i.*, r.role_name 
        FROM interviews i
        LEFT JOIN roles r ON i.role_id = r.id
        WHERE i.id = %s AND i.user_id = %s
        """,
        (interview_id, user_id)
    )
    if not interview:
        return None

    # Fetch assigned questions
    assigned = fetch_all(
        """
        SELECT iq.question_order, q.id as question_id, q.question_code, q.language, 
               q.topic, q.difficulty, q.question_text, a.answer_text, a.answered_at
        FROM interview_questions iq
        JOIN questions q ON iq.question_id = q.id
        LEFT JOIN answers a ON a.interview_id = iq.interview_id AND a.question_id = q.id
        WHERE iq.interview_id = %s
        ORDER BY iq.question_order ASC
        """,
        (interview_id,)
    )

    # Determine current unanswered question
    current_q = None
    for item in assigned:
        if not item.get('answer_text'):
            current_q = item
            break

    # If all answered, current_q is the last question
    if not current_q and assigned:
        current_q = assigned[-1]

    answered_count = sum(1 for item in assigned if item.get('answer_text'))

    return {
        'interview_id': interview['id'],
        'role_id': interview['role_id'],
        'role_name': interview.get('role_name', 'Software Engineer'),
        'difficulty': interview['difficulty'],
        'total_questions': interview['total_questions'],
        'status': interview['status'],
        'started_at': str(interview['started_at']),
        'answered_count': answered_count,
        'current_order': current_q['question_order'] if current_q else 1,
        'current_question': current_q,
        'all_questions': assigned
    }


def save_answer(interview_id, question_id, answer_text, user_id, status='answered'):
    """
    Stores or updates candidate's speech/text answer and triggers AI evaluation.
    If all questions have been answered, marks the interview as 'completed'
    and calculates final result scores and personalized feedback (Phases 7 & 8).
    """
    # Verify user owns the interview
    interview = fetch_one("SELECT id, total_questions FROM interviews WHERE id = %s AND user_id = %s", (interview_id, user_id))
    if not interview:
        raise ValueError("Interview session not found or unauthorized.")

    # Import answer analyzer here to avoid circular dependencies
    from answer_analyzer import analyze_and_store_answer, generate_interview_result

    # 1. Analyze and store answer with 1-5 scores, feedback, strength, improvement
    eval_result = analyze_and_store_answer(
        interview_id=interview_id,
        question_id=question_id,
        answer_text=answer_text,
        user_id=user_id,
        status=status
    )

    # 2. Check how many questions answered
    answers_count_row = fetch_one("SELECT COUNT(*) as cnt FROM answers WHERE interview_id = %s", (interview_id,))
    answered = answers_count_row['cnt'] if answers_count_row else 0
    is_completed = (answered >= interview['total_questions'])

    final_result_summary = None
    if is_completed:
        execute_query("UPDATE interviews SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = %s", (interview_id,))
        # Compute and persist final interview results
        try:
            final_result_summary = generate_interview_result(interview_id, user_id)
        except Exception as err:
            print(f"[WARN] Error computing final interview result: {err}")

    return {
        'answer_id': eval_result.get('answer_id'),
        'answered_count': answered,
        'total_questions': interview['total_questions'],
        'is_completed': is_completed,
        'scores': {
            'technical': eval_result.get('technical_score'),
            'communication': eval_result.get('communication_score'),
            'quality': eval_result.get('quality_score'),
            'confidence': eval_result.get('confidence_score')
        },
        'feedback': eval_result.get('feedback'),
        'strength': eval_result.get('strength'),
        'improvement': eval_result.get('improvement'),
        'final_result': final_result_summary
    }
