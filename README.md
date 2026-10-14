# BTC 1000X

Research-grade, adaptive, multi-strategy BTCUSDT perpetual system for Bitget. Starting capital 10 USDT.
**Research and DRY_RUN only.** No order is sent by any code in this repository; live execution requires
the owner's written authorisation, a dedicated sub-account and a controlled stop-order test.

Read in this order: `docs/PHASE1_REPORT.md` (status), `RUNBOOK.md` (operate), `research/registrations/`
(what was promised before each run), `research/results/` (what happened).

## Layout

```
src/b1k/
  config/      frozen defaults: risk (RULE 8), costs (verified Bitget rules), chronological splits
  data/        Binance archive -> Parquet with manifests; DuckDB loader; resampling; sealed holdout
  features/    causal indicators
  regime/      transparent 4h regime baseline
  strategies/  common interface (SignalIntent); A FAILED_BREAK; B TREND_PULLBACK
  backtest/    event-driven engine with 1m exit resolution; metrics with uncertainty
  portfolio/   regime router (eligibility learned on TRAIN only)
  risk/        deterministic risk engine, kill switch, 10 USDT feasibility calculator
  execution/   Bitget public data, DRY_RUN order payloads, forward shadow runner
  learning/    trade log schema, loss taxonomy, winner profiling (hypothesis generation only)
  monitoring/  health status
tests/         unit, integration, regression, leakage, execution
research/      experiments (runners), registrations (pre-run), results, strategy_registry
evidence/      exchange metadata snapshots, data quality, parity measurements
ops/           systemd units for the shadow runner
```

## Quick start

```
pip install -e .[dev]
python -m pytest
python -m b1k.data.binance_archive          # ~180 MB Parquet, 2020-01 .. yesterday
python -m b1k.data.quality
python -m b1k.risk.feasibility
python research/experiments/exp001_baseline.py
python -m b1k.execution.shadow run          # one DRY_RUN pass on live Bitget bars
```

## Hard rules

- `RISK.DRY_RUN = True`, `RISK.LIVE_TRADING = False`; `execution/orders.submit` raises if asked to go live.
- The holdout (2025-01-01 .. 2026-09-30) is sealed; `data.store.load_1m` drops it unless
  `B1K_UNSEAL_HOLDOUT=<experiment>` is set, and every unseal is logged.
- Experiments refuse to run on uncommitted code.
- No martingale, no averaging down, one position at a time, 1 % planned loss per trade.
