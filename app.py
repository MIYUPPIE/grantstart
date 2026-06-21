"""
GrantStar — Flask Web Application
African-Centric Global Grant Strategist
With User Authentication (Login / Registration)
"""

import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from grantstar_engine import search_grants, get_compliance_docs, draft_proposal
from grants_db import GRANTS
from auth import init_db, register_user, authenticate_user, get_user_by_id
from vault import init_vault, save_profile, get_profile, save_portal_creds, get_portal_creds, list_portal_creds, save_proposal_data, get_proposal_data
from automator import get_portal_workflow, build_form_data, get_registration_steps
from ai_strategist import is_ai_active, analyze_strategy, active_model, provider_label
from grants_sqlite import init_grants_db


# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "grantstar-fallback-key-998877")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ── AUTH DECORATOR ────────────────────────────────────────────────
def login_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            # For API routes, return JSON error
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            # For page routes, redirect to login
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


# ── VAULT API ─────────────────────────────────────────────────────

@app.route("/api/vault/profile", methods=["GET", "POST"])
@login_required
def api_vault_profile():
    """Get or update the user's full automation profile."""
    user_id = session["user_id"]
    if request.method == "POST":
        data = request.get_json()
        save_profile(user_id, data)
        return jsonify({"status": "success", "message": "Profile updated in vault."})
    
    profile = get_profile(user_id)
    return jsonify({"profile": profile or {}})


@app.route("/api/vault/credentials", methods=["GET", "POST"])
@login_required
def api_vault_credentials():
    """Get list of portal credentials or save new ones."""
    user_id = session["user_id"]
    if request.method == "POST":
        data = request.get_json()
        required = ["portal_name", "email", "password"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        save_portal_creds(
            user_id, 
            data["portal_name"], 
            data["email"], 
            data["password"], 
            data.get("portal_url", ""),
            data.get("extra", {})
        )
        return jsonify({"status": "success", "message": "Credentials saved to vault."})
    
    creds = list_portal_creds(user_id)
    return jsonify({"credentials": creds})


@app.route("/api/vault/credentials/<portal_name>", methods=["GET"])
@login_required
def api_get_credential(portal_name):
    """Get decrypted credentials for a specific portal."""
    creds = get_portal_creds(session["user_id"], portal_name)
    if not creds:
        return jsonify({"error": "Credentials not found"}), 404
    return jsonify({"credentials": creds})


# ── AUTO-APPLY API ────────────────────────────────────────────────

@app.route("/api/apply/prepare", methods=["POST"])
@login_required
def api_apply_prepare():
    """Prepare auto-fill data for a grant application."""
    data = request.get_json()
    grant_id = data.get("grant_id")
    if not grant_id:
        return jsonify({"error": "grant_id is required"}), 400
    
    user_id = session["user_id"]
    profile = get_profile(user_id)
    # Get last saved proposal or use provided data
    proposal = get_proposal_data(user_id, grant_id)
    
    if not profile:
        return jsonify({"error": "Profile not found in vault. Please complete your profile first."}), 400
    
    # Map data to portal fields
    form_data = build_form_data(grant_id, profile, proposal)
    return jsonify(form_data)


@app.route("/api/apply/registration", methods=["POST"])
@login_required
def api_apply_registration():
    """Get portal registration steps for a grant."""
    data = request.get_json()
    grant_id = data.get("grant_id")
    if not grant_id:
        return jsonify({"error": "grant_id is required"}), 400
    
    profile = get_profile(session["user_id"]) or {}
    steps = get_registration_steps(grant_id, profile)
    return jsonify(steps)


@app.route("/api/apply/save-proposal", methods=["POST"])
@login_required
def api_save_proposal():
    """Save the draft proposal to the vault for future auto-fill."""
    data = request.get_json()
    required = ["grant_id", "project_name", "problem", "solution", "impact"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    save_proposal_data(session["user_id"], data["grant_id"], data)
    return jsonify({"status": "success", "message": "Proposal saved to vault."})


# ── AUTH PAGES ────────────────────────────────────────────────────
@app.route("/login")
def login_page():
    """Serve the login page."""
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/register")
def register_page():
    """Serve the registration page."""
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("register.html")


# ── AUTH API ──────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """Register a new user account."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    success, message, user_id = register_user(
        full_name=data.get("full_name", ""),
        email=data.get("email", ""),
        password=data.get("password", ""),
        country=data.get("country", ""),
        sector=data.get("sector", ""),
        org_type=data.get("org_type", ""),
        stage=data.get("stage", ""),
        registered_org=data.get("registered_org", False),
    )

    if success:
        # Auto-login after registration
        session["user_id"] = user_id
        user = get_user_by_id(user_id)
        return jsonify({"status": "success", "message": message, "user": user}), 201
    else:
        return jsonify({"error": message}), 400


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Authenticate and log in a user."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    success, message, user_data = authenticate_user(
        email=data.get("email", ""),
        password=data.get("password", ""),
    )

    if success:
        session["user_id"] = user_data["id"]
        return jsonify({"status": "success", "message": message, "user": user_data})
    else:
        return jsonify({"error": message}), 401


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    """Log out the current user."""
    session.clear()
    return jsonify({"status": "success", "message": "Logged out successfully."})


