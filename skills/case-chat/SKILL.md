---
name: case-chat
description: Answer a caseworker's free-form question about the open case from the case record, with sources. Use for any question about the open case that another skill does not cover.
allowed-tools: case_get, relationships_list, placements_list, history_list, tasks_list, court_dates_list, visits_list, visit_get, notes_search, referrals_list, plan_get, proposals_list, memory_note
metadata:
  persona: caseworker
  kind: agent
  phase: 1
  feature: Chat with Binti AI
---
# Case chat

An agent loop with tools. Scoped to one case: always pass the open `case_id`.

## Steps
1. Decide which reads answer the question. Prefer structured tools (`tasks_list`, `court_dates_list`) over search.
2. For "what did X say about Y", use `notes_search` and quote the line with its timestamp.
3. Answer in 1 to 5 lines, each with a source.
4. If the worker says "remember…", save it with `memory_note`. It is case-scoped.

## Abstain
If the record doesn't hold the answer, say "I couldn't find that in this case record" and suggest where to look. Never fill gaps from general knowledge about families.
