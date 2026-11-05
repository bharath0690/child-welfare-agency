"""HTTP API as a plain WSGI app (stdlib only). Vercel's Python runtime serves `app` from api/index.py.

Identity comes from the persona switcher (headers X-Persona and X-User). There is no sign-in in the prototype;
a real deployment swaps this for the agency's identity provider and a scoped token per request.
"""
import json
import re
import traceback
from urllib.parse import parse_qs

from . import agent, db, gateway, llm, stages, workflows

ROUTES = []


def route(method, pattern):
    def deco(fn):
        ROUTES.append((method, re.compile("^" + pattern + "$"), fn))
        return fn
    return deco


class HTTPError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


def ident_of(req):
    persona = req["headers"].get("x-persona") or "caseworker"
    user = req["headers"].get("x-user") or {"caseworker": "cw1", "kin": "kin1", "applicant": "ap1"}.get(persona, "")
    return gateway.Identity.resolve(persona, user)


# --------------------------------------------------------------------------------------------------------
@route("GET", "/api/health")
def health(req):
    return {"ok": True, "mode": "live" if llm.enabled() else "scripted", "model": llm.model_name() if llm.enabled() else None,
            "db": db.db_path(), "seeded_on": db.row("SELECT v FROM meta WHERE k='seeded_on'")["v"]}


@route("GET", "/api/people")
def people(req):
    return {
        "caseworker": [{"id": w["id"], "name": w["name"], "cases": w["n"]} for w in db.rows(
            "SELECT w.id, w.name, COUNT(c.id) n FROM workers w LEFT JOIN cases c ON c.worker_id=w.id WHERE w.role='caseworker' GROUP BY w.id")],
        "kin": [{"id": k["id"], "name": k["name"], "caring_for": k["first"]} for k in db.rows(
            "SELECT k.id, k.name, c.first FROM kin_users k JOIN children c ON c.id=k.child_id")],
        "applicant": [{"id": a["id"], "name": a["household"]} for a in db.rows("SELECT id, household FROM applicants")],
    }


@route("GET", "/api/cases")
def cases(req):
    ident = ident_of(req)
    if ident.persona == "caseworker":
        return {"cases": [stages.list_row(ident, c["case_id"]) for c in gateway.call(ident, "cases_list_assigned")]}
    if ident.persona == "kin":
        ch = gateway.call(ident, "child_details_get")
        return {"cases": [{"case_id": sorted(ident.case_ids)[0], "child": ch["name"], "avatar_svg": ch.get("avatar_svg"), "age": ch["age"]}]}
    return {"cases": []}


@route("GET", r"/api/cases/(?P<case_id>[\w-]+)")
def case_detail(req, case_id):
    ident = ident_of(req)
    if ident.persona == "kin":
        if case_id not in ident.case_ids:
            raise gateway.GatewayError("forbidden", "You can only see the child in your care.")
        return {"view": "kin", "child": gateway.call(ident, "child_details_get"),
                "schedule": gateway.call(ident, "child_schedule_get"), "worker": gateway.call(ident, "worker_contact_get"),
                "hidden_note": "Some details are shared by the caseworker in person, under your agency's rules for caregivers."}
    if ident.persona != "caseworker":
        raise gateway.GatewayError("forbidden", "Case pages are for caseworkers and the child's caregiver.")
    g = lambda t: gateway.call(ident, t, {"case_id": case_id})
    props = g("proposals_list")
    for p in props:
        full = db.row("SELECT payload FROM proposals WHERE id=?", (p["id"],))
        p["payload"] = json.loads(full["payload"])
    return {"view": "caseworker", "case": g("case_get"), "relationships": g("relationships_list"), "placements": g("placements_list"),
            "history": g("history_list"), "tasks": g("tasks_list"), "court": g("court_dates_list"), "visits": g("visits_list"),
            "referrals": g("referrals_list"), "plan": g("plan_get"), "proposals": props,
            "stage": stages.stage(stages.bundle(ident, case_id)), "flags": stages.list_row(ident, case_id)["flags"]}


@route("GET", "/api/briefing")
def briefing(req):
    return workflows.briefing(ident_of(req))


@route("POST", "/api/ai/open")
def ai_open(req):
    b = req["json"]
    with agent.workspace(b.get("workspace")):
        return agent.open_panel(ident_of(req), b.get("object_type", "case"), b.get("object_id"))


@route("POST", "/api/ai/chat")
def ai_chat(req):
    b = req["json"]
    with agent.workspace(b.get("workspace")) as ws:
        out = agent.chat(ident_of(req), b.get("object_type", "case"), b.get("object_id"), b.get("message", ""))
        out["memory_writes"] = ws.memory_writes
        return out


@route("POST", r"/api/cases/(?P<case_id>[\w-]+)/actions/(?P<action_id>\d+)")
def action_update(req, case_id, action_id):
    return {"actions": stages.update(ident_of(req), case_id, int(action_id), req["json"].get("op", ""))}


