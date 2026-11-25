---
description: >
  Best practices for creating high-quality skills,
  adapted from agentskills.io and skills-best-practices guidance.
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

Keep `SKILL.md` under 500 lines.
Use it as the high-level workflow,
not as a container for every implementation detail.

Use moderate detail.
Give stepwise guidance and concrete examples,
but avoid encyclopedic coverage.

## Use Progressive Disclosure

Keep `SKILL.md` focused on core, always-needed instructions.
Move large or conditional details into `references/`, `assets/`, or `scripts/`.

Tell the agent exactly when to load each auxiliary file.
Use explicit triggers,
not generic statements like "see references".

Keep supporting files one directory level below the skill directory
when practical.
Prefer `references/schema.md` over deeper paths such as
`references/database/v1/schema.md`.
Preserve established paths when moving a file would break callers or links.

Use relative paths with forward slashes in skill instructions,
regardless of the host operating system.

Do not add human-facing README, changelog, or installation documents
to a skill unless the user or repository specifically needs them.
Do not duplicate instructions the agent can already follow reliably.

## Calibrate Control To Fragility

Use flexible guidance when multiple approaches are acceptable.
Be strict when order, safety, or reproducibility is critical.

Provide one default approach first,
then brief alternatives only as fallback paths.

Favor reusable procedures over single-instance answers.
Teach a method that generalizes across similar tasks.

Write procedural steps as direct commands to the agent.
Use third-person imperative phrasing,
such as "Read the configuration" or "Run the validator."
Number steps when execution order matters;
make decision points and skip conditions explicit.

Use one consistent term for each concept
and prefer terminology native to the skill's domain.

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
Keep scripts as small, single-purpose command-line tools;
do not use a skill's `scripts/` directory for reusable library code.
Make failures explicit with actionable messages on standard error
and a non-zero exit status.

## Quick Self-Check Before Finalizing

- Is this skill based on project-specific evidence?
- Does it state when to invoke it and when not to?
- Does its description include specific positive and negative triggers?
- Is there a clear default approach?
- Are fragile steps explicit and validated?
- Are non-essential details moved behind progressive disclosure?
- Are gotchas and templates included where they improve reliability?
- Are paths relative, forward-slashed, and easy to resolve?
- Are supporting scripts deterministic, small, and explicit about failures?

## Validate Skill Behavior

When a skill's routing or workflow changes materially,
add or update focused eval cases in its existing `evals/` directory.
Use realistic prompts that should trigger the skill
and similar prompts that should not.
Assert observable decisions, required actions, and output constraints.

For significant workflow changes,
simulate the skill against a representative request
using the full `SKILL.md` and supporting-file tree.
Check that each step names the file or tool to use,
that decision branches have explicit conditions,
and that no step requires inventing missing inputs.
Evaluate observable behavior rather than requesting private reasoning traces.

Test relevant failure states and edge cases,
including unavailable dependencies, unsupported inputs,
and incomplete or truncated evidence.
Confirm the skill reports blockers clearly
and does not claim actions or validation that did not occur.
Use the repository's existing evaluation approach;
do not add evaluation tooling solely for a one-off skill edit.

## Source

Guidance adapted from:
<https://agentskills.io/skill-creation/best-practices>
and <https://github.com/mgechev/skills-best-practices>
