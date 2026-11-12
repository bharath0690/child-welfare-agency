"""Tool gateway (architecture section 4).

Every tool call, from the model or from the scripted fallback, goes through `call()`:
  1. persona allowlist check        (a tool not on the list does not exist for that agent)
  2. schema validation of inputs    (no unexpected or oversized arguments)
  3. authorization with the USER's identity and scope (assigned cases, own child, own application)
  4. disclosure policy matrix       (fields are removed before data reaches the model)
  5. audit log                      (inputs, fields returned, decision)
Writes never change the record. They create an idempotent proposal that a human approves.
"""
import difflib
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from . import db
from . import observability as obs
from .avatars import svg

PERSONAS = ("caseworker", "applicant", "kin", "foster")
CAREGIVERS = ("kin", "foster")


class GatewayError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


@dataclass
class Identity:
    persona: str
    user_id: str
    name: str = ""
    case_ids: set = field(default_factory=set)
    child_id: str = None
    applicant_id: str = None

    @classmethod
    def resolve(cls, persona, user_id):
        if persona not in PERSONAS:
            raise GatewayError("bad_persona", f"Unknown persona {persona!r}")
        if persona == "caseworker":
            w = db.row("SELECT * FROM workers WHERE id=? AND role='caseworker'", (user_id,))
            if not w:
                raise GatewayError("unknown_user", "Unknown caseworker")
            ids = {r["id"] for r in db.rows("SELECT id FROM cases WHERE worker_id=?", (user_id,))}
            return cls(persona, user_id, w["name"], ids)
        if persona == "kin":
            k = db.row("SELECT * FROM kin_users WHERE id=?", (user_id,))
            if not k:
                raise GatewayError("unknown_user", "Unknown kin caregiver")
            ids = {r["id"] for r in db.rows("SELECT id FROM cases WHERE child_id=?", (k["child_id"],))}
            return cls(persona, user_id, k["name"], ids, child_id=k["child_id"])
        if persona == "foster":
            f = db.row("SELECT * FROM foster_users WHERE id=?", (user_id,))
            if not f:
                raise GatewayError("unknown_user", "Unknown foster parent")
            ids = {r["id"] for r in db.rows("SELECT id FROM cases WHERE child_id=?", (f["child_id"],))}
            return cls(persona, user_id, f["name"], ids, child_id=f["child_id"])
        a = db.row("SELECT * FROM applicants WHERE id=?", (user_id,))
        if not a:
            raise GatewayError("unknown_user", "Unknown applicant")
        return cls(persona, user_id, a["name"], set(), applicant_id=a["id"])


# ---------------------------------------------------------------------------------------------------------
# Disclosure policy matrix
# ---------------------------------------------------------------------------------------------------------
CHILD_FIELD_MAP = {  # output key -> matrix field
    "first": "name", "last": "name", "name": "name", "age": "age", "dob": "dob", "gender": "gender",
    "pronouns": "pronouns", "avatar_svg": "photo", "language": "language", "school": "school", "grade": "school",
    "medical": "medical", "allergies": "allergies", "race_ethnicity": "race_ethnicity", "icwa": "icwa",
    "parent_contact": "parent_contact", "removal_reason": "removal_reason",
}


def allowed_fields(persona):
    settings = {r["k"]: r["v"] for r in db.rows("SELECT * FROM agency_settings")}
    out = set()
    for r in db.rows("SELECT * FROM disclosure"):
        ok = bool(r[persona])
        if ok and r["setting"]:
            ok = settings.get(r["setting"]) == "true"
        if ok:
            out.add(r["field"])
    return out


def filter_child(obj, persona):
    allowed = allowed_fields(persona)
    return {k: v for k, v in obj.items() if k not in CHILD_FIELD_MAP or CHILD_FIELD_MAP[k] in allowed}


def age_of(dob_iso):
    b, t = date.fromisoformat(dob_iso), date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def child_view(child_id, case=None):
    c = db.row("SELECT * FROM children WHERE id=?", (child_id,))
    av = json.loads(c["avatar"])
    out = {
        "child_id": c["id"], "first": c["first"], "last": c["last"], "name": f"{c['first']} {c['last']}",
        "age": age_of(c["dob"]), "dob": c["dob"], "gender": c["gender"], "pronouns": c["pronouns"],
        "avatar_svg": svg(**av, label=f"Illustrated avatar of {c['first']}"), "language": c["language"],
        "school": c["school"], "grade": c["grade"], "medical": c["medical"], "allergies": c["allergies"],
        "race_ethnicity": c["race_ethnicity"], "icwa": c["icwa"],
    }
    if case:
        out.update(parent_contact=case["parent_contact"], removal_reason=case["removal_reason"])
    return out


# ---------------------------------------------------------------------------------------------------------
# Tool implementations. Each takes (ident, args) and returns JSON-serialisable data.
# ---------------------------------------------------------------------------------------------------------
def _case(ident, case_id):
    if case_id not in ident.case_ids:
        raise GatewayError("forbidden", "This case is outside your assignment.")
    return db.row("SELECT * FROM cases WHERE id=?", (case_id,))


def _kin_case(ident):
    return db.row("SELECT * FROM cases WHERE child_id=?", (ident.child_id,))


