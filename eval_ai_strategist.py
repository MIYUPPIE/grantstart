"""
Periodic eval for the LLM strategist — proves the proposal generator produces
usable, correctly-structured output against whatever real model is configured.

Paid (makes a live LLM call). Gated: if no key is configured it SKIPS with a
clear message instead of failing, so it never blocks the free gate suite.

Run before ship / nightly:
    python eval_ai_strategist.py

Point it at any provider via .env (LLM_BASE_URL / LLM_MODEL / LLM_API_KEY).
"""

import sys

from ai_strategist import (
    is_ai_active,
    active_model,
    generate_ai_proposal,
)

REQUIRED_KEYS = [
    "executive_summary",
    "problem_statement",
    "proposed_solution",
    "impact_and_outcomes",
    "sustainability_plan",
    "budget_justification",
    "sdgs",
    "global_terms",
]

PASS_THRESHOLD = 0.85  # fraction of required keys that must be present + non-empty


def run():
    if not is_ai_active():
        print("⏭️  SKIP: no LLM configured. Set LLM_API_KEY (or XAI_API_KEY) in .env.")
        return 0  # skip is not a failure

    print(f"🧪 Eval against model: {active_model()}")
    result = generate_ai_proposal(
        grant_name="Google.org AI for Social Good",
        funder="Google.org",
        project_name="AgriConnect",
        problem="Smallholder farmers in Northern Nigeria lack access to market pricing, "
                "causing 40% post-harvest losses.",
        solution="A mobile marketplace connecting farmers directly to buyers with "
                 "real-time pricing and logistics support.",
        impact="Connect 10,000 farmers, cut post-harvest losses by 30%, raise income 50%.",
        country="Nigeria",
        sector="Agriculture",
        beneficiaries="10,000 smallholder farmers",
    )

    if not isinstance(result, dict):
        print(f"❌ FAIL: generator returned {type(result).__name__}, expected dict.")
        return 1

    present = [k for k in REQUIRED_KEYS if str(result.get(k, "")).strip()]
    score = len(present) / len(REQUIRED_KEYS)
    missing = [k for k in REQUIRED_KEYS if k not in present]

    print(f"📊 Structure score: {score:.0%} ({len(present)}/{len(REQUIRED_KEYS)} keys)")
    if missing:
        print(f"   Missing/empty: {missing}")

    # Quality signals: SDGs should be a non-empty list, budget should look like a table.
    sdgs_ok = isinstance(result.get("sdgs"), list) and len(result["sdgs"]) > 0
    budget_ok = "|" in str(result.get("budget_justification", ""))
    print(f"   SDG list populated: {sdgs_ok}")
    print(f"   Budget markdown table: {budget_ok}")

    passed = score >= PASS_THRESHOLD and sdgs_ok
    print("✅ PASS" if passed else "❌ FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(run())
