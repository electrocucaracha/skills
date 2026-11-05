#!/usr/bin/env -S uv --quiet run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.0",
# ]
# ///

"""report.py — Generate the issue-ready Markdown audit report.

Usage::

    python3 scripts/report.py --results <results.json> [--out <report.md>]
        [--strictness normal|strict]

Reads the JSON produced by audit.py and writes a structured Markdown report.
"""

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import click


def _score(rel: str, scores: dict) -> int:
    return scores.get(rel, {}).get("score", 99_999)


def _drift_evidence_count(entry) -> int:
    """entry is [rel, evidence_list, evidence_count] or legacy [rel, evidence_list]."""
    return entry[2] if len(entry) > 2 else len(entry[1])


def _fmt_score(rel: str, scores: dict) -> str:
    s = scores.get(rel, {})
    return f"score={s.get('score', '?')} tier={s.get('tier', '?')} weight={s.get('weight', '?')}"


# Keep the ordered Markdown sections together so the output is easy to audit.
# pylint: disable-next=too-many-locals,too-many-branches,too-many-statements
def build_report(d: dict, strictness: str) -> str:
    """Render audit results as a traffic-prioritized Markdown report."""
    today = datetime.now(UTC).date().isoformat()
    missing = d["missing_in_es"]
    orphan = d["orphan_in_es"]
    drifted = d["drifted"]
    style = d["style_findings"]
    scores = d["scores"]

    missing_by_priority = sorted(missing, key=lambda r: _score(r, scores))
    drifted_by_priority = sorted(drifted, key=lambda x: _score(x[0], scores))

    # Quick wins: missing files already translated in ≥2 other langs AND < 200 lines
    missing_quick_wins = [
        r
        for r in missing_by_priority
        if scores.get(r, {}).get("cross_lang", 0) >= 2
        and scores.get(r, {}).get("lines", 9999) < 200
    ]
    # Quick wins: drifted files with ≤2 evidence items (minimal alignment work)
    drifted_quick_wins = [
        e for e in drifted_by_priority if _drift_evidence_count(e) <= 2
    ]

    lines: list[str] = []
    append_line = lines.append

    # ── header & metadata ───────────────────────────────────────────────────
    append_line("# Kubernetes Spanish Translation Audit")
    append_line("")
    append_line("## Metadata")
    append_line(f"- Date: {today}")
    append_line(
        f"- Repository: {d.get('repo', 'https://github.com/kubernetes/website')}"
    )
    append_line(f"- Scope: {d.get('scope', 'full tree')}")
    append_line(f"- Strictness: {strictness}")
    append_line(
        "- Traffic signal: Hugo frontmatter `weight` + section tier (lower score = higher expected traffic)"
    )
    append_line(
        "- Other languages detected: "
        + ", ".join(d.get("other_langs", []) or ["none detected"])
    )
    append_line("")

    # ── methodology ─────────────────────────────────────────────────────────
    append_line("## Priority Score Methodology")
    append_line("")
    append_line(
        "Three signals are combined into a single composite score per file. Lower score = translate or fix first."
    )
    append_line("")
    append_line("| Signal | Source | Effect |")
    append_line("|--------|--------|--------|")
    append_line(
        "| **Hugo page `weight`** | `weight:` frontmatter in `content/en/*.md` | "
        "Lower weight = higher nav position = more user exposure |"
    )
    append_line(
        "| **Section tier** | Top-level directory | "
        "`concepts/`, `tasks/`, `tutorials/`, `docs/` → tier 1; "
        "`setup/`, `reference/` → tier 2; `blog/`, `community/` → tier 3 |"
    )
    append_line(
        "| **Cross-language coverage** | Presence of same path in other `content/XX` dirs | "
        "Each additional language that translated this page reduces score by 200 pts (up to −1,600) |"
    )
    append_line(
        "| **Quick-win bonus** | Line count of the English file | "
        "Files under 500 lines get up to −500 pts bonus — less effort to translate |"
    )
    append_line("")
    append_line("```")
    append_line(
        "score = (tier × 10,000 + hugo_weight) − (min(cross_lang, 8) × 200) − max(0, 500 − file_lines)"
    )
    append_line("```")
    append_line("")
    append_line(
        "> **Upgrade path to real GA data**: connect the "
        "[GA4 Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)"
    )
    append_line(
        "> with a service-account JSON for the `kubernetes.io` property and pass "
        "`screenPageViews` per URL path into the scoring step of `audit.py`."
    )
    append_line("")

    # ── summary ─────────────────────────────────────────────────────────────
    append_line("## Summary")
    append_line(f"- English files scanned: {d['en_total']}")
    append_line(f"- Spanish files scanned: {d['es_total']}")
    append_line(f"- Paired files: {d['paired']}")
    append_line(f"- Missing in Spanish: {len(missing)}")
    append_line(f"- Orphan in Spanish: {len(orphan)}")
    append_line(f"- Aligned pairs: {d['aligned_count']}")
    append_line(f"- Drifted pairs: {len(drifted)}")
    append_line(f"- Possibly stale: {len(drifted)}")
    append_line(f"- Style consistency findings: {len(style)}")
    append_line("")

    # ── quick wins ───────────────────────────────────────────────────────────
    append_line("## Quick Wins")
    append_line("")
    append_line(
        "Files where the translation effort is minimal: "
        "already translated in other languages (reference available) "
        "and/or structurally close to aligned."
    )
    append_line("")
    append_line(
        "### Missing pages: already translated by ≥2 other languages AND < 200 lines"
    )
    append_line("")
    if missing_quick_wins:
        append_line("| # | Score | XLang | Lines | English file |")
        append_line("|---|-------|-------|-------|--------------|")
        for i, rel in enumerate(missing_quick_wins[:20], 1):
            s = scores.get(rel, {})
            append_line(
                f"| {i} | {s.get('score', '?')} | {s.get('cross_lang', '?')} | "
                f"{s.get('lines', '?')} | `content/en/{rel}` |"
            )
    else:
        append_line("> None found matching criteria (cross_lang ≥ 2, lines < 200).")
    append_line("")
    append_line(
        "### Drifted pages: ≤ 2 structural mismatches (close to aligned, minimal fix)"
    )
    append_line("")
    if drifted_quick_wins:
        append_line("| # | Score | XLang | Evidence items | File |")
        append_line("|---|-------|-------|----------------|------|")
        for i, entry in enumerate(drifted_quick_wins[:20], 1):
            rel = entry[0]
            s = scores.get(rel, {})
            ev_count = _drift_evidence_count(entry)
            append_line(
                f"| {i} | {s.get('score', '?')} | {s.get('cross_lang', '?')} | {ev_count} | `content/es/{rel}` |"
            )
    else:
        append_line("> None found matching criteria (evidence_count ≤ 2).")
    append_line("")

    # ── top-50 missing by traffic ────────────────────────────────────────────
    append_line("## Traffic-Prioritized: Top 50 Missing Translations")
    append_line("")
    append_line(
        "Files in `content/en` with no Spanish counterpart, sorted by composite score (highest priority first)."
    )
    append_line("")
    append_line("| # | Score | Tier | Wt | XLang | Lines | English file |")
    append_line("|---|-------|------|----|-------|-------|--------------|")
    for i, rel in enumerate(missing_by_priority[:50], 1):
        s = scores.get(rel, {})
        append_line(
            f"| {i} | {s.get('score', '?')} | {s.get('tier', '?')} | {s.get('weight', '?')} | "
            f"{s.get('cross_lang', '?')} | {s.get('lines', '?')} | `content/en/{rel}` |"
        )
    append_line("")

    # ── top-30 drifted by traffic ────────────────────────────────────────────
    append_line("## Traffic-Prioritized: Top 30 Drifted / Possibly-Stale Translations")
    append_line("")
    append_line("Paired files with structural divergence, sorted by composite score.")
    append_line("")
    append_line(
        "| # | Score | Tier | Wt | XLang | EvidenceItems | File | Key drift evidence |"
    )
    append_line(
        "|---|-------|------|----|-------|---------------|------|--------------------|"
    )
    for i, entry in enumerate(drifted_by_priority[:30], 1):
        rel, ev = entry[0], entry[1]
        s = scores.get(rel, {})
        ev_count = _drift_evidence_count(entry)
        short_ev = (ev[0][:70].replace("|", "∪")) if ev else "—"
        append_line(
            f"| {i} | {s.get('score', '?')} | {s.get('tier', '?')} | {s.get('weight', '?')} | "
            f"{s.get('cross_lang', '?')} | {ev_count} | `content/es/{rel}` | {short_ev} |"
        )
    append_line("")

    # ── full missing list ────────────────────────────────────────────────────
    append_line(
        f"## Missing in Spanish — Full List ({len(missing)} files, traffic-sorted)"
    )
    append_line("")
    append_line("> First 60 shown individually; remainder grouped by section.")
    append_line("")
    for rel in missing_by_priority[:60]:
        sc = scores.get(rel, {})
        append_line(
            f"- [ ] `content/en/{rel}` → expected `content/es/{rel}` "
            f"_(score {sc.get('score', '?')} · xlang {sc.get('cross_lang', '?')} · "
            f"{sc.get('lines', '?')} lines)_"
        )
    append_line("")
    rest = missing_by_priority[60:]
    if rest:
        sections = Counter(p.split("/")[0] for p in rest)
        append_line(
            f"<details><summary>Remaining {len(rest)} missing files by section</summary>"
        )
        append_line("")
        append_line("| Section | Count |")
        append_line("|---------|-------|")
        for sec, cnt in sorted(sections.items(), key=lambda x: -x[1]):
            append_line(f"| {sec} | {cnt} |")
        append_line("")
        append_line("</details>")
    append_line("")

    # ── orphans ──────────────────────────────────────────────────────────────
    append_line(f"## Orphan in Spanish ({len(orphan)} files)")
    append_line("")
    for f in orphan:
        append_line(f"- [ ] `content/es/{f}` → missing source `content/en/{f}`")
    append_line("")

    # ── full drifted list ────────────────────────────────────────────────────
    append_line(
        f"## Drifted or Possibly Stale Pairs — Full List ({len(drifted)} files, traffic-sorted)"
    )
    append_line("")
    for rel, ev, *_ec in drifted_by_priority:
        s = scores.get(rel, {})
        ev_count = _ec[0] if _ec else len(ev)
        append_line(f"### `content/es/{rel}` _(priority score {s.get('score', '?')})_")
        append_line(f"- Source: `content/en/{rel}`")
        append_line("- Classification: drifted / possibly-stale")
        append_line(
            f"- Traffic signal: tier={s.get('tier', '?')} weight={s.get('weight', '?')}"
        )
        append_line(
            f"- Cross-language coverage: {s.get('cross_lang', '?')} other language(s) have this file"
        )
        append_line(f"- Alignment gap: {ev_count} structural mismatch(es) to fix")
        append_line("- Evidence:")
        for ev_item in ev[:5]:
            append_line(f"  - {ev_item}")
        if len(ev) > 5:
            append_line(f"  - _(+{len(ev) - 5} more section mismatches)_")
        append_line(
            "- Suggested follow-up: Review and realign Spanish sections to match current English structure."
        )
        append_line("")

    # ── style findings ───────────────────────────────────────────────────────
    append_line(f"## Cross-file Spanish Style Findings — {len(style)} findings")
    append_line("")
    for sf in style:
        append_line(f"### {sf['id']}")
        append_line(f"- Impact: {sf['impact']}")
        append_line("- Evidence files:")
        for ef in sf["evidence"][:4]:
            append_line(f"  - `content/es/{ef}`")
        append_line(f"- Observation: {sf['observation']}")
        append_line(f"- Recommendation: {sf['recommendation']}")
        append_line("")

    # ── issue candidates ─────────────────────────────────────────────────────
    append_line("## Issue Candidates (Traffic-Weighted)")
    append_line("")
    append_line("### HIGH — Tier-1 missing translations")
    append_line("- **Severity:** high")
    append_line(
        "- **Title:** Translate highest-traffic tier-1 pages missing in content/es (batch 1)"
    )
    append_line("- **Top affected files:**")
    for rel in missing_by_priority[:10]:
        append_line(f"  - `content/en/{rel}`")
    append_line(
        "- **Rationale:** Pages with weight ≤ 10 in tier-1 sections "
        "are the most user-facing content on kubernetes.io/es."
    )
    append_line("")
    append_line("### HIGH — Drifted tier-1 pages")
    append_line("- **Severity:** high")
    append_line(
        "- **Title:** Realign top drifted Spanish pages to match current English structure"
    )
    append_line("- **Top affected files:**")
    for entry in drifted_by_priority[:8]:
        append_line(f"  - `content/es/{entry[0]}`")
    append_line(
        "- **Rationale:** Foundational pages (score ≤ 10,010) with confirmed structural drift — "
        "missing paragraphs or sections relative to English."
    )
    append_line("")
    append_line("### HIGH — Orphaned Spanish pages")
    append_line("- **Severity:** high")
    append_line(
        f"- **Title:** Remove or redirect {len(orphan)} orphaned content/es pages whose English source was deleted"
    )
    append_line(
        "- **Rationale:** Orphaned pages surface outdated information with no English anchor."
    )
    append_line("")
    tier1_missing = sum(1 for r in missing if scores.get(r, {}).get("tier", 9) == 1)
    append_line("### MEDIUM — Remaining tier-1 missing pages")
    append_line("- **Severity:** medium")
    append_line(
        "- **Title:** Translate remaining tier-1 docs missing a Spanish counterpart"
    )
    append_line(f"- **Affected files:** {tier1_missing} files in tier-1 sections")
    append_line("")
    append_line("### MEDIUM — Mixed imperative register (STYLE-002)")
    append_line("- **Severity:** medium")
    append_line(
        "- **Title:** Standardize Spanish imperative register across content/es"
    )
    append_line("")
    append_line(
        "### LOW — Tier-2/3 missing pages + style normalization (STYLE-001, STYLE-003)"
    )
    append_line("- **Severity:** low")
    append_line(
        "- **Title:** Track tier-2/3 missing pages; normalize anglicisms and Deployment term"
    )
    append_line("")

    # ── next actions ─────────────────────────────────────────────────────────
    append_line("## Next Actions for Project Intake")
    append_line("")
    append_line(
        "- [ ] Open issue for top-10 highest-priority missing pages "
        "(lowest composite score, tier 1) — assign to l10n-spanish contributors"
    )
    append_line(
        "- [ ] Tackle quick-win missing pages first: "
        "already translated in other languages AND < 200 lines — "
        "fastest path to visible coverage increase"
    )
    append_line(
        "- [ ] Open issue for top-10 highest-priority drifted pairs (lowest composite score) — assign for realignment"
    )
    append_line(
        "- [ ] Tackle quick-win drifted pages first: ≤ 2 evidence items — minimal structural diff to fix"
    )
    append_line(
        f"- [ ] Open batch issue for {len(orphan)} orphaned Spanish pages — "
        "assign to l10n-spanish team for deletion or redirect"
    )
    append_line(
        "- [ ] Group remaining tier-1 missing pages into a milestone tracking issue"
    )
    append_line(
        "- [ ] Add STYLE-002 (imperative register) to localization style-guide backlog — "
        "impacts all future translations"
    )
    append_line(
        "- [ ] Add STYLE-001 / STYLE-003 as style-guide clarification issues (lower urgency)"
    )
    append_line(
        "- [ ] _(Optional)_ Replace Hugo-weight proxy with real GA4 page-view data and re-run scoring"
    )

    return "\n".join(lines)


@click.command()
@click.option(
    "--results",
    required=True,
    help="Path to JSON produced by audit.py.",
)
@click.option(
    "--out",
    default=None,
    show_default=True,
    help="Output Markdown path (default: ./reports/k8s-es-translation-audit-YYYY-MM-DD.md).",
)
@click.option(
    "--strictness",
    type=click.Choice(["normal", "strict"]),
    default="normal",
    show_default=True,
    help="Strictness mode label embedded in report metadata.",
)
def main(results: str, out: str | None, strictness: str) -> None:
    """Read audit results and write the issue-ready UTF-8 report."""
    results_path = Path(results)
    if not results_path.exists():
        raise click.ClickException(f"results file not found: {results_path}")

    d = json.loads(results_path.read_text(encoding="utf-8"))
    report = build_report(d, strictness)

    if out:
        out_path = Path(out)
    else:
        out_path = (
            Path("reports")
            / f"k8s-es-translation-audit-{datetime.now(UTC).date().isoformat()}.md"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    click.echo(f"Report written to: {out_path}")


if __name__ == "__main__":
    main()
