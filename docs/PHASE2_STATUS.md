# BTC 1000X — Phase 2 status (2026-10-14 ~14:30 UTC, after round 4)

## Scoreboard (this repository)

| Exp | Family | Trials | VALIDATION 2023–24 | Holdout 2025-01..2026-09 | State |
|---|---|---|---|---|---|
| EXP-001 / INV | A failed-break 15m; B trend-pullback; inversions | 48 | all negative: cost, not direction | — | closed |
| EXP-002 | C funding-rate extreme reversal | 8 | 0 lead | — | closed |
| EXP-004 | D daily trend, perp + funding | 6 | 3 LEADs | **REJECTED** | closed |
| EXP-005 / 005b | E options-expiry 08:00 fade | 6 | 2 LEADs | **REJECTED** | closed |
| EXP-006 | F 3-sigma shock fade + OI flush | 4 | 0 lead | — | closed |
| EXP-007 | G FOMC drift | 3 | 0 lead | — | closed |
| EXP-008 | H daily compression breakout | 4 | 0 lead | — | closed |
| EXP-009 | I Fear & Greed / exchange flows | 6 | 1 CANDIDATE (8 trades) | **REJECTED** | closed |
| EXP-010 | B long with maker entries (rescue) | 4 | net still negative | — | closed |
| EXP-012 / 012b | J order-flow shocks (taker imbalance, intensity, OI) | 16 | gross within ±0.02 R | — | closed |
| EXP-011 | K Polymarket daily temperature: ensemble vs market | — | running (prices exist only from ~2026-09-15) | — | in progress |

Twelve families, 105 trials, three holdout looks. Shadow registries empty.

## Audits and readings done this round
- AUDIT-001: four public "profitable" repositories — none verifiable; two backtests are circular
  (`research/results/AUDIT-001.md`).
- Weather Quant (owner's project, 39 tickets): live copy-trading 0/16, -100 %; every registered OOS
  test KILL/INCONCLUSIVE; market log-loss beats the model by 19–57 %; bots reprice 134 s after the
  observation, before public METAR.
- Axiom (owner's project, ~50 tickets): real money -77 % (copy bot) and -0.81 SOL (manual); every
  early-launch / wallet-following / deployer / attention / LP hypothesis NEGATIVE; skilled wallets'
  profit sits in creation-slot entries (not imitable, AUC 0.40–0.44); one survivor (C03, +1.08 % at
  0.01 SOL, Kish ~21) awaits its clean re-test on 10-28.

## The owner's five priorities, against the evidence

| # | Direction | Status |
|---|---|---|
| 1 | BTC liquidation / order-flow anomalies | Tested on public data (EXP-006, EXP-012/012b): nothing after costs. Liquidation prints are not public historically; only a forward collector on the VPS can create the dataset. |
| 2 | BTC high-leverage system, positive after all costs | Phase 1–2: no family survives; the binding constraint is cost per R at 10 USDT. Not re-run (rule: no repackaging). |
| 3 | Synchronised signals of profitable CEX traders | Bitget copy-trading endpoints need an API key (any account); Binance/Bybit leaderboards are closed to automation. No historical archive exists: forward collection only. The owner's own Polymarket version of this (Weather Quant #15/#19/#21: 266 wallets, 0 promoted) and Solana version (Axiom #59/AX82: skill not imitable) both failed. |
| 4 | Solana new-token on-chain flows / smart money | Duplicates Axiom's ~50 tickets, all negative except C03 (pending 10-28). Not started here. |
| 5 | GitHub strategies with real fills and reproducible data | Protocol applied in AUDIT-001; zero of four passed. Will apply to any new candidate the owner names. |

## What would actually change the answer
1. Capital (200–300 USDT) — changes feasible stops and cost share for every BTC family.
2. Infrastructure the owner's projects lack: slot-0 / co-located execution (Axiom), sub-hourly
   station observations (Weather Quant), liquidation stream + order book archive (this project).
3. Scope: multi-coin cross-sectional books (the only factor family with OOS evidence, Smart Trader).

## Operations
- Repository: github.com/shengchen424-sketch/btc1000x, 36 tests passing.
- No order has been or can be sent.
