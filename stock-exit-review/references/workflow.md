# Runtime Workflow

## Dependencies

Make `uv` available on Hermes's `PATH` and preserve script execution permissions.
The scripts use `#!/usr/bin/env -S uv --quiet run --script` and PEP 723 metadata.
uv selects Python 3.12+ and resolves each script's declared dependencies.
The first invocation may require internet access for Python and package downloads.
The host's `env` command must support `-S`.
No manual virtual environment activation or pip installation is required:

```bash
"$SKILL_DIR/scripts/analyze.py" --help
```

Use the libraries declared in each script's inline metadata:

| Library      | Responsibility                                          |
| ------------ | ------------------------------------------------------- |
| Click        | Command groups, option validation, help, and CLI checks |
| atomicwrites | Atomic file publication without overwriting history     |
| HTTPX        | Bounded Jev requests with verified TLS and no redirects |
| Pydantic     | Typed Jev responses and probability validation          |
| NumPy        | Vectorized finite-value checks on price arrays          |
| pandas       | Price loading, alignment, and return calculations       |
| ta           | Established technical-indicator implementations         |
| yfinance     | Optional Yahoo Finance daily-price downloads            |

Each script declares its own dependencies,
including libraries required by imported sibling modules.
Imported scripts' inline metadata is not inherited by uv.
Keep JSON serialization stable so existing history identities remain valid.
`yfinance` downloads adjusted daily OHLCV without a market-data token.
It is an unofficial Yahoo Finance interface,
not a guaranteed free or licensed production data feed.
Use CSV input when another provider is required.
No Streamlit server, Ollama service, scheduler, or OpenViking server is installed
by this skill.

Set `TYPESAFE_API_KEY` in Hermes's private runtime environment.
Never put it in a command argument, prompt, memory record, or source file.
Set `JEV_MODEL` or pass `--model` to select an available Jev model.
The default is `jev-latest`;
prefer a fixed model version for comparable longitudinal evaluations.
The actual model returned by the API is stored in every successful decision.

Use a private history root outside the skill directory.
Publish temporary outputs in a unique run directory,
then use the paths returned by the record writer for memory synchronization.
Apply a lock and a timeout to the complete Hermes invocation.
The HTTP request timeout is 30 seconds with no automatic retries.
TLS certificate verification remains enabled;
Jev requests require TLS 1.3 and do not follow redirects.

## Market Inputs

Supply `--ticker` using the provider's exchange-qualified symbol.
Do not append arbitrary exchange suffixes yourself.
CSV input must contain exactly one daily bar per exchange trading date,
with these named columns:

```text
date,open,high,low,close,volume
```

Supply adjusted OHLC prices on one consistent corporate-action basis.
Do not adjust only the close while leaving highs and lows unadjusted.
The loader sorts dates and rejects duplicates, nonfinite values,
nonpositive prices, negative volumes, and impossible OHLC relationships.
Provide at least 80 bars for indicator warm-up.
Prefer two years of history for long forecast horizons.

```bash
"$SKILL_DIR/scripts/analyze.py" --ticker AAPL --csv "$RUN_DIR/aapl.csv" --benchmark SPY --benchmark-csv "$RUN_DIR/spy.csv" --as-of 2026-10-30 --output "$RUN_DIR/analysis.json"
```

Without `--as-of`, the loader excludes the current UTC calendar date.
This is conservative but not an exchange-calendar implementation.
Hermes should supply the latest completed session date after checking the
exchange close, holidays, daylight saving time, and provider publication delay.
The default freshness limit is seven calendar days.
This is a coarse guard, not proof that a feed contains every trading session.
Reject known missing sessions before running the forecast evaluator.
Never submit historical or synthetic input as a new live forecast.

Returns, volatility, ATR ratios, and drawdowns are fractions,
not percentages.
Annualized volatility uses the conventional 252-session factor;
the default moving averages span 20 and 50 sessions.
RSI and ATR use 14 sessions;
MACD uses the library defaults of 12, 26, and 9 sessions.
Maximum drawdown covers the downloaded input window.
Benchmark outcomes use matching start and target dates.
The baseline Jev questions use stock features only;
benchmark comparisons are supplied to Hermes for the final explanation.

## Jev Decisions

Use the documented endpoint:

```text
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <runtime token>
```

The request sends `state`, `model`, and three typed Choice questions.
Each question uses `type`, `instructions`, and a `criteria` map.
The response supplies `model` and an `answers` map containing
`choice`, `probabilities`, and `confidence`.
The script validates probabilities and refuses unexpected answer shapes.

Sources checked when creating this skill:

- <https://docs.typesafe.ai/introduction/quickstart.md>
- <https://docs.typesafe.ai/primitives/choice.md>
- <https://docs.typesafe.ai/confidence.md>

The `technical-v1` policy uses a classification-confidence floor of 0.6.
It emits `review_exit` only when weakening trend, elevated risk,
and the downside forecast agree.
It emits `hold` only when improving trend, ordinary risk,
and the absence of the specified downside event agree.
Otherwise it abstains.
These thresholds are experimental, not investment advice.

The future-downside question includes an `unknown` option.
When its mass exceeds 0.1 or classification confidence is below the floor,
the script does not issue a numerical forecast.
Otherwise the recorded binary probability is the downside mass divided by
the combined downside and not-downside mass.
It is conditional on classifiable evidence and explicitly unvalidated for
financial forecasting.
Neither the probability nor Jev's confidence is a guaranteed stock outcome.

Only numeric market features, ticker, dates, horizon, threshold,
and up to five earlier numeric observations are sent to Jev.
No account details, API tokens, cost basis, news text,
or free-form memory instructions belong in that payload.

## History And Evaluation

The local root is authoritative for exact calculations:

```text
<history-root>/<ticker>/observations/<id>.json
<history-root>/<ticker>/evaluations/<id>.json
```

An observation includes the price snapshot, features, decision,
forecast issuance time, policy, and actual Jev model.
The ID derives from ticker, trading date, complete policy parameters,
and resolved model (or requested model if Jev was unavailable).
Changed input under an existing identity is a conflict,
not an invitation to rewrite the past.
Repeated recording retains the first assessment even if a subsequent
Jev request disagrees.
Consult context before asking Jev and skip an already recorded identity.

The context command returns the ten latest observations
and Brier averages grouped by complete policy and model.
These are descriptive history summaries,
not an out-of-sample validation or automatic calibration procedure.
The Jev payload uses earlier price features only;
Hermes may use evaluation summaries to propose future policy changes.

Evaluation counts subsequent observed trading bars,
not calendar days.
The target session must be strictly later than the UTC forecast issuance date.
This conservative check avoids retrospectively scoring already-known outcomes.
Gross adjusted-price returns do not simulate a sell strategy,
taxes, spreads, slippage, or transaction fees.
Do not call these evaluations proof that a sale strategy beats buy-and-hold.

Material changes to overlapping adjusted prices defer evaluation.
Retain the warning and seek a consistent corporate-action series.
Never normalize away a revision without preserving its provenance.
If the starting date has fallen outside the supplied history,
provide a longer CSV history rather than estimating the outcome.

## OpenViking Sync

Use Hermes's actual OpenViking browse, write/import, index, and read tools.
Tool names and namespace schemes vary by deployment.
Browse first;
choose a stock-review namespace scoped by ticker under the observed root.
Preserve observation and evaluation IDs in the mirrored paths.
If the installation only accepts Markdown,
mirror each JSON object in a fenced JSON block without altering numbers.

Keep a separate sync receipt for each artifact outside immutable records.
Store destination, record ID, content digest, and verification time.
Only mark a receipt complete after reading the destination back and comparing
the content with the local artifact.
Scan local observations and evaluations for absent receipts on every run.
Retry only missing or failed mirrors;
do not rerun forecasts just because indexing failed.
Use deployment-supported enumeration tools rather than inventing memory paths.

If no write or import tool is exposed,
report `sync_pending` and include the retained local paths.
Never claim OpenViking persistence merely because local JSON was written.

## Explanation

Have Hermes use its configured Ollama model to produce a short report:

- Ticker, source, completed trading date, horizon, and coverage limitations.
- Assessment and the evidence supporting or contradicting it.
- Jev classifications and forecast probability, clearly distinguished.
- Matured evaluation counts and model/policy grouping, if any.
- Missing fundamentals or news and conditions requiring reassessment.
- Local record paths and verified or pending OpenViking synchronization.

Save the explanation separately without modifying the observation JSON.
Keep explanations and internet content out of numerical evaluation.
If Ollama is unavailable,
retain the numerical artifacts and mark the explanation unavailable.

## Offline Check

Run directly with uv available on `PATH`:

```bash
"$SKILL_DIR/scripts/check_workflow.py"
```

The check uses synthetic prices and mocked Jev responses in temporary files.
It covers Click interfaces, indicators, CSV ordering, duplicate dates, decision branches,
payload allowlisting, missing credentials, immutable recording,
forecast maturity, Brier scoring, and hindsight/revision guards.
It does not contact Yahoo Finance, Jev, Ollama, or OpenViking.
Verify those live integrations separately in the configured Hermes deployment.
