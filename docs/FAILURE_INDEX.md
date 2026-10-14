# Failure index — hypotheses already tested, by profit mechanism

Rule (owner, 2026-10-14): before any new experiment is registered, search this index. A new registration
must state which entry it is closest to and what is genuinely new (data, horizon, execution condition,
or mechanism), and why that would change the earlier failure's cause. Renamed indicators or re-tuned
parameters of a listed entry are refused.

| Mechanism | Where tested | Market / horizon | Outcome | Cause of failure |
|---|---|---|---|---|
| Failed breakout / liquidity-sweep reclaim | btc1000x EXP-001 A, EXP-001-INV; Smart Trader batch 6 (A6, A8) | BTC perp 15m, 6h; 10 perps 1h | gross ~0; net -0.5 R | no edge before costs; costs 0.5 R on tight stops |
| Trend pullback continuation (HTF trend + EMA pullback) | EXP-001 B, EXP-010 (maker rescue); ST batch 6 A1–A3, A7 | BTC 1h/4h; 10 perps 1h | gross +0.1 R, net < 0 | gross < exit costs; unfilled signals are the winners |
| EMA / MACD crosses, supertrend, Donchian intraday | ST batch 6, 14, 15 (96+ trials) | 1h–12h | net < 0 | costs; no edge at any timeframe |
| ICT / SMC (FVG, order block, OTE, CHoCH) | ST batch 6 | 1h | net < 0 both sides | none before costs |
| Price-action / S&R / chart patterns | ST batch 17–20 (S25 v2) | 15m–1D | 0/101 | none before costs |
| Funding-rate extreme reversal (single asset) | EXP-002; ST (funding level predicts nothing) | BTC 24–72h | positive 2020–22, zero 2023–24 | regime; crowded-long shorts lose in uptrends |
| Daily trend / breakout on the perp (long and short) | EXP-004 + holdout; ST batch 10–12 | BTC daily | LEAD in 2023–24, **-10 %/yr 2025–26** | pays funding; whipsaw in range; only halves drawdown |
| Options-expiry 08:00 UTC reversal | EXP-005/005b + holdout | BTC 15m, 240 min | +0.26 R 2023–24, **-0.08 R 2025–26** | effect disappeared (dealer pinning no longer binds) |
| 3-sigma hourly shock fade (+ OI flush) | EXP-006 | BTC 1h, 2–4h | gross <= 0 | shocks continue; OI filter removes continuation, no reversal left |
| FOMC pre-announcement drift / announcement-day reversal | EXP-007 | BTC daily, 2021–24 | negative | pattern absent after 2020 |
| Daily volatility-compression breakout | EXP-008 | BTC daily | Sharpe 0.9 in bull, -18 %/yr in TRAIN | period direction, not compression |
| Fear & Greed contrarian; greed short | EXP-009 + holdout | BTC daily | fear-buy +30 %/yr 2023–24, **-13 %/yr 2025–26** | buys every leg of a bear |
| Exchange net-inflow z-score | EXP-009 | BTC 5-day | Sharpe 0.3–0.6, never significant | weak |
| 5-minute taker-flow imbalance extremes (continuation and reversal) | EXP-012/012b | BTC 15–60 min | gross within ±0.02 R | no direction after flow extremes; cost 0.28 R |
| Crash rebound (coin -10 %, BTC -5 %, 24h) | ST batch 1–5 | 10 perps | p 0.05, unvalidated | found after looking; left tail |
| Cross-sectional 7-day momentum book | ST batch 7 D1 | 30 perps weekly | FAIL (Sharpe 0.4) | top-3 days carry it |
| Cross-sectional taker-flow book (5+5 weekly) | ST batch 7–9 **PROVISIONAL**, live since 2026-10-02 | 30 perps weekly | OOS +65–80 %/yr; see ST-AUDIT-001 | right-tail concentrated; start-day sensitive |
| Funding-carry book, composite books | ST batch 7 D3–D5 | 30 perps | provisional, weaker than flow | carry Sharpe fell since 2024 |
| Maker quoting / passive LP | Weather Quant #25 (48 variants); Axiom AX85 (24 strata) | Polymarket; Solana | all negative | adverse selection 1.5–4x spread |
| Copy-trading profitable wallets | Weather Quant #5/#12/#15/#19/#21 (266 wallets); Axiom #59, AX82 | Polymarket; Solana | live 0/16; -77 %; 0 promoted | skill not imitable; profit in creation slot / early entry |
| Forecast-vs-market on temperature buckets | Weather Quant #16/#28/#30; EXP-011 (market calibrated, Brier 0.058) | Polymarket daily | market better by 19–57 % log-loss | faster players with sub-hourly observations |
| Cross-platform prediction-market arbitrage | AUDIT-001 (Synpath) | Polymarket/Kalshi | artefact of sampled prices | no bid/ask; legal/geographic split |
| Solana new-token early entry, deployer/operator history, attention, right-tail bags | Axiom #27–#77, AX66–AX88 | Pump.fun / PumpSwap | all negative except C03 (pending 10-28) | profit only in creation slot; costs mis-modelled 13x |

| Regime gates / crowding filters as overlays on the flow book (BTC near-high, ETH/BTC, funding crowding) | EXP-013 | 30 perps weekly, 2025–26 paired | 0/5; CIs ±10–20 %/yr | tail-driven book makes 638 days underpowered; gates remove the winning tail |
| 14-day BTC-hedged residual momentum book (same engine as flow book) | EXP-014 | 30 perps weekly | standalone significant both windows (Sharpe 1.7); corr 0.47 with flow | not independent; DD 33 % |
| Flow + residual-momentum blended ranking | EXP-015 | 30 perps weekly, paired 2025–26 | +21 %/yr point estimate, p 0.08, DD doubles | underpowered; concentrates the tail |
| Funding-carry rank book | EXP-014 control; ST batch 7 D3 | 30 perps | 2023–24 Sharpe 1.4, 2025–26 -0.05 | carry decayed since 2025 |

Open, not failed: Smart Trader flow book (forward checkpoints 11-27, 12-25, 2027-04-02); Axiom C03 (10-28).
