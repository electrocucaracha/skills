# Abstraction And Planning Prompts

Templates for the write path (grouping, abstraction)
and the read path (relevance verification, plan adaptation).

Use them verbatim where possible.
They are tuned so that outputs land in the node schema without rework.

## Grouping Operator

Applied at every level,
starting from the raw stage segment.

```text
You are grouping procedural steps from one stage of a completed repair.

Stage: {localization | planning | execution-verification}
Input: an ordered list of items. At level 0 each item is a raw step with
thought, action, and observation. At higher levels each item is a node.

Task: partition the input into consecutive, non-overlapping groups where every
group shares one coherent procedural intent. Do not reorder. Do not drop items;
if an item belongs to no intent, place it in a group labelled "noise".

Output, per group:
- group_intent: one imperative sentence
- member_indexes: contiguous index range
- why_grouped: the shared sub-goal, not a summary of the steps

Stop condition: if the input already has two or fewer items, return it
unchanged.
```

## Abstraction Operator

Applied to each group produced above.

```text
You are abstracting one group of repair steps into a single knowledge node.

Target level: {L1 | L2 | L3}
- L1: keep concrete artifacts — file names, commands, error strings.
- L2: keep the tactic, remove the repository. Replace paths with symbolic
  anchors such as <workflow-file>. Name tool categories, not versions.
- L3: keep only the principle. Naming any file, tool, or repository is a
  failure at this level.

Produce the node schema fields: title, intent, applicable_when, key_actions,
verification, pitfalls, portability, retrieval_keys.

Hard rules:
- pitfalls must come from real dead ends in the input, not invented risks.
- applicable_when must be observable before the fix, not after.
- key_actions must change what an agent does next. Delete any action that
  would be taken anyway.
- If the group contains no verification evidence, set outcome to unverified
  and do not emit a level above L1.
```

## Level Decision

Run before each abstraction round.

```text
Given these nodes, decide the next abstraction level.

Choose L1 if the content still depends on repository-specific artifacts.
Choose L2 if the content is a strategy any project with the same ecosystem
could apply.
Choose L3 if the content is a problem-solving principle independent of
language, ecosystem, and tooling.

If raising the level would erase the only actionable content, stop abstracting
and return the current level as final.
```

## Relevance Verifier

Applied on the read path after lexical candidate retrieval.

```text
Target failure:
{symptom, error signature, stage, target repo language / ecosystem / shape}

Candidate node:
{node frontmatter and Context section}

Decide: applicable, or not applicable.

Reject when:
- portability.languages or portability.ecosystems exclude the target and the
  node is not marked universal.
- applicable_when contains a signal the target does not exhibit.
- The match rests on shared vocabulary rather than shared procedure.

Answer with the decision and one sentence of reason. The reason is recorded
and used to tighten applicable_when.
```

## Plan Adaptation

One invocation per stage.

```text
Target failure: {full description, logs, repo context}
Stage: {localization | planning | execution-verification}
Guidance: {retrieved nodes, ordered by original execution order}

Produce an executable plan for this stage only.

Requirements:
- Instantiate every retained action against the real target: real paths, real
  commands, real verification.
- Drop guidance that does not apply and say which and why.
- Carry every relevant pitfall forward as an explicit check.
- End with a verification step whose result is observable.
- Keep the plan to the minimum scope that resolves the failure. Prefer
  extending an existing condition over rewriting a component.

Output:
1. Assumptions the plan depends on
2. Numbered steps with commands
3. Verification
4. Guidance dropped, with reasons
```

## Outcome Retro

Applied after the plan is executed.

```text
Compare the plan with what actually happened.

Label the outcome: wrong-location, partial-fix, over-modification, verified,
or refuted.

For each retrieved node, state the update:
- which field to change (applicable_when, pitfalls, key_actions, portability)
- the exact replacement text
- the evidence counter to increment

If a failure mode recurred that no node covers, emit a new node instead of
stretching an existing one.
```
