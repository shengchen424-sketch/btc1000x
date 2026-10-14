# EXP-001 — Result: 0 CANDIDATE, 0 LEAD out of 24 trials; router adds no value

Run 2026-10-14 on commit `f34f69a` (registration in the same commit). VALIDATION = 2023-01-01 .. 2024-12-31.
HOLDOUT (2025-01 .. 2026-09) was not loaded. Files: `trials_val.csv`, `trials_train.csv`, `trades.parquet`
(31,957 trades with regime and loss class), `router.json`, `verdict.json`.

## Verdict table (VALIDATION, net R per trade, 95 % bootstrap CI)

| Trial | n | gross R | cost R | **net R** | CI | win % | stop % | gate |
|---|---|---|---|---|---|---|---|---|
| A long lb48 rr1.5 | 1697 | -0.08 | 0.58 | **-0.66** | [-0.71, -0.61] | 35 | 0.7 | FAIL |
| A long lb48 rr1.5 vol1.5 | 1132 | -0.10 | 0.58 | **-0.68** | [-0.75, -0.62] | 34 | 0.7 | FAIL |
| A long lb48 rr3 | 1667 | -0.09 | 0.56 | **-0.65** | [-0.72, -0.59] | 30 | 0.7 | FAIL |
| A long lb48 rr3 vol1.5 | 1124 | -0.10 | 0.57 | **-0.67** | [-0.75, -0.59] | 29 | 0.7 | FAIL |
| A long lb96 rr1.5 | 991 | -0.01 | 0.48 | **-0.49** | [-0.56, -0.42] | 39 | 0.7 | FAIL |
| A long lb96 rr1.5 vol1.5 | 662 | -0.06 | 0.48 | **-0.54** | [-0.62, -0.45] | 37 | 0.8 | FAIL |
| A long lb96 rr3 | 977 | -0.04 | 0.46 | **-0.50** | [-0.58, -0.42] | 34 | 0.7 | FAIL |
| A long lb96 rr3 vol1.5 | 661 | -0.07 | 0.47 | **-0.54** | [-0.64, -0.43] | 33 | 0.8 | FAIL |
| A short lb48 rr1.5 | 1894 | -0.01 | 0.64 | **-0.64** | [-0.70, -0.59] | 36 | 0.6 | FAIL |
| A short lb48 rr1.5 vol1.5 | 1184 | +0.00 | 0.63 | **-0.62** | [-0.69, -0.56] | 36 | 0.6 | FAIL |
| A short lb48 rr3 | 1853 | -0.04 | 0.61 | **-0.65** | [-0.71, -0.58] | 29 | 0.6 | FAIL |
| A short lb48 rr3 vol1.5 | 1177 | -0.01 | 0.61 | **-0.62** | [-0.70, -0.54] | 30 | 0.6 | FAIL |
| A short lb96 rr1.5 | 1171 | 0.00 | 0.54 | **-0.54** | [-0.60, -0.48] | 38 | 0.6 | FAIL |
| A short lb96 rr1.5 vol1.5 | 752 | -0.04 | 0.55 | **-0.58** | [-0.66, -0.50] | 36 | 0.7 | FAIL |
| A short lb96 rr3 | 1147 | -0.02 | 0.52 | **-0.53** | [-0.61, -0.45] | 32 | 0.6 | FAIL |
| A short lb96 rr3 vol1.5 | 749 | -0.03 | 0.53 | **-0.56** | [-0.66, -0.46] | 31 | 0.7 | FAIL |
| B long depth0.5 trail2 | 342 | +0.09 | 0.24 | **-0.14** | [-0.27, -0.01] | 33 | 1.3 | FAIL |
| B long depth0.5 trail3 | 258 | +0.15 | 0.22 | **-0.07** | [-0.25, +0.13] | 34 | 1.6 | FAIL |
| B long depth1.0 trail2 | 366 | +0.08 | 0.23 | **-0.15** | [-0.28, -0.01] | 33 | 1.3 | FAIL |
| B long depth1.0 trail3 | 274 | +0.12 | 0.21 | **-0.09** | [-0.27, +0.09] | 34 | 1.6 | FAIL |
| B short depth0.5 trail2 | 256 | -0.09 | 0.24 | **-0.33** | [-0.45, -0.20] | 29 | 1.3 | FAIL |
| B short depth0.5 trail3 | 198 | -0.14 | 0.22 | **-0.35** | [-0.51, -0.18] | 27 | 1.5 | FAIL |
| B short depth1.0 trail2 | 275 | -0.09 | 0.24 | **-0.33** | [-0.44, -0.21] | 30 | 1.3 | FAIL |
| B short depth1.0 trail3 | 213 | -0.13 | 0.22 | **-0.35** | [-0.50, -0.18] | 27 | 1.5 | FAIL |

