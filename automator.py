"""
GrantStar — Portal Automation Engine
Workflow definitions for grant portals: form field mappings, registration steps,
and auto-fill data preparation.
"""

from grants_db import GRANTS


# ── PORTAL WORKFLOW DEFINITIONS ───────────────────────────────────
# Each workflow describes how to automate interaction with a specific grant portal.
# Fields: portal URL, registration steps, application form fields with mappings.

PORTAL_WORKFLOWS = {
    "tef_2026": {
        "portal_name": "Tony Elumelu Foundation",
        "portal_url": "https://apply.tonyelumelufoundation.org/",
        "requires_account": True,
        "registration": {
            "url": "https://apply.tonyelumelufoundation.org/register",
            "steps": [
                {"action": "fill", "field": "First Name", "selector": "#first_name", "map_to": "first_name", "max_chars": 50},
                {"action": "fill", "field": "Last Name", "selector": "#last_name", "map_to": "last_name", "max_chars": 50},
                {"action": "fill", "field": "Email", "selector": "#email", "map_to": "email", "max_chars": 100},
                {"action": "fill", "field": "Password", "selector": "#password", "map_to": "portal_password"},
                {"action": "select", "field": "Country", "selector": "#country", "map_to": "country"},
                {"action": "select", "field": "Gender", "selector": "#gender", "map_to": "gender"},
                {"action": "fill", "field": "Phone", "selector": "#phone", "map_to": "phone", "max_chars": 20},
                {"action": "click", "field": "Terms & Conditions", "selector": "#terms_checkbox"},
                {"action": "submit", "field": "Submit", "selector": "#register_btn"},
            ],
        },
        "application": {
            "sections": [
                {
                    "name": "Personal Information",
                    "page": 1,
                    "fields": [
                        {"label": "Full Name", "selector": "#full_name", "map_to": "full_name", "max_chars": 100, "required": True},
                        {"label": "Email Address", "selector": "#email", "map_to": "email", "max_chars": 100, "required": True},
                        {"label": "Phone Number", "selector": "#phone", "map_to": "phone", "max_chars": 20, "required": True},
                        {"label": "Country", "selector": "#country", "map_to": "country", "type": "select", "required": True},
                        {"label": "City", "selector": "#city", "map_to": "city", "max_chars": 50},
                        {"label": "Date of Birth", "selector": "#dob", "map_to": "date_of_birth", "type": "date"},
                    ],
                },
                {
                    "name": "Business Information",
                    "page": 2,
                    "fields": [
                        {"label": "Business Name", "selector": "#business_name", "map_to": "org_name", "max_chars": 100, "required": True},
                        {"label": "Business Sector", "selector": "#sector", "map_to": "sector", "type": "select", "required": True},
                        {"label": "Year Founded", "selector": "#year_founded", "map_to": "org_year_founded", "max_chars": 4},
                        {"label": "Registration Number (CAC)", "selector": "#reg_number", "map_to": "org_registration_number", "max_chars": 20},
                        {"label": "Business Description", "selector": "#description", "map_to": "bio", "max_chars": 500, "required": True},
                        {"label": "Website", "selector": "#website", "map_to": "org_website", "max_chars": 200},
                    ],
                },
                {
                    "name": "Proposal",
                    "page": 3,
                    "fields": [
                        {"label": "Project Title", "selector": "#project_title", "map_to": "project_name", "max_chars": 100, "required": True, "source": "proposal"},
                        {"label": "Problem Statement", "selector": "#problem", "map_to": "problem", "max_chars": 1000, "required": True, "source": "proposal"},
                        {"label": "Proposed Solution", "selector": "#solution", "map_to": "solution", "max_chars": 1000, "required": True, "source": "proposal"},
                        {"label": "Expected Impact", "selector": "#impact", "map_to": "impact", "max_chars": 500, "required": True, "source": "proposal"},
                        {"label": "Target Beneficiaries", "selector": "#beneficiaries", "map_to": "beneficiaries", "max_chars": 300, "source": "proposal"},
                        {"label": "Budget (USD)", "selector": "#budget", "map_to": "budget_usd", "type": "number", "source": "proposal"},
                    ],
                },
            ],
        },
    },

    "google_org_ai": {
        "portal_name": "Google.org Impact Challenge",
        "portal_url": "https://impactchallenge.withgoogle.com/",
        "requires_account": True,
        "registration": {
            "url": "https://impactchallenge.withgoogle.com/signup",
            "steps": [
                {"action": "fill", "field": "Organization Name", "selector": "#org_name", "map_to": "org_name", "max_chars": 100},
                {"action": "fill", "field": "Contact Email", "selector": "#email", "map_to": "email", "max_chars": 100},
                {"action": "fill", "field": "Password", "selector": "#password", "map_to": "portal_password"},
                {"action": "fill", "field": "Contact Name", "selector": "#contact_name", "map_to": "full_name", "max_chars": 100},
                {"action": "select", "field": "Country", "selector": "#country", "map_to": "country"},
                {"action": "submit", "field": "Create Account", "selector": "#submit_btn"},
            ],
        },
        "application": {
            "sections": [
                {
                    "name": "Organization Details",
                    "page": 1,
                    "fields": [
                        {"label": "Organization Name", "selector": "#org_name", "map_to": "org_name", "max_chars": 150, "required": True},
                        {"label": "Organization Type", "selector": "#org_type", "map_to": "org_type", "type": "select", "required": True},
                        {"label": "Year Established", "selector": "#year_est", "map_to": "org_year_founded", "max_chars": 4},
                        {"label": "Website", "selector": "#website", "map_to": "org_website", "max_chars": 200},
                        {"label": "Country of Operation", "selector": "#country", "map_to": "country", "type": "select", "required": True},
                        {"label": "Organization Description", "selector": "#org_desc", "map_to": "bio", "max_chars": 1500, "required": True},
                        {"label": "Tax Registration Number", "selector": "#tax_id", "map_to": "tax_id", "max_chars": 30},
                    ],
                },
                {
                    "name": "Project Proposal",
                    "page": 2,
                    "fields": [
                        {"label": "Project Name", "selector": "#project_name", "map_to": "project_name", "max_chars": 150, "required": True, "source": "proposal"},
                        {"label": "How does this project use AI?", "selector": "#ai_usage", "map_to": "solution", "max_chars": 2000, "required": True, "source": "proposal"},
                        {"label": "What problem does this solve?", "selector": "#problem", "map_to": "problem", "max_chars": 2000, "required": True, "source": "proposal"},
                        {"label": "Expected Impact", "selector": "#impact", "map_to": "impact", "max_chars": 1500, "required": True, "source": "proposal"},
                        {"label": "Who benefits?", "selector": "#beneficiaries", "map_to": "beneficiaries", "max_chars": 500, "source": "proposal"},
                        {"label": "Requested Amount (USD)", "selector": "#amount", "map_to": "budget_usd", "type": "number", "source": "proposal"},
                    ],
                },
                {
                    "name": "Supporting Documents",
                    "page": 3,
                    "fields": [
                        {"label": "Registration Certificate", "selector": "#reg_cert", "map_to": "doc:registration", "type": "file"},
                        {"label": "Tax Exemption Certificate", "selector": "#tax_cert", "map_to": "doc:tax_clearance", "type": "file"},
                        {"label": "Financial Statements", "selector": "#financials", "map_to": "doc:financials", "type": "file"},
                    ],
                },
            ],
        },
    },

    "usaid_dca": {
        "portal_name": "USAID Development Innovation Ventures",
        "portal_url": "https://www.usaid.gov/div/apply",
        "requires_account": True,
        "registration": {
            "url": "https://www.sam.gov/SAM/pages/public/loginFAQ.jsf",
            "note": "USAID requires SAM.gov registration which is a multi-step government process (5-10 business days).",
            "steps": [
                {"action": "navigate", "field": "Go to SAM.gov", "url": "https://sam.gov", "note": "Create a SAM.gov account first"},
                {"action": "fill", "field": "Organization Legal Name", "selector": "#legal_name", "map_to": "org_name"},
                {"action": "fill", "field": "DUNS Number", "selector": "#duns", "map_to": "extra:duns_number", "note": "Apply at dnb.com if you don't have one"},
                {"action": "fill", "field": "Tax ID", "selector": "#tax_id", "map_to": "tax_id"},
                {"action": "fill", "field": "Physical Address", "selector": "#address", "map_to": "address"},
                {"action": "info", "field": "Processing Time", "note": "Registration takes 5-10 business days. Start immediately."},
            ],
        },
        "application": {
            "sections": [
                {
                    "name": "Applicant Information",
                    "page": 1,
                    "fields": [
                        {"label": "Organization Name", "selector": "#org_name", "map_to": "org_name", "max_chars": 200, "required": True},
                        {"label": "SAM.gov CAGE Code", "selector": "#cage", "map_to": "extra:cage_code", "max_chars": 10, "required": True},
                        {"label": "DUNS Number", "selector": "#duns", "map_to": "extra:duns_number", "max_chars": 13, "required": True},
                        {"label": "Lead Contact Name", "selector": "#contact", "map_to": "full_name", "max_chars": 100, "required": True},
                        {"label": "Lead Contact Email", "selector": "#email", "map_to": "email", "max_chars": 100, "required": True},
                        {"label": "Country of Registration", "selector": "#country", "map_to": "country", "type": "select", "required": True},
                    ],
                },
                {
                    "name": "Technical Proposal",
                    "page": 2,
                    "fields": [
                        {"label": "Concept Title", "selector": "#title", "map_to": "project_name", "max_chars": 150, "required": True, "source": "proposal"},
                        {"label": "Development Challenge", "selector": "#challenge", "map_to": "problem", "max_chars": 3000, "required": True, "source": "proposal"},
                        {"label": "Proposed Innovation", "selector": "#innovation", "map_to": "solution", "max_chars": 3000, "required": True, "source": "proposal"},
                        {"label": "Evidence of Impact", "selector": "#evidence", "map_to": "impact", "max_chars": 2000, "required": True, "source": "proposal"},
                        {"label": "Cost Effectiveness", "selector": "#cost", "map_to": "budget_usd", "type": "number", "source": "proposal"},
                    ],
                },
            ],
        },
    },

    # Generic fallback for grants without specific workflows
    "_generic": {
        "portal_name": "Generic Grant Portal",
        "portal_url": "",
        "requires_account": True,
        "registration": {
            "url": "",
            "steps": [
                {"action": "fill", "field": "Name", "map_to": "full_name"},
                {"action": "fill", "field": "Email", "map_to": "email"},
                {"action": "fill", "field": "Organization", "map_to": "org_name"},
                {"action": "fill", "field": "Password", "map_to": "portal_password"},
            ],
        },
        "application": {
            "sections": [
                {
                    "name": "Applicant Details",
                    "page": 1,
                    "fields": [
                        {"label": "Full Name / Contact Person", "map_to": "full_name", "max_chars": 100, "required": True},
                        {"label": "Email Address", "map_to": "email", "max_chars": 100, "required": True},
                        {"label": "Phone", "map_to": "phone", "max_chars": 20},
                        {"label": "Organization Name", "map_to": "org_name", "max_chars": 150, "required": True},
                        {"label": "Organization Type", "map_to": "org_type", "required": True},
                        {"label": "Country", "map_to": "country", "required": True},
                        {"label": "Tax ID", "map_to": "tax_id", "max_chars": 30},
                        {"label": "Website", "map_to": "org_website", "max_chars": 200},
                    ],
                },
                {
                    "name": "Project Proposal",
                    "page": 2,
                    "fields": [
                        {"label": "Project Title", "map_to": "project_name", "max_chars": 150, "required": True, "source": "proposal"},
                        {"label": "Problem Statement", "map_to": "problem", "max_chars": 2000, "required": True, "source": "proposal"},
                        {"label": "Proposed Solution", "map_to": "solution", "max_chars": 2000, "required": True, "source": "proposal"},
                        {"label": "Expected Impact", "map_to": "impact", "max_chars": 1500, "required": True, "source": "proposal"},
                        {"label": "Target Beneficiaries", "map_to": "beneficiaries", "max_chars": 500, "source": "proposal"},
                        {"label": "Budget (USD)", "map_to": "budget_usd", "type": "number", "source": "proposal"},
                    ],
                },
            ],
        },
    },
}


