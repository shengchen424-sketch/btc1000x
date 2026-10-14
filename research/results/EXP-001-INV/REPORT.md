# EXP-001-INV — Inverted signals: all 24 still lose; the loss is cost, not direction

Run 2026-10-14 on commit `20a8d21`, VALIDATION 2023–24. Prediction in the registration: all 24 net
negative. Outcome: all 24 net negative, 0 CANDIDATE, 0 LEAD.

| Family | Original gross R | Inverted gross R | Inverted net R |
|---|---|---|---|
| A long (8 trials) | -0.10 .. -0.01 | +0.03 .. +0.10 | **-0.37 .. -0.54** |
| A short (8) | -0.04 .. 0.00 | -0.03 .. +0.09 | **-0.47 .. -0.67** |
| B long (4) | +0.08 .. +0.15 | -0.08 .. -0.12 | **-0.26 .. -0.30** |
| B short (4) | -0.14 .. -0.09 | +0.02 .. +0.05 | **-0.18 .. -0.23** |

Reading: inverting flips the gross sign, as it must, and the best inverted gross is +0.10 R (A long
lb96, vol filter). The round trip still costs 0.37–0.64 R on A and 0.21–0.24 R on B, so every inverted
trial is net negative. Direction is not the problem; the signal carries at most ~0.1 R of information
either way, and execution at 10 USDT costs 2–6 times that.

Consequence: no inversion enters the registry. Confirms the Phase 1 conclusion that the cost share
per trade, set by capital and stop width, is the binding constraint.
