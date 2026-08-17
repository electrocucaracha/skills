#!/usr/bin/env python3
"""Repair knowledge base CLI: template, validate, index, query, outcome.

The knowledge base is a directory tree (default: .repair-kb, override with
--root or REPAIR_KB_ROOT):

    <root>/index.md
    <root>/taxonomy.md
    <root>/nodes/L1|L2|L3/<node-id>.md
    <root>/trajectories/<trajectory-id>.md

Node frontmatter uses a small YAML subset: scalars, inline lists, block lists,
folded scalars, and one level of nested mappings. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import datetime
import os
import pathlib
import re
import sys

LEVELS = ("L1", "L2", "L3")
STAGES = ("localization", "planning", "execution-verification")
STAGE_ABBR = {
    "localization": "loc",
    "planning": "plan",
    "execution-verification": "exec",
}
TRANSFER_BY_LEVEL = {
    "L1": "repo-specific",
    "L2": "project-agnostic",
    "L3": "universal",
}
OUTCOMES = ("verified", "partial", "unverified", "refuted")
LABELS = {
    "verified": "verified_count",
    "partial": None,
    "wrong-location": None,
    "over-modification": None,
    "refuted": "refuted_count",
}
LABEL_ADVICE = {
    "partial": "widen key_actions scope in the planning node",
    "wrong-location": "fix applicable_when and add a pitfall to the "
    "localization node",
    "over-modification": "add a minimality constraint to the planning node",
    "refuted": "narrow applicable_when or portability",
}

REQUIRED = (
    "id",
    "level",
    "stage",
    "failure_class",
    "title",
    "intent",
    "applicable_when",
    "key_actions",
    "verification",
    "pitfalls",
    "portability",
    "evidence",
    "retrieval_keys",
)
PORTABILITY_KEYS = ("languages", "ecosystems", "tools", "repo_shape", "transfer")
EVIDENCE_KEYS = (
    "source_trajectories",
    "repos",
    "outcome",
    "verified_count",
    "refuted_count",
    "last_verified",
)
RETRIEVAL_KEYS = ("symptoms", "error_signatures", "keywords")

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
TOKEN_RE = re.compile(r"[a-z0-9_.\-/]+")
STALE_DAYS = 180
DEFAULT_BUDGET = {"L1": 2, "L2": 2, "L3": 1}


# --- frontmatter -----------------------------------------------------------


def parse_scalar(raw: str) -> object:
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(item) for item in inner.split(",")]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_frontmatter(block: str) -> dict:
    """Parse the flat-plus-one-nested-level YAML subset used by node files."""
    data: dict = {}
    container: object = data
    key: str | None = None
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == 0:
            if ":" not in stripped:
                raise ValueError(f"unparsable line: {line!r}")
            key, _, rest = stripped.partition(":")
            key = key.strip()
            if rest.strip() in (">", "|", ">-", "|-"):
                data[key] = ""
                container = "folded"
            elif rest.strip():
                data[key] = parse_scalar(rest)
                container = data
            else:
                container = None  # decided by the first nested line
        elif container == "folded":
            data[key] = f"{data[key]} {stripped}".strip()
        elif stripped.startswith("- "):
            if not isinstance(container, list):
                container = []
                data[key] = container
            container.append(parse_scalar(stripped[2:]))
        else:
            if not isinstance(container, dict) or container is data:
                container = {}
                data[key] = container
            sub_key, _, rest = stripped.partition(":")
            container[sub_key.strip()] = parse_scalar(rest)
    return data


def load_frontmatter(path: pathlib.Path) -> dict:
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("missing YAML frontmatter delimited by ---")
    return parse_frontmatter(match.group(1))


# --- validation ------------------------------------------------------------


def check_nonempty_list(data: dict, key: str, errors: list[str]) -> None:
    if not isinstance(data.get(key), list) or not data[key]:
        errors.append(f"{key}: must be a non-empty list")


def check_id(data: dict, errors: list[str]) -> None:
    node_id = data.get("id", "")
    if not isinstance(node_id, str) or not ID_RE.match(node_id):
        errors.append("id: must be lowercase, hyphen-separated")
        return
    level, stage = data.get("level"), data.get("stage")
    if level in LEVELS and stage in STAGES:
        prefix = f"{level.lower()}-{STAGE_ABBR[stage]}-"
        if not node_id.startswith(prefix):
            errors.append(f"id: must start with '{prefix}'")


def check_portability(data: dict, errors: list[str]) -> None:
    portability = data.get("portability")
    if not isinstance(portability, dict):
        errors.append("portability: must be a mapping")
        return
    for key in PORTABILITY_KEYS:
        if key not in portability:
            errors.append(f"portability.{key}: missing")
    level = data.get("level")
    expected = TRANSFER_BY_LEVEL.get(level)
    if expected and portability.get("transfer") != expected:
        errors.append(
            f"portability.transfer: must be '{expected}' for level {level}"
        )
    if level == "L3":
        for key in ("languages", "ecosystems", "tools"):
            if portability.get(key) != ["*"]:
                errors.append(
                    f"portability.{key}: L3 nodes must be ['*']; otherwise "
                    "the node is an L2"
                )


def parse_date(value: object) -> datetime.date | None:
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        return None


def check_evidence(data: dict, errors: list[str], warnings: list[str]) -> None:
    evidence = data.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence: must be a mapping")
        return
    for key in EVIDENCE_KEYS:
        if key not in evidence:
            errors.append(f"evidence.{key}: missing")
    outcome = evidence.get("outcome")
    if outcome not in OUTCOMES:
        errors.append(f"evidence.outcome: must be one of {OUTCOMES}")
    if outcome == "unverified" and data.get("level") != "L1":
        errors.append(
            "evidence.outcome: unverified nodes must not be promoted above L1"
        )
    if not evidence.get("repos"):
        errors.append("evidence.repos: at least one repository required")
    if "last_verified" in evidence:
        parsed = parse_date(evidence["last_verified"])
        if parsed is None:
            errors.append("evidence.last_verified: must be YYYY-MM-DD")
        else:
            age = (datetime.date.today() - parsed).days
            if age > STALE_DAYS:
                warnings.append(
                    f"evidence.last_verified: stale by {age - STALE_DAYS} "
                    "days; re-verify or mark the node as decayed"
                )


def check_retrieval_keys(data: dict, errors: list[str]) -> None:
    keys = data.get("retrieval_keys")
    if not isinstance(keys, dict):
        errors.append("retrieval_keys: must be a mapping")
        return
    for key in RETRIEVAL_KEYS:
        if key not in keys:
            errors.append(f"retrieval_keys.{key}: missing")
    if not any(keys.get(key) for key in RETRIEVAL_KEYS):
        errors.append("retrieval_keys: at least one list must be non-empty")


def validate(path: pathlib.Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = load_frontmatter(path)
    except ValueError as exc:
        return [str(exc)], warnings

    for field in REQUIRED:
        if field not in data:
            errors.append(f"{field}: missing")
    if data.get("level") not in LEVELS:
        errors.append(f"level: must be one of {LEVELS}")
    if data.get("stage") not in STAGES:
        errors.append(f"stage: must be one of {STAGES}")
    check_id(data, errors)
    for key in ("applicable_when", "key_actions", "verification", "pitfalls"):
        check_nonempty_list(data, key, errors)
    check_portability(data, errors)
    check_evidence(data, errors, warnings)
    check_retrieval_keys(data, errors)
    return errors, warnings


# --- helpers ---------------------------------------------------------------


def node_paths(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted((root / "nodes").glob("L[123]/*.md"))


def load_nodes(root: pathlib.Path) -> list[tuple[pathlib.Path, dict]]:
    nodes = []
    for path in node_paths(root):
        try:
            nodes.append((path, load_frontmatter(path)))
        except ValueError as exc:
            print(f"{path}: SKIPPED {exc}", file=sys.stderr)
    return nodes


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value else []


# --- commands --------------------------------------------------------------


def cmd_template(args: argparse.Namespace) -> int:
    level, stage = args.level, args.stage
    abbr = STAGE_ABBR[stage]
    star = '["*"]'
    portable = (
        f"  languages: {star}\n  ecosystems: {star}\n  tools: {star}"
        if level == "L3"
        else '  languages: ["<lang>"]\n  ecosystems: ["<ecosystem>"]\n'
        '  tools: ["<tool>"]'
    )
    print(
        f"""---
