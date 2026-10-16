# ST-AUDIT-002 v2 — Replay with the live executor's rules: +32 % to +42 %/yr median historical scenario, unchanged above 200 USDT, better behaved at 105 USDT

Run 2026-10-15 (13:34–13:5x UTC) from the working tree on top of commit `46438bd` with the v2 patch to
`research/experiments/st_audit2_executable.py` uncommitted at run time (not through the experiment runner);
the committed script is identical to the one run except for the removal of one unused assignment.
Supersedes `research/results/ST-AUDIT-002/REPORT.md` on rule fidelity; v1 remains the record of the
floor-rounding variant.

**Label (owner / ST-AUDIT-003 §4): this is a HISTORICAL SCENARIO of the flow book under today's Bitget
contract rules (step, minimum, listing evidence) and Binance realised funding. It is not a verified
Bitget return, not a reproduction of the live account, and the CONS scenario is a sensitivity case,
not a lower bound.**

## 0. What changed from v1 (rules copied from `rg/book/core.py`, `rg/book/paper.py` after ST-AUDIT-003)
| Rule | v1 replay | v2 replay (= live) | ST-AUDIT-003 evidence |
|---|---|---|---|
| Untradeable coins | ranked with everyone, skipped when reached (occupy a top-10 slot) | removed BEFORE ranking; first 5 placeable of the remaining top-10 / bottom-10 | R1 LINK vs ADA, R2 SOL vs BNB: one coin differed per rebalance |
| Rounding | floor to lot; skip if < 50 % of target | nearest lot (`Lots.qty`); skip if more than 50 % off target either side (`MAX_SIZE_ERROR`) | live notionals 7.1–12.7 USDT around a 10.5 target |
| Existing position, same side | always resized to target | kept unless the size gap >= 5.5 USDT (`BAND_USDT`) | live R2/R3 targets |
| Non-ASCII contracts (龙虾USDT) | not in panel | not in panel (Binance fetch filter drops non-ASCII tickers) | live cannot sign orders for them; they were rank 1–7 in three live rebalances |
| Unchanged | eligibility from `bitget_listing_dates.json` (OPT = first quote, CONS = +30 d); 9 bps per unit traded; Binance funding; 2x trim; no ladder; no halt; equity compounds; 7 offsets reported separately; 2023-01..2026-09 | | |

Still NOT modelled (live facts from ST-AUDIT-003): execution at 00:35 UTC the next day instead of the
signal close (R1 ran 22.5 h late; fills vs Binance close cost −0.70 USDT over 27 fills, mostly R1);
Bitget funding instead of Binance (+0.042 vs +0.013 USDT over 13 days, same positions); actual fee
6.0 bps; slippage is measured against a same-time quote only for R3 (13 fills, median 0.0 bps, worst
+11 bps), while R1/R2 are measured against the 1-minute open (approximation) and the −0.70 USDT
fill-vs-Binance-close figure is execution delay plus price change, not slippage; the replay therefore
keeps 9 bps (6 fee + 3 slippage) and no yearly "saving" is claimed from the 3 bps difference until
slippage is measured on more fills with decision-time quotes; the 2x trim reference is reset at every rebalance for kept positions
(approximation; the live reference was not audited); universe membership can differ by one coin
when a non-ASCII contract is in the live top-30 (live ranks 29, this panel ranks a different 30th).

## 1. Table A — the 85 top-1 % research positions at 105 USDT, OPT dates (`top85_positions_executability.csv`)
| Question | v2 | v1 |
|---|---|---|
| Tradable on Bitget at entry | 61 / 85 (72 %); 24 not: 11 ABSENT (REEF, BLZ, BNX), 13 listed later (TRB x7 2023, AKE x6 Jul–Aug 2026) | same |
| Placeable at a 10.5 USDT slot | 61 / 85 (all tradable ones); notional 8.4–12.1 USDT (nearest lot) | 61 / 85; notional 5.8–10.5 USDT (floor) |
| Top-85 research profit retained (notional-weighted) | **71.6 %** | 68 % |
The only difference is that the same 61 positions are rounded to the nearest lot instead of down; the
lost 28 % is still TRB (+317 %, +204 % in Sep 2023), REEF, BLZ, BNX and the mid-2026 AKE run.

