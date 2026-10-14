# EXP-015 — Flow + residual-momentum blend: 0 of 2 adopted

Run 2026-10-14 on commit `d99efb3`. Paired B − A, 7 offsets pooled, independent window 2025–26.

| Book | 2025–26 Δ ann. | CI95 | p | 2023–24 Δ | B ann. / Sharpe / DD | A ann. / Sharpe / DD | gate |
|---|---|---|---|---|---|---|---|
| BLEND50 z(flow) + z(RM14) | +9.8 % | [-33.9, +48.8] | 0.33 | +0.7 % | 121 % / 2.22 / 33 % | 102 % / 2.12 / 15 % | DISCARD |
| BLEND25 z(flow) + 0.5 z(RM14) | +20.9 % | [-9.8, +49.4] | 0.078 | +2.7 % | 148 % / 2.60 / 31 % | 102 % / 2.12 / 15 % | DISCARD |

Reading: the flow-dominant blend raises the point estimate by 21 %/yr and Sharpe from 2.1 to 2.6 in
the independent window, with the same sign in 2023–24, but p 0.078 misses the registered 0.05 and the
CI spans zero; the maximum drawdown doubles (15 % -> 31 %), because the blend concentrates further
into the momentum tail. Under the owner's criterion (net return, with confidence) it is not adopted.
It is the best point estimate of any overlay tested (EXP-013: none above +6 %), and the only one
whose sign held in both windows. Recorded for a forward-shadow comparison alongside the baseline;
no further weights will be run.
