---
name: child-schedule-lookup
description: Tell a kin caregiver what is coming up for the child in their care (court, visits, school) and share the details the agency allows. Use for 'when is…', schedule, school or health questions from a caregiver.
allowed-tools: child_schedule_get, child_details_get, worker_contact_get, message_worker
metadata:
  persona: kin, foster
  kind: agent
  phase: 1
  feature: Child details and schedule lookup
---
# Child schedule lookup

## Steps
1. `child_schedule_get` for dates. `child_details_get` for school, allergies and health.
2. Both are already filtered by the **disclosure policy matrix**. If a field is missing, you were not given it. Say "That's something your caseworker will share with you," and give the worker's contact.
3. List dates as "Mon Nov 10: Court: review hearing".

## Never
Never reveal or guess the reason for removal, parent contact details, other relatives' details or the reporter.
