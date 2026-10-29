# EXP-016 — Polymarket crypto windows: resolution check and fair-value calibration

Run 2026-10-29 on commit 9f2a5d2, as registered (`research/registrations/EXP-016.md`). No Polymarket
price was compared with the model and no trading rule exists yet. Holdout 2025-01..2026-09 not loaded.

## 016a — the TWAP rule (5m / 15m / 4h)

1,584 settled BTC markets, 2026-10-20 .. 10-28, Binance spot 1 s as the stream proxy (`016a.md`):

| family | n | spot end vs start | TWAP-60s end vs start | window average |
|---|---|---|---|---|
| 15m | 768 | 94.4 % | **99.0 %** | 83.1 % |
| 4h | 48 | 95.8 % | 93.8 % | 87.5 % |
| 5m | 768 | 87.4 % | **99.2 %** | 87.4 % |

On the 49 markets where the two TWAP readings disagree by more than 2 bps, the end-point reading matched
49/49. **Adopted: Up iff the 60 s TWAP at the window end >= the 60 s TWAP at the window start.** The
remaining ~1 % (and 3 of 48 4h markets) are near-zero moves where Chainlink and Binance differ. The
practical consequence: the last minute of a 5m/15m window is already averaged in, so the outcome is
largely fixed about 30 s before the end.

## 016b — fair-value engine, VALIDATION 2023–24 (`016b.md`, parameters in `016b_params.json`)

| window | selected | VALIDATION n | Brier (M0) | gate |
|---|---|---|---|---|
| 15m | M2, k 0.945, t df 6 | 350,875 | 0.1367 (0.1376) | **CALIBRATED** |
| 1h | M2, k 0.928, t df 6 | 87,715 | 0.1432 (0.1440) | **CALIBRATED** |
| 4h | M2, k 0.941, t df 5 | 21,925 | 0.1456 (0.1462) | **CALIBRATED** |
| 1d noon-to-noon | M2, k 1.72, t df 2.5 | 3,654 | 0.1678 (0.1678) | **NOT_CALIBRATED** |

Reading the tables honestly:
- 15m and 1h errors are within about ±0.7 pp in every bin, top bins (p >= 0.95) within ±0.35 pp.
- 4h passes the registered gate but is over-confident by 1.0–1.5 pp at p 0.6–0.8 and under-confident
  by about 1 pp at p 0.9–0.98. The gate (CI touches ±1 pp) is lenient; for 4h a market gap smaller than
  about 1.5 pp cannot be told apart from model error.
- 1d fails: over-confident by 3–6 pp. The 60-minute EWMA volatility is too short-lived for a 24 h
  horizon (k = 1.72 and df at its lower bound are the symptom). Per the registration, daily
  markets get no reference price from this engine; a daily model needs a new registration and
  evaluation data other than 2023–24, which is now used.
- Limitation found after the run: the optimiser left the t df at its starting value 6.0 for 15m and 1h
  (flat likelihood in df); the result is what was registered, but "df 6" is not a fitted estimate.
- 15m and 4h use 1 m spot as the TWAP proxy; the Chainlink basis is not modelled.

## What this means for the plan

The engine can serve as the reference price for 15m, 1h and (with a ±1.5 pp tolerance) 4h windows.
The next experiment compares it with the collected books (market atlas, phase 2 of the plan), once the
collector has run for about 3 weeks. Not before: nothing in this report says the market is wrong.
