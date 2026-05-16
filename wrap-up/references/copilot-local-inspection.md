# Local Copilot Inspection for Wrap-up

## Purpose

Use local artifacts in ~/.copilot as a fallback source for Copilot activity context when GitHub billing APIs are unavailable or inaccessible.

This source is supporting context only. It must not be used as sole evidence of completed coding work.

## Evidence Rules

- Treat local data as directional signals: active windows, file-event volume, session presence.
- Do not claim completed work from local data alone.
- Always prioritize GitHub PR/review/commit evidence for completion claims.
- If local and GitHub data conflict, classify local data as advisory and keep GitHub as source of truth.

## Privacy Rules

- Do not include tokens, secrets, or authentication material.
- Do not include raw prompt or code transcript content by default.
- Prefer aggregate metrics over verbatim local text.

## Suggested Workflow

1. Check whether ~/.copilot exists for the current user.
2. Filter records by target date (YYYY-MM-DD).
3. Capture only non-sensitive metadata:
   - Number of files updated on target date
   - Distinct active directories
   - Earliest and latest timestamps
4. Generate a short wrap-up snippet:
   - Local Copilot activity detected on DATE (N files updated, D directories, active HH:MM-HH:MM).
5. If no records exist, return:
   - Copilot usage data unavailable (no local records found for target date).

## Scripted Option

Use scripts/summarize_local_copilot_usage.sh for an automated markdown summary:

- ./scripts/summarize_local_copilot_usage.sh
- ./scripts/summarize_local_copilot_usage.sh 2026-05-15

The script intentionally outputs only aggregate metadata and avoids raw content extraction.
