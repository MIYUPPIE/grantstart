"""
GrantStar — User Authentication Module
SQLite-based user management with secure password hashing.
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grantstar.db")


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database and create tables."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            country TEXT DEFAULT '',
            sector TEXT DEFAULT '',
            org_type TEXT DEFAULT '',
            stage TEXT DEFAULT '',
            registered_org INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("  ✅ Database initialized")


def register_user(full_name, email, password, country="", sector="", org_type="", stage="", registered_org=False):
    """
    Register a new user.
    Returns (success: bool, message: str, user_id: int or None)
    """
    # Validation
    if not full_name or not full_name.strip():
        return False, "Full name is required.", None
    if not email or "@" not in email:
        return False, "A valid email address is required.", None
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters.", None

    email = email.strip().lower()
    full_name = full_name.strip()

    conn = get_db()
    try:
        # Check if email already exists
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            return False, "An account with this email already exists.", None

        # Hash password and insert
        password_hash = generate_password_hash(password)
        cursor = conn.execute(
            """INSERT INTO users (full_name, email, password_hash, country, sector, org_type, stage, registered_org)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (full_name, email, password_hash, country, sector, org_type, stage, int(registered_org))
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, "Account created successfully!", user_id

    except sqlite3.IntegrityError:
        conn.close()
        return False, "An account with this email already exists.", None
    except Exception as e:
        conn.close()
        return False, f"Registration failed: {str(e)}", None


def authenticate_user(email, password):
    """
    Authenticate a user by email and password.
    Returns (success: bool, message: str, user_data: dict or None)
    """
    if not email or not password:
        return False, "Email and password are required.", None

    email = email.strip().lower()

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        return False, "No account found with this email.", None

    if not check_password_hash(user["password_hash"], password):
        return False, "Incorrect password.", None

    user_data = {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "country": user["country"],
        "sector": user["sector"],
        "org_type": user["org_type"],
        "stage": user["stage"],
        "registered_org": bool(user["registered_org"]),
        "created_at": user["created_at"],
    }

    return True, "Login successful!", user_data


def get_user_by_id(user_id):
    """Fetch a user by ID for session restoration."""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not user:
        return None

    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "country": user["country"],
        "sector": user["sector"],
        "org_type": user["org_type"],
        "stage": user["stage"],
        "registered_org": bool(user["registered_org"]),
        "created_at": user["created_at"],
    }
