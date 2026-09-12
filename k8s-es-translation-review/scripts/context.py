"""Shared context-window helpers for the review checks."""

CONTEXT_RADIUS = 2


def _window(entries: list[tuple[int, str]], index: int, radius: int) -> dict:
    """Build before-and-after context around an entry index."""
    start = max(0, index - radius)
    end = min(len(entries), index + radius + 1)
    return {
        "context_before": [
            {"line": ln, "text": text.rstrip()} for ln, text in entries[start:index]
        ],
        "context_after": [
            {"line": ln, "text": text.rstrip()} for ln, text in entries[index + 1 : end]
        ],
    }


def make_context_window(
    lines: list[str], line_no: int, radius: int = CONTEXT_RADIUS
) -> dict:
    """Context around a 1-based line number in a full file."""
    entries = list(enumerate(lines, 1))
    return {
        "line_text": lines[line_no - 1].rstrip(),
        **_window(entries, line_no - 1, radius),
    }


def context_window(prose_lines: list[tuple[int, str]], line_no: int) -> dict:
    """Context around a line number among prose lines only."""
    for index, (ln, _) in enumerate(prose_lines):
        if ln == line_no:
            return _window(list(prose_lines), index, CONTEXT_RADIUS)
    return {"context_before": [], "context_after": []}
