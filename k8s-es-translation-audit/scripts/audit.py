#!/usr/bin/env -S uv --quiet run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.0",
# ]
# ///

"""audit.py — Kubernetes Spanish translation auditor.

Usage::

    python3 scripts/audit.py --repo <path-to-website-clone> [--scope <subpath>] [--out <results.json>]

Outputs a single JSON file consumed by report.py.
"""

import json
import re
from pathlib import Path

import click


# ---------------------------------------------------------------------------
# Section-level traffic tier for kubernetes.io (empirical)
# Lower tier = higher expected traffic.
# ---------------------------------------------------------------------------
SECTION_TIER: dict[str, int] = {
    "concepts": 1,
    "tasks": 1,
    "tutorials": 1,
    "docs": 1,
    "home": 1,
    "setup": 2,
    "reference": 2,
    "releases": 2,
    "blog": 3,
    "training": 3,
    "community": 3,
    "case-studies": 3,
    "partners": 3,
}

# Style patterns
_TU_VERBS = re.compile(
    r"\b(ejecuta|abre|usa|escribe|ingresa|verifica|instala|crea|añade|elimina)\b"
)
_USTED_VERBS = re.compile(
    r"\b(ejecute|abra|use|escriba|ingrese|verifique|instale|cree|añada|elimine)\b"
)
_CLUSTER_ACCENTED = re.compile(r"\bclúster\b")
_CLUSTER_PLAIN = re.compile(r"\bcluster\b", re.IGNORECASE)
_DEPLOYMENT_ES = re.compile(r"\bdespliegue\b", re.IGNORECASE)
_DEPLOYMENT_EN = re.compile(r"\bDeployment\b")


def md_files(base: Path, scope: str | None) -> set[str]:
    root = base / scope if scope else base
    if not root.exists():
        return set()
    return {
        str(p.relative_to(base))
        for p in root.rglob("*")
        if p.suffix in (".md", ".mdx") and p.is_file()
    }


def get_frontmatter_weight(path: Path) -> int:
    try:
        text = path.read_text(errors="replace")
        m = re.search(r"^weight:\s*(\d+)", text, re.MULTILINE)
        return int(m.group(1)) if m else 999
    except Exception:
        return 999


def section_tier(rel: str) -> int:
    return SECTION_TIER.get(rel.split("/")[0], 2)


def cross_lang_count(rel: str, other_lang_dirs: list[Path]) -> int:
    """Count non-en/es language dirs that contain this file."""
    return sum(1 for d in other_lang_dirs if (d / rel).exists())


def file_lines(path: Path) -> int:
    try:
        return len(path.read_text(errors="replace").splitlines())
    except Exception:
        return 999


def composite_score(rel: str, weight: int, xlang: int, lines: int) -> int:
    """Lower = higher priority.

    Base: tier × 10_000 + hugo_weight
    Cross-language bonus: up to -1_600 pts (8 langs × 200) — more translations = more important
    Quick-win bonus: up to -500 pts for files < 500 lines — smaller = less effort
    """
    base = section_tier(rel) * 10_000 + weight
    xlang_bonus = min(xlang, 8) * 200
    qw_bonus = max(0, 500 - lines) if lines < 500 else 0
    return base - xlang_bonus - qw_bonus


def parse_structure(text: str) -> dict[str, dict]:
    """Return {heading: {paragraphs, lists, code_blocks}} per section."""
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_h = "__preamble__"
    buf: list[str] = []
    for line in lines:
        if re.match(r"^#{1,6}\s", line):
            sections.append((current_h, buf))
            current_h = line.strip()
            buf = []
        else:
            buf.append(line)
    sections.append((current_h, buf))

    result = {}
    for heading, body in sections:
        body_text = "\n".join(body)
        result[heading] = {
            "paragraphs": len([p for p in re.split(r"\n{2,}", body_text) if p.strip()]),
            "lists": len(re.findall(r"^[\-\*\+]\s|\d+\.\s", body_text, re.MULTILINE)),
            "code_blocks": len(re.findall(r"```", body_text)) // 2,
        }
    return result


def compare_structures(
    en_struct: dict, es_struct: dict
) -> tuple[str, list[str]]:
    evidence: list[str] = []
    es_headings = set(es_struct.keys())
    for h in en_struct:
        if h == "__preamble__":
            continue
        if h not in es_headings:
            evidence.append(f"Section '{h}' present in EN but absent in ES")
            continue
        diffs = [
            f"{m}: EN={en_struct[h][m]} ES={es_struct[h][m]}"
            for m in ("paragraphs", "lists", "code_blocks")
            if en_struct[h][m] != es_struct[h][m]
        ]
        if diffs:
            evidence.append(f"Section '{h}': " + ", ".join(diffs))
    return ("drifted" if evidence else "aligned", evidence)


def _discover_other_langs(repo: Path) -> list[Path]:
    content_dir = repo / "content"
    try:
        return [
            d for d in content_dir.iterdir()
            if d.is_dir() and d.name not in ("en", "es")
        ]
    except Exception:
        return []


