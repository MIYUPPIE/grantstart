"""
GrantStar Engine — Core logic for grant search, compliance checking, and proposal drafting.
"""

from datetime import datetime
from grants_sqlite import get_all_grants, get_country_docs, get_all_impact_translations
from ai_strategist import generate_ai_proposal, is_ai_active, provider_label


def search_grants(country, sector, org_type, stage, registered=True):
    """
    Search and rank grants by relevance and ease of application for African applicants.
    """
    results = []
    all_grants = get_all_grants()

    for grant in all_grants:
        score = 0
        reasons = []
        warnings = []

        # ── Country Eligibility ──
        eligible = grant["eligible_countries"]
        excluded = grant["excluded_countries"]

        if country in excluded:
            continue  # Hard exclusion — skip entirely

        if "ALL_GLOBAL" in eligible or "ALL_AFRICA" in eligible or country in eligible:
            score += 30
            if country in eligible:
                reasons.append(f"Specifically targets {country}")
                score += 20
            elif "ALL_AFRICA" in eligible:
                reasons.append("Open to all African countries")
                score += 10
            else:
                reasons.append("Open globally (verify African eligibility)")
        else:
            continue  # Not eligible

        # ── Sector Match ──
        sector_lower = sector.lower()
        grant_sectors_lower = [s.lower() for s in grant["sectors"]]
        if sector_lower in grant_sectors_lower:
            score += 25
            reasons.append(f"Matches your sector: {sector}")
        else:
            # Partial match — some sectors are close
            score += 5
            warnings.append(f"Your sector '{sector}' is not a primary focus")

        # ── Organization Type Match ──
        if org_type in grant["org_types"]:
            score += 20
            reasons.append(f"Accepts {org_type} applications")
        else:
            score -= 10
            warnings.append(f"Typically for: {', '.join(grant['org_types'])}")

        # ── Stage Match ──
        if stage in grant["stages"]:
            score += 15
            reasons.append(f"Suitable for {stage} stage")
        else:
            score -= 5
            warnings.append(f"Designed for: {', '.join(grant['stages'])} stage(s)")

        # ── Registration Bonus ──
        if registered:
            score += 5
            reasons.append("Your registration status meets requirements")
        elif grant["difficulty"] > 5:
            warnings.append("Registration strongly recommended for this grant")

        # ── Deadline Check ──
        try:
            deadline = datetime.strptime(grant["deadline"], "%Y-%m-%d")
            days_left = (deadline - datetime.now()).days
            if days_left < 0:
                warnings.append("⚠️ Deadline has passed!")
                score -= 50
            elif days_left < 30:
                warnings.append(f"⏰ Only {days_left} days left — urgent!")
                score += 5  # Urgency bonus for awareness
            elif days_left < 90:
                reasons.append(f"Deadline in {days_left} days — good timeline")
            else:
                reasons.append(f"Comfortable timeline: {days_left} days remaining")
        except ValueError:
            pass

        # ── Ease Adjustment ──
        ease_score = 10 - grant["difficulty"]
        score += ease_score * 2

        results.append({
            **grant,
            "match_score": max(score, 0),
            "match_reasons": reasons,
            "warnings": warnings,
            "days_until_deadline": days_left if 'days_left' in dir() else None,
        })

    # Sort by match score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results


def get_compliance_docs(grant_id, country):
    """
    Get the specific documents needed for a grant application based on the user's country.
    """
    all_grants = get_all_grants()
    grant = next((g for g in all_grants if g["id"] == grant_id), None)
    if not grant:
        return {"error": f"Grant '{grant_id}' not found"}

    # Get grant-specific docs
    grant_docs = grant.get("required_docs", {})
    general_docs = grant_docs.get("ALL", [])
    country_docs = grant_docs.get(country, [])

    # Get country-specific knowledge
    country_knowledge = get_country_docs(country) or {}

    # Build the compliance response
    compliance = {
        "grant_name": grant["name"],
        "grant_funder": grant["funder"],
        "country": country,
        "general_documents": general_docs,
        "country_specific_documents": country_docs,
        "country_knowledge": {
            "tax_id_info": country_knowledge.get("tax_id", "Contact your local revenue authority"),
            "registration_info": country_knowledge.get("registration", "Contact your local business registry"),
            "compliance_info": country_knowledge.get("compliance", "Check local compliance requirements"),
            "additional_docs": country_knowledge.get("extras", []),
        },
        "tips": _get_compliance_tips(grant, country),
    }

    return compliance


