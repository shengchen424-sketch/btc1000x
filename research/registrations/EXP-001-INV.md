# EXP-001-INV — Diagnostic: exact inversion of the 24 EXP-001 trials

Registered 2026-10-14 after EXP-001's VALIDATION results were read (owner's request: "if all are
negative, run the signals inverted"). This is a DIAGNOSTIC on already-seen data, not a discovery
experiment: whatever it shows cannot be promoted; it can only tell us where the loss came from.

## Rule

Same signal bars as EXP-001; direction flipped; stop and take-profit mirrored around the entry
reference; same max_hold and trailing multiple (`strategies/inverted.py`). Costs, fills and funding as
in EXP-001. VALIDATION 2023-01-01 .. 2024-12-31. No new parameters.

## Prediction, written before the run

Net R of an inverted trial is approximately -(gross R) - cost R, because fees and slippage are paid in
both directions. From EXP-001: A gross is -0.10 .. 0.00 and cost 0.46-0.64, so inverted A should be
about -0.36 .. -0.64 net; B long gross +0.08 .. +0.15, cost 0.21-0.24, so inverted B long about
-0.30 .. -0.40; B short gross -0.09 .. -0.14, so inverted B short about -0.08 .. -0.15. Expected result:
**all 24 inverted trials net negative**; none reaches LEAD. (Mirroring is not exact because stops,
targets and trails are path-dependent, so the numbers will differ from this arithmetic.)

## Gates

Same as EXP-001 for reporting only (CANDIDATE / LEAD / FAIL). A LEAD here would NOT enter the shadow
registry; it would require a fresh registration and a confirmation on data not used so far.
