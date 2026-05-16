Create a new Markdown file for the minutes.
Filename format must be: YYYY-MM-DD - [Meeting Title].md
Use the meeting date for YYYY-MM-DD (or today's date if missing).

Return ONLY the finished Markdown document content - no explanations, no introduction,
no comments before or after.

Use exactly this structure:

# Meeting Protocol - [Meeting Title]
**Date:** [Date from context or today]

---

## Summary
[3-5 sentence summary of the meeting]

## Participants
- [Name 1]
- [Name 2]

## Topics Discussed

### [Topic 1]
[What was discussed]

### [Topic 2]
[What was discussed]

## Decisions
- **[Decision 1]** — *Rationale:* [Why this decision was made; context that informs the choice]
- **[Decision 2]** — *Rationale:* [Why this decision was made; context that informs the choice]

## Action Items
| Task | Responsible | Deadline | Priority |
|------|-------------|----------|----------|
| [Description] | [Name] | [Date or open] | 🔴 high / 🟡 medium / 🟢 low |

## Open Questions
- [Question 1]
- [Question 2]