# ── AUTOMATION FUNCTIONS ──────────────────────────────────────────

def get_portal_workflow(grant_id):
    """Get the automation workflow for a specific grant portal."""
    base_workflow = PORTAL_WORKFLOWS.get(grant_id) or PORTAL_WORKFLOWS["_generic"]
    workflow = base_workflow.copy()

    # Attach grant info
    grant = next((g for g in GRANTS if g["id"] == grant_id), None)
    if grant and isinstance(workflow, dict):
        workflow["grant_name"] = grant["name"]
        workflow["grant_funder"] = grant["funder"]
        if not workflow.get("portal_url"):
            workflow["portal_url"] = grant.get("url", "")

    return workflow


def build_form_data(grant_id, profile, proposal=None):
    """
    Build the auto-fill data by mapping user profile and proposal data
    to the portal's form fields.
    
    Returns a list of sections, each with fields populated from user data.
    """
    workflow = get_portal_workflow(grant_id)
    app_config = workflow.get("application")
    sections = []
    if isinstance(app_config, dict):
        sections = app_config.get("sections", [])
    
    profile = profile or {}
    proposal = proposal or {}

    # Split full name into first/last
    full_name = str(profile.get("full_name", ""))
    name_parts = full_name.split(" ", 1)
    profile["first_name"] = name_parts[0] if name_parts else ""
    profile["last_name"] = name_parts[1] if len(name_parts) > 1 else ""

    filled_sections = []

    for section in sections:
        if not isinstance(section, dict):
            continue
            
        filled_fields = []
        fields_list = section.get("fields", [])
        for field in fields_list:
            if not isinstance(field, dict):
                continue
                
            map_key = str(field.get("map_to", ""))
            source = str(field.get("source", "profile"))
            max_chars = int(field.get("max_chars", 0))

            # Determine value source
            if source == "proposal":
                value = str(proposal.get(map_key, ""))
            elif map_key.startswith("doc:"):
                doc_key = map_key.replace("doc:", "")
                doc_paths = profile.get("document_paths", {})
                if isinstance(doc_paths, dict):
                    value = str(doc_paths.get(doc_key, "[Upload Required]"))
                else:
                    value = "[Upload Required]"
            elif map_key.startswith("extra:"):
                extra_key = map_key.replace("extra:", "")
                value = str(profile.get(extra_key, ""))
            else:
                value = str(profile.get(map_key, ""))

            # Truncate to max chars if needed
            if max_chars and len(value) > max_chars:
                value = value[:max_chars - 3] + "..."
                truncated = True
            else:
                truncated = False

            filled_fields.append({
                "label": str(field.get("label", "")),
                "value": value,
                "max_chars": max_chars,
                "char_count": len(value),
                "truncated": truncated,
                "required": bool(field.get("required", False)),
                "type": str(field.get("type", "text")),
                "filled": bool(value and value != "[Upload Required]"),
                "selector": str(field.get("selector", "")),
                "note": str(field.get("note", "")),
            })

        filled_sections.append({
            "name": str(section.get("name", "Untitled Section")),
            "page": int(section.get("page", 1)),
            "fields": filled_fields,
            "completion": _section_completion(filled_fields),
        })

    return {
        "grant_id": grant_id,
        "portal_name": str(workflow.get("portal_name", "")),
        "portal_url": str(workflow.get("portal_url", "")),
        "grant_name": str(workflow.get("grant_name", "")),
        "sections": filled_sections,
        "overall_completion": _overall_completion(filled_sections),
        "requires_account": bool(workflow.get("requires_account", False)),
    }


