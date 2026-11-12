"""Guardrails at input, output and draft time (architecture section 7).

Deterministic on purpose: these checks must work with or without a model, and are easy to test and audit.
They are a first layer. A trained classifier and red-team set replace the word lists before any real use.
"""
import re

# --- Input: safety disclosure (kin and applicant chats; also caseworker chat for crisis words) ----------
SAFETY_PATTERNS = [
    r"\b(hit|hits|hitting|beat|beats|beating|punch\w*|kick\w*|slap\w*|chok\w*)\s+(me|him|her|them|the (kid|child|baby)|my)\b",
    r"\bhurt(s|ing)?\s+(me|him|her|them|the (kid|child|baby)|himself|herself|themself)\b",
    r"\b(bruise|bruises|bruised|burn mark|black eye)\b",
    r"\b(touch(ed|ing)? (him|her|me|them) (inappropriately|wrong)|sexual(ly)? abus\w*|molest\w*)\b",
    r"\babus(e|ed|ing|ive)\b",
    r"\b(not safe|unsafe|in danger|scared of (him|her|them|my|his|their))\b",
    r"\b(kill|suicid\w*|self[- ]harm|cutting (himself|herself|themself)|overdos\w*|want to die|end (my|his|her) life)\b",
    r"\b(ran away|(he|she|they|child|kid) (is|are|went) missing|can'?t find (him|her|them))\b",
    r"\b(gun|knife|weapon)\b",
    r"\b(me pega|le pega|nos pega|abuso|no est[aá] segur[oa]|lastim\w*|tiene miedo de)\b",
]
CRISIS_LINE = "If a child is in immediate danger, call 911 now."

# --- Input: prompt injection -------------------------------------------------------------------------
INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)", r"\bsystem prompt\b", r"you are now\b",
    r"pretend (to be|you are)", r"act as (an? )?(admin|caseworker|supervisor|developer)", r"reveal (your|the) (instructions|prompt)",
    r"disregard (the|your) (rules|policy)", r"\bjailbreak\b", r"show me (all|other) (cases|families|children)",
]

# --- Emotional cues, used to adapt tone (AGENTS.md) ---------------------------------------------------
EMOTION_CUES = {
    "overwhelmed": [r"overwhelm", r"too much", r"can'?t (do|handle) (this|it)", r"don'?t know what to do", r"\blost\b", r"so many"],
    "worried": [r"worr", r"nervous", r"anxious", r"\bscared\b", r"afraid", r"what if", r"preocup", r"miedo"],
    "frustrated": [r"frustrat", r"still waiting", r"nobody", r"no one (called|answers)", r"why (is|does) (it|this) take",
                   r"again\?", r"ridiculous", r"annoy"],
    "grieving": [r"\bsad\b", r"\bmiss(es|ing)? (my|her|his|their|mom|dad)", r"crying", r"heartbr", r"extra[ñn]a"],
    "rushed": [r"\bbehind\b", r"swamped", r"no time", r"slammed", r"deadline", r"tonight", r"asap", r"urgent", r"quick(ly)?"],
    "money_strain": [r"money", r"afford", r"bills", r"\brent\b", r"groceries", r"dinero"],
}

# --- Output: decisions the AI must never make -------------------------------------------------------
DECISION_PATTERNS = [
    r"\b(i|we) (recommend|suggest|advise)\b[^.]{0,60}\b(plac(e|ing|ement)|remov(e|al|ing)|custody|reunif\w*|terminat\w*|adopt\w*)",
    r"\b(should|must) (be )?(placed|removed|returned home|reunified|adopted)\b",
    r"\brisk (score|level|rating) (is|of)\b",
    r"\b(you are|they are|is) (eligible|not eligible|ineligible|approved|denied)\b",
    r"\b(high|low|medium)[- ]risk (family|parent|child|home)\b",
]
LEGAL_ADVICE_PATTERNS = [r"\byou (should|must) (file|sue|petition|appeal)\b", r"\byour legal right is\b", r"\bin my legal opinion\b"]