No trial has a positive calendar year in VALIDATION (0 of 2 for every trial). Every trial's CI upper bound
is below +0.13 R; 20 of 24 are entirely below zero.

## What the numbers say

1. **Strategy A has no edge before costs.** Gross R (fills included, fees and funding excluded) is
   -0.10 to 0.00 for all 16 trials, on 660–1,900 trades each. The failed-break reclaim on 15m BTC bars
   is not followed by the move the hypothesis needs. Costs then take 0.46–0.64 R per trade because the
   stops are 0.6–0.8 % of price: 12 bps fees + 13 bps slippage on a 0.65 % stop is 0.38 R before funding
   and gap losses. The 10 USDT replay loses 73–91 % on VALIDATION.
2. **Strategy B long has a small gross edge that costs erase.** Gross +0.08 to +0.15 R per trade;
   costs 0.21–0.24 R; net -0.07 to -0.15. The best trial (trail 3 ATR) is indistinguishable from zero
   (p 0.76). Its stops are 1.3–1.6 % of price, above the 0.91 % that one lot on a 10 USDT account can
   carry at 1 % risk: the account replay skips 30 % of its trades and still loses 8 %.
3. **Strategy B short loses before costs** in a period (2023–24) that trended up; mirroring a long
   setup did not produce a symmetric short.
4. **Regime router: nothing to route.** On TRAIN, 0 of 160 (trial, regime) pairs met the eligibility
   rule (n >= 30, mean > 0, p < 0.10). The router therefore outputs NO_TRADE for everything, which is
   the correct answer here, and by the registered rule it does not add value. Descriptively on
   VALIDATION, B long in TREND_UP had gross +0.17 R / net -0.06 R (n 449): the direction of the
   hypothesis, not enough to pay for execution.
5. **Loss taxonomy** (deterministic rules, `learning/trade_log.py`): of A's 12,562 VALIDATION losses,
   4,666 realised worse than -1.5 R on a stop. With a 0.65 % stop, fees plus trigger slippage alone
   turn a 1 R stop into about -1.35 R, so most of these are cost inflation on tight stops rather than
   gaps; the taxonomy threshold should be set relative to the cost model in Phase 2.

## Pre-registered consequences

- No trial enters `research/strategy_registry/shadow_trials.json`. The shadow runner stays idle.
- Per the registration's failure criterion, the next step is **not** a wider grid, another timeframe,
  or a filter on these two families using this data.
- The HOLDOUT stays sealed; nothing qualifies for confirmation.

## Caveats

- Binance 1m bars stand in for Bitget's (parity: close p99 |diff| 6.6 bps, return correlation 0.999 on
  2026-08..10). Bitget's book at 10 USDT size is deeper than needed; the slippage model (3/10 bps) is an
  assumption, not a measurement. Making it kinder cannot rescue A (gross <= 0) and would move B long to
  roughly break-even at best.
- 2023–24 is one regime pair (bear-to-bull recovery, then bull). A short-side result in that window is
  not a verdict on shorts in bear markets, but the registration did not allow a regime-conditional
  rescue and none is claimed.
