# Runtime Workflow

## Contents

- [Dependencies](#dependencies)
- [Restricted Hermes Runtimes](#restricted-hermes-runtimes)
- [Market Inputs](#market-inputs)
- [Jev Decisions](#jev-decisions)
- [History And Evaluation](#history-and-evaluation)
- [OpenViking Sync](#openviking-sync)
- [Explanation](#explanation)
- [Offline Check](#offline-check)

## Dependencies

Make system Python 3.11+ and `uv` available on Hermes's `PATH`.
Run the standard-library preflight before downloading market data or calling Jev:

```bash
python3 "$SKILL_DIR/scripts/preflight.py" --run-dir "$RUN_DIR" --history-root "$STOCK_HISTORY_ROOT"
```

The probe checks writable absolute directories outside the installed skill,
then imports the workflow modules and native dependencies through uv.
It reads dependencies from the scripts' PEP 723 metadata.
It does not call Yahoo Finance, Jev, or OpenViking,
or print credentials and raw dependency errors.
It has a 180-second default timeout with no retries;
operators can set `--timeout` between 1 and 600 seconds during provisioning.
Exit zero and `status: ready` establish local import readiness only,
not network access or durable storage.

Use explicit uv invocations rather than relying on executable script bits
or the shebang's `env -S` support.
uv selects Python 3.12+ and resolves each script's declared dependencies.
The first invocation may require internet access for Python and package downloads.
No manual virtual environment activation or pip installation is required:

```bash
uv run --no-project --script "$SKILL_DIR/scripts/analyze.py" --help
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
Use a ten-minute workflow budget by default,
including preflight and memory synchronization;
stop and report the last completed stage when it expires.
The HTTP request timeout is 30 seconds with no automatic retries.
TLS certificate verification remains enabled;
Jev requests require TLS 1.3 and do not follow redirects.

## Restricted Hermes Runtimes

Resolve `SKILL_DIR` from the installed skill location provided by Hermes.
Host checkout paths and sandbox mount paths can differ.
If the directory is absent or unreadable,
stop and request the correct skill mount rather than searching the filesystem.
An inaccessible terminal working directory must be corrected in the terminal
or scheduler configuration before launching commands.
Do not reset `HOME`;
that can relocate uv's cache and managed Python onto unsuitable storage.

On Linux,
`failed to map segment from shared object` may indicate a `noexec` mount,
not insufficient memory or an incompatible NumPy release.
A writable `/tmp` can still forbid executable mappings from native `.so` files.
Changing Python versions, reinstalling wheels, or chmod cannot fix `noexec`.
Plain Python scripts can be read from such a mount by an executable interpreter;
native libraries still need executable storage.

Before enabling scheduled reviews,
an operator must provision an executable Python interpreter and writable,
exec-capable locations for `UV_CACHE_DIR` and `UV_PYTHON_INSTALL_DIR`,
or rebuild the sandbox image with the required runtime.
Set these variables in the scheduler environment before preflight
and preserve them for all subsequent commands.
Never remount filesystems, elevate privileges, or disable sandbox protections.
If all writable storage is `noexec`,
stop with a runtime blocker.
Do not recreate NumPy, pandas, ta, Pydantic, HTTPX, or the history writer
as ad hoc pure-Python fallback scripts.

The scheduler must also supply a persistent `STOCK_HISTORY_ROOT`,
such as a durable volume visible to the execution sandbox.
Preflight checks writability but cannot prove persistence across sandbox restarts.
Temporary run artifacts may use `/tmp`;
authoritative history may not rely on ephemeral sandbox storage.
If a required tool approval is denied or times out,
stop that operation and report it.
Do not retry through `execute_code`, another tool, or a terminal heredoc.

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
uv run --no-project --script "$SKILL_DIR/scripts/analyze.py" --ticker AAPL --csv "$RUN_DIR/aapl.csv" --benchmark SPY --benchmark-csv "$RUN_DIR/spy.csv" --as-of 2026-10-30 --output "$RUN_DIR/analysis.json"
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
Require exact content storage and read-back,
not a memory-extraction tool that summarizes or rewrites the object.

Keep a separate sync receipt for each artifact outside immutable records.
Store destination, record ID, content digest, and verification time.
Only mark a receipt complete after reading the destination back and comparing
the content with the local artifact.
Scan local observations and evaluations for absent receipts on every run.
Retry only missing or failed mirrors;
do not rerun forecasts just because indexing failed.
Use deployment-supported enumeration tools rather than inventing memory paths.

If an import tool returns a signed-upload URL,
attempt it only through the documented transport to the expected deployment host.
Keep signed URLs and tokens out of logs and receipts.
The execution sandbox may not resolve or reach a host that the MCP proxy can reach.
Make at most one upload attempt per artifact with a 30-second transport timeout.
If that host is unreachable,
do not guess alternate hosts, tunnel, or switch to lossy memory extraction.
An MCP-only exact write is acceptable only if that capability is documented
by the deployment's tools.

Make at most one exact read-back attempt per artifact in a run.
An accepted asynchronous write is still `sync_pending` until its content matches.
Record the returned destination or job ID and retry verification on a later run;
do not upload it again merely because indexing is pending.
Semantic search misses do not establish write failure,
and approximate search hits do not verify a mirror.

If no reachable exact write or import tool is exposed,
report `sync_pending` and include the retained local paths.
A pending receipt includes the failure stage and safe reason,
destination or job ID if provided, content digest, and last attempt time.
Leave verification time unset until exact read-back succeeds.
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

Run with uv available on `PATH`:

```bash
uv run --no-project --script "$SKILL_DIR/scripts/check_workflow.py"
```

The check uses synthetic prices and mocked Jev responses in temporary files.
It covers Click interfaces, indicators, CSV ordering, duplicate dates, decision branches,
payload allowlisting, missing credentials, immutable recording,
forecast maturity, Brier scoring, hindsight/revision guards,
benchmark retention, and bounded preflight failures.
It does not contact Yahoo Finance, Jev, Ollama, or OpenViking.
Verify those live integrations separately in the configured Hermes deployment.