def t_cases_list_assigned(ident, a):
    out = []
    for c in db.rows("SELECT * FROM cases WHERE worker_id=? ORDER BY case_no", (ident.user_id,)):
        ch = db.row("SELECT first, last, dob FROM children WHERE id=?", (c["child_id"],))
        out.append({"case_id": c["id"], "case_no": c["case_no"], "child": f"{ch['first']} {ch['last']}",
                    "age": age_of(ch["dob"]), "status": c["status"], "permanency_goal": c["permanency_goal"]})
    return out


def t_case_get(ident, a):
    c = _case(ident, a["case_id"])
    out = {"case_id": c["id"], "case_no": c["case_no"], "opened_on": c["opened_on"], "status": c["status"],
           "permanency_goal": c["permanency_goal"], "jurisdiction": c["jurisdiction"], "flags": json.loads(c["flags"]),
           "worker": db.row("SELECT name FROM workers WHERE id=?", (c["worker_id"],))["name"],
           "placement": db.row("SELECT caregiver, kind, start_on, city FROM placements WHERE child_id=? AND current=1",
                               (c["child_id"],))}
    out["child"] = filter_child(child_view(c["child_id"], c), ident.persona)
    if "removal_reason" in out["child"]:
        out["removal_reason"] = out["child"].pop("removal_reason")
    return out


def t_relationships_list(ident, a):
    c = _case(ident, a["case_id"])
    return db.rows("SELECT id, name, relation, contact_status, language, phone, last_contact_on FROM relationships "
                   "WHERE child_id=? ORDER BY id", (c["child_id"],))


def t_placements_list(ident, a):
    c = _case(ident, a["case_id"])
    return db.rows("SELECT caregiver, kind, start_on, end_on, city, current FROM placements WHERE child_id=? "
                   "ORDER BY start_on DESC", (c["child_id"],))


def t_history_list(ident, a):
    _case(ident, a["case_id"])
    return db.rows("SELECT on_date, kind, text FROM history WHERE case_id=? ORDER BY on_date DESC", (a["case_id"],))


def t_tasks_list(ident, a):
    _case(ident, a["case_id"])
    return db.rows("SELECT id, title, due_on, status, kind FROM tasks WHERE case_id=? ORDER BY due_on", (a["case_id"],))


def t_court_dates_list(ident, a):
    _case(ident, a["case_id"])
    return db.rows("SELECT on_date, hearing, report_status FROM court_dates WHERE case_id=? ORDER BY on_date",
                   (a["case_id"],))


def t_visits_list(ident, a):
    _case(ident, a["case_id"])
    return db.rows("SELECT id, on_date, kind, location, consent, note_status, transcript IS NOT NULL AS has_recording "
                   "FROM visits WHERE case_id=? ORDER BY on_date DESC", (a["case_id"],))


def t_visit_get(ident, a):
    _case(ident, a["case_id"])
    v = db.row("SELECT * FROM visits WHERE id=? AND case_id=?", (a["visit_id"], a["case_id"]))
    if not v:
        raise GatewayError("not_found", "Visit not found on this case.")
    if not v["consent"]:
        v["transcript"] = None
        v["consent_note"] = "No recording consent for this visit, so there is no transcript."
    return v


def t_notes_search(ident, a):
    _case(ident, a["case_id"])
    stop = {"what", "did", "does", "say", "said", "about", "the", "and", "his", "her", "their", "they", "was", "were",
            "has", "have", "any", "how", "when", "who", "tell", "mention", "mentioned", "with", "from", "this", "that"}
    q = [w.strip("?.,!") for w in a["query"].lower().split()]
    q = [w for w in q if len(w) > 2 and w not in stop]
    if not q:
        return []
    cands = []
    for n in db.rows("SELECT id, on_date, body, status FROM notes WHERE case_id=?", (a["case_id"],)):
        cands.append({"source": f"Visit note {n['on_date']} ({n['status']})", "text": n["body"][:400]})
    for v in db.rows("SELECT on_date, transcript FROM visits WHERE case_id=? AND consent=1 AND transcript IS NOT NULL",
                     (a["case_id"],)):
        for line in v["transcript"].splitlines():
            if line.strip():
                cands.append({"source": f"Visit transcript {v['on_date']} {line[:7]}", "text": line[8:]})
    for h in db.rows("SELECT on_date, text FROM history WHERE case_id=?", (a["case_id"],)):
        cands.append({"source": f"Case history {h['on_date']}", "text": h["text"]})
    # Rank by rarity-weighted term matches: a word that appears everywhere (the child's name) counts for little.
    df = {w: sum(1 for c in cands if w in c["text"].lower()) for w in q}
    scored = []
    for i, c in enumerate(cands):
        score = sum(1.0 / df[w] for w in q if df[w] and w in c["text"].lower())
        if score:
            scored.append((-score, i, c))
    if not scored:
        return []
    best = -min(scored)[0]
    return [c for sc, _, c in sorted(scored) if -sc >= best * 0.5][:12]


def t_referrals_list(ident, a):
    _case(ident, a["case_id"])
    return db.rows("SELECT provider, service, status, sent_on FROM referrals WHERE case_id=?", (a["case_id"],))


def t_plan_get(ident, a):
    _case(ident, a["case_id"])
    return db.rows("SELECT goal, status FROM plan_goals WHERE case_id=?", (a["case_id"],))