## 2. Table B — five capital levels x three books x two scenarios (`executable_table_OPT.csv`, `_CONS.csv`, per-offset `offsets_*.csv`)
Median / worst / best of the 7 rebalance offsets (each offset is one path; not pooled). Ann. = net
annualised return; DD = maximum drawdown; skips per path over 3.75 years.

**Flow book A (research +79 %/yr, Sharpe 2.0, DD 17 %)**
| Scen. | Capital | Ann. med / worst / best | Sharpe med / worst | DD med / worst | Min equity | Cost %/yr | Funding %/yr | Long / short / net exp. | Max net exp. | Cash | Skips unlisted* / min-order / rounding |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OPT | 105 | **+42 / +28 / +78 %** | 1.20 / 0.95 | 22 / 28 % | 89.7 | 10.0 | 24.9 | 0.51 / 0.49 / +0.02 | 0.16 | 0 % | 767 / 27 / 72 |
| OPT | 200 | +42 / +33 / +78 % | 1.21 / 1.09 | 23 / 27 % | 179 | 10.3 | 27.1 | 0.50 / 0.50 / 0.00 | 0.10 | 0 % | 767 / 0 / 1 |
| OPT | 300 | +41 / +31 / +78 % | 1.20 / 1.04 | 22 / 26 % | 260 | 10.2 | 25.7 | 0.50 / 0.50 / 0.00 | 0.09 | 0 % | 767 / 0 / 0 |
| OPT | 500 | +41 / +32 / +78 % | 1.19 / 1.05 | 23 / 26 % | 433 | 10.3 | 26.5 | 0.50 / 0.50 / 0.00 | 0.06 | 0 % | 767 / 0 / 0 |
| OPT | 1,000 | +40 / +31 / +78 % | 1.18 / 1.03 | 23 / 26 % | 835 | 10.3 | 26.0 | 0.50 / 0.50 / 0.00 | 0.03 | 0 % | 767 / 0 / 0 |
| CONS | 105 | **+32 / +25 / +65 %** | 1.03 / 0.88 | 22 / 26 % | 85.5 | 9.1 | 20.0 | 0.51 / 0.50 / +0.02 | 0.14 | 0 % | 787 / 37 / 75 |
| CONS | 200 | +33 / +31 / +66 % | 1.10 / 1.00 | 22 / 25 % | 173 | 9.2 | 19.4 | 0.50 / 0.50 / 0.00 | 0.12 | 0 % | 787 / 0 / 3 |
| CONS | 300 | +32 / +27 / +70 % | 1.01 / 0.93 | 23 / 25 % | 249 | 8.9 | 19.7 | 0.50 / 0.50 / 0.00 | 0.10 | 0 % | 787 / 0 / 0 |
| CONS | 500 | +32 / +27 / +69 % | 1.02 / 0.92 | 23 / 25 % | 411 | 9.1 | 20.5 | 0.50 / 0.50 / 0.00 | 0.06 | 0 % | 787 / 0 / 0 |
| CONS | 1,000 | +33 / +27 / +68 % | 1.03 / 0.92 | 22 / 26 % | 805 | 9.3 | 20.9 | 0.50 / 0.50 / 0.00 | 0.04 | 0 % | 787 / 0 / 0 |

\* "unlisted" is now counted BEFORE ranking (every ineligible coin of the 30-universe at every
rebalance), so 767/787 is not comparable with v1's 326/349, which counted only ineligible coins met
inside the top/bottom 10. Same data, different counter.

**RM14** (research +74 %, Sharpe 1.7, DD 33 %): OPT median +41–45 %/yr, worst +32–36 %, Sharpe 1.1–1.2,
**DD worst 59–60 %**; CONS +32–39 %, worst +26–31 %, DD worst 58–60 %. Funding ≈ +2–3 %/yr only.
**BLEND25** (research +100 %, Sharpe 2.6, DD 31 %): OPT median +69–73 %, worst +42–46 %, Sharpe 1.6–1.7,
**DD worst 52 %**; CONS +52–58 %, worst +34–38 %, DD worst 52–55 %. Both remain "historical evidence,
not adopted" (EXP-014/015); 2025–26 is development data for them.

