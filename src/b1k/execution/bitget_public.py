"""Read-only Bitget public market data (no credentials, no order endpoints in this module)."""
from __future__ import annotations

import time

import pandas as pd
import requests

API = "https://api.bitget.com/api/v2/mix/market"
PT = "USDT-FUTURES"
GRAN = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1H", "4h": "4H"}


def _get(path: str, params: dict, retries: int = 3) -> dict:
    delay = 1.0
    for i in range(retries + 1):
        try:
            r = requests.get(f"{API}/{path}", params=params, timeout=20)
            j = r.json()
            if r.status_code == 200 and j.get("code") == "00000":
                return j
        except (requests.RequestException, ValueError):
            pass
        if i < retries:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"bitget {path} failed")


def contract(symbol: str = "BTCUSDT") -> dict:
    return _get("contracts", {"productType": PT, "symbol": symbol})["data"][0]


def ticker(symbol: str = "BTCUSDT") -> dict:
    return _get("ticker", {"productType": PT, "symbol": symbol})["data"][0]


def candles(symbol: str, rule: str, limit: int = 1000, end_ms: int | None = None) -> pd.DataFrame:
    """Closed candles only (the last row from the API is the live, unfinished bar and is dropped)."""
    p = {"productType": PT, "symbol": symbol, "granularity": GRAN[rule], "limit": min(limit, 1000)}
    if end_ms:
        p["endTime"] = end_ms
    d = _get("candles", p)["data"]
    df = pd.DataFrame(d, columns=["open_time", "open", "high", "low", "close", "volume", "quote_volume"])
    df = df.astype({"open_time": "int64", "open": float, "high": float, "low": float, "close": float,
                    "volume": float, "quote_volume": float}).sort_values("open_time").reset_index(drop=True)
    step = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}[rule]
    df["close_time"] = df["open_time"] + step
    now = int(time.time() * 1000)
    return df[df["close_time"] <= now].reset_index(drop=True)


def next_funding(symbol: str = "BTCUSDT") -> tuple[float, int | None]:
    t = ticker(symbol)
    try:
        nf = _get("funding-time", {"productType": PT, "symbol": symbol})["data"][0]
        return float(t["fundingRate"]), int(nf["nextFundingTime"])
    except Exception:
        return float(t["fundingRate"]), None
