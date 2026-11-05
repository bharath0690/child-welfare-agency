---
name: case-summary
description: Summarize a case for handoff or a quick catch-up: who the child is, placement, goal, stage, recent visits, court, relatives and open items. Every line has a source. Use when asked to summarize, give an overview or catch up.
allowed-tools: case_get, placements_list, history_list, visits_list, court_dates_list, relationships_list, tasks_list, referrals_list, notes_search
metadata:
  persona: caseworker
  kind: agent
  phase: 1
  feature: Case summary on handoff
---
# Case summary

## Steps
1. `case_get`, for child, case, placement and goal.
2. `history_list`, `visits_list`, `court_dates_list`, `relationships_list`, `tasks_list` and `referrals_list`, for the recent picture.
3. Use `notes_search` only for specific questions the summary raises.
4. Write 6 to 8 lines in this order: who; why open (as recorded); where placed and since when; goal and stage; last visit and next hearing; relatives reached out of identified; open items.

## Rules
- A source on every line: "(Source: placements)".
- Use the reason for removal exactly as recorded. Never add judgment.
- If something is unknown, write "not recorded". Never guess.
