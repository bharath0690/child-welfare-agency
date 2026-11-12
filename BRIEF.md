# Brief for Claude Code

**Goal.** Share an externally viewable prototype of the three priority Child Welfare Agency journeys (caseworker, prospective foster/adoptive parent, kin caregiver), plus the licensed foster parent after placement, with AI features. Deployed on Vercel from Git. No viewer sign-in.

**Status.** v0.2: working prototype. There are two parts:
- **Journeys:** the original 21 concept screens (vanilla JS, `data.js`).
- **Cases workspace:** a Python stdlib API over SQLite with mock data (`cwa/`, `api/index.py`). It has a case list, case and child pages, and a context-aware Agency AI panel.

AI runs scripted by default and goes live with `DEEPSEEK_API_KEY`. See `README.md`.

**Principles**
- Human-led AI: every draft carries an "Agency AI draft" banner; the worker or family reviews and signs. AI never drafts placement or custody recommendations.
- Consent before recording. Language check flags fault-assigning wording (caseworker visit note).
- Relief before reward: give caseworkers time back first; recognition is named work, never scores or rankings tied to child outcomes.
- Families always know who holds each step, who to call, and when they will hear back (reply deadline with supervisor escalation).
- Fictional data only. Not an official product of any agency or vendor.

**Front end.** `cases.js` renders the Cases tab (routes `#/cases`, `#/case/<id>`, `#/application`). `H` (app.js) holds state `S`, `H.SCR[persona][stage]` renderers, `H.ACT` click actions via `data-act`/`data-arg`, `H.CHATS` scripted chats, `H.rate` rating buttons that feed the AI quality drawer.

**AI architecture.** The full target AI architecture (all tables plus the diagram) is in `docs/ai-architecture.md`. It is the source of truth for AI work in this repo. The persona canvas is in `canvas/index.html`.

**Agent.** `AGENTS.md` defines the core agent and four persona profiles. `skills/*/SKILL.md` holds 18 skills (Phase 1 plus `caseload-chat`). Caseworkers land on the Agency AI home (`#/home`), a full-screen chat over their whole caseload. Chats and memories are kept per viewer in a browser workspace (`#/workspace`). The Journey study and AI quality tools sit in the top-right "Internal use" menu. Every tool call goes through `cwa/gateway.py`.

**Next**
1. Evals: the 49-case golden set is in `evals/` (49/49 pass). It includes evidence-based cases for each priority persona, each naming its public source. Next, add law citation and abstain sets with counsel, bilingual translation review, and edit distance from real signed notes.
2. Real speech to text for visit capture. Transcripts are seeded today.
3. Phase 2: law and policy RAG (vector half and corpus), plan builder. (Court report assembly moved to Phase 1 and is built.)
4. SMS channel for kin (Phase 1 in the design; needs a messaging provider). Counsel sign-off on care-needs sharing.
5. Persistence on Vercel (a hosted database) and rate limits per user.
6. Review the three drilldown journeys and the Cases workspace with the owner.
7. Braintrust: production traces (`cwa/observability.py`) and eval experiments (`evals/braintrust_eval.py`, CI) are wired. They turn on with `BRAINTRUST_API_KEY` in Vercel and as a GitHub secret.
