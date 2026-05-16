---
name: minutes-transcriber
description: Create structured meeting minutes from transcripts or notes using a fixed Markdown template. Use when you need decisions, action items, and open questions captured in a consistent format.
---

# Minutes Transcriber

Convert transcripts or raw notes into clear, decision-focused meeting minutes using the shared protocol template in `references/template.md`.

## Purpose / Overview

This skill produces concise, actionable minutes for internal meetings, usually up to 60 minutes. The output emphasizes decisions, rationale, and follow-up tasks so teams can move quickly from discussion to execution.

## When To Use

Use this skill when:

- You need minutes from a transcript, recording notes, or ad-hoc notes
- The output must include decisions, action items, and open questions
- You need a stable Markdown structure for downstream tooling

## Discovery (Clarifying Questions)

Before drafting, ask up to 3 clarifying questions if key context is missing:

- What is the meeting title and date?
- Do you have an agenda, transcript, recording, or only notes?
- Who should review or receive the final minutes?

If missing details remain after clarification, proceed with placeholders rather than blocking.

## Output Contract

- Use the template in `references/template.md`
- Create the minutes in a new Markdown file (do not inline only in chat)
- Filename must be: `YYYY-MM-DD - <meeting-title>.md`
- Build filename date from meeting date (or today's date if missing)
- Sanitize `<meeting-title>` for filenames: trim spaces, replace `/` and `:` with `-`, collapse repeated spaces
- Return only the finished Markdown document (no intro, no commentary)
- Summary: 3 to 5 sentences
- Topics Discussed: 2 to 6 sections with meaningful headings
- Decisions: explicit, unambiguous, and include rationale
- Action Items: include responsible person and deadline when available, otherwise `open`
- Open Questions: include unresolved items; use `- None` if none remain

## Operational Workflow

1. Collect metadata (title, date, source materials, participants if available).
2. Compute output filename using date + title: `YYYY-MM-DD - <meeting-title>.md`.
3. Create a new Markdown file with that name and write the completed minutes into it.
4. Identify meeting objective and major discussion threads.
5. Organize notes into 2 to 6 topic sections, reflecting agenda flow when available.
6. Extract explicit decisions and capture why each decision was made.
7. Derive action items from commitments and assign priority:
   - Use `🔴 high` for urgent/blocking work
   - Use `🟡 medium` for normal follow-up work
   - Use `🟢 low` for informational/non-urgent work
8. Extract open questions that remain unresolved at the end of the meeting.
9. Validate output against the template before finalizing the file.

## Quality Rules

- Use objective, neutral language and avoid speculation
- Focus on outcomes and commitments over conversational detail
- Keep decisions clear, with explicit chosen options
- Pair action items to the decision or discussion they address
- Include enough context so readers understand the reasoning without rereading the transcript

## Handling Missing Data

If key information is unavailable, still produce the full template and use placeholders:

- Participant unknown: `- open`
- Topic details unavailable: `[Details unavailable from source notes]`
- Decision missing: `- None recorded`
- Action items missing: `| None | open | open | 🟢 low |`
- Open questions missing: `- None`

This keeps the output stable and machine-friendly for downstream workflows.

## Example Prompt

- "Create minutes from this transcript using our protocol template. Highlight decisions with rationale and add action items with owners, deadlines, and priorities."