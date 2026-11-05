---
name: inquiry-triage
description: Classify a new foster, adoption or kin inquiry by language, intent and urgency, route it to a named worker, and send an acknowledgement. Use when a family submits an inquiry.
allowed-tools: program_search
metadata:
  persona: applicant
  kind: workflow
  phase: 1
  feature: Inquiry triage and routing
---
# Inquiry triage

A deterministic workflow (`workflows.inquiry_triage`). It runs on a public form, so it holds no case data.

## Steps
1. Run the safety check on the text. If it describes a child at risk, set urgency to "urgent: safety", escalate to the intake duty worker and include the 911 line.
2. Detect the language (reply in it).
3. Set the intent: foster, adoption, respite, kinship or general question.
4. Route it: licensing intents go to the licensing worker, and kinship goes to the intake duty worker.
5. Send an acknowledgement that names who will contact them and when.

## Never
Never promise eligibility or approval.
