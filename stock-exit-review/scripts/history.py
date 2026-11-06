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

"""Record immutable stock observations and evaluate matured downside forecasts."""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1,<9",
#     "atomicwrites>=1.4,<2",
#     "httpx>=0.28,<1",
#     "pydantic>=2.10,<3",
# ]
# ///

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import click
from analyze import read_json, ticker_option, ticker_value, write_json
from decide import analysis_hash


def identity(analysis: dict, decision: dict) -> str:
    """Derive a stable record identifier from market and policy identity."""
    key = [
        analysis["ticker"],
        analysis["as_of"],
        decision["policy"],
        decision["model"] or decision["requested_model"],
    ]
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]


def record(root: Path, analysis: dict, decision: dict) -> dict:
    """Save an immutable observation after verifying its input identity."""
    ticker = ticker_value(analysis["ticker"])
    if decision["ticker"] != ticker or decision["as_of"] != analysis["as_of"]:
        raise ValueError("analysis and decision identity mismatch")
    if decision["analysis_hash"] != analysis_hash(analysis):
        raise ValueError("analysis changed after decision")
    record_id = identity(analysis, decision)
    path = root / ticker / "observations" / (record_id + ".json")
    observation = {"id": record_id, "analysis": analysis, "decision": decision}
    if path.exists():
        previous = read_json(path)
        if previous["decision"]["analysis_hash"] != decision["analysis_hash"]:
            raise ValueError(
                "historical input revision; existing observation preserved"
            )
        return {
            "status": "existing",
            "id": record_id,
            "path": str(path),
            "assessment": previous["decision"]["assessment"],
        }
    created = write_json(path, observation, immutable=True)
    return {
        "status": "created" if created else "existing",
        "id": record_id,
        "path": str(path),
        "sync": "sync_pending",
    }


def prices(series: list[dict]) -> dict[str, float]:
    """Validate and index an ascending series of positive adjusted closes."""
    result = {}
    for item in series:
        date = dt.date.fromisoformat(item["date"]).isoformat()
        value = item["close"]
        if (
            date in result
            or not isinstance(value, (float, int))
            or (isinstance(value, bool) or not math.isfinite(value) or value <= 0)
        ):
            raise ValueError("invalid historical price series")
        result[date] = float(value)
    if list(result) != sorted(result):
        raise ValueError("historical price series must be ascending")
    return result


# Eligibility gates and benchmark evidence must be evaluated against the same snapshot.
# pylint: disable-next=too-many-locals,too-many-return-statements
def evaluate_one(observation: dict, latest: dict) -> dict | None:
    """Score a matured forecast only when source history remains comparable."""
    analysis, decision = observation["analysis"], observation["decision"]
    forecast = decision["forecast"]
    if forecast is None:
        return None
    current, original = prices(latest["series"]), prices(analysis["series"])
    start = analysis["as_of"]
    if start not in current:
        return None
    future = [date for date in current if start < date <= latest["as_of"]]
    horizon = decision["policy"]["horizon_sessions"]
    if len(future) < horizon:
        return None
    target = future[horizon - 1]
    issued = dt.datetime.fromisoformat(decision["issued_at"]).date().isoformat()
    if target <= issued:
        return {
            "id": observation["id"],
            "status": "ineligible",
            "reason": "target session not later than forecast issuance date",
        }
    if analysis["source"] != latest["source"]:
        return {"id": observation["id"], "status": "source_changed"}
    if any(
        not math.isclose(original[date], current[date], rel_tol=1e-6)
        for date in original.keys() & current.keys()
    ):
        return {
            "id": observation["id"],
            "status": "historical_revision",
            "reason": "adjusted history revised; no score produced",
        }
    realized = current[target] / original[start] - 1
    event = realized <= decision["policy"]["downside_threshold"]
    probability = forecast["probability"]
    result = {
        "id": observation["id"],
        "status": "evaluated",
        "target_date": target,
        "policy": decision["policy"],
        "model": decision["model"],
        "realized_return": realized,
        "downside_event": event,
        "forecast_probability": probability,
        "brier_score": (probability - int(event)) ** 2,
        "benchmark_return": None,
        "excess_return": None,
        "cost_assumption": "gross adjusted-price return; no trades simulated",
    }
    before, after = analysis.get("benchmark"), latest.get("benchmark")
    if (
        before
        and after
        and before["ticker"] == after["ticker"]
        and (before["source"] == after["source"])
    ):
        base, updated = prices(before["series"]), prices(after["series"])
        if (
            start in base
            and start in updated
            and target in updated
            and all(
                math.isclose(base[date], updated[date], rel_tol=1e-6)
                for date in base.keys() & updated.keys()
            )
        ):
            result["benchmark_return"] = updated[target] / base[start] - 1
            result["excess_return"] = realized - result["benchmark_return"]
    return result


