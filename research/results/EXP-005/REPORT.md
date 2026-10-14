# EXP-005 — Options-expiry 08:00 UTC fade: 2 LEADs (240-min hold), 0 CANDIDATE

Run 2026-10-14 on commit `30d3533` (registration `863653d`). VALIDATION 2023–24. Stop 1 %, |move| >= 0.1 %.

| Trial | TRAIN n / mean R | VAL n | VAL mean R | median | CI95 | win | p | max share | years + | gate |
|---|---|---|---|---|---|---|---|---|---|---|
| monthly, hold 90 min | 30 / +0.72 | 22 | +0.15 | +0.12 | [-0.02, +0.35] | 59 % | 0.067 | 30 % | 2/2 | FAIL |
| monthly, hold 240 min | 30 / +0.84 | 22 | **+0.28** | +0.27 | [+0.03, +0.54] | 77 % | 0.024 | 20 % | 2/2 | **LEAD** |
| weekly, hold 90 min | 128 / +0.04 | 85 | +0.04 | -0.02 | [-0.07, +0.16] | 46 % | 0.24 | 16 % | 2/2 | FAIL |
| weekly, hold 240 min | 128 / +0.03 | 85 | **+0.23** | +0.14 | [+0.05, +0.42] | 64 % | 0.011 | 15 % | 2/2 | **LEAD** |

Cost per trade 0.18 R (1 % stop). Exits: almost all by time (stop hit on 1/22 and 6/85).
10 USDT one-lot replay on VALIDATION: monthly-240 +2.4 % (20 trades taken, 2 skipped), weekly-240 +9.6 %
(80 taken, 5 skipped, max DD 2.6 %). Both have stop_frac 1.0 % > 0.91 %, hence not CANDIDATE by the
registered feasibility clause; the weekly-240 trial would otherwise have met every CANDIDATE condition
(p 0.011 < 0.0125, CI lower > 0, share 15 %).

## Reading

- The reversal after the 08:00 UTC expiry is present in VALIDATION on both event sets, and only at the
  longer 240-minute horizon; the 90-minute horizon from the paper's description is too short here.
- TRAIN is not supportive for the weekly set (2020 strongly negative, 2021 strongly positive, 2022
  negative), which means the effect is not stable year to year; the monthly set is positive in TRAIN
  overall but driven by 2021 (+2.2 R per trade), the paper's period.
- Both LEADs rest on 2023–24. The sealed holdout (2025-01 .. 2026-09) is the natural one-shot
  confirmation; the Wintermute remark that expiry pinning "no longer binds" (LIT-001) is exactly the
  2025–26 question.

## Consequence (per registration)

Two LEADs, observation only. EXP-005b (stop 0.90 %) is registered as the allowed feasibility variant;
whichever of its trials passes enters the shadow registry and goes to a registered holdout look.
