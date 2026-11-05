"""Case stage and next-action engine (skill: next-action).

Rules decide the stage and the actions, so the result is explainable and testable.
The model, when one is configured, only words the explanation. It never ranks families or predicts risk.
Stage names match the caseworker journey in data.js (stages 1 to 6; stage 0 is the worker's day).
"""
import json
from datetime import date, datetime

from . import db, gateway

STAGES = {
    1: "Accept a new case",
    2: "Build the plan with the family",
    3: "Visit and capture",
    4: "Find and engage kin",
    5: "Prepare for court",
    6: "Reach permanency and close",
}
VISIT_INTERVAL = 28  # agency policy in the prototype: monthly caseworker visits (confirm per jurisdiction)


def _days(iso):
    return (date.fromisoformat(iso[:10]) - date.today()).days


def bundle(ident, case_id):
    """Everything the rules need, read through the gateway so it is authorized and audited."""
    g = lambda t: gateway.call(ident, t, {"case_id": case_id})
    return {"case": g("case_get"), "tasks": g("tasks_list"), "court": g("court_dates_list"), "visits": g("visits_list"),
            "relationships": g("relationships_list"), "referrals": g("referrals_list"), "plan": g("plan_get"),
            "proposals": g("proposals_list")}


def stage(b):
    c = b["case"]
    opened = -_days(c["opened_on"])
    court_soon = [x for x in b["court"] if 0 <= _days(x["on_date"]) <= 14]
    placement_kin = (c.get("placement") or {}).get("kind") == "kin"
    kin_open = [r for r in b["relationships"] if r["contact_status"] != "Successfully Contacted"]
    plan_draft = not b["plan"] or all(g["status"] == "draft" for g in b["plan"])
    if c["status"] == "closing":
        return 6, [f"Case status is closing; permanency goal: {c['permanency_goal']}"]
    if court_soon:
        h = court_soon[0]
        return 5, [f"{h['hearing']} in {_days(h['on_date'])} days ({h['on_date']})",
                   f"Court report status: {h['report_status']}"]
    if opened <= 30 and plan_draft:
        return 1, [f"Case opened {opened} days ago", "No agreed case plan yet"]
    if plan_draft:
        return 2, ["Case plan goals are missing or still in draft"]
    if not placement_kin and kin_open and "kin" in c["permanency_goal"].lower():
        return 4, [f"Permanency goal: {c['permanency_goal']}",
                   f"{len(kin_open)} relatives not yet reached"]
    if not placement_kin and kin_open and len(kin_open) > len(b["relationships"]) / 2:
        return 4, ["Child is not placed with kin", f"{len(kin_open)} of {len(b['relationships'])} relatives not yet reached"]
    return 3, ["Plan in place; ongoing visits and services"]


