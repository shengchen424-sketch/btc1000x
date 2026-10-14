# BTC 1000X — Phase 1 report (2026-10-14)

## 1. Completed

| Task | State | Evidence |
|---|---|---|
| 1 Environment | partial: VPS unreachable from this cloud session (network policy); used the Smart Trader audit of 2026-10-02/07 for the protected inventory | §4 |
| 2 Bitget BTCUSDT contract rules | done, from the public API 2026-10-14 12:10 UTC | `evidence/exchange/contract_BTCUSDT.json`, `position_tiers_BTCUSDT.json`, `funding_BTCUSDT.json` |
| 3 10 USDT feasibility | done; calculator + table | `src/b1k/risk/feasibility.py`, `evidence/exchange/feasibility_10usdt.json` |
| 4 Architecture | done (RULE 2 layout, common `SignalIntent` interface) | `README.md` |
| 5 Data pipeline | done: Binance UM BTCUSDT 1m 2020-01-01 .. 2026-10-13 (2.65 M bars), funding; manifests with sha256; 0 duplicates, 0 misaligned, 0 bad OHLC; Bitget parity measured | `evidence/data_quality_1m.json`, `evidence/exchange/bitget_vs_binance_parity.json` |
| 6 Strategy interface | done; backtest and shadow share `prepare()/signal_at()` | `src/b1k/strategies/base.py` |
| 7 Strategies A and B | done, long and short | `failed_break.py`, `trend_pullback.py` |
| 8 Event-driven backtester | done: 1m exit resolution, stop-before-TP in the same bar, gap fills at the open, trailing from prior bars only, funding at settlements | `src/b1k/backtest/engine.py` |
| 9 Risk controls | done: deterministic engine, kill switch, DRY_RUN default, live path raises | `src/b1k/risk/engine.py`, `execution/orders.py` |
| 10 Baseline research | done: EXP-001 registered and committed before VALIDATION was read; 24 trials | `research/registrations/EXP-001.md`, `research/results/EXP-001/` |
| 11 Comparison and feasibility | done | `research/results/EXP-001/REPORT.md` and §3 below |
| 12 Next phase | §5 | |
| Tests | 24 passing (`python -m pytest`): unit, leakage/causality, execution fills, integration, determinism | `tests/` |

## 2. Verified exchange rules and feasibility (Bitget BTCUSDT USDT-FUTURES)

Min 0.0001 BTC, step 0.0001, min notional 5 USDT, taker 0.06 %, maker 0.02 %, max leverage 150, tier-1
maintenance margin 0.4 % (<= 200k USDT), funding every 8 h (last 100 settlements: mean +0.0057 %, max +0.01 %).
One lot at 83,720 = 8.37 USDT notional.

| Leverage | margin | free margin | cost per stop-out | max stop at 1 % risk | liquidation distance | feasible |
|---|---|---|---|---|---|---|
| 5x | 1.67 | 8.32 | 0.023 USDT (23 % of budget) | 0.91 % | 19.5 % | yes |
| 10x | 0.84 | 9.16 | same | 0.91 % | 9.5 % | yes |
| 20x | 0.42 | 9.58 | same | 0.91 % | 4.5 % | yes |
| 30x | 0.28 | 9.72 | same | 0.91 % | 2.9 % | yes |
| 50x–100x | <= 0.17 | >= 9.83 | same | 0.91 % | 0.5–1.5 % | **no**: liquidation inside 2x the stop |

Leverage changes margin, not risk. Position size cannot vary: one lot or nothing until equity ~20 USDT.
Every stop-out costs 23 % of the risk budget before the market moves.

## 3. Research result (EXP-001)

**0 CANDIDATE, 0 LEAD, router adds no value.** Details in `research/results/EXP-001/REPORT.md`.

- A (failed break, 15m): gross R -0.10 .. 0.00 before costs on 660–1,900 trades per trial; net -0.49 .. -0.68.
  No edge exists to pay the 0.46–0.64 R round-trip cost that 0.6–0.8 % stops imply.
- B long (trend pullback, 1h/4h): gross +0.08 .. +0.15 R; net -0.07 .. -0.15; best trial p 0.76, CI [-0.25, +0.13].
  Stops 1.3–1.6 % exceed what 10 USDT can carry at 1 % risk.
- B short: negative before costs in 2023–24.
- Regime router: 0 of 160 (trial, regime) pairs eligible on TRAIN -> NO_TRADE everywhere.
- 10 USDT replay on VALIDATION: A -73 % to -91 %; B long -8 % to -21 %; B short -32 % to -38 %.

## 4. Problems and fixes

| Problem | Fix / status |
|---|---|
| VPS 187.77.128.30 unreachable (ports 22/8080/8888 blocked by this session's network policy) | TASK 1 done from the Smart Trader audit; the live inventory check (`pm2 ls`, `systemctl list-timers`, disk) must be re-run on the VPS before deploying anything. Deployment is a `git clone` into `/root/btc1000x`; it touches no other unit. |
| Account is in union margin mode; isolated margin rejected (code 40883 in earlier logs); same account trades BTCUSDT live for Smart Trader's book, one-way mode merges positions | Owner approved a mode change and will create a sub-account. Until the sub-account exists, `LIVE_TRADING` stays impossible by code. |
| Disk below the owner's 100 GB floor (87 GB on 2026-10-07) | This project needs ~0.2 GB. Owner is watching the disk. |
| Binance microsecond timestamps in 2025+ archive files | normalised to ms in the fetcher; covered by the quality report |
| Trail tighter than the structural stop made 1 R inconsistent | initial stop = tighter of the two (fixed before any VALIDATION read) |
| Engine debugging exposed the 4 default trials on 2022 (TRAIN) | disclosed in the registration; VALIDATION untouched until the registered run |

## 5. Recommendation for Phase 2

1. **Capital, not code, is the binding constraint.** At 10 USDT with 1 % risk, any stop wider than 0.91 %
   is unexecutable and any stop narrower pays >= 0.3 R per trade in costs. No published intraday BTC
   pattern family has shown a gross edge of that size after Smart Trader's 21 batches and this
   experiment. Decision for the owner: (a) keep 10 USDT and accept that research continues in
   shadow with no live path, or (b) set a research capital threshold (about 200–300 USDT lets one lot
   carry a 2–3 % stop at 1 % risk, or ten lots carry a 0.9 % stop) before any live authorisation.
2. **Do not reopen A or B with new parameters, timeframes or filters** (registration failure criterion).
3. **Test distinct mechanisms with lower cost share**, each as its own registration:
   - EXP-002 funding-rate carry / basis extremes on the daily clock (entry via maker limit orders at
     2 bps; holding days, stop 3–5 %): the only factor family that passed gates in the owner's earlier
     project, never tested as a single-asset BTC rule here.
   - EXP-003 liquidation-cascade rebound on 1m/5m using Binance `liquidationSnapshot` archive files
     if coverage is adequate (to be verified first; do not assume).
   - EXP-004 daily-close trend (SMA200 filter + Donchian 55/20) on the perpetual with funding paid:
     Smart Trader found it works on spot and fails on the perp because of funding; a registered re-test
     with Bitget's actual funding (available from 2026-07) settles whether the perp version is viable.
4. **Execution research that lowers cost share**: maker entries (limit at the signal bar's close,
   cancel if unfilled in one bar) cut 4 bps per side; measure fill rates in shadow before assuming them
   in a backtest.
5. **Forward shadow** stays idle (empty `shadow_trials.json`). Deploy the timer on the VPS only when a
   trial reaches LEAD; until then it would only consume resources.

Stop before live trading: nothing in this phase qualifies for live or paper capital.
