---
name: language-check
description: Flag fault-assigning or stigmatizing wording in a caseworker's note and suggest neutral, factual rewrites grounded in what was said or seen. Use on any draft or note before signing.
allowed-tools: visit_get
metadata:
  persona: caseworker
  kind: workflow
  phase: 1
  feature: Language and bias check
---
# Language and bias check

Deterministic first pass in `guardrails.language_check`. The worker decides what to change.

## What gets flagged (examples)
| Phrase | Suggest | Why |
|---|---|---|
| noncompliant | has not yet completed [step] | Labels the person |
| refused to | did not / said they would not | Assigns intent |
| failed to | did not | Assigns fault |
| claims that | said that | Casts doubt |
| dirty home | describe observable conditions | Subjective |
| addict | person who uses substances | Person-first |

## Steps
1. Run the check and list each finding: the phrase, the suggestion and the reason.
2. If the worker asks for a rewrite, ground it in the transcript (`visit_get`). Never invent facts to replace an opinion.
3. Never auto-change signed records.

## Eval
Catch rate and false alarms against a supervisor-labeled set.
