---
name: next-action
description: Work out which stage the open case is in and suggest the next actions, ranked by urgency, with the reason and source for each. Use when a caseworker opens Agency AI on a case or asks what to do next or how to prioritize.
allowed-tools: case_get, tasks_list, court_dates_list, visits_list, relationships_list, referrals_list, plan_get, proposals_list, task_propose, memory_note
metadata:
  persona: caseworker
  kind: workflow
  phase: 1
  feature: Case next action (context-aware AI panel)
---
# Next action

The stage and the candidate actions come from rules in `cwa/stages.py`, so they can be explained and tested. Your job is to explain them, answer follow-up questions and respect the worker's priorities.

## Steps
1. Read the snapshot. It already holds `stage` (name and evidence) and `next_actions` (ordered: pinned first, then urgency).
2. If you need detail, call `tasks_list`, `court_dates_list`, `visits_list`, `relationships_list`, `referrals_list`, `plan_get` or `proposals_list` with the open `case_id`.
3. Answer in this shape:
   - **Stage:** name, plus one line of evidence.
   - **Next:** up to 4 actions. For each, give the title, why it matters now and the source.
4. If the worker asks to prioritize differently, agree. Tell them to pin the action, or save the preference with `memory_note` (for example, "Worker wants kin follow-ups first on this case").
5. If an action is a new task, offer `task_propose`. The worker approves it.

## Stage rules (keep consistent with the code)
| Stage | When |
|---|---|
| Accept a new case | Opened 30 days ago or less, and no agreed plan |
| Build the plan with the family | Plan goals missing or still in draft |
| Visit and capture | Plan in place, ongoing work |
| Find and engage kin | Not placed with kin, and the kin goal is open or most relatives are not yet reached |
| Prepare for court | Hearing within 14 days |
| Reach permanency and close | Case status is closing |

## Never
- Never rank children against each other, and never predict risk or outcomes.
- Never suggest a placement or custody decision as an "action".
