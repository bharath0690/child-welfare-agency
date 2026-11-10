"""LLM-judge scorers: helpfulness, and politeness and empathy.

The rubric is not written here. It is read from AGENTS.md ("## Helpful and kind" plus the persona's **Tone** line),
the same text the agent gets in its system prompt, so what the agent is told and how it is graded can't drift apart.

Each judge returns a 1 to 5 grade and a one-sentence reason. Braintrust shows it as a 0 to 1 score
((grade - 1) / 4), so 5 is 100% and 3 is 50%.

The judge calls the model through binti/llm.py, the same model gateway the app uses. Key: JUDGE_API_KEY, else
DEEPSEEK_API_KEY. Without a key the judges return None and Braintrust leaves the score blank.
Use: evals/braintrust_eval.py.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from binti import llm  # noqa: E402

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


def _key():
    return (os.environ.get("JUDGE_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or "").strip()


def judge(metric, persona, question, reply, context=None, api_key=None):
    """Return {"grade": 1-5, "score": 0-1, "reason": str}, or None without a key or on a model failure."""
    key = api_key or _key()
    if not key or not reply:
        return None
    section, tone = rubric(persona)
    who = PERSONA_NAME.get(persona, persona)
    system = ("You grade replies from Binti AI, an assistant in a child welfare platform. Be strict and consistent. "
              "Grade only the metric you are asked about, not accuracy or safety, which are checked elsewhere.\n\n"
              f"The standard the assistant was given:\n{section}\n\nTone for this person ({who}):\n{tone}\n\n"
              f"{METRICS[metric]}\n\nReply with JSON only: {{\"grade\": 1-5, \"reason\": \"one sentence\"}}")
    user = (f"Person: {who}\nTheir message:\n{question}\n\n"
            + (f"What a good reply must do here (from the eval case):\n{context}\n\n" if context else "")
            + f"Binti AI's reply:\n{reply}")
    try:
        msg = llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}],
                       temperature=0, max_tokens=200, json_mode=True, api_key=key)
        out = json.loads(msg.get("content") or "{}")
        grade = int(out["grade"])
    except (llm.LLMError, ValueError, KeyError, TypeError):
        return None
    grade = min(5, max(1, grade))
    return {"grade": grade, "score": (grade - 1) / 4, "reason": str(out.get("reason", ""))[:300]}
