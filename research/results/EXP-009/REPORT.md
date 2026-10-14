# EXP-009 — Fear & Greed and exchange flows: 1 CANDIDATE on VALIDATION (FNG_L25), with a failed TRAIN

Run 2026-10-14 on commit `f1dad82`. Data: alternative.me Fear & Greed (daily), CoinMetrics exchange
flows (one-day lag).

| Rule | TRAIN CAGR / Sharpe / max DD / trades | VAL CAGR / Sharpe / max DD / trades | VAL p | time in mkt | gate |
|---|---|---|---|---|---|
| **FNG_L25** (F&G <= 25 long, exit >= 50) | **-13.5 % / 0.03 / 56 % / 39** | **+30.4 % / 1.91 / 6.7 % / 8** | 0.004 | 5.9 % | **CANDIDATE** |
| FNG_L (20 / 40) | -10.8 % / 0.04 / 52 % / 30 | +6.7 % / 0.78 / 1.6 % / 2 | 0.14 | 0.4 % | FAIL |
| FNG_S (>= 80 short, exit <= 60) | -20.5 % / -0.58 / 68 % | -7.3 % / -0.25 / 24 % | 0.64 | | FAIL |
| FNG_S75 | -32.2 % / -0.87 / 77 % | -15.1 % / -0.44 / 45 % | 0.73 | | FAIL |
| EXFLOW_S (net inflow z >= 2, short 5d) | +5.5 % / 0.34 | -8.8 % / -0.35 | 0.69 | | FAIL |
| EXFLOW_L (z <= -2, long 5d) | +13.9 % / 0.60 / 26 % / 66 | +9.4 % / 0.53 / 26 % / 44 | 0.23 | 15 % | FAIL |

## Reading
- FNG_L25 passes every VALIDATION gate (Sharpe 1.9, p 0.004, MAR 4.5 > buy-and-hold 3.9) on **eight
  trades**: 2023 had 3, 2024 had 5, each a dip bought during "extreme fear" in a market that then
  rose. On TRAIN the same rule lost 13.5 % a year with a 56 % drawdown: buying fear in 2022 meant
  buying every leg of the bear. The gate is VALIDATION-only by registration, so it is formally a
  CANDIDATE, and by the registered consequence it goes to a one-shot holdout look (EXP-009-HOLDOUT,
  registered with a 25 % prior).
- Shorting greed loses in both periods (greed persists in uptrends). Exchange-flow extremes are
  weakly positive on the long side in both periods (Sharpe 0.5–0.6) but never significant.
- Social-media history itself was not obtainable (X paid, Reddit / Trends / GDELT / Wikipedia
  refused this session's egress address); F&G is the only sentiment series with a 2018–2026 record.
