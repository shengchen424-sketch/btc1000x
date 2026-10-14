# BTC 1000X — Phase 2 status (2026-10-14 13:05 UTC)

Autonomous research loop, reporting after each round. Everything below is on `main`.

## Scoreboard

| Exp | Family | Trials | VALIDATION 2023–24 | Holdout 2025-01..2026-09 | State |
|---|---|---|---|---|---|
| EXP-001 | A failed-break 15m; B trend-pullback 1h/4h | 24 | 0 lead; costs 0.2–0.6 R/trade | — | closed |
| EXP-001-INV | the same 24 inverted | 24 | all negative: loss is cost, not direction | — | closed |
| EXP-002 | C funding-rate extreme reversal | 8 | 0 lead (positive on TRAIN only) | — | closed |
| EXP-004 | D daily-close trend, perp + funding | 6 | 3 long rules LEAD (Sharpe 1.4–1.6, below buy-and-hold) | **REJECTED** (T7_L -10.5 %/yr) | closed |
| EXP-005 / 005b | E options-expiry 08:00 UTC fade | 4 + 2 | 2 LEAD (240-min hold, +0.26 R, p 0.008) | **REJECTED** (-0.08 R, every half-year negative) | closed |
| EXP-006 | F 3-sigma hourly shock fade, OI-flush filter | 4 | 0 lead; OI filter removes continuation, no reversal left | — | closed |

Six families, 72 trials, two one-shot holdout looks spent. Shadow registries are empty. No trial is
eligible for forward observation, let alone live capital.

## What the evidence says, in order of strength

1. **Cost share per trade is the binding constraint at 10 USDT.** With a 1 % risk budget the widest
   executable stop is 0.91 % of price, and at that width a taker round trip is >= 0.2 R. No intraday
   family produced a gross edge above 0.15 R.
2. **Two mechanisms that were real in 2023–24 were gone in 2025–26** (expiry fade, long daily trend).
   The validation period was a bull market with one drawdown; the holdout was a bear/range window.
   A result that holds in one regime and not the next is not an edge for a 10 USDT account that cannot
   survive learning which regime it is in.
3. **Nothing in the literature scan (LIT-001) clears the cost hurdle unconditionally**; the three
   mechanism-backed candidates have now been tested (two) or lack historical data (ETF flows,
   2024+ only, and the public source blocks automated access).

## What remains that is cheap and registered-testable

- EXP-007 FOMC pre-announcement drift (calendar from federalreserve.gov; ~8 events a year; low power).
- EXP-008 daily volatility-compression breakout (undocumented in the literature; daily clock so costs
  are not binding; the only daily family not yet tried).
- Maker-fee execution study: fill probability of a passive limit at the signal close, measured on 1m
  bars — a cost-model input, not a strategy. Would lower cost share from ~0.2 R to ~0.06 R on
  1.5 % stops, which is the only way Strategy B long (gross +0.08..+0.15 R) could turn net positive.
  This would be a registered rescue attempt of a closed family and is flagged as such.

## Decisions only the owner can make

1. Capital: 10 USDT cannot pay for any intraday strategy; 200–300 USDT changes the feasible stop
   width and the cost share. The research can continue at 10 USDT but the answer so far is "no".
2. Whether to spend effort on the maker-execution rescue of Strategy B (low prior, transparent).
3. Whether to widen the universe beyond BTC (the owner's earlier project found that the only factors
   with evidence are cross-sectional books over many coins, which this project's scope excludes).

## Operations
- Repository: github.com/shengchen424-sketch/btc1000x, 30 tests passing, data 0.3 GB (rebuildable).
- Shadow runner is built and tested against live Bitget data; nothing is registered for it to run.
- No order has been or can be sent (`LIVE_TRADING` False; live path raises).
