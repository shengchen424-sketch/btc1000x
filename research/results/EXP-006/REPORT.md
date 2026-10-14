# EXP-006 — Tail-shock fade with OI flush: 0 CANDIDATE, 0 LEAD (family closed)

Run 2026-10-14 on commit `7e5dd03` (a first run on `6989442` had the OI trials at n = 0 because the
metrics timestamps were stored in seconds; fixed and re-run, the no-OI trials are unchanged).
VALIDATION 2023–24, |r_1h| >= 3 sigma(720h), stop 1.5 %.

| Trial | TRAIN n / mean R | VAL n | gross R | cost R | **net R** | CI95 | win | years + | gate |
|---|---|---|---|---|---|---|---|---|---|
| no OI condition, hold 2h | 245 / -0.28 | 340 | -0.07 | 0.13 | **-0.20** | [-0.29, -0.12] | 41 % | 0/2 | FAIL |
| no OI condition, hold 4h | 233 / -0.24 | 328 | -0.11 | 0.13 | **-0.24** | [-0.34, -0.15] | 37 % | 0/2 | FAIL |
| OI drop >= 2 %, hold 2h | 65 / -0.27 | 104 | +0.01 | 0.13 | **-0.11** | [-0.26, +0.04] | 44 % | 0/2 | FAIL |
| OI drop >= 2 %, hold 4h | 64 / -0.18 | 103 | -0.06 | 0.13 | **-0.19** | [-0.35, -0.03] | 41 % | 0/2 | FAIL |

Reading: 3-sigma hourly moves in BTC continued rather than reverted in 2023–24 (gross negative
without the OI condition). Conditioning on an open-interest flush removes the continuation (gross
+0.01 R at 2 h) but there is no reversal left to pay 0.13 R of costs. This agrees with arXiv
2608.21888 (unconditional reversal dead) and extends it: the liquidation-flush tail is flat too, on
104 events. Family closed; no k / OI / hold / stop variants.
