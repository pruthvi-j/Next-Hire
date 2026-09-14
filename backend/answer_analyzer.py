"""
NEXT HIRE - AI Answer Analysis, Scoring & Feedback Engine (Phases 7 & 8)
Master of Computer Applications (MCA) Academic Project

This module performs:
1. Multi-dimensional evaluation of candidate answers (Technical, Communication, Quality, Confidence).
2. Integration with external AI APIs (Google Gemini, OpenAI) via environment variables.
3. Academic Heuristic NLP Fallback evaluator when AI services are offline/unconfigured.
4. Final interview evaluation, weighted scoring formula, and personalized recommendations.
"""

import os
import re
import json
import urllib.request
import urllib.error
from database import fetch_one, fetch_all, execute_query


# =====================================================================
# CONFIGURATION & ENVIRONMENT KEYS
# =====================================================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_SERVICE_URL = os.getenv('AI_SERVICE_URL')  # Optional custom LLM endpoint


# =====================================================================
# TECHNICAL DOMAIN KNOWLEDGE BASES (For Fallback & Validation)
# =====================================================================

DOMAIN_KEYWORDS = {
    'python': [
        'list', 'tuple', 'dict', 'dictionary', 'set', 'mutable', 'immutable', 'decorator', 
        'generator', 'yield', 'lambda', 'class', 'object', 'inheritance', 'polymorphism', 
        'encapsulation', 'gil', 'global interpreter lock', 'memory', 'garbage collection', 
        'comprehension', 'exception', 'try', 'except', 'module', 'package', 'dunder', 
        'self', 'init', 'iterable', 'iterator', 'reference', 'dynamic typing'
    ],
    'sql': [
        'select', 'from', 'where', 'join', 'inner join', 'left join', 'right join', 'group by', 
        'order by', 'having', 'aggregate', 'primary key', 'foreign key', 'unique', 'null', 
        'index', 'b-tree', 'acid', 'atomicity', 'consistency', 'isolation', 'durability', 
        'transaction', 'commit', 'rollback', 'normalization', '1nf', '2nf', '3nf', 
        'view', 'trigger', 'stored procedure', 'schema', 'relational', 'table'
    ],
    'javascript': [
        'var', 'let', 'const', 'scope', 'hoisting', 'closure', 'callback', 'promise', 
        'async', 'await', 'event loop', 'call stack', 'dom', 'prototype', 'prototype chain', 
        'arrow function', 'this', 'event bubbling', 'event delegation', 'json', 'api', 
        'fetch', 'es6', 'destructuring', 'spread', 'rest', 'strict mode'
    ],
    'java': [
        'jvm', 'jre', 'jdk', 'bytecode', 'garbage collector', 'oop', 'class', 'object', 
        'inheritance', 'polymorphism', 'abstract', 'interface', 'encapsulation', 'overloading', 
        'overriding', 'static', 'final', 'super', 'this', 'thread', 'multithreading', 
        'exception', 'try-catch', 'collection', 'arraylist', 'hashmap', 'generics'
    ],
    'c': [
        'pointer', 'memory', 'malloc', 'calloc', 'free', 'realloc', 'structure', 'struct', 
        'union', 'preprocessor', 'macro', 'header', 'array', 'string', 'null-terminated', 
        'stack', 'heap', 'segmentation fault', 'recursion', 'function pointer', 'typedef'
    ]
}

# Positive discourse / articulation indicators
COMMUNICATION_POSITIVE_MARKERS = [
    'specifically', 'furthermore', 'for example', 'in particular', 'additionally',
    'consequently', 'therefore', 'primarily', 'in contrast', 'moreover',
    'is defined as', 'operates by', 'ensures that', 'means that', 'responsible for'
]

# Hedging / uncertainty markers (Observable speech/transcript signals)
UNCERTAINTY_MARKERS = [
    "maybe", "i guess", "not sure", "i don't know", "i think maybe", 
    "probably", "might be", "not really sure", "um", "uh", "er", "dunno"
]


# =====================================================================
# AI API CALL HANDLERS
# =====================================================================