def _get_compliance_tips(grant, country):
    """Generate context-aware compliance tips."""
    tips = []

    if grant["difficulty"] >= 7:
        tips.append("🔴 HIGH DIFFICULTY: Consider hiring a grant writer or consultant for this application.")

    if "SCUML Certificate" in grant.get("required_docs", {}).get(country, []):
        tips.append("💡 SCUML Tip: Apply at your nearest EFCC office. Processing takes 2-4 weeks.")

    if "BBBEE Certificate" in grant.get("required_docs", {}).get(country, []):
        tips.append("💡 BBBEE Tip: You need a verification agency. Level 1-3 gives you a significant advantage.")

    if "CR12" in grant.get("required_docs", {}).get(country, []):
        tips.append("💡 CR12 Tip: Download from eCitizen portal (Kenya). Ensure it's not older than 12 months.")

    if "SAM.gov Registration" in grant.get("required_docs", {}).get("ALL", []):
        tips.append("⚠️ SAM.gov Registration can take up to 10 business days. Start immediately!")

    if "EU PIC Number" in str(grant.get("required_docs", {})):
        tips.append("⚠️ EU PIC registration: Do this at the EU Funding & Tender Portal first.")

    if grant.get("currency") == "USD" and country == "Nigeria":
        tips.append("💰 Budget in USD but factor in NGN volatility. Use CBN official rate + 10% buffer.")
    elif grant.get("currency") == "EUR":
        tips.append("💰 Grant is in EUR. Ensure your organization can receive EUR payments.")

    if any(tag in grant.get("tags", []) for tag in ["consortium", "partnership-required"]):
        tips.append("🤝 This grant requires a consortium/partnership. Start networking NOW.")

    return tips


def draft_proposal(grant_id, project_name, problem, solution, impact,
                   country="Nigeria", sector="Tech", beneficiaries="", budget_usd=0):
    """
    Generate a Problem-Solution-Impact proposal draft tailored for international donors.
    """
    all_grants = get_all_grants()
    grant = next((g for g in all_grants if g["id"] == grant_id), None)
    if not grant:
        return {"error": f"Grant '{grant_id}' not found"}

    # Step 1: Try AI Strategist (any configured LLM)
    ai_result = None
    if is_ai_active():
        ai_result = generate_ai_proposal(
            grant_name=grant["name"],
            funder=grant["funder"],
            project_name=project_name,
            problem=problem,
            solution=solution,
            impact=impact,
            country=country,
            sector=sector,
            beneficiaries=beneficiaries
        )

    # Step 2: Build Proposal (AI or Rule-based)
    if ai_result:
        # Use high-quality AI generated sections
        proposal = {
            "grant_name": grant["name"],
            "project_title": project_name,
            "sections": ai_result, # Contains the PSI structure
            "sdg_alignment": ai_result.get("sdgs", []),
            "global_keywords": ai_result.get("global_terms", []),
            "strategy_mode": provider_label(),
            "word_count": 0
        }
    else:
        # Fallback to Rule-based templates
        impact_data = _translate_impact(sector, problem, solution)
        proposal = {
            "grant_name": grant["name"],
            "project_title": project_name,
            "sections": {
                "executive_summary": _generate_executive_summary(
                    project_name, problem, solution, impact, grant, country
                ),
                "problem_statement": _generate_problem_statement(
                    problem, country, sector, impact_data
                ),
                "proposed_solution": _generate_solution(
                    solution, project_name, impact_data
                ),
                "impact_and_outcomes": _generate_impact(
                    impact, beneficiaries, impact_data
                ),
                "sustainability_plan": _generate_sustainability(
                    project_name, sector, grant
                ),
                "budget_justification": _generate_budget_justification(
                    budget_usd, grant, country
                ),
            },
            "sdg_alignment": impact_data.get("sdgs", []),
            "global_keywords": impact_data.get("global_terms", []),
            "strategy_mode": "Rule-based Engine (Fallback)",
            "word_count": 0,
        }

    # Calculate total word count
    sections_dict = proposal["sections"]
    total_words = 0
    total_words = 0
    if isinstance(sections_dict, dict):
        for text in sections_dict.values():
            if isinstance(text, str):
                total_words += len(text.split())
            elif isinstance(text, dict):
                # Recurse for nested dicts (like sections)
                for sub_text in text.values():
                    if isinstance(sub_text, str):
                        total_words += len(sub_text.split())
    
    proposal["word_count"] = total_words

    return proposal


def _translate_impact(sector, problem, solution):
    """Translate local impact language into global donor-friendly terminology."""
    result = {"sdgs": [], "global_terms": []}
    
    # Search through impact translations
    text = f"{sector} {problem} {solution}".lower()
    translations = get_all_impact_translations()
    
    for keyword, data in translations.items():
        if keyword in text:
            # Avoid duplicate extensions
            for sdg in data.get("sdgs", []):
                if sdg not in result["sdgs"]:
                    result["sdgs"].append(sdg)
            for term in data.get("global_terms", []):
                if term not in result["global_terms"]:
                    result["global_terms"].append(term)

    # Default SDGs if none matched
    if not result["sdgs"]:
        result["sdgs"] = ["SDG 8: Decent Work & Economic Growth",
                          "SDG 9: Industry, Innovation & Infrastructure"]
        result["global_terms"] = ["Inclusive Economic Development",
                                  "Innovation-Driven Growth"]

    return result


