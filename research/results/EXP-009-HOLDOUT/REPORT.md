# EXP-009-HOLDOUT — FNG_L25 REJECTED on 2025-01 .. 2026-09; sentiment family closed

One-shot unseal 2026-10-14 on commit `64acac7` (third entry in `research/results/unseal_log.jsonl`).

| Rule | CAGR | Sharpe | max DD | MAR | p | in market | trades | verdict |
|---|---|---|---|---|---|---|---|---|
| **FNG_L25 (primary)** | -13.3 % | -0.23 | 40 % | -0.34 | 0.62 | 49 % | 24 | **REJECTED** |
| FNG_L (20/40) | -11.6 % | -0.24 | 38 % | -0.31 | 0.62 | 34 % | 18 | secondary |
| EXFLOW_L | +3.3 % | 0.33 | 19 % | 0.18 | 0.33 | 9 % | 24 | secondary |
| FNG_S75 (short greed) | +15.6 % | 1.33 | 6 % | 2.57 | 0.039 | 12 % | 11 | secondary; failed TRAIN and VAL |
| buy and hold | -10.1 % | -0.03 | 54 % | -0.19 | | | | baseline |

Exactly the TRAIN pattern repeated: in a falling market "extreme fear" arrives on every leg down and
the rule buys each one; 24 trades, 49 % of the time in the market, -13 % a year. The VALIDATION
result (8 trades in a bull market) was the regime, not the signal. The prior in the registration
(25 % confirmed / 50 % negative CAGR) was right.

FNG_S75 (short when greed >= 75) was the mirror winner in this window after losing in both earlier
periods: the same regime dependence from the other side. Not promotable; not registered as primary.

Consequence: sentiment family closed. Three holdout looks have now been spent (expiry fade, daily
trend, sentiment); each rejected a rule that passed VALIDATION. The common cause is the same each
time: 2023–24 was one regime and 2025–26 another, and a rule that only works in one of them is not
an edge.
