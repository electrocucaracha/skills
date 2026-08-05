#!/usr/bin/env -S uv --quiet run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "asyncclick",
#     "mcp[cli]>=1.8.0",
# ]
# ///
"""
check_paragraphs.py — compare heading/paragraph structure of ES files against EN source.

Outputs a JSON file:
{
  "findings": [
    {
      "file": "content/es/docs/...",
      "line": 12,
      "severity": "error|warning|suggestion",
      "code": "PARA-001",
      "message": "..."
    }
  ],
  "errors": [["file", "error message"]]
}
"""

import argparse
from difflib import SequenceMatcher
import json
import re
import unicodedata
from pathlib import Path

CONTEXT_RADIUS = 2


ES_TO_EN_HEADING_MAP = {
    "y": "and",
    "de": "of",
    "del": "of",
    "para": "for",
    "antes": "before",
    "comenzar": "begin",
    "comenzando": "begin",
    "patron": "pattern",
    "patrones": "pattern",
    "controlador": "controller",
    "controladores": "controller",
    "diseno": "design",
    "diseño": "design",
    "forma": "ways",
    "formas": "ways",
    "ejecutar": "running",
    "estado": "state",
    "deseado": "desired",
    "actual": "current",
    "proceso": "process",
    "revision": "review",
    "revisar": "review",
    "revisando": "reviewing",
    "lista": "checklist",
    "verificacion": "checklist",
    "anadir": "adding",
    "agregar": "adding",
    "eliminar": "removing",
    "manejo": "handling",
    "tipos": "types",
    "solicitudes": "requests",
    "soporte": "support",
    "errores": "errors",
    "codigo": "code",
    "etiquetas": "labels",
    "clasificacion": "triage",
    "categorizacion": "categorize",
    "colaboradores": "contributors",
    "aprobadores": "approvers",
    "hacer": "commit",
    "commits": "commit",
    "otra": "another",
    "persona": "person",
}

HEADING_STOPWORDS = {
    "the",
    "a",
    "an",
    "to",
    "for",
    "of",
    "and",
    "in",
    "en",
    "la",
    "el",
    "los",
    "las",
    "un",
    "una",
}


def make_context_window(lines: list[str], line_no: int, radius: int = CONTEXT_RADIUS) -> dict:
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return {
        "context_before": [
            {"line": idx, "text": lines[idx - 1].rstrip()}
            for idx in range(start, line_no)
        ],
        "context_after": [
            {"line": idx, "text": lines[idx - 1].rstrip()}
            for idx in range(line_no + 1, end + 1)
        ],
    }


def en_reference_window(lines: list[str], line_no: int, radius: int = CONTEXT_RADIUS) -> list[dict]:
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return [
        {"line": idx, "text": lines[idx - 1].rstrip()}
        for idx in range(start, end + 1)
    ]


def build_paragraph_writing_hint(section_title: str, en_snippet: list[dict]) -> str:
    """Return a concrete Spanish writing hint for missing/incomplete sections."""
    en_focus = ""
    if en_snippet:
        en_focus = " ".join(
            entry.get("text", "").strip() for entry in en_snippet if entry.get("text")
        )
        en_focus = re.sub(r"\s+", " ", en_focus).strip()
        if len(en_focus) > 220:
            en_focus = en_focus[:219].rstrip() + "…"

    hint = (
        f"Redacción sugerida para la sección «{section_title}»: "
        "comienza con una oración que explique el objetivo de la sección; "
        "continúa con 1-2 oraciones que describan el proceso o criterio técnico principal; "
        "cierra con una acción concreta para la persona que revisa la PR."
    )
    if en_focus:
        hint += f" Referencia EN a cubrir: «{en_focus}»."
    return hint


def _strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )


def _heading_tokens(text: str) -> set[str]:
    # Remove common markdown/hugo heading suffixes that are not translatable prose.
    cleaned = re.sub(r"\{#[^}]+\}", " ", text)
    cleaned = re.sub(r"\{\{[^}]+\}\}", " ", cleaned)

    normalized = _strip_accents(cleaned.lower())
    normalized = re.sub(r"[^a-z0-9\s]+", " ", normalized)
    tokens: list[str] = []
    for raw in normalized.split():
        # Very light stemming to make plural/singular headings comparable.
        if len(raw) > 4 and raw.endswith("s"):
            raw = raw[:-1]
        mapped = ES_TO_EN_HEADING_MAP.get(raw, raw)
        if len(mapped) > 4 and mapped.endswith("s"):
            mapped = mapped[:-1]
        if mapped and mapped not in HEADING_STOPWORDS:
            tokens.append(mapped)
    return set(tokens)


