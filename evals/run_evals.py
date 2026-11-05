"""Run the golden eval set against a fresh seeded database.

    python3 evals/run_evals.py            # scripted mode (no model), deterministic
    python3 evals/run_evals.py --live     # uses DEEPSEEK_API_KEY for chat cases
    python3 evals/run_evals.py --json     # machine-readable results

Exit code 1 if any critical case fails (use it as a release gate).
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if "--live" not in sys.argv:
    os.environ.pop("DEEPSEEK_API_KEY", None)

from binti import agent, db, gateway, guardrails, stages, workflows  # noqa: E402

G = gateway


def ident(c):
    return G.Identity.resolve(c["persona"], c["user"])


def text_checks(text, e, errs):
    low = (text or "").lower()
    for s in e.get("include_all", []) + e.get("body_include_all", []) + e.get("draft_include_all", []):
        if s.lower() not in low:
            errs.append(f"missing {s!r}")
    if e.get("include_any") and not any(s.lower() in low for s in e["include_any"]):
        errs.append(f"none of {e['include_any']}")
    for s in e.get("exclude_all", []) + e.get("body_exclude_all", []) + e.get("draft_exclude_all", []):
        if s.lower() in low:
            errs.append(f"contains forbidden {s!r}")


def run_case(c):
    db.reset_for_tests(":memory:")
    e, errs, got = c["expect"], [], ""
    t = c["type"]
    if t == "chat":
        out = agent.chat(ident(c), "case" if c["persona"] != "applicant" else "application", c.get("object_id"), c["input"])
        meta, got = out["meta"], out["reply"]
        if "escalated" in e and bool(meta.get("escalated")) != e["escalated"]:
            errs.append(f"escalated={bool(meta.get('escalated'))}")
        text_checks(got, e, errs)
        for f in e.get("flags_include", []):
            if f not in meta.get("flags", []):
                errs.append(f"flag {f} missing")
        for f in e.get("flags_exclude", []):
            if f in meta.get("flags", []):
                errs.append(f"flag {f} present")
        for tool in e.get("tools_include", []):
            if tool not in meta.get("tools", []):
                errs.append(f"tool {tool} not used")
    elif t == "gateway":
        try:
            res = G.call(ident(c), c["tool"], c["args"])
            got = json.dumps(sorted(res.keys()) if isinstance(res, dict) else res)[:200]
            if "error_code" in e:
                errs.append(f"expected error {e['error_code']}, call succeeded")
            for f in e.get("fields_exclude", []):
                if f in res:
                    errs.append(f"leaked field {f}")
            for f in e.get("fields_include", []):
                if f not in res:
                    errs.append(f"missing field {f}")
        except G.GatewayError as ex:
            got = ex.code
            if ex.code != e.get("error_code"):
                errs.append(f"error {ex.code}")
    elif t == "output_guard":
        got, flags = guardrails.check_output(c["text"], c["persona"])
        for f in e.get("flags_include", []):
            if f not in flags:
                errs.append(f"flag {f} missing")
    elif t == "workflow":
        a, w = dict(c.get("args", {})), c["workflow"]
        if "visit" in a:
            q = "SELECT id FROM visits WHERE case_id=? " + ("AND transcript IS NOT NULL " if a["visit"] == "recorded" else "") + "ORDER BY on_date DESC"
            a["visit_id"] = db.row(q, (a["case_id"],))["id"]
            del a["visit"]
        if "relative" in a:
            a["relationship_id"] = db.row("SELECT id FROM relationships WHERE name=?", (a.pop("relative"),))["id"]
        if w == "language_check":
            out = workflows.language_check(a["text"])
            got = [f["phrase"].lower() for f in out["findings"]]
            if got != e["phrases_equal"]:
                errs.append(f"phrases {got}")
        elif w == "inquiry_triage":
            out = workflows.inquiry_triage(a["name"], a["text"])
            got = out["acknowledgement"]
        else:
            fn = {"visit_note": workflows.visit_note, "prefill": workflows.prefill, "first_contact": workflows.first_contact,
                  "application_help": workflows.application_help}[w]
            out = fn(ident(c), **a)
            got = out.get("body") or out.get("draft") or out.get("error") or ""
        if isinstance(out, dict):
            if "error_contains" in e and e["error_contains"] not in (out.get("error") or ""):
                errs.append(f"no error containing {e['error_contains']!r}")
            if "error_contains" not in e and out.get("error"):
                errs.append(f"error: {out['error']}")
            for k, v in e.get("field_equals", {}).items():
                if out.get(k) != v:
                    errs.append(f"{k}={out.get(k)!r}")
            for k, spec in e.get("fields", {}).items():
                f = out.get("fields", {}).get(k, {})
                if "value" in spec and f.get("value") != spec["value"]:
                    errs.append(f"{k}.value={f.get('value')!r}")
                if spec.get("quote_required") and not f.get("quote"):
                    errs.append(f"{k} has no quote")
                if "quote_contains" in spec and spec["quote_contains"] not in (f.get("quote") or ""):
                    errs.append(f"{k}.quote={f.get('quote')!r}")
                if "confidence" in spec and f.get("confidence") != spec["confidence"]:
                    errs.append(f"{k}.confidence={f.get('confidence')}")
            if w != "language_check":
                text_checks(got if isinstance(got, str) else "", e, errs)
    elif t == "stage":
        i = ident(c)
        got = {cid: stages.stage(stages.bundle(i, cid))[0] for cid in e["stages"]}
        errs += [f"{cid}: {got[cid]} != {v}" for cid, v in e["stages"].items() if got[cid] != v]
    elif t == "next_action":
        i, got = ident(c), {}
        for cid, s in e.get("first_action_contains", {}).items():
            acts = stages.refresh(i, cid)["actions"]
            got[cid] = acts[0]["title"] if acts else None
            if not acts or s.lower() not in acts[0]["title"].lower():
                errs.append(f"{cid} first action: {got[cid]!r}")
        for cid, s in e.get("actions_include", {}).items():
            titles = [a["title"] for a in stages.refresh(i, cid)["actions"]]
            if not any(s.lower() in x.lower() for x in titles):
                errs.append(f"{cid} has no action like {s!r}")
    elif t == "memory":
        i = ident(c)
        agent.chat(i, "case", c["save_on"], c["input"])
        saved = bool(agent.memory(("case", c["save_on"])))
        leaked = bool(agent.memory(("case", c["check_absent_on"])))
        got = {"saved": saved, "leaked": leaked}
        if not saved:
            errs.append("not saved")
        if leaked:
            errs.append("memory leaked to another case")
    return errs, got


def main():
    cases = json.loads((ROOT / "evals" / "golden.json").read_text())["cases"]
    results = []
    for c in cases:
        try:
            errs, got = run_case(c)
        except Exception as ex:  # noqa: BLE001 - an eval crash is a failure, not a runner crash
            errs, got = [f"crashed: {type(ex).__name__}: {ex}"], None
        results.append({"id": c["id"], "severity": c["severity"], "category": c["category"], "passed": not errs, "errors": errs,
                        "got": got if isinstance(got, (str, dict, list)) else str(got)})
    if "--json" in sys.argv:
        print(json.dumps(results, indent=2, default=str))
    else:
        for r in results:
            print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['severity']:<8} {r['id']:<34} {'; '.join(r['errors'])}")
        n = sum(r["passed"] for r in results)
        crit = [r["id"] for r in results if not r["passed"] and r["severity"] == "critical"]
        print(f"\n{n}/{len(results)} passed. Critical failures: {', '.join(crit) or 'none'}")
    sys.exit(1 if any(not r["passed"] and r["severity"] == "critical" for r in results) else 0)


if __name__ == "__main__":
    main()
