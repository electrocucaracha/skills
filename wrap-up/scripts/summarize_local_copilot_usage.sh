#!/bin/bash
# Summarize local GitHub Copilot activity from ~/.copilot for wrap-up context.
# Usage: ./summarize_local_copilot_usage.sh [date]
# Example: ./summarize_local_copilot_usage.sh 2026-05-15

set -u

DATE="${1:-}"
COPILOT_DIR="${HOME}/.copilot"

if [[ "${DATE}" == "-h" || "${DATE}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./summarize_local_copilot_usage.sh [date]

Arguments:
  date  Target date in YYYY-MM-DD format (default: today)

Output:
  Markdown summary with non-sensitive, aggregate activity signals from ~/.copilot.
EOF
  exit 0
fi

if [ -z "${DATE}" ]; then
  DATE=$(date +%Y-%m-%d)
fi

if ! date -j -f "%Y-%m-%d" "${DATE}" "+%Y-%m-%d" >/dev/null 2>&1; then
  echo "ERROR: Invalid date format '${DATE}'. Expected YYYY-MM-DD"
  exit 1
fi

echo "# Local Copilot Usage Context for ${DATE}"
echo ""
echo "**Source**: ${COPILOT_DIR}"
echo "**Target Date**: ${DATE}"
echo ""
echo "## Copilot Usage (optional)"

if [ ! -d "${COPILOT_DIR}" ]; then
  echo "- Copilot usage data unavailable (local ~/.copilot directory not found)."
  echo ""
  echo "## Wrap-up Snippet"
  echo ""
  echo "**Copilot Usage (optional)**: Copilot usage data unavailable (local ~/.copilot directory not found)."
  exit 0
fi

# Capture files modified on target date only; suppress permission errors.
MODIFIED_FILES=$(find "${COPILOT_DIR}" -type f -newermt "${DATE} 00:00:00" ! -newermt "${DATE} 23:59:59" 2>/dev/null || true)

if [ -z "${MODIFIED_FILES}" ]; then
  echo "- Copilot usage data unavailable (no local records found for target date)."
  echo ""
  echo "## Wrap-up Snippet"
  echo ""
  echo "**Copilot Usage (optional)**: Copilot usage data unavailable (no local records found for target date)."
  exit 0
fi

FILE_COUNT=$(printf "%s\n" "${MODIFIED_FILES}" | sed '/^$/d' | wc -l | tr -d ' ')
DIR_COUNT=$(printf "%s\n" "${MODIFIED_FILES}" | sed '/^$/d' | xargs -I{} dirname "{}" | sort -u | wc -l | tr -d ' ')

EARLIEST=$(printf "%s\n" "${MODIFIED_FILES}" | sed '/^$/d' | while IFS= read -r f; do
  stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$f"
done | sort | head -n 1)

LATEST=$(printf "%s\n" "${MODIFIED_FILES}" | sed '/^$/d' | while IFS= read -r f; do
  stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$f"
done | sort | tail -n 1)

echo "- Local Copilot activity detected for ${DATE}."
echo "- Files updated: ${FILE_COUNT}"
echo "- Active directories: ${DIR_COUNT}"
echo "- Activity window: ${EARLIEST} to ${LATEST}"
echo ""
echo "## Wrap-up Snippet"
echo ""
echo "**Copilot Usage (optional)**: Local Copilot activity detected on ${DATE} (${FILE_COUNT} files updated, ${DIR_COUNT} active directories, activity window ${EARLIEST} to ${LATEST})."
echo ""
echo "## Notes"
echo "- Local telemetry is supporting context only and should not be used as completion evidence."
echo "- No raw prompt/code content is extracted by this script."
