---
name: k8s-es-translation-review
description: "Review a Kubernetes website Spanish translation PR end-to-end. Clones kubernetes/website, fetches the PR diff, and runs four deterministic checks: (1) paragraph/heading alignment against the English source, (2) writing consistency within the file and across the Spanish corpus, (3) internal link validation, (4) syntax, typos, and untranslated terms. Produces a Markdown report with one table per reviewed file containing line number, severity, and review comment in Spanish. Also supports a follow-up mode (--base-findings) that verifies whether suggestions from a previous review have been applied or addressed. Use when asked to review a k8s Spanish translation PR, check a localization PR, revisar PR de documentación, validate a kubernetes/website Spanish PR, or verify that previous review comments were addressed."
argument-hint: "PR number (e.g. 12345), optionally with --base-findings path/to/previous.json"
---

# k8s-es-translation-review

Review a Kubernetes website Spanish translation pull request against the English source and Spanish style conventions,
producing a single full Markdown report with detailed observations.

## When to Use

- Review a k8s Spanish translation PR before approving
- Validate paragraph completeness, links, and terminology in a localization PR
- Generate a structured review table for the PR submitter
- Apply kubernetes contrib review guidelines to `content/es/` changes
- **Verify a follow-up PR** to check whether suggestions from a previous review were applied

## Required Inputs

| Input | Required | Default |
|-------|----------|---------|
| PR number | yes | — |
| Repository | no | `https://github.com/kubernetes/website` |
| Base findings (previous review) | no | none (first review) |
| Output path | no | `./reports/k8s-review-PR<number>-YYYY-MM-DD.md` |
| Save findings path | no | none |

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

---

### Step 2 — Identify changed files

```bash
git diff --name-only origin/main...pr-branch -- 'content/es/**'
```

Only review files under `content/es/`. If no Spanish files changed, report that the PR has no Spanish content changes.

---

### Step 3 — Run the four checks

Run the scripts in sequence. Each script writes a JSON file consumed by the report generator.

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

| Grupo | Significado |
|-------|-------------|
| ✅ Aplicado | Finding from the previous review that no longer appears in the current scan |
| ⚠️ Pendiente | Finding from the previous review still detected in the current scan |
| 🆕 Nuevo | New finding not present in the previous review |

Matching logic: a previous finding is considered **resolved** when no current finding shares the same `(file, code)` pair within ±5 lines of the original. Line tolerance handles minor line-number shifts due to edits above the flagged area.

### Decision rule for verification

| Outcome | Action |
|---------|---------|
| All 🔴 Error findings resolved | PR is ready for technical approval |
| 🔴 Errors still Pendiente | Request another revision |
| Only 🟡/🔵 Pendiente | Reviewer may approve at their discretion |

---

### Check 1 — Paragraph Alignment (`check_paragraphs.py`)
Parses headings and paragraph blocks in both the ES file and its EN mirror.
Flags:
- Missing sections (present in EN, absent in ES)
- Extra sections (present in ES, absent in EN)
- Section content significantly shorter than EN (< 50% of EN paragraph count)
- Heading text drift (EN heading not reflected accurately in ES)

### Check 2 — Internal Link Validation (`check_links.py`)
Resolves all Markdown links `[text](target)` and Hugo shortcodes `{{< relref "..." >}}`.
Flags:
- Links targeting a `content/` path that does not exist in the repo
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
2. Per-file sections with a review table:

```markdown
### content/es/docs/concepts/example.md

| Línea | Código | Severidad | Contexto | Comentario | Sugerencia |
|-------|--------|-----------|----------|------------|------------|
| 12    | PARA-004 | 🔴 Error | 10: párrafo anterior<br>11: contexto cercano<br>> 12: línea marcada | Sección "Overview" falta en la traducción ... | Añadir la sección faltante a partir del bloque EN de referencia. |
| 34    | LINK-001 | 🟡 Aviso | 32: párrafo anterior<br>33: enlace previo<br>> 34: línea marcada | Enlace roto: `/docs/tasks/foo` no existe ... | Corregir el destino o eliminar el enlace. |
| 67    | STYLE-003a | 🔵 Sugerencia | 65: frase anterior<br>66: contexto cercano<br>> 67: línea marcada | Usar "clúster" en lugar de "cluster" ... | Sustituir "cluster" por "clúster" en esta línea. |
```

3. Summary checklist for the submitter

4. **Resumen enumerado de observaciones** (ordered by severity and volume),
with one numbered item per finding category to prioritize fixes quickly.

Each finding should include enough local context to act on it directly:

- The flagged line text
- Up to two nearby lines before and after when available
- A concrete suggestion to apply
- For paragraph/section findings (`PARA-003`, `PARA-004`), include explicit guidance on **how to write** the new paragraph (opening sentence intent, technical detail sentence, and closing action sentence)
- For missing EN sections, a short EN reference snippet around the source heading

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

| Situation | Action |
|-----------|--------|
| `git clone` fails (network blocked) | Stop; tell user to clone manually and pass `--repo` |
| PR has no `content/es/` changes | Report it and exit cleanly |
| EN counterpart missing | Flag as 🔴 Error (orphan ES file) |
| Script fails on a single file | Continue; record the error in the report |
| PR targets a non-`main` base branch | Warn; compare against that branch instead |
