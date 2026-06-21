"""
GrantStar — Credential Vault
Encrypted storage for user profiles, portal credentials, and proposal data.
Uses Fernet symmetric encryption for sensitive fields.
"""

import os
import json
import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grantstar.db")
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".vault_key")


def _get_cipher():
    """Get or create the Fernet cipher for encryption."""
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as f:
            f.write(key)
    return Fernet(key)


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_vault():
    """Create vault tables."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            city TEXT DEFAULT '',
            state_province TEXT DEFAULT '',
            country TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            org_name TEXT DEFAULT '',
            org_type TEXT DEFAULT '',
            org_registration_number TEXT DEFAULT '',
            org_year_founded TEXT DEFAULT '',
            org_website TEXT DEFAULT '',
            sector TEXT DEFAULT '',
            stage TEXT DEFAULT '',
            tax_id TEXT DEFAULT '',
            document_paths TEXT DEFAULT '{}',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS portal_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            portal_name TEXT NOT NULL,
            portal_url TEXT DEFAULT '',
            encrypted_email TEXT DEFAULT '',
            encrypted_password TEXT DEFAULT '',
            extra_data TEXT DEFAULT '{}',
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, portal_name)
        );

        CREATE TABLE IF NOT EXISTS saved_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            grant_id TEXT NOT NULL,
            project_name TEXT DEFAULT '',
            problem TEXT DEFAULT '',
            solution TEXT DEFAULT '',
            impact TEXT DEFAULT '',
            beneficiaries TEXT DEFAULT '',
            budget_usd REAL DEFAULT 0,
            extra_fields TEXT DEFAULT '{}',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, grant_id)
        );
    """)
    conn.commit()
    conn.close()
    print("  ✅ Vault tables initialized")


# ── USER PROFILE ──────────────────────────────────────────────────

def save_profile(user_id, data):
    """Save or update the user's full profile for auto-fill."""
    conn = _get_db()
    fields = [
        "full_name", "email", "phone", "address", "city", "state_province",
        "country", "bio", "org_name", "org_type", "org_registration_number",
        "org_year_founded", "org_website", "sector", "stage", "tax_id"
    ]

    # Handle document_paths as JSON
    doc_paths = json.dumps(data.get("document_paths", {}))

    existing = conn.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()

    if existing:
        sets = ", ".join(f"{f} = ?" for f in fields)
        values = [data.get(f, "") for f in fields]
        values.append(doc_paths)
        values.append(datetime.utcnow().isoformat())
        values.append(user_id)
        conn.execute(
            f"UPDATE user_profiles SET {sets}, document_paths = ?, updated_at = ? WHERE user_id = ?",
            values
        )
    else:
        placeholders = ", ".join(["?"] * (len(fields) + 2))
        field_names = ", ".join(fields) + ", document_paths, user_id"
        values = [data.get(f, "") for f in fields]
        values.append(doc_paths)
        values.append(user_id)
        conn.execute(f"INSERT INTO user_profiles ({field_names}) VALUES ({placeholders})", values)

    conn.commit()
    conn.close()
    return True


def get_profile(user_id):
    """Get the user's full profile."""
    conn = _get_db()
    row = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    if not row:
        return None

    profile = dict(row)
    try:
        profile["document_paths"] = json.loads(profile.get("document_paths", "{}"))
    except (json.JSONDecodeError, TypeError):
        profile["document_paths"] = {}
    return profile


def get_profile_completion(user_id):
    """Calculate profile completion percentage."""
    profile = get_profile(user_id)
    if not profile:
        return 0, []

    required_fields = [
        ("full_name", "Full Name"),
        ("email", "Email"),
        ("phone", "Phone Number"),
        ("country", "Country"),
        ("org_name", "Organization Name"),
        ("org_type", "Organization Type"),
        ("sector", "Sector"),
        ("tax_id", "Tax ID (TIN/KRA/SARS)"),
        ("bio", "Bio / Organization Description"),
    ]

    filled = 0
    missing = []
    for field, label in required_fields:
        if profile.get(field):
            filled += 1
        else:
            missing.append(label)

    pct = int((filled / len(required_fields)) * 100)
    return pct, missing


# ── PORTAL CREDENTIALS ────────────────────────────────────────────

def save_portal_creds(user_id, portal_name, email, password, portal_url="", extra=None):
    """Save encrypted portal credentials."""
    cipher = _get_cipher()
    enc_email = cipher.encrypt(email.encode()).decode()
    enc_password = cipher.encrypt(password.encode()).decode()
    extra_json = json.dumps(extra or {})

    conn = _get_db()
    conn.execute("""
        INSERT INTO portal_credentials (user_id, portal_name, portal_url, encrypted_email, encrypted_password, extra_data)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, portal_name) DO UPDATE SET
            portal_url = excluded.portal_url,
            encrypted_email = excluded.encrypted_email,
            encrypted_password = excluded.encrypted_password,
            extra_data = excluded.extra_data,
            registered_at = CURRENT_TIMESTAMP
    """, (user_id, portal_name, portal_url, enc_email, enc_password, extra_json))
    conn.commit()
    conn.close()
    return True


def get_portal_creds(user_id, portal_name):
    """Get decrypted portal credentials."""
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM portal_credentials WHERE user_id = ? AND portal_name = ?",
        (user_id, portal_name)
    ).fetchone()
    conn.close()

    if not row:
        return None

    cipher = _get_cipher()
    try:
        email = cipher.decrypt(row["encrypted_email"].encode()).decode()
        password = cipher.decrypt(row["encrypted_password"].encode()).decode()
    except Exception:
        return None

    return {
        "portal_name": row["portal_name"],
        "portal_url": row["portal_url"],
        "email": email,
        "password": password,
        "extra": json.loads(row["extra_data"] or "{}"),
        "registered_at": row["registered_at"],
    }


def list_portal_creds(user_id):
    """List all saved portal names (without passwords)."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT portal_name, portal_url, registered_at FROM portal_credentials WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── SAVED PROPOSALS ───────────────────────────────────────────────

def save_proposal_data(user_id, grant_id, data):
    """Save proposal draft data for a specific grant."""
    extra = json.dumps(data.get("extra_fields", {}))
    conn = _get_db()
    conn.execute("""
        INSERT INTO saved_proposals (user_id, grant_id, project_name, problem, solution, impact, beneficiaries, budget_usd, extra_fields)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, grant_id) DO UPDATE SET
            project_name = excluded.project_name,
            problem = excluded.problem,
            solution = excluded.solution,
            impact = excluded.impact,
            beneficiaries = excluded.beneficiaries,
            budget_usd = excluded.budget_usd,
            extra_fields = excluded.extra_fields,
            updated_at = CURRENT_TIMESTAMP
    """, (
        user_id, grant_id,
        data.get("project_name", ""),
        data.get("problem", ""),
        data.get("solution", ""),
        data.get("impact", ""),
        data.get("beneficiaries", ""),
        data.get("budget_usd", 0),
        extra,
    ))
    conn.commit()
    conn.close()
    return True


def get_proposal_data(user_id, grant_id):
    """Get saved proposal draft for a grant."""
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM saved_proposals WHERE user_id = ? AND grant_id = ?",
        (user_id, grant_id)
    ).fetchone()
    conn.close()

    if not row:
        return None

    result = dict(row)
    try:
        result["extra_fields"] = json.loads(result.get("extra_fields", "{}"))
    except (json.JSONDecodeError, TypeError):
        result["extra_fields"] = {}
    return result
