# EXP-005-HOLDOUT — Expiry fade REJECTED on 2025-01 .. 2026-09; family closed

One-shot unseal 2026-10-14 12:57 UTC on commit `6989442` (logged in `research/results/unseal_log.jsonl`).
Rules exactly as EXP-005b: hold 240 min, |move| >= 0.1 %, stop 0.90 %.

| Trial | n | mean R | median | CI95 | win | p | 2025H1 | 2025H2 | 2026 Jan–Sep | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| monthly | 17 | -0.07 | -0.12 | [-0.43, +0.30] | 35 % | 0.64 | | | | **REJECTED** |
| weekly | 66 | -0.08 | -0.15 | [-0.29, +0.15] | 39 % | 0.75 | -0.17 (27) | -0.02 (22) | -0.03 (34) | **REJECTED** |

(Half-year blocks are pooled over both trials: 83 trades, every block negative.)

## Reading
The 2023–24 reversal after the 08:00 UTC expiry did not exist in 2025–26: mean net R is slightly
negative, the median is -0.15 R, and the stop fired on 14 of 66 weekly trades against 6 of 85 in
VALIDATION. This matches the practitioner claim recorded in LIT-001 that expiry pinning stopped
binding in 2025–26 and the paper's own sample ending in 2023. The prior written in the registration
(50 % / 35 %) was too optimistic.

## Consequence (per registration)
Both trials are removed from the shadow registry. The expiry-fade family is closed; no variant
(thresholds, holds, stops, event subsets, OI conditioning) will be run on this data under any new id,
because the holdout has now been seen for this mechanism.

What this look cost: the 2025-01 .. 2026-09 window is no longer unseen for the expiry mechanism. It
remains sealed for every other family (the loader only exposes it under an explicit experiment id).
