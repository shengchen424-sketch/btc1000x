# EXP-012b — Order-flow shocks (intensity >= 1.0): 0/8; family closed on public data

Run 2026-10-14 on commit `acab41b`. Events: 1,020 (TRAIN 2021-07..2022 ~600, VALIDATION 2023–24 ~334).

| Trial | VAL n | gross R | net R | p | gate |
|---|---|---|---|---|---|
| CONT (with the flow), 15 min | 334 | -0.01 | -0.30 | 1.00 | FAIL |
| CONT, 60 min | 322 | -0.02 | -0.31 | 1.00 | FAIL |
| REV (against the flow), 15 min | 334 | +0.02 | -0.27 | 1.00 | FAIL |
| REV, 60 min | 321 | +0.02 | -0.28 | 1.00 | FAIL |
| any trial with OI drop >= 0.5 % | 3 | | | | FAIL (no events) |

Reading: after a 5-minute one-sided taker-flow extreme, the next 15–60 minutes carry no direction at
all — gross R is within ±0.02 R in both directions, on 320–334 events, and TRAIN agrees (-0.27 to
-0.33 net). The round-trip cost at a 0.6 % stop (~0.28 R) is the whole result. An open-interest
flush coinciding with the flow extreme almost never happens at 5-minute resolution (3 events in two
years), so the "liquidation" version of this signal cannot be tested on public data.

This matches the published microstructure evidence (LIT-001: sub-hour effects < 2 bps). The family is
closed. The only remaining form of priority 1 is forward collection of the Binance `forceOrder`
liquidation stream and the order book on the VPS, which produces testable data in months, not now.
