import os
import re
import openpyxl
from database import get_db_connection, execute_query, fetch_one, init_db

# Primary and alternative paths for the Excel question bank
DEFAULT_EXCEL_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'NextHire Question Bank.xlsx'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NextHire Question Bank.xlsx'),
    r"C:\Users\Admin\OneDrive\Documents\NextHire Question Bank.xlsx"
]

REQUIRED_COLUMNS = ['ID', 'Language', 'Topic', 'Difficulty', 'Question']
OPTIONAL_COLUMNS = ['Expected Answer']

# =====================================================================
# KEY CONCEPT EXTRACTION ENGINE
# =====================================================================

# Common stop words to filter out when extracting key concepts
STOP_WORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'out', 'up', 'down',
    'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
    'neither', 'each', 'every', 'all', 'any', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'only', 'same', 'than', 'too', 'very',
    'just', 'because', 'if', 'when', 'where', 'how', 'what', 'which',
    'who', 'whom', 'this', 'that', 'these', 'those', 'i', 'me', 'my',
    'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it',
    'its', 'they', 'them', 'their', 'while', 'also', 'about', 'then',
    'there', 'here', 'over', 'under', 'again', 'further', 'once',
    'used', 'using', 'uses', 'use', 'like', 'well', 'includes', 'include',
    'such', 'commonly', 'generally', 'allows', 'allow', 'provides',
    'provide', 'means', 'means', 'known', 'called', 'refers', 'refer',
    'typically', 'often', 'usually', 'example'
}

# Technical terms that should always be preserved as key concepts
TECHNICAL_TERMS = {
    # Python
    'mutable', 'immutable', 'list', 'tuple', 'dictionary', 'dict', 'set',
    'decorator', 'generator', 'lambda', 'class', 'object', 'inheritance',
    'polymorphism', 'encapsulation', 'function', 'variable', 'module',
    'exception', 'try-except', 'args', 'kwargs', 'shallow copy', 'deep copy',
    'dynamic typing', 'interpreted', 'high-level', 'general-purpose',

    # Java
    'jvm', 'jdk', 'jre', 'bytecode', 'interface', 'abstract', 'overloading',
    'overriding', 'multithreading', 'arraylist', 'linkedlist', 'hashmap',
    'primitive types', 'platform independence', 'garbage collection',

    # C
    'pointer', 'memory address', 'malloc', 'calloc', 'struct', 'structure',
    'null pointer', 'pointer arithmetic', 'dynamic memory allocation',
    'storage classes', 'auto', 'register', 'static', 'extern', 'array',
    'procedural', 'embedded systems',

    # JavaScript
    'closure', 'callback', 'promise', 'async', 'await', 'hoisting',
    'scope', 'dom', 'event bubbling', 'prototype', 'arrow function',
    'es6', 'json', 'destructuring', 'template literals', 'let', 'const', 'var',
    'block scope', 'function scope', 'lexical', 'asynchronous',

    # SQL
    'primary key', 'foreign key', 'inner join', 'left join', 'group by',
    'where', 'having', 'aggregate', 'normalization', 'subquery',
    'acid', 'atomicity', 'consistency', 'isolation', 'durability',
    'select', 'ddl', 'dml', 'asc', 'desc', 'null',

    # General OOP / CS
    'oop', 'object-oriented', 'data structures', 'algorithms',
    'abstraction', 'data type', 'boolean', 'integer', 'float', 'string',
    'recursion', 'iteration', 'loop', 'for loop', 'while loop',
    'condition', 'if-else', 'elif', 'switch',
    'reusable', 'blueprint', 'instance', 'parameter', 'return value',
    'key-value', 'hashable', 'runtime', 'compile time',
    'code reuse', 'hierarchical', 'parent class', 'child class',
    'contiguous memory', 'linked nodes', 'random access',
}


