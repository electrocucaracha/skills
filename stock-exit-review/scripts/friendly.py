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

"""Emit a friendly, plain-language TL;DR + justification for a stock-exit decision.

The detailed/technical report is the OpenViking / capture record's job; this is the
short message the user actually reads. Pure presentation over the already-made
decision (reads ``decision['summary']``) plus the analysis features and benchmark;
it NEVER re-derives the verdict. Dependency-light: stdlib + click only."""

from __future__ import annotations

import json

import click

VERDICT_LABEL = {
    "HOLD": "HOLD",
    "SELL": "SELL / REVIEW EXIT",
    "NO_DECISION": "NO ACTION",
}
ASSESS_TO_VERDICT = {
    "hold": "HOLD",
    "review_exit": "SELL",
    "insufficient_evidence": "NO_DECISION",
}


def _pct(x, sign=True):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "n/a"
    return f"{x * 100:+.2f}%" if sign else f"{x * 100:.1f}%"


def _num(x, nd=2):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "n/a"


def friendly(analysis, decision, benchmark=None) -> str:
    feats = analysis.get("features", {}) or {}
    pol = decision.get("policy", {}) or {}
    floor = pol.get("min_confidence", 0.6)
    thr = pol.get("downside_threshold", -0.05)
    horizon = pol.get("horizon_sessions", 20)
    ticker = decision.get("ticker") or analysis.get("ticker") or "STK"
    as_of = decision.get("as_of") or analysis.get("as_of", "")
    smry = decision.get("summary") or {}
    verdict = smry.get("verdict") or ASSESS_TO_VERDICT.get(
        decision.get("assessment", "insufficient_evidence"), "NO_DECISION"
    )
    answers = decision.get("answers") or {}
    t, r, d = (
        answers.get("trend") or {},
        answers.get("risk") or {},
        answers.get("downside") or {},
    )
    bench = benchmark if benchmark is not None else (analysis.get("benchmark") or {})
    bench_ret = bench.get("return_20") if isinstance(bench, dict) else None

    L = [
        (
            f"*{ticker} exit review \u2014 session {as_of}* \u2192 "
            f"*{VERDICT_LABEL[verdict]}*"
        )
    ]

    if verdict == "NO_DECISION":
        confs = " \u00b7 ".join(
            f"{q} *{(answers.get(q) or {}).get('choice', '?')} "
            f"{float((answers.get(q) or {}).get('confidence', 0)):.2f}*"
            for q in ("trend", "risk", "downside")
        )
        L.append(
            f"_Why:_ No Jev question cleared the {floor:.2f} confidence "
            f"floor \u2014 {confs}. The policy yields no trade: a genuine "
            f"\u2018no decision\u2019, not a hold or a sell."
        )
    else:
        why = "; ".join(smry.get("justification") or []) or VERDICT_LABEL[verdict] + "."
        L.append(f"_Why:_ {why}")

    L.append("_Signals (computed, not model-generated):_")
    if t:
        close = feats.get("close", 0)
        s20 = feats.get("sma_20", 0)
        s50 = feats.get("sma_50", 0)
        rel = "sits above" if (close or 0) >= (s20 or 0) else "is below"
        L.append(
            f"- *Trend {t.get('choice', '?')}:* close {_num(close)} {rel} "
            f"SMA20 ({_num(s20)}) and SMA50 ({_num(s50)}); 20-day return "
            f"{_pct(feats.get('return_20'))}; MACD hist "
            f"{_num(feats.get('macd_histogram'))} (momentum "
            f"{'fading' if float(feats.get('macd_histogram', 0) or 0) < 0 else 'building'})."
        )
    if r:
        L.append(
            f"- *Risk {r.get('choice', '?')}:* drawdown from peak "
            f"{_pct(feats.get('drawdown_from_peak'))}, annualized vol "
            f"{_pct(feats.get('annualized_volatility'), False)}, volume "
            f"{_num(feats.get('volume_ratio_20'), 1)}\u00d7."
        )
    if d:
        L.append(
            f"- *Downside {d.get('choice', '?')}:* 20-day return "
            f"{_pct(feats.get('return_20'))} vs the {_pct(thr)} threshold "
            f"over {horizon} sessions."
        )

    if bench_ret is not None:
        w = feats.get("return_20", 0)
        s = bench_ret
        excess = (float(w or 0) - float(s)) * 100
        rsi = feats.get("rsi_14")
        rsi_txt = ""
        if rsi is not None:
            tag = (
                "neutral"
                if 40 <= float(rsi) <= 60
                else ("strong" if float(rsi) > 60 else "weak")
            )
            rsi_txt = f" RSI {_num(rsi, 1)} ({tag})."
        L.append(
            f"_Outperformance:_ {ticker} {_pct(w)} vs SPY {_pct(s)} over "
            f"{horizon} sessions (~{excess:+.1f}pp excess).{rsi_txt}"
        )

    L.append(
        "_Caveats:_ technical-only (no fundamentals or news) \u2014 a research "
        "signal, not financial advice."
    )
    return "\n".join(L)


@click.command()
@click.option(
    "--analysis", "analysis_path", required=True, type=click.Path(exists=True)
)
@click.option(
    "--decision", "decision_path", required=True, type=click.Path(exists=True)
)
@click.option("--benchmark", "benchmark_path", default=None, type=click.Path())
@click.option("--output", "output_path", default=None, type=click.Path())
def main(analysis_path, decision_path, benchmark_path, output_path):
    with open(analysis_path) as analysis_file, open(decision_path) as decision_file:
        analysis = json.load(analysis_file)
        decision = json.load(decision_file)
    if benchmark_path:
        with open(benchmark_path) as benchmark_file:
            benchmark = json.load(benchmark_file)
    else:
        benchmark = None
    text = friendly(analysis, decision, benchmark)
    if output_path:
        with open(output_path, "w") as output_file:
            output_file.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
