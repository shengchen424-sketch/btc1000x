# BTC 1000X — Phase 2 status (2026-10-14 13:15 UTC, after round 3)

Autonomous research loop, reporting after each round. Everything below is on `main`.

## Scoreboard

| Exp | Family | Trials | VALIDATION 2023–24 | Holdout 2025-01..2026-09 | State |
|---|---|---|---|---|---|
| EXP-001 | A failed-break 15m; B trend-pullback 1h/4h | 24 | 0 lead; costs 0.2–0.6 R/trade | — | closed |
| EXP-001-INV | the same 24 inverted | 24 | all negative: loss is cost, not direction | — | closed |
| EXP-002 | C funding-rate extreme reversal | 8 | 0 lead | — | closed |
| EXP-004 | D daily trend, perp + funding | 6 | 3 long LEADs (below buy-and-hold) | **REJECTED** (-10.5 %/yr) | closed |
| EXP-005/005b | E options-expiry 08:00 fade | 6 | 2 LEADs (+0.26 R, p 0.008) | **REJECTED** (-0.08 R) | closed |
| EXP-006 | F 3-sigma shock fade + OI flush | 4 | 0 lead | — | closed |
| EXP-007 | G FOMC drift | 3 | 0 lead (negative) | — | closed |
| EXP-008 | H daily compression breakout | 4 | 0 lead (Sharpe 0.9, p 0.09; TRAIN negative) | — | closed |
| EXP-009 | I Fear & Greed / exchange flows | 6 | 1 CANDIDATE (FNG_L25, 8 trades; TRAIN -13 %/yr) | **REJECTED** (-13 %/yr) | closed |
| EXP-010 | B long with maker entries (rescue) | 4 | fill 98 %, net still -0.04..-0.10 R | — | closed |

Ten families, 89 trials, three one-shot holdout looks spent, one literature scan (LIT-001).
Shadow registries are empty. No trial is eligible for forward observation.

## The one finding that repeats

Every rule that passed VALIDATION (daily trend longs, expiry fade, fear-buying) failed the holdout
in the same way: 2023–24 was a bull regime with one drawdown, 2025–26 a bear/range regime. The
rules were long-the-regime, not an edge. The short mirrors did the opposite (DON_S +15 %, FNG_S75
+16 % in the holdout after failing both earlier periods). Nothing worked in both.

At the intraday level the constraint is arithmetic: with 10 USDT and 1 % risk the widest executable
stop is 0.91 % and a round trip costs >= 0.2 R; no intraday family produced a gross edge above
0.15 R; maker entries recover ~0.05 R of that.

## Social-media data (owner request)

- Obtainable with history: Fear & Greed (2018–), CoinMetrics on-chain flows (2019–). Tested: EXP-009.
- Not obtainable without paying or bypassing access controls: X/Twitter history (API is paid),
  Reddit (403 for this egress), Google Trends / GDELT / Wikipedia pageviews (rate-limited for this
  shared address; could work from the VPS).
- Built: `b1k.intelligence.social_collector` — public Telegram channel previews (no login) plus
  F&G, lexicon score, hourly timer (`ops/b1k-social.*`). Tested live: 73 messages from 4 channels.
  It builds a forward dataset only; the first testable sample is months away.

## Decisions only the owner can make (the loop is paused here on purpose)

1. **Capital.** Research at 10 USDT has answered "no" ten times. 200–300 USDT changes which stops
   and horizons are executable.
2. **Universe.** The owner's earlier project found the only factors with out-of-sample evidence are
   cross-sectional long/short books across many coins (flow, carry). This project is BTC-only by
   charter. Widening it is a scope decision.
3. **Paid data.** X API basic tier, or a sentiment vendor, if social signals are to be tested on
   history rather than collected forward for months.
4. **Forward collection on the VPS.** Deploying `b1k-social.timer` costs nothing and starts the
   clock on a social dataset; it needs the VPS connection (network allowlist + a dedicated SSH key).

Continuing to run new rule families on the same 2020–2026 data without one of these changes would be
a search for the one in twenty that passes by chance; the registrations' failure criteria forbid it.

## Operations
- Repository: github.com/shengchen424-sketch/btc1000x, 35 tests passing, data 0.3 GB (rebuildable),
  alt-data snapshots in `evidence/alt/`.
- No order has been or can be sent (`LIVE_TRADING` False; live path raises).
