# EXP-010 — Maker-entry rescue of Strategy B long: fails; closed

Run 2026-10-14 on commit `64acac7`. VALIDATION 2023–24. Passive limit at the signal close, 60-minute
window, fill only if a later 1m low trades strictly below the limit; maker fee 2 bps, no entry slippage.

| Trial (B long) | signals | fill rate | taker net R (same signals) | **maker net R** | cost R | p | unfilled signals' taker R | gate |
|---|---|---|---|---|---|---|---|---|
| depth 0.5, trail 2 | 342 | 98 % | -0.15 | **-0.10** | 0.18 | 0.92 | +0.41 (6) | FAIL |
| depth 0.5, trail 3 | 258 | 99 % | -0.10 | **-0.04** | 0.16 | 0.66 | +1.41 (3) | FAIL |
| depth 1.0, trail 2 | 366 | 98 % | -0.16 | **-0.10** | 0.18 | 0.93 | +0.45 (6) | FAIL |
| depth 1.0, trail 3 | 274 | 99 % | -0.12 | **-0.07** | 0.16 | 0.77 | +1.20 (2) | FAIL |

Reading: the limit almost always fills (price revisits the signal close within an hour 98 % of the
time), so the maker entry saves the 4 bps fee difference and the 3 bps entry slippage: about 0.05 R
per trade. The remaining cost (0.16–0.18 R) is the exit side — stops and trails fire into a moving
market and are modelled at taker fee plus 10 bps. The signal's gross edge (+0.08 .. +0.15 R) does not
cover that either. The few unfilled signals were the big winners (price never came back), the usual
adverse selection of passive entries. The rescue fails; Strategy B stays closed.

Useful by-product: a measured fill-rate assumption (98 % within 60 minutes at the 1h close) for any
future 1h-clock strategy's cost model.
