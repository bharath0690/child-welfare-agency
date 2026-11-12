"""Production logging to Braintrust (architecture sections 2 and 7: audit and online evals).

Off unless BRAINTRUST_API_KEY is set and the `braintrust` package is installed. When off, every helper is a
no-op, so the app keeps running on the standard library alone. Logging must never break a request: every call
into the SDK is wrapped.

Each AI request (chat, panel open, workflow, family message) becomes one trace:
  root span  "POST /api/ai/chat"  input, output, persona, user, mode, tools, flags, latency
    llm span   one per model call, with token usage
    tool span  one per gateway call, with the policy decision and the fields returned (not the values)

Privacy rules (prototype; fictional data only):
  - A message that triggers safety escalation is replaced by "[redacted: safety disclosure]". It goes to a person,
    not to an analytics store.
  - BRAINTRUST_LOG_CONTENT=false logs metadata only (no message text or replies).
  - Real case data would need a vendor agreement, zero retention and data residency (architecture section 8, Q3).

Settings (environment variables):
  BRAINTRUST_API_KEY      required to turn logging on
  BRAINTRUST_PROJECT      optional, default "binti-ai-prototype"
  BRAINTRUST_LOG_CONTENT  optional, "false" logs metadata only
"""
import contextlib
import contextvars
import os
import time

PROJECT = os.environ.get("BRAINTRUST_PROJECT", "binti-ai-prototype")
REDACTED = "[redacted: safety disclosure]"
_logger = None
_failed = False
_trace = contextvars.ContextVar("binti_trace_id", default=None)


def current_trace_id():
    """Root span id of the request being handled, so drafts can be linked to the trace that made them."""
    return _trace.get()


def enabled():
    return bool(os.environ.get("BRAINTRUST_API_KEY", "").strip()) and not _failed


def log_content():
    return os.environ.get("BRAINTRUST_LOG_CONTENT", "true").strip().lower() not in ("false", "0", "no")


def _get_logger():
    global _logger, _failed
    if _logger is None and enabled():
        try:
            import braintrust
            _logger = braintrust.init_logger(project=PROJECT, async_flush=True)
        except Exception:  # noqa: BLE001 - missing package or bad key: run without logging
            _failed = True
    return _logger


def _clean(value):
    return value if log_content() else "[content not logged]"


@contextlib.contextmanager
def request_trace(name, persona, user, body, kind=None):
    """Root span for one API request. Yields a dict; set rec["output"] (and optionally rec["metadata"])."""
    rec = {"output": None, "metadata": {}, "trace_id": None}
    logger = _get_logger()
    if logger is None:
        yield rec
        return
    started = time.time()
    try:
        span = logger.start_span(name=name, type="task")
        rec["trace_id"] = span.id
    except Exception:  # noqa: BLE001
        yield rec
        return
    token = _trace.set(span.id)
    error = None
    try:
        with span:
            try:
                yield rec
            except Exception as e:  # noqa: BLE001 - record the failure, then re-raise it
                error = e
                raise
            finally:
                _finish(span, rec, persona, user, body, started, error, kind)
    finally:
        _trace.reset(token)
        flush()


def _finish(span, rec, persona, user, body, started, error, kind=None):
    try:
        out = rec.get("output") if isinstance(rec.get("output"), dict) else {"value": rec.get("output")}
        meta = (out or {}).get("meta") or {}
        inp = dict(body or {})
        ws = inp.pop("workspace", None)  # browser-held chat history; already in earlier traces
        ws = ws if isinstance(ws, dict) else {}
        if meta.get("escalated"):
            inp["message"] = REDACTED
        metadata = {"persona": persona, "user": user, "kind": kind, "mode": meta.get("mode"), "tools": meta.get("tools"),
                    "flags": meta.get("flags"), "escalated": bool(meta.get("escalated")), **rec.get("metadata", {})}
        if kind == "chat":
            # Keep the Input and Output columns readable: just the message and the reply. The rest goes to metadata.
            metadata.update({"object_type": inp.get("object_type"), "object_id": inp.get("object_id"),
                             "case_refs": meta.get("case_refs"), "emotions": meta.get("emotions")})
            # One conversation = one browser chat thread. Group or score by metadata.conversation_id in Braintrust.
            cid = ws.get("conversation_id")
            metadata["conversation_id"] = (cid[:64] if isinstance(cid, str) and cid else
                                           f"{persona}:{user}:{inp.get('object_type')}:{inp.get('object_id') or '-'}")
            thread = ws.get("thread") if isinstance(ws.get("thread"), list) else []
            metadata["turn_number"] = 1 + sum(1 for m in thread if isinstance(m, dict) and m.get("role") == "user")
            inp = {"message": inp.get("message")}
            out = {"reply": out.get("reply")} if not error else out
        scores = {}
        if "flags" in meta:  # online signals for the chat path (architecture section 7)
            scores["guardrail_clean"] = 0 if any(f.startswith(("decision_", "legal_", "reading_level")) for f in meta["flags"]) else 1
        span.log(input=_clean(inp), output=_clean(out if not error else {"error": str(error)}),
                 metadata={k: v for k, v in metadata.items() if v is not None},
                 tags=[t for t in (kind, persona) if t] or None,
                 metrics={"latency_ms": round((time.time() - started) * 1000)}, scores=scores or None)
    except Exception:  # noqa: BLE001
        pass


@contextlib.contextmanager
def child_span(name, span_type, input=None, metadata=None):
    """Nested span under the current request. Yields a function to log the output.

    Only inside a traced request: a tool call from a page load would otherwise start its own top-level trace."""
    if _get_logger() is None or current_trace_id() is None:
        yield lambda **kw: None
        return
    try:
        import braintrust
        span = braintrust.start_span(name=name, type=span_type)
    except Exception:  # noqa: BLE001
        yield lambda **kw: None
        return
    with span:
        try:
            span.log(input=_clean(input), metadata=metadata or {})
        except Exception:  # noqa: BLE001
            pass

        def log(**kw):
            try:
                if "output" in kw:
                    kw["output"] = _clean(kw["output"])
                span.log(**kw)
            except Exception:  # noqa: BLE001
                pass
        yield log


def feedback(trace_id, scores, comment=None, metadata=None):
    """Attach human signals to a logged trace: a viewer's rating, or whether the worker approved and how much they edited."""
    logger = _get_logger()
    if logger is None or not trace_id:
        return False
    try:
        logger.log_feedback(id=trace_id, scores={k: float(v) for k, v in scores.items()}, comment=comment, metadata=metadata or None)
        flush()
        return True
    except Exception:  # noqa: BLE001
        return False


def flush():
    if _logger is not None:
        try:
            _logger.flush()
        except Exception:  # noqa: BLE001
            pass
