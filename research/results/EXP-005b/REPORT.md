# EXP-005b — 0.90 % stop variant: both trials LEAD (weekly one misses CANDIDATE only on the stop line)

Run 2026-10-14 on commit `3c28f6b`. VALIDATION 2023–24, stop 0.90 %, hold 240 min, |move| >= 0.1 %.

| Trial | n | mean R | median | CI95 | win | p | max share | by year | 10 USDT replay | gate |
|---|---|---|---|---|---|---|---|---|---|---|
| monthly | 22 | +0.32 | +0.29 | [+0.04, +0.59] | 77 % | 0.021 | 20 % | 2023 +0.12, 2024 +0.51 | +5.4 % (22 taken, 0 skipped) | LEAD |
| weekly | 85 | +0.26 | +0.15 | [+0.06, +0.47] | 64 % | 0.0084 | 15 % | 2023 +0.33, 2024 +0.20 | +18.7 %, max DD 2.4 % (85 taken, 0 skipped) | LEAD |

Prediction held: the tighter stop changed net R by +0.03 R. The weekly trial meets every CANDIDATE
condition except that its realised mean stop fraction is 0.92 % (stop set from the signal close,
filled at the next open), a hair over the registered 0.91 % line; by the registration it is a LEAD.
All 85 + 22 trades are now feasible on the 10 USDT account at 1 % risk (0 skipped).

Cost per trade is 0.20 R, so the weekly trial's gross edge is ~0.46 R per event: a 240-minute reversal
of about 0.4 % of price after the 08:00 UTC expiry, on 85 Fridays. Both trials enter the shadow
registry as LEADs and go to the registered one-shot holdout look (EXP-005-HOLDOUT).