def _heading_match_score(en_heading: str, es_heading: str) -> float:
    en_tokens = _heading_tokens(en_heading)
    es_tokens = _heading_tokens(es_heading)
    if not en_tokens and not es_tokens:
        token_score = 1.0
    elif not en_tokens or not es_tokens:
        token_score = 0.0
    else:
        inter = len(en_tokens & es_tokens)
        union = len(en_tokens | es_tokens)
        token_score = inter / union if union else 0.0

    # Backup character similarity helps with partially untranslated headings (e.g. PR, issue).
    char_score = SequenceMatcher(
        None,
        " ".join(sorted(en_tokens)),
        " ".join(sorted(es_tokens)),
    ).ratio()

    return (0.7 * token_score) + (0.3 * char_score)


def align_h2_headings(en_h2: list[dict], es_h2: list[dict], threshold: float = 0.32) -> tuple[list[dict], list[dict]]:
    """Return (missing_en_h2, extra_es_h2) after fuzzy bilingual heading alignment."""
    unmatched_es_indices = set(range(len(es_h2)))
    missing: list[dict] = []

    for en_h in en_h2:
        best_idx = -1
        best_score = -1.0
        for idx in unmatched_es_indices:
            score = _heading_match_score(en_h["text"], es_h2[idx]["text"])
            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx >= 0 and best_score >= threshold:
            unmatched_es_indices.remove(best_idx)
        else:
            missing.append(en_h)

    extra = [es_h2[idx] for idx in sorted(unmatched_es_indices)]
    return missing, extra

# ── Markdown parsing ──────────────────────────────────────────────────────────


_SKIP_LINE_RE = re.compile(
    r"^\s*```"                    # fenced code block fence
    r"|^\s*\{\{[<{%]"            # Hugo shortcode-only line
    r"|^\s*<!--"                 # HTML comment
    r"|^\s*\|"                   # Markdown table row or separator
    r"|^\s*<[a-zA-Z/]"          # inline HTML tag at line start
)


def _is_prose_line(line: str) -> bool:
    """Return True for lines that carry translatable prose content."""
    stripped = line.strip()
    if not stripped:
        return False
    return not _SKIP_LINE_RE.match(line)


def parse_structure(text: str) -> list[dict]:
    """Return a list of blocks: {type, level, text, line, para_count, prose_lines}."""
    blocks = []
    lines = text.splitlines()
    i = 0
    current_section: dict | None = None
    para_lines: list[str] = []
    in_code_fence = False

    def flush_paras():
        nonlocal para_lines
        if current_section is not None and para_lines:
            combined = "\n".join(para_lines)
            paras = [p.strip() for p in re.split(r"\n\s*\n", combined) if p.strip()]
            current_section["para_count"] = len(paras)
            current_section["prose_lines"] = sum(
                1 for ln in para_lines if _is_prose_line(ln)
            )
        para_lines = []

    while i < len(lines):
        line = lines[i]
        # Track fenced code blocks so we don't count their content as prose.
        if re.match(r"^\s*```", line):
            in_code_fence = not in_code_fence
            if current_section is not None:
                para_lines.append(line)
            i += 1
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line) if not in_code_fence else None
        if heading_match:
            flush_paras()
            level = len(heading_match.group(1))
            text_raw = heading_match.group(2).strip()
            text_clean = re.sub(r"\{\{[^}]+\}\}", "", text_raw).strip()
            current_section = {
                "type": "heading",
                "level": level,
                "text": text_clean,
                "line": i + 1,
                "para_count": 0,
                "prose_lines": 0,
            }
            blocks.append(current_section)
        else:
            if line.strip():
                para_lines.append(line)
            elif para_lines:
                para_lines.append("")
        i += 1

    flush_paras()
    return blocks


def extract_frontmatter(text: str) -> tuple[dict, int]:
    """Return (frontmatter_dict, first_content_line). Very basic YAML extraction."""
    fm: dict = {}
    if not text.startswith("---"):
        return fm, 0
    end = text.find("\n---", 3)
    if end == -1:
        return fm, 0
    fm_text = text[3:end]
    first_line = text[:end].count("\n") + 2
    for line in fm_text.splitlines():
        m = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip("\"'")
    return fm, first_line


# ── Checks ────────────────────────────────────────────────────────────────────