# --- Fault-assigning language in records (caseworker visit note) -------------------------------------
FAULT_TERMS = [
    (r"\bnon-?compliant\b", "has not yet completed [specific step]", "Labels the person instead of describing what happened."),
    (r"\brefused to\b", "did not / said they would not", "'Refused' assigns intent. Describe what was said or done."),
    (r"\bfailed to\b", "did not", "'Failed' assigns fault. State the fact."),
    (r"\buncooperative\b", "describe the specific behavior", "Opinion, not an observation."),
    (r"\b(hostile|aggressive|combative)\b", "quote what was said or describe what was done", "Characterization, not an observation."),
    (r"\b(claims|claimed|alleges|alleged) that\b", "said that", "Casts doubt on the parent's account."),
    (r"\badmitted\b", "said", "Implies wrongdoing."),
    (r"\b(dirty|filthy|messy) (home|house|apartment)\b", "describe observable conditions (e.g. dishes in sink, no food in fridge)",
     "Subjective. Describe what you saw."),
    (r"\b(drug addict|addict|junkie)\b", "person who uses substances / person with a substance use disorder", "Person-first language."),
    (r"\b(lazy|unfit|bad (mother|father|parent)|manipulative|neglectful (mother|father|parent))\b",
     "describe the specific behavior and its effect on the child", "Judgment about character."),
    (r"\bbroken home\b", "family", "Stigmatizing."),
    (r"\bdenies\b", "said [what they said]", "Implies the statement is false."),
]


def _any(patterns, text):
    return [p for p in patterns if re.search(p, text, re.I)]


def check_input(text, persona):
    t = text or ""
    safety = bool(_any(SAFETY_PATTERNS, t))
    emotions = [k for k, pats in EMOTION_CUES.items() if _any(pats, t)]
    return {"safety": safety, "injection": bool(_any(INJECTION_PATTERNS, t)), "emotions": emotions,
            "spanish": bool(re.search(r"[¿¡ñáéíóú]|\b(hola|gracias|ayuda|necesito|puedo|niñ[oa]s?)\b", t, re.I))}




def _decides(text):
    """True when the text states a decision. Conditional mentions ("after you are approved") are explanations, not verdicts."""
    for pat in DECISION_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            before = text[max(0, m.start() - 24):m.start()]
            if re.search(r"\b(before|after|until|once|when|if|unless|whether)\s*$", before, re.I):
                continue
            return True
    return False


def check_output(text, persona):
    flags = []
    if _decides(text):
        flags.append("decision_blocked")
        text = ("I can't make or recommend placement, custody, eligibility, approval or risk decisions. "
                + ("Those decisions belong to you, your supervisor and the court. I can gather the facts and sources for you."
                   if persona == "caseworker" else
                   "Those decisions are made by people at the agency and the court. Your caseworker can talk this through with you."))
    if persona != "caseworker" and _any(LEGAL_ADVICE_PATTERNS, text):
        flags.append("legal_advice_softened")
        text += "\n\nThis is general information, not legal advice. For your family's situation, ask your worker or a family law advisor."
    grade = reading_grade(text)
    if persona == "kin" and grade > 8.5:
        flags.append(f"reading_level_{grade:.0f}")
    return text, flags


def language_check(text):
    """Return fault-assigning phrases with suggested neutral rewrites. The worker decides."""
    out = []
    for pat, suggestion, why in FAULT_TERMS:
        for m in re.finditer(pat, text or "", re.I):
            out.append({"start": m.start(), "end": m.end(), "phrase": m.group(0), "suggestion": suggestion, "why": why})
    return sorted(out, key=lambda x: x["start"])


def reading_grade(text):
    """Flesch-Kincaid grade level (rough; good enough to flag text that is too hard)."""
    words = re.findall(r"[A-Za-z']+", text or "")
    if not words:
        return 0.0
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    syl = sum(max(1, len(re.findall(r"[aeiouy]+", w.lower())) - (1 if w.lower().endswith("e") else 0)) for w in words)
    return max(0.0, 0.39 * len(words) / sentences + 11.8 * syl / len(words) - 15.59)
