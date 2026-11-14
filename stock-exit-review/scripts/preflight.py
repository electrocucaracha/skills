"""Check Hermes paths and dependency imports without importing native packages."""

import argparse
import json
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path


def check_runtime(run_dir: Path, history_root: Path, timeout: int) -> dict:
    skill_dir = Path(__file__).resolve().parent.parent
    for path in (run_dir, history_root):
        if not path.is_absolute():
            raise ValueError("run and history directories must be absolute")
        if path.resolve().is_relative_to(skill_dir):
            raise ValueError("run and history directories must be outside the skill")
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.TemporaryFile(dir=path) as handle:
            handle.write(b"stock-exit-review preflight\n")
            handle.flush()
    uv = shutil.which("uv")
    if not uv:
        return {
            "status": "blocked",
            "reason": "uv_missing",
            "action": "Expose uv on the scheduler PATH; do not install it during a review.",
        }
    dependencies = set()
    for name in ("analyze.py", "decide.py", "history.py"):
        source = (skill_dir / "scripts" / name).read_text(encoding="utf-8")
        metadata = source.split("# /// script\n", 1)[1].split("# ///", 1)[0]
        dependencies.update(
            tomllib.loads(
                "\n".join(line.removeprefix("# ") for line in metadata.splitlines())
            )["dependencies"]
        )
    command = [uv, "--no-progress", "run", "--no-project", "--python", ">=3.12"]
    for dependency in sorted(dependencies):
        command.extend(["--with", dependency])
    command.extend(
        [
            "python",
            "-c",
            (
                "import sys; sys.path.insert(0, sys.argv[1]); "
                "import numpy, pandas, ta, yfinance, pydantic_core; "
                "import analyze, decide, history"
            ),
            str(skill_dir / "scripts"),
        ]
    )
    try:
        result = subprocess.run(
            command, cwd=run_dir, capture_output=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "blocked",
            "reason": "dependency_probe_timeout",
            "action": "Provision the runtime outside the scheduled review, then retry.",
        }
    if result.returncode:
        diagnostic = result.stderr.decode("utf-8", errors="replace").lower()
        native_failure = any(
            text in diagnostic
            for text in (
                "failed to map segment",
                "permission denied",
                "operation not permitted",
            )
        )
        return {
            "status": "blocked",
            "reason": (
                "native_import_failed" if native_failure else "dependency_probe_failed"
            ),
            "action": "Check runtime permissions and noexec mounts. Use an operator-provisioned "
            "Python and uv cache on executable storage; do not rewrite the pipeline.",
        }
    return {
        "status": "ready",
        "run_dir": str(run_dir),
        "history_root": str(history_root),
        "dependencies": "imported",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=180)
    arguments = parser.parse_args(argv)
    if not 1 <= arguments.timeout <= 600:
        parser.error("--timeout must be between 1 and 600 seconds")
    try:
        result = check_runtime(
            arguments.run_dir, arguments.history_root, arguments.timeout
        )
    except (OSError, ValueError) as error:
        result = {
            "status": "blocked",
            "reason": type(error).__name__,
            "action": "Provide readable skill files and writable absolute run/history paths.",
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
