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


class TestJudges(unittest.TestCase):
    def test_rubric_is_agents_md(self):
        section, tone = judges.rubric("kin")
        self.assertIn("Answer the question asked", section)
        self.assertIn("acknowledge it in one short, sincere sentence", section)
        self.assertTrue(tone.startswith("**Tone:** calm, gentle"))
        self.assertTrue(judges.rubric("caseworker")[1].startswith("**Tone:** a professional, efficient colleague"))

    def test_no_key_no_score(self):
        with mock.patch.dict(os.environ, {}, clear=True):
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


if __name__ == "__main__":
    unittest.main()
