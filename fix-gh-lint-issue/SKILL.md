---
name: fix-gh-lint-issue
description: >
  Fix Super-Linter failures reported in a GitHub issue
  titled "super-linter GitHub action has failed"
  (label super-linter-issue),
  created by the electrocucaracha/gh-workflows linter.yml workflow.
  Applies code fixes that survive `make fmt`
  and adds preventive configuration so the same findings do not recur.
  Use when the user mentions a super-linter issue, a failed lint workflow,
  "fix lint issue", or gives an issue URL or number from that workflow.
---

# Fix GitHub Lint Issue

Resolve a Super-Linter issue filed by the
[linter.yml](https://github.com/electrocucaracha/gh-workflows/blob/main/.github/workflows/linter.yml)
workflow.
Fix the findings,
make sure `make fmt` keeps the fixes,
and prevent recurrence.

## When to Use

- Resolve a GitHub issue labeled `super-linter-issue`.
- Investigate a failed shared Super-Linter workflow.
- Fix lint findings that return after `make fmt`.

## Inputs

Use the issue URL or number and the target repository checkout.
If the issue is not supplied,
find the open `super-linter-issue` in the current repository.
Read the latest comments for the current failure logs.

## Issue Format

The workflow files one open issue per repository:

- Title: `super-linter GitHub action has failed`
- Label: `super-linter-issue`
- Later failures are added as **comments** on the same issue,
  so read all comments and prefer the newest.
- The body has `Workflow run:` and `Commit:` lines,
  then `## Failed linter logs`.
- Each `### <path>` section holds a 4-space indented log.
  Structured JSON entries (failed linters only) are used when available;
  otherwise raw logs.
- Logs are truncated at about 60 KB.
  If truncated or empty, open the workflow run URL
  (`gh run view <id> --log-failed`).

## Workflow

Copy this checklist and track it:

```text
- [ ] 1. Read the issue and comments
- [ ] 2. Reproduce locally
- [ ] 3. Fix findings
- [ ] 4. Verify `make fmt` is stable
- [ ] 5. Add preventive actions
- [ ] 6. Re-validate and summarize
```

### 1. Read the issue

Use the issue number or URL given;
otherwise find it in the current repository:

```bash
gh issue list --state open --label super-linter-issue \
  --json number,title,url
gh issue view <number> --comments
```

Group findings by linter and file.
Note the commit SHA and confirm the checkout is at or after it.

### 2. Reproduce locally

Prefer the repository's own targets:
inspect `Makefile` for `lint`, `fmt`, and similar targets.
Run the lint target when it exists;
it usually runs Super-Linter in Docker with the same rules.
Otherwise run only the failing linters directly
(for example `shellcheck`, `yamllint`, `markdownlint`, `hadolint`).

Look for linter configs the workflow honors:
`LINTER_RULES_PATH` is `/`,
so configs live at the repository root.

### 3. Fix findings

- Fix the root cause in the code.
  Do not disable a rule just to silence it.
- Edit only the files named in the findings and their direct dependencies.
- Keep one logical fix per linter so the diff is reviewable.
- If a rule is genuinely wrong for the repository,
  scope the exemption narrowly (a path or a single rule)
  and explain why in a comment.

### 4. Make fixes survive `make fmt`

`make fmt` typically runs auto-formatters
(prettier, shfmt, black, and similar)
that can rewrite a fix back into a failing form.

1. Read the `fmt` target and note which formatters and configs it uses.
2. Run `make fmt`, then `git diff`.
3. If `make fmt` changes or reverts your fix,
   the formatter and the linter disagree.
   Reconcile them in config, not by alternating edits:
   align line length, indentation, quote style, and rule sets
   (for example prettier vs. yamllint, shfmt vs. shellcheck,
   black vs. flake8).
4. Run `make fmt` again until the diff is empty,
   then rerun the linter.
   Both must pass in the same tree state.

### 5. Add preventive actions

Choose only what applies to the findings:

- Align formatter and linter configs
  (`.yamllint.yml`, `.markdownlint.yaml`, `.prettierrc`,
  `.editorconfig`, `.flake8`, `.shellcheckrc`)
  so formatted output is always lint-clean.
- Make `make fmt` cover the file types that failed.
- Add or update a pre-commit hook or lint target
  so the same check runs before pushing.
- Add a short note to contributor docs
  only if the mistake is a convention, not a tool-enforceable rule.

Do not add tooling the repository does not already use
unless nothing else prevents the recurrence.

### 6. Re-validate and summarize

Run `make fmt` then the lint target (or the narrowed linters).
Confirm a clean `git status` after a second `make fmt`.
Report per finding: file, rule, fix, and the preventive action added.
Do not close the issue or push unless the user asks;
the issue closes when the workflow next passes
or when the user closes it.

## Verification

- Confirm the affected linters pass after `make fmt`.
- Confirm a second formatting pass introduces no additional changes.
- Report each finding's file, rule, fix, and preventive action.
- Do not push changes or close the issue without an explicit request.

## Gotchas

- Issue comments, not the body, hold the latest failure after the first run.
- The log excerpt may include only failed linters;
  a fix can expose findings from linters that were not listed.
  Rerun everything.
- Callers can pass `validate_overrides` (`VALIDATE_*` flags)
  in their workflow file;
  check `.github/workflows/` before enabling a linter locally
  that CI has disabled.
- Do not edit `linter.yml` in the target repository;
  it is a shared workflow from gh-workflows.

## References

- [Shared lint workflow](https://github.com/electrocucaracha/gh-workflows/blob/main/.github/workflows/linter.yml):
  issue format and Super-Linter configuration.
