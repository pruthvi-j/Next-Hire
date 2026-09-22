"""
NEXT HIRE - AI Answer Analysis, Scoring & Feedback Engine (Phases 7, 8 & 9)
Master of Computer Applications (MCA) Academic Project

This module performs:
1. Multi-dimensional evaluation of candidate answers (Technical, Communication, Quality, Confidence).
2. CONCEPT-BASED semantic answer matching (not exact string matching).
3. Integration with external AI APIs (Google Gemini, OpenAI) via environment variables.
4. Academic Heuristic NLP Fallback evaluator with synonym/concept mapping when AI is offline.
5. Final interview evaluation, weighted scoring formula, and personalized recommendations.

IMPORTANT - Evaluation Philosophy:
  - Answers are evaluated on CONCEPT UNDERSTANDING, not memorization.
  - The expected_answer is a REFERENCE ANSWER, not an exact required answer.
  - Candidates are scored on meaning, technical correctness, and completeness.
  - Different wording that conveys the same concept = HIGH score.
  - Partial concept coverage = PARTIAL score (not zero).
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
# CONCEPT SYNONYM MAPPING
# Used to recognize equivalent technical terms during heuristic evaluation.
# =====================================================================

CONCEPT_SYNONYMS = {
    # mutable
    'mutable': ['can be changed', 'can be modified', 'modifiable', 'changeable', 'can change',
                 'can edit', 'editable', 'can modify', 'modified', 'are modifiable',
                 'allows modification', 'elements can be changed'],
    'immutable': ['cannot be changed', 'cannot be modified', 'unmodifiable', 'unchangeable',
                  'fixed', 'cannot change', 'cannot be altered', 'cannot normally be changed',
                  'cannot be edited', 'cannot edit', 'not modifiable', 'cannot modify',
                  'cannot be updated', 'not changed', 'cannot normally'],

    # Memory / Pointers
    'memory address': ['address in memory', 'address of', 'location in memory', 'memory location', 'stores the address'],
    'pointer': ['stores address', 'holds address', 'contains address', 'points to'],
    'null pointer': ['null value', 'invalid address', 'no valid target', 'not point to'],

    # OOP
    'class': ['blueprint', 'template', 'definition'],
    'object': ['instance', 'instantiation'],
    'inheritance': ['acquire', 'inherits', 'derived from', 'extends', 'parent class', 'child class'],
    'encapsulation': ['combining data', 'restrict access', 'private fields', 'data hiding'],
    'polymorphism': ['same interface', 'same method name', 'different behavior', 'different implementation'],
    'overloading': ['same name but different', 'multiple methods with same name', 'different parameter'],
    'overriding': ['subclass provides', 'own implementation', 'redefine method'],
    'abstraction': ['hide implementation', 'abstract method'],

    # Python specific
    'high-level': ['high level', 'easy to read', 'readable', 'human-readable', 'abstracted'],
    'interpreted': ['runs line by line', 'not compiled', 'run directly', 'executed directly',
                    'interpreter', 'interprets'],
    'general-purpose': ['general purpose', 'used for many things', 'versatile', 'multipurpose',
                        'wide range', 'programming language'],
    'dynamic typing': ['no type declaration', 'type at runtime', 'type is determined at runtime',
                        'does not require type', 'no explicit type'],
    'key-value': ['key value pairs', 'key-value pairs', 'key and value'],
    'hashable': ['unique keys', 'keys must be unique'],
    'shallow copy': ['copies outer object', 'shares nested', 'references nested'],
    'deep copy': ['copies all levels', 'independent copy', 'recursively copies'],
    'generator': ['yield', 'lazy evaluation', 'generates values on demand'],
    'decorator': ['wraps function', 'modifies function', 'adds behavior'],

    # SQL / Database
    'filter': ['filters', 'filtering', 'filter records', 'filters records', 'filters rows', 'filter rows'],
    'rows': ['records', 'row', 'data', 'entries', 'tuples'],
    'before grouping': ['before group by', 'before the grouping', 'before the grouping operation', 'prior to grouping', 'before grouping operation'],
    'filter rows': ['filter records', 'filter individual rows', 'filter data', 'filters the rows', 'filters records'],
    'group by': ['grouping', 'grouping operation', 'groups rows', 'aggregate', 'group the data'],
    'where': ['filters before', 'filters rows before grouping', 'condition before group', 'where clause'],
    'having': ['filters after grouping', 'filter groups', 'after group by'],
    'primary key': ['unique identifier', 'uniquely identifies each row', 'unique and non-null'],
    'foreign key': ['references another table', 'referential integrity', 'references a key'],
    'inner join': ['matching rows from both', 'only matching', 'rows where match exists'],
    'left join': ['all rows from left', 'null values when no match', 'returns all from left'],
    'normalization': ['reduce redundancy', 'eliminate redundancy', 'organized into related tables'],
    'subquery': ['nested query', 'query inside', 'inner query'],
    'acid': ['atomicity', 'consistency', 'isolation', 'durability', 'transaction properties'],
    'ddl': ['create', 'alter', 'drop', 'define structure'],
    'dml': ['insert', 'update', 'delete', 'manipulate data'],

    # Java
    'jvm': ['java virtual machine', 'bytecode execution', 'platform independence'],
    'platform independence': ['write once run anywhere', 'runs on any platform', 'portable'],
    'garbage collection': ['automatic memory', 'frees memory automatically', 'memory management'],
    'interface': ['contract', 'abstract methods that classes must implement', 'multiple inheritance'],

    # C language
    'struct': ['structure', 'groups variables', 'user-defined data type'],
    'malloc': ['allocates memory', 'memory allocation', 'allocate bytes'],
    'calloc': ['allocates and initializes', 'initialized to zero'],
    'dynamic memory': ['heap memory', 'runtime memory allocation', 'allocated during program execution'],
    'pointer arithmetic': ['increment decrement pointer', 'move pointer', 'pointer moves'],
    'storage class': ['scope', 'lifetime', 'linkage'],

    # JavaScript
    'closure': ['remembers variables', 'access outer scope', 'lexical scope', 'function remembers'],
    'event bubbling': ['propagates upward', 'bubbles up', 'parent elements'],
    'promise': ['asynchronous operation', 'pending fulfilled rejected', 'future value'],
    'async await': ['asynchronous', 'simpler syntax for promises', 'handle asynchronous'],
    'scope': ['where variables can be accessed', 'variable accessibility', 'where variables are accessible'],
    'var': ['function scope', 'function-scoped', 'function scope only'],
    'let': ['block scope', 'block-scoped', 'can be reassigned'],
    'const': ['block scope', 'cannot be reassigned', 'binding cannot change'],
    'arrow function': ['shorter syntax', 'lexical this', 'fat arrow'],
}


# =====================================================================
# DOMAIN KNOWLEDGE BASES (For Fallback Validation)
# =====================================================================

DOMAIN_KEYWORDS = {
    'python': [
        'list', 'tuple', 'dict', 'dictionary', 'set', 'mutable', 'immutable', 'decorator',
        'generator', 'yield', 'lambda', 'class', 'object', 'inheritance', 'polymorphism',
        'encapsulation', 'gil', 'global interpreter lock', 'memory', 'garbage collection',
        'comprehension', 'exception', 'try', 'except', 'module', 'package', 'dunder',
        'self', 'init', 'iterable', 'iterator', 'reference', 'dynamic typing',
        'interpreted', 'high-level', 'general-purpose', 'standard library', 'args', 'kwargs',
        'shallow', 'deep', 'copy'
    ],
    'sql': [
        'select', 'from', 'where', 'join', 'inner join', 'left join', 'right join', 'group by',
        'order by', 'having', 'aggregate', 'primary key', 'foreign key', 'unique', 'null',
        'index', 'b-tree', 'acid', 'atomicity', 'consistency', 'isolation', 'durability',
        'transaction', 'commit', 'rollback', 'normalization', '1nf', '2nf', '3nf',
        'view', 'trigger', 'stored procedure', 'schema', 'relational', 'table',
        'ddl', 'dml', 'subquery', 'asc', 'desc'
    ],
    'javascript': [
        'var', 'let', 'const', 'scope', 'hoisting', 'closure', 'callback', 'promise',
        'async', 'await', 'event loop', 'call stack', 'dom', 'prototype', 'prototype chain',
        'arrow function', 'this', 'event bubbling', 'event delegation', 'json', 'api',
        'fetch', 'es6', 'destructuring', 'spread', 'rest', 'strict mode',
        'template literals', 'modules', 'classes', 'default parameters'
    ],
    'java': [
        'jvm', 'jre', 'jdk', 'bytecode', 'garbage collector', 'oop', 'class', 'object',
        'inheritance', 'polymorphism', 'abstract', 'interface', 'encapsulation', 'overloading',
        'overriding', 'static', 'final', 'super', 'this', 'thread', 'multithreading',
        'exception', 'try-catch', 'collection', 'arraylist', 'hashmap', 'generics',
        'platform independence', 'robustness', 'portability'
    ],
    'c': [
        'pointer', 'memory', 'malloc', 'calloc', 'free', 'realloc', 'structure', 'struct',
        'union', 'preprocessor', 'macro', 'header', 'array', 'string', 'null-terminated',
        'stack', 'heap', 'segmentation fault', 'recursion', 'function pointer', 'typedef',
        'storage class', 'auto', 'register', 'static', 'extern', 'embedded', 'procedural'
    ]
}

# Positive discourse / articulation indicators
COMMUNICATION_POSITIVE_MARKERS = [
    'specifically', 'furthermore', 'for example', 'in particular', 'additionally',
    'consequently', 'therefore', 'primarily', 'in contrast', 'moreover',
    'is defined as', 'operates by', 'ensures that', 'means that', 'responsible for',
    'the difference', 'on the other hand', 'while', 'whereas', 'however'
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
# CONCEPT-BASED SEMANTIC MATCHING ENGINE
# =====================================================================

def _normalize_text(text):
    """Lowercase and remove extra punctuation for comparison."""
    return re.sub(r'[^\w\s]', ' ', (text or '').lower()).strip()


def _text_contains_concept(text_lower, concept):
    """
    Checks if a text contains a concept, including synonym expansion.
    Returns True if the concept OR any of its synonyms are present.
    """
    concept_lower = concept.lower().strip()

    # Direct match
    if concept_lower in text_lower:
        return True

    # Check synonyms from the CONCEPT_SYNONYMS map
    synonyms = CONCEPT_SYNONYMS.get(concept_lower, [])
    for syn in synonyms:
        if syn.lower() in text_lower:
            return True

    # Reverse synonym lookup — check if candidate text maps back to this concept
    for key, syns in CONCEPT_SYNONYMS.items():
        for syn in syns:
            if concept_lower in syn.lower() or syn.lower() == concept_lower:
                if key.lower() in text_lower:
                    return True

    return False


def evaluate_concept_match(expected_answer, candidate_answer, key_concepts_str,
                           question_text='', topic='', difficulty='Medium'):
    """
    Core concept-based semantic evaluator.

    Compares the candidate's answer against the expected answer using:
    1. Key concept coverage (extracted concepts from expected answer)
    2. Synonym expansion (different words for same technical concept)
    3. Semantic overlap via n-gram matching
    4. Partial credit for partial concept coverage

    Returns a dict with:
        concept_match: "high" / "medium" / "partial" / "low" / "none"
        concept_score: float 0.0 – 5.0
        matched_concepts: list
        missing_concepts: list
        completeness: float 0.0 – 5.0
        feedback: str
    """
    if not candidate_answer or len(candidate_answer.strip()) < 5:
        return {
            'concept_match': 'none',
            'concept_score': 0.0,
            'matched_concepts': [],
            'missing_concepts': [],
            'completeness': 0.0,
            'feedback': 'No meaningful answer provided.'
        }

    candidate_lower = _normalize_text(candidate_answer)
    expected_lower = _normalize_text(expected_answer or '')

    # Parse key concepts
    raw_concepts = []
    if key_concepts_str:
        raw_concepts = [c.strip() for c in key_concepts_str.split(',') if c.strip()]

    # If no key concepts available, extract from expected answer on-the-fly
    if not raw_concepts and expected_answer:
        # Simple fallback: use non-stop-word tokens from expected answer
        stop = {'a', 'an', 'the', 'is', 'are', 'and', 'or', 'to', 'of', 'in', 'for',
                'it', 'be', 'by', 'as', 'at', 'on', 'with', 'not', 'can', 'also',
                'that', 'this', 'from', 'while', 'but', 'its', 'into', 'than',
                'used', 'using', 'uses', 'such', 'more', 'when', 'if', 'these'}
        words = _normalize_text(expected_answer).split()
        raw_concepts = [w for w in words if w not in stop and len(w) > 2][:10]

    # Score concept coverage
    matched = []
    missing = []

    for concept in raw_concepts:
        if _text_contains_concept(candidate_lower, concept):
            matched.append(concept)
        else:
            missing.append(concept)

    # Calculate coverage ratio
    total_concepts = len(raw_concepts)
    matched_count = len(matched)
    coverage = matched_count / total_concepts if total_concepts > 0 else 0.5

    # Calculate semantic overlap between candidate and expected (word-level Jaccard)
    if expected_lower:
        exp_words = set(expected_lower.split()) - {'a', 'an', 'the', 'is', 'are', 'and', 'or',
                                                    'to', 'of', 'in', 'for', 'it', 'be', 'by',
                                                    'not', 'can', 'that', 'this', 'from', 'but'}
        cand_words = set(candidate_lower.split())
        intersection = exp_words & cand_words
        union = exp_words | cand_words
        jaccard = len(intersection) / len(union) if union else 0.0
    else:
        jaccard = 0.0

    # Combined score calibration:
    # Concept coverage is the primary signal (85%). Jaccard word overlap is auxiliary (15%).
    # When 100% of required concepts are matched (directly or via synonyms),
    # the candidate has demonstrated full understanding → guarantee HIGH match (>= 0.80).
    if coverage >= 1.0:
        combined = max(0.85, (0.85 * coverage) + (0.15 * jaccard))
    elif coverage >= 0.75:
        combined = max(0.70, (0.80 * coverage) + (0.20 * jaccard))
    else:
        combined = (0.75 * coverage) + (0.25 * jaccard)

    # Adjust for difficulty
    difficulty_bonus = {'Easy': 0.0, 'Medium': 0.0, 'Hard': 0.05}.get(difficulty, 0.0)
    combined = min(1.0, combined + difficulty_bonus)

    # Map to concept_score (0-5) and concept_match label
    concept_score = round(combined * 5.0, 1)

    if combined >= 0.75:
        concept_match = 'high'
    elif combined >= 0.55:
        concept_match = 'medium'
    elif combined >= 0.30:
        concept_match = 'partial'
    elif combined >= 0.10:
        concept_match = 'low'
    else:
        concept_match = 'none'

    # Completeness: based on length relative to expected + concept coverage
    expected_word_count = len((expected_answer or '').split())
    candidate_word_count = len(candidate_answer.split())
    length_ratio = min(1.0, candidate_word_count / max(expected_word_count, 1))
    completeness = round(((coverage * 0.7) + (length_ratio * 0.3)) * 5.0, 1)
    completeness = max(0.5, min(5.0, completeness))

    # Targeted feedback
    if concept_match == 'high':
        feedback = f"Excellent concept understanding demonstrated. The answer correctly covers the core technical meaning."
    elif concept_match == 'medium':
        if missing:
            feedback = f"Good understanding shown. The answer covers the main concept but is missing some detail on: {', '.join(missing[:2])}."
        else:
            feedback = f"Good understanding of the concept. Consider adding more specific technical detail."
    elif concept_match == 'partial':
        if matched:
            feedback = f"Partially correct. You correctly mentioned: {', '.join(matched[:2])}. Missing key concepts: {', '.join(missing[:3])}."
        else:
            feedback = f"Partially on topic but missing the core technical concepts. Focus on: {', '.join(missing[:3])}."
    elif concept_match == 'low':
        feedback = f"The answer shows limited understanding of the concept. Key concepts to review: {', '.join(missing[:4])}."
    else:
        feedback = "The answer does not address the technical concept asked. Please review the fundamentals."

    return {
        'concept_match': concept_match,
        'concept_score': concept_score,
        'matched_concepts': matched,
        'missing_concepts': missing,
        'completeness': completeness,
        'feedback': feedback
    }


# =====================================================================
# ENHANCED HEURISTIC NLP EVALUATION ENGINE (Guaranteed Fallback)
# =====================================================================

def evaluate_with_heuristic_nlp(question_text, answer_text, language='General', topic='General',
                                 difficulty='Medium', role_name='Software Engineer',
                                 resume_context=None, expected_answer=None, key_concepts=None):
    """
    High-precision, resilient NLP evaluator built on concept matching & linguistics.
    Now uses concept-based semantic evaluation as the PRIMARY scoring signal.

    Scoring Philosophy:
    - Concept coverage (weighted 60%): Does the candidate explain the right concepts?
    - Communication clarity (weighted 20%): Is the explanation clear and structured?
    - Answer completeness (weighted 20%): Is the answer sufficiently detailed?

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

    # ---------------------------------------------------------------
    # PRIMARY SCORING: Concept-Based Evaluation
    # ---------------------------------------------------------------
    concept_result = evaluate_concept_match(
        expected_answer=expected_answer or '',
        candidate_answer=answer_clean,
        key_concepts_str=key_concepts or '',
        question_text=question_text,
        topic=topic,
        difficulty=difficulty
    )

    concept_score = concept_result['concept_score']  # 0-5
    concept_match = concept_result['concept_match']
    matched_concepts = concept_result['matched_concepts']
    missing_concepts = concept_result['missing_concepts']

    # ---------------------------------------------------------------
    # SECONDARY SCORING: Domain Keywords (Supplementary Signal)
    # ---------------------------------------------------------------
    lang_key = (language or 'General').lower()
    known_kws = DOMAIN_KEYWORDS.get(lang_key, DOMAIN_KEYWORDS['python'])
    matched_kws = [kw for kw in known_kws if kw in answer_lower]
    kw_count = len(matched_kws)

    # ---------------------------------------------------------------
    # 1. Technical Score (concept-led, keyword-supplemented)
    # ---------------------------------------------------------------
    if concept_score >= 4.0 or (concept_match in ['high'] and kw_count >= 1):
        tech_score = 5
    elif concept_score >= 3.0 or concept_match == 'medium':
        tech_score = 4
    elif concept_score >= 2.0 or concept_match == 'partial':
        tech_score = 3
    elif concept_score >= 1.0 or (kw_count >= 1 and word_count >= 10):
        tech_score = 2
    else:
        tech_score = 1

    # Ensure partial-concept answers never score 0 (partial credit rule)
    if concept_match == 'partial' and tech_score < 3:
        tech_score = 3
    if concept_match == 'low' and tech_score < 2:
        tech_score = 2

    # ---------------------------------------------------------------
    # 2. Communication Clarity Scoring (1 – 5)
    # ---------------------------------------------------------------
    comm_markers = sum(1 for m in COMMUNICATION_POSITIVE_MARKERS if m in answer_lower)
    filler_markers = sum(1 for u in UNCERTAINTY_MARKERS if re.search(r'\b' + re.escape(u) + r'\b', answer_lower))
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

    # ---------------------------------------------------------------
    # 3. Answer Quality & Completeness Scoring (1 – 5)
    # ---------------------------------------------------------------
    # Use concept-based completeness as primary signal
    quality_score = round(concept_result['completeness'])

    # Cross-validate with length heuristic
    if word_count < 5:
        quality_score = min(quality_score, 1)
    elif word_count < 10:
        quality_score = min(quality_score, 2)

    quality_score = max(1, min(5, quality_score))

    # ---------------------------------------------------------------
    # 4. Confidence Estimate (1 – 5)
    # Observable based on response indicators only.
    # ---------------------------------------------------------------
    confidence_score = 3
    if filler_markers == 0 and comm_markers >= 1 and word_count >= 20:
        confidence_score = 5
    elif filler_markers == 0 and word_count >= 15:
        confidence_score = 4
    elif filler_markers >= 2:
        confidence_score = 2
    elif word_count < 8:
        confidence_score = 1

    # ---------------------------------------------------------------
    # 5. Tailored Feedback, Strength, and Improvement Tip
    # ---------------------------------------------------------------
    topic_str = topic if topic and topic != 'General' else language

    # Use concept evaluation feedback as primary feedback
    feedback = concept_result['feedback']

    # Build strength message
    if matched_concepts:
        strength = f"Good grasp of key concepts: {', '.join(matched_concepts[:3])}."
    elif matched_kws:
        strength = f"Good use of {language} technical vocabulary: {', '.join(matched_kws[:2])}."
    else:
        strength = f"Attempted to address {topic_str} in the context of {role_name}."

    # Build improvement message
    if missing_concepts:
        improvement = f"To score higher, include these key concepts: {', '.join(missing_concepts[:3])}."
    elif concept_match in ['high', 'medium']:
        improvement = f"Consider adding concrete examples or code snippets to reinforce your explanation of {topic_str}."
    else:
        improvement = f"Review the definition and working of {topic_str} in {language}, focusing on technical precision."

    return {
        'technical_score': tech_score,
        'communication_score': comm_score,
        'quality_score': quality_score,
        'confidence_score': confidence_score,
        'feedback': feedback,
        'strength': strength,
        'improvement': improvement,
        'concept_match': concept_match,
        'matched_concepts': matched_concepts,
        'missing_concepts': missing_concepts,
        'source': 'heuristic_nlp_fallback'
    }