def t_proposals_list(ident, a):
    _case(ident, a["case_id"])
    rows = db.rows("SELECT id, kind, summary, status, created_at FROM proposals WHERE object_type='case' AND object_id=? "
                   "AND status='pending' ORDER BY id", (a["case_id"],))
    return rows


def t_memory_note(ident, a):
    obj = ("case", a["case_id"]) if ident.persona == "caseworker" else _own_object(ident)
    if ident.persona == "caseworker":
        _case(ident, a["case_id"])
    db.execute("INSERT INTO case_memory (object_type, object_id, fact, source, created_at) VALUES (?,?,?,?,?)",
               (obj[0], obj[1], a["fact"][:500], f"{ident.persona}:{ident.user_id}", _now()))
    return {"saved": True, "scope": f"{obj[0]} {obj[1]} only"}


def _own_object(ident):
    if ident.persona in CAREGIVERS:
        return ("case", _kin_case(ident)["id"])
    return ("application", ident.applicant_id)


# drafts (proposals) ------------------------------------------------------------------------------------
def _propose(ident, obj_type, obj_id, kind, payload, summary):
    key = kind + ":" + hashlib.sha256(json.dumps([obj_type, obj_id, payload], sort_keys=True).encode()).hexdigest()[:16]
    existing = db.row("SELECT id, status FROM proposals WHERE idem_key=?", (key,))
    if existing:
        return {"proposal_id": existing["id"], "status": existing["status"], "idempotent_replay": True}
    pid = db.execute("INSERT INTO proposals (trace_id, idem_key, object_type, object_id, kind, payload, summary, status, created_by, "
                     "created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (obs.current_trace_id(), key, obj_type, obj_id, kind, json.dumps(payload), summary, "pending",
                      f"agency-ai for {ident.persona}:{ident.user_id}", _now()))
    return {"proposal_id": pid, "status": "pending", "diff": payload, "needs": approver(kind)}


def approver(kind):
    return {"note": "Caseworker review and signature", "court_report": "Caseworker writes the recommendation and signs", "form": "Caseworker review", "task": "Caseworker approval",
            "outreach": "Caseworker review (bilingual check if translated)", "application_field": "Family submits",
            "message": "Delivered to the caseworker", "callback": "Delivered to the caseworker"}.get(kind, "Human review")


def t_note_draft(ident, a):
    _case(ident, a["case_id"])
    v = db.row("SELECT on_date FROM visits WHERE id=? AND case_id=?", (a["visit_id"], a["case_id"]))
    if not v:
        raise GatewayError("not_found", "Visit not found on this case.")
    out = _propose(ident, "case", a["case_id"], "note", {"visit_id": a["visit_id"], "body": a["body"], "on_date": v["on_date"]},
                   f"Visit note draft for {v['on_date']}")
    db.execute("UPDATE visits SET note_status='draft' WHERE id=? AND note_status='none'", (a["visit_id"],))
    return out


def t_form_prefill_draft(ident, a):
    _case(ident, a["case_id"])
    return _propose(ident, "case", a["case_id"], "form",
                    {"visit_id": a["visit_id"], "form_type": a["form_type"], "fields": a["fields"]},
                    f"{a['form_type']} pre-filled from visit")


def t_task_propose(ident, a):
    _case(ident, a["case_id"])
    return _propose(ident, "case", a["case_id"], "task", {"title": a["title"], "due_on": a["due_on"]},
                    f"Task: {a['title']}")


def t_outreach_draft(ident, a):
    c = _case(ident, a["case_id"])
    r = db.row("SELECT * FROM relationships WHERE id=? AND child_id=?", (a["relationship_id"], c["child_id"]))
    if not r:
        raise GatewayError("not_found", "Relative not found on this case.")
    return _propose(ident, "case", a["case_id"], "outreach",
                    {"relationship_id": r["id"], "to": r["name"], "language": a["language"], "body": a["body"]},
                    f"First-contact message to {r['name']} ({a['language']})")


# applicant -------------------------------------------------------------------------------------------
def t_application_get(ident, a):
    ap = db.row("SELECT * FROM applicants WHERE id=?", (ident.applicant_id,))
    w = db.row("SELECT name, phone, email FROM workers WHERE id=?", (ap["worker_id"],))
    return {"household": ap["household"], "stage": ap["stage"], "application": json.loads(ap["application"]),
            "licensing_worker": w}


def t_checklist_get(ident, a):
    ap = db.row("SELECT checklist FROM applicants WHERE id=?", (ident.applicant_id,))
    return json.loads(ap["checklist"])


def t_application_field_draft(ident, a):
    ap = json.loads(db.row("SELECT application FROM applicants WHERE id=?", (ident.applicant_id,))["application"])
    if a["field"] not in ap["fields"]:
        raise GatewayError("bad_field", f"Unknown application field {a['field']!r}")
    return _propose(ident, "application", ident.applicant_id, "application_field",
                    {"field": a["field"], "value": a["value"], "before": ap["fields"][a["field"]]},
                    f"Draft for '{a['field']}'")


