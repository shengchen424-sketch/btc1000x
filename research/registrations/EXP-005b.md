# EXP-005b — Feasibility variant of the two EXP-005 LEADs: stop 0.90 %

Registered 2026-10-14 after EXP-005's VALIDATION results were read. EXP-005's registration allowed
exactly this follow-up: "a LEAD would need a 0.9 % stop variant registered separately before any
shadow use". Nothing else changes.

## Trials: 2
ExpiryFade events {monthly, weekly}, hold_bars 16 (240 min), min_move 0.10 %, **stop 0.90 %** (was 1.00 %).

## Prediction
In EXP-005 the stop fired on 1 of 22 (monthly) and 6 of 85 (weekly) VALIDATION trades, so a 10 %
tighter stop should change net R by less than 0.05 R and leave the gate status unchanged (LEAD; a
CANDIDATE needs p < 0.025 for two trials and CI lower > 0, which the weekly trial may reach since its
stop_frac now passes the feasibility line).

## Consequence
A trial that is LEAD or CANDIDATE here enters `shadow_trials.json` for forward observation (DRY_RUN
intents only) and is the subject of a separately registered one-shot holdout confirmation
(EXP-005-HOLDOUT). A FAIL here closes the variant; EXP-005's 1 % trials stay LEADs for observation
only and cannot be used live at 10 USDT.