id: {level.lower()}-{abbr}-<failure-class>-<slug>
level: {level}
stage: {stage}
failure_class: <failure-class>
title: <one imperative line>
intent: <one sentence>
applicable_when:
  - <observable signal before the fix>
key_actions:
  - <action that changes what the agent does next>
verification:
  - <observable proof the action worked>
pitfalls:
  - <real dead end from this repair>
portability:
{portable}
  repo_shape: ["service"]
  transfer: {TRANSFER_BY_LEVEL[level]}
evidence:
  source_trajectories: ["traj-{datetime.date.today()}-<context>"]
  repos: ["<owner>/<name>"]
  outcome: verified
  verified_count: 1
  refuted_count: 0
  last_verified: "{datetime.date.today()}"
retrieval_keys:
  symptoms: ["<what a human observes>"]
  error_signatures: ["<literal log string>"]
  keywords: ["<synonym>"]
---

## Context

## Procedure

## Verification

## Pitfalls

## Provenance
"""
    )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    paths = args.paths or node_paths(args.root)
    if not paths:
        print(f"no node files under {args.root}/nodes/")
        return 1
    failed = False
    for path in paths:
        if not path.is_file():
            print(f"{path}: not a file")
            failed = True
            continue
        errors, warnings = validate(path)
        for warning in warnings:
            print(f"{path}: WARN {warning}")
        for error in errors:
            print(f"{path}: ERROR {error}")
        if errors:
            failed = True
        else:
            print(f"{path}: OK")
    return 1 if failed else 0


def cmd_index(args: argparse.Namespace) -> int:
    nodes = load_nodes(args.root)
    if not nodes:
        print(f"no node files under {args.root}/nodes/")
        return 1

    by_level: dict[str, int] = {level: 0 for level in LEVELS}
    classes: dict[str, dict] = {}
    repos: set[str] = set()
    stale: list[str] = []
    today = datetime.date.today()

    for path, data in nodes:
        level = str(data.get("level"))
        by_level[level] = by_level.get(level, 0) + 1
        entry = classes.setdefault(
            str(data.get("failure_class")),
            {"loc": 0, "plan": 0, "exec": 0, "repos": set(), "last": None},
        )
        stage = str(data.get("stage"))
        if stage in STAGE_ABBR:
            entry[STAGE_ABBR[stage]] += 1
        evidence = data.get("evidence") or {}
        node_repos = as_list(evidence.get("repos"))
        entry["repos"].update(node_repos)
        repos.update(node_repos)
        parsed = parse_date(evidence.get("last_verified"))
        if parsed:
            if entry["last"] is None or parsed > entry["last"]:
                entry["last"] = parsed
            if (today - parsed).days > STALE_DAYS:
                stale.append(f"{data.get('id')} — last verified {parsed}")

    lines = [
        "# Repair Knowledge Base Index",
        "",
        f"Updated: {today}",
        "Nodes: {} ({})".format(
            len(nodes),
            " / ".join(f"{lvl} {by_level.get(lvl, 0)}" for lvl in LEVELS),
        ),
        f"Repos contributing: {len(repos)}",
        "",
        "## By failure class",
        "",
        "| failure_class | loc | plan | exec | repos | last_verified |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name in sorted(classes):
        entry = classes[name]
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                name,
                entry["loc"],
                entry["plan"],
                entry["exec"],
                len(entry["repos"]),
                entry["last"] or "-",
            )
        )
    lines += ["", f"## Stale (>{STALE_DAYS} days unverified)", ""]
    lines += [f"- {item}" for item in sorted(stale)] or ["- none"]

    out = args.root / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(nodes)} nodes, {len(stale)} stale)")
    return 0


def portability_ok(data: dict, language: str | None, ecosystem: str | None):
    portability = data.get("portability") or {}
    for value, key in ((language, "languages"), (ecosystem, "ecosystems")):
        if not value:
            continue
        allowed = [item.lower() for item in as_list(portability.get(key))]
        if "*" not in allowed and value.lower() not in allowed:
            return False
    return True


def score_node(data: dict, text: str, failure_class: str | None) -> int:
    tokens = set(TOKEN_RE.findall(text.lower()))
    keys = data.get("retrieval_keys") or {}
    score = 0
    for field, weight in (
        ("error_signatures", 3),
        ("symptoms", 2),
        ("keywords", 1),
    ):
        for key in as_list(keys.get(field)):
            low = key.lower()
            if low and (low in text or tokens & set(TOKEN_RE.findall(low))):
                score += weight
    if failure_class and data.get("failure_class") == failure_class:
        score += 4
    evidence = data.get("evidence") or {}
    score += min(int(evidence.get("verified_count") or 0), 3)
    score -= 2 * int(evidence.get("refuted_count") or 0)
    return score


def cmd_query(args: argparse.Namespace) -> int:
    text = (args.text or "").lower()
    selected: list[tuple[int, pathlib.Path, dict]] = []
    budget = dict(DEFAULT_BUDGET)
    if args.budget:
        for item in args.budget.split(","):
            level, _, count = item.partition("=")
            budget[level.strip()] = int(count)

    for level in LEVELS:
        candidates = []
        for path, data in load_nodes(args.root):
            if data.get("level") != level or data.get("stage") != args.stage:
                continue
            if not portability_ok(data, args.language, args.ecosystem):
                continue
            score = score_node(data, text, args.failure_class)
            if score > 0 or not text:
                candidates.append((score, path, data))
        candidates.sort(key=lambda item: (-item[0], str(item[1])))
        selected.extend(candidates[: budget.get(level, 0)])

    if not selected:
        print(f"no matching nodes for stage={args.stage}")
        return 1

    print(f"# guidance: stage={args.stage} (read these files in order)")
    for score, path, data in selected:
        evidence = data.get("evidence") or {}
        stale = ""
        parsed = parse_date(evidence.get("last_verified"))
        if parsed and (datetime.date.today() - parsed).days > STALE_DAYS:
            stale = "  [STALE]"
        print(
            f"{data.get('level')}  score={score}  {path}{stale}\n"
            f"    {data.get('title')}"
        )
    return 0


def cmd_outcome(args: argparse.Namespace) -> int:
    today = datetime.date.today().isoformat()
    counter = LABELS[args.label]
    failed = False
    for node_id in args.node_ids:
        matches = [p for p in node_paths(args.root) if p.stem == node_id]
        if not matches:
            print(f"{node_id}: not found under {args.root}/nodes/")
            failed = True
            continue
        path = matches[0]
        text = path.read_text(encoding="utf-8")
        if counter:
            match = re.search(rf"^(\s+{counter}:\s*)(\d+)", text, re.MULTILINE)
            if not match:
                print(f"{path}: ERROR evidence.{counter} not found")
                failed = True
                continue
            text = (
                text[: match.start()]
                + f"{match.group(1)}{int(match.group(2)) + 1}"
                + text[match.end() :]
            )
        text = re.sub(
            r'^(\s+last_verified:\s*)"?[\d-]+"?',
            rf'\g<1>"{today}"',
            text,
            count=1,
            flags=re.MULTILINE,
        )
        path.write_text(text, encoding="utf-8")
        advice = LABEL_ADVICE.get(args.label)
        suffix = f" — next: {advice}" if advice else ""
        print(f"{path}: {args.label}{suffix}")
    return 1 if failed else 0


# --- entry point -----------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=pathlib.Path(os.environ.get("REPAIR_KB_ROOT", ".repair-kb")),
        help="knowledge base root (default: .repair-kb)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("template", help="print a schema-correct node skeleton")
    p.add_argument("--level", choices=LEVELS, required=True)
    p.add_argument("--stage", choices=STAGES, required=True)
    p.set_defaults(func=cmd_template)

    p = sub.add_parser("validate", help="validate node files (default: all)")
    p.add_argument("paths", nargs="*", type=pathlib.Path)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("index", help="rebuild index.md from the node tree")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("query", help="retrieve guidance for one repair stage")
    p.add_argument("--stage", choices=STAGES, required=True)
    p.add_argument("--text", help="symptom text, error signature, or log line")
    p.add_argument("--language", help="target repo language")
    p.add_argument("--ecosystem", help="target repo ecosystem")
    p.add_argument("--failure-class")
    p.add_argument("--budget", help="per-level budget, e.g. L1=2,L2=2,L3=1")
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("outcome", help="record a plan outcome on used nodes")
    p.add_argument("--label", choices=sorted(LABELS), required=True)
    p.add_argument("node_ids", nargs="+")
    p.set_defaults(func=cmd_outcome)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