def t_program_search(ident, a):
    """Keyword (BM25-style) retrieval over program content, filtered by audience first.
    The vector half of hybrid RAG is a later step; see docs/ai-architecture.md section 9."""
    import math
    import re
    aud = {"caseworker": ("applicant", "kin", "foster", "all"), "applicant": ("applicant", "all"), "kin": ("kin", "all"),
           "foster": ("foster", "applicant", "all")}[ident.persona]
    docs = db.rows(f"SELECT id, title, body, source FROM program_docs WHERE audience IN ({','.join('?' * len(aud))})", aud)
    tok = lambda s: re.findall(r"[a-z]+", s.lower())
    stop = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "i", "my", "me", "for", "can", "do", "what", "how",
            "you", "it", "be", "are", "on", "with", "before", "if", "they", "them", "this", "that", "get"}
    q = [w for w in tok(a["query"]) if w not in stop]
    syn = {"kids": "child", "kid": "child", "money": "financial", "pay": "payment", "help": "help", "take": "care",
           "approved": "approval", "license": "approval", "fingerprint": "fingerprints", "court": "hearings"}
    q += [syn[w] for w in q if w in syn]
    if not q:
        return []
    N, avg = len(docs), sum(len(tok(d["title"] + " " + d["body"])) for d in docs) / max(len(docs), 1)
    scored = []
    for d in docs:
        words = tok(d["title"] + " " + d["title"] + " " + d["body"])
        s = 0.0
        for w in set(q):
            tf = sum(1 for x in words if x.startswith(w[:6]))
            if tf:
                df = sum(1 for o in docs if w[:6] in o["title"].lower() + o["body"].lower())
                idf = math.log(1 + (N - df + .5) / (df + .5))
                s += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * len(words) / avg))
        if s > 0.4:
            scored.append((s, d))
    scored.sort(key=lambda x: -x[0])
    return [{"title": d["title"], "text": d["body"], "source": d["source"], "score": round(s, 2)} for s, d in scored[:3]]


# kin -------------------------------------------------------------------------------------------------
def t_child_details_get(ident, a):
    c = _kin_case(ident)
    return filter_child(child_view(c["child_id"], c), ident.persona)


def t_child_schedule_get(ident, a):
    c = _kin_case(ident)
    court = db.rows("SELECT on_date, hearing FROM court_dates WHERE case_id=? AND on_date>=? ORDER BY on_date",
                    (c["id"], date.today().isoformat()))
    last = db.row("SELECT on_date FROM visits WHERE case_id=? ORDER BY on_date DESC", (c["id"],))
    nxt = (date.fromisoformat(last["on_date"]) + timedelta(days=7 if c["status"] == "open" and
                                                           _days_since(c["opened_on"]) < 30 else 28)).isoformat()
    items = [{"date": x["on_date"], "what": f"Court: {x['hearing']}", "source": "Court calendar"} for x in court]
    items.append({"date": nxt, "what": "Caseworker home visit (to confirm with your worker)", "source": "Visit schedule"})
    ch = db.row("SELECT school FROM children WHERE id=?", (c["child_id"],))
    if not ch["school"].lower().startswith("not in school"):
        items.append({"date": "Weekdays", "what": f"School: {ch['school']}", "source": "Child record"})
    return sorted(items, key=lambda x: x["date"])


def t_worker_contact_get(ident, a):
    c = _kin_case(ident) if ident.persona in CAREGIVERS else None
    wid = c["worker_id"] if c else db.row("SELECT worker_id FROM applicants WHERE id=?", (ident.applicant_id,))["worker_id"]
    return db.row("SELECT name, role, phone, email FROM workers WHERE id=?", (wid,))


def _owner(ident):
    return (ident.persona, ident.user_id)


def _worker_for(ident):
    if ident.persona in CAREGIVERS:
        return _kin_case(ident)["worker_id"]
    if ident.persona == "applicant":
        return db.row("SELECT worker_id FROM applicants WHERE id=?", (ident.applicant_id,))["worker_id"]
    return None


def add_business_days(start, n):
    d = start
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def messages_with_clock(owner_type, owner_id):
    """Messages to the worker with their response deadline. Unanswered past the deadline -> escalated to the supervisor."""
    days = int((db.row("SELECT v FROM agency_settings WHERE k='message_response_business_days'") or {"v": "2"})["v"])
    out = []
    for m in db.rows("SELECT * FROM worker_messages WHERE owner_type=? AND owner_id=? ORDER BY sent_at DESC", (owner_type, owner_id)):
        w = db.row("SELECT name, phone, supervisor_id FROM workers WHERE id=?", (m["worker_id"],))
        sup = db.row("SELECT name, phone FROM workers WHERE id=?", (w["supervisor_id"],)) if w and w["supervisor_id"] else None
        sent = datetime.fromisoformat(m["sent_at"])
        due = add_business_days(sent.date(), days)
        if m["answered_at"]:
            state = "answered"
        elif date.today() > due:
            state = "escalated"
            if not m["escalated_to"] and sup:
                db.execute("UPDATE worker_messages SET escalated_to=?, escalated_at=? WHERE id=?",
                           (sup["name"], due.isoformat(), m["id"]))
                m["escalated_to"], m["escalated_at"] = sup["name"], due.isoformat()
        else:
            state = "waiting"
        out.append({"id": m["id"], "text": m["text"], "sent_on": m["sent_at"][:10], "worker": w["name"] if w else None,
                    "respond_by": due.isoformat(), "state": state, "answer": m["answer"],
                    "escalated_to": m["escalated_to"] or (sup["name"] if state == "escalated" and sup else None),
                    "supervisor": sup})
    return out


