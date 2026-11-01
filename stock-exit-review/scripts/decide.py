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

"""Ask Jev atomic market questions and apply a conservative research policy."""

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
import os
import ssl
from typing import Annotated, Literal, Self

import click
import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

from analyze import read_json, ticker_value, write_json

FEATURE_KEYS = (
    "close", "sma_20", "sma_50", "rsi_14", "macd_histogram",
    "atr_fraction", "return_20", "annualized_volatility",
    "max_drawdown", "drawdown_from_peak", "volume_ratio_20",
)

QUESTIONS = {
    "trend": {
        "type": "choice",
        "instructions": "Classify the current price trend using only supplied features.",
        "criteria": {
            "improving": "Price and trend indicators consistently strengthen.",
            "deteriorating": "Price and trend indicators consistently weaken.",
            "mixed": "Signals disagree or there is insufficient evidence.",
        },
    },
    "risk": {
        "type": "choice",
        "instructions": "Classify current downside-risk evidence, not future returns.",
        "criteria": {
            "elevated": "Drawdown and volatility together suggest elevated risk.",
            "ordinary": "Supplied risk indicators do not jointly show elevated risk.",
            "unknown": "The supplied risk evidence is inconclusive.",
        },
    },
    "downside": {
        "type": "choice",
        "instructions": (
            "Estimate whether the adjusted close after horizon_sessions additional "
            "trading sessions will have a return <= downside_threshold relative "
            "to the supplied latest close. Use only supplied market evidence. "
            "Do not confuse classification certainty with forecasting accuracy."
        ),
        "criteria": {
            "downside": "The specified terminal downside event occurs.",
            "not_downside": "The specified terminal downside event does not occur.",
            "unknown": "Evidence is insufficient to estimate this future event.",
        },
    },
}


def analysis_hash(analysis: dict) -> str:
    payload = {key: value for key, value in analysis.items()
               if key not in ("captured_at", "requested_as_of")}
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, allow_nan=False
    ).encode()).hexdigest()


def market_features(features: dict) -> dict:
    selected = {key: features[key] for key in FEATURE_KEYS}
    if not all(value is None or (isinstance(value, (int, float)) and
               not isinstance(value, bool) and math.isfinite(value))
               for value in selected.values()):
        raise ValueError("invalid numeric market features")
    return selected


Probability = Annotated[float, Field(ge=0, le=1)]


class ChoiceAnswer(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False)

    type: Literal["choice"]
    choice: str
    confidence: Probability
    probabilities: dict[str, Probability]

    @model_validator(mode="after")
    def check_distribution(self) -> Self:
        if not math.isclose(sum(self.probabilities.values()), 1, abs_tol=0.001):
            raise ValueError("Jev probabilities do not sum to one")
        if self.choice not in self.probabilities or (
            self.probabilities[self.choice] < max(self.probabilities.values())
        ):
            raise ValueError("invalid Jev selected choice")
        return self


class JevResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    model: Annotated[str, Field(min_length=1, max_length=128)]
    answers: dict[str, ChoiceAnswer]

    @model_validator(mode="after")
    def check_questions(self) -> Self:
        if set(self.answers) != set(QUESTIONS):
            raise ValueError("invalid Jev answer schema")
        for name, answer in self.answers.items():
            if set(answer.probabilities) != set(QUESTIONS[name]["criteria"]):
                raise ValueError("invalid Jev answer options")
        return self


def query_jev(state: dict, model: str, token: str) -> dict:
    body = json.dumps({"state": state, "model": model,
                       "questions": QUESTIONS}, allow_nan=False).encode()
    tls = ssl.create_default_context()
    tls.minimum_version = ssl.TLSVersion.TLSv1_3
    with httpx.Client(timeout=30, follow_redirects=False, verify=tls) as client:
        with client.stream(
            "POST", "https://api.typesafe.ai/v1/systemone", content=body,
            headers={"Authorization": "Bearer " + token,
                     "Content-Type": "application/json", "Accept": "application/json"},
        ) as response:
            response.raise_for_status()
            payload = bytearray()
            for chunk in response.iter_bytes(chunk_size=65_536):
                payload.extend(chunk)
                if len(payload) > 2_000_000:
                    raise ValueError("Jev response exceeds size limit")
    return JevResponse.model_validate_json(payload).model_dump()


