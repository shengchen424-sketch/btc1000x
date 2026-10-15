# ST-AUDIT-002 — Bitget-executable replay: the research return roughly halves, and listing eligibility, not capital, is the main cause

Run 2026-10-15 on commit `09e411a`. Historical executability of the flow book (A), RM14 and BLEND25,
evaluated UNDER TODAY'S CONTRACT RULES (step, minimum) with historical eligibility scenarios.
Not a live reproduction: no VPS fills, orders or rejections were available (see §5).

## 0. Eligibility evidence (`evidence/exchange/bitget_listing_dates.json`)
| Class | Symbols (of 180 traded) | Meaning | Treatment |
|---|---|---|---|
| EARLIEST-QUOTE | 146 | first daily candle served by Bitget history-candles, paged to exhaustion; no cross-symbol clustering of first dates (max 3 symbols share a date), so not a retention edge; **not an official listing confirmation** (the announcements API serves recent items only) | OPT: eligible from that date; CONS: from that date + 30 days |
| ABSENT | 34 | no Bitget candles under the symbol or its 1000-prefix alias: delisted, renamed or never listed; indistinguishable | unlisted in every scenario; 11.4 % of research PnL |
Delisted-contract coverage gap: today's contract list cannot show past delistings; ABSENT is the
visible part of that gap and a lower bound on it.

## 1. Table A — the 85 top-1 % research positions (89 % of research PnL), at 105 USDT, OPT dates
`top85_positions_executability.csv` (symbol, dates, research return, evidence, Bitget first quote,
tradable at entry, quantity and notional at a 10.5 USDT slot, reason, retained profit fraction).