No path at any capital or book went below 73 USDT at 105 or became unable to trade (0 dead paths).

## 3. v1 -> v2, per offset (flow book)
| | OPT 105 | CONS 105 | OPT 1,000 | CONS 1,000 |
|---|---|---|---|---|
| Δ ann. per offset (pts) | +4.9, +14.5, +5.7, +3.7, −1.2, +6.1, −1.0 | +9.4, +15.1, +14.4, +7.0, −1.8, +1.0, −2.3 | +2.6, +0.1, −0.9, +0.6, 0.0, +0.9, +0.9 | +2.6, +1.4, −0.6, +1.0, +0.4, +1.3, +1.1 |
| Δ max DD per offset (pts) | −14.1, −3.5, −5.6, −0.1, −1.2, −2.3, +3.1 | −16.9, −6.1, −4.1, −0.3, −2.4, −0.9, −4.1 | within ±1.6 | within ±0.9 |
| Median ann. | 38 -> 42 % | 27 -> 32 % | 40 -> 40 % | 32 -> 33 % |
| Worst DD | 36 -> 28 % | 40 -> 26 % | 26 -> 26 % | 26 -> 26 % |
| Cash / max net exposure | 8 % / 0.30 -> 0 % / 0.16 | 8 % / 0.30 -> 0 % / 0.14 | 2 % / 0.12 -> 0 % / 0.03 | 2 % / 0.11 -> 0 % / 0.04 |

Reading: the live rules matter only for the small account. Nearest-lot rounding places the slots that
floor rounding rejected (min-order skips 193 -> 27 per path), the book is fully invested and balanced,
and the worst path's drawdown falls by 8–14 points; the 5.5 USDT band removes small resize trades. The
direction of the change is not guaranteed in general (two of seven offsets are lower), but five of seven
offsets improve by 4–15 points. Above 200 USDT every offset is within ±2.6 points of v1.

**Correction to v1 §3**: "minimum executable capital for a balanced book ~300 USDT" was a floor-rounding
artefact. Under the live rules a 105 USDT account already holds 10 positions with 0 % cash and a maximum
net exposure of 0.16, at the price of about one skipped slot per month (27 + 72 skips over 45 months);
at 200 USDT skips are ≈ 0. Fees per unit traded still do not fall with capital (cost line 9–10 %/yr at
every level), and returns do not rise with capital.

