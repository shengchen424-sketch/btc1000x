# ST-AUDIT-001 — Smart Trader taker-flow book: independent reproduction and profit-source audit

Date 2026-10-14. Scope: the owner's only strategy with out-of-sample evidence (Smart Trader, branch
`v31/retail-growth`; live on Bitget since 2026-10-02 at ~105 USDT). Method: rebuild the data from the
public Binance archive (900 UM USDT perps, daily bars 2022-06 .. 2026-09, funding for the 180 traded
symbols), re-implement the rule as mapped from `rg/book/core.py` / `rg/book/paper.py`, run the research
form (fractional weights, 7 rebalance offsets), and attribute. Code: `research/experiments/st_audit_*.py`.
Outputs: `positions.parquet` (8,576 positions), `daily.parquet`, `summary.json`.

## 1. The rule (as implemented, three differences from how it is usually described)
Universe = top 30 by 30-day rolling median of daily quote volume, listed >= 180 days (not top 10).
Factor = 7-day sum of taker-buy quote / 7-day sum of quote volume - 0.5, on DAILY bars (not 15m).
5 longs = first 5 of the top-10 ranks, 5 shorts = first 5 of the bottom-10; equal weight, gross 1.0;
rebalance every 7 days on the completed daily bar; 10 bps per unit of turnover; trim to entry size above
2x; realised funding. Live adds exchange stops (long -50 %, short +100 %) and Bitget lots; the 30 %
halt is disabled (`HALT_DD = 1.01`). The quoted "+59 %/yr, Sharpe 1.97" is the batch-7 quintile
research book, not the live 5+5 form.

## 2. Reproduction (2023-01-01 .. 2026-09-30, research form)
| Source | Ann. return | Sharpe | Max DD |
|---|---|---|---|
| Smart Trader batch 9 `live_config_daily_net` (same window) | +65–81 % | 1.85 | 21 % |
| **This reproduction, 7 offsets pooled** | **+79 %** | **2.01** | **17 %** |
| by start offset (0..6) | +61 / +64 / +63 / +79 / +115 / +95 / +65 % | 1.52–2.24 | 18–27 % |

Independent data and code reproduce the headline. Decomposition per year (pooled, % of equity):

| Year | Net | Long leg | Short leg | Funding | Cost | Max DD |
|---|---|---|---|---|---|---|
| 2023 | +83 % | +79 | -14 | +26 | -6.7 | 11 % |
| 2024 | +42 % | +46 | +16 | +3 | -6.7 | 17 % |
| 2025 | +65 % | -4 | +73 | +6 | -6.8 | 9 % |
| 2026 (to 09-30) | +166 % (ann.) | -4 | +28 | +23 | -5.0 | 15 % |

Funding is +15.5 %/yr of the result (shorts in crowded alts collect it), costs -6.7 %/yr at 1.0 gross.

## 3. Profit sources — the owner's five questions

**Concentration (the main finding).** 8,576 positions: mean +1.43 %, median +0.15 %. Longs: mean
+2.3 %, **median -1.25 %**; shorts: mean +0.6 %, median +1.6 %. The top 1 % of positions (85) are
**89 % of total PnL**; the top 5 % are 207 % (the other 95 % lose, mean -1.6 %). The ten best coins
are 84 % of PnL: ZEC 20 %, TRB 11 %, AKE 8 %, SUI 8 %, BTC 7 %, RUNE 7 %, SIREN 6 %, SOL 6 %, BLZ 6 %,
CRV 6 %. Best single positions: TRB long +317 % (2023-09..11), LAB +248 %, AKE +235 %, SIREN +219 %,
PIPPIN +212 %, ZEC +198 %. At the daily level: skew 1.7, kurtosis 18; dropping the best 1 % of days
takes the annual return from +79 % to +36 %; dropping 5 % makes it -18 %.
Reading: the long leg is a lottery on 7-day-flow winners in small/mid caps; the short leg is the
steady part. The strategy's expectation is real in aggregate but arrives in a handful of positions.

**Long/short interaction.** Daily leg returns correlate -0.67 (by year -0.46 to -0.88): the legs hedge
each other strongly, which is why the book is BTC-neutral (corr -0.03) with max DD 17 % despite
single positions of +300 %. Since 2025 the long leg is flat/negative and the short leg carries: a
regime shift inside the sample that the pooled numbers hide.

**Regime.** Earns most when BTC is >20 % below its 90-day high (+193 %/yr, Sharpe 2.1) and least
near highs (+24 %/yr, Sharpe 0.9). It is a dispersion/crash harvester: a natural hedge for any long
BTC exposure in the owner's portfolio.

**Capacity (batch 8, order-by-order with Bitget lots).** The curve flattens at 200–300 USDT: Sharpe
0.86 (worst start -0.62) at 105 USDT with the drawdown ladder, 1.6 at 200, 1.7 at 300–1,000. The
live 105 USDT configuration only works with the ladder removed (which it is), at 27 % worst DD.
Costs 8–12 %/yr. Each extra USDT of risk budget above ~300 buys nothing until the universe's
liquidity binds (not reached at 1,000).

**Decay.** Last 30 days to 09-30: -63 % annualised (one -9 % day on 09-24 when AKE, a short, +?/
ONDO +27 % moved against it); last 90 days +43 %/yr, Sharpe 1.1; the rolling-90-day Sharpe is at
the 37th percentile of its own history. No evidence of decay; also no power to detect any in 30 days.

**Executability on Bitget.** 141 of the 180 traded symbols are listed on Bitget today (39 are not,
15 % of PnL; BLZ, BNX, FTM among the top contributors). The right-tail positions were in coins that
are listed (ZEC, TRB, AKE, SIREN, LAB), but whether a 10 USDT lot in them fills at the daily close
without moving the price is untested; the live record (16 fills, slippage -2 bps median) covers
majors only.

**Start-day sensitivity.** 7 offsets span +61 % to +115 %/yr and Sharpe 1.5–2.2: a third of the
result is which weekday the book happens to rebalance on. Pooling offsets (daily tranches) halves
the drawdown (17 % vs 18–27 %); the live form uses one offset.

## 4. What this means for the three-layer design
1. Validated portfolio: the book qualifies on evidence, but its expectation is tail-driven. Position
   caps, stops (long -50 %) and the 2x trim all cut the right tail that carries it; the live form's
   stop at -50 % removes almost nothing (losers are small), but any take-profit or tighter trim would
   remove the strategy. The 2x trim is already in the reproduction.
2. Capital allocation: at ~105 USDT the strategy is below its capacity knee; the first 200 USDT of
   capital is worth more than any research. Size by the short leg's steadiness, not the long leg's
   lottery.
3. Research (week 2): incremental-alpha tests must target the identified weaknesses — the long leg
   since 2025, and the near-high regime — not the aggregate. Candidates: BTC-regime gate on the long
   leg (reduce when BTC is near highs), funding/OI crowding on the short leg, ETH/BTC relative flow.
   Each as B - A paired on the same days with CI; registered first.

## 5. Caveats
- Research form, fractional weights, no lots/stops; funding from Binance, prices from Binance (the
  live venue is Bitget; the book's own parity check: close p99 3 bps).
- The universe and factor reconstruction may differ from the VPS data in exclusions and dead symbols
  (864 vs 900 symbols); the agreement of the headline numbers says the differences are small.
- Position returns exclude funding; daily series include it.
