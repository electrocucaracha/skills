# Node Schema

Every node is a Markdown file with YAML frontmatter.
The frontmatter is the machine-readable record;
the body holds prose the agent reads at plan time.

## Frontmatter Fields

### Required

| Field             | Type   | Notes                                                        |
| ----------------- | ------ | ------------------------------------------------------------ |
| `id`              | string | `<level>-<stage-abbr>-<failure-class>-<slug>`, lowercase      |
| `level`           | enum   | `L1`, `L2`, `L3`                                             |
| `stage`           | enum   | `localization`, `planning`, `execution-verification`          |
| `failure_class`   | string | Controlled vocabulary term, see `taxonomy.md` in memory       |
| `title`           | string | One line, imperative                                          |
| `intent`          | string | What this node accomplishes, one sentence                     |
| `applicable_when` | list   | Observable signals that must hold                             |
| `key_actions`     | list   | Ordered, executable at `L1`, procedural at `L2`/`L3`          |
| `verification`    | list   | How to prove the action worked                                |
| `pitfalls`        | list   | Dead ends and false signals seen during the original repair   |
| `portability`     | map    | See below                                                     |
| `evidence`        | map    | See below                                                     |
| `retrieval_keys`  | map    | See below                                                     |

### Optional

| Field      | Type | Notes                                       |
| ---------- | ---- | ------------------------------------------- |
| `parent`   | id   | Node one level above                        |
| `children` | list | Node IDs one level below                    |
| `supersedes` | list | Node IDs this node replaces               |

### `portability`

| Key           | Type | Notes                                                        |
| ------------- | ---- | ------------------------------------------------------------ |
| `languages`   | list | `["shell", "go"]` or `["*"]` when language-independent        |
| `ecosystems`  | list | `["github-actions", "maven", "npm"]` or `["*"]`               |
| `tools`       | list | Concrete tools the actions invoke                             |
| `repo_shape`  | list | `monorepo`, `polyrepo`, `library`, `service`, `infra`, `docs` |
| `transfer`    | enum | `repo-specific`, `project-agnostic`, `universal`              |

`transfer` must align with `level`:
`L1` is `repo-specific`,
`L2` is `project-agnostic`,
`L3` is `universal`.

`L3` nodes must set `languages`, `ecosystems`, and `tools` to `["*"]`.
If they cannot,
the node is really an `L2`.

### `evidence`

| Key               | Type   | Notes                                                  |
| ----------------- | ------ | ------------------------------------------------------ |
| `source_trajectories` | list | Trajectory IDs this node was abstracted from       |
| `repos`           | list   | `owner/name` where the knowledge was confirmed          |
| `outcome`         | enum   | `verified`, `partial`, `unverified`, `refuted`          |
| `verified_count`  | int    | Times a retrieved plan using this node succeeded        |
| `refuted_count`   | int    | Times it misled a repair                                |
| `last_verified`   | date   | `YYYY-MM-DD`                                            |

### `retrieval_keys`

| Key                | Type | Notes                                                   |
| ------------------ | ---- | ------------------------------------------------------- |
| `symptoms`         | list | What a human observes                                    |
| `error_signatures` | list | Literal strings or regexes seen in logs                  |
| `keywords`         | list | Free-text synonyms for lexical matching                  |

## Body Sections

Use exactly these headings,
in this order:

```markdown
## Context

## Procedure

## Verification

## Pitfalls

## Provenance
```

`Context` explains when the node fires and when it must not.
`Procedure` expands `key_actions` into prose with commands.
`Provenance` links the trajectory records and repos.

## Example — L1 node

```markdown
---
id: l1-loc-ci-metric-miscount-scoped-conclusion-grep
level: L1
stage: localization
failure_class: ci-metric-miscount
title: Scope conclusion counts to the conclusion field before ratio math
intent: >
  Prove that a reported CI failure rate is real and not an artifact of
  substring matching across the whole API payload.
applicable_when:
  - A failure rate was computed from a grep over raw JSON
  - Counted failures exceed the sampled run count
key_actions:
  - Re-count with the field name as a pre-filter, then match the value
  - Report total_all_time and sample_size as separate fields
verification:
  - Recomputed failure count is less than or equal to sample size
  - Sum of all conclusion buckets equals sample size
pitfalls:
  - Bare value grep matches log bodies and stack traces
  - total_count is lifetime, not sample size, so ratios are meaningless
portability:
  languages: ["shell"]
  ecosystems: ["github-actions"]
  tools: ["curl", "grep", "jq"]
  repo_shape: ["polyrepo"]
  transfer: repo-specific
evidence:
  source_trajectories: ["traj-2026-07-22-ci-audit"]
  repos: ["electrocucaracha/krd"]
  outcome: verified
  verified_count: 3
  refuted_count: 0
  last_verified: "2026-08-14"
retrieval_keys:
  symptoms: ["failure rate above 100%", "more failures than runs"]
  error_signatures: ['"conclusion"']
  keywords: ["grep overcount", "failure rate", "workflow runs"]
parent: l2-loc-metric-miscount-validate-denominator
---

## Context
...
```

## Example — L3 node

```markdown
---
id: l3-loc-measurement-validity-check-denominator
level: L3
stage: localization
failure_class: measurement-validity
title: Establish the denominator before trusting any ratio
intent: >
  Prevent decisions driven by ratios whose numerator and denominator come
  from different populations.
applicable_when:
  - A decision depends on a rate, percentage, or ratio
  - Numerator and denominator were produced by different queries
key_actions:
  - Name the population each term counts
  - Reject the ratio when the populations differ
  - Report both raw counts alongside any derived rate
verification:
  - Both terms are traceable to the same sampled population
pitfalls:
  - Lifetime totals silently substituted for sample totals
  - Aggregations that drop a non-success category entirely
portability:
  languages: ["*"]
  ecosystems: ["*"]
  tools: ["*"]
  repo_shape: ["monorepo", "polyrepo", "service", "infra"]
  transfer: universal
evidence:
  source_trajectories: ["traj-2026-07-22-ci-audit"]
  repos: ["electrocucaracha/krd", "electrocucaracha/pkg-mgr_scripts"]
  outcome: verified
  verified_count: 5
  refuted_count: 0
  last_verified: "2026-08-14"
retrieval_keys:
  symptoms: ["implausible rate", "metric disagreement"]
  error_signatures: []
  keywords: ["denominator", "ratio", "sampling"]
children:
  - l2-loc-metric-miscount-validate-denominator
---
```

## Anti-Examples

Reject these on sight:

- `title: Fix the linter` — names no class of problem.
- `key_actions: ["Investigate the root cause"]` — changes no behavior.
- Missing `portability` — will be retrieved for incompatible stacks.
- `L3` node naming a file, tool, or repo — it is an `L2` in disguise.
- A node whose only evidence is one unverified attempt promoted above `L1`.
