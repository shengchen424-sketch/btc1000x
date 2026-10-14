# EXP-002 — Funding-rate extreme reversal: 0 CANDIDATE, 0 LEAD (family closed)

Run 2026-10-14 on commit `ead9bfc`. VALIDATION 2023-01-01 .. 2024-12-31. Stop 3 %, window 270 settlements.

| Trial | TRAIN n | TRAIN mean R | VAL n | VAL mean R | VAL p | gate |
|---|---|---|---|---|---|---|
| LONG after bottom 10 %, hold 24h | 60 | +0.34 | 76 | -0.00 | 0.52 | FAIL |
| LONG after bottom 10 %, hold 72h | 46 | +0.45 | 48 | +0.24 | 0.10 | FAIL |
| LONG after bottom 3 %, hold 24h | 24 | +0.56 | 41 | -0.07 | 0.71 | FAIL |
| LONG after bottom 3 %, hold 72h | 19 | +0.82 | 32 | -0.02 | 0.54 | FAIL |
| SHORT after top 10 %, hold 24h | 75 | +0.16 | 101 | -0.21 | 1.00 | FAIL |
| SHORT after top 10 %, hold 72h | 58 | +0.03 | 63 | -0.38 | 1.00 | FAIL |
| SHORT after top 3 %, hold 24h | 32 | +0.19 | 44 | -0.09 | 0.77 | FAIL |
| SHORT after top 3 %, hold 72h | 25 | +0.30 | 29 | -0.33 | 0.95 | FAIL |

Reading: every trial is positive on TRAIN (2020–22, the period in which "funding extremes reverse"
became folklore) and none is on VALIDATION. Shorting crowded longs lost in 2023–24 because the market
kept rising through high funding; the long side after negative funding is a coin flip with one trial
at +0.24 R on 48 trades (p 0.10), which does not meet LEAD. The family is closed per the registration:
no further percentile, hold or stop variants on this data.

Costs were small here (about 0.08 R per trade plus funding), so this is a genuine absence of signal in
the validation period, not a cost artefact. The 10 USDT replay skipped every trade (3 % stop on one
lot exceeds 1 % risk), as predicted in the registration.
