# Brief for Claude Code

**Goal.** Share an externally viewable prototype of the three priority Binti journeys (caseworker, prospective foster/adoptive parent, kin caregiver) with AI features. Deployed on Vercel from Git. No viewer sign-in.

**Status.** v0.1: static site, vanilla JS, no build. 21 screens (7 stages x 3 personas) following `data.js`. AI is scripted. No API key.

**Principles**
- Human-led AI: every draft carries a "Binti AI draft" banner; the worker or family reviews and signs. AI never drafts placement or custody recommendations.
- Consent before recording. Language check flags fault-assigning wording (caseworker visit note).
- Reward with time and progress, never scores or rankings tied to child outcomes.
- Fictional data only. Not an official Binti product.

**Architecture.** `H` (app.js) holds state `S`, `H.SCR[persona][stage]` renderers, `H.ACT` click actions via `data-act`/`data-arg`, `H.CHATS` scripted chats, `H.rate` rating buttons that feed the AI quality drawer.

**Architecture.** The target AI architecture is in `docs/ai-architecture.md`. The owner has suggestions to apply to it. The persona canvas is in `canvas/index.html`.

**Next (waiting on the owner's AI feature details)**
1. Replace scripted AI with real feature specs: meeting transcription, form pre-fill, "Chat with Binti AI".
2. Evals: draft accuracy, edit distance, bias flags caught, minutes saved. The drawer is a sketch.
3. Optional live AI: a `/api` Vercel function with the key server-side, rate limiting, scripted fallback.
4. Review the three drilldown journeys with the owner; they have not been reviewed yet.
