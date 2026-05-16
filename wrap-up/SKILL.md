---
name: wrap-up
description: Create an end-of-day wrap-up from GitHub activity, optional Copilot usage, and weekly meeting context using the 1-3-5 format. Use when you need a daily standup summary, accomplishment log, or stakeholder update.
compatibility: Requires gh CLI; optionally uses jq and GitHub API permissions for Copilot usage scripts.
---

# Daily Wrap-up Skill

Generate an organized end-of-day summary by combining GitHub activity with meeting context.

Meeting-context scope rule: use all available meeting minutes from the current week (Monday through the target date), not only today's meeting notes.

Accuracy rule: GitHub activity is the primary evidence source. The wrap-up must be grounded in fetched GitHub data for the requested date and user.

## Quick Start

The wrap-up skill synthesizes your work across three sources:

1. **GitHub activity** - PRs, code reviews, commits fetched via GitHub CLI
2. **GitHub Copilot usage (optional)** - Usage/budget signals from GitHub billing APIs when accessible, or local telemetry clues from `~/.copilot`
3. **Meeting context** - Meeting minutes you provide via IDE reference (#), aggregated across the current week

GitHub evidence is required for factual claims about completed coding work. Meeting notes may add context and prioritization, but should not introduce unverified completions.
Weekly meeting context should be used to explain why today's GitHub changes matter, including commitments, dependencies, and blockers discussed earlier in the week.
Copilot usage is supporting context only and must never be used as sole evidence of completed coding outcomes.

Output is organized using the **1-3-5 rule**: 1 high-priority task, 3 medium-priority tasks, and 5 low-priority tasks. Each task includes action-oriented language and brief context for why it was done.

Each completed task must be written as a single paragraph (one numbered item per task) with no nested sub-bullets.

**Example prompt:**
```
Create my wrap-up for today. Here are this week's meeting minutes:
# Meeting Notes

## Product Planning Standup
- Action: Complete PR review for analytics dashboard
- Action: Merge security patch before EOD (production blocker)
- Stakeholder: Product team awaiting feature branch
```

## Process

### 1. Gather GitHub Activity
Uses `gh` CLI to fetch:
- **Pull requests** created/updated/authored today
- **Code reviews** completed today
- **Commits** authored today

The script (`scripts/fetch_github_activity.sh`) fetches this automatically.

Execution requirement:
- Always run `scripts/fetch_github_activity.sh [user] [date]` (or equivalent `gh` queries) first.
- Treat the script output as source-of-truth evidence for what was completed on that date.
- Include PR/commit identifiers when available.

Validation requirement:
- If `gh` is unavailable, unauthenticated, rate-limited, or returns partial data, explicitly label the wrap-up as **partial**.
- In partial mode, separate verified items from unverified meeting-note context.
- Never present unverified items as completed facts.

### 2. Extract Meeting Context
Parse meeting minutes (provided as markdown via # reference) across the full week (Monday through target date) to identify:
- **Action items** with owners and deadlines
- **Blockers** and their impact
- **Stakeholder commitments** and urgency signals
- **Decisions** that affect prioritization

Weekly synthesis requirement:
- Build a single context timeline from all meetings in scope.
- Use earlier-in-week decisions to explain today's trade-offs and prioritization.
- If today's changes do not match today's meeting topics but do match earlier-week meetings, still treat them as in-scope context.

### 3. Gather Copilot Usage (Optional)
When available and authorized, fetch GitHub Copilot usage/budget data via GitHub REST billing endpoints (for example, budget and usage APIs documented by GitHub).

The script (`scripts/fetch_copilot_usage.sh`) fetches this context automatically.

Execution guidance:
- Attempt Copilot usage fetch only when credentials and permissions are available.
- Run `scripts/fetch_copilot_usage.sh [org] [date]` to generate a wrap-up-ready markdown snippet.
- Keep date scope aligned with the wrap-up target date.
- Include only fields returned by the API response; do not infer or estimate missing values.

Validation guidance:
- If API access is denied, unavailable, or returns no Copilot fields, omit usage metrics and continue.
- In that case, add: `Copilot usage data unavailable (insufficient permissions or no data).`
- Never block wrap-up generation on missing Copilot usage.

Alternative local-source execution:
- Run `scripts/summarize_local_copilot_usage.sh [date]` to gather aggregate, non-sensitive activity signals from `~/.copilot`.
- Use this only as supporting context; completed work still requires GitHub evidence.
- For detailed rules and examples, follow `references/copilot-local-inspection.md`.

### 4. Synthesize into 1-3-5 Format

Apply these reporting rules while synthesizing:
- Focus on outcomes and impact, not activity logs (for example: "Completed first draft of project X presentation" instead of "Worked on project X").
- Keep the **1-3-5** structure to make priorities obvious.
- Quantify progress when possible (percent complete, counts, milestones, PR numbers).
- Be strategic with detail: skip routine noise unless it was high-priority, unusual, or unblocks others.
- Highlight blockers early and clearly (what is blocked, impact, and next action).
- Use strong action verbs to start accomplishment statements (for example: "Finalized", "Developed", "Resolved", "Launched", "Unblocked").
- Keep the summary concise by listing only the top 3-5 accomplishments.
- For significant achievements, use STAR in one sentence: Situation/Task, Action, and Result.
- Prefer claims that can be tied to at least one GitHub artifact (PR, commit, or review).
- Do not invent metrics, timings, counts, or completion states.

**Categorization logic:**

#### HIGH (1 task)
- Production issues or security fixes
- Blocking items preventing others' work
- Time-sensitive deliverables with external deadlines
- Meeting action items marked urgent or blocking

**Example:**
```
1. **[HIGH] Merge Security Patch to Production:** Resolved CVE-2026-XXXX in the auth module and moved the production blocker to ready-to-merge status with PR #823 approved, reducing immediate login risk and restoring release confidence.
```

#### MEDIUM (3 tasks)
- Feature work aligned with sprint/roadmap
- PR reviews that unblock teams
- Technical debt reduction with clear value
- Meeting action items with standard priority
- Work that advances key initiatives

**Examples:**
```
1. **[MEDIUM] Complete Analytics Dashboard Feature Branch:** Advanced a Q2 roadmap commitment to review-ready state in PR #445, addressed 2 review comments, and moved the feature to approximately 80% completion so product validation can proceed.

2. **[MEDIUM] Review and Approve Database Optimization PR:** Completed technical review on PR #451 to unblock the data pipeline team, leaving only minor fixes before merge and preventing a likely sprint spillover.

3. **[MEDIUM] Update Kafka Consumer Documentation:** Published and merged onboarding updates in PR #429, reducing recurring setup questions and improving handoff reliability for new contributors.
```

#### LOW (5 tasks)
- Routine operational work
- Smaller improvements and polish
- Questions answered in chat
- Tech debt items
- Refactoring and cleanup

**Examples:**
```
1. **[LOW] Respond to Team Questions in #ask-devs:** Answered 4 implementation questions that unblocked same-day progress across multiple threads while keeping support turnaround within expected response time.

2. **[LOW] Add Unit Tests for Payment Utility Function:** Added targeted test coverage for edge cases to lower regression risk and improve confidence in upcoming payment-related merges.

3. **[LOW] Update CONTRIBUTING.md with New CI Pipeline Steps:** Clarified contributor setup flow to reduce onboarding friction and cut repeated setup clarifications for first-time contributors.

4. **[LOW] Clean Up Abandoned Feature Branches:** Deleted 8 stale branches to improve repository hygiene and make active work streams easier to identify.

5. **[LOW] Fix Deployment Config Formatting Issues:** Standardized config formatting to improve readability and reduce review friction for future deployment changes.
```

### 5. Format Output

Output is markdown with short, scannable sections. Use this format:

```markdown
# Daily Wrap-up — May 13, 2026

## Summary
Today I focused on [primary focus area] and [secondary focus area], resulting in measurable progress on delivery and team unblockers.

- **Finalized** [major deliverable] to [milestone/%], enabling [impact].
- **Resolved** [blocker/issue] by [action], reducing [risk/delay].
- **Developed** [feature/improvement] in [PR/commit], moving [initiative] to [stage/%].
- **Reviewed/Approved** [count] PRs, unblocking [team/project].

**GitHub Activity**: X PRs, Y reviews, Z commits
**Copilot Usage (optional)**: [key metrics from API or "data unavailable"]

**Evidence Scope**: GitHub data for [user] on [date]

## High Priority

1. **Merge Auth Security Patch to Production:** Closed CVE-2026-XXXX by finalizing PR #823 (45 mins), removed the release blocker, and restored authentication deployment readiness.

## Medium Priority 

1. **Complete Analytics Dashboard Feature Branch:** Progressed PR #445 to review-ready (2 hours), moving the roadmap deliverable to about 80% and unblocking product validation.

2. **Review Database Optimization PR for Data Team:** Completed review for PR #451 (1 hour), unblocking the data pipeline sprint objective pending minor edits.

3. **Update Kafka Consumer Documentation:** Merged PR #429 (1.5 hours), reducing onboarding delays and recurring support questions.

## Low Priority

1. **Respond to Team Questions in #ask-devs:** Resolved 4 implementation questions, helping maintain same-day execution momentum.

2. **Add Unit Tests for Payment Module:** Added missing coverage for critical utility logic to reduce regression risk.

3. **Update CONTRIBUTING.md:** Improved setup instructions so new contributors can complete CI setup with fewer clarification cycles.

4. **Clean Up Feature Branches:** Removed 8 inactive branches to improve repository clarity.

5. **Fix Configuration File Formatting:** Standardized deployment config formatting to simplify future reviews.
```

### 6. Save Wrap-up File

After generating the wrap-up content, save it as a Markdown file using the target date as the filename:
- Filename format: `YYYY-MM-DD.md`
- Example: `2026-05-13.md`
- Use the wrap-up target date (not necessarily today's system date if a different date was requested).

Default location:
- Save in `wrap-up/assets/` when that folder exists.
- If unavailable, save in the current working folder.

If a file for that date already exists:
- Overwrite the file only when the user explicitly asks to regenerate/replace.
- Otherwise, append a suffix `_v2`, `_v3`, etc. (for example: `2026-05-13_v2.md`).

Formatting requirement for generated wrap-ups:
- Keep section headers and summary bullets.
- Do not include a Reflection section.
- For task lists, use numbered items only.
- Each task item must be one concise paragraph with outcome, impact, and measurable progress when available.
- Do not use nested bullets under any task item.
- In `Summary`, include a 1-2 sentence high-level progress statement before bullets.
- In `Summary`, keep to 3-5 accomplishment bullets, each starting with an action verb and including a metric or milestone when available.
- In `Summary`, use specific accomplishments (avoid vague statements like "worked on" or "helped with").
- Every completed coding claim must map to GitHub evidence in the fetched activity (PR/review/commit).
- If evidence is unavailable, mark the claim as `Context only (unverified)` or omit it.
- Persist the final markdown to a date-named file (`YYYY-MM-DD.md`) as part of completion.
- If Copilot usage is included, clearly label it as supporting context and keep it separate from completion claims.

## Using Meeting Context

Meeting minutes should be provided via IDE reference (using `#` in Copilot). Provide all available meetings for the week. Structure them simply:

```markdown
# Team Standup — May 13

## Blockers
- Payment API deployment delayed (unblocks checkout team)

## Action Items
- [YOU] Merge security patch before EOD
- [YOU] Review analytics dashboard PR
- [JOHN] Deploy payment API

## Decisions
- Prioritize Q2 roadmap over tech debt this sprint

## Next Steps
- Alert stakeholders if analytics review delayed
```

The skill will:
1. Parse action items with owner assignment
2. Extract deadline/urgency signals
3. Aggregate context from all meetings in the week
4. Optionally fetch Copilot usage/budget metrics when accessible
5. Combine weekly meeting context with GitHub activity (and optional Copilot usage)
6. Automatically categorize tasks
7. Generate the formatted summary

Evidence reconciliation rules:
1. Confirm completed work against GitHub activity first.
2. Use weekly meeting context to explain impact, urgency, and priority.
3. Keep unresolved or not-yet-merged items phrased as in progress, unless a merged/closed state is present in GitHub evidence.
4. If meeting notes conflict with GitHub data, prefer GitHub status and note the discrepancy.
5. Treat Copilot usage as secondary telemetry, not completion proof.

Scope fallback rules:
1. If only today's meeting notes are provided, generate the wrap-up with a note: `Weekly meeting context unavailable; context may be incomplete.`
2. If multiple meetings are provided for the week, prioritize explicit decisions, blockers, and owner-tagged actions over general discussion notes.

## Customization

### Override Priorities
If a task should rank differently than the algorithm suggests, explicitly note it in the meeting minutes:
```
## Priorities
- [HIGH] Merge payment API (customer-facing, EOD deadline)
- [MEDIUM] Review analytics (roadmap item)
```

### Exclude Items
If certain GitHub activity shouldn't appear in wrap-up, note it:
```
## Out of Scope
- PR #999 (follow-up from yesterday)
- Review comments on draft PR
```

### Add Context
Include brief notes for anything that needs explanation:
```
## Additional Context
- Spent 3 hours on emergency incident response (outside normal work)
- Pairing session with data team on Kafka optimization
```

### Copilot Usage Scope (Optional)
If you want Copilot usage included, provide org/budget context and preferred metric scope:
```
## Copilot Usage
- Include Copilot billing/usage signals if available
- Org: my-org
- Scope: daily for the target date
```

## See Also

- **[1-3-5 Rule Reference](references/1-3-5-rule.md)** — Detailed categorization guidelines and action-oriented language patterns
- **[GitHub Activity Script](scripts/fetch_github_activity.sh)** — Bash script that fetches PR/review/commit data
- **[Copilot Usage Script](scripts/fetch_copilot_usage.sh)** — Bash script that fetches Copilot billing/usage context for wrap-ups
- **GitHub Billing Budgets API Docs** — https://docs.github.com/en/rest/billing/budgets?apiVersion=2022-11-28

---

**Tips:**
- Aim for realistic tasks. If you consistently can't complete all 9, adjust numbers.
- Include links to PRs/commits for easy navigation during retrospectives.
- Use consistent timing notation (e.g., "1.5 hours", "45 mins") to track velocity patterns.
- Review your wrap-up weekly to identify patterns and calendar blockers.
