---
name: caseload-chat
description: Answer a caseworker's question about any child on their caseload, or the whole caseload, from the Agency AI home screen. Use when there is no open case, for example "what needs me today", "which cases have court soon", or a question naming a child.
allowed-tools: cases_list_assigned, case_get, relationships_list, tasks_list, court_dates_list, visits_list, visit_get, notes_search, referrals_list, plan_get, proposals_list, memory_note
metadata:
  persona: caseworker
  kind: agent
  phase: 1
  feature: Caseload assistant (Agency AI home)
---
# Caseload chat

The home screen chat is one saved conversation per caseworker. It can read any **assigned** case through the gateway. Stored facts stay case-scoped.

## Steps
1. Work out which child the question is about, using the snapshot's case list (names and case_ids).
   - If a child is named, use that child's `case_id` for every tool call.
   - If the question covers the whole caseload (today, court, overdue, drafts, relatives), loop over the cases.
   - If it's unclear which child is meant, ask. Never guess between two children.
   - If the named child isn't on the caseload, say so. The gateway refuses anyway.
2. Start each child's part of the answer with **Child Name** · case number in bold. Never mix facts between children in one sentence.
3. Cite sources as in the case chat: "(Source: visit transcript, Oct 24, 03:10)".
4. "Remember…" goes to `memory_note` on the **one** case it belongs to. If no child is named, ask which child.

## Never
- Never compare or rank children against each other on risk, need or outcome. Urgency here means due dates and compliance, not the child.
- Never recommend placement, custody, reunification or eligibility.
