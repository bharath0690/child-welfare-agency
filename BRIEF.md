# Brief for Claude Code

**Goal.** Share an externally viewable prototype of the three priority Binti journeys (caseworker, prospective foster/adoptive parent, kin caregiver) with AI features. Deployed on Vercel from Git. No viewer sign-in.

**Status.** v0.2: working prototype. There are two parts:
- **Journeys:** the original 21 concept screens (vanilla JS, `data.js`).
- **Cases workspace:** a Python stdlib API over SQLite with mock data (`binti/`, `api/index.py`). It has a case list, case and child pages, and a context-aware Binti AI panel.

AI runs scripted by default and goes live with `DEEPSEEK_API_KEY`. See `README.md`.

**Principles**
- Human-led AI: every draft carries a "Binti AI draft" banner; the worker or family reviews and signs. AI never drafts placement or custody recommendations.
- Consent before recording. Language check flags fault-assigning wording (caseworker visit note).
- Reward with time and progress, never scores or rankings tied to child outcomes.
- Fictional data only. Not an official Binti product.

**Front end.** `cases.js` renders the Cases tab (routes `#/cases`, `#/case/<id>`, `#/application`). `H` (app.js) holds state `S`, `H.SCR[persona][stage]` renderers, `H.ACT` click actions via `data-act`/`data-arg`, `H.CHATS` scripted chats, `H.rate` rating buttons that feed the AI quality drawer.

**AI architecture.** The full target AI architecture (all tables plus the diagram) is in `docs/ai-architecture.md`. It is the source of truth for AI work in this repo. The persona canvas is in `canvas/index.html`.

**Agent.** `AGENTS.md` defines the core agent and three persona profiles. `skills/*/SKILL.md` holds 15 skills (Phase 1 plus `caseload-chat`). Caseworkers land on the Binti AI home (`#/home`), a full-screen chat over their whole caseload. Every tool call goes through `binti/gateway.py`.

**Next**
1. Evals: the 25-case golden set is in `evals/` (24/25 pass; T1 needs a plain-language rewrite of the kin guide content). Next, add law citation and abstain sets with counsel, bilingual translation review, and edit distance from real signed notes.
2. Real speech to text for visit capture. Transcripts are seeded today.
3. Phase 2: law and policy RAG (vector half and corpus), court report assembly, plan builder.
4. Persistence on Vercel (a hosted database) and rate limits per user.
5. Review the three drilldown journeys and the Cases workspace with the owner.
