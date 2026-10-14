# EXP-004-HOLDOUT — One-shot confirmation of the EXP-004 long daily-trend LEADs on the sealed holdout

Registered 2026-10-14 after EXP-004's VALIDATION results were read and BEFORE the holdout is opened
for this family. This is the only unseal for the daily-trend family. Rules are frozen as in
`src/b1k/strategies/daily_trend.py` at this commit.

## Primary and secondary
Primary: T7_L (SMA200 filter + 55-day breakout, 20-day-low / SMA200 exit). Secondary (reported, no
promotion on their own): DON_L, SMA200_L. Baseline: buy-and-hold perpetual with funding paid.

## Holdout
2025-01-01 .. 2026-09-30 daily bars (638 days) built from the sealed 1m data; realised funding.
Simulation needs a 200-day warm-up: bars from 2024-04 are used for indicator state only; returns are
scored from 2025-01-01. Position on 2025-01-01 is whatever the rule holds given history up to
2024-12-31 (no look-ahead; the rule is deterministic from past closes).

## Prediction, written before the look
The owner's earlier project found T7 on SPOT passes 2018–19 and the perp version fails DEV on
funding. Disclosure: the shadow runner's dry run on 2026-10-14 fetched Bitget daily candles from
2025-09 to 2026-10-13 to compute today's target positions (all three rules LONG at the 2026-10-13
close of 83,138); no return statistic was computed from them. Prior: 45 % that T7_L's holdout Sharpe
is >= 0.7 with p < 0.10; 60 % that its max drawdown is smaller than buy-and-hold's.

## Gates (daily net returns on the holdout)
CONFIRMED: CAGR > 0, Sharpe >= 0.7, one-sided p < 0.05, max drawdown < buy-and-hold's max drawdown,
MAR > buy-and-hold's MAR.
WEAK: CAGR > 0 and Sharpe >= 0.3, not CONFIRMED.
REJECTED: otherwise.

## Consequence
CONFIRMED (primary) -> T7_L becomes CHAMPION in the shadow registry (DRY_RUN); a forward checkpoint
(>= 180 forward days, >= 4 completed trades) is registered before any live discussion; the owner must
separately decide the risk unit, because the rule has no 1 % stop. WEAK -> stays LEAD in shadow.
REJECTED -> the family is closed; daily rules leave the shadow registry.
