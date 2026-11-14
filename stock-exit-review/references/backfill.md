# Backfilling Historical Dates (no look-ahead)

Use when running this skill for a PAST trading date, or backfilling a contiguous
range of completed trading days that predate the current clock. One date per run,
chronological, weekends and US market holidays excluded.

## Why a past date is hard

The liveness check compares the reference `now()` to the observation's
`captured_at`. Running for a past date against the real clock marks every
pre-recent record "stale or unusable" and forces `insufficient_evidence`. You
cannot set the system clock (not root; usually no faketime), so move ONLY the
reference time, never the data.

## The launcher pattern: pre-import, then patch, then exec

- Do NOT freeze the clock at interpreter startup (e.g. a `sitecustomize.py` on
  PYTHONPATH). pandas/ta/yfinance touch time-based internals AT IMPORT and hang
  forever when the clock is frozen; the patch reads fine for `datetime.now` but
  the heavy libs never finish importing.
- Instead: in a launcher, import every heavy lib (pandas, ta, yfinance, click,
  atomicwrites, httpx, pydantic) FIRST while the clock is real; THEN monkeypatch
  `datetime.now` (and any `now()` the skill calls) to a fixed `BACKFILL_NOW` =
  the review date at market close UTC; THEN exec the real skill script. Leave the
  skill source unmodified.
- Data truncation is the script's own `--as-of` (it slices the CSV to the review
  date). Only the liveness reference time moves. That IS the no-look-ahead
  guarantee: `captured_at == review date` and no feature sees a later bar.
- Verify the guarantee per record: assert `captured_at` equals the review date and
  the features exclude every bar after `--as-of`.

## Preflight paths

Preflight rejects a `run_dir` or `history_root` inside the skill source tree.
Put them under an exec-capable `$HOME` (never `/tmp`, which is `noexec` here),
e.g. `$HOME/.stock-history` and `$HOME/.stock-runs`.

## Resumable driver + bounded batches

- One driver per date: `analyze -> decide -> record -> verify`, writing a per-date
  receipt carrying a terminal status. Skip any date that already has a `complete`
  receipt, so a resume continues from the earliest incomplete date (idempotent).
- Write the receipt BEFORE the inter-iteration pause. A terminated or
  time-capped batch call therefore still leaves every COMPLETED date's receipt on
  disk — a batch that times out is not a failed batch. Verify completion by
  receipt presence plus `history.py verify` (re-hash the observation), never by
  the shell call's exit code.
- Pace N seconds between successful iterations (this user's backfill used 60s).
- Batch size under the terminal ceiling: a 60s pause plus a ~40s pipeline means
  ~5 dates/call fills the ~420s foreground ceiling, and the 6th date's receipt
  still lands because it is written before its own pause. Do not relaunch one
  unattended multi-hour loop if the environment gates long-running/irreversible
  commands for consent; fall back to bounded per-date batches (each still
  resumable) rather than retrying the gated loop through another tool or a
  heredoc.

## Data hygiene

- Build one adjusted-OHLCV master CSV per ticker (auto-adjusted) with enough
  warm-up history; drop the incomplete final bar before slicing.
- Some feeds emit a phantom bar on a US holiday that is not a trading day (e.g.
  Good Friday can carry OHLCV that looks real). Drop it from BOTH the master CSV
  and the observation-day list, and confirm the day list excludes weekends plus
  US market holidays (New Year's, MLK, Presidents' Day, Good Friday, Memorial,
  Juneteenth, Independence, Labor, Thanksgiving, Christmas).

## Expected result — do not "fix" it

On technical-only data the Jev `downside` question confidence sits systematically
below the 0.60 policy floor, so a backfill of a stable or rising name produces
mostly `insufficient_evidence` abstentions. That is the skill's correct
conservative behavior, not a pipeline fault. Do not lower the floor, force a
`hold`, or recycle an older decision to make the backfill "produce" signals;
record the abstentions and report them.

### Why the confidence never accumulates

The decision is point-in-time and _conjunctive_: `decide.py`'s `assessment()`
aborts to `insufficient_evidence` the moment ANY of the three current
classifications (trend, risk, downside) is below the `--min-confidence` floor.
`decide.py` feeds Jev only the last five prior _market features_
(`previous_market_features` in the state) — NOT prior Jev _responses_
(classifications, confidences, decisions) — so a weak reading one day does not
compound with a weak reading the next; confidence cannot accumulate across the
series. The binding constraint is usually the `downside` question (observed
confidence ~0.04-0.40, never >= 0.60): forecasting a specific >= 5% drop within
20 sessions for a stable large-cap is near a coin flip, and Jev hedges with an
`unknown` bucket that further dilutes every class's confidence. Diagnose which
question is the binding constraint with `scripts/diagnose_abstention.py`
(per-question confidence min/max/mean and the count clearing the floor, plus any
date on which all three clear) rather than re-deriving it by hand. Making the
decision accumulate evidence over prior responses (a rolling/Bayesian update) is a
new policy version (`technical-v2`); the Learning Policy requires the user to
approve it, so do not rewrite the decision or lower the floor unilaterally.

### Context look-ahead guard

`history.py context` lists ALL observations regardless of date; `decide.py`'s
`item["as_of"] < analysis["as_of"]` filter is the ONLY thing that keeps a
future-dated or test record out of the decision (the analysis hash excludes the
context, so a polluted context does not corrupt the record). Keep the history root
free of future-dated/test observations — they pollute every run's context even
though they do not leak into a decision.

## Capture and mirror

Run `scripts/capture.py capture` after `history.py record` to write the
authoritative durable record: a self-contained capture (analysis + decision +
evaluation + explanation + OpenViking sync status) and a reconciliation manifest
under a persistent `CAPTURE_ROOT` outside the skill tree. Its ID reuses the
`history.identity` scheme, so it always matches the observation ID. On every run,
first run `capture.py pending` to list records whose mirror is not yet `verified`,
retry each with one write + one exact read-back (dedupe by ID, never rerun a
forecast), and `capture.py confirm` only after the read-back content matches.
The `history.py` local record and the `capture.py` manifest are authoritative;
the OpenViking mirror is a reconciled copy, best-effort `sync_pending` when the
signed-upload host is unreachable (see the main gotchas). Batch compact JSON per
run with real numbers preserved; never fabricate a read-back for a just-mirrored
record.