def extract_key_concepts(expected_answer, question_text='', language='', topic=''):
    """
    Extracts key technical concepts from an expected answer.
    Uses a combination of:
    1. Technical term matching against known vocabulary
    2. Noun phrase extraction using simple NLP patterns
    3. Important qualifier extraction (mutable/immutable, etc.)

    Returns a comma-separated string of key concepts.
    """
    if not expected_answer:
        return ''

    text = expected_answer.strip()
    text_lower = text.lower()
    concepts = []

    # 1. Match known technical terms (preserving multi-word terms)
    for term in sorted(TECHNICAL_TERMS, key=len, reverse=True):
        if term.lower() in text_lower:
            # Avoid duplicates
            if term.lower() not in [c.lower() for c in concepts]:
                concepts.append(term)

    # 2. Extract additional single-word technical nouns not in stop words
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_+#.]*', text)
    for word in words:
        w_lower = word.lower()
        if (w_lower not in STOP_WORDS and
            len(w_lower) > 2 and
            w_lower not in [c.lower() for c in concepts]):
            # Check if it looks like a technical term
            # (capitalized, contains special chars, or is a known pattern)
            if (word[0].isupper() or
                '_' in word or
                any(c in word for c in '+#.') or
                w_lower in TECHNICAL_TERMS):
                concepts.append(word)

    # 3. Extract key verb-object patterns like "stores memory address"
    patterns = [
        r'stores?\s+([\w\s]+?)(?:\.|,|$)',
        r'defines?\s+([\w\s]+?)(?:\.|,|$)',
        r'creates?\s+([\w\s]+?)(?:\.|,|$)',
        r'supports?\s+([\w\s]+?)(?:\.|,|$)',
        r'filters?\s+([\w\s]+?)(?:\.|,|$)',
        r'executes?\s+([\w\s]+?)(?:\.|,|$)',
    ]
    for pat in patterns:
        matches = re.findall(pat, text_lower)
        for match in matches:
            phrase = match.strip()
            # Only short meaningful phrases
            phrase_words = phrase.split()
            if 1 < len(phrase_words) <= 4:
                clean = ' '.join(w for w in phrase_words if w not in STOP_WORDS)
                if clean and clean not in [c.lower() for c in concepts]:
                    concepts.append(clean)

    # 4. Add the topic and language as context concepts if not already present
    if topic and topic.lower() not in [c.lower() for c in concepts]:
        concepts.append(topic)
    if language and language.lower() not in [c.lower() for c in concepts]:
        concepts.append(language)

    # Limit to most relevant concepts (max 15)
    return ', '.join(concepts[:15])


def locate_excel_file():
    """Finds the question bank Excel file from standard project locations."""
    for path in DEFAULT_EXCEL_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "Could not locate 'NextHire Question Bank.xlsx'. "
        "Please ensure the file exists in 'database/' or 'backend/'."
    )


