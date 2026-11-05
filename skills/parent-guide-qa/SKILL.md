---
name: parent-guide-qa
description: Answer a prospective foster or adoptive parent's questions about steps, requirements and timelines in plain words, from the agency guide, with sources. Use for any 'how does this work' question from an applicant.
allowed-tools: program_search, application_get, checklist_get, worker_contact_get
metadata:
  persona: applicant
  kind: agent
  phase: 1
  feature: Plain-language guide and Q&A
---
# Parent guide Q&A

## Steps
1. `program_search` with the question in plain words. It is filtered to applicant content.
2. If the question is about *their* progress, use `application_get` or `checklist_get` instead.
3. Answer in 3 to 6 short sentences: the step in plain words, what it asks of the family, then who to call (`worker_contact_get`).
4. Cite the guide: "(Source: Cedar County caregiver guide: Background checks)".

## Rules
- Never predict approval or give dates the system doesn't hold.
- If the guide doesn't cover it, say so and give the worker's contact.
- Normalize nerves about the home study and background checks.
