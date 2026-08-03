---
description: >
  Frontmatter format rules for SKILL.md files,
  following the agentskills.io specification.
applyTo: "**/SKILL.md"
---

# SKILL.md Frontmatter Format

Every `SKILL.md` must open with YAML frontmatter.
Follow the [agentskills.io specification](https://agentskills.io/specification) exactly.
Use only fields defined in the spec;
do not add custom top-level keys outside of `metadata`.

## Required Fields

### `name`

Must match the parent directory name exactly.
Allowed characters: lowercase letters (`a–z`), digits (`0–9`), and hyphens (`-`).
Length: 1–64 characters.
Must not start or end with a hyphen.
Must not contain consecutive hyphens (`--`).

### `description`

Length: 1–1024 characters.
Describe both what the skill does and when to invoke it.
Include specific trigger keywords and phrases
so agents can match the skill to relevant tasks.

## Optional Fields

| Field           | Notes                                                               |
| --------------- | ------------------------------------------------------------------- |
| `license`       | License name or path to a bundled license file.                     |
| `compatibility` | Environment requirements. Omit unless the skill has specific needs. |
| `metadata`      | Arbitrary string key-value map for additional properties.           |
| `allowed-tools` | Space-separated string of pre-approved tools. Experimental.         |

## Minimal Example

```yaml
---
name: skill-name
description: What this skill does and when to use it.
---
```

## Example with Optional Fields

```yaml
---
name: pdf-processing
description: >
  Extract PDF text, fill forms, and merge files.
  Use when handling PDFs or when the user mentions forms or document extraction.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```
