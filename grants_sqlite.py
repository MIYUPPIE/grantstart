import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_grants_db():
    """Initialize the grants and compliance tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # GRANTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            funder TEXT,
            type TEXT,
            amount_min REAL,
            amount_max REAL,
            currency TEXT,
            deadline TEXT,
            sectors TEXT,
            eligible_countries TEXT,
            excluded_countries TEXT,
            org_types TEXT,
            stages TEXT,
            url TEXT,
            description TEXT,
            required_docs TEXT,
            difficulty INTEGER,
            tags TEXT
        )
    """)

    # COUNTRY COMPLIANCE KNOWLEDGE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS country_docs (
            country TEXT PRIMARY KEY,
            doc_data TEXT
        )
    """)

    # SDG IMPACT TRANSLATIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS impact_translations (
            keyword TEXT PRIMARY KEY,
            translation_data TEXT
        )
    """)

    conn.commit()
    conn.close()

def save_grant(grant_dict):
    """Save or update a grant in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Flatten amount_usd for easier storage
    amount_min = grant_dict.get("amount_usd", {}).get("min", 0)
    amount_max = grant_dict.get("amount_usd", {}).get("max", 0)

    cursor.execute("""
        INSERT OR REPLACE INTO grants (
            id, name, funder, type, amount_min, amount_max, currency, deadline,
            sectors, eligible_countries, excluded_countries, org_types, stages,
            url, description, required_docs, difficulty, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        grant_dict["id"],
        grant_dict["name"],
        grant_dict.get("funder"),
        grant_dict.get("type"),
        amount_min,
        amount_max,
        grant_dict.get("currency"),
        grant_dict.get("deadline"),
        json.dumps(grant_dict.get("sectors", [])),
        json.dumps(grant_dict.get("eligible_countries", [])),
        json.dumps(grant_dict.get("excluded_countries", [])),
        json.dumps(grant_dict.get("org_types", [])),
        json.dumps(grant_dict.get("stages", [])),
        grant_dict.get("url"),
        grant_dict.get("description"),
        json.dumps(grant_dict.get("required_docs", {})),
        grant_dict.get("difficulty", 5),
        json.dumps(grant_dict.get("tags", []))
    ))
    conn.commit()
    conn.close()

def get_all_grants():
    """Fetch all grants from DB and reconstitute JSON fields."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grants")
    rows = cursor.fetchall()
    conn.close()

    grants = []
    for row in rows:
        g = dict(row)
        # Re-map amount_usd structure
        g["amount_usd"] = {"min": g.pop("amount_min"), "max": g.pop("amount_max")}
        # Parse JSON fields
        for field in ["sectors", "eligible_countries", "excluded_countries", "org_types", "stages", "required_docs", "tags"]:
            try:
                g[field] = json.loads(g[field])
            except:
                g[field] = [] if field != "required_docs" else {}
        grants.append(g)
    return grants

def save_country_docs(country, data_dict):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO country_docs (country, doc_data) VALUES (?, ?)", (country, json.dumps(data_dict)))
    conn.commit()
    conn.close()

def get_country_docs(country):
    conn = get_db_connection()
    row = conn.execute("SELECT doc_data FROM country_docs WHERE country = ?", (country,)).fetchone()
    conn.close()
    return json.loads(row["doc_data"]) if row else None

def save_impact_translation(keyword, data_dict):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO impact_translations (keyword, translation_data) VALUES (?, ?)", (keyword, json.dumps(data_dict)))
    conn.commit()
    conn.close()

def get_all_impact_translations():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM impact_translations").fetchall()
    conn.close()
    return {row["keyword"]: json.loads(row["translation_data"]) for row in rows}
