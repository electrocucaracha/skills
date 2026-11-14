#!/usr/bin/env python3
"""Diagnose why stock-exit-review decisions abstain to `insufficient_evidence`.

Reads every observation under <root>/<ticker>/observations/ and, for each of the
three Jev classification questions (trend, risk, downside), reports confidence
min/max/mean and how many clear the policy floor, then names the binding
constraint (the question that fails most often) and lists any date on which all
three clear the floor — the only dates that could produce `hold`/`review_exit`.

Stdlib only: runs with plain `python3`, no uv or heavy libs. Read-only over
already-recorded observations; it changes no record and reruns no forecast.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter

QUESTIONS = ("trend", "risk", "downside")


def load_observations(root: str, ticker: str):
    """Load existing observations and extract available confidence scores."""
    path = os.path.join(root, ticker, "observations")
    rows = []
    for p in sorted(glob.glob(os.path.join(path, "*.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                o = json.load(f)
        except (OSError, ValueError):
            continue
        analysis = o.get("analysis", {}) or {}
        decision = o.get("decision", {}) or {}
        conf = {}
        for q, a in (decision.get("answers") or {}).items():
            if (
                q in QUESTIONS
                and isinstance(a, dict)
                and a.get("confidence") is not None
            ):
                try:
                    conf[q] = float(a["confidence"])
                except (TypeError, ValueError):
                    continue
        rows.append((analysis.get("as_of", "?"), decision.get("assessment", "?"), conf))
    rows.sort(key=lambda r: str(r[0]))
    return rows


def main() -> int:
    """Report which confidence threshold most often blocks a decision."""
    ap = argparse.ArgumentParser(description="Diagnose decision abstentions.")
    ap.add_argument(
        "--root", required=True, help="history root containing <ticker>/observations/"
    )
    ap.add_argument("--ticker", required=True)
    ap.add_argument(
        "--min-confidence",
        type=float,
        default=0.60,
        help="policy confidence floor (default 0.60)",
    )
    args = ap.parse_args()

    rows = load_observations(args.root, args.ticker)
    if not rows:
        print(
            f"no observations under {os.path.join(args.root, args.ticker, 'observations')}"
        )
        return 1

    n = len(rows)
    floor = args.min_confidence
    print(f"ticker={args.ticker}  observations={n}  floor={floor}")
    print(f"{'question':<8} {'n':>4} {'min':>6} {'max':>6} {'mean':>6}  #>=floor")

    fails = {}
    for q in QUESTIONS:
        vals = [r[2][q] for r in rows if q in r[2]]
        over = [v for v in vals if v >= floor]
        fails[q] = n - len(over)
        if vals:
            print(
                f"{q:<8} {len(vals):>4} {min(vals):>6.2f} {max(vals):>6.2f} "
                f"{sum(vals) / len(vals):>6.2f}  {len(over)}/{len(vals)}"
            )
        else:
            print(f"{q:<8}   0  {'-':>6} {'-':>6} {'-':>6}  0/{n}")

    binding = max(fails, key=lambda question: fails[question])
    print(
        f"\nbinding constraint: '{binding}' "
        f"(fails the floor on {fails[binding]}/{n} dates)"
    )
    allthree = [r[0] for r in rows if all(r[2].get(q, 0.0) >= floor for q in QUESTIONS)]
    head = f"-> {allthree[:10]}" if allthree else "(none)"
    print(
        f"dates with all three >= floor (could produce hold/review_exit): "
        f"{len(allthree)} {head}"
    )
    print(
        "assessments: " + json.dumps(dict(Counter(r[1] for r in rows)), sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
