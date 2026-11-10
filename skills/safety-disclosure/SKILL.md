---
name: safety-disclosure
description: Detect a possible safety disclosure about a child in any family message and escalate immediately to a named human. Runs on every kin and applicant message before the model sees it.
allowed-tools: worker_contact_get
metadata:
  persona: kin, applicant, foster
  kind: guardrail
  phase: 1
  feature: Safety disclosure detection
---
# Safety disclosure

This runs in the runtime **before** any model call (`agent._escalate`). It must work with no model.

## Steps
1. Match the message against the safety patterns (`guardrails.SAFETY_PATTERNS`, English and Spanish).
2. On a match: record an escalation routed to the named worker (`worker_contact_get`), reply with the fixed safety message and stop.
3. The reply thanks them, says who was told, gives "If a child is in immediate danger, call 911 now." and the worker's phone number.

## Rules
- Prefer recall to precision. A human reviews every escalation.
- Never ask probing questions about the incident. That is a trained professional's job.
- Never tell the person the report is confidential or anonymous. That is not ours to promise.

## Eval
Safety recall on red-team scripts. Ship with any family chat.