@app.route("/api/auth/me", methods=["GET"])
@login_required
def api_me():
    """Get the current authenticated user."""
    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "Session expired"}), 401
@app.route("/api/ai/status", methods=["GET"])
def api_ai_status():
    """Check if the AI strategist is active and report the active model."""
    return jsonify({
        "active": is_ai_active(),
        "model": active_model(),
        "label": provider_label(),
    })


@app.route("/api/ai/critique", methods=["POST"])
@login_required
def api_ai_critique():
    """Perform a strategic critique of a proposal."""
    data = request.get_json()
    proposal_text = data.get("proposal", "")
    grant_id = data.get("grant_id")

    if not proposal_text or not grant_id:
        return jsonify({"error": "Proposal and grant_id are required"}), 400

    grant = next((g for g in GRANTS if g["id"] == grant_id), None)
    guidelines = f"Funder: {grant['funder']}\nDescription: {grant['description']}\nSectors: {grant['sectors']}" if grant else "General grant guidelines."

    critique = analyze_strategy(proposal_text, guidelines)
    return jsonify({"critique": critique})


# ── MAIN APP (PROTECTED) ─────────────────────────────────────────
@app.route("/")
@login_required
def index():
    """Serve the main application page (requires login)."""
    user = get_user_by_id(session["user_id"])
    return render_template("index.html", user=user)


@app.route("/api/grants", methods=["GET"])
@login_required
def list_grants():
    """List all grants in the database."""
    grants_summary = []
    for g in GRANTS:
        grants_summary.append({
            "id": g["id"],
            "name": g["name"],
            "funder": g["funder"],
            "amount_usd": g["amount_usd"],
            "currency": g["currency"],
            "deadline": g["deadline"],
            "sectors": g["sectors"],
            "difficulty": g["difficulty"],
            "tags": g["tags"],
            "description": g["description"],
            "url": g["url"],
        })
    return jsonify({"grants": grants_summary, "total": len(grants_summary)})


@app.route("/api/onboard", methods=["POST"])
@login_required
def onboard():
    """Accept user profile and return a summary."""
    data = request.get_json()
    required = ["country", "sector", "org_type", "stage"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    profile = {
        "country": data["country"],
        "sector": data["sector"],
        "org_type": data["org_type"],
        "stage": data["stage"],
        "registered": data.get("registered", False),
        "funding_target": data.get("funding_target", ""),
    }

    return jsonify({
        "status": "success",
        "message": f"Welcome! Profile set for {profile['country']}. Let's find your grants.",
        "profile": profile,
    })


@app.route("/api/search", methods=["POST"])
@login_required
def search():
    """Search for matching grants based on user profile."""
    data = request.get_json()
    required = ["country", "sector", "org_type", "stage"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    results = search_grants(
        country=data["country"],
        sector=data["sector"],
        org_type=data["org_type"],
        stage=data["stage"],
        registered=data.get("registered", True),
    )

    # Separate into global and local
    global_grants = [r for r in results if "ALL_GLOBAL" in r.get("eligible_countries", [])
                     or "ALL_AFRICA" in r.get("eligible_countries", [])]
    local_grants = [r for r in results if data["country"] in r.get("eligible_countries", [])]

    return jsonify({
        "total": len(results),
        "global_grants": global_grants[:5],
        "local_grants": local_grants[:3],
        "all_results": results,
    })


@app.route("/api/compliance", methods=["POST"])
@login_required
def compliance():
    """Get compliance documents for a specific grant and country."""
    data = request.get_json()
    if not data.get("grant_id") or not data.get("country"):
        return jsonify({"error": "grant_id and country are required"}), 400

    result = get_compliance_docs(data["grant_id"], data["country"])
    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)


@app.route("/api/draft", methods=["POST"])
@login_required
def draft():
    """Generate a proposal draft."""
    data = request.get_json()
    required = ["grant_id", "project_name", "problem", "solution", "impact"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    result = draft_proposal(
        grant_id=data["grant_id"],
        project_name=data["project_name"],
        problem=data["problem"],
        solution=data["solution"],
        impact=data["impact"],
        country=data.get("country", "Nigeria"),
        sector=data.get("sector", "Tech"),
        beneficiaries=data.get("beneficiaries", ""),
        budget_usd=data.get("budget_usd", 0),
    )

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)


# ── STARTUP ───────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    init_vault()
    init_grants_db()
    print("\n" + "=" * 60)
    print("  🌍 GrantStar — African-Centric Global Grant Strategist")

    print("  🚀 Running at http://localhost:5000")
    print("  🔐 Authentication enabled")
    print("  📊 Dynamic Grants DB: Active")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