def check_frontmatter(es_path: Path, en_path: Path) -> list[dict]:
    findings = []
    es_text = es_path.read_text(encoding="utf-8", errors="replace")
    en_text = en_path.read_text(encoding="utf-8", errors="replace")
    es_fm, _ = extract_frontmatter(es_text)
    en_fm, _ = extract_frontmatter(en_text)

    required = ["title", "description", "weight", "content_type"]
    for key in required:
        if key in en_fm and key not in es_fm:
            findings.append(
                {
                    "file": str(es_path),
                    "line": 1,
                    "severity": "error",
                    "code": "PARA-001",
                    "message": (
                        f"Frontmatter falta el campo obligatorio `{key}`. "
                        f"El archivo EN tiene: `{key}: {en_fm[key]}`."
                    ),
                    "suggestion": (
                        f"Añadir `{key}: {en_fm[key]}` al frontmatter del archivo ES "
                        "y ajustar la traducción solo si el valor requiere localización."
                    ),
                }
            )
    return findings


def check_structure(es_path: Path, en_path: Path, en_rel: str) -> list[dict]:
    findings = []
    es_text = es_path.read_text(encoding="utf-8", errors="replace")
    en_text = en_path.read_text(encoding="utf-8", errors="replace")
    en_lines = en_text.splitlines()

    # Conflict markers
    for i, line in enumerate(es_text.splitlines(), 1):
        if re.match(r"^(<{7}|={7}|>{7})", line):
            findings.append(
                {
                    "file": str(es_path),
                    "line": i,
                    "severity": "error",
                    "code": "PARA-002",
                    "message": "Marcador de conflicto de merge sin resolver. Debe eliminarse antes del merge.",
                    "suggestion": "Resolver el conflicto, conservar solo el contenido final y eliminar las marcas `<<<<<<<`, `=======` y `>>>>>>>`.",
                }
            )

    es_blocks = parse_structure(es_text)
    en_blocks = parse_structure(en_text)

    es_headings = [b for b in es_blocks if b["type"] == "heading"]
    en_headings = [b for b in en_blocks if b["type"] == "heading"]

    # Check paragraph count ratio per section (> 60% threshold)
    # PARA-003 / PARA-007: compare para count and prose line count per section.
    # Uses bilingual fuzzy alignment so translated headings are matched correctly.
    en_h2_all = [h for h in en_headings if h["level"] == 2]
    es_h2_all = [h for h in es_headings if h["level"] == 2]

    # Build a mapping from each ES h2 to its best-matching EN h2 via fuzzy score.
    MATCH_THRESHOLD = 0.32
    unmatched_en = list(range(len(en_h2_all)))
    es_to_en: dict[int, int] = {}  # es_idx -> en_idx
    for es_idx, es_h in enumerate(es_h2_all):
        best_score = -1.0
        best_en_idx = -1
        for en_idx in unmatched_en:
            score = _heading_match_score(en_h2_all[en_idx]["text"], es_h["text"])
            if score > best_score:
                best_score = score
                best_en_idx = en_idx
        if best_en_idx >= 0 and best_score >= MATCH_THRESHOLD:
            es_to_en[es_idx] = best_en_idx
            unmatched_en.remove(best_en_idx)

    for es_idx, es_h in enumerate(es_h2_all):
        en_idx = es_to_en.get(es_idx)
        if en_idx is None:
            continue
        en_h = en_h2_all[en_idx]

        en_pc = en_h.get("para_count", 0)
        es_pc = es_h.get("para_count", 0)
        if en_pc > 1 and es_pc < en_pc * 0.5:
            ref_line = en_h.get("line", 1)
            ref_context = en_reference_window(en_lines, ref_line)
            findings.append(
                {
                    "file": str(es_path),
                    "line": es_h["line"],
                    "severity": "warning",
                    "code": "PARA-003",
                    "message": (
                        f"La sección «{es_h['text']}» tiene {es_pc} párrafo(s) pero el original "
                        f"en inglés tiene {en_pc}. El contenido podría estar incompleto."
                    ),
                    "suggestion": (
                        "Comparar esta sección con el original EN y completar los párrafos "
                        "o detalles técnicos que todavía no aparecen en la traducción. "
                        + build_paragraph_writing_hint(es_h["text"], ref_context)
                    ),
                    "reference_file": en_rel,
                    "reference_line": ref_line,
                    "reference_context": ref_context,
                }
            )

        # Semantic line-break alignment: compare prose line counts per section.
        # EN uses one sentence/clause per line (semantic line breaks); ES should
        # have a comparable number of prose lines.  A ratio < 0.55 suggests
        # that sentences were merged and content may have been silently dropped.
        en_pl = en_h.get("prose_lines", 0)
        es_pl = es_h.get("prose_lines", 0)
        if en_pl >= 4 and es_pl < en_pl * 0.55:
            ref_line = en_h.get("line", 1)
            ref_context = en_reference_window(en_lines, ref_line)
            findings.append(
                {
                    "file": str(es_path),
                    "line": es_h["line"],
                    "severity": "warning",
                    "code": "PARA-007",
                    "message": (
                        f"La sección «{es_h['text']}» tiene {es_pl} línea(s) de prosa pero "
                        f"el original EN tiene {en_pl}. "
                        "El EN usa saltos de línea semánticos (una oración por línea); "
                        "la traducción ES parece haber comprimido varias oraciones en menos líneas, "
                        "lo que puede indicar contenido omitido."
                    ),
                    "suggestion": (
                        "Revisar párrafo a párrafo en la sección EN y verificar que cada "
                        "oración o cláusula del original esté presente en la traducción. "
                        "Aplicar saltos de línea semánticos en ES para facilitar revisiones futuras. "
                        + build_paragraph_writing_hint(es_h["text"], ref_context)
                    ),
                    "reference_file": en_rel,
                    "reference_line": ref_line,
                    "reference_context": ref_context,
                }
            )

    # Sections present in EN but missing in ES (level 2 headings, bilingual fuzzy matching)
    missing_h2, extra_h2 = align_h2_headings(en_h2_all, es_h2_all)

    for missing_h in missing_h2:
        ref_line = missing_h["line"]
        missing = missing_h["text"].lower()
        ref_context = en_reference_window(en_lines, ref_line) if ref_line else []
        findings.append(
            {
                "file": str(es_path),
                "line": 1,
                "severity": "error",
                "code": "PARA-004",
                "message": (
                    f"La sección de nivel 2 «{missing}» existe en el original EN (línea {ref_line}) "
                    "pero no se encontró en la traducción ES."
                ),
                "suggestion": (
                    "Añadir esta sección al archivo ES y traducir el contenido de la sección "
                    f"correspondiente en `{en_path.name}` empezando cerca de la línea {ref_line}. "
                    + build_paragraph_writing_hint(missing_h["text"], ref_context)
                ),
                "reference_file": en_rel,
                "reference_line": ref_line,
                "reference_context": ref_context,
            }
        )

    # Extra sections in ES not present in EN
    for extra_h in extra_h2:
        extra = extra_h["text"].lower()
        es_line = extra_h["line"]
        findings.append(
            {
                "file": str(es_path),
                "line": es_line,
                "severity": "warning",
                "code": "PARA-005",
                "message": (
                    f"La sección de nivel 2 «{extra}» está en la traducción ES pero no existe "
                    "en el original EN. Verificar si es intencional."
                ),
                "suggestion": (
                    "Confirmar si la sección adicional debe mantenerse. "
                    "Si no es intencional, alinearla con la estructura del archivo EN."
                ),
            }
        )

    return findings


