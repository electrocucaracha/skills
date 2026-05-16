---
name: weekly-summary
description: Create a weekly report by aggregating daily wrap-up files into key achievements and follow-up tasks. Use when you need a concise weekly status update or retrospective summary.
---

# Weekly Summary

Create a weekly roll-up from daily wrap-up files with two required outcomes:
- Week achievements
- Follow-up tasks for next week

Use the output template in `references/template.md`.

## Inputs

Expected daily files:
- Format: `YYYY-MM-DD.md`
- Alternative source: user-provided folder or file list

Week selection rules:
- If user provides a week or date range, use it.
- If not provided, use the most recent complete Monday to Sunday window with available files.
- Include only files in range; do not infer missing days.

## Workflow

1. Resolve source files
- Collect daily wrap-up files in the selected week range.
- Sort chronologically.
- If no files are found, stop and report that input is missing.

2. Extract structured signals from each daily file
- Completed work items and measurable outcomes
- Mentions of blockers, risks, and dependencies
- Carry-over items or explicit next steps

3. Synthesize weekly achievements
- Merge duplicates across days.
- Group by initiative/theme.
- Prefer outcome statements over activity statements.
- Include evidence references to day files when available.

4. Build follow-up task list
- Capture unfinished work and newly identified next actions.
- Write each task as the immediate next step, not the broad project ("Draft intro section of Q2 report" not "Work on Q2 report").
- Start every task with a specific action verb (Call, Draft, Schedule, Review, Deploy, Fix, Send, Test, etc.).
- Assign a realistic time estimate to each task (e.g., "30 min", "2 hrs").
- Include owner and deadline only when present in source files; do not invent them.

5. Produce weekly report
- Fill `references/template.md`.
- Keep concise and scannable.
- Save output as markdown.

## Output Rules

- Required sections (in order):
  - TL;DR
  - Progress (PPP — Progress)
  - Plans (PPP — Plans)
    - *Plans*: 3-5 bullet points of what comes next. Forward-looking and specific.
    - *Problems*: 2-3 bullet points of blockers or risks needing attention. State the impact and what help is needed first, context second. Omit section if none.
  - Keep it brief and skimmable: use short bullets, not paragraphs. No preamble or filler sentences.
  - Be objective and action-oriented: every bullet states a fact or an action, never an opinion or vague status.
  - Mark uncertain claims as `Context only (unverified)`.

- Achievement writing — XYZ Formula:
  - Every achievement must follow: **"Accomplished [X] as measured by [Y] by doing [Z]"**
    - **X**: The impact delivered.
    - **Y**: The numerical metric measuring what you accomplished. When a hard number is unavailable, use a qualitative measure (e.g., improved team collaboration, raised customer satisfaction ratings).
    - **Z**: The specific action taken.
  - Quantify everything: use numbers, percentages, or dollar amounts to show scale.
  - Start every bullet with a strong action verb (e.g., Spearheaded, Optimized, Negotiated, Reduced, Delivered, Accelerated). Never use passive openers like "Responsible for" or "Helped with".
  - Focus on value, not duties: describe what changed or improved, not what the daily job entailed.
  - Align with organizational goals: frame outcomes around company growth, cost savings, delivery speed, or operational efficiency.

- Follow-up task writing rules:
  - Start every task with a specific action verb (Call, Draft, Schedule, Review, Deploy, Fix, Send, Test, Finalize, etc.). Never use passive nouns or vague openers like "Work on" or "Look into".
  - Write the immediate next step, not the broad project. "Draft intro section of Q2 report (30 min)" not "Work on Q2 report".
  - Assign a realistic time estimate to every task (e.g., 30 min, 2 hrs). This forces accurate scoping and triggers immediate action.
  - Include owner and deadline only when present in source files; never invent them.
  - **5 rules for effective follow-ups** — apply when a task involves reaching out to a person:
    1. **Personalize**: Reference a specific topic, decision, or pain point from the prior interaction to jog memory instantly. Never open with "Just checking in".
    2. **Add value**: Pair the ask with something useful — a relevant resource, new insight, or data point tied to their goals.
    3. **Make the ask effortless**: State one single, direct question or action. Never make the recipient wade through a long recap to find what you need.
    4. **Offer a graceful out**: Include a low-pressure release (e.g., "Let me know if this isn't a priority right now") to remove guilt and increase response rates.
    5. **Keep it scannable**: 3-5 short bullets or paragraphs max. Busy people skim — structure for that.

- Risk statement writing rules (If-Then-Result):
  - Write each risk as: **If [Condition], then [Risk Event], resulting in [Measurable Consequence to objective].**
    - **Condition (If)**: Present-tense known fact or root cause.
    - **Risk Event (Then)**: Specific uncertain incident triggered by that condition.
    - **Result (Resulting in)**: Concrete consequence on cost, schedule, quality, safety, or reputation.
  - Avoid vague language. Name the specific asset, driver, and impact.
  - Separate cause from event. Do not present a root cause as the risk event.
  - Use present tense and direct verbs. Do not use weak phrasing like "might", "could", or "maybe".
  - Keep impact measurable whenever possible (hours downtime, weeks delay, dollar impact, error-rate change).
  - One risk per statement. Never combine multiple risks in a single bullet.
  - Include mitigation as a next action immediately after each risk statement when available.

- Metrics writing rules (actionable and decision-driving):
  - Tie every metric to a specific strategic goal (growth, cost efficiency, reliability, speed, quality, customer value).
  - Separate metrics into **Leading Indicators (Inputs)** and **Lagging Indicators (Outputs)**.
    - **Inputs**: actions taken that drive outcomes (for example: experiments run, deployments completed, stakeholder reviews held).
    - **Outputs**: business or delivery results (for example: conversion rate, revenue impact, defect rate, cycle time, SLA attainment).
  - Use HEART or INPUT/OUTPUT framing:
    - HEART (when user experience is the objective): Happiness, Engagement, Adoption, Retention, Task Success.
    - INPUT/OUTPUT (default): Leading input actions and lagging outcome results.
  - For each metric, include: current value, trend vs prior week, target, and decision/action.
  - Avoid vanity metrics and raw data dumps. Keep only metrics that trigger a concrete decision.
  - If a metric is unavailable, mark it `open` and state the immediate data-collection next step.

## File Naming

Default output filename:
- `README.md`

Default output location:
- Folder structure: `YYYY/WWNN/README.md` (example: `2026/WW20/README.md`).
- Derive `YYYY` and `WW` from the week being summarized.
- Create the folder if it does not exist.

If target file exists:
- overwrite only when user explicitly asks
- else write `README-v2.md`, `README-v3.md`, and so on

## Quality Checks

Before finalizing:
- Confirm every achievement is backed by at least one daily wrap-up entry.
- Remove duplicates and low-value noise.
- Ensure follow-up tasks are clear and directly actionable.
- Ensure output includes both required outcomes: achievements and follow-up tasks.
- Ensure each risk line follows If-Then-Result and includes a measurable consequence.
- Ensure each metric is tied to a strategic goal and includes a decision/action, not just a number.