def run_style_analysis(es_root: Path, paired: list[str]) -> list[dict]:
    sample = paired[:80]
    findings = []

    accent_files: list[str] = []
    plain_files: list[str] = []
    tu_files: list[str] = []
    usted_files: list[str] = []
    desp_files: list[str] = []
    depl_files: list[str] = []

    for rel in sample:
        try:
            text = (es_root / rel).read_text(errors="replace")
        except Exception:
            continue
        if _CLUSTER_ACCENTED.search(text):
            accent_files.append(rel)
        if _CLUSTER_PLAIN.search(text):
            plain_files.append(rel)
        if _TU_VERBS.search(text):
            tu_files.append(rel)
        if _USTED_VERBS.search(text):
            usted_files.append(rel)
        if _DEPLOYMENT_EN.search(text):
            desp_files.append(rel)
        if _DEPLOYMENT_ES.search(text):
            depl_files.append(rel)

    if accent_files and plain_files:
        findings.append({
            "id": "STYLE-001",
            "impact": "minor",
            "evidence": (accent_files[:2] + plain_files[:2]),
            "observation": "Mixed usage of 'clúster' (accented) vs 'cluster' (unaccented) across content/es files.",
            "recommendation": (
                "Standardize on 'clúster' per RAE guidelines or 'cluster' per Kubernetes "
                "project convention. Document the chosen form in the localization style guide."
            ),
        })

    if tu_files and usted_files:
        findings.append({
            "id": "STYLE-002",
            "impact": "major",
            "evidence": (tu_files[:2] + usted_files[:2]),
            "observation": (
                "Mixed imperative register: some files use 'tú' forms (ejecuta, usa) "
                "while others use 'usted' forms (ejecute, use)."
            ),
            "recommendation": (
                "Align all docs to 'usted' form as specified in the Kubernetes Spanish "
                "localization guide."
            ),
        })

    if desp_files and depl_files:
        findings.append({
            "id": "STYLE-003",
            "impact": "minor",
            "evidence": (desp_files[:2] + depl_files[:2]),
            "observation": (
                "Inconsistent translation of 'Deployment': some files keep the English "
                "term, others use 'despliegue'."
            ),
            "recommendation": (
                "Keep 'Deployment' as a proper noun when referring to the API object; "
                "use 'despliegue' only for the general concept."
            ),
        })

    return findings


@click.command()
@click.option("--repo", required=True, help="Path to kubernetes/website clone.")
@click.option(
    "--scope",
    default=None,
    show_default=True,
    help="Subpath under content/en to limit scan.",
)
@click.option(
    "--out",
    default="/tmp/k8s_audit_results.json",
    show_default=True,
    help="Output JSON path.",
)
def main(repo: str, scope: str | None, out: str) -> None:
    repo_path = Path(repo)
    en_root = repo_path / "content/en"
    es_root = repo_path / "content/es"

    if not en_root.exists() or not es_root.exists():
        raise click.ClickException(
            f"content/en or content/es not found under {repo_path}"
        )

    click.echo("Building file inventories…", err=True)
    en_files = md_files(en_root, scope)
    es_files = md_files(es_root, scope)

    missing_in_es = sorted(en_files - es_files)
    orphan_in_es = sorted(es_files - en_files)
    paired = sorted(en_files & es_files)

    click.echo(
        f"  EN={len(en_files)}  ES={len(es_files)}  paired={len(paired)}",
        err=True,
    )

    other_lang_dirs = _discover_other_langs(repo_path)
    click.echo(
        f"  Other language trees found: {[d.name for d in other_lang_dirs]}",
        err=True,
    )

    scores: dict[str, dict] = {}
    for rel in missing_in_es:
        en_path = en_root / rel
        w = get_frontmatter_weight(en_path)
        xl = cross_lang_count(rel, other_lang_dirs)
        ln = file_lines(en_path)
        scores[rel] = {
            "weight": w,
            "tier": section_tier(rel),
            "cross_lang": xl,
            "lines": ln,
            "score": composite_score(rel, w, xl, ln),
        }

    click.echo("Comparing paired file structures…", err=True)
    drifted: list[tuple[str, list[str], int]] = []
    aligned_count = 0
    errors: list[tuple[str, str]] = []

    for rel in paired:
        try:
            en_path = en_root / rel
            en_text = en_path.read_text(errors="replace")
            es_text = (es_root / rel).read_text(errors="replace")
            status, evidence = compare_structures(
                parse_structure(en_text),
                parse_structure(es_text),
            )
            w = get_frontmatter_weight(en_path)
            xl = cross_lang_count(rel, other_lang_dirs)
            ln = file_lines(en_path)
            scores[rel] = {
                "weight": w,
                "tier": section_tier(rel),
                "cross_lang": xl,
                "lines": ln,
                "score": composite_score(rel, w, xl, ln),
            }
            if status == "drifted":
                drifted.append((rel, evidence, len(evidence)))
            else:
                aligned_count += 1
        except Exception as exc:
            errors.append((rel, str(exc)))

    click.echo("Running Spanish style analysis…", err=True)
    style_findings = run_style_analysis(es_root, paired)

    results = {
        "en_total": len(en_files),
        "es_total": len(es_files),
        "paired": len(paired),
        "missing_in_es": missing_in_es,
        "orphan_in_es": orphan_in_es,
        "drifted": drifted,  # each entry: [rel, evidence_list, evidence_count]
        "aligned_count": aligned_count,
        "style_findings": style_findings,
        "scores": scores,
        "errors": errors,
        "scope": scope or "full tree",
        "repo": str(repo_path),
        "other_langs": [d.name for d in other_lang_dirs],
    }

    out_path = Path(out)
    out_path.write_text(json.dumps(results, indent=2))
    click.echo(f"Results written to: {out_path}", err=True)
    click.echo(
        f"Summary: missing={len(missing_in_es)} orphan={len(orphan_in_es)}"
        f" drifted={len(drifted)} aligned={aligned_count}"
        f" style={len(style_findings)}",
        err=True,
    )


if __name__ == "__main__":
    main()
