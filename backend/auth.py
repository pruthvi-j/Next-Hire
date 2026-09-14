import re
from functools import wraps
from flask import session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import fetch_one, execute_query


def is_valid_email(email):
    """Simple regex to validate email format."""
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_regex, email) is not None


def register_user(name, email, password):
    """
    Validates user input, hashes the password, and creates a new user record.
    Returns: (success: bool, message: str, user_data: dict | None)
    """
    name = (name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not name or len(name) < 2:
        return False, "Full name must be at least 2 characters.", None

    if not email or not is_valid_email(email):
        return False, "Please enter a valid email address.", None

    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    # Check for existing email
    existing_user = fetch_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing_user:
        return False, "An account with this email already exists.", None

    # Secure password hashing (Werkzeug uses pbkdf2:sha256/scrypt)
    hashed_password = generate_password_hash(password)

    try:
        user_id = execute_query(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        return True, "User registered successfully.", {
            "id": user_id,
            "name": name,
            "email": email
        }
    except Exception as err:
        return False, f"Registration failed due to a database error: {str(err)}", None


def authenticate_user(email, password):
    """
    Verifies credentials and returns user details upon successful authentication.
    Returns: (success: bool, message: str, user_data: dict | None)
    """
    email = (email or "").strip().lower()
    password = password or ""

    if not email or not password:
        return False, "Email and password are required.", None

    user = fetch_one("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
    if not user:
        return False, "Invalid email or password.", None

    if not check_password_hash(user["password"], password):
        return False, "Invalid email or password.", None

    return True, "Login successful.", {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }


def get_user_by_id(user_id):
    """Fetches user details by user ID (excluding password)."""
    if not user_id:
        return None
    return fetch_one("SELECT id, name, email, created_at FROM users WHERE id = %s", (user_id,))


def login_required(f):
    """Decorator to enforce session-based authentication on protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "status": "error",
                "authenticated": False,
                "message": "Authentication required. Please log in."
            }), 401
        return f(*args, **kwargs)
    return decorated_function
