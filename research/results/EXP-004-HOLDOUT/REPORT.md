# EXP-004-HOLDOUT — Daily-trend long rules REJECTED on 2025-01 .. 2026-09; family closed

One-shot unseal 2026-10-14 13:00 UTC on commit `10c5b39` (logged in `research/results/unseal_log.jsonl`).
Holdout: 638 daily bars, realised funding, fees 9 bps per position change.

| Rule | CAGR | Sharpe | max DD | MAR | p (daily) | in market | trades | verdict |
|---|---|---|---|---|---|---|---|---|
| **T7_L (primary)** | -10.5 % | -0.58 | 27 % | -0.39 | 0.78 | 20 % | 13 | **REJECTED** |
| DON_L | -15.3 % | -0.79 | 35 % | -0.44 | 0.85 | 28 % | 17 | REJECTED |
| SMA200_L | -2.6 % | +0.05 | 32 % | -0.08 | 0.48 | 49 % | 19 | REJECTED |
| Buy and hold perp | -10.1 % | -0.03 | 54 % | -0.19 | | 100 % | | baseline |
| (secondary, not registered for promotion) DON_S | +14.9 % | +0.60 | 19 % | +0.79 | 0.21 | 33 % | 8 | n/a |
| (secondary) T7_S / SMA200_S | +0.5 % / -3.1 % | +0.15 / +0.07 | 23 % / 31 % | | 0.42 / 0.46 | | | n/a |

## Reading
2025–26 was a drawdown window for BTC (buy-and-hold -10 % a year with a 54 % maximum drawdown). The
long trend rules did what a trend filter does — they cut the drawdown roughly in half — but they
still lost money: 13–19 round trips of whipsaw at 9 bps each plus funding, with no sustained uptrend
to ride. The prior in the registration (45 % for Sharpe >= 0.7) was wrong; the 60 % prior that the
drawdown would be smaller than buy-and-hold's was right, and that is the only thing this family does.

DON_S (short Donchian) was positive in this window. It failed on TRAIN and VALIDATION and was not
registered as a primary; by the rules it cannot be promoted, and a short that works only in the one
window where the market fell is not evidence of an edge.

## Consequence (per registration)
All three daily rules leave the shadow registry. The daily-trend family is closed on this history.
The holdout has now been seen for two families (expiry fade, daily trend) and stays sealed for all
others.
