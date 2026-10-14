"""Frozen project defaults. Changing RISK or COSTS is a research decision: record it in
research/registrations/ before any run that depends on it."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("B1K_ROOT", Path(__file__).resolve().parents[3]))


@dataclass(frozen=True)
class Paths:
    root: Path = ROOT
    data_raw: Path = ROOT / "data" / "raw"
    data_parquet: Path = ROOT / "data" / "parquet"
    manifests: Path = ROOT / "data" / "manifests"
    evidence: Path = ROOT / "evidence"
    results: Path = ROOT / "research" / "results"
    state: Path = ROOT / "state"


@dataclass(frozen=True)
class RiskDefaults:
    """RULE 8 research defaults. Not a guarantee of loss containment."""
    INITIAL_EQUITY: float = 10.0
    RISK_PER_TRADE: float = 0.01
    DAILY_LOSS_LIMIT: float = 0.03
    WEEKLY_LOSS_LIMIT: float = 0.06
    MAX_CONCURRENT_POSITIONS: int = 1
    MARGIN_MODE: str = "ISOLATED"
    DRY_RUN: bool = True
    LIVE_TRADING: bool = False
    MAX_LEVERAGE: int = 10          # feasibility: liquidation must stay >= 2x the stop distance
    LIQ_BUFFER_MULT: float = 2.0
    MAX_DATA_AGE_S: int = 180       # a signal on data older than this is stale


@dataclass(frozen=True)
class CostModel:
    """Bitget BTCUSDT USDT-FUTURES, verified 2026-10-14 (evidence/exchange/contract_BTCUSDT.json).
    Every entry and exit is modelled as a taker fill: stop and take-profit trigger orders on Bitget
    execute as market orders, and the shadow runner uses market entries."""
    taker_fee: float = 0.0006
    maker_fee: float = 0.0002
    slip_entry: float = 0.0003      # 3 bps: market order into a ~0.1 USD spread book, small size
    slip_exit_trigger: float = 0.0010  # 10 bps: a stop fires into a moving market
    slip_exit_time: float = 0.0003
    funding_interval_h: int = 8
    min_qty_btc: float = 0.0001
    qty_step_btc: float = 0.0001
    min_notional_usdt: float = 5.0
    tier1_mmr: float = 0.004


@dataclass(frozen=True)
class Splits:
    """Chronological splits. HOLDOUT is sealed: loading it requires B1K_UNSEAL_HOLDOUT=<experiment id>
    and every unseal is appended to research/results/unseal_log.jsonl."""
    train: tuple[str, str] = ("2020-01-01", "2022-12-31")
    validation: tuple[str, str] = ("2023-01-01", "2024-12-31")
    holdout: tuple[str, str] = ("2025-01-01", "2026-09-30")
    forward_start: str = "2026-10-14"


PATHS = Paths()
RISK = RiskDefaults()
COSTS = CostModel()
SPLITS = Splits()
