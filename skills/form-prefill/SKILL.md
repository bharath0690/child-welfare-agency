---
name: form-prefill
description: Pre-fill the monthly caseworker visit form from a consented visit transcript, showing the source quote and a confidence level for each field. Use after visit capture, or when the worker asks to fill the visit form.
allowed-tools: visit_get, form_prefill_draft
metadata:
  persona: caseworker
  kind: workflow
  phase: 1
  feature: Form pre-fill with provenance
---
# Form pre-fill

## Steps (workflow: `workflows.prefill`)
1. `visit_get` (consent required).
2. For each field, find the supporting line. Record `value`, `quote`, `ts`, `source` and `confidence` (high, medium or low).
   - Fields: visit_date, location, persons_present, recording_consent, child_seen_alone, school_update, health_update, child_reports_feeling_safe, services_discussed, next_visit.
3. When there is no supporting line, the value is empty and confidence is low. Never guess.
4. Save with `form_prefill_draft`. The worker reviews it, and low-confidence fields need their input.

## Rule
A value with no quote must come from structured data (the visit log) and say so.
