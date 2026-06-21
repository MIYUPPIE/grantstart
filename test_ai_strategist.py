"""
Gate tests for the provider-agnostic LLM layer (ai_strategist).

Deterministic, offline, free, <2s. No network calls. Validates:
  - any OpenAI-compatible provider/model is selected purely from env vars
  - missing / placeholder keys resolve to "offline"
  - JSON replies are parsed robustly across model output styles
  - _chat() degrades gracefully when a model rejects response_format / temperature

Run:  python -m unittest test_ai_strategist -v
"""

import importlib
import os
import unittest


def _reload(env):
    """Reload ai_strategist with a clean, controlled environment.

    dotenv is neutralized so the real .env can't leak keys into these
    deterministic, offline tests.
    """
    import dotenv
    keys = ["LLM_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY",
            "LLM_BASE_URL", "LLM_MODEL", "LLM_TEMPERATURE"]
    saved = {k: os.environ.get(k) for k in keys}
    orig_load = dotenv.load_dotenv
    try:
        dotenv.load_dotenv = lambda *a, **k: False
        for k in keys:
            os.environ.pop(k, None)
        os.environ.update(env)
        import ai_strategist
        return importlib.reload(ai_strategist)
    finally:
        dotenv.load_dotenv = orig_load
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestJsonExtraction(unittest.TestCase):
    def setUp(self):
        self.mod = _reload({})  # offline is fine; _extract_json is pure

    def test_plain_json(self):
        self.assertEqual(self.mod._extract_json('{"a": 1}'), {"a": 1})

    def test_fenced_json_block(self):
        text = 'Sure!\n```json\n{"a": 1, "b": [2, 3]}\n```\nDone.'
        self.assertEqual(self.mod._extract_json(text), {"a": 1, "b": [2, 3]})

    def test_fenced_plain_block(self):
        text = '```\n{"x": "y"}\n```'
        self.assertEqual(self.mod._extract_json(text), {"x": "y"})

    def test_prose_wrapped_json(self):
        text = 'Here is your proposal: {"executive_summary": "hello"} thanks'
        self.assertEqual(self.mod._extract_json(text),
                         {"executive_summary": "hello"})

    def test_invalid_returns_none(self):
        self.assertIsNone(self.mod._extract_json("not json at all"))

    def test_empty_returns_none(self):
        self.assertIsNone(self.mod._extract_json(""))
        self.assertIsNone(self.mod._extract_json(None))


class TestProviderConfig(unittest.TestCase):
    def test_offline_when_no_key(self):
        mod = _reload({})
        self.assertFalse(mod.is_ai_active())
        self.assertIsNone(mod.active_model())
        self.assertIn("offline", mod.provider_label().lower())

    def test_offline_on_placeholder_key(self):
        mod = _reload({"LLM_API_KEY": "your_api_key_here"})
        self.assertFalse(mod.is_ai_active())

    def test_any_provider_from_env(self):
        mod = _reload({
            "LLM_API_KEY": "sk-real-looking-key",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_MODEL": "anthropic/claude-3.5-sonnet",
        })
        self.assertTrue(mod.is_ai_active())
        self.assertEqual(mod.active_model(), "anthropic/claude-3.5-sonnet")
        self.assertEqual(mod.LLM_BASE_URL, "https://openrouter.ai/api/v1")
        self.assertIn("anthropic/claude-3.5-sonnet", mod.provider_label())

    def test_legacy_xai_key_still_works(self):
        mod = _reload({"XAI_API_KEY": "xai-legacy-key"})
        self.assertTrue(mod.is_ai_active())
        # Default model when only legacy key is set.
        self.assertEqual(mod.active_model(), "grok-4.3")

    def test_default_base_url_and_model(self):
        mod = _reload({"LLM_API_KEY": "sk-x"})
        self.assertEqual(mod.LLM_BASE_URL, "https://api.x.ai/v1")
        self.assertEqual(mod.LLM_MODEL, "grok-4.3")

    def test_bad_temperature_falls_back(self):
        mod = _reload({"LLM_API_KEY": "sk-x", "LLM_TEMPERATURE": "not-a-number"})
        self.assertEqual(mod.LLM_TEMPERATURE, 0.7)


class _Msg:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()


class _Resp:
    def __init__(self, content):
        self.choices = [_Msg(content)]


class _PickyClient:
    """Fake client that rejects response_format and custom temperature,
    mimicking models that don't support structured output / sampling."""
    def __init__(self):
        self.calls = []
        self.chat = type("C", (), {"completions": self})()

    def create(self, **params):
        self.calls.append(params)
        if "response_format" in params:
            raise Exception("response_format not supported by this model")
        if params.get("temperature", 0) not in (0, None):
            raise Exception("temperature is fixed for this model")
        return _Resp('{"ok": true}')


class TestChatGracefulDegradation(unittest.TestCase):
    def test_chat_degrades_to_supported_request(self):
        mod = _reload({"LLM_API_KEY": "sk-x"})
        mod.client = _PickyClient()
        out = mod._chat(
            messages=[{"role": "user", "content": "hi"}],
            json_mode=True,
            temperature=0.9,
        )
        self.assertEqual(out, '{"ok": true}')
        # It tried the rich request first, then degraded to a bare one.
        self.assertGreaterEqual(len(mod.client.calls), 2)
        self.assertIn("response_format", mod.client.calls[0])
        self.assertNotIn("response_format", mod.client.calls[-1])

    def test_chat_returns_none_when_offline(self):
        mod = _reload({})
        self.assertIsNone(mod._chat(messages=[{"role": "user", "content": "x"}]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