def t_message_worker(ident, a):
    wid = _worker_for(ident)
    key = "msg:" + hashlib.sha256(json.dumps([ident.persona, ident.user_id, a["text"]]).encode()).hexdigest()[:16]
    if not db.row("SELECT id FROM worker_messages WHERE idem_key=?", (key,)):
        db.execute("INSERT INTO worker_messages (idem_key, owner_type, owner_id, from_name, worker_id, text, sent_at) VALUES (?,?,?,?,?,?,?)",
                   (key, ident.persona, ident.user_id, ident.name, wid, a["text"][:2000], _now()))
    m = messages_with_clock(ident.persona, ident.user_id)[0]
    return {"sent": True, "to": m["worker"], "respond_by": m["respond_by"],
            "if_no_reply": f"If there's no reply by {m['respond_by']}, it goes to {m['supervisor']['name']} automatically." if m["supervisor"] else ""}


def t_messages_get(ident, a):
    return messages_with_clock(ident.persona, ident.user_id)


def t_contacts_get(ident, a):
    """Who to call for what: named worker, their supervisor, then agency lines for this audience."""
    out = []
    wid = _worker_for(ident)
    w = db.row("SELECT name, role, phone, email, supervisor_id FROM workers WHERE id=?", (wid,))
    if w:
        out.append({"role": "Your worker", "name": w["name"] + " (" + w["role"] + ")", "phone": w["phone"], "hours": "Weekdays",
                    "use_for": "Day-to-day questions about the child or your application."})
        sup = db.row("SELECT name, role, phone FROM workers WHERE id=?", (w["supervisor_id"],)) if w["supervisor_id"] else None
        if sup:
            out.append({"role": "Their supervisor", "name": sup["name"] + " (" + sup["role"] + ")", "phone": sup["phone"], "hours": "Weekdays",
                        "use_for": "No reply within 2 business days, or a concern about how things are going with your worker."})
    for c in db.rows("SELECT * FROM agency_contacts ORDER BY sort"):
        if ident.persona in c["audience"].split(","):
            out.append({"role": c["role"], "name": c["name"], "phone": c["phone"], "hours": c["hours"], "use_for": c["use_for"]})
    return out


def t_care_needs_get(ident, a):
    c = _kin_case(ident)
    if "care_needs" not in allowed_fields(ident.persona):
        return {"available": False, "note": "Your agency hasn't turned on sharing of care needs. Ask your caseworker."}
    n = db.row("SELECT * FROM care_needs WHERE child_id=?", (c["child_id"],))
    if not n:
        return {"available": False, "note": "Your caseworker hasn't written these yet. Ask them what the child needs day to day."}
    return {"available": True, "routines": n["routines"], "health": n["health"], "school": n["school"], "comfort": n["comfort"],
            "avoid": n["avoid"], "updated_on": n["updated_on"], "source": n["source"]}


def _with_age(items, start=None):
    out = []
    for it in items:
        x = dict(it)
        since = x.get("since", 0)
        x["since_on"] = (date.today() - timedelta(days=since)).isoformat()
        x["days"] = since
        t = x.get("typical")
        x["stalled"] = bool(t) and x["status"] not in ("done", "reused", "active") and since > t[1]
        out.append(x)
    return out


def t_approval_status_get(ident, a):
    k = db.row("SELECT * FROM kin_users WHERE id=?", (ident.user_id,))
    target = int((db.row("SELECT v FROM agency_settings WHERE k='kin_license_target_days'") or {"v": "90"})["v"])
    day = _days_since(k["placed_on"])
    return {"placed_on": k["placed_on"], "day": day, "agency_target_days": target, "national_average_days": 160,
            "items": _with_age(json.loads(k["approval"])),
            "note": "Steps run in parallel. Anything past its usual time is flagged to the supervisor."}


def t_supports_get(ident, a):
    if ident.persona == "kin":
        k = db.row("SELECT * FROM kin_users WHERE id=?", (ident.user_id,))
        day = _days_since(k["placed_on"])
        return {"supports": json.loads(k["supports"]), "first_payment_on": k["first_payment_on"],
                "time_to_first_payment": (f"Paid on {k['first_payment_on']}" if k["first_payment_on"]
                                          else f"Day {day} since placement, no payment yet"),
                "now_without_license": [s["name"] for s in json.loads(k["supports"]) if not s["license"] and s["status"] != "active"]}
    f = db.row("SELECT * FROM foster_users WHERE id=?", (ident.user_id,))
    pay = json.loads(f["payments"])
    pend = [dict(x, submitted_on=(date.today() + timedelta(days=x["submitted"])).isoformat(), days=-x["submitted"]) for x in pay["pending"]]
    return {"supports": json.loads(f["supports"]), "monthly": pay["monthly"],
            "last_paid_on": (date.today() + timedelta(days=pay["last_paid"])).isoformat(),
            "next_payment_on": (date.today() + timedelta(days=pay["next_due"])).isoformat(), "pending_reimbursements": pend}


