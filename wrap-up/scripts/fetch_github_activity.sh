#!/bin/bash
# Fetch GitHub activity for a specific date (PRs, code reviews, commits)
# Usage: ./fetch_github_activity.sh [username] [date]
# Examples:
#   ./fetch_github_activity.sh                    # Current user, today
#   ./fetch_github_activity.sh john.doe           # Specific user, today
#   ./fetch_github_activity.sh john.doe 2026-05-13

set -u

USERNAME="${1:-}"
DATE="${2:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is not installed. Install it with: brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI is not authenticated. Run: gh auth login"
  exit 1
fi

if [ -z "$USERNAME" ]; then
  USERNAME=$(gh api user --jq '.login')
fi

if [ -z "$DATE" ]; then
  DATE=$(date +%Y-%m-%d)
fi

if ! date -j -f "%Y-%m-%d" "$DATE" "+%Y-%m-%d" >/dev/null 2>&1; then
  echo "ERROR: Invalid date format '$DATE'. Expected YYYY-MM-DD"
  exit 1
fi

echo "# GitHub Activity for ${DATE}"
echo ""
echo "**User**: ${USERNAME}"
echo ""

echo "## Pull Requests (authored, updated on ${DATE})"
echo ""
PR_OUTPUT=$(GH_PAGER=cat gh search prs \
  --author="${USERNAME}" \
  --updated="${DATE}" \
  --limit 100 \
  --sort=updated \
  --order=desc \
  --json number,title,state,repository,url \
  --template '{{if .}}{{range .}}- PR #{{.number}}: {{.title}} [{{.state}}] - {{.repository.nameWithOwner}} - {{.url}}
{{end}}{{end}}' 2>/dev/null)

if [ -n "$PR_OUTPUT" ]; then
  echo "$PR_OUTPUT"
else
  echo "- No PRs found for this date"
fi

PR_COUNT=$(GH_PAGER=cat gh search prs --author="${USERNAME}" --updated="${DATE}" --limit 100 --json number --jq 'length' 2>/dev/null || echo "0")

echo ""
echo "## Code Reviews (reviewed by ${USERNAME}, updated on ${DATE})"
echo ""
REVIEW_OUTPUT=$(GH_PAGER=cat gh search prs \
  --reviewed-by="${USERNAME}" \
  --updated="${DATE}" \
  --limit 100 \
  --sort=updated \
  --order=desc \
  --json number,title,state,repository,url \
  --template '{{if .}}{{range .}}- PR #{{.number}}: {{.title}} ({{.state}}) - {{.repository.nameWithOwner}} - {{.url}}
{{end}}{{end}}' 2>/dev/null)

if [ -n "$REVIEW_OUTPUT" ]; then
  echo "$REVIEW_OUTPUT"
else
  echo "- No reviews found for this date"
fi

REVIEW_COUNT=$(GH_PAGER=cat gh search prs --reviewed-by="${USERNAME}" --updated="${DATE}" --limit 100 --json number --jq 'length' 2>/dev/null || echo "0")

echo ""
echo "## Commits (authored on ${DATE})"
echo ""
COMMIT_OUTPUT=$(GH_PAGER=cat gh search commits \
  --author="${USERNAME}" \
  --author-date="${DATE}" \
  --limit 100 \
  --sort=author-date \
  --order=desc \
  --json sha,repository,url,commit \
  --template '{{if .}}{{range .}}- {{printf "%.7s" .sha}}: {{.commit.messageHeadline}} - {{.repository.nameWithOwner}} - {{.url}}
{{end}}{{end}}' 2>/dev/null)

if [ -n "$COMMIT_OUTPUT" ]; then
  echo "$COMMIT_OUTPUT"
else
  echo "- No commits found for this date"
fi

COMMIT_COUNT=$(GH_PAGER=cat gh search commits --author="${USERNAME}" --author-date="${DATE}" --limit 100 --json sha --jq 'length' 2>/dev/null || echo "0")

echo ""
echo "## Totals"
echo ""
echo "- PRs: ${PR_COUNT}"
echo "- Reviews: ${REVIEW_COUNT}"
echo "- Commits: ${COMMIT_COUNT}"
echo ""
echo "---"
echo ""
echo "Use this output as source evidence in the wrapup. If an item is not listed above, do not claim it as completed."
