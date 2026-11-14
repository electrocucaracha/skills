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

# Fix GitHub linting issue

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
- The body has a hidden `super-linter-commit: <sha>` marker,
  `Workflow run:`, `Commit:`, `Ref:`,
  and a `Failed linters:` line listing the linter names
  (for example `PYTHON_BLACK`, `PYTHON_PYLINT`),
  then `## Failed linter logs`.
  Older issues lack `Ref:` and `Failed linters:`.
- Each `### <LINTER>` section holds a 4-space indented log
  with the `/github/workspace/` prefix removed,
  so paths are repository-relative.
  Older issues use `### <results file path>` headings.
- Each linter gets its own size budget (about 60 KB total);
  a `[truncated ...]` line means open the workflow run URL
  (`gh run view <id> --log-failed`).
- A commit already reported is not commented again.

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
When a linter reports many findings (for example Pylint),
group by rule ID and fix per rule:
some rules need a repository-wide config choice
(for example `.pylintrc` or `.python-lint` per-file ignores for tests)
rather than per-line edits.
Use the commit SHA from the newest report,
which may be in a comment rather than the issue body.
Prefer its `super-linter-commit` marker when present;
otherwise use that report's `Commit:` line.
Confirm `HEAD` contains that commit before editing.
Compare the reported SHA as the base and the local `HEAD` as the head:

```bash
owner="OWNER"
repo="REPO"
reported_sha="REPORTED_SHA"
gh api "repos/$owner/$repo/compare/$reported_sha...$(git rev-parse HEAD)" \
  --jq '{status, ahead_by, behind_by}'
```

Proceed only when `behind_by` is `0`
and the comparison status is `ahead` or `identical`.
Dirty worktree changes do not advance `HEAD`
and do not satisfy this check.
If the checkout is behind or the comparison cannot be verified,
do not patch against the stale revision;
preserve the worktree and ask for an updated checkout or permission to sync it.

### 2. Reproduce locally

Prefer the repository's own targets:
inspect `Makefile` for `lint`, `fmt`, and similar targets.
Check what each target actually runs before choosing it.
Use a target when it matches the CI checks;
otherwise run the reported linter directly
(for example `shellcheck`, `yamllint`, `markdownlint`, `hadolint`).
Inspect the caller workflow for `VALIDATE_*` overrides
so local checks match the checks enabled in CI.

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

1. Inspect the `fmt` target and the CI linter configuration
   for the formatter used on each affected file type.
   Treat the CI formatter as the source of truth.
   For example, a `PYTHON_BLACK` failure requires Black-compatible output;
   a passing `ruff format --check` is not a substitute when the two disagree.
2. Run `make fmt` and inspect the diff for expected and incidental changes.
3. If formatting conflicts with CI,
   reconcile the commands or configuration instead of alternating edits.
   Prefer one formatter per file type;
   keep multiple formatters only if they produce the same output.
   For example, make `fmt` use Ruff when CI checks `ruff format`,
   rather than letting Black and Ruff rewrite the same file differently.
4. Run the affected formatter's check and lint again.
   Then run `make fmt` a second time and confirm it introduces no new diff.
   Keep the intended fix in the worktree;
   a clean `git status` is not expected while changes are pending.

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

Run `make fmt`, the affected linters,
and the full CI-equivalent lint target when one exists.
If no equivalent target exists,
run all CI-enabled checks relevant to the changed files.
Confirm a second `make fmt` introduces no additional changes.
Report per finding: file, rule, fix, and the preventive action added.
Report failures from broader, unrelated checks separately;
do not expand the fix to unrelated baseline issues.
Do not close the issue or push unless the user asks;
the issue closes when the workflow next passes
or when the user closes it.

## Verification

- Confirm the affected linters pass after `make fmt`.
- Confirm a second formatting pass introduces no additional diff
  while retaining the intended fix.
- Report each finding's file, rule, fix, and preventive action.
- Do not push changes or close the issue without an explicit request.

## Gotchas

- Issue comments, not the body, hold the latest failure after the first run.
- Black diffs and MyPy/Pylint findings often co-occur on the same files;
  fix types and structure first, then run the formatter last.
- Pylint `E1120` on decorator-based CLIs (click/typer)
  is a false positive; scope a `disable-next` directive instead of rewriting.
- Keep Pylint exceptions narrow and formatter-stable:
  put `disable-next` directly above the reported call or function definition,
  explain the framework or lifecycle reason,
  then rerun Pylint after `make fmt`.
- When local mypy reports missing third-party modules or stubs,
  use the project's declared environment when available
  and distinguish environment-only import errors from the issue's findings.
- The log excerpt may include only failed linters.
- Callers can pass `validate_overrides` (`VALIDATE_*` flags)
  in their workflow file;
  check `.github/workflows/` before enabling a linter locally
  that CI has disabled.
- Do not edit `linter.yml` in the target repository;
  it is a shared workflow from gh-workflows.

## References

- [Shared lint workflow](https://github.com/electrocucaracha/gh-workflows/blob/main/.github/workflows/linter.yml):
  issue format and Super-Linter configuration.