# =====================================================================
# PUBLIC AI ANALYSIS INTERFACE (Phase 7 + Phase 9 Concept Evaluation)
# =====================================================================

def analyze_answer(question_text, answer_text, language='General', topic='General',
                   difficulty='Medium', role_name='Software Engineer',
                   resume_context=None, expected_answer=None, key_concepts=None):
    """
    Main entrypoint for AI Answer Analysis with Concept-Based Evaluation.

    Evaluation Priority:
    1. Google Gemini API (with concept-based prompt) — best quality
    2. OpenAI GPT API (with concept-based prompt) — high quality
    3. Heuristic NLP + Concept Matcher — always available, no API required

    The expected_answer is ALWAYS used as a reference only.
    The evaluation is based on conceptual understanding, not exact wording.
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

    # Prepare concept-aware prompt for LLM
    resume_note = f"Candidate Resume Context: {resume_context}" if resume_context else "Candidate: Technical Job Applicant"

    # Build expected answer section for the AI prompt
    expected_section = ""
    if expected_answer:
        expected_section = f"""
REFERENCE ANSWER (for concept comparison only — NOT required exact wording):
"{expected_answer}"

KEY CONCEPTS to evaluate against:
{key_concepts or 'Identify from the reference answer above.'}

EVALUATION RULES:
- Do NOT require the candidate to use the exact words from the reference answer.
- Do NOT penalize different but technically equivalent phrasing.
- DO reward the candidate if they explain the same concept using different words or examples.
- DO give partial credit if the candidate covers the main concept but misses some details.
- DO give low score only if the technical meaning is wrong or completely unrelated.
"""

    prompt = f"""You are NextHire's AI Technical Interview Evaluator for the job role '{role_name}'.