def call_gemini_api(prompt_text):
    """
    Calls Google Gemini API using REST endpoint.
    Returns parsed JSON dict or None on failure.
    """
    if not GEMINI_API_KEY:
        return None

    # Supported model endpoints
    models = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
    
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    resp_json = json.loads(response.read().decode('utf-8'))
                    candidates = resp_json.get('candidates', [])
                    if candidates:
                        content_part = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                        parsed = _extract_json_from_text(content_part)
                        if parsed:
                            parsed['source'] = f'gemini_api ({model_name})'
                            return parsed
        except Exception:
            continue

    return None


def call_openai_api(prompt_text):
    """
    Calls OpenAI Chat Completions API using REST endpoint.
    Returns parsed JSON dict or None on failure.
    """
    if not OPENAI_API_KEY:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are NextHire, an expert academic and industry technical interviewer. Output valid JSON only."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENAI_API_KEY}'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                resp_json = json.loads(response.read().decode('utf-8'))
                content = resp_json['choices'][0]['message']['content']
                parsed = _extract_json_from_text(content)
                if parsed:
                    parsed['source'] = 'openai_api (gpt-4o-mini)'
                    return parsed
    except Exception:
        return None

    return None


def _extract_json_from_text(text):
    """Safely parses JSON even if wrapped in markdown code blocks."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    if cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except Exception:
        # Regex search for outermost JSON object
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return None


# =====================================================================
# ACADEMIC HEURISTIC NLP EVALUATION ENGINE (Guaranteed Fallback)
# =====================================================================

def evaluate_with_heuristic_nlp(question_text, answer_text, language='General', topic='General', difficulty='Medium', role_name='Software Engineer', resume_context=None):
    """
    High-precision, resilient NLP evaluator built on linguistics & concept mapping.
    Ensures the system never crashes even if external AI APIs are unconfigured or down.
    Scores 1-5 across Technical, Communication, Quality, and Confidence Estimate.
    """
    answer_clean = (answer_text or '').strip()

    # Case 1: Empty or near-empty answer handling
    if not answer_clean or len(answer_clean) < 5:
        return {
            'technical_score': 1,
            'communication_score': 1,
            'quality_score': 1,
            'confidence_score': 1,
            'feedback': 'No answer was recorded for this question.',
            'strength': 'None observed (response blank or unattempted).',
            'improvement': 'Ensure you attempt every question by speaking or typing key technical concepts even if unsure.',
            'source': 'heuristic_nlp_fallback'
        }

    words = answer_clean.lower().split()
    word_count = len(words)
    answer_lower = answer_clean.lower()

    # 1. Technical Knowledge Scoring (1 - 5)
    lang_key = (language or 'General').lower()
    known_kws = DOMAIN_KEYWORDS.get(lang_key, DOMAIN_KEYWORDS['python'])
    matched_kws = [kw for kw in known_kws if kw in answer_lower]

    # Keyword density score
    kw_count = len(matched_kws)
    if kw_count >= 5 or (kw_count >= 3 and word_count >= 30):
        tech_score = 5
    elif kw_count >= 3 or (kw_count >= 2 and word_count >= 20):
        tech_score = 4
    elif kw_count >= 1 and word_count >= 15:
        tech_score = 3
    elif word_count >= 10:
        tech_score = 2
    else:
        tech_score = 1

    # 2. Communication Clarity Scoring (1 - 5)
    comm_markers = sum(1 for m in COMMUNICATION_POSITIVE_MARKERS if m in answer_lower)
    filler_markers = sum(1 for u in UNCERTAINTY_MARKERS if re.search(r'\b' + re.escape(u) + r'\b', answer_lower))

    # Sentence structure check (punctuation and capitalization)
    sentences = [s.strip() for s in re.split(r'[.!?]+', answer_clean) if s.strip()]
    sentence_count = len(sentences)

    comm_score = 3  # baseline
    if word_count >= 25 and comm_markers >= 1:
        comm_score += 1
    if sentence_count >= 2 and (answer_clean[0].isupper() or any(s[0].isupper() for s in sentences)):
        comm_score += 1
    if filler_markers >= 2:
        comm_score -= 1
    if word_count < 10:
        comm_score = min(comm_score, 2)

    comm_score = max(1, min(5, comm_score))

    # 3. Answer Quality & Completeness Scoring (1 - 5)
    quality_score = 3
    if word_count >= 40 and kw_count >= 3:
        quality_score = 5
    elif word_count >= 25 and kw_count >= 2:
        quality_score = 4
    elif word_count >= 15:
        quality_score = 3
    elif word_count >= 8:
        quality_score = 2
    else:
        quality_score = 1

    # 4. Confidence Estimate (1 - 5)
    # Important: Presented strictly as an estimate based on observable response/speech indicators.
    confidence_score = 3
    if filler_markers == 0 and comm_markers >= 1 and word_count >= 20:
        confidence_score = 5
    elif filler_markers == 0 and word_count >= 15:
        confidence_score = 4
    elif filler_markers >= 2:
        confidence_score = 2
    elif word_count < 8:
        confidence_score = 1

    # 5. Tailored Feedback, Strength, and Improvement Tip
    topic_str = topic if topic and topic != 'General' else language
    if matched_kws:
        strength = f"Good grasp of core {language} concepts, particularly mentioning {', '.join(matched_kws[:2])}."
    else:
        strength = f"Attempted response addressing {topic_str} in context of {role_name}."

    if tech_score >= 4:
        feedback = f"Strong and coherent explanation demonstrating sound technical understanding of {topic_str}."
        improvement = f"Continue deepening knowledge with practical edge cases and production trade-offs in {language}."
    elif tech_score == 3:
        feedback = f"Satisfactory answer covering foundational aspects of {topic_str}, but could benefit from greater technical depth."
        improvement = f"Include concrete syntax examples or architectural details when discussing {topic_str}."
    else:
        feedback = f"Basic overview provided. The response lacks key technical terms and comprehensive explanation for {topic_str}."
        improvement = f"Review standard definitions and operational mechanics of {topic_str} in {language}."

    return {
        'technical_score': tech_score,
        'communication_score': comm_score,
        'quality_score': quality_score,
        'confidence_score': confidence_score,
        'feedback': feedback,
        'strength': strength,
        'improvement': improvement,
        'source': 'heuristic_nlp_fallback'
    }


# =====================================================================
# PUBLIC AI ANALYSIS INTERFACE (Phase 7)
# =====================================================================

def analyze_answer(question_text, answer_text, language='General', topic='General', difficulty='Medium', role_name='Software Engineer', resume_context=None):
    """
    Main entrypoint for Phase 7 AI Answer Analysis.
    Tries external AI APIs (Gemini/OpenAI) first.
    Gracefully falls back to heuristic NLP without application crash.
    """
    answer_clean = (answer_text or '').strip()

    # Immediate handling for empty / unattempted answers
    if not answer_clean:
        return {
            'technical_score': 1,
            'communication_score': 1,
            'quality_score': 1,
            'confidence_score': 1,
            'feedback': 'No answer was recorded for this question.',
            'strength': 'None observed (response blank or unattempted).',
            'improvement': 'Ensure you attempt every question by speaking or typing key technical concepts even if unsure.',
            'source': 'system_empty_handler'
        }

    # Prepare prompt for LLM
    resume_note = f"Candidate Resume Context: {resume_context}" if resume_context else "Candidate: Technical Job Applicant"
    prompt = f"""You are NextHire's AI Technical Interview Evaluator for the job role '{role_name}'.
