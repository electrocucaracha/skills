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

"""Run offline checks; synthetic inputs never become live forecasts."""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1,<9",
#     "atomicwrites>=1.4,<2",
#     "httpx>=0.28,<1",
#     "pydantic>=2.10,<3",
#     "numpy>=1.26,<3",
#     "pandas>=2.2,<3",
#     "ta==0.11.0",
# ]
# ///

import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from click.testing import CliRunner
import pandas as pd

import analyze
import decide
import history


class WorkflowChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.analysis = {
            "ticker": "AAPL", "as_of": "2026-10-26", "source": "csv",
            "series": [{"date": "2026-10-26", "close": 100}],
            "features": dict.fromkeys(decide.FEATURE_KEYS, 1.0),
            "data_quality": {"usable": True},
        }
        self.decision = {
            "ticker": "AAPL", "as_of": "2026-10-26",
            "analysis_hash": decide.analysis_hash(self.analysis),
            "policy": {"version": "technical-v1", "horizon_sessions": 2,
                       "downside_threshold": -0.05, "min_confidence": 0.6},
            "model": "offline-fixture", "requested_model": "offline-fixture",
            "assessment": "hold", "issued_at": "2026-10-27T01:00:00+00:00",
            "forecast": {"probability": 0.8},
        }
        self.answers = {
            "trend": {"type": "choice", "confidence": 0.85, "choice": "improving",
                      "probabilities": {"improving": 0.9, "deteriorating": 0.05, "mixed": 0.05}},
            "risk": {"type": "choice", "confidence": 0.85, "choice": "ordinary",
                     "probabilities": {"ordinary": 0.9, "elevated": 0.05, "unknown": 0.05}},
            "downside": {"type": "choice", "confidence": 0.85, "choice": "not_downside",
                         "probabilities": {"downside": 0.05, "not_downside": 0.9, "unknown": 0.05}},
        }

    def test_indicators_and_csv_validation(self):
        close = pd.Series(range(100, 200), dtype=float)
        frame = pd.DataFrame({"open": close, "high": close + 1, "low": close - 1,
                              "close": close, "volume": 1000})
        frame.index = pd.bdate_range(end="2026-10-30", periods=100)
        self.assertEqual(analyze.features(frame)["sma_20"], 189.5)
        self.assertEqual(analyze.features(frame)["max_drawdown"], 0)
        path = self.root / "prices.csv"
        frame.iloc[::-1].to_csv(path, index_label="date")
        loaded = analyze.load_prices("AAPL", str(path), dt.date(2026, 10, 30))
        self.assertTrue(loaded.index.is_monotonic_increasing)
        output = self.root / "analysis.json"
        invocation = CliRunner().invoke(analyze.main, [
            "--ticker", "aapl", "--csv", str(path), "--as-of", "2026-10-30",
            "--output", str(output),
        ])
        self.assertEqual(invocation.exit_code, 0, invocation.output)
        self.assertEqual(analyze.read_json(output)["ticker"], "AAPL")
        pd.concat([frame, frame.iloc[-1:]]).to_csv(path, index_label="date")
        with self.assertRaises(ValueError):
            analyze.load_prices("AAPL", str(path), dt.date(2026, 10, 30))

    def test_assessment_branches(self):
        self.assertEqual(decide.assessment(self.answers, 0.6)[0], "hold")
        self.answers["risk"]["choice"] = "elevated"
        self.assertEqual(decide.assessment(self.answers, 0.6)[0], "insufficient_evidence")
        self.answers["trend"]["choice"] = "deteriorating"
        self.answers["downside"]["choice"] = "downside"
        self.assertEqual(decide.assessment(self.answers, 0.6)[0], "review_exit")
        self.answers["trend"]["confidence"] = 0.1
        self.assertEqual(decide.assessment(self.answers, 0.6)[0], "insufficient_evidence")

    def test_jev_transport_and_validation(self):
        response = {"model": "offline-fixture", "answers": self.answers}
        with patch("decide.httpx.Client") as client:
            handle = client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value
            handle.iter_bytes.return_value = [json.dumps(response).encode()]
            self.assertEqual(decide.query_jev({}, "fixture", "offline-placeholder"), response)
            self.assertEqual(client.call_args.kwargs["timeout"], 30)
            self.assertFalse(client.call_args.kwargs["follow_redirects"])
            self.answers["risk"]["probabilities"]["ordinary"] = 2
            handle.iter_bytes.return_value = [json.dumps(response).encode()]
            with self.assertRaises(ValueError):
                decide.query_jev({}, "fixture", "offline-placeholder")

    def test_missing_credentials_and_mocked_forecast(self):
        today = dt.datetime.now(dt.timezone.utc).date()
        self.analysis["as_of"] = (today - dt.timedelta(days=1)).isoformat()
        input_path, output_path = self.root / "analysis.json", self.root / "decision.json"
        analyze.write_json(input_path, self.analysis)
        arguments = ["--analysis", str(input_path), "--output", str(output_path)]
        runner = CliRunner()
        with patch.dict("os.environ", {}, clear=True):
            with patch("decide.query_jev") as remote:
                invocation = runner.invoke(decide.main, arguments)
                self.assertEqual(invocation.exit_code, 0, invocation.output)
                remote.assert_not_called()
        self.assertEqual(analyze.read_json(output_path)["assessment"], "insufficient_evidence")
        with patch.dict(
            "os.environ", {"TYPESAFE_API_KEY": "offline-placeholder"}, clear=True
        ), patch("decide.query_jev", return_value={"model": "fixture", "answers": self.answers}):
            invocation = runner.invoke(decide.main, arguments)
            self.assertEqual(invocation.exit_code, 0, invocation.output)
        result = analyze.read_json(output_path)
        self.assertEqual(result["assessment"], "hold")
        self.assertAlmostEqual(result["forecast"]["probability"], 0.05 / 0.95)
        self.assertNotIn("offline-placeholder", json.dumps(result))

    def test_feature_allowlist(self):
        features = self.analysis["features"]
        features["account_identifier"] = "private"
        self.assertNotIn("account_identifier", decide.market_features(features))
        features["close"] = float("nan")
        with self.assertRaises(ValueError):
            decide.market_features(features)

    def test_click_interfaces(self):
        runner = CliRunner()
        for command in (analyze.main, decide.main, history.main):
            invocation = runner.invoke(command, ["--help"])
            self.assertEqual(invocation.exit_code, 0, invocation.output)
        invocation = runner.invoke(analyze.main, [
            "--ticker", "../private", "--output", str(self.root / "out.json"),
        ])
        self.assertEqual(invocation.exit_code, 2)
        invocation = runner.invoke(analyze.main, [
            "--ticker", "AAPL", "--max-age-days", "31",
            "--output", str(self.root / "out.json"),
        ])
        self.assertEqual(invocation.exit_code, 2)
        input_path = self.root / "analysis.json"
        analyze.write_json(input_path, self.analysis)
        invocation = runner.invoke(decide.main, [
            "--analysis", str(input_path), "--horizon", "0",
            "--output", str(self.root / "out.json"),
        ])
        self.assertEqual(invocation.exit_code, 2)
        output = self.root / "context.json"
        invocation = runner.invoke(history.main, [
            "--root", str(self.root), "context", "--ticker", "aapl",
            "--output", str(output),
        ])
        self.assertEqual(invocation.exit_code, 0, invocation.output)
        self.assertEqual(analyze.read_json(output)["ticker"], "AAPL")

    def test_immutable_records_and_context(self):
        first = history.record(self.root, self.analysis, self.decision)
        self.assertEqual(first["status"], "created")
        self.analysis["captured_at"] = "new capture"
        self.analysis["requested_as_of"] = "2026-10-27"
        self.assertEqual(history.record(self.root, self.analysis, self.decision)["status"], "existing")
        self.assertEqual(history.context(self.root, "AAPL")["observations"][0]["id"], first["id"])
        self.analysis["series"][0]["close"] = 101
        self.decision["analysis_hash"] = decide.analysis_hash(self.analysis)
        with self.assertRaises(ValueError):
            history.record(self.root, self.analysis, self.decision)

    def test_maturity_scoring_revisions_and_leakage(self):
        observation = {"id": "fixture", "analysis": self.analysis, "decision": self.decision}
        latest = copy.deepcopy(self.analysis)
        self.assertIsNone(history.evaluate_one(observation, latest))
        latest["as_of"] = "2026-10-28"
        latest["series"] += [{"date": "2026-10-27", "close": 98},
                             {"date": "2026-10-28", "close": 90}]
        outcome = history.evaluate_one(observation, latest)
        self.assertTrue(outcome["downside_event"])
        self.assertAlmostEqual(outcome["brier_score"], 0.04)
        latest["series"][0]["close"] = 101
        self.assertEqual(history.evaluate_one(observation, latest)["status"], "historical_revision")
        self.decision["issued_at"] = "2026-10-28T23:00:00+00:00"
        self.assertEqual(history.evaluate_one(observation, latest)["status"], "ineligible")


if __name__ == "__main__":
    unittest.main()