def evaluate(root: Path, latest: dict) -> dict:
    """Persist eligible outcomes while deferring revised or changed history."""
    ticker = ticker_value(latest["ticker"])
    updates, pending = [], []
    if latest["data_quality"]["usable"] is not True:
        return {"updates": [], "status": "unusable_latest_data"}
    for path in sorted((root / ticker / "observations").glob("*.json")):
        observation = read_json(path)
        target = root / ticker / "evaluations" / (observation["id"] + ".json")
        if target.exists():
            continue
        outcome = evaluate_one(observation, latest)
        if outcome is None:
            continue
        if outcome["status"] in ("historical_revision", "source_changed"):
            pending.append(outcome)
            continue
        write_json(target, outcome, immutable=True)
        updates.append(
            {
                "path": str(target),
                "id": observation["id"],
                "status": outcome["status"],
                "sync": "sync_pending",
            }
        )
    return {"updates": updates, "deferred": pending}


def context(root: Path, ticker: str) -> dict:
    """Export recent observations and evaluation scores grouped by policy/model."""
    observations = []
    for path in (root / ticker / "observations").glob("*.json"):
        observation = read_json(path)
        analysis, decision = observation["analysis"], observation["decision"]
        observations.append(
            {
                "id": observation["id"],
                "path": str(path),
                "as_of": analysis["as_of"],
                "features": analysis["features"],
                "assessment": decision["assessment"],
                "policy": decision["policy"],
                "model": decision["model"],
            }
        )
    observations.sort(key=lambda item: (item["as_of"], item["id"]))
    groups: dict[str, list[float]] = {}
    for path in (root / ticker / "evaluations").glob("*.json"):
        outcome = read_json(path)
        if outcome["status"] != "evaluated":
            continue
        key = json.dumps([outcome["policy"], outcome["model"]], sort_keys=True)
        groups.setdefault(key, []).append(outcome["brier_score"])
    return {
        "ticker": ticker,
        "observations": observations[-10:],
        "evaluation_groups": [
            {
                "policy": json.loads(key)[0],
                "model": json.loads(key)[1],
                "count": len(scores),
                "mean_brier": sum(scores) / len(scores),
            }
            for key, scores in groups.items()
        ],
    }


@click.group(help=__doc__)
@click.option("--root", type=click.Path(file_okay=False, path_type=Path), required=True)
@click.pass_context
def main(ctx, root) -> None:
    """Resolve the external history root for subsequent subcommands."""
    ctx.obj = root.expanduser().resolve()


@main.command("record", help="Save an immutable observation and decision.")
@click.option("--analysis", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--decision", type=click.Path(exists=True, dir_okay=False), required=True)
@click.pass_obj
def record_command(root, analysis, decision) -> None:
    """Record an immutable analysis and decision pair."""
    result = record(root, read_json(analysis), read_json(decision))
    click.echo(json.dumps(result, sort_keys=True, allow_nan=False))


@main.command(
    "evaluate", help="Evaluate matured forecasts without modifying observations."
)
@click.option("--analysis", type=click.Path(exists=True, dir_okay=False), required=True)
@click.pass_obj
def evaluate_command(root, analysis) -> None:
    """Evaluate matured observations using the supplied latest market data."""
    result = evaluate(root, read_json(analysis))
    click.echo(json.dumps(result, sort_keys=True, allow_nan=False))


@main.command(
    "context", help="Export recent observations and grouped evaluation scores."
)
@click.option("--ticker", callback=ticker_option, required=True)
@click.option("--output", type=click.Path(dir_okay=False), required=True)
@click.pass_obj
def context_command(root, ticker, output) -> None:
    """Write recent historical context for a validated ticker."""
    result = context(root, ticker)
    write_json(output, result)
    click.echo(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        # Click supplies callback arguments; CI cannot infer its missing dependency.
        # pylint: disable-next=no-value-for-parameter
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        raise SystemExit("history failed: " + str(error)) from None
