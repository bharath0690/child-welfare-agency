"""LLM-judge scorers: rubric comes from AGENTS.md, grades are normalized, no key means no score."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evals"))
import judges  # noqa: E402
from binti import llm  # noqa: E402


class Block:
    def __init__(self, type, text=""):
        self.type, self.text = type, text


class FakeClaude:
    """Stands in for anthropic.Anthropic(): records the request, returns a canned response."""
    def __init__(self, text='{"grade": 5, "reason": "Warm and clear."}', stop="end_turn"):
        self.calls, self.text, self.stop = [], text, stop
        self.beta = self
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        r = mock.Mock()
        r.stop_reason, r.content = self.stop, [Block("thinking"), Block("text", self.text)]
        return r


@mock.patch.dict(os.environ, {"JUDGE_PROVIDER": "deepseek"})
class TestJudges(unittest.TestCase):
    def test_rubric_is_agents_md(self):
        section, tone = judges.rubric("kin")
        self.assertIn("Answer the question asked", section)
        self.assertIn("acknowledge it in one short, sincere sentence", section)
        self.assertTrue(tone.startswith("**Tone:** calm, gentle"))
        self.assertTrue(judges.rubric("caseworker")[1].startswith("**Tone:** a professional, efficient colleague"))

    def test_no_key_no_score(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(judges.provider())
            self.assertIsNone(judges.judge("helpfulness", "kin", "How long until I get paid?", "Day 6..."))

    def test_grade_normalized_and_prompt_carries_rubric(self):
        seen = {}

        def fake(messages, **kw):
            seen.update(system=messages[0]["content"], user=messages[1]["content"], kw=kw)
            return {"content": json.dumps({"grade": 4, "reason": "Answers early with a named contact."})}
        with mock.patch.object(llm, "chat", fake):
            r = judges.judge("politeness_empathy", "foster", "Isabella is melting down", "You don't have to handle this alone...",
                             context="Give the 24-hour behavior line.", api_key="k")
        self.assertEqual(r, {"grade": 4, "score": 0.75, "reason": "Answers early with a named contact."})
        self.assertIn("POLITENESS AND EMPATHY", seen["system"])
        self.assertIn("practical, steady colleague", seen["system"])
        self.assertIn("24-hour behavior line", seen["user"])
        self.assertEqual((seen["kw"]["temperature"], seen["kw"]["json_mode"], seen["kw"]["api_key"]), (0, True, "k"))

    def test_out_of_range_clamped_and_bad_output_ignored(self):
        with mock.patch.object(llm, "chat", lambda m, **k: {"content": '{"grade": 9}'}):
            self.assertEqual(judges.judge("helpfulness", "kin", "q", "a", api_key="k")["score"], 1.0)
        with mock.patch.object(llm, "chat", lambda m, **k: {"content": "not json"}):
            self.assertIsNone(judges.judge("helpfulness", "kin", "q", "a", api_key="k"))

        def down(m, **k):
            raise llm.LLMError("unreachable")
        with mock.patch.object(llm, "chat", down):
            self.assertIsNone(judges.judge("helpfulness", "kin", "q", "a", api_key="k"))

    def test_live_prompt_includes_section(self):
        from binti import agent
        core, _ = agent.system_prompt_parts("kin")
        self.assertIn("## Helpful and kind", core)


class TestClaudeJudge(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test", "JUDGE_PROVIDER": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        judges._claude = None

    def test_claude_preferred_when_key_set(self):
        self.assertEqual(judges.provider("deepseek-key"), "anthropic")
        self.assertEqual(judges.model_label(), "claude-opus-5-5")

    def test_request_shape_and_parse(self):
        judges._claude = fake = FakeClaude()
        r = judges.judge("helpfulness", "kin", "How long until I get paid?", "Day 6 since placement...")
        self.assertEqual(r, {"grade": 5, "score": 1.0, "reason": "Warm and clear."})
        kw = fake.calls[0]
        self.assertEqual(kw["model"], "claude-opus-5-5")
        self.assertEqual(kw["output_config"]["format"]["schema"], judges.GRADE_SCHEMA)
        self.assertEqual((kw["fallbacks"], kw["betas"]), ("default", ["server-side-fallback-2026-07-01"]))
        self.assertNotIn("temperature", kw)  # rejected by current Claude models
        self.assertIn("HELPFULNESS", kw["system"])
        self.assertIn("calm, gentle", kw["system"])

    def test_refusal_means_no_score(self):
        judges._claude = FakeClaude(stop="refusal")
        self.assertIsNone(judges.judge("helpfulness", "kin", "q", "a"))


class TestSavedScorers(unittest.TestCase):
    """evals/braintrust_scorers.py: the scorers pushed to the Braintrust library use the same rubric."""

    def test_two_llm_scorers_with_agents_md_rubric(self):
        import braintrust_scorers as bs
        names = [p.name for p in bs.project._publishable_prompts]
        self.assertEqual(names, ["Helpfulness", "Politeness and empathy"])
        msgs = bs.messages("politeness_empathy")
        self.assertIn("acknowledge it in one short, sincere sentence", msgs[0]["content"])
        for name in judges.PERSONA_NAME.values():
            self.assertIn(f"- {name}:", msgs[0]["content"])
        self.assertIn("{{metadata.persona}}", msgs[1]["content"])
        self.assertIn("{{output}}", msgs[1]["content"])
        self.assertEqual(bs.CHOICES["4"], 0.75)


if __name__ == "__main__":
    unittest.main()
