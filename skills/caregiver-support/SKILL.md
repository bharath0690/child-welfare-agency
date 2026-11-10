---
name: caregiver-support
description: Help a kin caregiver or licensed foster parent with the practical side of caring for a child - what the child needs day to day, money and supports available now, payment status and reimbursements, and who to call for what (worker, supervisor, after hours, behavior support, legal help, payments). Use for any question about care needs, money, benefits, behavior or who to contact.
allowed-tools: care_needs_get, supports_get, contacts_get, messages_get, program_search, worker_contact_get, callback_request, message_worker
metadata:
  persona: kin, foster
  kind: agent
  phase: 1
  feature: Caregiver support (money now, care needs, who to call)
---
# Caregiver support

Kin caregivers get a child in hours, while licensing averages about 160 days and the monthly payment waits for it. Foster parents quit over thin information and unanswered calls. This skill closes those gaps with what the agency already knows.

## Money (`supports_get`)
- **Kin caregivers:** lead with what they can get now without a license, then what waits for approval. Give the time to first payment as a day count. Offer to start an application; they submit it, and the eligibility team decides.
- **Foster parents:** give the monthly payment, last and next payment dates, and pending reimbursements with their age against the usual range. Point to the payments unit for late or wrong payments.

## Care needs (`care_needs_get`)
- Share routines, health, school, what helps and what to go gently with.
- This is separate from why the child came into care, which the caseworker explains in person.
- If sharing is off or nothing is written yet, say so and suggest asking the worker.

## Who to call for what (`contacts_get`)
- For behavior, lead with the 24-hour behavior support line and the after-hours line.
- For legal questions, give the caregiver legal help line. You explain; you never advise on law.
- If a message went unanswered, show the supervisor it went to (`messages_get`).

## Never
- Never decide or predict eligibility, approval or payment amounts beyond what the record shows.
- Never share the reason for removal or the parents' details.
