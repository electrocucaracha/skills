---
description: >
  Best practices for creating high-quality skills,
  adapted from agentskills.io guidance.
applyTo: "**/SKILL.md"
---

# Skill Creation Best Practices

Use these rules when creating or updating any `SKILL.md`.
They complement frontmatter validation rules in
`skill-format.instructions.md`.

## Ground In Real Expertise

Start from real execution in your environment,
not generic advice.
Capture what actually worked,
including sequence, corrections, context, and output expectations.

Prefer project artifacts as source material:

- internal docs and runbooks
- API contracts, schemas, and configs
- code review comments and issue history
- real incident and failure patterns with fixes

## Iterate With Execution Feedback

Treat the first draft as a baseline.
Run real tasks,
review execution traces,
then refine.

When behavior is wrong or wasteful,
tighten vague instructions,
remove irrelevant guidance,
and set a clear default path.

## Spend Context Wisely

Only include information the agent is unlikely to infer correctly.
Cut generic background the model already knows.

Scope each skill as one coherent unit of work.
Avoid skills that are too narrow to be useful,
or too broad to trigger reliably.

Use moderate detail.
Give stepwise guidance and concrete examples,
but avoid encyclopedic coverage.

## Use Progressive Disclosure

Keep `SKILL.md` focused on core, always-needed instructions.
Move large or conditional details into `references/`, `assets/`, or `scripts/`.

Tell the agent exactly when to load each auxiliary file.
Use explicit triggers,
not generic statements like "see references".

## Calibrate Control To Fragility

Use flexible guidance when multiple approaches are acceptable.
Be strict when order, safety, or reproducibility is critical.

Provide one default approach first,
then brief alternatives only as fallback paths.

Favor reusable procedures over single-instance answers.
Teach a method that generalizes across similar tasks.

## Prefer High-Leverage Instruction Patterns

Include a **Gotchas** section for non-obvious, environment-specific traps.
Keep it current by adding corrections from real runs.

Use templates when output format matters.
Inline short templates in `SKILL.md`.
Store long templates in `assets/` and reference them conditionally.

Use checklists for multi-step workflows with dependencies.
Use validation loops for quality gates:
do work,
validate,
fix,
repeat until passing.

For risky or destructive actions,
require plan-validate-execute flow before applying changes.

Bundle repeated logic into tested scripts in `scripts/`
instead of re-deriving logic each run.

## Quick Self-Check Before Finalizing

- Is this skill based on project-specific evidence?
- Does it state when to invoke it and when not to?
- Is there a clear default approach?
- Are fragile steps explicit and validated?
- Are non-essential details moved behind progressive disclosure?
- Are gotchas and templates included where they improve reliability?

## Source

Guidance adapted from:
<https://agentskills.io/skill-creation/best-practices>
