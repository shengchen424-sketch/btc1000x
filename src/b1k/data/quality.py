"""Data quality: gaps, duplicates, timestamp sanity, freshness, Bitget parity. Reports, never repairs."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests


def validate_1m(df: pd.DataFrame) -> dict:
    ot = df["open_time"].to_numpy()
    d = np.diff(ot)
    gaps = np.where(d > 60_000)[0]
    gap_list = [{"after": int(ot[i]), "missing_bars": int(d[i] // 60_000 - 1)} for i in gaps[:50]]
    bad_ohlc = int(((df["high"] < df[["open", "close"]].max(axis=1)) |
                    (df["low"] > df[["open", "close"]].min(axis=1))).sum())
    return {
        "rows": int(len(df)),
        "first": pd.to_datetime(ot[0], unit="ms", utc=True).isoformat() if len(ot) else None,
        "last": pd.to_datetime(ot[-1], unit="ms", utc=True).isoformat() if len(ot) else None,
        "duplicates": int(pd.Series(ot).duplicated().sum()),
        "non_monotonic": int((d <= 0).sum()),
        "misaligned": int((ot % 60_000 != 0).sum()),
        "gaps": int(len(gaps)),
        "missing_bars_total": int(sum(max(x // 60_000 - 1, 0) for x in d[d > 60_000])),
        "largest_gaps": sorted(gap_list, key=lambda g: -g["missing_bars"])[:10],
        "bad_ohlc_rows": bad_ohlc,
        "zero_volume_bars": int((df["volume"] <= 0).sum()),
    }


def freshness_seconds(df: pd.DataFrame) -> float:
    last_close = df["open_time"].iloc[-1] / 1000 + 60
    return datetime.now(timezone.utc).timestamp() - last_close


def bitget_parity(df1m: pd.DataFrame, granularity: str = "15m", limit: int = 1000) -> dict:
    """Compare Binance-derived bars with Bitget's own candles for the latest window.
    Returns bps statistics; a one-off measurement, saved to evidence by the caller."""
    from b1k.data.store import resample
    rule = {"15m": "15m", "1H": "1h", "4H": "4h"}[granularity]
    r = requests.get("https://api.bitget.com/api/v2/mix/market/candles",
                     params={"productType": "USDT-FUTURES", "symbol": "BTCUSDT",
                             "granularity": granularity, "limit": limit}, timeout=30)
    r.raise_for_status()
    bg = pd.DataFrame(r.json()["data"], columns=["open_time", "open", "high", "low", "close", "vol", "qvol"])
    bg = bg.astype({"open_time": "int64", "open": float, "high": float, "low": float, "close": float})
    bn = resample(df1m, rule)
    m = bg.merge(bn, on="open_time", suffixes=("_bg", "_bn"))
    if m.empty:
        return {"overlap_bars": 0}
    close_bps = 1e4 * (m["close_bg"] / m["close_bn"] - 1)
    hi_bps = 1e4 * (m["high_bg"] / m["high_bn"] - 1)
    lo_bps = 1e4 * (m["low_bg"] / m["low_bn"] - 1)
    rb = np.log(m["close_bg"]).diff().dropna()
    rn = np.log(m["close_bn"]).diff().dropna()
    return {
        "granularity": granularity, "overlap_bars": int(len(m)),
        "close_bps_mean": float(close_bps.mean()), "close_bps_p99_abs": float(close_bps.abs().quantile(0.99)),
        "high_bps_p99_abs": float(hi_bps.abs().quantile(0.99)), "low_bps_p99_abs": float(lo_bps.abs().quantile(0.99)),
        "return_corr": float(np.corrcoef(rb, rn)[0, 1]),
        "measured_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    from b1k.config import PATHS
    from b1k.data.store import load_1m
    from b1k.config import SPLITS
    df = load_1m()
    rep = validate_1m(df)
    rep["freshness_s"] = freshness_seconds(df)
    rep["note"] = (f"rows inside the sealed holdout {SPLITS.holdout} are excluded by load_1m, so one "
                   f"gap of that length is expected and is not a data defect")
    PATHS.evidence.mkdir(parents=True, exist_ok=True)
    (PATHS.evidence / "data_quality_1m.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