Analyze the following candidate answer to the technical interview question.

[INTERVIEW QUESTION]
Question: {question_text}
Language/Domain: {language}
Topic: {topic}
Difficulty: {difficulty}
Target Role: {role_name}
{resume_note}

[CANDIDATE ANSWER]
"{answer_clean}"

Evaluate the candidate's answer and produce:
1. technical_score: Integer 1 to 5 (Technical knowledge and accuracy)
2. communication_score: Integer 1 to 5 (Clarity, structure, and readability)
3. quality_score: Integer 1 to 5 (Completeness and depth of answer)
4. confidence_score: Integer 1 to 5 (Estimate based strictly on observable response fluency and assertion, not psychological diagnosis)
5. feedback: Short 1-2 sentence constructive evaluation.
6. strength: One notable strength observed in the answer.
7. improvement: One specific actionable area for improvement.

Output ONLY a JSON object matching this exact schema:
{{
  "technical_score": 4,
  "communication_score": 4,
  "quality_score": 4,
  "confidence_score": 4,
  "feedback": "Concise feedback text.",
  "strength": "Key strength.",
  "improvement": "Key area for improvement."
}}"""

    # Try Gemini API
    if GEMINI_API_KEY:
        try:
            gemini_res = call_gemini_api(prompt)
            if gemini_res and _validate_evaluation_dict(gemini_res):
                return _normalize_evaluation_dict(gemini_res, 'gemini_api')
        except Exception:
            pass

    # Try OpenAI API
    if OPENAI_API_KEY:
        try:
            openai_res = call_openai_api(prompt)
            if openai_res and _validate_evaluation_dict(openai_res):
                return _normalize_evaluation_dict(openai_res, 'openai_api')
        except Exception:
            pass

    # Graceful fallback: Heuristic NLP
    return evaluate_with_heuristic_nlp(
        question_text=question_text,
        answer_text=answer_clean,
        language=language,
        topic=topic,
        difficulty=difficulty,
        role_name=role_name,
        resume_context=resume_context
    )


def _validate_evaluation_dict(d):
    """Validates that all required fields are present in the response."""
    keys = ['technical_score', 'communication_score', 'quality_score', 'confidence_score', 'feedback', 'strength', 'improvement']
    return all(k in d for k in keys)


def _normalize_evaluation_dict(d, source):
    """Sanitizes scores to guaranteed 1-5 integers and strings."""
    def clean_score(v):
        try:
            val = int(round(float(v)))
            return max(1, min(5, val))
        except (ValueError, TypeError):
            return 3

    return {
        'technical_score': clean_score(d.get('technical_score', 3)),
        'communication_score': clean_score(d.get('communication_score', 3)),
        'quality_score': clean_score(d.get('quality_score', 3)),
        'confidence_score': clean_score(d.get('confidence_score', 3)),
        'feedback': str(d.get('feedback') or 'Response analyzed.').strip(),
        'strength': str(d.get('strength') or 'Technical effort demonstrated.').strip(),
        'improvement': str(d.get('improvement') or 'Deepen conceptual explanations.').strip(),
        'source': source
    }


def analyze_and_store_answer(interview_id, question_id, answer_text, user_id=None):
    """
    Evaluates an individual answer and saves the scores and feedback in the answers table.
    """
    # Fetch question metadata and interview context
    q_data = fetch_one(
        """
        SELECT q.question_text, q.language, q.topic, q.difficulty,
               r.role_name
        FROM questions q
        JOIN interview_questions iq ON iq.question_id = q.id
        JOIN interviews i ON iq.interview_id = i.id
        LEFT JOIN roles r ON i.role_id = r.id
        WHERE iq.interview_id = %s AND q.id = %s
        """,
        (interview_id, question_id)
    )

    if not q_data:
        q_data = fetch_one("SELECT question_text, language, topic, difficulty FROM questions WHERE id = %s", (question_id,))

    question_text = q_data['question_text'] if q_data else 'Technical question'
    language = q_data.get('language', 'General') if q_data else 'General'
    topic = q_data.get('topic', 'General') if q_data else 'General'
    difficulty = q_data.get('difficulty', 'Medium') if q_data else 'Medium'
    role_name = q_data.get('role_name', 'Software Engineer') if q_data else 'Software Engineer'

    # Run AI / NLP Analysis
    eval_result = analyze_answer(
        question_text=question_text,
        answer_text=answer_text,
        language=language,
        topic=topic,
        difficulty=difficulty,
        role_name=role_name
    )

    # Save to answers table
    existing = fetch_one("SELECT id FROM answers WHERE interview_id = %s AND question_id = %s", (interview_id, question_id))
    if existing:
        execute_query(
            """
            UPDATE answers
            SET answer_text = %s,
                technical_score = %s,
                communication_score = %s,
                quality_score = %s,
                confidence_score = %s,
                feedback = %s,
                strength = %s,
                improvement = %s,
                answered_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                answer_text,
                eval_result['technical_score'],
                eval_result['communication_score'],
                eval_result['quality_score'],
                eval_result['confidence_score'],
                eval_result['feedback'],
                eval_result['strength'],
                eval_result['improvement'],
                existing['id']
            )
        )
        answer_id = existing['id']
    else:
        answer_id = execute_query(
            """
            INSERT INTO answers 
            (interview_id, question_id, answer_text, technical_score, communication_score, 
             quality_score, confidence_score, feedback, strength, improvement)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                interview_id,
                question_id,
                answer_text,
                eval_result['technical_score'],
                eval_result['communication_score'],
                eval_result['quality_score'],
                eval_result['confidence_score'],
                eval_result['feedback'],
                eval_result['strength'],
                eval_result['improvement']
            )
        )

    eval_result['answer_id'] = answer_id
    return eval_result


# =====================================================================
# FINAL SCORING FORMULA & PERSONALIZED FEEDBACK ENGINE (Phase 8)
# =====================================================================

"""
SCORING FORMULA DOCUMENTATION:
-----------------------------
Each answered question receives scores from 1 to 5 across 4 dimensions:
1. S_tech : Technical Knowledge & Accuracy (1-5)
2. S_qual : Answer Quality & Completeness (1-5)
3. S_comm : Communication Clarity (1-5)
4. S_conf : Observable Confidence Estimate (1-5)

Average Dimension Scores:
  Avg_Tech = sum(S_tech) / N
  Avg_Qual = sum(S_qual) / N
  Avg_Comm = sum(S_comm) / N
  Avg_Conf = sum(S_conf) / N

Weighted Final Overall Score (Percentage 0 to 100%):
  Overall Score = 100 * (0.40 * (Avg_Tech / 5.0) +
                         0.25 * (Avg_Qual / 5.0) +
                         0.20 * (Avg_Comm / 5.0) +
                         0.15 * (Avg_Conf / 5.0))

Weight Distribution:
- Technical Skills: 40% (Core domain accuracy and algorithmic competency)
- Answer Quality:   25% (Depth, comprehensive coverage, and relevance)
- Communication:    20% (Sentence structure, technical vocabulary, conciseness)
- Confidence:       15% (Observable speech/response fluency and decisiveness)
"""

def calculate_final_scores(answers_list):
    """
    Computes dimension averages and the final weighted overall score.
    answers_list: list of dicts with technical_score, communication_score, quality_score, confidence_score
    """
    if not answers_list:
        return {
            'overall_score': 0.0,
            'technical_score': 0.0,
            'communication_score': 0.0,
            'quality_score': 0.0,
            'confidence_score': 0.0,
            'num_answered': 0
        }

    n = len(answers_list)
    sum_tech = sum(a.get('technical_score') or 1 for a in answers_list)
    sum_comm = sum(a.get('communication_score') or 1 for a in answers_list)
    sum_qual = sum(a.get('quality_score') or 1 for a in answers_list)
    sum_conf = sum(a.get('confidence_score') or 1 for a in answers_list)

    avg_tech = round(sum_tech / n, 2)
    avg_comm = round(sum_comm / n, 2)
    avg_qual = round(sum_qual / n, 2)
    avg_conf = round(sum_conf / n, 2)

    # Weighted Overall Score (0 - 100%)
    weighted_score = (
        0.40 * (avg_tech / 5.0) +
        0.25 * (avg_qual / 5.0) +
        0.20 * (avg_comm / 5.0) +
        0.15 * (avg_conf / 5.0)
    ) * 100.0

    return {
        'overall_score': round(weighted_score, 1),
        'technical_score': avg_tech,
        'communication_score': avg_comm,
        'quality_score': avg_qual,
        'confidence_score': avg_conf,
        'num_answered': n
    }


def synthesize_personalized_feedback(answers_list, role_name='Software Engineer'):
    """
    Synthesizes aggregated strengths, weaknesses (areas to improve), and recommendations
    from the individual evaluated questions.
    """
    strengths = []
    weaknesses = []
    recommendations = []

    languages_covered = set()
    high_scoring_topics = []
    low_scoring_topics = []

    for a in answers_list:
        lang = a.get('language') or 'General'
        topic = a.get('topic') or lang
        languages_covered.add(lang)

        tech = a.get('technical_score') or 1
        comm = a.get('communication_score') or 1
        qual = a.get('quality_score') or 1

        if tech >= 4:
            high_scoring_topics.append((lang, topic))
        elif tech <= 2:
            low_scoring_topics.append((lang, topic))

        # Check for specific strength text
        if a.get('strength') and len(strengths) < 3 and 'None observed' not in a.get('strength'):
            strengths.append(a.get('strength'))

        # Check for specific improvement text
        if a.get('improvement') and len(weaknesses) < 3:
            weaknesses.append(a.get('improvement'))

    # Synthesize clean bullet points if sparse
    if high_scoring_topics:
        top_lang = high_scoring_topics[0][0]
        strengths.insert(0, f"Good {top_lang} knowledge and conceptual understanding.")
    else:
        strengths.append("Willingness to attempt diverse technical question prompts.")

    if len(strengths) < 2 and languages_covered:
        strengths.append(f"Demonstrated foundational understanding of {', '.join(languages_covered)}.")

    if low_scoring_topics:
        low_lang, low_topic = low_scoring_topics[0]
        weaknesses.insert(0, f"Deepen explanation clarity for {low_topic} in {low_lang}.")
    else:
        weaknesses.append("Give more complete and detailed answers with code/syntax examples.")

    if len(weaknesses) < 2:
        weaknesses.append("Improve technical communication by reducing filler hesitation words.")

    # Actionable Recommendations
    for lang in languages_covered:
        if lang.lower() == 'python':
            recommendations.append("Practice Python OOP and generator/decorator patterns.")
        elif lang.lower() == 'sql':
            recommendations.append("Practice complex SQL queries including multi-table joins and aggregation.")
        elif lang.lower() == 'javascript':
            recommendations.append("Master modern JavaScript closures, asynchronous event loop, and promises.")
        elif lang.lower() == 'java':
            recommendations.append("Review Java multithreading, memory model, and collections framework.")
        elif lang.lower() == 'c':
            recommendations.append("Strengthen pointer arithmetic, dynamic memory allocation, and struct design.")

    recommendations.append("Improve technical communication using structured explanations (Definition -> Example -> Trade-off).")
    recommendations.append(f"Benchmarked review for {role_name} interview scenarios.")

    # Limit to top 3-4 each
    return {
        'strengths': strengths[:3],
        'weaknesses': weaknesses[:3],
        'recommendations': recommendations[:3]
    }


def generate_interview_result(interview_id, user_id=None, force_recompute=False):
    """
    Evaluates any un-evaluated answers in the interview session,
    calculates final scores, synthesizes feedback, and persists into interview_results.
    Returns the comprehensive result payload.
    """
    # 1. Fetch interview details
    interview = fetch_one(
        """
        SELECT i.*, r.role_name
        FROM interviews i
        LEFT JOIN roles r ON i.role_id = r.id
        WHERE i.id = %s
        """,
        (interview_id,)
    )
    if not interview:
        raise ValueError(f"Interview session #{interview_id} not found.")

    role_name = interview.get('role_name') or 'Software Engineer'

    # Check if result already exists and not forcing recompute
    if not force_recompute:
        existing_res = fetch_one("SELECT * FROM interview_results WHERE interview_id = %s", (interview_id,))
        if existing_res:
            # Fetch detailed answers for breakdown
            detailed_answers = _fetch_detailed_interview_answers(interview_id)
            return _format_result_payload(interview, existing_res, detailed_answers)

    # 2. Fetch all assigned questions and candidate answers
    assigned_questions = fetch_all(
        """
        SELECT iq.question_order, q.id as question_id, q.question_code, q.language, 
               q.topic, q.difficulty, q.question_text,
               a.id as answer_id, a.answer_text, a.technical_score, a.communication_score,
               a.quality_score, a.confidence_score, a.feedback, a.strength, a.improvement
        FROM interview_questions iq
        JOIN questions q ON iq.question_id = q.id
        LEFT JOIN answers a ON a.interview_id = iq.interview_id AND a.question_id = q.id
        WHERE iq.interview_id = %s
        ORDER BY iq.question_order ASC
        """,
        (interview_id,)
    )

    # 3. Analyze any answers that do not have scores yet
    analyzed_answers = []
    for item in assigned_questions:
        ans_text = item.get('answer_text') or ''
        tech_score = item.get('technical_score')

        # If answer exists but is not scored yet (or was blank)
        if tech_score is None:
            eval_dict = analyze_answer(
                question_text=item['question_text'],
                answer_text=ans_text,
                language=item['language'],
                topic=item['topic'],
                difficulty=item['difficulty'],
                role_name=role_name
            )
            # Store scores in database
            if item.get('answer_id'):
                execute_query(
                    """
                    UPDATE answers
                    SET technical_score = %s, communication_score = %s,
                        quality_score = %s, confidence_score = %s,
                        feedback = %s, strength = %s, improvement = %s
                    WHERE id = %s
                    """,
                    (
                        eval_dict['technical_score'],
                        eval_dict['communication_score'],
                        eval_dict['quality_score'],
                        eval_dict['confidence_score'],
                        eval_dict['feedback'],
                        eval_dict['strength'],
                        eval_dict['improvement'],
                        item['answer_id']
                    )
                )
            else:
                # Candidate skipped or left blank; record placeholder answer record
                ans_id = execute_query(
                    """
                    INSERT INTO answers 
                    (interview_id, question_id, answer_text, technical_score, communication_score,
                     quality_score, confidence_score, feedback, strength, improvement)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        interview_id,
                        item['question_id'],
                        '',
                        eval_dict['technical_score'],
                        eval_dict['communication_score'],
                        eval_dict['quality_score'],
                        eval_dict['confidence_score'],
                        eval_dict['feedback'],
                        eval_dict['strength'],
                        eval_dict['improvement']
                    )
                )
                item['answer_id'] = ans_id

            item.update(eval_dict)

        analyzed_answers.append(item)

    # 4. Calculate Final Scores via documented formula
    final_scores = calculate_final_scores(analyzed_answers)

    # 5. Synthesize Personalized Feedback
    feedback_bundle = synthesize_personalized_feedback(analyzed_answers, role_name=role_name)

    # Convert list to JSON strings for database storage
    strengths_json = json.dumps(feedback_bundle['strengths'])
    weaknesses_json = json.dumps(feedback_bundle['weaknesses'])
    recs_json = json.dumps(feedback_bundle['recommendations'])

    # 6. Save or update interview_results table
    existing = fetch_one("SELECT id FROM interview_results WHERE interview_id = %s", (interview_id,))
    if existing:
        execute_query(
            """
            UPDATE interview_results
            SET overall_score = %s,
                technical_score = %s,
                communication_score = %s,
                quality_score = %s,
                confidence_score = %s,
                strengths = %s,
                weaknesses = %s,
                recommendations = %s,
                created_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                final_scores['overall_score'],
                final_scores['technical_score'],
                final_scores['communication_score'],
                final_scores['quality_score'],
                final_scores['confidence_score'],
                strengths_json,
                weaknesses_json,
                recs_json,
                existing['id']
            )
        )
        res_id = existing['id']
    else:
        res_id = execute_query(
            """
            INSERT INTO interview_results
            (interview_id, overall_score, technical_score, communication_score,
             quality_score, confidence_score, strengths, weaknesses, recommendations)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                interview_id,
                final_scores['overall_score'],
                final_scores['technical_score'],
                final_scores['communication_score'],
                final_scores['quality_score'],
                final_scores['confidence_score'],
                strengths_json,
                weaknesses_json,
                recs_json
            )
        )

    # Mark interview completed if not already
    execute_query("UPDATE interviews SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = %s", (interview_id,))

    # Format return
    res_record = {
        'id': res_id,
        'interview_id': interview_id,
        'overall_score': final_scores['overall_score'],
        'technical_score': final_scores['technical_score'],
        'communication_score': final_scores['communication_score'],
        'quality_score': final_scores['quality_score'],
        'confidence_score': final_scores['confidence_score'],
        'strengths': strengths_json,
        'weaknesses': weaknesses_json,
        'recommendations': recs_json,
        'created_at': 'Just now'
    }

    return _format_result_payload(interview, res_record, analyzed_answers)


