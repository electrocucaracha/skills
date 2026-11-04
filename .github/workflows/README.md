# GitHub Actions Workflows

These files call reusable workflows from
[electrocucaracha/gh-workflows](https://github.com/electrocucaracha/gh-workflows).
Keep repository-specific triggers,
permissions,
and secret mappings here;
maintain shared execution logic upstream.

## Scheduled Updates

[update.yml](update.yml) runs every Friday at 00:00 UTC
and supports manual runs from the Actions tab.
Only one update run per Git ref remains active;
a new run cancels the previous one.

The shared workflow runs
[ci/update_versions.sh](../../ci/update_versions.sh)
and opens a pull request with the resulting changes.
The script fetches release tags,
provisions uv in a temporary environment when needed,
updates pre-commit hooks and managed dependencies,
and synchronizes marketplace and plugin versions.

The update job requests `contents: write` and `pull-requests: write`.
It does not merge the generated pull request.

## Lint Checks

[linter.yml](linter.yml) runs on pushes and pull requests.
It delegates validation to the shared Super-Linter workflow,
using the repository's linter configuration files.
Inspect the Actions run for failing checks and diagnostic logs.

The linter job requests `contents: read` and `issues: write`.
The pinned shared workflow requires `COPILOT_TOKEN` for its Copilot integration.
Repository secrets are not available to pull requests from forks;
token-dependent features are therefore unavailable for those runs.

## Required Secrets

Configure these under **Settings > Secrets and variables > Actions**:

- `WORKFLOW_TOKEN`: a token authorized to push update branches and create
  pull requests in this repository.
  It must also permit workflow-file updates when those files change.
- `COPILOT_TOKEN`: a credential authorized to use Copilot through the
  shared linter's integration.

Both callers default to `contents: read` outside their job-specific grants.
They pass only the named secrets rather than inheriting all repository secrets.
Never commit token values to workflow files.

## Shared Workflow Updates

Both callers pin the reusable workflows to commit
`8f0fa8c0acf90de07569a66d774498c3101d235f` (`v12.1.1`).
Before changing the pin,
review the upstream workflow's inputs,
required secrets,
and permissions.

Validate caller changes locally with:

```bash
actionlint .github/workflows/update.yml .github/workflows/linter.yml
```

Run the command from the repository root.
Local validation checks workflow syntax;
a GitHub Actions run is still required to verify credentials and runner behavior.
