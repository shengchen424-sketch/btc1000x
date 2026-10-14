# EXP-009-HOLDOUT — One-shot confirmation of FNG_L25 (Fear & Greed <= 25 -> long) on the sealed holdout

Registered 2026-10-14 after EXP-009's VALIDATION results were read and BEFORE the holdout is opened
for the sentiment family. Only unseal for this family.

## Trial
FNG_L25 exactly as registered in EXP-009: long when the Fear & Greed value stamped for day D is <= 25,
decided at D's close, executed at the next open; exit when F&G >= 50 or after 30 days. 1.0x notional,
fees 9 bps per change, realised funding. Secondary (reported only): FNG_L (20/40), EXFLOW_L.

## Holdout
2025-01-01 .. 2026-09-30 daily bars; F&G snapshot `evidence/alt/fng_2018-02_2026-10-14.parquet`.

## Prediction, written before the look
VALIDATION: CAGR +30 %, Sharpe 1.9, p 0.004, but on 8 trades covering 6 % of the days, in a bull
market where every fear episode recovered. TRAIN (2020–22): CAGR -13.5 %, max drawdown 56 % on 39
trades: buying fear during the 2022 bear lost repeatedly. The holdout is a drawdown window. Prior:
25 % that FNG_L25 is CONFIRMED; 50 % that its holdout CAGR is negative.

## Gates (daily net returns on the holdout)
CONFIRMED: CAGR > 0, Sharpe >= 0.7, one-sided p < 0.05, max drawdown < buy-and-hold's, MAR > buy-and-hold's.
WEAK: CAGR > 0 and Sharpe >= 0.3, not CONFIRMED. REJECTED: otherwise.

## Consequence
CONFIRMED -> CHAMPION in the shadow registry (DRY_RUN) with a forward checkpoint (>= 6 completed
trades or 180 days). WEAK -> LEAD in shadow (forward observation, owner's tune-then-forward decision).
REJECTED -> sentiment family closed.
