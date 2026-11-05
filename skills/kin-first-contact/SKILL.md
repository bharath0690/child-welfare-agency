---
name: kin-first-contact
description: Draft a first-contact message to a relative in plain words and the relative's language, with a person to call, for the caseworker to review before sending. Use when a relative has not been contacted or did not respond.
allowed-tools: case_get, relationships_list, outreach_draft
metadata:
  persona: caseworker
  kind: workflow
  phase: 1
  feature: Kin first-contact message
---
# Kin first-contact message

The first contact is often a shock. The message must be calm, short and clear.

## Steps (workflow: `workflows.first_contact`)
1. `case_get` and `relationships_list`, to get the relative's name and preferred language.
2. Draft the message: who is writing; that the child is in the agency's care and is **safe**; that family matters; the options (stay in touch, care for the child, other support); no pressure to decide today; a named person and phone number.
3. Write it in the relative's language. Machine translations need a bilingual human check before sending.
4. Save with `outreach_draft`. The caseworker reviews it and sends it.

## Never include
The reason for removal, parents' details or anything from the case record beyond the child's first name.

## Reading level
Grade 6 to 8.
