# AI architecture (target design, v1)

Source: the "Binti AI architecture" doc written on 4 Nov 2026. This file is the repo copy so Claude Code can work from it. The owner has suggestions to add. Treat this as a draft to revise, not a fixed spec. Binti's real AI implementation is unknown, so validate with engineering.

## Decision
One Binti AI platform with **three persona-scoped agents** (Caseworker, Applicant, Kin) on one shared runtime, plus **shared specialist sub-agents and workflows**.
- Split by who is asking (permissions, trust, tone). Share by what needs doing (law lookup, translation, drafting, safety).
- Rejected: one big agent (permissions live in prompt text the model can be talked out of) and three separate agents (law, translation and safety logic built three times, answers drift).
- Fixed-step, high-stakes work = deterministic **workflow** with model calls inside (visit capture, form pre-fill, court report). Open-ended Q&A = **agent loop** with tools.
- Revisit when a fourth persona (supervisor, court, provider) arrives.

## Shared specialists
Law and policy Q&A, Case questions, Visit capture, Form pre-fill, Report drafting, Family finding, Translation, Document intake, Safety handoff.

## Harness (14 components)
Identity and authorization context, context assembly, hybrid RAG (law and policy), hybrid RAG (case record), tool gateway (MCP), workflow engine, speech to text, translation, memory (case-scoped, nothing across cases), guardrails (input, retrieval, output, action), human in the loop, model gateway, audit and observability, evals.

## Hybrid RAG
- Corpora: law and policy (federal floor: ASFA, ICWA, Title IV-E, Fostering Connections, FFPSA, CAPTA; state statute and regs; court rules; ICPC; agency policy), program and provider content, case record. Law list is from general knowledge: counsel must confirm per jurisdiction.
- Pipeline: filter first (jurisdiction, effective date, audience, permissions) -> persona query rewrite with glossary -> BM25 + vector with reciprocal rank fusion -> cross-encoder rerank -> return parent section -> follow statute/regulation/policy links -> compose with citations or abstain.
- Do not embed what you can query (appointments, tasks, statuses come from tools).
- Explain, do not give legal advice. Golden question set per jurisdiction, written with counsel.

## Tool calling
Gateway wraps each Binti module as an MCP server. Per call: exchange the user session for a scoped token, check the persona allowlist, filter fields by a **disclosure policy matrix** (field x persona x agency setting), log. Writes create proposals a human approves.
- Caseworker: read case summary, notes search, tasks, court dates, genogram, referral status, providers, external record search. Draft: note, form pre-fill, task, outreach, court report, referral, visit.
- Applicant: read own status, checklist, trainings, visit slots. Draft: application field, upload, book slot, request references (after family confirms who).
- Kin: read child schedule, allowed child details, worker contact, benefit options. Draft: benefit application, message worker, callback, report a concern.
- Never: other families' data, parents' records, reporter identity, placement changes, eligibility or approval decisions.

## Features by persona and phase
Phase 0: gateway, authorization context, audit log, eval harness, safety disclosure detection.
Phase 1 Caseworker: day briefing, case summary, case chat, visit transcription, note drafting, form pre-fill with provenance, language and bias check. Family: parent guide Q&A, inquiry triage, application assistant, kin first-contact message, kin decision guide, child schedule lookup.
Phase 2: law and policy Q&A, family finding, outreach translation, court report assembly, plan builder and referral matching, document intake, reference automation, home study drafting, status explainer, benefits navigator, approval checklist reuse, everyday care assistant, strain and support triage.
Phase 3: compliance data watcher, closing checklist pre-fill, placement call explainer, long-term path explainer, agency drop-off analytics.

## Guardrails and evals
Guardrails at input (injection, PII, safety disclosure), retrieval (permissions, jurisdiction, date), output (citation required, no legal advice, no placement/custody/eligibility/risk decisions, fault-language check, reading level), action (draft only, approval, rate limits).
Evals: draft accuracy, edit distance, fault-language catch rate, citation accuracy, abstain rate, translation quality, safety recall, time saved.

## Non-goals
No predictive risk scoring. No AI decision on placement, custody, eligibility or approval. No recording without consent. No AI text to a court without worker sign-off. No training on case data.

## Open questions
1. Are caregiver chats part of the discoverable case record? 2. Who owns the disclosure policy matrix per agency? 3. Data residency and model vendor terms per state, and Canada and Australia. 4. Who curates the law corpus? 5. Which confidentiality rules apply to the data (state child welfare, education, health)? 6. Does Binti's existing AI work already fix choices (model provider, chat surface)?
