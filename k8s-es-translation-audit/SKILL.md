---
name: k8s-es-translation-audit
description: "Detect missing or outdated Kubernetes Spanish documentation by cloning kubernetes/website to a temporary folder, comparing content/es against content/en for file parity and paragraph alignment, scoring every finding by Hugo navigation weight so the highest-traffic pages are prioritized first, and producing an issue-ready Markdown report for project triage. Use when asked to find untranslated docs, stale translations, paragraph drift, translation deletion gaps, or inconsistent Spanish documentation style."
argument-hint: "Optional scope path under content/en (for example: docs/tasks/)"
---

# get-k8s-es-docs

Audit Kubernetes Spanish documentation completeness and consistency. The skill
executes two deterministic scripts (`scripts/audit.py` → `scripts/report.py`),
then prints the report path so the output is always reproducible.

## When to Use

- detect Spanish translation files missing for English pages
- detect Spanish pages that no longer have an English source (orphans)
- detect stale translations after English content updates
- compare paragraph and heading alignment between English and Spanish files
- review cross-file Spanish writing-style inconsistencies
- generate a structured findings document for issue creation in the Kubernetes docs workflow

Typical prompts:

- `audit kubernetes spanish translation coverage`
- `find missing and outdated docs between content/en and content/es`
- `run a full es vs en translation drift analysis`
- `generate an issue-ready report for k8s Spanish translation gaps`

## Required Inputs

| Input                         | Required | Default                                            |
| ----------------------------- | -------- | -------------------------------------------------- |
| Repository URL                | no       | `https://github.com/kubernetes/website`            |
| Scope path under `content/en` | no       | full tree                                          |
| Output report path            | no       | `./reports/k8s-es-translation-audit-YYYY-MM-DD.md` |
| Strictness mode               | no       | `normal`                                           |

## Procedure

### Step 1 — Clone the repository

Use a shallow sparse checkout to fetch only the two language trees.

```bash
tmp_dir="$(mktemp -d)"
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/kubernetes/website "$tmp_dir/website"
cd "$tmp_dir/website"
# Include common language trees so cross-language coverage signal works
git sparse-checkout set \
    content/en content/es \
    content/de content/fr content/ja content/ko \
    content/pt content/zh content/it content/pl
```

If `git` is unavailable or the clone fails, stop and report the exact error.
Do **not** fall back to a full clone without confirming with the user — the
repository is several gigabytes.

Verify the clone succeeded:

```bash
echo "en: $(find content/en -name '*.md' -o -name '*.mdx' | wc -l)"
echo "es: $(find content/es -name '*.md' -o -name '*.mdx' | wc -l)"
```

Expected: EN ≈ 2 400–2 600 files, ES ≈ 200–300 files.

---

### Step 2 — Run the auditor (`scripts/audit.py`)

```bash
python3 scripts/audit.py \
    --repo "$tmp_dir/website" \
    [--scope docs/tasks/] \
    --out /tmp/k8s_audit_results.json
```

The script writes a single JSON file with all findings.

| JSON key         | Contents                                                                          |
| ---------------- | --------------------------------------------------------------------------------- |
| `en_total`       | total English markdown files in scope                                             |
| `es_total`       | total Spanish markdown files in scope                                             |
| `paired`         | count of files that exist in both languages                                       |
| `missing_in_es`  | sorted list of English-only paths                                                 |
| `orphan_in_es`   | sorted list of Spanish-only paths                                                 |
| `drifted`        | list of `[path, evidence_list, evidence_count]` for structurally diverged pairs   |
| `aligned_count`  | count of structurally equivalent pairs                                            |
| `style_findings` | list of cross-file style inconsistency objects (STYLE-001 … STYLE-003)            |
| `scores`         | dict of `path → {weight, tier, cross_lang, lines, score}` for every analysed file |
| `errors`         | list of `[path, error_message]` for files that could not be parsed                |
| `other_langs`    | list of other language directory names found under `content/`                     |

**What the script checks:**

1. **File parity** — every English `.md`/`.mdx` is cross-referenced against
   its expected Spanish mirror path and vice versa.

2. **Structural alignment** — for each paired file the script compares heading
   hierarchy, paragraph block count per section, list item count, and code
   block count. Files where any section diverges are classified `drifted`.