def _fetch_detailed_interview_answers(interview_id):
    """Fetches questions and evaluated answers for detailed breakdown view."""
    return fetch_all(
        """
        SELECT iq.question_order, q.id as question_id, q.question_code, q.language, 
               q.topic, q.difficulty, q.question_text,
               a.id as answer_id, a.answer_text, a.technical_score, a.communication_score,
               a.quality_score, a.confidence_score, a.feedback, a.strength, a.improvement
        FROM interview_questions iq
        JOIN questions q ON iq.question_id = q.id
        LEFT JOIN answers a ON a.interview_id = iq.interview_id AND a.question_id = q.id
        WHERE iq.interview_id = %s
        ORDER BY iq.question_order ASC
        """,
        (interview_id,)
    )


def _format_result_payload(interview, res_record, detailed_answers):
    """Helper to assemble a clean, consistent response payload."""
    def parse_json_or_list(val):
        if not val:
            return []
        if isinstance(val, list):
            return val
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [line.strip() for line in str(val).split('\n') if line.strip()]

    overall = float(res_record['overall_score'])
    tech = float(res_record['technical_score'])
    comm = float(res_record['communication_score'])
    qual = float(res_record['quality_score'])
    conf = float(res_record['confidence_score'])

    ai_engine = "Academic Heuristic NLP Evaluator (Active)"
    if GEMINI_API_KEY:
        ai_engine = "Google Gemini AI (Active via GEMINI_API_KEY)"
    elif OPENAI_API_KEY:
        ai_engine = "OpenAI GPT-4o-mini (Active via OPENAI_API_KEY)"

    return {
        'interview_id': interview['id'],
        'role_name': interview.get('role_name', 'Software Engineer'),
        'difficulty': interview.get('difficulty', 'Medium'),
        'total_questions': interview.get('total_questions', len(detailed_answers)),
        'answered_count': sum(1 for a in detailed_answers if a.get('answer_text')),
        'status': interview.get('status', 'completed'),
        'overall_score': overall,
        'scores': {
            'overall': overall,
            'technical': {
                'score_5': tech,
                'percentage': round((tech / 5.0) * 100, 1),
                'label': 'Technical Knowledge'
            },
            'communication': {
                'score_5': comm,
                'percentage': round((comm / 5.0) * 100, 1),
                'label': 'Communication Clarity'
            },
            'quality': {
                'score_5': qual,
                'percentage': round((qual / 5.0) * 100, 1),
                'label': 'Answer Quality & Completeness'
            },
            'confidence': {
                'score_5': conf,
                'percentage': round((conf / 5.0) * 100, 1),
                'label': 'Confidence Estimate',
                'disclaimer': 'Estimate based on observable response and speech indicators, not a psychological diagnosis or guaranteed measurement.'
            }
        },
        'strengths': parse_json_or_list(res_record['strengths']),
        'weaknesses': parse_json_or_list(res_record['weaknesses']),
        'recommendations': parse_json_or_list(res_record['recommendations']),
        'ai_service_info': {
            'engine': ai_engine,
            'confidence_disclaimer': 'Confidence must be presented as an estimate based on observable response/speech indicators, not as a psychological diagnosis or guaranteed measurement.'
        },
        'questions_details': [
            {
                'order': a.get('question_order', idx + 1),
                'question_id': a.get('question_id'),
                'question_code': a.get('question_code', f"Q{idx+1}"),
                'language': a.get('language', 'General'),
                'topic': a.get('topic', 'General'),
                'difficulty': a.get('difficulty', 'Medium'),
                'question_text': a.get('question_text', ''),
                'answer_text': a.get('answer_text') or '(No answer provided)',
                'scores': {
                    'technical': a.get('technical_score') or 1,
                    'communication': a.get('communication_score') or 1,
                    'quality': a.get('quality_score') or 1,
                    'confidence': a.get('confidence_score') or 1
                },
                'feedback': a.get('feedback') or 'No feedback available.',
                'strength': a.get('strength') or 'None observed.',
                'improvement': a.get('improvement') or 'Review conceptual fundamentals.'
            }
            for idx, a in enumerate(detailed_answers)
        ]
    }
