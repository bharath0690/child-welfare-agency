---
name: status-explainer
description: Explain where a family's process is up to (licensing checklist, kin approval or adoption steps), who holds each pending item, since when, how long it usually takes, and what happens if a message goes unanswered. Use for "why is this taking so long", "where is my approval", "who has it" or "I'm not hearing back".
allowed-tools: checklist_get, application_get, approval_status_get, adoption_status_get, messages_get, contacts_get, worker_contact_get
metadata:
  persona: applicant, kin, foster
  kind: agent
  phase: 1
  feature: Status and timeline explainer (moved to Phase 1)
---
# Status explainer

The most consistent complaint from prospective parents is not hearing back. The next is waiting without knowing why. Answer both with facts from the record.

## Steps
1. Read the right list for the persona:
   - Applicant: `checklist_get`
   - Kin caregiver: `approval_status_get`
   - Foster parent: `adoption_status_get`
2. For each pending item, give the status, **who holds it**, since when, and the usual range. If it is past its usual range, say it has been flagged to the supervisor.
3. For kin, give the day count since placement, the agency target (90 days in the prototype) and the national average of about 160 days. Then point to help available now (skill: `caregiver-support`).
4. If they mention silence, use `messages_get`:
   - Waiting: name the worker and the reply deadline.
   - Past the deadline: name the supervisor it went to, with their phone.
   - Then use `contacts_get` for the rest of the list.

## Never
- Never predict an approval, a court date or an adoption date.
- Never blame the family or the worker. State who holds what.
