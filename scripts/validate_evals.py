"""Validate the structure of skill evaluation files."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def is_nonempty_strings(value: object, *, allow_empty: bool = False) -> bool:
    """Return whether a value is a string array with the requested emptiness."""
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def validate_case(
    path: Path, index: int, case: object, seen_ids: set[int | str]
) -> list[str]:
    """Return validation errors for one eval case."""
    label = f"{path}: evals[{index}]"
    if not isinstance(case, dict):
        return [f"{label} must be an object"]

    errors = []
    case_id = case.get("id")
    if isinstance(case_id, bool) or not isinstance(case_id, (int, str)):
        errors.append(f"{label}.id must be a string or integer")
    elif case_id in seen_ids:
        errors.append(f"{label}.id duplicates {case_id!r}")
    else:
        seen_ids.add(case_id)

    for field in ("prompt", "expected_output"):
        value = case.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}.{field} must be a non-empty string")

    if not is_nonempty_strings(case.get("assertions")):
        errors.append(f"{label}.assertions must contain non-empty strings")
    if not is_nonempty_strings(case.get("files"), allow_empty=True):
        errors.append(f"{label}.files must be an array of strings")
    return errors


def validate(path: Path) -> tuple[int, list[str]]:
    """Return the case count and validation errors for one eval file."""
    try:
        with path.open(encoding="utf-8") as eval_file:
            data = json.load(eval_file)
    except (OSError, json.JSONDecodeError) as error:
        return 0, [f"{path}: {error}"]

    errors = []
    if not isinstance(data, dict):
        return 0, [f"{path}: top level must be an object"]
    if data.get("skill_name") != path.parent.parent.name:
        errors.append(
            f"{path}: skill_name must match directory {path.parent.parent.name!r}"
        )
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        errors.append(f"{path}: description must be a non-empty string")

    cases = data.get("evals")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{path}: evals must be a non-empty array")
        return 0, errors

    seen_ids = set()
    for index, case in enumerate(cases, start=1):
        errors.extend(validate_case(path, index - 1, case, seen_ids))

    return len(cases), errors


def main() -> int:
    """Validate all skill eval files and print a concise result."""
    paths = sorted(ROOT.glob("*/evals/evals.json"))
    if not paths:
        print("No skill eval files found.", file=sys.stderr)
        return 1

    total_cases = 0
    errors = []
    for path in paths:
        case_count, file_errors = validate(path)
        total_cases += case_count
        errors.extend(file_errors)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated {len(paths)} eval suites and {total_cases} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
