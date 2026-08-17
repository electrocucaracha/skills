---
name: repair-knowledge-base
description: >
  Turn completed fixes into a reusable, cross-repo knowledge base of repair
  nodes, kept on disk by a CLI and mirrored into the OpenViking memory system.
  Use when the user says capture this fix, record what we learned, build a fix
  knowledge base, store the repair in memory, reuse past fixes, why did we fix
  this before, or asks for a plan grounded in previous repairs across repos.
  Applies hierarchical trajectory abstraction (localization, planning,
  execution-and-verification at low, medium, and high abstraction levels) so
  knowledge captured in one repository transfers to others.
metadata:
  hermes:
    tags:
      [
        memory,
        knowledge-base,
        openviking,
        repair,
        trajectory-abstraction,
        experience-reuse,
        cross-repo,
      ]
---

# Repair Knowledge Base

Store finished repairs as structured nodes,
retrieve them for new failures in any repository.

All mechanical work is done by `scripts/kb.py`.
Run the commands;
do not reimplement their logic.

## Model

One repair produces nodes at three stages
(`localization`, `planning`, `execution-verification`)
and three levels:

- `L1` — repo-specific action, keeps real paths and commands.
- `L2` — project-agnostic tactic, symbolic anchors instead of paths.
- `L3` — universal principle, names no file, tool, or repo.

Retrieval mixes levels.
Mixing beats any single level.

## CLI

```bash
python3 scripts/kb.py template --level L1 --stage localization
python3 scripts/kb.py validate [PATH ...]
python3 scripts/kb.py index
python3 scripts/kb.py query --stage localization --text "ERROR ..." \
    --language shell --ecosystem github-actions
python3 scripts/kb.py outcome --label verified NODE_ID [NODE_ID ...]
```

Root defaults to `.repair-kb/`.
Override with `--root` or `REPAIR_KB_ROOT`.

## Write Path — after a fix lands

1. Save the raw session steps to
   `.repair-kb/trajectories/traj-<date>-<context>.md`.
   This is provenance;
   it is never retrieved as guidance.
2. Check for an existing node before adding one:
   ```bash
   python3 scripts/kb.py query --stage localization --text "<the symptom>"
   ```
   If a node already covers it,
   edit that node instead of creating a duplicate.
3. For each stage worth recording,
   emit a skeleton and fill it:
   ```bash
   python3 scripts/kb.py template --level L1 --stage localization \
       > .repair-kb/nodes/L1/<node-id>.md
   ```
   Write `pitfalls` from real dead ends in the session.
   Write `applicable_when` as signals observable *before* the fix.
4. Validate and index:
   ```bash
   python3 scripts/kb.py validate && python3 scripts/kb.py index
   ```
   Fix every ERROR before continuing.
5. Mirror to OpenViking, see Memory Sync below.

Abstracting `L1` into `L2` and `L3` is judgement work.
Load [references/abstraction-prompts.md](references/abstraction-prompts.md)
only when doing that step.
Field definitions live in
[references/node-schema.md](references/node-schema.md);
load it only when a validation error is unclear.

## Read Path — before fixing something new

1. Retrieve guidance per stage:
   ```bash
   python3 scripts/kb.py query --stage localization --text "<error or symptom>" \
       --language <lang> --ecosystem <ecosystem>
   ```
2. Read the printed files in the order given.
   That order is the guidance sequence.
3. Adapt it into a plan for the current repo:
   real paths, real commands, real verification.
   Drop guidance that does not apply and say why.
4. Execute, then record what happened:
   ```bash
   python3 scripts/kb.py outcome --label verified NODE_ID
   ```
   Labels:
   `verified`, `partial`, `wrong-location`, `over-modification`, `refuted`.
   The command prints which field to revise for the non-verified labels.

Retrieval without an `outcome` call decays the knowledge base into folklore.

## Memory Sync

The CLI owns the on-disk tree.
OpenViking is the durable copy.

Browse the memory root first
and mirror the path pattern you observe:

```text
viking_browse viking://user/default/memories/entities/
```

Then write each changed file to
`viking://user/default/memories/entities/repair-kb/<same relative path>`.
Never guess a URI scheme.
If no memory tool is exposed,
commit `.repair-kb/` and report that the sync is pending.

Layout, ID rules, and retrieval details are in
[references/viking-layout.md](references/viking-layout.md).
Load it only before the first sync of a session.

## Gotchas

- **Never retrieve raw trajectories as guidance.**
  They carry failed exploration and repo-specific noise.
  Keep them in `trajectories/`, which `query` does not read.
- **A node without `portability` gets retrieved for the wrong stack**
  and produces a plan referencing files that do not exist.
  `validate` rejects it;
  do not work around the rejection.
- **`L3` nodes drift into platitudes.**
  If an `L3` node cannot change what the agent does next,
  delete it.
- **Merging is harder than adding, so it gets skipped.**
  Always run the Step 2 `query` before writing a new node.
- **`index` is not automatic.**
  Run it after every write,
  or the new node stays missing from the index.
- **`[STALE]` in query output means unverified for over 180 days.**
  Treat that guidance as a hypothesis,
  not a fact.
