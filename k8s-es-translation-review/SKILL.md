---
name: k8s-es-translation-review
description: "Review a Kubernetes website Spanish translation PR end-to-end. Clones kubernetes/website, fetches the PR diff, and runs four deterministic checks: (1) paragraph/heading alignment against the English source, (2) writing consistency within the file and across the Spanish corpus, (3) internal link validation, (4) syntax, typos, and untranslated terms. Produces a Markdown report with one table per reviewed file containing line number, severity, and review comment in Spanish. Also supports a follow-up mode (--base-findings) that verifies whether suggestions from a previous review have been applied or addressed. Use when asked to review a k8s Spanish translation PR, check a localization PR, revisar PR de documentación, validate a kubernetes/website Spanish PR, or verify that previous review comments were addressed."
argument-hint: "PR number (e.g. 12345), optionally with --base-findings path/to/previous.json"
---

# k8s-es-translation-review

Review a Kubernetes site Spanish translation pull request against the English source and Spanish style conventions,
producing a single full Markdown report with detailed observations.

## When to Use

- Review a k8s Spanish translation PR before approving
- Validate paragraph completeness, links, and terminology in a localization PR
- Generate a structured review table for the PR submitter
- Apply kubernetes contrib review guidelines to `content/es/` changes
- **Verify a follow-up PR** to check whether suggestions from a previous review were applied

## Required Inputs

| Input                           | Required | Default                                         |
| ------------------------------- | -------- | ----------------------------------------------- |
| PR number                       | yes      | —                                               |
| Repository                      | no       | `https://github.com/kubernetes/website`         |
| Base findings (previous review) | no       | none (first review)                             |
| Output path                     | no       | `./reports/k8s-review-PR<number>-YYYY-MM-DD.md` |
| Save findings path              | no       | none                                            |

## Procedure

### Step 1 — Clone and fetch the PR

```bash
TMP="$(mktemp -d)"
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/kubernetes/website "$TMP/website"
cd "$TMP/website"
git sparse-checkout set content/en content/es
git fetch origin "pull/<PR_NUMBER>/head:pr-branch"
git checkout pr-branch
```

Verify clone:

```bash
echo "en: $(find content/en -name '*.md' | wc -l)"
echo "es: $(find content/es -name '*.md' | wc -l)"
```

Resolve the PR submitter's fork URL and head commit SHA for accurate file links in the report.
Use the GitHub API; fall back to the local checkout SHA if the API is unavailable:

```bash
# Preferred: resolve from GitHub API
PR_JSON=$(curl -sf \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/kubernetes/website/pulls/<PR_NUMBER>")
HEAD_REPO=$(echo "$PR_JSON" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print((d['head']['repo'] or {}).get('html_url',''))")
HEAD_REF=$(echo  "$PR_JSON" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d['head']['sha'])")

# Fallback: use local HEAD SHA and upstream repo URL
HEAD_REF=${HEAD_REF:-$(git rev-parse HEAD)}
HEAD_REPO=${HEAD_REPO:-https://github.com/kubernetes/website}
```

If clone or fetch fails, stop and report the error. Do **not** fall back to a full clone without user confirmation.

When the environment has a custom corporate CA bundle, set `SSL_CERT_FILE` before calling GitHub API endpoints so that `urllib` can validate the certificate chain correctly. Without this, HEAD/base branch detection and PR comment deduplication may silently fail and the review may incorrectly conclude that there are no Spanish changes.

---

### Step 2 — Identify changed files

Always compare the PR branch against the actual target branch for the PR, not blindly against `origin/main`.
This matters for PRs from a fork or for repos whose default branch is not `main`.

```bash
BASE_REF=$(curl -sf -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/kubernetes/website/pulls/<PR_NUMBER>" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print((d.get('base') or {}).get('ref','main'))")

git fetch origin "${BASE_REF}" --depth=1
git diff --name-only "origin/${BASE_REF}...pr-branch" -- 'content/es/**'
```

Only review files under `content/es/`. If no Spanish files changed, report that the PR has no Spanish content changes.

### Step 2b — Load existing PR discussion

Before generating findings, query and paginate all three GitHub REST collections:

```text
/repos/{owner}/{repo}/issues/{PR_NUMBER}/comments
/repos/{owner}/{repo}/pulls/{PR_NUMBER}/reviews
/repos/{owner}/{repo}/pulls/{PR_NUMBER}/comments
```