def t_adoption_status_get(ident, a):
    f = db.row("SELECT * FROM foster_users WHERE id=?", (ident.user_id,))
    return {"steps": _with_age(json.loads(f["adoption"])),
            "context": "Nationally, the median time from termination of parental rights to adoption was about 9 months (AFCARS, FY2012).",
            "note": "Dates depend on the court. Your caseworker and the caregiver legal help line can explain each step."}


def t_court_report_draft(ident, a):
    _case(ident, a["case_id"])
    h = db.row("SELECT on_date, hearing FROM court_dates WHERE case_id=? AND on_date=?", (a["case_id"], a["hearing_date"]))
    if not h:
        raise GatewayError("not_found", "No hearing on that date for this case.")
    return _propose(ident, "case", a["case_id"], "court_report", {"hearing_date": h["on_date"], "hearing": h["hearing"], "body": a["body"]},
                    f"Court report draft: {h['hearing']}, {h['on_date']}")


def t_callback_request(ident, a):
    obj = _own_object(ident)
    return _propose(ident, obj[0], obj[1], "callback", {"from": ident.name, "reason": a["reason"]},
                    f"Callback request from {ident.name}")


# ---------------------------------------------------------------------------------------------------------
# Registry: schema + persona allowlist. The same definitions are sent to the model as tool specs.
# ---------------------------------------------------------------------------------------------------------
S = lambda d="": {"type": "string", "description": d}
I = lambda d="": {"type": "integer", "description": d}
CASE = {"case_id": S("Case id, e.g. case-01")}

TOOLS = {
    "cases_list_assigned": ("read", ("caseworker",), "List the cases assigned to the signed-in caseworker.", {}, [], t_cases_list_assigned),
    "case_get": ("read", ("caseworker",), "Case and child details (fields filtered by the disclosure policy).", CASE, ["case_id"], t_case_get),
    "relationships_list": ("read", ("caseworker",), "Relatives and family friends with contact status.", CASE, ["case_id"], t_relationships_list),
    "placements_list": ("read", ("caseworker",), "Current and past placements.", CASE, ["case_id"], t_placements_list),
    "history_list": ("read", ("caseworker",), "Case history events, newest first.", CASE, ["case_id"], t_history_list),
    "tasks_list": ("read", ("caseworker",), "Open tasks with due dates.", CASE, ["case_id"], t_tasks_list),
    "court_dates_list": ("read", ("caseworker",), "Court hearings and report status.", CASE, ["case_id"], t_court_dates_list),
    "visits_list": ("read", ("caseworker",), "Visits with consent and note status.", CASE, ["case_id"], t_visits_list),
    "visit_get": ("read", ("caseworker",), "One visit including its transcript when consent was given.",
                  {**CASE, "visit_id": I("Visit id")}, ["case_id", "visit_id"], t_visit_get),
    "notes_search": ("read", ("caseworker",), "Search notes, transcripts and history on one case. Returns quotes with sources.",
                     {**CASE, "query": S("Words to look for")}, ["case_id", "query"], t_notes_search),
    "referrals_list": ("read", ("caseworker",), "Service referrals and their status.", CASE, ["case_id"], t_referrals_list),
    "plan_get": ("read", ("caseworker",), "Case plan goals and status.", CASE, ["case_id"], t_plan_get),
    "proposals_list": ("read", ("caseworker",), "AI drafts on this case waiting for review.", CASE, ["case_id"], t_proposals_list),
    "memory_note": ("memory", ("caseworker",), "Save a fact to this case's memory so it is remembered next session. Case-scoped only.",
                    {**CASE, "fact": S("Short fact worth remembering")}, ["case_id", "fact"], t_memory_note),
    "note_draft": ("draft", ("caseworker",), "Create a visit note DRAFT for the worker to review and sign.",
                   {**CASE, "visit_id": I(), "body": S("Draft note text with transcript timestamps as citations")},
                   ["case_id", "visit_id", "body"], t_note_draft),
    "form_prefill_draft": ("draft", ("caseworker",), "Create a pre-filled form DRAFT with a source quote and confidence per field.",
                           {**CASE, "visit_id": I(), "form_type": S(), "fields": {"type": "object"}},
                           ["case_id", "visit_id", "form_type", "fields"], t_form_prefill_draft),
    "task_propose": ("draft", ("caseworker",), "Propose a task for the worker to approve.",
                     {**CASE, "title": S(), "due_on": S("YYYY-MM-DD")}, ["case_id", "title", "due_on"], t_task_propose),
    "outreach_draft": ("draft", ("caseworker",), "Draft a first-contact message to a relative for worker review.",
                       {**CASE, "relationship_id": I(), "language": S(), "body": S()},
                       ["case_id", "relationship_id", "language", "body"], t_outreach_draft),
    "program_search": ("read", ("caseworker", "applicant", "kin", "foster"), "Search agency program content (licensing, kin options, supports). Returns cited passages.",
                       {"query": S("The question in plain words")}, ["query"], t_program_search),
    "application_get": ("read", ("applicant",), "The family's own application and licensing worker.", {}, [], t_application_get),
    "checklist_get": ("read", ("applicant",), "The family's own requirements checklist.", {}, [], t_checklist_get),
    "application_field_draft": ("draft", ("applicant",), "Draft text for one application field. The family edits and submits.",
                                {"field": S(), "value": S()}, ["field", "value"], t_application_field_draft),
    "child_details_get": ("read", CAREGIVERS, "Details about the child in your care that the agency allows you to see.", {}, [], t_child_details_get),
    "child_schedule_get": ("read", CAREGIVERS, "Upcoming court dates, visits and school for the child in your care.", {}, [], t_child_schedule_get),
    "worker_contact_get": ("read", ("kin", "foster", "applicant"), "Name and contact details of your worker.", {}, [], t_worker_contact_get),
    "message_worker": ("request", ("kin", "foster", "applicant"),
                       "Send a message to your worker. It has a reply deadline and goes to their supervisor if unanswered.",
                       {"text": S()}, ["text"], t_message_worker),
    "messages_get": ("read", ("kin", "foster", "applicant"), "Your messages to your worker, with reply deadlines and escalation status.",
                     {}, [], t_messages_get),
    "contacts_get": ("read", ("kin", "foster", "applicant"),
                     "Who to call for what: your worker, their supervisor, after-hours, behavior support, legal help, payments.",
                     {}, [], t_contacts_get),
    "care_needs_get": ("read", CAREGIVERS, "What the child in your care needs day to day: routines, health, school, what helps.",
                       {}, [], t_care_needs_get),
    "approval_status_get": ("read", ("kin",), "Your approval steps: who holds each one, since when, and how long it usually takes.",
                            {}, [], t_approval_status_get),
    "supports_get": ("read", CAREGIVERS, "Money and supports: what you can get now, payment status and pending reimbursements.",
                     {}, [], t_supports_get),
    "adoption_status_get": ("read", ("foster",), "Adoption steps for the child in your care: who holds each one and typical timing.",
                            {}, [], t_adoption_status_get),
    "court_report_draft": ("draft", ("caseworker",), "Create a court report DRAFT of cited facts. The worker writes the recommendation and signs.",
                           {**CASE, "hearing_date": S("YYYY-MM-DD"), "body": S()}, ["case_id", "hearing_date", "body"], t_court_report_draft),
    "callback_request": ("request", ("kin", "foster", "applicant"), "Ask your worker to call you back.", {"reason": S()}, ["reason"], t_callback_request),
}