def assessment(answers: dict, minimum: float) -> tuple[str, list[str]]:
    if any(answer["confidence"] < minimum for answer in answers.values()):
        return "insufficient_evidence", ["low Jev classification confidence"]
    trend, risk = answers["trend"]["choice"], answers["risk"]["choice"]
    downside = answers["downside"]["choice"]
    if trend == "mixed" or risk == "unknown" or downside == "unknown":
        return "insufficient_evidence", ["mixed or unknown evidence"]
    if trend == "deteriorating" and risk == "elevated" and downside == "downside":
        return "review_exit", ["weak trend, elevated risk, downside forecast"]
    if trend == "improving" and risk == "ordinary" and downside == "not_downside":
        return "hold", ["improving trend and ordinary risk evidence"]
    return "insufficient_evidence", ["signals conflict; human review required"]


@click.command(help=__doc__)
@click.option("--analysis", "analysis_path",
              type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--context", "context_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--horizon", type=click.IntRange(1, 252), default=20, show_default=True)
@click.option("--downside-threshold", type=click.FloatRange(-1, 0, min_open=True,
              max_open=True), default=-0.05, show_default=True)
@click.option("--min-confidence", type=click.FloatRange(0, 1), default=0.6,
              show_default=True)
@click.option("--model", envvar="JEV_MODEL", default="jev-latest", show_default=True)
@click.option("--output", type=click.Path(dir_okay=False), required=True)
def main(analysis_path, context_path, horizon, downside_threshold,
         min_confidence, model, output) -> None:
    analysis = read_json(analysis_path)
    ticker_value(analysis["ticker"])
    as_of = dt.date.fromisoformat(analysis["as_of"])
    features = market_features(analysis["features"])
    policy = {"version": "technical-v1", "horizon_sessions": horizon,
              "downside_threshold": downside_threshold,
              "min_confidence": min_confidence}
    context = read_json(context_path) if context_path else {}
    market_history = []
    if context.get("ticker") == analysis["ticker"]:
        for item in context.get("observations", [])[-5:]:
            if item["as_of"] < analysis["as_of"]:
                market_history.append({"as_of": item["as_of"],
                                       "features": market_features(item["features"])})
    state = {
        "ticker": analysis["ticker"], "as_of": analysis["as_of"],
        "features": features,
        "horizon_sessions": horizon,
        "downside_threshold": downside_threshold,
        "previous_market_features": market_history,
        "coverage": "technical price/volume only; no fundamentals or news",
    }
    result = {
        "schema_version": 1, "ticker": analysis["ticker"],
        "as_of": analysis["as_of"], "analysis_hash": analysis_hash(analysis),
        "issued_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": policy, "requested_model": model, "model": None,
        "assessment": "insufficient_evidence", "answers": {}, "forecast": None,
        "reasons": [],
    }
    today = dt.datetime.now(dt.timezone.utc).date()
    token = os.getenv("TYPESAFE_API_KEY")
    if analysis["data_quality"]["usable"] is not True or (today - as_of).days > 7 or as_of > today:
        result["reasons"] = ["stale or unusable market data"]
    elif not token:
        result["reasons"] = ["TYPESAFE_API_KEY unavailable"]
    else:
        try:
            response = query_jev(state, model, token)
            result["model"] = response["model"]
            result["answers"] = {key: response["answers"][key] for key in QUESTIONS}
            result["assessment"], result["reasons"] = assessment(
                result["answers"], min_confidence
            )
            downside = result["answers"]["downside"]
            distribution = downside["probabilities"]
            if distribution["unknown"] <= 0.1 and downside["confidence"] >= min_confidence:
                result["forecast"] = {
                    "event": "terminal_adjusted_return_lte_threshold",
                    "probability": distribution["downside"] /
                    (distribution["downside"] + distribution["not_downside"]),
                    "unknown_probability": distribution["unknown"],
                    "conditional_on_classifiable": True,
                    "validated_for_finance": False,
                }
        except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError):
            result["assessment"] = "insufficient_evidence"
            result["answers"] = {}
            result["forecast"] = None
            result["reasons"] = ["Jev unavailable or invalid response; no automatic retry"]
    write_json(output, result)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        raise SystemExit("decision input/output failed: " + type(error).__name__) from None