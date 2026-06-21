
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider-agnostic LLM configuration.
#
# GrantStar talks to ANY OpenAI-compatible chat endpoint. Point these three
# env vars at whatever provider/model you want and it just works:
#
#   xAI (Grok)    LLM_BASE_URL=https://api.x.ai/v1                 LLM_MODEL=grok-4.3
#   OpenAI        LLM_BASE_URL=https://api.openai.com/v1           LLM_MODEL=gpt-4o
#   Groq          LLM_BASE_URL=https://api.groq.com/openai/v1      LLM_MODEL=llama-3.3-70b-versatile
#   OpenRouter    LLM_BASE_URL=https://openrouter.ai/api/v1        LLM_MODEL=anthropic/claude-3.5-sonnet
#   Together      LLM_BASE_URL=https://api.together.xyz/v1         LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
#   Gemini        LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/  LLM_MODEL=gemini-2.0-flash
#   Ollama (local)LLM_BASE_URL=http://localhost:11434/v1           LLM_MODEL=llama3.1   (any non-empty key)
#   LM Studio     LLM_BASE_URL=http://localhost:1234/v1            LLM_MODEL=<loaded-model>
#
# Legacy XAI_API_KEY is still honored so existing setups keep working.
# ---------------------------------------------------------------------------

LLM_API_KEY = (
    os.getenv("LLM_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("XAI_API_KEY")
)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.x.ai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "grok-4.3")

try:
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
except (TypeError, ValueError):
    LLM_TEMPERATURE = 0.7

# Common copy/paste placeholders that should be treated as "no key set".
_PLACEHOLDERS = {
    "",
    "your_xai_api_key_here",
    "your_api_key_here",
    "your_openai_api_key_here",
    "changeme",
    "sk-...",
}


def _build_client():
    """Construct an OpenAI-compatible client, or None when no real key is set."""
    if not LLM_API_KEY or LLM_API_KEY.strip().lower() in _PLACEHOLDERS:
        return None
    kwargs = {"api_key": LLM_API_KEY.strip()}
    if LLM_BASE_URL:
        kwargs["base_url"] = LLM_BASE_URL.strip()
    try:
        return OpenAI(**kwargs)
    except Exception as e:  # pragma: no cover - defensive, bad config only
        print(f"⚠️ LLM client init failed: {e}")
        return None


client = _build_client()


def is_ai_active():
    """Check if a usable LLM is configured."""
    return client is not None


def active_model():
    """The model id currently in use, or None when offline."""
    return LLM_MODEL if is_ai_active() else None


def provider_label():
    """Human label for the active strategist, including the model name."""
    if not is_ai_active():
        return "Rule-based (AI offline)"
    return f"AI Strategist · {LLM_MODEL} (Active)"


def _extract_json(text):
    """Parse a JSON object out of a model reply, tolerant of markdown fences
    and leading/trailing prose. Returns a dict or None."""
    if not text:
        return None
    candidate = text.strip()

    # Prefer a ```json ... ``` (or plain ``` ... ```) fenced block if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)

    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        pass

    # Last resort: grab the outermost {...} span and try that.
    brace = re.search(r"\{.*\}", candidate, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _chat(messages, json_mode=False, temperature=None):
    """One chat completion that works across providers/models.

    Sends the most capable request first, then degrades gracefully so models
    that don't support JSON response_format or a custom temperature still
    answer instead of erroring out. Returns the raw string content or None.
    """
    if client is None:
        return None

    temp = LLM_TEMPERATURE if temperature is None else temperature
    base = {"model": LLM_MODEL, "messages": messages}

    # Ordered from richest to most permissive. Each falls back to the next
    # on any provider rejection (unsupported response_format, fixed temp, etc.).
    attempts = []
    if json_mode:
        attempts.append({**base, "temperature": temp, "response_format": {"type": "json_object"}})
    attempts.append({**base, "temperature": temp})
    attempts.append({**base})

    last_err = None
    for params in attempts:
        try:
            completion = client.chat.completions.create(**params)
            return completion.choices[0].message.content
        except Exception as e:
            last_err = e
            continue

    print(f"⚠️ LLM error ({LLM_MODEL} @ {LLM_BASE_URL}): {last_err}")
    return None


def generate_ai_proposal(grant_name, funder, project_name, problem, solution, impact, country, sector, beneficiaries):
    """
    Generate a high-quality grant proposal using the configured LLM.
    Returns a dictionary of sections matching the internal proposal structure,
    or None on failure (caller falls back to rule-based templates).
    """
    if not is_ai_active():
        return None

    system_prompt = (
        "You are GrantStar, an elite African-centric Global Grant Strategist. "
        "Your mission is to help African startups and NGOs win global grants (USD/EUR/GBP). "
        "You specialize in the 'Problem-Solution-Impact' (PSI) framework and SDG alignment. "
        "Your tone is professional, visionary, and data-driven, yet deeply rooted in African context. "
        "Avoid generic AI fluff; use specific, impactful language. "
        "Always respond with a single valid JSON object and nothing else."
    )

    user_prompt = f"""
    Draft a comprehensive grant proposal for the following project:
    - Grant: {grant_name} (Funder: {funder})
    - Project: {project_name}
    - Location: {country}
    - Sector: {sector}
    - Problem: {problem}
    - Solution: {solution}
    - Impact: {impact}
    - Beneficiaries: {beneficiaries}

    Structure the response as a JSON object with these EXACT keys:
    - executive_summary
    - problem_statement
    - proposed_solution
    - impact_and_outcomes
    - sustainability_plan
    - budget_justification
    - sdgs (a list of aligned UN Sustainable Development Goals)
    - global_terms (a list of 5 high-impact buzzwords for international donors)

    For 'budget_justification', create a professional markdown table.
    Translate local impact into powerful global development terminology.
    """

    content = _chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        json_mode=True,
    )
    return _extract_json(content)


def analyze_strategy(proposal_text, grant_guidelines):
    """
    Perform a 'Red Team' critique of a proposal vs grant requirements.
    """
    if not is_ai_active():
        return "AI Strategist offline. Using standard compliance checks."

    prompt = f"""
    Act as a cynical Global Grant Reviewer.
    Critique this proposal draft against the provided grant guidelines.

    PROPOSAL:
    {proposal_text}

    GUIDELINES:
    {grant_guidelines}

    Provide:
    1. TOP 3 WEAKNESSES that might lead to rejection.
    2. KEY ENHANCEMENTS to make it 'un-rejectable'.
    3. STRATEGIC SCORE (1-10).
    """

    content = _chat(
        messages=[
            {"role": "system", "content": "You are a senior grant reviewer at the Bill & Melinda Gates Foundation."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )
    if content is None:
        return "Error analyzing strategy: the LLM did not return a response."
    return content