3. **Traffic scoring** — every finding is assigned a priority score:

   ```
   score = (tier × 10,000 + hugo_weight) − (min(cross_lang, 8) × 200) − max(0, 500 − file_lines)
   ```

   - `hugo_weight` — `weight:` frontmatter of the English page (lower = higher nav position)
   - `section_tier` — top-level directory: `concepts/`, `tasks/`, `tutorials/`, `docs/` → tier 1;
     `setup/`, `reference/` → tier 2; `blog/`, `community/` → tier 3
   - `cross_lang` — number of other `content/XX` language trees that already contain this file;
     each additional language reduces the score by 200 pts (proves page is worth translating and
     provides a reference translation)
   - `file_lines` — line count of the English file; files under 500 lines get a quick-win bonus
     of up to 500 pts (less effort to translate)

4. **Spanish style analysis** — over a sample of up to 80 paired files the
   script detects:
   - STYLE-001: mixed `clúster` vs `cluster` usage
   - STYLE-002: mixed imperative register (`tú` vs `usted` verb forms)
   - STYLE-003: inconsistent treatment of the `Deployment` API object term

---

### Step 3 — Generate the Markdown report (`scripts/report.py`)

```bash
python3 scripts/report.py \
    --results /tmp/k8s_audit_results.json \
    [--out ./reports/k8s-es-translation-audit-YYYY-MM-DD.md] \
    [--strictness normal]
```

The report is written to `./reports/` by default. Print the path to the user.

**Report sections (always present):**

1. Metadata (date, repo, scope, strictness, traffic-signal description)
2. Priority Score Methodology (formula, section-tier table, GA4 upgrade path)
3. Summary counts
4. Traffic-prioritized top-50 missing translations (table with score, tier, weight, xlang, lines)
5. Traffic-prioritized top-30 drifted pairs (table with score, tier, weight, xlang, evidence items)
6. **Quick Wins** — missing pages already translated in ≥2 other languages AND < 200 lines; drifted pages with ≤2 structural mismatches
7. Full missing-in-es list (first 60 individual, remainder grouped by section)
8. Full orphan-in-es list
9. Full drifted/possibly-stale pairs (detailed, traffic-sorted)
10. Cross-file Spanish style findings
11. Issue candidates with severity
12. Next actions checklist for project board intake

---

### Step 4 — Quality checks before returning

All of the following must be true:

- [ ] `audit.py` exited 0 and the JSON is non-empty
- [ ] every English file in scope is classified (missing, orphan, or paired)
- [ ] every paired file has an alignment result
- [ ] every drifted or style claim includes at least one evidence item
- [ ] report file exists and its line count is > 100

If any check fails, print the first failing item and the remediation.

---

## Decision Rules

| Situation                                           | Action                                                                                                                                                                                                |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git clone` fails (network blocked)                 | Stop; tell user to run clone manually and provide the `--repo` path                                                                                                                                   |
| `content/en` or `content/es` missing after clone    | Stop; verify sparse-checkout targets                                                                                                                                                                  |
| `audit.py` partially fails (some files in `errors`) | Continue; list failed files in the report                                                                                                                                                             |
| User provides `--scope`                             | Pass it to `audit.py --scope`; report covers only that subtree                                                                                                                                        |
| User wants real GA4 page-view data                  | Ask for GA4 property ID and service-account JSON; extend `audit.py` to call the GA4 Data API (`runReport` with `screenPageViews` per `pagePath`) and replace `hugo_weight` with normalized view count |

## Severity Rules

| Severity | When                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------- |
| `high`   | Missing or orphaned pages in tier-1 sections; structural drift changing meaning on tier-1 pages   |
| `medium` | Stale translations on tier-1 pages; partial section mismatch; recurring terminology inconsistency |
| `low`    | Minor style inconsistency; punctuation-level quality gaps; tier-2/3 missing pages                 |

## Minimum Clarifications

Ask only when required:

- Should the audit cover all docs or a specific subtree? (maps to `--scope`)
- Where to save the findings report? (maps to `--out`)
- Normal or strict paragraph-alignment mode? (maps to `--strictness`)
