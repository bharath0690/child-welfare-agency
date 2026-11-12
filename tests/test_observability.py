"""Braintrust logging: off without a key, never breaks a request, links drafts to their trace."""
import io
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from binti import api, db, observability as obs  # noqa: E402


class FakeSpan:
    def __init__(self, store, name, kind, parent=None):
        self.store, self.id, self.name, self.kind, self.parent = store, f"span-{len(store.spans)}", name, kind, parent
        self.logs = []
        store.spans.append(self)

    def log(self, **kw):
        self.logs.append(kw)

    def __enter__(self):
        self.store.stack.append(self)
        return self

    def __exit__(self, *a):
        self.store.stack.pop()


class FakeLogger:
    def __init__(self):
        self.spans, self.stack, self.feedback = [], [], []

    def start_span(self, name, type):
        return FakeSpan(self, name, type)

    def log_feedback(self, **kw):
        self.feedback.append(kw)

    def flush(self):
        pass


class FakeBraintrust:
    def __init__(self, logger):
        self.logger = logger

    def start_span(self, name, type):
        return FakeSpan(self.logger, name, type, parent=self.logger.stack[-1] if self.logger.stack else None)


def call(method, path, body=None, persona="caseworker", user="cw1"):
    raw = json.dumps(body or {}).encode()
    env = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "", "CONTENT_LENGTH": str(len(raw)),
           "wsgi.input": io.BytesIO(raw), "HTTP_X_PERSONA": persona, "HTTP_X_USER": user}
    out = {}
    body = b"".join(api.app(env, lambda s, h: out.update(status=s)))
    return out["status"], json.loads(body)


class TestObservability(unittest.TestCase):
    def setUp(self):
        db.reset_for_tests(":memory:")
        os.environ.pop("DEEPSEEK_API_KEY", None)

    def tearDown(self):
        os.environ.pop("BRAINTRUST_API_KEY", None)
        obs._logger, obs._failed = None, False
        sys.modules.pop("braintrust", None) if isinstance(sys.modules.get("braintrust"), FakeBraintrust) else None

    def test_off_without_key(self):
        os.environ.pop("BRAINTRUST_API_KEY", None)
        status, out = call("POST", "/api/ai/chat", {"object_type": "case", "object_id": "case-01", "message": "When is court?"})
        self.assertTrue(status.startswith("200"))
        self.assertNotIn("trace_id", out)
        self.assertEqual(call("POST", "/api/feedback", {"trace_id": "x", "rating": "ok"})[1], {"logged": False})

    def _fake(self):
        os.environ["BRAINTRUST_API_KEY"] = "test"
        fake = FakeLogger()
        obs._logger = fake
        sys.modules["braintrust"] = FakeBraintrust(fake)
        return fake

    def test_chat_trace_has_tool_spans(self):
        fake = self._fake()
        status, out = call("POST", "/api/ai/chat", {"object_type": "case", "object_id": "case-01", "message": "When is court?"})
        root = fake.spans[0]
        self.assertEqual(out["trace_id"], root.id)
        self.assertEqual(root.logs[-1]["metadata"]["persona"], "caseworker")
        tools = [s for s in fake.spans if s.kind == "tool"]
        self.assertTrue(tools and all(s.parent is root for s in tools))
        # tool spans carry field names, never the values
        self.assertNotIn("Review hearing", json.dumps([s.logs for s in tools]))

    def test_chat_trace_is_readable_and_tagged(self):
        fake = self._fake()
        call("POST", "/api/ai/chat", {"object_type": "case", "object_id": "case-01", "message": "When is court?", "workspace": {"x": 1}})
        root = fake.spans[0]
        log = root.logs[-1]
        self.assertEqual(root.name, "chat · caseworker")
        self.assertEqual(log["input"], {"message": "When is court?"})
        self.assertEqual(list(log["output"]), ["reply"])
        self.assertEqual(log["tags"], ["chat", "caseworker"])
        self.assertEqual(log["metadata"]["object_id"], "case-01")

    def test_chat_turns_share_a_conversation_id(self):
        fake = self._fake()
        ws = {"conversation_id": "c-abc", "thread": []}
        call("POST", "/api/ai/chat", {"object_type": "application", "message": "What's left?", "workspace": ws},
             persona="applicant", user="ap1")
        ws["thread"] = [{"role": "user", "content": "What's left?"}, {"role": "assistant", "content": "..."}]
        call("POST", "/api/ai/chat", {"object_type": "application", "message": "Who do I call?", "workspace": ws},
             persona="applicant", user="ap1")
        roots = [s for s in fake.spans if s.parent is None]
        metas = [r.logs[-1]["metadata"] for r in roots]
        self.assertEqual([m["conversation_id"] for m in metas], ["c-abc", "c-abc"])
        self.assertEqual([m["turn_number"] for m in metas], [1, 2])

    def test_page_loads_and_panel_open_make_no_traces(self):
        fake = self._fake()
        call("GET", "/api/application", persona="applicant", user="ap1")  # calls several gateway tools
        call("POST", "/api/ai/open", {"object_type": "case", "object_id": "case-01"})
        self.assertEqual(fake.spans, [])

    def test_safety_disclosure_is_redacted(self):
        fake = self._fake()
        msg = "She told me her mom's boyfriend hits her"
        call("POST", "/api/ai/chat", {"object_type": "case", "message": msg}, persona="kin", user="kin1")
        self.assertNotIn("boyfriend", json.dumps(fake.spans[0].logs, default=str))
        self.assertEqual(fake.spans[0].logs[-1]["input"]["message"], obs.REDACTED)

    def test_draft_linked_to_trace_and_approval_is_feedback(self):
        fake = self._fake()
        hearing = db.row("SELECT on_date FROM court_dates WHERE case_id='case-01' AND on_date>=date('now') ORDER BY on_date")["on_date"]
        _, out = call("POST", "/api/workflows/court-report", {"case_id": "case-01", "hearing_date": hearing})
        pid = out["proposal"]["proposal_id"]
        self.assertEqual(db.row("SELECT trace_id FROM proposals WHERE id=?", (pid,))["trace_id"], out["trace_id"])
        call("POST", "/api/feedback", {"proposal_id": pid, "rating": "edit"})
        call("POST", f"/api/proposals/{pid}", {"op": "approve", "edited": {"body": out["body"] + "\nRecommendation: written by the worker."}})
        scores = {k: v for f in fake.feedback if f["id"] == out["trace_id"] for k, v in f["scores"].items()}
        self.assertEqual(scores["viewer_rating"], 0.5)
        self.assertEqual(scores["approved"], 1.0)
        self.assertTrue(0.9 < scores["edit_similarity"] < 1.0)

    def test_feedback_scoped_to_own_drafts(self):
        self._fake()
        pid = db.row("SELECT id FROM proposals WHERE object_type='case' AND object_id NOT IN ('case-01','case-02','case-03','case-04') LIMIT 1")
        if pid:
            status, _ = call("POST", "/api/feedback", {"proposal_id": pid["id"], "rating": "ok"})
            self.assertFalse(status.startswith("200"))

    def test_logging_failure_never_breaks_request(self):
        os.environ["BRAINTRUST_API_KEY"] = "test"

        class Broken(FakeLogger):
            def start_span(self, *a, **k):
                raise RuntimeError("network down")
        obs._logger = Broken()
        status, out = call("POST", "/api/ai/chat", {"object_type": "case", "object_id": "case-01", "message": "When is court?"})
        self.assertTrue(status.startswith("200"))
        self.assertIn("reply", out)


if __name__ == "__main__":
    unittest.main()