def actions(b):
    """Return candidate next actions, each with why, source and an urgency score (higher = sooner)."""
    out, c = [], b["case"]
    first = c["child"].get("first", "the child")

    def add(key, title, why, source, score, due=None, skill=None, ui=None):
        out.append(dict(key=key, title=title, why=why, source=source, score=score, due_on=due, skill=skill, ui=ui))

    for p in b["proposals"]:
        if p["kind"] == "note":
            add(f"review-proposal-{p['id']}", "Review and sign the AI-drafted visit note",
                f"{p['summary']} is waiting for your signature. Notes count once you sign them.",
                "Pending AI draft", 80, None, "visit-capture", f"proposal:{p['id']}")
    for v in b["visits"]:
        if v["has_recording"] and v["consent"] and v["note_status"] == "none":
            add(f"draft-note-{v['id']}", f"Draft the visit note from the {v['on_date']} recording",
                "The visit was recorded with consent, but no note exists yet.", f"Visit {v['on_date']}", 75,
                None, "visit-capture", f"visit-note:{v['id']}")
            add(f"prefill-{v['id']}", "Pre-fill the monthly visit form from the same recording",
                "Same facts, entered once. Each field shows its source quote.", f"Visit {v['on_date']}", 55,
                None, "form-prefill", f"prefill:{v['id']}")
    last = b["visits"][0]["on_date"] if b["visits"] else c["opened_on"]
    since = -_days(last)
    if since >= VISIT_INTERVAL - 5 and c["status"] != "closing":
        overdue = since - VISIT_INTERVAL
        add("visit-due", f"Schedule a visit with {first}" + (f" ({overdue} days overdue)" if overdue > 0 else ""),
            f"Last visit was {since} days ago; visits are due every {VISIT_INTERVAL} days (agency policy in this prototype).",
            f"Visit log, last {last}", 90 if overdue > 0 else 60)
    for h in b["court"]:
        n = _days(h["on_date"])
        if 0 <= n <= 14 and h["report_status"] != "submitted":
            add(f"court-{h['on_date']}", f"Prepare the court report for the {h['hearing'].lower()}",
                f"Hearing in {n} days. Report status: {h['report_status']}. Court report assembly (cited facts, your recommendation) is a Phase 2 feature.",
                f"Court calendar {h['on_date']}", 95 - n, h["on_date"])
    court_action = any(a["key"].startswith("court-") for a in out)
    for t in b["tasks"]:
        if t["status"] != "open" or (court_action and t["kind"] == "court"):
            continue
        n = _days(t["due_on"])
        if n < 0:
            add(f"task-{t['id']}", f"Overdue: {t['title']}", f"Was due {t['due_on']} ({-n} day{'s' if n != -1 else ''} ago).",
                "Task list", 85 + min(-n, 10), t["due_on"])
        elif n <= 7:
            add(f"task-{t['id']}", t["title"], f"Due {t['due_on']} (in {n} days).", "Task list", 70 - n, t["due_on"])
    for r in b["relationships"]:
        if r["contact_status"] == "Attempted Contact" and r["last_contact_on"] and -_days(r["last_contact_on"]) >= 7:
            add(f"kin-{r['id']}", f"Follow up with {r['name']}, {r['relation'].lower()}",
                f"Last attempt {-_days(r['last_contact_on'])} days ago with no response. "
                + (f"Prefers {r['language']}." if r["language"] != "English" else ""),
                "Relationships", 50, None, "kin-first-contact", f"outreach:{r['id']}")
        elif r["contact_status"] == "Not Yet Contacted" and r["relation"] not in ("Tribe",):
            add(f"kin-{r['id']}", f"Make first contact with {r['name']}, {r['relation'].lower()}",
                "Identified relative who has not been contacted yet."
                + (f" Prefers {r['language']}; a translated draft can be prepared for your review." if r["language"] != "English" else ""),
                "Relationships", 58, None, "kin-first-contact", f"outreach:{r['id']}")
    for f in b["referrals"]:
        if f["status"] == "awaiting reply" and f["sent_on"] and -_days(f["sent_on"]) >= 7:
            add(f"ref-{f['provider']}", f"Chase the referral to {f['provider']}",
                f"{f['service']} referral sent {-_days(f['sent_on'])} days ago with no reply.", "Referral log", 52)
        elif f["status"] == "not sent":
            add(f"ref-{f['provider']}", f"Send the {f['service'].lower()} referral to {f['provider']}",
                "Referral is in the plan but has not been sent.", "Referral log", 54)
    if not b["plan"] or all(g["status"] == "draft" for g in b["plan"]):
        add("plan", "Agree the case plan with the family",
            "No agreed plan yet. Plan builder can turn goals into dated tasks (Phase 2 feature).", "Case plan", 65, None)
    if c["status"] == "closing":
        add("closing", "Complete the closing checklist",
            "Permanency reached. Closing checklist pre-fill is a Phase 3 feature; the steps are listed in the case.", "Case status", 70)
    return out


def refresh(ident, case_id):
    """Compute stage and actions, merge with the worker's saved priorities, persist, return ordered list."""
    b = bundle(ident, case_id)
    st, evidence = stage(b)
    cands = actions(b)
    now = datetime.now().isoformat(timespec="seconds")
    keys = set()
    for a in cands:
        keys.add(a["key"])
        db.execute(
            "INSERT INTO case_actions (case_id, key, title, why, source, skill, ui, due_on, score, status, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?, 'open', ?) ON CONFLICT(case_id, key) DO UPDATE SET title=excluded.title, "
            "why=excluded.why, source=excluded.source, skill=excluded.skill, ui=excluded.ui, due_on=excluded.due_on, "
            "score=excluded.score, updated_at=excluded.updated_at",
            (case_id, a["key"], a["title"], a["why"], a["source"], a["skill"], a["ui"], a["due_on"], a["score"], now))
    # Actions whose condition no longer holds are resolved automatically.
    for r in db.rows("SELECT id, key FROM case_actions WHERE case_id=? AND status='open'", (case_id,)):
        if r["key"] not in keys:
            db.execute("UPDATE case_actions SET status='resolved', updated_at=? WHERE id=?", (now, r["id"]))
    return {"stage": {"index": st, "name": STAGES[st], "evidence": evidence}, "actions": ordered(case_id)}


