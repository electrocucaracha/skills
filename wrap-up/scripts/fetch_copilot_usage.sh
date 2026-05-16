#!/bin/bash
# Fetch GitHub Copilot billing/budget signals for wrap-up context.
# Usage: ./fetch_copilot_usage.sh [org] [date]
# Examples:
#   ./fetch_copilot_usage.sh my-org 2026-05-15
#   ./fetch_copilot_usage.sh my-org
#   ./fetch_copilot_usage.sh            # Tries to infer org from current repo

set -u

ORG="${1:-}"
DATE="${2:-}"

if [[ "${ORG}" == "-h" || "${ORG}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./fetch_copilot_usage.sh [org] [date]

Arguments:
  org   GitHub organization login. If omitted, inferred from current repo owner.
  date  Target date in YYYY-MM-DD format (default: today)

Output:
  Markdown summary for wrap-up context with Copilot usage/budget availability.
EOF
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is not installed. Install it with: brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI is not authenticated. Run: gh auth login"
  exit 1
fi

if [ -z "$DATE" ]; then
  DATE=$(date +%Y-%m-%d)
fi

if ! date -j -f "%Y-%m-%d" "$DATE" "+%Y-%m-%d" >/dev/null 2>&1; then
  echo "ERROR: Invalid date format '$DATE'. Expected YYYY-MM-DD"
  exit 1
fi

if [ -z "$ORG" ]; then
  ORG=$(gh repo view --json owner --jq '.owner.login' 2>/dev/null || true)
fi

if [ -z "$ORG" ]; then
  echo "ERROR: Organization was not provided and could not be inferred from the current repo."
  echo "Usage: ./fetch_copilot_usage.sh <org> [date]"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required for parsing API responses. Install it with: brew install jq"
  exit 1
fi

API_VERSION_HEADER="X-GitHub-Api-Version: 2022-11-28"
BUDGET_PATH="orgs/${ORG}/settings/billing/budgets"
USAGE_PATH="orgs/${ORG}/settings/billing/usage"

BUDGET_RAW=$(GH_PAGER=cat gh api -H "$API_VERSION_HEADER" "$BUDGET_PATH" 2>/dev/null || true)
USAGE_RAW=$(GH_PAGER=cat gh api -H "$API_VERSION_HEADER" "$USAGE_PATH" 2>/dev/null || true)

echo "# GitHub Copilot Usage Context for ${DATE}"
echo ""
echo "**Org**: ${ORG}"
echo "**Target Date**: ${DATE}"
echo ""

echo "## Copilot Usage (optional)"

if [ -z "$BUDGET_RAW" ] && [ -z "$USAGE_RAW" ]; then
  echo "- Copilot usage data unavailable (insufficient permissions or no data)."
  echo ""
  echo "## Notes"
  echo "- Tried endpoint: /${BUDGET_PATH}"
  echo "- Tried endpoint: /${USAGE_PATH}"
  echo "- Keep wrap-up generation running; do not block on missing Copilot telemetry."
  exit 0
fi

BUDGET_COUNT=0
BUDGET_HAS_COPILOT="no"
if [ -n "$BUDGET_RAW" ]; then
  BUDGET_COUNT=$(echo "$BUDGET_RAW" | jq 'if type=="array" then length elif has("budgets") then (.budgets|length) else 1 end' 2>/dev/null || echo "0")
  if echo "$BUDGET_RAW" | jq -e '.. | strings | ascii_downcase | select(contains("copilot"))' >/dev/null 2>&1; then
    BUDGET_HAS_COPILOT="yes"
  fi
fi

USAGE_HAS_COPILOT="no"
if [ -n "$USAGE_RAW" ]; then
  if echo "$USAGE_RAW" | jq -e '.. | strings | ascii_downcase | select(contains("copilot"))' >/dev/null 2>&1; then
    USAGE_HAS_COPILOT="yes"
  fi
fi

if [ "$BUDGET_HAS_COPILOT" = "yes" ] || [ "$USAGE_HAS_COPILOT" = "yes" ]; then
  echo "- Copilot telemetry found in billing responses."
else
  echo "- Billing responses returned, but no explicit Copilot fields were detected."
fi

if [ -n "$BUDGET_RAW" ]; then
  echo "- Budget records returned: ${BUDGET_COUNT}"
else
  echo "- Budget records returned: unavailable"
fi

if [ -n "$USAGE_RAW" ]; then
  echo "- Usage endpoint returned: yes"
else
  echo "- Usage endpoint returned: unavailable"
fi

echo ""
echo "## Wrap-up Snippet"
echo ""
if [ "$BUDGET_HAS_COPILOT" = "yes" ] || [ "$USAGE_HAS_COPILOT" = "yes" ]; then
  echo "**Copilot Usage (optional)**: Copilot-related billing telemetry detected for org ${ORG} (date scope: ${DATE}); include only API-returned fields."
elif [ -n "$BUDGET_RAW" ] || [ -n "$USAGE_RAW" ]; then
  echo "**Copilot Usage (optional)**: Billing endpoints returned data, but no explicit Copilot fields were detected for org ${ORG} on ${DATE}."
else
  echo "**Copilot Usage (optional)**: Copilot usage data unavailable (insufficient permissions or no data)."
fi

echo ""
echo "## Notes"
echo "- Endpoints queried: /${BUDGET_PATH}, /${USAGE_PATH}"
echo "- This script provides supporting telemetry only, not completion evidence."