def allowlist(persona):
    return [n for n, t in TOOLS.items() if persona in t[1]]


def specs(persona, only=None):
    """OpenAI-style tool specs (DeepSeek uses the same format)."""
    out = []
    for n in allowlist(persona):
        if only is not None and n not in only:
            continue
        kind, _, desc, props, req, _ = TOOLS[n]
        out.append({"type": "function", "function": {
            "name": n, "description": f"[{kind}] {desc}",
            "parameters": {"type": "object", "properties": props, "required": req, "additionalProperties": False}}})
    return out


def _validate(name, args):
    _, _, _, props, req, _ = TOOLS[name]
    if not isinstance(args, dict):
        raise GatewayError("bad_args", "Arguments must be an object.")
    extra = set(args) - set(props)
    if extra:
        raise GatewayError("bad_args", f"Unexpected arguments: {sorted(extra)}")
    for r in req:
        if r not in args:
            raise GatewayError("bad_args", f"Missing argument {r!r}")
    for k, v in args.items():
        t = props[k].get("type")
        if t == "string" and (not isinstance(v, str) or len(v) > 6000):
            raise GatewayError("bad_args", f"{k} must be a string under 6000 characters")
        if t == "integer":
            if isinstance(v, str) and v.isdigit():
                args[k] = int(v)
            elif not isinstance(v, int) or isinstance(v, bool):
                raise GatewayError("bad_args", f"{k} must be an integer")
        if t == "object" and not isinstance(v, dict):
            raise GatewayError("bad_args", f"{k} must be an object")
    return args


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _days_since(iso):
    return (date.today() - date.fromisoformat(iso[:10])).days


def _audit(ident, tool, args, decision, reason="", result=None):
    fields = []
    if isinstance(result, dict):
        fields = sorted(result.keys())
        if isinstance(result.get("child"), dict):
            fields += ["child." + k for k in sorted(result["child"].keys()) if k != "avatar_svg"]
    elif isinstance(result, list) and result and isinstance(result[0], dict):
        fields = sorted(result[0].keys())
    obj = args.get("case_id") if isinstance(args, dict) else None
    db.execute("INSERT INTO audit_log (at, persona, user_id, tool, args, object, fields, decision, reason) VALUES (?,?,?,?,?,?,?,?,?)",
               (_now(), ident.persona, ident.user_id, tool, json.dumps(args)[:2000], obj or ident.child_id or ident.applicant_id,
                json.dumps(fields), decision, reason))


