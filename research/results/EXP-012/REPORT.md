# EXP-012 — Order-flow shocks (registered thresholds): underpowered, 0/8

Run 2026-10-14 on commit `6a9db4e`. Registered event: |OFI5| >= trailing 99th percentile AND 5-minute
trade count >= 3x its 7-day median.

Events: 66 in 2021-07 .. 2024-12 (TRAIN 59, VALIDATION 7); with the OI-drop condition, 1. Every trial
FAILS the n >= 60 gate by construction; the 7 validation trades (REV 15 min: gross +0.25 R, net -0.04 R)
carry no information.

## Signal-count scan (no outcomes read)
| |OFI5| quantile | intensity ratio | events 2021-07..2024-12 | of which 2023–24 |
|---|---|---|---|---|
| 0.99 | >= 3.0 (registered) | 66 | 7 |
| 0.99 | >= 2.0 | 149 | 24 |
| 0.99 | >= 1.5 | 348 | 79 |
| 0.99 | >= 1.0 | 1,020 | 340 |
| 0.995 | >= 1.5 | 142 | 22 |

Reading: extreme one-sided taker flow at 5-minute resolution is mostly a quiet-market phenomenon
(few trades, all one side), not a burst. Requiring a burst removes almost everything. Events also
fall by half from 2021–22 to 2023–24 as BTC liquidity deepened.

Consequence: one pre-declared relaxation (intensity >= 1.0) is registered as EXP-012b and run once.
