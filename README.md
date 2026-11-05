# Binti AI journeys (prototype)

A working prototype of AI-assisted child welfare journeys for a **caseworker**, a **prospective foster or adoptive parent** and a **kin caregiver**. All names, cases and data are fictional. Children are shown as illustrated avatars, never photos. It is not an official Binti product.

- **Binti AI home** (default landing for caseworkers): a full-screen chat over the whole caseload. "Your day" cards are color-coded by urgency (red urgent, amber soon, blue routine). Tap a card to ask about it, or ask anything about any child. Answers name the child and link to their case. The sidebar holds My cases and the Journey study pages.
- **My cases** (sidebar): the case list. It has a case list with filters, a "Your day" briefing, and case and child pages. **Ask Binti AI** reads the current case, names its stage and suggests next actions you can pin and reorder, then lets you ask about the case. Use **Full screen** in the panel header for a two-column view, with actions on the left and a wide chat on the right. The chat box grows as you type: Enter sends, and Shift+Enter adds a new line.
- **Journey study** (top menu): the original 21-screen concept walkthrough from the persona canvas (`canvas/index.html`).
- **Viewing as** switcher: stands in for sign-in. Choose one of three caseworkers, a kin caregiver or an applicant family.

The design is in `docs/ai-architecture.md`, and the agent profile is in `AGENTS.md`.

## Run it locally
```bash
python3 dev.py            # http://localhost:3000  (static site + /api on one port)
```
```bash
python3 dev.py --reseed   # rebuild the SQLite database from binti/seed.py
```
```bash
python3 -m unittest discover -s tests -v
```
```bash
python3 evals/run_evals.py      # 25-case golden eval set (see evals/README.md)
```
You need Python 3.10 or later. There's nothing to install: the backend uses only the standard library.

## Turn on the live model (DeepSeek)
Without a key, the app runs in **scripted mode**. It uses the same gateway, rules and guardrails, and fills in the wording from templates. With a key, the persona agents call DeepSeek with tool calling.

1. Create a key at **platform.deepseek.com**, under API keys. Don't paste it into chat, code or a commit.
2. **On Vercel:** go to Project, then Settings, then Environment Variables, and add `DEEPSEEK_API_KEY`. Tick Production and Preview. Optionally add `DEEPSEEK_MODEL` (default `deepseek-chat`). Then go to **Deployments** and redeploy the latest one so it picks up the variable.
3. **Locally:** copy `.env.example` to `.env`, paste the key, and run `python3 dev.py`. `.env` is git-ignored.
4. Check that it worked: the blue bar shows **AI: live · deepseek-chat**, or open `/api/health`.

Only fictional data is in this prototype. Before any real data goes to a model vendor, settle the vendor's terms and data residency. This is open question 3 in the architecture doc.

## Deploy on Vercel
1. Import the GitHub repo at vercel.com/new. Framework preset: **Other**. Leave the build command empty.
2. Vercel serves the static files and runs `api/index.py` (Python) for `/api/*`, as configured in `vercel.json`.
3. If viewers are asked to log in, turn off **Deployment Protection** for production.

**Data on Vercel:** Vercel's file system is read-only, so the database is seeded into `/tmp` when an instance starts. Chat history, memory and approvals last while that instance stays warm, then reset to the seed data. Locally, they persist in `data/binti.db`. For persistence on Vercel later, point `binti/db.py` at a hosted database such as Turso or Postgres.

## How it fits together
```
index.html, app.js, screens-*.js   journey walkthrough (unchanged)
cases.js, cases.css                case list, case page, application, Binti AI panel
api/index.py                       Vercel entry point -> binti/api.py (WSGI, no framework)
binti/
  seed.py        schema + fictional data (12 children, 3 caseworkers, kin caregiver, applicant)
  gateway.py     tool gateway: persona allowlist, schema checks, scope, disclosure matrix, audit, proposals
  stages.py      case stage + next-action rules (explainable, tested)
  agent.py       persona runtime: AGENTS.md profile + skills + DeepSeek tool loop + scripted fallback
  workflows.py   fixed-step workflows: briefing, visit note, form pre-fill, language check, first contact, triage, application help
  guardrails.py  safety disclosure, prompt injection, emotional cues, decision/legal-advice output checks, fault language
  llm.py         model gateway (DeepSeek, OpenAI-compatible)
  skills.py      loads skills/<name>/SKILL.md
AGENTS.md                          core agent + three persona profiles (tone, emotional states, tools)
skills/<name>/SKILL.md             14 skills (Agent Skills format) with their allowed tools
tests/test_backend.py              permissions, disclosure, stages, guardrails, workflows, live tool loop (fake server)
evals/golden.json, run_evals.py    25-case golden eval set and runner (release gate on critical cases)
```

### Why a plain Python WSGI app over SQLite
- **One deploy:** Vercel serves the existing static front end as-is and runs one Python function for `/api`. There's no build step and the front end needs no rewrite.
- **No dependencies:** Python's standard library covers HTTP, SQLite and JSON. Cold starts stay fast, and there's nothing to install or patch.
- **Easy to move:** the same `app` runs under `dev.py`, Vercel, or any WSGI host such as gunicorn on Render or Fly if you later need a persistent database.
- **Trade-off:** there's no request validation framework, so the gateway does its own schema checks (section 4 of the architecture). If the API grows, FastAPI is the natural next step.

## API (all JSON; identity from `X-Persona` and `X-User` headers)
| Method and path | What it does |
|---|---|
| `GET /api/health` | Mode (live or scripted), model and seed date |
| `GET /api/people` | Options for the "Viewing as" switcher |
| `GET /api/cases` | Case list rows: child, age, stage, next due, flags, last visit |
| `GET /api/cases/{id}` | Case page (caseworker), or the kin view filtered by the disclosure matrix |
| `GET /api/briefing` | Start-of-day briefing |
| `POST /api/ai/open` | Opens Binti AI on the current object: stage, next actions, saved chat, memory |
| `POST /api/ai/chat` | Sends a message to the persona agent |
| `POST /api/cases/{id}/actions/{aid}` | `pin`, `unpin`, `up`, `down`, `done` or `dismiss` a suggested action |
| `POST /api/workflows/{visit-note,prefill,language-check,first-contact,inquiry-triage,application-help}` | Runs a workflow; writes become proposals |
| `POST /api/proposals/{id}` | A person approves (and may edit) or rejects an AI draft |
| `GET /api/audit?case_id=` | Gateway audit log for a case |
