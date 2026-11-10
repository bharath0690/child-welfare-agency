---
name: court-report-assembly
description: Assemble a court report draft from cited facts in the case record (placement, visits, signed notes, plan progress, services, efforts to find relatives) for an upcoming hearing. Use when a hearing is within two weeks or the worker asks for help with a court report. The worker writes the recommendation.
allowed-tools: case_get, court_dates_list, visits_list, plan_get, referrals_list, relationships_list, placements_list, court_report_draft
metadata:
  persona: caseworker
  kind: workflow
  phase: 1
  feature: Court report assembly (moved to Phase 1)
---
# Court report assembly

Preparing court reports is one of the heaviest documentation loads in the evidence, often done the night before. This workflow takes the gathering work off the worker. The judgment stays with them.

## Steps (workflow: `workflows.court_report`)
1. `court_dates_list`: confirm the hearing and its date.
2. Gather the facts: `case_get`, `placements_list`, `visits_list`, the last three signed notes, `plan_get`, `referrals_list` and `relationships_list`.
3. Write the report in fixed sections:
   1. Placement
   2. Visits since the last hearing
   3. From signed visit notes
   4. Case plan progress
   5. Services and referrals
   6. Efforts to find and engage relatives
   7. Recommendation
4. Every line ends with its source.
5. Section 7 is always the placeholder "[Written by the caseworker…]". Never fill it in.
6. Save the draft with `court_report_draft`. The worker edits it, writes the recommendation and signs. Approving it marks the report "ready to file".

## Never
- No recommendation on placement, custody, reunification, termination or adoption.
- No characterization of the parents. State facts with sources.
