#!/usr/bin/env -S uv --quiet run --script
# Copyright (c) 2026
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Durable capture and reconciliation for stock-exit-review decisions.

Guarantees that every decision is captured durably and retrievably,
independent of OpenViking reachability. It writes a self-contained capture
record (analysis + decision + optional evaluation + optional explanation +
OpenViking sync status) to a persistent capture root and maintains a manifest
index. Pending OpenViking mirrors are reconciled on later runs by exact
read-back, deduplicated by record id. The capture record is the authoritative
durable record; OpenViking is a reconciled mirror.

The record id uses the same identity() helper as history so a capture id always
equals its observation id.

This script is intentionally self-contained (stdlib + click + atomicwrites
only) so the capture guarantee holds even when the heavy analysis
dependencies (numpy/pandas/ta/yfinance) cannot be imported.
"""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1,<9",
#     "atomicwrites>=1.4,<2",
# ]
# ///

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import click
from atomicwrites import atomic_write


def read_json(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: dict, *, immutable: bool = False) -> bool:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(data, sort_keys=True, allow_nan=False, indent=2)
    try:
        with atomic_write(path, overwrite=not immutable, encoding="utf-8") as handle:
            handle.write(rendered)
    except FileExistsError:
        return False
    return True


def identity(analysis: dict, decision: dict) -> str:
    # Mirrors history.identity() exactly so capture ids == observation ids.
    key = [
        analysis["ticker"],
        analysis["as_of"],
        decision["policy"],
        decision["model"] or decision["requested_model"],
    ]
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]


def _now(iso: str | None) -> str:
    return iso if iso else dt.datetime.now(dt.UTC).isoformat()


def load_manifest(root: Path, ticker: str) -> dict:
    path = root / ticker / "manifest.json"
    return (
        read_json(path)
        if path.exists()
        else {"ticker": ticker, "updated": None, "records": {}}
    )


def save_manifest(root: Path, manifest: dict) -> None:
    write_json(root / manifest["ticker"] / "manifest.json", manifest)


@click.group(help=__doc__)
@click.option(
    "--root",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Persistent capture root, outside the skill directory.",
)
@click.pass_context
def main(ctx, root) -> None:
    ctx.obj = root.expanduser().resolve()


@main.command("capture", help="Write a durable capture record and update the manifest.")
@click.option("--analysis", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--decision", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option(
    "--evaluation",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Matured evaluation JSON, if any.",
)
@click.option(
    "--explanation",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Explanation artifact (JSON or text), if any.",
)
@click.option(
    "--ov-status",
    type=click.Choice(["sync_pending", "verified", "failed", "na"]),
    default="sync_pending",
    show_default=True,
    help="OpenViking mirror status for this record.",
)
@click.option(
    "--ov-uri", default=None, help="OpenViking destination URI or job id, if any."
)
@click.option(
    "--ov-digest",
    default=None,
    help="Content digest of the OpenViking write, if verified.",
)
@click.option("--now", default=None, help="ISO timestamp override (backfill / tests).")
@click.pass_obj
def capture_command(
    root, analysis, decision, evaluation, explanation, ov_status, ov_uri, ov_digest, now
) -> None:
    analysis = read_json(analysis)
    decision = read_json(decision)
    if (
        decision["ticker"] != analysis["ticker"]
        or decision["as_of"] != analysis["as_of"]
    ):
        raise ValueError("analysis and decision identity mismatch")
    ticker = str(analysis["ticker"])
    record_id = identity(analysis, decision)
    cap_path = root / ticker / "captures" / (record_id + ".json")
    attempts, captured_at = 0, None
    was_new = not cap_path.exists()
    if cap_path.exists():
        previous = read_json(cap_path)
        attempts = previous.get("ov_attempts", 0)
        captured_at = previous.get("captured_at")
    else:
        entry = {
            "id": record_id,
            "ticker": ticker,
            "as_of": analysis["as_of"],
            "assessment": decision["assessment"],
            "model": decision.get("model"),
            "policy": decision["policy"],
            "analysis": analysis,
            "decision": decision,
            "evaluation": _load_maybe_json(evaluation) if evaluation else None,
            "explanation": _load_maybe_json(explanation) if explanation else None,
            "ov_status": ov_status,
            "ov_uri": ov_uri,
            "ov_digest": ov_digest,
            "ov_attempts": attempts,
            "identity_scheme": "history.identity v1",
            "captured_at": _now(now),
        }
        write_json(cap_path, entry, immutable=True)
    manifest = load_manifest(root, ticker)
    prev = manifest["records"].get(record_id, {})
    manifest["records"][record_id] = {
        "as_of": analysis["as_of"],
        "assessment": decision["assessment"],
        "model": decision.get("model"),
        "policy": decision["policy"],
        "capture_path": str(cap_path),
        "ov_status": ov_status,
        "ov_uri": ov_uri,
        "ov_digest": ov_digest,
        "ov_attempts": attempts,
        "ov_last_attempt": _now(now),
        "verified_at": prev.get("verified_at"),
        "captured_at": captured_at or _now(now),
        "created": was_new,
    }
    manifest["updated"] = _now(now)
    save_manifest(root, manifest)
    click.echo(
        json.dumps(
            {
                "status": (
                    "created"
                    if manifest["records"][record_id]["created"]
                    else "existing"
                ),
                "id": record_id,
                "capture_path": str(cap_path),
                "ov_status": ov_status,
                "manifest": str(root / ticker / "manifest.json"),
            },
            sort_keys=True,
            allow_nan=False,
        )
    )


@main.command(
    "pending", help="List records whose OpenViking mirror is not yet verified."
)
@click.option("--ticker", default=None, help="Restrict to one ticker namespace.")
@click.pass_obj
def pending_command(root, ticker) -> None:
    tickers = [ticker] if ticker else [d.name for d in root.iterdir() if d.is_dir()]
    out = []
    for t in tickers:
        manifest = load_manifest(root, t)
        for rid, rec in manifest["records"].items():
            if rec.get("ov_status") != "verified":
                out.append(
                    {
                        "record_id": rid,
                        "ticker": t,
                        "as_of": rec.get("as_of"),
                        "assessment": rec.get("assessment"),
                        "ov_status": rec.get("ov_status"),
                        "ov_attempts": rec.get("ov_attempts", 0),
                        "capture_path": rec.get("capture_path"),
                    }
                )
    out.sort(key=lambda r: (r["ticker"], r.get("as_of") or "", r["record_id"]))
    click.echo(
        json.dumps({"pending": out, "count": len(out)}, sort_keys=True, allow_nan=False)
    )


@main.command(
    "confirm", help="Mark a record verified after an exact OpenViking read-back."
)
@click.option("--ticker", required=True)
@click.option("--id", "record_id", required=True)
@click.option("--ov-uri", required=True, help="Destination URI or job id that matched.")
@click.option("--ov-digest", required=True, help="Digest of the read-back content.")
@click.option("--now", default=None, help="ISO timestamp override.")
@click.pass_obj
def confirm_command(root, ticker, record_id, ov_uri, ov_digest, now) -> None:
    manifest = load_manifest(root, ticker)
    rec = manifest["records"].get(record_id)
    if rec is None:
        raise ValueError("no captured record " + record_id + " for " + ticker)
    rec["ov_status"] = "verified"
    rec["ov_uri"] = ov_uri
    rec["ov_digest"] = ov_digest
    rec["verified_at"] = _now(now)
    cap_path = Path(rec["capture_path"])
    if cap_path.exists():
        cap = read_json(cap_path)
        cap["ov_status"] = "verified"
        cap["ov_uri"] = ov_uri
        cap["ov_digest"] = ov_digest
        cap["verified_at"] = rec["verified_at"]
        write_json(cap_path, cap)
    manifest["updated"] = _now(now)
    save_manifest(root, manifest)
    click.echo(
        json.dumps(
            {
                "status": "verified",
                "id": record_id,
                "ticker": ticker,
                "ov_uri": ov_uri,
                "verified_at": rec["verified_at"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )


@main.command("report", help="Summary of capture + OpenViking sync status.")
@click.option("--ticker", default=None)
@click.pass_obj
def report_command(root, ticker) -> None:
    tickers = [ticker] if ticker else [d.name for d in root.iterdir() if d.is_dir()]
    counts = {"verified": 0, "sync_pending": 0, "failed": 0, "na": 0}
    pending, ranges = [], {}
    for t in tickers:
        manifest = load_manifest(root, t)
        asofs = []
        for rid, rec in manifest["records"].items():
            status = rec.get("ov_status", "sync_pending")
            counts[status] = counts.get(status, 0) + 1
            asofs.append(rec.get("as_of"))
            if status != "verified":
                pending.append(
                    {
                        "record_id": rid,
                        "ticker": t,
                        "as_of": rec.get("as_of"),
                        "ov_status": status,
                        "ov_attempts": rec.get("ov_attempts", 0),
                    }
                )
        if asofs:
            ranges[t] = [min(asofs), max(asofs)]
    pending.sort(key=lambda r: (r["ticker"], r.get("as_of") or ""))
    click.echo(
        json.dumps(
            {
                "by_status": counts,
                "date_ranges": ranges,
                "pending": pending,
                "pending_count": len(pending),
            },
            sort_keys=True,
            allow_nan=False,
        )
    )


def _load_maybe_json(path: str | Path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        raise SystemExit("capture failed: " + str(error)) from None
