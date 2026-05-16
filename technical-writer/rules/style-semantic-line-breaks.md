# style-semantic-line-breaks

**Priority**:
CRITICAL
**Category**:
Writing Style

## Why It Matters

Semantic line breaks keep prose readable in source, make Git diffs smaller and more precise,
and let writers revise one clause or sentence without rewrapping an entire paragraph.
In Markdown and similar lightweight markup, these line breaks stay invisible in rendered output,
so they improve authoring and review without changing the reader experience.

## Incorrect

```markdown
Use semantic line breaks in source files because they make prose easier to review in Git diffs and help editors revise one clause without rewrapping an entire paragraph while preserving the same rendered output.
```

One long physical line hides the structure of the thought.
Small edits create noisy diffs.

## Correct

```markdown
Use semantic line breaks in source files.
They make prose easier to review in Git diffs,
and they help editors revise one clause without rewrapping an entire paragraph.
Rendered Markdown stays the same.
```

Each line maps to a meaningful unit of thought.
Source is easier to scan,
and diffs isolate the real change.

## Guidelines

- Break after every sentence.
- Prefer a break after independent clauses marked by commas, semicolons, colons, or em dashes.
- Add a break after a dependent clause when it clarifies grammar or keeps source manageable.
- Break before a list when the list lead-in reads more clearly as its own unit.
- Keep rendered output unchanged; if a break changes layout, do not use it.
- Do not break inside hyphenated words.
- Treat 80 characters as a strong guideline, but allow longer lines for links, inline code, or other markup.

## When to Apply It

Use semantic line breaks for new or substantially revised prose in Markdown, AsciiDoc, reStructuredText,
and similar formats that collapse single newlines into spaces.
Do not waste time reflowing an entire documentation set at once.
Apply the pattern incrementally as you touch content.

## Git Review Tip

When reviewing prose-heavy changes, prefer `git diff --word-diff` to see word-level edits inside semantically broken lines.
