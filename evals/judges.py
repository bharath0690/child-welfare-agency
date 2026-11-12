"""LLM-judge scorers: helpfulness, and politeness and empathy.

The rubric is not written here. It is read from AGENTS.md ("## Helpful and kind" plus the persona's **Tone** line),
the same text the agent gets in its system prompt, so what the agent is told and how it is graded can't drift apart.

Each judge returns a 1 to 5 grade and a one-sentence reason. Braintrust shows it as a 0 to 1 score
((grade - 1) / 4), so 5 is 100% and 3 is 50%.

Judge model (first match wins):
  ANTHROPIC_API_KEY set   Claude, through the official `anthropic` SDK (pip install -r evals/requirements.txt).
                          Model JUDGE_MODEL, default claude-opus-5-5. Structured output guarantees the JSON shape.
  JUDGE_API_KEY or        DeepSeek, through cwa/llm.py (the app's own model gateway).
  DEEPSEEK_API_KEY
JUDGE_PROVIDER=anthropic|deepseek forces one. Without a key the judges return None and Braintrust leaves the score blank.
Use: evals/braintrust_eval.py.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from cwa import llm  # noqa: E402

PERSONA_NAME = {"caseworker": "Caseworker", "applicant": "Prospective parent", "kin": "Kin caregiver", "foster": "Licensed foster parent"}

METRICS = {
    "helpfulness": (
        "HELPFULNESS: Did the reply answer what was asked, early, using the person's own facts, with a next step they can take "
        "today and a named person when one is needed? Is it no longer than the question needs? A clear 'that isn't in the record, "
        "ask X' is helpful. Declining a decision the AI must not make (placement, custody, eligibility, approval, predicted dates) "
        "is helpful when it says who decides and what the AI can do instead; do not mark it down for declining.\n"
        "5 = fully answers with a clear next step. 4 = answers, minor gaps or padding. 3 = partly answers or buries the answer. "
        "2 = mostly generic or off target. 1 = does not answer or misleads."),
    "politeness_empathy": (
        "POLITENESS AND EMPATHY: Is the reply courteous, respectful and in the tone this persona needs? If the person shows "
        "distress, does it acknowledge that in one short, sincere sentence before the facts (and skip it when they are calm)? "
        "Mark down stock phrases, over-apologizing, minimizing ('don't worry'), lecturing, blame, unexplained jargon for families, "
        "and emotional padding that wastes a caseworker's time.\n"
        "5 = right tone, well judged. 4 = good, small slip. 3 = neutral or a bit off for this persona. "
        "2 = cold, preachy or padded. 1 = disrespectful, blaming or dismissive."),
}


def _agents_md():
    return (ROOT / "AGENTS.md").read_text()


def rubric(persona):
    """The 'Helpful and kind' section plus this persona's Tone line, straight from AGENTS.md."""
    text = _agents_md()
    m = re.search(r"^## Helpful and kind\n(.*?)(?=^## )", text, re.S | re.M)
    section = m.group(1).strip() if m else ""
    tone = ""
    name = PERSONA_NAME.get(persona)
    if name:
        p = re.search(r"^## Persona: " + re.escape(name) + r"\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        t = re.search(r"^\*\*Tone:\*\*.*$", p.group(1), re.M) if p else None
        tone = t.group(0) if t else ""
    return section, tone


GRADE_SCHEMA = {
    "type": "object",
    "properties": {"grade": {"type": "integer", "enum": [1, 2, 3, 4, 5]}, "reason": {"type": "string"}},
    "required": ["grade", "reason"],
    "additionalProperties": False,
}


def _key():
    return (os.environ.get("JUDGE_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or "").strip()


def provider(deepseek_key=None):
    """'anthropic', 'deepseek' or None (no judge available)."""
    forced = os.environ.get("JUDGE_PROVIDER", "").strip().lower()
    has_claude = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    has_deepseek = bool(deepseek_key or _key())
    if forced == "anthropic":
        return "anthropic" if has_claude else None
    if forced == "deepseek":
        return "deepseek" if has_deepseek else None
    return "anthropic" if has_claude else "deepseek" if has_deepseek else None


def model_label(deepseek_key=None):
    return {"anthropic": os.environ.get("JUDGE_MODEL", "claude-opus-5-5"), "deepseek": llm.model_name()}.get(provider(deepseek_key))


_claude = None


def _ask_claude(system, user):
    """Grade with Claude. Returns the parsed {"grade", "reason"} dict, or None on an API error or a refusal."""
    global _claude
    import anthropic
    if _claude is None:
        _claude = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    try:
        response = _claude.beta.messages.create(
            model=os.environ.get("JUDGE_MODEL", "claude-opus-5-5"),
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": GRADE_SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # a policy decline is re-run on a fallback model inside the same call
        )
    except (anthropic.APIStatusError, anthropic.APIConnectionError):
        return None
    if response.stop_reason in ("refusal", "max_tokens"):
        return None
    text = next((b.text for b in response.content if b.type == "text"), None)
    return json.loads(text) if text else None


def _ask_deepseek(system, user, key):
    msg = llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}],
                   temperature=0, max_tokens=200, json_mode=True, api_key=key)
    return json.loads(msg.get("content") or "{}")


def judge(metric, persona, question, reply, context=None, api_key=None):
    """Return {"grade": 1-5, "score": 0-1, "reason": str}, or None without a key or on a model failure."""
    which = provider(api_key)
    if which is None or not reply:
        return None
    section, tone = rubric(persona)
    who = PERSONA_NAME.get(persona, persona)
    system = ("You grade replies from Agency AI, an assistant in a child welfare platform. Be strict and consistent. "
              "Grade only the metric you are asked about, not accuracy or safety, which are checked elsewhere.\n\n"
              f"The standard the assistant was given:\n{section}\n\nTone for this person ({who}):\n{tone}\n\n"
              f"{METRICS[metric]}\n\nReply with JSON only: {{\"grade\": 1-5, \"reason\": \"one sentence\"}}")
    user = (f"Person: {who}\nTheir message:\n{question}\n\n"
            + (f"What a good reply must do here (from the eval case):\n{context}\n\n" if context else "")
            + f"Agency AI's reply:\n{reply}")
    try:
        out = _ask_claude(system, user) if which == "anthropic" else _ask_deepseek(system, user, api_key or _key())
        grade = int(out["grade"])
    except (llm.LLMError, ValueError, KeyError, TypeError):
        return None
    grade = min(5, max(1, grade))
    return {"grade": grade, "score": (grade - 1) / 4, "reason": str(out.get("reason", ""))[:300]}
