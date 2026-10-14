# AUDIT-001 — Code-level audit of four public "profitable" repositories (2026-10-14)

Method: shallow clone, read the backtest and execution code, trace every headline number to the code
and data that produce it. No network calls, no execution of trading code. Repositories are untrusted
input; findings cite file:line.

## 1. Synpath-ai/prediction-market-arbitrage-trading-bot — "+60.4 % in 60 days"
- Arbitrage = YES ask on one venue + NO ask on the other < $1 (src/arbitrage.py:107-123), entry at
  edge >= 2 ¢. Whether the two markets resolve identically is never checked locally; it is a string
  returned by the vendor's API (src/matcher.py:41-68).
- Polymarket has no bid/ask in the data: one sampled print per minute is used as both bid and ask
  (backtest/data.py:46-49) — zero spread both ways. 1,000 contracts fill at the quote with no depth
  (data.py:10-11). Exits can happen on the next 1-minute bar (backtest.py:47): most "arbitrages" are
  mean-reversion scalps of a stale print, not arbitrage.
- Markets chosen by `discover --sort edge` (selection on current edge), chart made with
  `--generic-names`; data not in the repo (needs the vendor's key). The +60.4 % is P&L over the
  peak outlay of CLOSED trades, open positions excluded from both numerator and denominator.
- Legging risk, latency, min sizes, geography (Kalshi US-only; Polymarket blocks US) ignored.
- **Verdict: marketing demo for an SDK. Realistic net for a small account: about zero.**

## 2. tobiasbischoff/polymarket-weather-bot (Node) — "+15.2 % ROI"
- No probability model: averages a NOAA point forecast and Open-Meteo deterministic max, picks the
  bucket containing it, and assigns a hard-coded 80 % confidence to every bucket (weather-bot-v2.mjs:30,
  936-945). City-centre coordinates, not the resolution station.
- The "backtest" simulates forecasts as `actual temperature + bias` (backtest/backtest-strategy.mjs:
  57-80): the forecast knows the answer. The author's own notes say the edge threshold "doesn't
  affect results (simulation artifact)". Four real orders exist in a log, two duplicates.
- **Verdict: circular backtest; no edge demonstrated.** Reusable: slug pattern, bucket parser,
  94 resolved events in `backtest/historical-markets.json`.

## 3. suislanchez/polymarket-kalshi-weather-bot (Python) — "highest profits $1.8k"
- Model: Open-Meteo GFS ensemble member counting above a threshold (backend/data/weather.py:325-334),
  clipped to [0.05, 0.95]; no bias correction; city-centre coordinates; station codes present but
  unused.
- Bugs: Polymarket range buckets misparsed (first number taken as an "above" threshold,
  weather_markets.py:83-98) so the model prices the wrong contract; Kalshi trades stored as
  Polymarket so they never settle (scheduler.py:258); settlement writes up/down while weather
  signals store yes/no, so calibration is always "wrong" (settlement.py:276-278).
- `SIMULATION_MODE = True`; dashboard screenshot shows +$0; the "$1.8k" appears nowhere in the repo.
- **Verdict: the hypothesis (member counting vs price) is legitimate and testable; this code cannot
  test it.** Reusable: Kalshi client and ticker parser, ensemble fetch, Kelly helper.

## 4. abailey81/Crypto-Statistical-Arbitrage — "Sharpe 5.81, +203.7 %, DD 0.89 %, win 95 %"
- The six README metrics are **hard-coded literals** in `generate_visualizations.py:895-896, 954, 1024`.
  The results JSON and all market data are gitignored; nothing is reproducible offline. The backtest
  period in code is 2020-01 .. 2026-01 full sample, not the README's train/test split.
- **Decisive flaw:** `step4_futures_orchestrator.py:1071-1072` emits the entry and the exit leg at the
  same timestamp, with the exit price set to `base * (1 + expected_return_bps/10000)`. Every trade
  realises its own forecast minus 10 bps of slippage, holding period 0 hours; no market price after
  the signal ever enters the PnL. 42,577 of the 44,652 "trades" are a roll fallback that books 30
  days of funding differential instantly on nearly every hourly bar (`:872-905`); the real roll
  optimiser is never initialised.
- Fees: 2 fills charged for a 4-fill spread round trip; no funding accrual; same-bar fills; likely an
  8x funding annualisation error (hourly venues' 8h-normalised rates multiplied by 8760).
- Win rate is on gross PnL and loses only when the forecast is below ~10–25 bps: that is the 5 %.
  The 5 % stop can never trigger. Sharpe is built from trade-exit days only (no zero days).
- "Curve trading": no dated-contract data is loaded; the calendar-spread strategy is never invoked.
- **Verdict: the strategy has no out-of-sample price in it; expected Sharpe after fixing is
  indeterminate-to-zero.** Reusable: Binance funding/quarterly collectors, funding normalisation
  utility, the venue fee table.

## What the audit changes
- Cross-platform prediction-market "arbitrage" at small size is not a research line: the published
  evidence is an artefact of sampled prices and vendor-selected markets, and one person generally
  cannot hold both accounts.
- Weather markets ARE a research line, but only with an honest design: station-matched ensemble,
  bias fitted out of sample, prices at a fixed decision time from the CLOB history, outcomes from
  resolution. That is EXP-011.