def ordered(case_id):
    rows = db.rows("SELECT * FROM case_actions WHERE case_id=? AND status IN ('open') "
                   "ORDER BY pinned DESC, CASE WHEN pinned=1 THEN rank END ASC, score DESC", (case_id,))
    return rows


def update(ident, case_id, action_id, op):
    if case_id not in ident.case_ids or ident.persona != "caseworker":
        raise gateway.GatewayError("forbidden", "Only the assigned caseworker can change this case's actions.")
    a = db.row("SELECT * FROM case_actions WHERE id=? AND case_id=?", (action_id, case_id))
    if not a:
        raise gateway.GatewayError("not_found", "No such action.")
    now = datetime.now().isoformat(timespec="seconds")
    if op == "pin":
        top = db.row("SELECT COALESCE(MAX(rank), 0) m FROM case_actions WHERE case_id=? AND pinned=1", (case_id,))["m"]
        db.execute("UPDATE case_actions SET pinned=1, rank=?, updated_at=? WHERE id=?", (top + 1, now, action_id))
    elif op == "unpin":
        db.execute("UPDATE case_actions SET pinned=0, rank=0, updated_at=? WHERE id=?", (now, action_id))
    elif op in ("up", "down"):
        pinned = [r["id"] for r in db.rows("SELECT id FROM case_actions WHERE case_id=? AND pinned=1 AND status='open' "
                                            "ORDER BY rank", (case_id,))]
        if action_id in pinned:
            i = pinned.index(action_id)
            j = i - 1 if op == "up" else i + 1
            if 0 <= j < len(pinned):
                pinned[i], pinned[j] = pinned[j], pinned[i]
            for n, pid in enumerate(pinned):
                db.execute("UPDATE case_actions SET rank=? WHERE id=?", (n + 1, pid))
    elif op in ("done", "dismiss"):
        db.execute("UPDATE case_actions SET status=?, pinned=0, updated_at=? WHERE id=?",
                   ("done" if op == "done" else "dismissed", now, action_id))
        db.execute("INSERT INTO case_memory (object_type, object_id, fact, source, created_at) VALUES ('case',?,?,?,?)",
                   (case_id, f"Worker marked '{a['title']}' as {op}.", f"caseworker:{ident.user_id}", now))
    else:
        raise gateway.GatewayError("bad_args", "op must be pin, unpin, up, down, done or dismiss")
    return ordered(case_id)


def list_row(ident, case_id):
    """One row of the caseworker case list: child, age, stage, next due, flags, last visit."""
    b = bundle(ident, case_id)
    st, _ = stage(b)
    c = b["case"]
    dues = [t["due_on"] for t in b["tasks"] if t["status"] == "open"] + [h["on_date"] for h in b["court"] if _days(h["on_date"]) >= 0]
    next_due = min(dues) if dues else None
    next_what = None
    if next_due:
        t = [t["title"] for t in b["tasks"] if t["due_on"] == next_due] + [h["hearing"] for h in b["court"] if h["on_date"] == next_due]
        next_what = t[0] if t else None
    last_visit = b["visits"][0]["on_date"] if b["visits"] else None
    flags = list(c["flags"])
    if last_visit and -_days(last_visit) > VISIT_INTERVAL:
        flags.append("Visit overdue")
    if any(_days(t["due_on"]) < 0 for t in b["tasks"] if t["status"] == "open"):
        flags.append("Overdue task")
    if any(0 <= _days(h["on_date"]) <= 14 for h in b["court"]):
        flags.append("Court soon")
    if any(p["kind"] == "note" for p in b["proposals"]):
        flags.append("Draft to sign")
    if any(v["has_recording"] and v["consent"] and v["note_status"] == "none" for v in b["visits"]):
        flags.append("Recording to write up")
    if "ICWA" not in flags and c["child"].get("icwa", "").startswith("Reason to know"):
        flags.append("ICWA")
    return {"case_id": case_id, "case_no": c["case_no"], "child": c["child"]["name"], "avatar_svg": c["child"]["avatar_svg"],
            "age": c["child"]["age"], "gender": c["child"]["gender"], "stage": {"index": st, "name": STAGES[st]},
            "next_due": next_due, "next_due_what": next_what, "flags": flags, "last_visit": last_visit,
            "days_since_visit": -_days(last_visit) if last_visit else None, "placement": c["placement"],
            "permanency_goal": c["permanency_goal"]}