@route("POST", "/api/workflows/visit-note")
def wf_visit_note(req):
    b = req["json"]
    return workflows.visit_note(ident_of(req), b["case_id"], b["visit_id"])


@route("POST", "/api/workflows/prefill")
def wf_prefill(req):
    b = req["json"]
    return workflows.prefill(ident_of(req), b["case_id"], b["visit_id"])


@route("POST", "/api/workflows/language-check")
def wf_language(req):
    return workflows.language_check(req["json"].get("text", "")[:8000])


@route("POST", "/api/workflows/first-contact")
def wf_first_contact(req):
    b = req["json"]
    return workflows.first_contact(ident_of(req), b["case_id"], b["relationship_id"])


@route("POST", "/api/workflows/inquiry-triage")
def wf_triage(req):
    b = req["json"]
    return workflows.inquiry_triage(b.get("name", ""), b.get("text", "")[:2000], b.get("language"))


@route("POST", "/api/workflows/application-help")
def wf_app_help(req):
    b = req["json"]
    return workflows.application_help(ident_of(req), b.get("field", ""), b.get("notes", "")[:2000])


@route("GET", "/api/application")
def application(req):
    ident = ident_of(req)
    return {"application": gateway.call(ident, "application_get"), "checklist": gateway.call(ident, "checklist_get"),
            "pending": [dict(p, payload=json.loads(p["payload"])) for p in db.rows(
                "SELECT id, kind, payload, summary, status FROM proposals WHERE object_type='application' AND object_id=? AND status='pending'",
                (ident.applicant_id,))]}


@route("POST", r"/api/proposals/(?P<pid>\d+)")
def proposal(req, pid):
    b = req["json"]
    return gateway.decide(ident_of(req), int(pid), b.get("op", ""), b.get("edited"))


@route("GET", "/api/audit")
def audit(req):
    ident = ident_of(req)
    case_id = req["query"].get("case_id", [None])[0]
    if ident.persona != "caseworker" or (case_id and case_id not in ident.case_ids):
        raise gateway.GatewayError("forbidden", "Audit log is visible to the assigned caseworker.")
    if case_id:
        rows = db.rows("SELECT at, persona, user_id, tool, object, fields, decision, reason FROM audit_log WHERE object=? ORDER BY id DESC LIMIT 60", (case_id,))
    else:
        rows = db.rows("SELECT at, persona, user_id, tool, object, fields, decision, reason FROM audit_log WHERE user_id=? ORDER BY id DESC LIMIT 60", (ident.user_id,))
    return {"entries": rows}


# --------------------------------------------------------------------------------------------------------
STATUS = {200: "200 OK", 400: "400 Bad Request", 403: "403 Forbidden", 404: "404 Not Found", 405: "405 Method Not Allowed",
          413: "413 Payload Too Large", 500: "500 Internal Server Error"}
ERR_STATUS = {"forbidden": 403, "not_allowed": 403, "not_found": 404, "unknown_user": 403, "bad_persona": 400, "bad_args": 400, "bad_field": 400}


def app(environ, start_response):
    path = environ.get("PATH_INFO") or "/"
    query = parse_qs(environ.get("QUERY_STRING", ""))
    if path.rstrip("/") in ("/api/index", "/api") and "__p" in query:  # Vercel rewrite fallback
        path = "/api/" + query.pop("__p")[0].lstrip("/")
    method = environ.get("REQUEST_METHOD", "GET").upper()
    headers = {k[5:].replace("_", "-").lower(): v for k, v in environ.items() if k.startswith("HTTP_")}
    try:
        size = int(environ.get("CONTENT_LENGTH") or 0)
        if size > 200_000:
            raise HTTPError(413, "Request too large")
        raw = environ["wsgi.input"].read(size) if size else b""
        body = json.loads(raw) if raw else {}
        if not isinstance(body, dict):
            raise HTTPError(400, "JSON body must be an object")
        for m, rx, fn in ROUTES:
            hit = rx.match(path.rstrip("/") or "/")
            if hit and m == method:
                out, status = fn({"headers": headers, "json": body, "query": query}, **hit.groupdict()), 200
                break
        else:
            raise HTTPError(404 if not any(rx.match(path) for _, rx, _ in ROUTES) else 405, "Not found")
    except gateway.GatewayError as e:
        status, out = ERR_STATUS.get(e.code, 400), {"error": e.message, "code": e.code}
    except HTTPError as e:
        status, out = e.status, {"error": e.message}
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        status, out = 400, {"error": f"Bad request: {e}"}
    except Exception:  # noqa: BLE001 - last-resort handler; details go to the server log only
        traceback.print_exc()
        status, out = 500, {"error": "Something went wrong on our side."}
    data = json.dumps(out, default=str).encode()
    start_response(STATUS.get(status, f"{status} Error"), [("Content-Type", "application/json; charset=utf-8"),
                                                           ("Cache-Control", "no-store"), ("Content-Length", str(len(data)))])
    return [data]
