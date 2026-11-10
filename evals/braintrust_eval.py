"""Run the golden set as a Braintrust experiment.

    python3 evals/braintrust_eval.py            # scripted mode, results sent to Braintrust
    python3 evals/braintrust_eval.py --live     # chat cases call the model (DEEPSEEK_API_KEY)
    python3 evals/braintrust_eval.py --local    # run with the Braintrust SDK but send nothing

Needs `pip install braintrust` and BRAINTRUST_API_KEY (except with --local). The project is BRAINTRUST_PROJECT,
default "binti-ai-prototype". Cases, checks and pass rules are the same as evals/run_evals.py, so both runners
always agree. Each case is tagged with its persona, severity and, for evidence-based cases, the public source.

Scores per case:
  golden_pass         1 if every check in the case passed
  critical_gate       1 or 0 on critical cases only (the release gate); blank on other cases
  <persona>_pass      the same pass score, split by persona group so each one gets its own pass bar (architecture section 7)
  helpfulness         LLM judge, chat cases only (evals/judges.py). Rubric read from AGENTS.md "Helpful and kind"
  politeness_empathy  LLM judge, chat cases only, same rubric plus the persona's Tone line
The judges use Claude when ANTHROPIC_API_KEY is set (pip install -r evals/requirements.txt), else DeepSeek with
JUDGE_API_KEY or DEEPSEEK_API_KEY; without a key their scores are left blank. --no-judge skips them.

Exit code 1 if any critical case fails.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evals"))
# Keep the key for the judges before run_evals drops DEEPSEEK_API_KEY (scripted mode must not call the model for answers)
NO_JUDGE = "--no-judge" in sys.argv
JUDGE_KEY = os.environ.get("JUDGE_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
import run_evals  # noqa: E402  (also drops DEEPSEEK_API_KEY unless --live)
import judges  # noqa: E402

import braintrust  # noqa: E402

PROJECT = os.environ.get("BRAINTRUST_PROJECT", "binti-ai-prototype")
LOCAL = "--local" in sys.argv
LIVE = "--live" in sys.argv
GROUP = {"caseworker": "caseworker", "kin": "kin", "applicant": "parent", "foster": "parent"}


def group(case):
    return GROUP.get(case.get("persona"), "shared")


def load():
    cases = json.loads((ROOT / "evals" / "golden.json").read_text())["cases"]
    return [{
        "input": c,
        "expected": c["expect"],
        "metadata": {"id": c["id"], "persona": c.get("persona", "none"), "group": group(c), "category": c["category"],
                     "severity": c["severity"], "type": c["type"], "evidence": c.get("evidence"), "why": c["why"]},
        "tags": [group(c), c["severity"]] + (["evidence"] if c.get("evidence") else []),
    } for c in cases]


def task(case):
    try:
        errs, got = run_evals.run_case(case)
    except Exception as ex:  # noqa: BLE001 - a crash is a failed case, not a failed run
        errs, got = [f"crashed: {type(ex).__name__}: {ex}"], None
    return {"errors": errs, "got": got if isinstance(got, (str, dict, list)) else str(got)}


def golden_pass(input, output, expected):
    return braintrust.Score(name="golden_pass", score=0 if output["errors"] else 1,
                            metadata={"errors": output["errors"]} if output["errors"] else None)


def critical_gate(input, output, expected):
    if input["severity"] != "critical":
        return None
    return 0 if output["errors"] else 1


def persona_pass(input, output, expected):
    return braintrust.Score(name=f"{group(input)}_pass", score=0 if output["errors"] else 1)


def _judged(metric, input, output):
    if input["type"] != "chat" or NO_JUDGE or judges.provider(JUDGE_KEY) is None or not isinstance(output.get("got"), str):
        return None
    r = judges.judge(metric, input.get("persona"), input["input"], output["got"], context=input.get("why"), api_key=JUDGE_KEY)
    return None if r is None else braintrust.Score(name=metric, score=r["score"], metadata={"grade": r["grade"], "reason": r["reason"]})


def helpfulness(input, output, expected):
    return _judged("helpfulness", input, output)


def politeness_empathy(input, output, expected):
    return _judged("politeness_empathy", input, output)


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or None
    except OSError:
        return None


def main():
    if not LOCAL and not os.environ.get("BRAINTRUST_API_KEY"):
        sys.exit("BRAINTRUST_API_KEY is not set. Set it, or run with --local to try the SDK without sending results.")
    mode = "live" if LIVE else "scripted"
    result = braintrust.Eval(
        PROJECT,
        experiment_name=f"golden-{mode}-{git_commit() or 'local'}",
        data=load,
        task=task,
        scores=[golden_pass, critical_gate, persona_pass, helpfulness, politeness_empathy],
        metadata={"mode": mode, "golden_set": "evals/golden.json", "commit": git_commit(), "judge_model": None if NO_JUDGE else judges.model_label(JUDGE_KEY)},
        max_concurrency=1,  # each case reseeds one shared in-memory database
        no_send_logs=LOCAL,
    )
    failed = [r for r in result.results if r.output and r.output["errors"]]
    for r in failed:
        print(f"FAIL  {r.input['severity']:<8} {r.input['id']:<34} {'; '.join(r.output['errors'])}")
    crit = [r.input["id"] for r in failed if r.input["severity"] == "critical"]
    n = len(result.results)
    print(f"\n{n - len(failed)}/{n} passed. Critical failures: {', '.join(crit) or 'none'}")
    sys.exit(1 if crit else 0)


if __name__ == "__main__":
    main()