| Question | Answer |
|---|---|
| Tradable on Bitget on the entry day? | **61 of 85 (72 %)**; 24 not: 11 ABSENT (REEF, BLZ, BNX), 13 listed later (TRB x7 in 2023 — Bitget first quote 2024-06-26; AKE x6 in Jul–Aug 2026 — first quote 2026-09-01) |
| Evidence | EARLIEST-QUOTE for 74, ABSENT for 11; none confirmed by an official announcement |
| Placeable with 105 USDT (10.5 USDT slot, today's step/minimum)? | 61 of 85 (every tradable one): rounding leaves 82–100 % of the slot (SIREN at 0.25 USD: 30–40 contracts = 8.6–10.0 USDT) |
| Profit retained (notional-weighted) | **68 %** of the top-85 research return; 0 % from ABSENT symbols; the single largest position (TRB +317 %, Sep 2023) is lost |

## 2. Table B — five capital levels x three books x two scenarios (`executable_table_OPT.csv`, `_CONS.csv`)
Median and worst of the 7 rebalance offsets (NOT pooled; each offset is one path). 2023-01 .. 2026-09.
Costs 9 bps per unit traded (6 taker + 3 slippage); funding = Binance realised rates (0 missing
position-days); 2x trim; no ladder; no halt; equity compounds; skipped slots stay in cash.

**Flow book A (research: +79 %/yr, Sharpe 2.0, DD 17 %)**
| Scenario | Capital | Ann. median / worst | Sharpe med / worst | Max DD worst | Min equity worst | Dead paths | Cost %/yr | Funding %/yr | Avg positions | Long / short / net exp. | Max net exp. | Cash | Skips unlisted / min-order |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OPT | 105 | +38 / +23 % | 1.18 / 0.84 | 36 % | 84.6 | 0 | 8.8 | 19.4 | 10.0 | 0.45 / 0.47 / -0.02 | 0.30 | 8 % | 326 / 193 |
| OPT | 200 | +37 / +29 % | 1.14 / 1.02 | 30 % | 170 | 0 | 9.0 | 21.4 | 10.0 | 0.46 / 0.48 / -0.02 | 0.18 | 6 % | 303 / 46 |
| OPT | 300 | +44 / +30 % | 1.25 / 1.04 | 26 % | 267 | 0 | 9.5 | 25.3 | 10.0 | 0.46 / 0.48 / -0.02 | 0.15 | 5 % | 297 / 2 |
| OPT | 500 | +40 / +30 % | 1.19 / 1.02 | 26 % | 427 | 0 | 9.9 | 25.6 | 10.0 | 0.48 / 0.49 / -0.01 | 0.12 | 3 % | 296 / 0 |
| OPT | 1,000 | +40 / +30 % | 1.17 / 1.02 | 26 % | 851 | 0 | 9.9 | 25.4 | 10.0 | 0.49 / 0.50 / 0.00 | 0.12 | 2 % | 296 / 0 |
| CONS | 105 | +27 / +14 % | 0.97 / 0.58 | 40 % | 79.9 | 0 | 8.1 | 13.0 | 10.0 | / / -0.02 | 0.30 | 8 % | 349 / 214 |
| CONS | 200 | +26 / +22 % | 0.94 / 0.82 | 29 % | 165 | 0 | 8.0 | 15.9 | 10.0 | / / -0.02 | 0.19 | 6 % | 322 / 55 |
| CONS | 300 | +31 / +27 % | 0.99 / 0.95 | 26 % | 257 | 0 | 8.6 | 19.3 | 10.0 | / / -0.02 | 0.15 | 5 % | 313 / 6 |
| CONS | 500 | +31 / +25 % | 1.01 / 0.90 | 25 % | 405 | 0 | 8.7 | 19.4 | 10.0 | / / -0.01 | 0.12 | 3 % | 313 / 0 |
| CONS | 1,000 | +32 / +25 % | 1.01 / 0.90 | 26 % | 813 | 0 | 8.9 | 20.2 | 10.0 | / / -0.01 | 0.11 | 2 % | 313 / 0 |

**RM14** (research +74 %, Sharpe 1.7, DD 33 %): OPT median +38–42 %/yr, worst +33 %, Sharpe 1.1 / 0.95,
**max DD 54–59 %**; CONS +31–34 %, DD 54–58 %. **BLEND25** (research +100 %, Sharpe 2.6, DD 31 %):
OPT +55 % (105) to +70 % (300–1,000), worst +30–41 %, Sharpe 1.5–1.7 / 1.0–1.2, **DD 48–52 %**;
CONS +47–56 %, DD 43–51 %. Full rows in the CSVs.

No path at any capital reached the point of being unable to trade (min equity 80 USDT at 105; 0 dead paths).

## 3. Where the research return goes (flow book, 1,000 USDT, median of 7 offsets)
| Step | Ann. return | Δ |
|---|---|---|
| Research form (fractional weights, 10 bps turnover) | +79 % | |
| + contract lots, 9 bps/unit, compounding, every symbol eligible | +66 % | -13 |
| + Bitget eligibility, OPT dates | +40 % | **-26** |
| + 30-day conservative buffer (CONS) | +32 % | -8 |
At 105 USDT the min-order skips (193 per path) add little further loss (+38 % vs +40 %) because a
skipped slot is refilled by the next-ranked placeable coin. What the small account does change is
balance: with a skipped slot the book's net exposure reaches ±0.30 of equity at 105 USDT against
±0.12 at 500+ (average net exposure -0.02 everywhere). Minimum executable capital for a balanced
book under today's rules is therefore ~300 USDT (min-order skips fall to 2 per path); this is not a
capacity ceiling, and returns do not rise with capital beyond that.

## 4. What this means
1. The research headline (+79 %/yr) is not what the Bitget account can earn from this rule: the
   executable range is **+27 % to +44 %/yr median (worst path +14 % to +30 %)** with 26–40 % drawdowns,
   depending on how listing dates are treated. The gap is mostly coins that were not on Bitget
   when the signal fired (TRB 2023, AKE mid-2026, REEF/BLZ/BNX), i.e. the right tail.
2. RM14 and BLEND25 keep more of their return under execution but carry 45–60 % drawdowns; nothing
   here changes their status (historical evidence, not adopted).
3. Live record so far (8 cycles, +1.27 % NAV) is consistent with the executable, not the research,
   series, but 4 days say nothing.

## 5. Not covered (needs the VPS evidence pack, read-only and redacted)
Per-fill slippage on small coins, orders rejected by Bitget, target-vs-filled positions per
rebalance, stop confirmations, funding bills after 10-06. Until then this replay is "what the rule
could have done on Bitget under today's rules", not a reproduction of the live account.