def process_file(es_rel: str, repo: Path) -> tuple[list[dict], str | None]:
    """Return (findings, error_message)."""
    es_path = repo / es_rel
    en_rel = es_rel.replace("content/es/", "content/en/", 1)
    en_path = repo / en_rel

    if not es_path.exists():
        return [], f"ES file not found: {es_rel}"
    if not en_path.exists():
        return [
            {
                "file": es_rel,
                "line": 1,
                "severity": "error",
                "code": "PARA-006",
                "message": (
                    f"No existe un archivo EN equivalente en `{en_rel}`. "
                    "Este archivo ES es un huérfano sin fuente inglesa."
                ),
                "suggestion": (
                    "Verificar si el archivo EN cambió de ruta, fue eliminado o falta en el checkout. "
                    "Si no hay fuente EN, coordinar antes de mantener una página ES huérfana."
                ),
            }
        ], None

    findings = []
    try:
        findings += check_frontmatter(es_path, en_path)
        findings += check_structure(es_path, en_path, en_rel)
    except Exception as exc:
        return findings, str(exc)

    # Normalise file field and attach the actual line text for context
    es_lines = es_path.read_text(encoding="utf-8", errors="replace").splitlines()
    for f in findings:
        f["file"] = es_rel
        ln = f.get("line", 1)
        if isinstance(ln, int) and 1 <= ln <= len(es_lines):
            f.setdefault("line_text", es_lines[ln - 1].rstrip())
            for key, value in make_context_window(es_lines, ln).items():
                f.setdefault(key, value)

    return findings, None


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument(
        "--files", required=True, help="Comma-separated list of relative file paths"
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    repo = Path(args.repo)
    files = [f.strip() for f in args.files.split(",") if f.strip()]

    all_findings: list[dict] = []
    errors: list[list[str]] = []

    for es_rel in files:
        findings, err = process_file(es_rel, repo)
        all_findings.extend(findings)
        if err:
            errors.append([es_rel, err])

    result = {"findings": all_findings, "errors": errors}
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"check_paragraphs: {len(all_findings)} finding(s), {len(errors)} error(s)")


if __name__ == "__main__":
    main()
