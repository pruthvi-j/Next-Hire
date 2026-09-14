import os
import openpyxl
from database import get_db_connection, execute_query, fetch_one, init_db

# Primary and alternative paths for the Excel question bank
DEFAULT_EXCEL_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'NextHire Question Bank.xlsx'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NextHire Question Bank.xlsx'),
    r"C:\Users\Admin\OneDrive\Documents\NextHire Question Bank.xlsx"
]

REQUIRED_COLUMNS = ['ID', 'Language', 'Topic', 'Difficulty', 'Question']


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
    """
    # Ensure database tables exist
    init_db()

    if not excel_path:
        excel_path = locate_excel_file()

    print(f"==================================================")
    print(f"        NEXT HIRE - QUESTION BANK IMPORTER        ")
    print(f"==================================================")
    print(f"[INFO] Source Excel File: {excel_path}")

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    
    total_rows_read = 0
    imported_count = 0
    updated_count = 0
    skipped_headers = 0

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
            for req in REQUIRED_COLUMNS:
                if col_name.lower() == req.lower():
                    header_map[req] = idx

        # Validate that required columns exist
        missing_cols = [req for req in REQUIRED_COLUMNS if req not in header_map]
        if missing_cols:
            print(f"[SKIP] Sheet '{sheet_name}' is missing required columns: {missing_cols}. Ignoring sheet.")
            continue

        print(f"[SUCCESS] Validated columns in '{sheet_name}': {REQUIRED_COLUMNS}")

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

            # Idempotent database insertion: check if question_code already exists
            existing = fetch_one("SELECT id FROM questions WHERE question_code = %s", (q_code,))
            if existing:
                # Update existing record to ensure data integrity without duplication
                execute_query(
                    """
                    UPDATE questions 
                    SET language = %s, topic = %s, difficulty = %s, question_text = %s, active = 1
                    WHERE question_code = %s
                    """,
                    (language, topic, difficulty, question_text, q_code)
                )
                updated_count += 1
            else:
                # Insert new question
                execute_query(
                    """
                    INSERT INTO questions (question_code, language, topic, difficulty, question_text, active)
                    VALUES (%s, %s, %s, %s, %s, 1)
                    """,
                    (q_code, language, topic, difficulty, question_text)
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
    print(f"Total Active Questions in Bank: {total_valid}")
    print(f"==================================================")

    return total_valid


if __name__ == '__main__':
    import_questions_from_excel()