def import_questions_from_excel(excel_path=None):
    """
    Reads the Excel question bank, validates sheets and columns,
    and performs idempotent insertion into the MySQL/SQLite database.
    Now also imports expected answers and generates key concepts.
    """
    # Ensure database tables exist
    init_db()

    if not excel_path:
        excel_path = locate_excel_file()

    print(f"==================================================")
    print(f"        NEXT HIRE - QUESTION BANK IMPORTER        ")
    print(f"     (With Expected Answers & Key Concepts)       ")
    print(f"==================================================")
    print(f"[INFO] Source Excel File: {excel_path}")

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    
    total_rows_read = 0
    imported_count = 0
    updated_count = 0
    skipped_headers = 0
    answers_imported = 0

    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        print(f"\n[INFO] Inspecting Sheet: '{sheet_name}' (max_row={sheet.max_row}, max_column={sheet.max_column})")

        # Ignore empty sheets (rule requirement)
        if sheet.max_row <= 1:
            print(f"[SKIP] Sheet '{sheet_name}' is empty or contains only 1 row. Ignoring.")
            continue

        # Read header row
        header_row = [str(cell.value).strip() if cell.value is not None else '' for cell in sheet[1]]
        header_map = {}
        for idx, col_name in enumerate(header_row):
            for req in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
                if col_name.lower() == req.lower():
                    header_map[req] = idx

        # Validate that required columns exist
        missing_cols = [req for req in REQUIRED_COLUMNS if req not in header_map]
        if missing_cols:
            print(f"[SKIP] Sheet '{sheet_name}' is missing required columns: {missing_cols}. Ignoring sheet.")
            continue

        has_expected_answer = 'Expected Answer' in header_map
        print(f"[SUCCESS] Validated columns in '{sheet_name}': {REQUIRED_COLUMNS}")
        if has_expected_answer:
            print(f"[SUCCESS] 'Expected Answer' column detected — will import reference answers.")
        else:
            print(f"[INFO] No 'Expected Answer' column found — importing questions only.")

        # Process data rows
        for row_idx in range(2, sheet.max_row + 1):
            row_cells = [cell.value for cell in sheet[row_idx]]
            if not any(row_cells):
                continue

            total_rows_read += 1

            q_code = str(row_cells[header_map['ID']]).strip() if row_cells[header_map['ID']] is not None else ''
            language = str(row_cells[header_map['Language']]).strip() if row_cells[header_map['Language']] is not None else ''
            topic = str(row_cells[header_map['Topic']]).strip() if row_cells[header_map['Topic']] is not None else ''
            difficulty = str(row_cells[header_map['Difficulty']]).strip() if row_cells[header_map['Difficulty']] is not None else ''
            question_text = str(row_cells[header_map['Question']]).strip() if row_cells[header_map['Question']] is not None else ''

            # Read expected answer if column exists
            expected_answer = ''
            if has_expected_answer:
                raw_answer = row_cells[header_map['Expected Answer']]
                expected_answer = str(raw_answer).strip() if raw_answer is not None else ''

            # Ignore repeated internal header rows (e.g. 'ID', 'Language', ...)
            if q_code.upper() == 'ID' or language.upper() == 'LANGUAGE':
                skipped_headers += 1
                continue

            if not q_code or not question_text:
                continue

            # Standardize difficulty casing ('Easy', 'Medium', 'Hard')
            difficulty = difficulty.capitalize() if difficulty else 'Medium'
            if difficulty not in ['Easy', 'Medium', 'Hard']:
                difficulty = 'Medium'

            # Auto-generate key concepts from expected answer
            key_concepts = extract_key_concepts(
                expected_answer=expected_answer,
                question_text=question_text,
                language=language,
                topic=topic
            )

            if expected_answer:
                answers_imported += 1

            # Idempotent database insertion: check if question_code already exists
            existing = fetch_one("SELECT id FROM questions WHERE question_code = %s", (q_code,))
            if existing:
                # Update existing record to ensure data integrity without duplication
                execute_query(
                    """
                    UPDATE questions 
                    SET language = %s, topic = %s, difficulty = %s, question_text = %s,
                        expected_answer = %s, key_concepts = %s, active = 1
                    WHERE question_code = %s
                    """,
                    (language, topic, difficulty, question_text, expected_answer, key_concepts, q_code)
                )
                updated_count += 1
            else:
                # Insert new question
                execute_query(
                    """
                    INSERT INTO questions (question_code, language, topic, difficulty, question_text,
                                           expected_answer, key_concepts, active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (q_code, language, topic, difficulty, question_text, expected_answer, key_concepts)
                )
                imported_count += 1

    wb.close()

    total_valid = imported_count + updated_count
    print(f"\n==================================================")
    print(f"             IMPORT SUMMARY REPORT                ")
    print(f"==================================================")
    print(f"Total Rows Evaluated: {total_rows_read}")
    print(f"Repeated Header Rows Skipped: {skipped_headers}")
    print(f"Newly Imported Questions: {imported_count}")
    print(f"Existing Questions Updated (Idempotent): {updated_count}")
    print(f"Questions with Expected Answers: {answers_imported}")
    print(f"Total Active Questions in Bank: {total_valid}")
    print(f"==================================================")

    return total_valid


if __name__ == '__main__':
    import_questions_from_excel()