Evaluate the candidate's answer based on CONCEPTUAL UNDERSTANDING and TECHNICAL MEANING.

[INTERVIEW CONTEXT]
Question: {question_text}
Language/Domain: {language}
Topic: {topic}
Difficulty: {difficulty}
Target Role: {role_name}
{resume_note}
{expected_section}
[CANDIDATE ANSWER]
"{answer_clean}"

Scoring Guidelines:
- technical_score 5: Candidate clearly understands the concept, even in different words.
- technical_score 4: Candidate mostly correct, minor omissions.
- technical_score 3: Main concept understood but important details missing (PARTIAL credit).
- technical_score 2: Some relevant ideas but significant technical gaps or mild misconception.
- technical_score 1: Incorrect technical meaning or completely unrelated answer.

Evaluate and produce:
1. technical_score: Integer 1-5 (concept understanding & technical accuracy)
2. communication_score: Integer 1-5 (clarity, structure, readability)
3. quality_score: Integer 1-5 (completeness and depth)
4. confidence_score: Integer 1-5 (observable response fluency estimate only)
5. feedback: 1-2 sentence evaluation noting concept accuracy.
6. strength: One specific strength in the answer.
7. improvement: One specific, actionable improvement.

Output ONLY a JSON object:
{{
  "technical_score": 4,
  "communication_score": 4,
  "quality_score": 4,
  "confidence_score": 4,
  "feedback": "Concise concept-focused feedback.",
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

    # Graceful fallback: Heuristic NLP with Concept Matcher
    return evaluate_with_heuristic_nlp(
        question_text=question_text,
        answer_text=answer_clean,
        language=language,
        topic=topic,
        difficulty=difficulty,
        role_name=role_name,
        resume_context=resume_context,
        expected_answer=expected_answer,
        key_concepts=key_concepts
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


def analyze_and_store_answer(interview_id, question_id, answer_text, user_id=None, status='answered'):
    """
    Evaluates an individual answer and saves the scores and feedback in the answers table.
    Now fetches expected_answer and key_concepts for concept-based evaluation.
    """
    # Fetch question metadata, expected answer, and key concepts
    q_data = fetch_one(
        """
        SELECT q.question_text, q.language, q.topic, q.difficulty,
               q.expected_answer, q.key_concepts,
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
        q_data = fetch_one(
            "SELECT question_text, language, topic, difficulty, expected_answer, key_concepts FROM questions WHERE id = %s",
            (question_id,)
        )

    question_text = q_data['question_text'] if q_data else 'Technical question'
    language = q_data.get('language', 'General') if q_data else 'General'
    topic = q_data.get('topic', 'General') if q_data else 'General'
    difficulty = q_data.get('difficulty', 'Medium') if q_data else 'Medium'
    role_name = q_data.get('role_name', 'Software Engineer') if q_data else 'Software Engineer'
    expected_answer = q_data.get('expected_answer', '') if q_data else ''
    key_concepts = q_data.get('key_concepts', '') if q_data else ''

    # Run AI / NLP Analysis with concept-based evaluation if not skipped
    if status == 'skipped':
        eval_result = {
            'technical_score': 0,
            'communication_score': 0,
            'quality_score': 0,
            'confidence_score': 0,
            'feedback': 'Question explicitly skipped by candidate.',
            'strength': 'None',
            'improvement': 'Review foundational concepts before attempting.'
        }
    else:
        eval_result = analyze_answer(
            question_text=question_text,
            answer_text=answer_text,
            language=language,
            topic=topic,
            difficulty=difficulty,
            role_name=role_name,
            expected_answer=expected_answer,
            key_concepts=key_concepts
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
                status = %s,
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
                status,
                existing['id']
            )
        )
        answer_id = existing['id']
    else:
        answer_id = execute_query(
            """
            INSERT INTO answers
            (interview_id, question_id, answer_text, technical_score, communication_score,
             quality_score, confidence_score, feedback, strength, improvement, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                eval_result['improvement'],
                status
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
1. S_tech : Technical Knowledge & Accuracy (1-5)  — based on CONCEPT MATCH
2. S_qual : Answer Quality & Completeness (1-5)   — based on concept coverage + length
3. S_comm : Communication Clarity (1-5)           — based on structure & articulation
4. S_conf : Observable Confidence Estimate (1-5)  — based on response fluency indicators

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
- Technical Skills: 40% (Core concept accuracy — NOT keyword memorization)
- Answer Quality:   25% (Depth, completeness, concept coverage)
- Communication:    20% (Structure, vocabulary, clarity)
- Confidence:       15% (Observable response fluency and decisiveness)
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
        strengths.insert(0, f"Good {top_lang} conceptual understanding demonstrated.")
    else:
        strengths.append("Willingness to attempt diverse technical question prompts.")

    if len(strengths) < 2 and languages_covered:
        strengths.append(f"Demonstrated foundational understanding of {', '.join(languages_covered)}.")

    if low_scoring_topics:
        low_lang, low_topic = low_scoring_topics[0]
        weaknesses.insert(0, f"Deepen concept explanation clarity for {low_topic} in {low_lang}.")
    else:
        weaknesses.append("Give more complete and detailed answers with examples or analogies.")

    if len(weaknesses) < 2:
        weaknesses.append("Improve technical communication by reducing filler hesitation words.")

    # Actionable Recommendations
    for lang in languages_covered:
        if lang.lower() == 'python':
            recommendations.append("Practice explaining Python OOP concepts (inheritance, polymorphism, encapsulation) with examples.")
        elif lang.lower() == 'sql':
            recommendations.append("Practice complex SQL queries including JOINs, GROUP BY, and HAVING clauses.")
        elif lang.lower() == 'javascript':
            recommendations.append("Master closures, asynchronous JavaScript (async/await, Promises), and scope.")
        elif lang.lower() == 'java':
            recommendations.append("Review Java OOP pillars, multithreading, and the collections framework.")
        elif lang.lower() == 'c':
            recommendations.append("Strengthen pointer arithmetic, dynamic memory management, and structures.")

    recommendations.append("Structure answers as: Definition → How it works → Example → Use case.")
    recommendations.append(f"Review {role_name} interview topics and practice explaining concepts in your own words.")

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

    # 2. Fetch all assigned questions and candidate answers (including expected_answer and key_concepts)
    assigned_questions = fetch_all(
        """
        SELECT iq.question_order, q.id as question_id, q.question_code, q.language,
               q.topic, q.difficulty, q.question_text,
               q.expected_answer, q.key_concepts,
               a.id as answer_id, a.answer_text, a.technical_score, a.communication_score,
               a.quality_score, a.confidence_score, a.feedback, a.strength, a.improvement, a.status
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
                role_name=role_name,
                expected_answer=item.get('expected_answer', ''),
                key_concepts=item.get('key_concepts', '')
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
    # Filter out skipped answers from the final scoring calculation
    scored_answers = [a for a in analyzed_answers if a.get('status') != 'skipped']
    final_scores = calculate_final_scores(scored_answers)

    # 5. Synthesize Personalized Feedback
    feedback_bundle = synthesize_personalized_feedback(scored_answers, role_name=role_name)
    
    answered_count = len(scored_answers)
    skipped_count = len(analyzed_answers) - answered_count
    total_q = len(analyzed_answers)
    answered_percentage = round((answered_count / total_q) * 100, 1) if total_q > 0 else 0.0

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
                answered_count = %s,
                skipped_count = %s,
                answered_percentage = %s,
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
                answered_count,
                skipped_count,
                answered_percentage,
                existing['id']
            )
        )
        res_id = existing['id']
    else:
        res_id = execute_query(
            """
            INSERT INTO interview_results
            (interview_id, overall_score, technical_score, communication_score,
             quality_score, confidence_score, strengths, weaknesses, recommendations,
             answered_count, skipped_count, answered_percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                recs_json,
                answered_count,
                skipped_count,
                answered_percentage
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
        'answered_count': answered_count,
        'skipped_count': skipped_count,
        'answered_percentage': answered_percentage,
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
               a.quality_score, a.confidence_score, a.feedback, a.strength, a.improvement, a.status
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

    ai_engine = "Academic Heuristic NLP + Concept Matcher (Active)"
    if GEMINI_API_KEY:
        ai_engine = "Google Gemini AI + Concept Evaluation (Active via GEMINI_API_KEY)"
    elif OPENAI_API_KEY:
        ai_engine = "OpenAI GPT-4o-mini + Concept Evaluation (Active via OPENAI_API_KEY)"

    return {
        'interview_id': interview['id'],
        'role_name': interview.get('role_name', 'Software Engineer'),
        'difficulty': interview.get('difficulty', 'Medium'),
        'total_questions': interview.get('total_questions', len(detailed_answers)),
        'answered_count': res_record.get('answered_count', sum(1 for a in detailed_answers if a.get('status') != 'skipped' and a.get('answer_text'))),
        'skipped_count': res_record.get('skipped_count', sum(1 for a in detailed_answers if a.get('status') == 'skipped')),
        'answered_percentage': res_record.get('answered_percentage', 100.0),
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
            'evaluation_method': 'Concept-based semantic matching (not exact string comparison)',
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
                'status': a.get('status') or 'answered',
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
