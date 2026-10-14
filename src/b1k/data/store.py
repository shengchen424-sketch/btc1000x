"""Load bars, resample, enforce point-in-time availability and the sealed holdout."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from b1k.config import PATHS, SPLITS

RULE_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}


def _parquet_files(symbol: str, interval: str) -> list[Path]:
    d = PATHS.data_parquet / f"{symbol}_{interval}"
    return sorted(d.glob("*.parquet"))


def load_1m(symbol: str = "BTCUSDT", start: str | None = None, end: str | None = None,
            allow_holdout: bool = False) -> pd.DataFrame:
    """1m bars, UTC, deduplicated, sorted. `end` is inclusive by date. Rows inside the sealed
    holdout are removed unless allow_holdout (which requires B1K_UNSEAL_HOLDOUT and is logged)."""
    files = _parquet_files(symbol, "1m")
    if not files:
        raise FileNotFoundError("no 1m parquet; run python -m b1k.data.binance_archive")
    con = duckdb.connect()
    q = f"SELECT * FROM read_parquet({[str(f) for f in files]})"
    conds = []
    if start:
        conds.append(f"open_time >= {int(pd.Timestamp(start, tz='UTC').timestamp() * 1000)}")
    if end:
        conds.append(f"open_time < {int((pd.Timestamp(end, tz='UTC') + pd.Timedelta(days=1)).timestamp() * 1000)}")
    if conds:
        q += " WHERE " + " AND ".join(conds)
    df = con.execute(q + " ORDER BY open_time").df()
    df = df.drop_duplicates("open_time", keep="last").reset_index(drop=True)
    df["ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    if not allow_holdout:
        h0 = pd.Timestamp(SPLITS.holdout[0], tz="UTC")
        h1 = pd.Timestamp(SPLITS.holdout[1], tz="UTC") + pd.Timedelta(days=1)
        df = df[(df["ts"] < h0) | (df["ts"] >= h1)].reset_index(drop=True)
    else:
        _log_unseal()
    return df


def _log_unseal() -> None:
    exp = os.environ.get("B1K_UNSEAL_HOLDOUT")
    if not exp:
        raise PermissionError("holdout is sealed: set B1K_UNSEAL_HOLDOUT=<experiment id> deliberately")
    PATHS.results.mkdir(parents=True, exist_ok=True)
    with open(PATHS.results / "unseal_log.jsonl", "a") as f:
        f.write(json.dumps({"experiment": exp, "at": datetime.now(timezone.utc).isoformat()}) + "\n")


def resample(df1m: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Right-closed, left-labelled bars from 1m bars. A bar at label T covers [T, T+rule) and is
    known at T+rule (its close_time). Partial trailing bars are dropped."""
    step = RULE_MS[rule]
    g = (df1m["open_time"] // step) * step
    agg = df1m.groupby(g).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                              close=("close", "last"), volume=("volume", "sum"),
                              quote_volume=("quote_volume", "sum"), count=("count", "sum"),
                              taker_buy_volume=("taker_buy_volume", "sum"), n1m=("open", "size"))
    agg.index.name = "open_time"
    agg = agg.reset_index()
    expected = step // 60_000
    agg = agg[agg["n1m"] == expected].drop(columns="n1m").reset_index(drop=True)
    agg["close_time"] = agg["open_time"] + step
    agg["ts"] = pd.to_datetime(agg["open_time"], unit="ms", utc=True)
    return agg


def split_mask(ts: pd.Series, name: str) -> pd.Series:
    a, b = getattr(SPLITS, name)
    return (ts >= pd.Timestamp(a, tz="UTC")) & (ts < pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1))


def file_digest(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()
