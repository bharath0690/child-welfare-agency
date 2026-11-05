---
name: day-briefing
description: Build the caseworker's start-of-day briefing across all assigned cases, ranked by urgency, with one tap to open each case. Use when the worker opens the case list or asks what matters today.
allowed-tools: cases_list_assigned, tasks_list, court_dates_list, visits_list, proposals_list
metadata:
  persona: caseworker
  kind: workflow
  phase: 1
  feature: Start-of-day briefing
---
# Day briefing

A deterministic workflow (`workflows.briefing`). It runs the next-action rules on each assigned case and merges the top items.

## Steps
1. `cases_list_assigned`, to get the cases.
2. For each case, take the top two next actions (the next-action skill). Pinned items get a boost.
3. Sort everything by urgency score and keep the top 6.
4. Write one short summary line: number of cases, court within two weeks, and the single most important item.
5. Show the time-back figure from **telemetry** (signed AI-drafted notes multiplied by the baseline minutes). Never generate this number with a model.

## Output
- A greeting by first name, then the summary line.
- The items: child, action, why, source.
- Time back this period, labeled as illustrative.

## Never
- No scores, streaks or rankings tied to child outcomes.
