# ST-AUDIT-002 — Bitget-executable replay of the flow book and its two candidates

Registered 2026-10-15 before the replay was run. Reviewer's priority: before any portfolio question,
establish whether the research returns can land in the owner's Bitget account at all.

## Corrections carried from the review of EXP-014/015 (recorded here so the record is right)
- RM14 is reclassified from "DISCARD" to **"historical evidence, diversification threshold not
  passed"**: 2023–24 p 0.0073 (Bonferroni-3 0.022), 2025–26 p 0.0099 (0.030), full p 0.0004;
  corr with the flow book 0.64 (2023–24) / 0.47 (2025–26). Standalone evidence is real; it is not
  independent; it is not shown to improve the portfolio (50/50 mix raises Sharpe 2.12 -> 2.25, DD 15 -> 21 %);
  not eligible for live.
- The claim "one-sided taker buying implies positive 14-day residual return by construction" is
  withdrawn; the two variables are different. The measured overlap is the correlation above.
- 141/180 is by SYMBOL count (78 %); by position count it is 89 %; the unlisted-today symbols carry
  15.2 % of net PnL and 13.1 % of gross profits. Those figures use today's listing and are
  superseded by this audit, which uses historical listing dates.
- "Capacity knee 200–300 USDT" meant the MINIMUM EXECUTABLE CAPITAL (lot rounding, 5 USDT minimum,
  the drawdown ladder), not a capacity ceiling. Fees per unit of risk do not fall with capital;
  what changes is the fraction of the target book that can be placed. This replay produces the
  equity -> placeable fraction -> cost -> return table that the claim needs.
- Because 2025–26 was examined when RM14 and BLEND25 were selected, it is DEVELOPMENT data for
  them from now on; only forward data is independent for those two.

## Replay rules (same for all three books)
Data: rebuilt Binance daily panel and funding (ST-AUDIT-001). Eligibility: a coin can be held only
if Bitget's first daily candle (`evidence/exchange/bitget_listing_dates.json`, from
history-candles) is on or before the entry date. Signal: computed on the full Binance universe (the
live code does the same, then skips unplaceable coins). Selection: first 5 placeable within the
top-10 ranks / bottom-10 ranks. Sizing: target notional = equity x gross / 10; quantity rounded DOWN
to the contract step (today's `sizeMultiplier`/`minTradeNum`, the only ones available); skip if
notional < 5 USDT or the rounded size is more than 50 % below target (live rule). Costs: taker 6 bps
+ 3 bps slippage per unit traded (live measured slippage was -2 bps median on majors; 3 bps is the
registered assumption); realised funding; 2x trim; no ladder, no halt (live configuration); equity
compounds. Capital 105, 200, 300, 500, 1,000 USDT; 7 offsets; 2023-01 .. 2026-09.

## Outputs per book x capital
Net annual return, Sharpe, max DD; average placeable fraction of target notional; average positions
held; skips by reason (unlisted / below minimum / rounding); cost %/yr; funding %/yr; and the ratio
executable-return / research-return. Plus, for the 85 top-1 % research positions: listed on Bitget
at entry (yes/no) and placeable at 105 USDT (yes/no).

## What this cannot show
Fill quality in small coins at the daily close (needs the live fills), and Bitget's own price series
(Binance proxy; parity 3–6 bps on majors, unknown on small coins).

## Amendment v2 (2026-10-15, after ST-AUDIT-003, before the v2 run)
ST-AUDIT-003 (VPS, read-only) showed the live executor differs from the rules registered above in three
places: untradeable coins are removed BEFORE ranking (then first 5 placeable of the remaining top-10);
quantities are rounded to the NEAREST lot with a ±50 % tolerance (not floored); a same-direction
position is kept unless the size gap is >= 5.5 USDT. v2 copies these three rules; everything else is
unchanged. Outputs to `research/results/ST-AUDIT-002v2/`. Reporting label fixed in advance: "historical
scenario under today's contract rules and Binance funding", never "verified Bitget return"; CONS is a
sensitivity case, not a lower bound. Still not modelled: next-day 00:35 execution, Bitget funding,
non-ASCII contracts (absent from the panel).

## Addendum (2026-10-16): reproducibility check and post-rounding risk
Owner's four conditions recorded: (1) nearest-lot rounding matching live does not make the risk acceptable
by itself; per-symbol, gross, net exposure and margin headroom after rounding are reported (REPORT §6) and
"cash 0" is defined as a notional-allocation measure; (2) the ST-AUDIT-003 reconciliation covers money
and fills, not selection (rankings were not logged); (3) slippage claims are limited to fills with a
same-time quote (R3) and no yearly saving is inferred from 9 vs 6 bps; (4) v2 is reproduced from a clean
checkout of `66c9ad1` on the fixed data snapshot (REPRO.md): 33/33 output files identical. Labelled a
reproducibility check, not fresh validation. `st_audit2_paths.py` is a companion that emits daily equity
and holdings for future comparison; it changes no result.
