# EXP-007 — FOMC drift: 0/3, closed

Run 2026-10-14 on commit `f1dad82`. 16 statements in TRAIN (2021–22), 16 in VALIDATION (2023–24).

| Rule | TRAIN CAGR / Sharpe | VAL CAGR / Sharpe | VAL p | gate |
|---|---|---|---|---|
| PRE_LONG (long the day before) | +1.3 % / 0.23 | -1.1 % / -0.06 | 0.53 | FAIL |
| DAY_SHORT (short the statement day) | -6.7 % / -0.71 | -3.9 % / -0.36 | 0.69 | FAIL |
| BOTH | -5.5 % / -0.44 | -5.0 % / -0.29 | 0.66 | FAIL |

The pre-2020 pattern (Pyo & Lee) is absent in 2021–24 in both directions. Underpowered as predicted
(16 events a split), but the point estimates are negative, not merely insignificant. Closed.
