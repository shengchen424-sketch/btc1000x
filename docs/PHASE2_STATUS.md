# BTC 1000X — Phase 2 status (2026-10-16 ~03:00 UTC, after the executability audits, the reproducibility check and the production-side logging/shadow branches)

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
| EXP-011 | K Polymarket daily temperature: ensemble vs market | — | market calibrated (Brier 0.058) | — | closed |
| EXP-016 | L Polymarket crypto windows: resolution check + fair-value engine (no market comparison yet) | 3 models × 4 windows | 15m/1h/4h CALIBRATED, 1d NOT | — | infrastructure; market atlas after ~3 weeks of books |

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

## Program pivot (owner, 2026-10-14): research the validated strategy, not new ones
- ST-AUDIT-001: the Smart Trader flow book reproduced independently (+79 %/yr, Sharpe 2.0, DD 17 %
  pooled over 7 offsets, 2023–2026-09). Top 1 % of positions = 89 % of PnL; long leg median negative;
  legs correlate -0.67; since 2025 the short leg carries; capacity knee 200–300 USDT; 141/180 coins on Bitget.
- EXP-013: five incremental overlays, paired B − A on 2025–26: 0 adopted (CIs ±10–20 %/yr).
- EXP-011 closed: Polymarket temperature market calibrated (Brier 0.058); ensemble archive unavailable.
- EXP-014: residual momentum (14d) significant standalone (Sharpe 1.7 both windows) but corr 0.47 with the flow book; carry decayed. EXP-015: flow+RM14 blend +21 %/yr point estimate, p 0.08, DD doubles: not adopted.
- ST-AUDIT-002 / 002v2: Bitget-executable replay of A, RM14, BLEND25 at 105–1,000 USDT with historical
  listing evidence (146 EARLIEST-QUOTE, 34 ABSENT of 180 traded symbols) and, in v2, the live executor's
  selection/rounding/band rules. Flow book: **+32 to +42 %/yr median historical scenario** (worst path
  +25 to +33 %, DD 22–28 %) vs +79 % research; the gap is coins not on Bitget when the signal fired (TRB
  2023, AKE 2026, REEF/BLZ/BNX = 28 % of top-85 profit). Rules matter only at 105 USDT (v1 floor
  rounding -> ~300 USDT minimum was an artefact; live nearest-lot rule fully invests 105 USDT). Label:
  historical scenario under today's contract rules and Binance funding, not a verified return.
  Reproduced byte-for-byte from a clean checkout of `66c9ad1` on the fixed data snapshot (33/33 files,
  `REPRO.md`; a reproducibility check, not fresh validation). Post-rounding risk (`REPORT.md` §6): at
  105 USDT single positions reach 15.7–16.5 % of equity (lot grid + absolute 5.5 USDT band), gross up to
  1.2x at rebalance and 1.4x between, initial margin at 3x cross peaks at 48 % of equity; "cash 0" is a
  notional-allocation measure, not free margin.
- ST-AUDIT-003 (VPS session, read-only, redacted pack in Smart-trader `docs/audit/ST-AUDIT-003/`): account
  identity reconciled to 0.0000 residual; 27 live orders all full fills at 6.0 bps, ~0 slippage; live
  2026-10-01..10-14 −2.78 % (13 days, not annualised); three executor-vs-replay rule differences found
  and copied into 002v2; four logging gaps on the production side listed, nothing changed.
- Production-side follow-up (VPS session, Smart-trader repo, 2026-10-15/16, reviewed here from the pushed branches):
  `v31/logging-fixes` @ e7758e2 (order lifecycle events with source/armed/phase; ledger fees and funding with
  unknown != 0 and billId de-duplication; decision records with decision_id, code/config version, data
  cut-off and hashes, full ranking, exclusion reasons, rounded targets, observe-only post-rounding risk check;
  262 tests pass vs 249 baseline, same 4 known failures; selection statements unchanged — `select()` wraps the
  old `targets()` code and R2/R3 replays match the logs). `v31/xshadow` @ 7b88232 (order-disabled forward paper
  shadow of A / RM14 / BLEND25, spec XSHADOW-1 hash 614971cfced6ddc3 referencing btc1000x 66c9ad1, no adapter /
  gateway imports, restart-safe paper fills, smoke test on public data, hardened systemd units proposed, not
  installed, no prospective start time yet). Neither is deployed; both wait for the owner.
  Note: BLEND25 = z(flow) + 0.5 z(RM14), i.e. effective weights 2/3 : 1/3 (the "0.75/0.25" shorthand used in one
  coordination message was wrong; the code and EXP-015 report were always 0.5 z); its EXP-015 verdict is DISCARD
  and it is shadowed for observation only. Live incident: the 2026-10-16 00:35 UTC live pass aborted at start-up
  on a Bitget public-API timeout (`/mix/market/contracts`); no account read, no order; read-only check afterwards:
  equity 102.50, 10 positions / 10 stops, ledger 0 difference; no retry logic exists (fix needs owner approval).
- `docs/FAILURE_INDEX.md` created: 26 mechanism families with their failure causes.

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
- No order has been or can be sent from this repository. The Smart Trader book runs live at 105 USDT on the VPS (owner's decision);
  no added capital, no executor change, no new strategy until the 2026-11-27 forward checkpoint.
