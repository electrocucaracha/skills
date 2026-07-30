#!/usr/bin/env -S uv --quiet run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.0",
# ]
# ///

"""report.py — Generate the issue-ready Markdown audit report.

Usage::

    python3 scripts/report.py --results <results.json> [--out <report.md>] [--strictness normal|strict]

Reads the JSON produced by audit.py and writes a structured Markdown report.
"""

import json
from collections import Counter
from datetime import date
from pathlib import Path

import click


def _score(rel: str, scores: dict) -> int:
    return scores.get(rel, {}).get("score", 99_999)


def _drift_evidence_count(entry) -> int:
    """entry is [rel, evidence_list, evidence_count] or legacy [rel, evidence_list]."""
    return entry[2] if len(entry) > 2 else len(entry[1])


def _fmt_score(rel: str, scores: dict) -> str:
    s = scores.get(rel, {})
    return f"score={s.get('score','?')} tier={s.get('tier','?')} weight={s.get('weight','?')}"


def build_report(d: dict, strictness: str) -> str:
    today = date.today().isoformat()
    missing = d["missing_in_es"]
    orphan = d["orphan_in_es"]
    drifted = d["drifted"]
    style = d["style_findings"]
    scores = d["scores"]

    missing_by_priority = sorted(missing, key=lambda r: _score(r, scores))
    drifted_by_priority = sorted(drifted, key=lambda x: _score(x[0], scores))

    # Quick wins: missing files already translated in ≥2 other langs AND < 200 lines
    missing_quick_wins = [
        r for r in missing_by_priority
        if scores.get(r, {}).get("cross_lang", 0) >= 2
        and scores.get(r, {}).get("lines", 9999) < 200
    ]
    # Quick wins: drifted files with ≤2 evidence items (minimal alignment work)
    drifted_quick_wins = [
        e for e in drifted_by_priority
        if _drift_evidence_count(e) <= 2
    ]

    lines: list[str] = []
    A = lines.append

    # ── header & metadata ───────────────────────────────────────────────────
    A("# Kubernetes Spanish Translation Audit")
    A("")
    A("## Metadata")
    A(f"- Date: {today}")
    A(f"- Repository: {d.get('repo', 'https://github.com/kubernetes/website')}")
    A(f"- Scope: {d.get('scope', 'full tree')}")
    A(f"- Strictness: {strictness}")
    A("- Traffic signal: Hugo frontmatter `weight` + section tier (lower score = higher expected traffic)")
    A("- Other languages detected: " + ", ".join(d.get("other_langs", []) or ["none detected"]))
    A("")

    # ── methodology ─────────────────────────────────────────────────────────
    A("## Priority Score Methodology")
    A("")
    A("Three signals are combined into a single composite score per file. Lower score = translate or fix first.")
    A("")
    A("| Signal | Source | Effect |")
    A("|--------|--------|--------|")
    A("| **Hugo page `weight`** | `weight:` frontmatter in `content/en/*.md` | Lower weight = higher nav position = more user exposure |")
    A("| **Section tier** | Top-level directory | `concepts/`, `tasks/`, `tutorials/`, `docs/` → tier 1; `setup/`, `reference/` → tier 2; `blog/`, `community/` → tier 3 |")
    A("| **Cross-language coverage** | Presence of same path in other `content/XX` dirs | Each additional language that translated this page reduces score by 200 pts (up to −1,600) |")
    A("| **Quick-win bonus** | Line count of the English file | Files under 500 lines get up to −500 pts bonus — less effort to translate |")
    A("")
    A("```")
    A("score = (tier × 10,000 + hugo_weight) − (min(cross_lang, 8) × 200) − max(0, 500 − file_lines)")
    A("```")
    A("")
    A("> **Upgrade path to real GA data**: connect the [GA4 Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)")
    A("> with a service-account JSON for the `kubernetes.io` property and pass `screenPageViews` per URL path into the scoring step of `audit.py`.")
    A("")

    # ── summary ─────────────────────────────────────────────────────────────
    A("## Summary")
    A(f"- English files scanned: {d['en_total']}")
    A(f"- Spanish files scanned: {d['es_total']}")
    A(f"- Paired files: {d['paired']}")
    A(f"- Missing in Spanish: {len(missing)}")
    A(f"- Orphan in Spanish: {len(orphan)}")
    A(f"- Aligned pairs: {d['aligned_count']}")
    A(f"- Drifted pairs: {len(drifted)}")
    A(f"- Possibly stale: {len(drifted)}")
    A(f"- Style consistency findings: {len(style)}")
    A("")

    # ── quick wins ───────────────────────────────────────────────────────────
    A("## Quick Wins")
    A("")
    A("Files where the translation effort is minimal: already translated in other languages (reference available) and/or structurally close to aligned.")
    A("")
    A("### Missing pages: already translated by ≥2 other languages AND < 200 lines")
    A("")
    if missing_quick_wins:
        A("| # | Score | XLang | Lines | English file |")
        A("|---|-------|-------|-------|--------------|")
        for i, rel in enumerate(missing_quick_wins[:20], 1):
            s = scores.get(rel, {})
            A(f"| {i} | {s.get('score','?')} | {s.get('cross_lang','?')} | {s.get('lines','?')} | `content/en/{rel}` |")
    else:
        A("> None found matching criteria (cross_lang ≥ 2, lines < 200).")
    A("")
    A("### Drifted pages: ≤ 2 structural mismatches (close to aligned, minimal fix)")
    A("")
    if drifted_quick_wins:
        A("| # | Score | XLang | Evidence items | File |")
        A("|---|-------|-------|----------------|------|")
        for i, entry in enumerate(drifted_quick_wins[:20], 1):
            rel = entry[0]
            s = scores.get(rel, {})
            ev_count = _drift_evidence_count(entry)
            A(f"| {i} | {s.get('score','?')} | {s.get('cross_lang','?')} | {ev_count} | `content/es/{rel}` |")
    else:
        A("> None found matching criteria (evidence_count ≤ 2).")
    A("")

    # ── top-50 missing by traffic ────────────────────────────────────────────
    A(f"## Traffic-Prioritized: Top 50 Missing Translations")
    A("")
    A("Files in `content/en` with no Spanish counterpart, sorted by composite score (highest priority first).")
    A("")
    A("| # | Score | Tier | Wt | XLang | Lines | English file |")
    A("|---|-------|------|----|-------|-------|--------------|")
    for i, rel in enumerate(missing_by_priority[:50], 1):
        s = scores.get(rel, {})
        A(f"| {i} | {s.get('score','?')} | {s.get('tier','?')} | {s.get('weight','?')} | {s.get('cross_lang','?')} | {s.get('lines','?')} | `content/en/{rel}` |")
    A("")

    # ── top-30 drifted by traffic ────────────────────────────────────────────
    A(f"## Traffic-Prioritized: Top 30 Drifted / Possibly-Stale Translations")
    A("")
    A("Paired files with structural divergence, sorted by composite score.")
    A("")
    A("| # | Score | Tier | Wt | XLang | EvidenceItems | File | Key drift evidence |")
    A("|---|-------|------|----|-------|---------------|------|--------------------|")
    for i, entry in enumerate(drifted_by_priority[:30], 1):
        rel, ev = entry[0], entry[1]
        s = scores.get(rel, {})
        ev_count = _drift_evidence_count(entry)
        short_ev = (ev[0][:70].replace("|", "∪")) if ev else "—"
        A(f"| {i} | {s.get('score','?')} | {s.get('tier','?')} | {s.get('weight','?')} | {s.get('cross_lang','?')} | {ev_count} | `content/es/{rel}` | {short_ev} |")
    A("")

    # ── full missing list ────────────────────────────────────────────────────
    A(f"## Missing in Spanish — Full List ({len(missing)} files, traffic-sorted)")
    A("")
    A("> First 60 shown individually; remainder grouped by section.")
    A("")
    for rel in missing_by_priority[:60]:
        sc = scores.get(rel, {})
        A(f"- [ ] `content/en/{rel}` → expected `content/es/{rel}` _(score {sc.get('score','?')} · xlang {sc.get('cross_lang','?')} · {sc.get('lines','?')} lines)_")
    A("")
    rest = missing_by_priority[60:]
    if rest:
        sections = Counter(p.split("/")[0] for p in rest)
        A(f"<details><summary>Remaining {len(rest)} missing files by section</summary>")
        A("")
        A("| Section | Count |")
        A("|---------|-------|")
        for sec, cnt in sorted(sections.items(), key=lambda x: -x[1]):
            A(f"| {sec} | {cnt} |")
        A("")
        A("</details>")
    A("")

    # ── orphans ──────────────────────────────────────────────────────────────
    A(f"## Orphan in Spanish ({len(orphan)} files)")
    A("")
    for f in orphan:
        A(f"- [ ] `content/es/{f}` → missing source `content/en/{f}`")
    A("")

    # ── full drifted list ────────────────────────────────────────────────────
    A(f"## Drifted or Possibly Stale Pairs — Full List ({len(drifted)} files, traffic-sorted)")
    A("")
    for rel, ev, *_ec in drifted_by_priority:
        s = scores.get(rel, {})
        ev_count = _ec[0] if _ec else len(ev)
        A(f"### `content/es/{rel}` _(priority score {s.get('score','?')})_")
        A(f"- Source: `content/en/{rel}`")
        A(f"- Classification: drifted / possibly-stale")
        A(f"- Traffic signal: tier={s.get('tier','?')} weight={s.get('weight','?')}")
        A(f"- Cross-language coverage: {s.get('cross_lang','?')} other language(s) have this file")
        A(f"- Alignment gap: {ev_count} structural mismatch(es) to fix")
        A("- Evidence:")
        for ev_item in ev[:5]:
            A(f"  - {ev_item}")
        if len(ev) > 5:
            A(f"  - _(+{len(ev) - 5} more section mismatches)_")
        A("- Suggested follow-up: Review and realign Spanish sections to match current English structure.")
        A("")

    # ── style findings ───────────────────────────────────────────────────────
    A(f"## Cross-file Spanish Style Findings — {len(style)} findings")
    A("")
    for sf in style:
        A(f"### {sf['id']}")
        A(f"- Impact: {sf['impact']}")
        A("- Evidence files:")
        for ef in sf["evidence"][:4]:
            A(f"  - `content/es/{ef}`")
        A(f"- Observation: {sf['observation']}")
        A(f"- Recommendation: {sf['recommendation']}")
        A("")

    # ── issue candidates ─────────────────────────────────────────────────────
    A("## Issue Candidates (Traffic-Weighted)")
    A("")
    A("### HIGH — Tier-1 missing translations")
    A("- **Severity:** high")
    A("- **Title:** Translate highest-traffic tier-1 pages missing in content/es (batch 1)")
    A("- **Top affected files:**")
    for rel in missing_by_priority[:10]:
        A(f"  - `content/en/{rel}`")
    A("- **Rationale:** Pages with weight ≤ 10 in tier-1 sections are the most user-facing content on kubernetes.io/es.")
    A("")
    A("### HIGH — Drifted tier-1 pages")
    A("- **Severity:** high")
    A("- **Title:** Realign top drifted Spanish pages to match current English structure")
    A("- **Top affected files:**")
    for entry in drifted_by_priority[:8]:
        A(f"  - `content/es/{entry[0]}`")
    A("- **Rationale:** Foundational pages (score ≤ 10,010) with confirmed structural drift — missing paragraphs or sections relative to English.")
    A("")
    A("### HIGH — Orphaned Spanish pages")
    A("- **Severity:** high")
    A(f"- **Title:** Remove or redirect {len(orphan)} orphaned content/es pages whose English source was deleted")
    A("- **Rationale:** Orphaned pages surface outdated information with no English anchor.")
    A("")
    tier1_missing = sum(1 for r in missing if scores.get(r, {}).get("tier", 9) == 1)
    A("### MEDIUM — Remaining tier-1 missing pages")
    A("- **Severity:** medium")
    A("- **Title:** Translate remaining tier-1 docs missing a Spanish counterpart")
    A(f"- **Affected files:** {tier1_missing} files in tier-1 sections")
    A("")
    A("### MEDIUM — Mixed imperative register (STYLE-002)")
    A("- **Severity:** medium")
    A("- **Title:** Standardize Spanish imperative register across content/es")
    A("")
    A("### LOW — Tier-2/3 missing pages + style normalization (STYLE-001, STYLE-003)")
    A("- **Severity:** low")
    A("- **Title:** Track tier-2/3 missing pages; normalize anglicisms and Deployment term")
    A("")

    # ── next actions ─────────────────────────────────────────────────────────
    A("## Next Actions for Project Intake")
    A("")
    A("- [ ] Open issue for top-10 highest-priority missing pages (lowest composite score, tier 1) — assign to l10n-spanish contributors")
    A("- [ ] Tackle quick-win missing pages first: already translated in other languages AND < 200 lines — fastest path to visible coverage increase")
    A("- [ ] Open issue for top-10 highest-priority drifted pairs (lowest composite score) — assign for realignment")
    A("- [ ] Tackle quick-win drifted pages first: ≤ 2 evidence items — minimal structural diff to fix")
    A(f"- [ ] Open batch issue for {len(orphan)} orphaned Spanish pages — assign to l10n-spanish team for deletion or redirect")
    A("- [ ] Group remaining tier-1 missing pages into a milestone tracking issue")
    A("- [ ] Add STYLE-002 (imperative register) to localization style-guide backlog — impacts all future translations")
    A("- [ ] Add STYLE-001 / STYLE-003 as style-guide clarification issues (lower urgency)")
    A("- [ ] _(Optional)_ Replace Hugo-weight proxy with real GA4 page-view data and re-run scoring")

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
    results_path = Path(results)
    if not results_path.exists():
        raise click.ClickException(f"results file not found: {results_path}")

    d = json.loads(results_path.read_text())
    report = build_report(d, strictness)

    if out:
        out_path = Path(out)
    else:
        out_path = (
            Path("reports") / f"k8s-es-translation-audit-{date.today().isoformat()}.md"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    click.echo(f"Report written to: {out_path}")


if __name__ == "__main__":
    main()