## 4. Cross-reference to ST-AUDIT-003 (VPS, read-only, Smart-trader `docs/audit/ST-AUDIT-003/`)
- Account identity reconciled to 0.0000 USDT residual; 27 live orders, all single full fills, 6.0 bps;
  no stop triggered; exchange positions = ledger = log. This reconciles money and fills, not selection:
  the decision-time rankings were not logged, so "live picks = rule" is shown only by reconstruction
  for R2/R3 and cannot be shown for R1 (production logging fix #11 in ST-AUDIT-003 §3).
- Live 2026-10-01 close -> 10-14 close: account −2.78 % (102.34 from 105.26); the live rule idealised
  (same-day, fractional, no cost) −3.57 %; the v1 replay rule −10.44 % because it held 龙虾USDT, −2.79 %
  with that contract excluded. 13 days are not annualised and say nothing about the scenario above
  (one week of a book whose median weekly return has a standard deviation near 5 %).
- "8 cycles, +1.27 % NAV" in v1 §4.3 meant 8 live passes (10-02 22:29 to 10-06 00:35), of which 2
  placed orders and 2 rebalances completed; by the cut-off there were 27 passes and 3 rebalances.
- The one-coin-per-rebalance selection differences found there (LINK/ADA, SOL/BNB, 龙虾) are exactly the
  rules copied into v2; whether v2 now matches the live selection historically cannot be checked
  (the R1 ranking was not logged), only forward.
- Open on the production side (not changed here, per the owner): fees/funding fields empty in daily
  records; pre-signature order failures not logged; full ranking and exclusion reasons not saved per
  rebalance. These are logging fixes, listed in ST-AUDIT-003 §3 #9–#12 with the rule that any change is
  prepared in isolation with a diff and rollback for the owner's review.

## 5. Status
- Flow book A: live at 105 USDT since 2026-10-02; executable historical scenario +32 to +42 %/yr median,
  worst path +25 to +33 %, DD 22–28 %; forward checkpoints 2026-11-27, 12-25, 2027-04-02 unchanged.
- No added capital, no new strategy, no change to the live executor from this audit.
- RM14 / BLEND25: historical evidence only; a forward shadow is the only way to add independent data.

## 6. Risk after nearest-lot rounding and the meaning of "cash 0" (added 2026-10-16, `st_audit2_paths.py`, `risk_after_rounding.csv`, `paths/`)
Flow book, OPT and CONS, 7 offsets each; exposure = |notional| / equity; margin at the live setting
(`rg/book/paper.py` LEVERAGE = 3, checked per order via `crossedMarginLeverage`, i.e. cross margin 3x).

| | 105 USDT | 1,000 USDT |
|---|---|---|
| Per-symbol exposure at rebalance: median / p99 / max | 10.0 % / 14.1 % / **15.7 % (OPT), 16.5 % (CONS)** | 10.0 % / 10.9 % / 11.8 % |
| Positions > 15 % of equity at rebalance (of 1,960 per scenario) | 1 (OPT), 2 (CONS); 8 of 27,380 across all paths; all BTC/CRV/SOL in 2023–24 when one lot was a large share of 10.5 USDT | 0 |
| Positions outside 8–12 % at rebalance | 1,380 below 8 %, 1,819 above 12 % (of 27,380): the lot grid scatters sizes ±20–40 % around target | ≈ none |
| Gross exposure at rebalance (max) | 1.17–1.19 | 1.02–1.03 |
| Daily (between rebalances) max: single symbol / gross / |net| | 24 % / 1.39–1.44 / 0.24–0.27 | 21 % / 1.41–1.42 / 0.22 |
| Initial margin used at 3x, max (gross / 3) | 46–48 % of equity | 47 % |
| Free-margin trough (1 − margin used) | 52–54 % | 53 % |

Readings.
1. **Nearest-lot rounding does widen single positions at 105 USDT**: the ±50 % tolerance allows a slot of
   up to 15 % of equity, and the 5.5 USDT band then keeps a same-direction position without resizing even
   when it has drifted, which is how 15.7–16.5 % appears (band 5.5 USDT = 52 % of a 10.5 USDT slot at
   105 USDT, but 5.5 % of a slot at 1,000 USDT; the live band is absolute, not proportional). The
   replay's size-tolerance check is applied at order time only, as in the live code; drift is bounded by
   the 2x trim (daily single-symbol maximum 24 %). This is a property of the live rules, not of the
   replay, and it is a reason to keep the gross at 1.0x and leverage at 3x unchanged, not a reason to
   change the rules from this audit.
2. **Gross and net exposure** stay within 1.0–1.2x at rebalance and 1.4x between rebalances (winners
   grow, losers shrink, equity falls); |net| peaks at 0.27 at 105 USDT. Nothing in the replay exceeds
   what 3x cross margin can carry: initial margin peaks at 48 % of equity and the worst 7-offset drawdown
   is 28 %, far from a cross-margin liquidation (which would need equity near the maintenance margin,
   roughly 1–2 % of gross notional). Maintenance-margin tiers, funding deductions on margin and Bitget's
   margin-ratio formula are not modelled; this is a headroom estimate, not a margin-call simulation.
3. **"Cash 0" is a notional-allocation statement**: `cash_frac = 1 − gross notional / equity` at the
   rebalance, so 0 % means the ten targets sum to about one times equity (gross 1.0x). It is not free
   margin and not idle balance: with 3x cross leverage about one third of equity is posted as initial
   margin and two thirds remain free at the rebalance. The v1 figure of "8 % cash" meant the floor
   rounding left ~8 % of the target notional unplaced; v2's 0 % means nearest rounding places it. Neither
   number is a liquidity reserve, and the live account's actual free margin is read from the exchange
   snapshot (ST-AUDIT-003 `cycles.csv`), not from this replay.
4. Open to the production side (ST-AUDIT-003 logging fix #3 / owner's request): record per rebalance the
   rounded targets, the per-symbol exposure after rounding, gross/net exposure and the exchange's margin
   headroom, so the next rebalance can be checked against these bounds directly.
