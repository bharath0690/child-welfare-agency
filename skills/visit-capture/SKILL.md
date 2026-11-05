---
name: visit-capture
description: Turn a consented visit recording into a draft visit note with transcript citations, for the worker to review and sign. Use after a recorded visit, or when a visit has a recording but no note.
allowed-tools: visit_get, visits_list, note_draft
metadata:
  persona: caseworker
  kind: workflow
  phase: 1
  feature: Visit transcription and visit note drafting
---
# Visit capture

You are drafting a visit note from a transcript. Write only what the transcript supports.

## Steps (workflow: `workflows.visit_note`)
1. `visit_get`. If there is no consent or no transcript, stop and say so. Never draft from memory.
2. Draft the note in these sections: opening line (visit type, place, date); Child seen alone (yes or no, with timestamp); School; Health; Family time; Services; Child's views (seen alone); Next steps.
3. Every sentence ends with the transcript timestamp in brackets, like [03:40].
4. Run the language check on the draft and show any findings.
5. Save with `note_draft`. It becomes a proposal the worker reviews, edits and signs.

## Writing rules
- Describe what was said and seen. Use the speaker's own words for anything sensitive.
- No opinions, no diagnoses, no blaming words.
- Leave anything unclear out, and list it under "To confirm".
- Never write a placement, custody or risk recommendation.

## Output
Plain text with section headings, under 250 words.