Use each comment body, file path, and line when available to identify findings already
raised in the PR discussion. Suppress a finding only with concrete evidence of
equivalence: an inline comment on the same file and nearby line, the same finding code,
or a file/line reference plus at least two distinctive terms from the finding. Do not
suppress a finding for a generic approval, unrelated discussion, or weak keyword match.

Record every suppressed finding with the matching comment URL, source, reason, and
original finding in the saved findings JSON. If an endpoint fails, continue the review
but include the endpoint error in the report and state that deduplication was incomplete.

### Step 2c — Restrict findings to the contributor diff

Run the checks with the full ES file available for context, but report only findings
whose flagged line or flagged line range intersects a line added or modified by the PR.
Build this allowlist from the PR diff against the actual target branch (`origin/${BASE_REF}...pr-branch`),
not from the final file's total line range. Do not report pre-existing terminology, register,
link, typography, frontmatter, or structure issues merely because the file is in the PR.

Findings with no changed-line intersection must be excluded from all report tables,
summary counts, compact comments, and saved `findings`. Preserve them separately as
`out_of_scope_findings` with the reason `line is outside the contributor diff` for
auditability. A deleted file has no added lines and therefore must not produce content
findings. Keep the changed-file list visible so reviewers can distinguish a changed file
with no in-scope findings from an unreviewed file.

---

### Step 3 — Run the four checks

Use `scripts/review_pr.py` as the default entry point. It runs the checks, applies the
changed-line and existing-comment filters, and then invokes the report generator. Do not
invoke `generate_report.py` directly for a PR review unless you have first applied both
filters to the check JSON files.

```bash
# Paragraph and heading alignment against EN source
python3 scripts/check_paragraphs.py \
    --repo "$TMP/website" \
    --files <changed_files_list> \
    --out /tmp/k8s_review_paragraphs.json

# Internal link validation
python3 scripts/check_links.py \
    --repo "$TMP/website" \
    --files <changed_files_list> \
    --out /tmp/k8s_review_links.json

# Writing consistency and untranslated terms
python3 scripts/check_style.py \
    --repo "$TMP/website" \
    --files <changed_files_list> \
    --out /tmp/k8s_review_style.json

# Generate the final report
python3 scripts/generate_report.py \
    --paragraphs /tmp/k8s_review_paragraphs.json \
    --links      /tmp/k8s_review_links.json \
    --style      /tmp/k8s_review_style.json \
    --pr         <PR_NUMBER> \
    --head-repo  "$HEAD_REPO" \
    --head-ref   "$HEAD_REF" \
    --out        <output_path> \
    [--base-findings <previous_findings.json>]  # omit for first review
```

The report must state how many existing PR comments were loaded and how many findings
were omitted as duplicates. Omitted findings must not appear in summary counts, tables,
or the compact PR comment.

---

### Step 4 — Quality checks before returning

All of the following must pass:

- [ ] Every changed ES file was checked against its EN counterpart
- [ ] Every finding includes a line number **and the actual line text** (`line_text`)
- [ ] All broken links have the exact line and broken target
- [ ] Report file exists and has > 30 lines
- [ ] No script exited with a non-zero code without being reported

Print the report path when done.

---

## Verification Mode — Checking That Previous Suggestions Were Addressed

When a contributor submits a revised PR after receiving a review, use `--base-findings` to compare the new state against the previous review's saved findings.

### Step 0 — Save findings from the first review

```bash
python3 scripts/review_pr.py \
    --pr <ORIGINAL_PR> \
    --save-findings ./reports/pr<ORIGINAL_PR>-findings.json \
    --out ./reports/k8s-review-PR<ORIGINAL_PR>.md
```

### Run follow-up review on the revised PR

```bash
python3 scripts/review_pr.py \
    --pr <REVISED_PR> \
    --base-findings ./reports/pr<ORIGINAL_PR>-findings.json \
    --out ./reports/k8s-review-PR<REVISED_PR>-followup.md
```

The follow-up report includes a **Seguimiento de sugerencias previas** section at the top with three groups:

| Grupo        | Significado                                                                 |
| ------------ | --------------------------------------------------------------------------- |
| ✅ Aplicado  | Finding from the previous review that no longer appears in the current scan |
| ⚠️ Pendiente | Finding from the previous review still detected in the current scan         |
| 🆕 Nuevo     | New finding not present in the previous review                              |

Matching logic: a previous finding is considered **resolved** when no current finding shares the same `(file, code)` pair within ±5 lines of the original. Line tolerance handles minor line-number shifts due to edits above the flagged area.

### Decision rule for verification

| Outcome                        | Action                                   |
| ------------------------------ | ---------------------------------------- |
| All 🔴 Error findings resolved | PR is ready for technical approval       |
| 🔴 Errors still Pendiente      | Request another revision                 |
| Only 🟡/🔵 Pendiente           | Reviewer may approve at their discretion |

---

### Check 1 — Paragraph Alignment (`check_paragraphs.py`)

Parses headings and paragraph blocks in both the ES file and its EN mirror.
Flags:

- Missing sections (present in EN, absent in ES)
- Extra sections (present in ES, absent in EN)
- Section content significantly shorter than EN (< 50% of EN paragraph count)
- Heading text drift (EN heading not reflected accurately in ES)

Valid Spanish heading equivalences that must not be treated as drift or structural mismatches:

- `Helpful Resources` → `Recursos útiles`
- `Contact` → `Contacto`
- `Binaries` → `Binarios`

Do not raise `PARA-004` / `PARA-005` for legitimate translated headings when the ES heading is a faithful Spanish equivalent of the EN section title. If the heading is a valid translation, compare the section body instead of enforcing a one-to-one English word match.

Mailto links are valid external links in Kubernetes docs and must not be treated as broken by the link checker. A link such as `mailto:release-managers@kubernetes.io` is not a repo-relative file and should be ignored as an external address rather than flagged as `LINK-001`.

Paragraph drift detection must not rely only on a 3+ paragraph anchor pattern. Real drift can occur in shorter sections or when the technical anchors are sparse; detection should consider paragraph similarity to the wrong EN paragraph and allow some tolerance for shorter sections.

### Check 2 — Internal Link Validation (`check_links.py`)

Resolves all Markdown links `[text](target)` and Hugo shortcodes `{{< relref "..." >}}`.
Flags:

- Links targeting a `content/` path that does not exist in the repository
- Anchor fragments `#section-id` that don't correspond to a heading in the target file
- Links that point to English-only paths that have no Spanish equivalent (warn only)

### Check 3 — Writing Consistency (`check_style.py`)

Checks run **only on prose lines** — the following are automatically excluded to avoid false positives:

- YAML frontmatter (`---` block at the top of each file)
- Fenced code blocks (` ``` ... ``` `)
- HTML comments (`<!-- ... -->`)
- Hugo shortcode-only lines (`{{< ... >}}`, `{{% ... %}}`)
- Inline HTML tags at line start (`<div>`, `</div>`, etc.)
- Markdown table rows and separator lines (`| ... |`, `|---|`)

Flags:

- Untranslated English terms that the [k8s style guide](https://kubernetes.io/docs/contribute/style/style-guide/) requires to be translated or left as-is consistently
- Register inconsistency (`tú`/`vosotros` vs `usted`/`ustedes` within the same file)
- Terminology drift: `clúster` vs `cluster`, `contenedor` vs `container`, `nodo` vs `node`
- Obvious typographic errors (double spaces, missing accents on common words)
- English phrases left untranslated (detects sequences of 4+ consecutive English words)
- Wrapped-line compaction EN→ES (`STYLE-007`): when EN keeps a sentence in two wrapped prose lines and ES compresses it into one line with internal double spacing; report as alignment signal instead of plain typo

`STYLE-004` should only trigger for **internal** double spaces between words.
Leading indentation, list nesting, and Markdown continuation spacing must not be flagged as typographic double-space errors.

### Check 4 — Kubernetes PR Review Guide

Applies guidelines from [reviewing-prs.md](https://github.com/kubernetes/website/blob/main/content/en/docs/contribute/review/reviewing-prs.md):

- Technical accuracy check (code blocks and command names unchanged from EN)
- Frontmatter completeness (`title`, `description`, `weight`, `content_type`)
- File encoding (UTF-8), line endings (LF)
- No unresolved merge conflict markers (`<<<<`, `====`, `>>>>`)

---

## Report Format

The report is a Markdown file with:

1. Header: PR number, date, reviewer, summary counts
1. Per-file sections with a review table:

```markdown
### content/es/docs/concepts/example.md

| Línea | Código     | Severidad     | Contexto                                                            | Comentario                                    | Sugerencia                                                       |
| ----- | ---------- | ------------- | ------------------------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------- |
| 12    | PARA-004   | 🔴 Error      | 10: párrafo anterior<br>11: contexto cercano<br>> 12: línea marcada | Sección "Overview" falta en la traducción ... | Añadir la sección faltante a partir del bloque EN de referencia. |
| 34    | LINK-001   | 🟡 Aviso      | 32: párrafo anterior<br>33: enlace previo<br>> 34: línea marcada    | Enlace roto: `/docs/tasks/foo` no existe ...  | Corregir el destino o eliminar el enlace.                        |
| 67    | STYLE-003a | 🔵 Sugerencia | 65: frase anterior<br>66: contexto cercano<br>> 67: línea marcada   | Usar "clúster" en lugar de "cluster" ...      | Sustituir "cluster" por "clúster" en esta línea.                 |
```

1. Summary checklist for the submitter

1. **Resumen enumerado de observaciones** (ordered by severity and volume),
   with one numbered item per finding category to prioritize fixes quickly.

Each finding should include enough local context to act on it directly:

- The flagged line text
- Up to two nearby lines before and after when available
- A concrete suggestion to apply
- For every finding that changes Spanish wording, include the proposed
  sentence or sentence fragment exactly as it should be written.
- Prefer an explicit `Antes:` / `Después:` pair when the original wording is
  available.
- If a complete replacement would be misleading, provide a reusable sentence
  pattern with the variable technical term or value clearly marked.
- Do not give a vague instruction such as "improve the wording" or "use a
  consistent register" without showing the resulting Spanish wording.
- Only recommend a register change when the flagged text actually addresses
  the reader with a pronoun or verb form such as `tú`, `usted`, `tu`, or
  `su`; do not classify ordinary third-person subjunctive forms as formal
  reader address.
- For paragraph/section findings (`PARA-003`, `PARA-004`), include explicit guidance on **how to write** the new paragraph (opening sentence intent, technical detail sentence, and closing action sentence)
- For missing EN sections, a short EN reference snippet around the source heading

### Wording Recommendation Format

For findings involving translation, register, terminology, accents, or
sentence structure, use this format in the `Sugerencia` column and in the
corresponding summary item:

```text
Antes: "Para comprobar si su distribución usa cgroup v2, consulte ..."
Después: "Para comprobar si tu distribución usa cgroup v2, consulta ..."
Motivo: Mantener el tratamiento informal usado en el resto del documento.
```

When the finding concerns a missing or incomplete sentence, give a complete
example that preserves the technical meaning:

```text
Redacción propuesta: "La forma recomendada de usar cgroup v2 es utilizar
una distribución de Linux con cgroup v2 habilitado y configurado de forma
predeterminada."
```

For terminology-only findings, show the exact replacement and preserve product
names, commands, API fields, and other terms that must remain in English:

```text
Reemplazo: "container runtime" → "runtime de contenedores"
Oración resultante: "El runtime de contenedores es compatible con cgroup v2."
```

If the proposed wording cannot be determined from the source or local context,
mark the finding as requiring manual review instead of inventing a correction.

Repeated low-value style findings may be grouped into a single row when they are adjacent,
share the same code,
and require the same fix.
The grouped row should show the affected line range and preserve nearby context.

Severities:

- 🔴 **Error** — must fix before merge (missing sections, broken links, conflict markers)
- 🟡 **Aviso** — should fix (untranslated text blocks, register inconsistency)
- 🔵 **Sugerencia** — optional improvement (style, terminology preference)

---

## Decision Rules

| Situation                           | Action                                              |
| ----------------------------------- | --------------------------------------------------- |
| `git clone` fails (network blocked) | Stop; tell user to clone manually and pass `--repo` |
| PR has no `content/es/` changes     | Report it and exit cleanly                          |
| EN counterpart missing              | Flag as 🔴 Error (orphan ES file)                   |
| Script fails on a single file       | Continue; record the error in the report            |
| PR targets a non-`main` base branch | Warn; compare against that branch instead           |