def get_registration_steps(grant_id, profile):
    """Get portal registration steps with auto-filled data."""
    workflow = get_portal_workflow(grant_id)
    reg = workflow.get("registration")
    if not isinstance(reg, dict):
        return {"error": "No registration workflow defined for this portal."}

    # Split full name
    profile = profile or {}
    full_name = str(profile.get("full_name", ""))
    name_parts = full_name.split(" ", 1)
    profile["first_name"] = name_parts[0] if name_parts else ""
    profile["last_name"] = name_parts[1] if len(name_parts) > 1 else ""

    filled_steps = []
    steps_list = reg.get("steps", [])
    if isinstance(steps_list, list):
        for step in steps_list:
            if not isinstance(step, dict):
                continue
            map_key = str(step.get("map_to", ""))
            value = profile.get(map_key, "") if map_key else ""

            filled_steps.append({
                "action": str(step.get("action", "fill")),
                "field": str(step.get("field", "")),
                "value": str(value),
                "selector": str(step.get("selector", "")),
                "note": str(step.get("note", "")),
                "url": str(step.get("url", "")),
                "filled": bool(value),
            })

    return {
        "portal_name": str(workflow.get("portal_name", "")),
        "portal_url": str(reg.get("url") or workflow.get("portal_url", "")),
        "note": str(reg.get("note", "")),
        "steps": filled_steps,
        "grant_name": str(workflow.get("grant_name", "")),
    }


def _section_completion(fields):
    """Calculate completion percentage for a section."""
    if not fields:
        return 0
    required = [f for f in fields if isinstance(f, dict) and f.get("required")]
    if not required:
        filled = [f for f in fields if isinstance(f, dict) and f.get("filled")]
        return int((len(filled) / max(len(fields), 1)) * 100)
    filled_required = [f for f in required if f.get("filled")]
    return int((len(filled_required) / len(required)) * 100)


def _overall_completion(sections):
    """Calculate overall form completion."""
    if not sections:
        return 0
    total = sum(s.get("completion", 0) for s in sections if isinstance(s, dict))
    return int(total / len(sections))
