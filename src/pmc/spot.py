"""Binance SPOT klines from the public archive (Polymarket hourly / daily markets resolve on spot
BTC/USDT; b1k.data.binance_archive serves the UM perpetual). Cached as parquet under data/cache/."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from b1k.config import PATHS
from b1k.data.binance_archive import _fetch_klines, _months

BASE = "https://data.binance.vision/data/spot"
CACHE = PATHS.root / "data" / "cache" / "spot"


def _cached(url: str, path: Path) -> pd.DataFrame | None:
    if path.exists():
        return pd.read_parquet(path)
    df = _fetch_klines(url, "spot_klines")
    if df is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return df


def day(symbol: str, interval: str, d: str) -> pd.DataFrame | None:
    url = f"{BASE}/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{d}.zip"
    return _cached(url, CACHE / f"{symbol}_{interval}" / f"{d}.parquet")


def month(symbol: str, interval: str, ym: str) -> pd.DataFrame | None:
    url = f"{BASE}/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{ym}.zip"
    return _cached(url, CACHE / f"{symbol}_{interval}" / f"{ym}.parquet")


def range_1m(start: str, end: str, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """1 m spot klines for whole months covering [start, end] (ISO dates), indexed by open time UTC."""
    parts = [month(symbol, "1m", ym) for ym in _months(start, end)]
    df = pd.concat([p for p in parts if p is not None], ignore_index=True)
    df["t"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.drop_duplicates("t").set_index("t").sort_index()
    return df.loc[start:end]
