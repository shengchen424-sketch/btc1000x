# EXP-005-HOLDOUT — One-shot confirmation of the two EXP-005b LEADs on the sealed holdout

Registered 2026-10-14 after EXP-005b's VALIDATION results were read and BEFORE the holdout was
opened. This is the first and only unseal for the expiry-fade family; `data.store.load_1m` logs it in
`research/results/unseal_log.jsonl`. No parameter may change after this look, whatever it shows.

## Trials: exactly the two EXP-005b LEADs
ExpiryFade, hold 16 x 15m (240 min), |move| >= 0.10 %, stop 0.90 %, events {monthly, weekly}.

## Holdout
2025-01-01 .. 2026-09-30 (21 months; ~21 monthly and ~90 weekly expiry events). Costs, fills,
funding as registered. Independent of TRAIN and VALIDATION; data was downloaded before EXP-001 and
never loaded by any experiment (enforced by the loader).

## Prediction, written before the look
LIT-001 reports a 2026 practitioner claim that expiry pinning no longer binds, and EXP-005's TRAIN
years were unstable. Prior: 50 % that the weekly trial's holdout mean net R is > 0 with p < 0.05;
35 % for the monthly trial (n ~ 21).

## Gates
CONFIRMED: mean net R > 0, one-sided p < 0.05, bootstrap CI95 lower > 0, at least 2 of the 3 half-year
blocks (2025H1, 2025H2, 2026 Jan–Sep) positive, max trade <= 25 % of gross profits.
WEAK: mean net R > 0 and p < 0.20, not CONFIRMED.
REJECTED: otherwise.

## Consequence
CONFIRMED -> the trial becomes CHAMPION in the shadow registry: still DRY_RUN; a frozen forward
checkpoint is registered next (>= 30 forward events for weekly, >= 12 for monthly) before any
live-authorisation discussion. WEAK -> stays LEAD in shadow, no promotion. REJECTED -> family closed;
removed from the shadow registry.
