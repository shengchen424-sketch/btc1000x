# EXP-012b — Order-flow shocks: one pre-declared relaxation of the event definition

Registered 2026-10-14 after EXP-012 ran. EXP-012's registered thresholds (|OFI5| >= 99th percentile
AND trade-count ratio >= 3) produced 66 events in 3.5 years and 7 in VALIDATION: the gate (n >= 60)
could not be reached and the outcome read (7 trades) is uninformative. A signal-count scan WITHOUT
outcomes (research/results/EXP-012/REPORT.md) shows the intensity filter is what removes events:
extreme one-sided flow happens mostly in quiet minutes. This registration relaxes exactly one thing,
once: intensity ratio >= 1.0 (the 5-minute trade count must at least match its 7-day median), which
gives ~1,020 events (340 in VALIDATION). Nothing else changes. This is not a parameter sweep: no
other threshold will be run under the order-flow family.

## Trials: 8 (as EXP-012)
mode {CONT, REV} x hold {15 min, 60 min} x OI {none, drop 0.5 %}. Stop 0.6 %, time exit. Bonferroni 8.

## Gates
As EXP-012 (n >= 60, mean net R > 0, CI95 lower > 0, p < 0.00625, both years positive, max trade
<= 20 %). LEAD: n >= 60, mean > 0, p < 0.05, both years positive.

## Prediction
Prior that any trial reaches LEAD: 15 % (unchanged). Failure closes the family on public data.