def _generate_executive_summary(project_name, problem, solution, impact, grant, country):
    return (
        f"**{project_name}** is a transformative initiative based in {country} that addresses "
        f"a critical development challenge: {problem.lower()}. "
        f"\n\n"
        f"Our proposed intervention — {solution.lower()} — is designed to deliver measurable, "
        f"sustainable impact aligned with the strategic priorities of {grant['funder']}. "
        f"\n\n"
        f"Expected outcomes include: {impact}. "
        f"This project directly contributes to the global development agenda and positions "
        f"{country} as a leader in innovative, locally-driven solutions to shared challenges."
    )


def _generate_problem_statement(problem, country, sector, impact_data):
    sdg_refs = ", ".join(impact_data["sdgs"][:3]) if impact_data["sdgs"] else "multiple SDGs"
    return (
        f"## Problem Statement\n\n"
        f"In {country} and across Sub-Saharan Africa, communities face a persistent challenge: "
        f"**{problem}**. This issue undermines progress toward {sdg_refs} and "
        f"disproportionately affects vulnerable populations.\n\n"
        f"Current interventions have proven insufficient due to limited local capacity, "
        f"inadequate funding, and a disconnect between global frameworks and on-the-ground realities. "
        f"Without targeted action, this challenge will continue to widen inequality gaps and "
        f"slow the region's trajectory toward sustainable development.\n\n"
        f"Our research and community engagement confirm that the {sector.lower()} sector "
        f"holds transformative potential to address this gap — but only with the right support."
    )


def _generate_solution(solution, project_name, impact_data):
    terms = impact_data.get("global_terms", [])
    keywords = f" Our approach leverages {', '.join(terms[:2])}." if terms else ""
    return (
        f"## Proposed Solution\n\n"
        f"**{project_name}** will implement the following intervention: {solution}.{keywords}\n\n"
        f"### Key Components:\n"
        f"1. **Design & Development** — Build and validate the core solution with input from "
        f"target beneficiaries and local stakeholders.\n"
        f"2. **Pilot & Iteration** — Deploy a pilot programme in a target community, collect data, "
        f"and iterate based on user feedback.\n"
        f"3. **Scale & Sustainability** — Develop a scaling roadmap and sustainability model to "
        f"ensure long-term impact beyond the grant period.\n\n"
        f"This phased approach minimizes risk while maximizing learning and demonstrable outcomes."
    )


def _generate_impact(impact, beneficiaries, impact_data):
    sdgs = "\n".join(f"- {sdg}" for sdg in impact_data.get("sdgs", []))
    return (
        f"## Impact & Expected Outcomes\n\n"
        f"### Direct Impact\n"
        f"{impact}\n\n"
        f"### Target Beneficiaries\n"
        f"{beneficiaries if beneficiaries else 'Community members in the target region, with a focus on underserved populations.'}\n\n"
        f"### Monitoring & Evaluation\n"
        f"We will implement a rigorous M&E framework using both quantitative metrics "
        f"(reach, adoption, revenue impact) and qualitative indicators (user satisfaction, "
        f"behavioral change, community feedback).\n\n"
        f"### SDG Alignment\n"
        f"{sdgs}\n\n"
        f"All outcomes will be documented and shared with the funder through quarterly impact reports."
    )


def _generate_sustainability(project_name, sector, grant):
    return (
        f"## Sustainability Plan\n\n"
        f"**{project_name}** is designed for sustainability beyond the grant period through:\n\n"
        f"1. **Revenue Model** — A clear path to financial self-sufficiency through "
        f"service fees, partnerships, or product sales within the {sector.lower()} sector.\n"
        f"2. **Local Ownership** — Training and capacity building ensures the community "
        f"can operate and maintain the solution independently.\n"
        f"3. **Partnerships** — Strategic alliances with local government, industry players, "
        f"and civil society organizations provide ongoing support.\n"
        f"4. **Knowledge Sharing** — Lessons learned will be documented and shared as "
        f"open-source resources to amplify impact across the region."
    )


def _generate_budget_justification(budget_usd, grant, country):
    if budget_usd <= 0:
        budget_usd = grant["amount_usd"]["min"]

    return (
        f"## Budget Justification\n\n"
        f"**Requested Amount:** ${budget_usd:,.2f} USD\n\n"
        f"The budget has been carefully structured to maximize impact while maintaining "
        f"financial prudence. Key allocations include:\n\n"
        f"| Category | Allocation | Justification |\n"
        f"|----------|-----------|---------------|\n"
        f"| Personnel | 35% | Local team salaries at competitive {country} market rates |\n"
        f"| Technology & Equipment | 25% | Core solution development and deployment |\n"
        f"| Operations & Logistics | 20% | Field operations, travel, and community engagement |\n"
        f"| M&E and Reporting | 10% | Data collection, analysis, and impact documentation |\n"
        f"| Contingency | 10% | Currency fluctuation buffer and unforeseen costs |\n\n"
        f"All expenditures will be documented with receipts and reported in accordance "
        f"with {grant['funder']}'s financial guidelines."
    )