def call(ident: Identity, name: str, args: dict = None):
    args = dict(args or {})
    with obs.child_span("tool: " + name, "tool", input=args, metadata={"persona": ident.persona}) as log:
        if name not in TOOLS or ident.persona not in TOOLS[name][1]:
            _audit(ident, name, args, "deny", "not on persona allowlist")
            log(metadata={"decision": "deny", "reason": "not on persona allowlist"})
            raise GatewayError("not_allowed", f"Tool {name!r} is not available to the {ident.persona} agent.")
        try:
            args = _validate(name, args)
            result = TOOLS[name][5](ident, args)
        except GatewayError as e:
            _audit(ident, name, args, "deny", e.message)
            log(metadata={"decision": "deny", "reason": e.message})
            raise
        _audit(ident, name, args, "allow", "", result)
        # Log which fields came back, not their values: the disclosure matrix already decided what the agent may see.
        log(output={"fields": sorted(result.keys()) if isinstance(result, dict) else f"{len(result)} rows" if isinstance(result, list) else type(result).__name__},
            metadata={"decision": "allow"})
        return result


# ---------------------------------------------------------------------------------------------------------
# Human approval of proposals (called from the UI, never by the model)
# ---------------------------------------------------------------------------------------------------------
def decide(ident: Identity, proposal_id: int, op: str, edited=None):
    p = db.row("SELECT * FROM proposals WHERE id=?", (proposal_id,))
    if not p or p["status"] != "pending":
        raise GatewayError("not_found", "No pending proposal with that id.")
    payload = json.loads(p["payload"])
    if p["object_type"] == "case":
        if ident.persona != "caseworker" or p["object_id"] not in ident.case_ids:
            raise GatewayError("forbidden", "Only the assigned caseworker can approve drafts on this case.")
    elif ident.persona != "applicant" or p["object_id"] != ident.applicant_id:
        raise GatewayError("forbidden", "Only the family can submit their application text.")
    if op not in ("approve", "reject"):
        raise GatewayError("bad_args", "op must be approve or reject")
    if op == "reject" and p["kind"] == "note":
        db.execute("UPDATE visits SET note_status='none' WHERE id=? AND note_status='draft'", (payload["visit_id"],))
    if op == "approve":
        if isinstance(edited, dict):
            payload.update({k: v for k, v in edited.items() if k in payload})
        _materialize(ident, p, payload)
    original = json.loads(p["payload"])
    db.execute("UPDATE proposals SET status=?, payload=?, decided_by=?, decided_at=? WHERE id=?",
               ("approved" if op == "approve" else "rejected", json.dumps(payload), ident.user_id, _now(), proposal_id))
    # Online eval signal (architecture section 7): did the person approve, and how much did they change the draft?
    scores = {"approved": 1 if op == "approve" else 0}
    text_key = next((k for k in ("body", "text", "draft") if isinstance(original.get(k), str)), None)
    if op == "approve" and text_key:
        scores["edit_similarity"] = round(difflib.SequenceMatcher(None, original[text_key], payload.get(text_key) or "").ratio(), 3)
    obs.feedback(p["trace_id"], scores, metadata={"decided_by": ident.user_id, "kind": p["kind"]})
    _audit(ident, "proposal_" + op, {"proposal_id": proposal_id, "case_id": p["object_id"]}, "allow", p["kind"])
    return {"proposal_id": proposal_id, "status": "approved" if op == "approve" else "rejected"}


def _materialize(ident, p, payload):
    cid, k, today = p["object_id"], p["kind"], date.today().isoformat()
    if k == "note":
        db.execute("INSERT INTO notes (case_id, visit_id, on_date, author, body, status, ai_drafted) VALUES (?,?,?,?,?,?,1)",
                   (cid, payload["visit_id"], payload["on_date"], ident.user_id, payload["body"], "signed"))
        db.execute("UPDATE visits SET note_status='signed' WHERE id=?", (payload["visit_id"],))
        db.execute("INSERT INTO history (case_id, on_date, kind, text) VALUES (?,?,?,?)",
                   (cid, today, "note", f"Visit note for {payload['on_date']} signed (drafted with Agency AI)."))
    elif k == "form":
        db.execute("INSERT INTO forms (case_id, visit_id, form_type, fields, status) VALUES (?,?,?,?,?)",
                   (cid, payload["visit_id"], payload["form_type"], json.dumps(payload["fields"]), "submitted"))
    elif k == "task":
        db.execute("INSERT INTO tasks (case_id, title, due_on, status, kind) VALUES (?,?,?,?,?)",
                   (cid, payload["title"], payload["due_on"], "open", "ai"))
    elif k == "outreach":
        db.execute("UPDATE relationships SET contact_status='Attempted Contact', last_contact_on=? WHERE id=?",
                   (today, payload["relationship_id"]))
        db.execute("INSERT INTO history (case_id, on_date, kind, text) VALUES (?,?,?,?)",
                   (cid, today, "outreach", f"First-contact message sent to {payload['to']} ({payload['language']})."))
    elif k == "court_report":
        db.execute("UPDATE court_dates SET report_status='ready to file' WHERE case_id=? AND on_date=?", (cid, payload["hearing_date"]))
        db.execute("INSERT INTO history (case_id, on_date, kind, text) VALUES (?,?,?,?)",
                   (cid, today, "court", f"Court report for the {payload['hearing'].lower()} on {payload['hearing_date']} signed (facts drafted with Agency AI)."))
    elif k == "application_field":
        ap = db.row("SELECT application FROM applicants WHERE id=?", (cid,))
        data = json.loads(ap["application"])
        data["fields"][payload["field"]] = payload["value"]
        db.execute("UPDATE applicants SET application=? WHERE id=?", (json.dumps(data), cid))
