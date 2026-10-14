"""Historical BTCUSDT USDT-M perpetual data from the public Binance archive (data.binance.vision).

Why Binance and not Bitget: Bitget's public history-candles endpoint serves 200 bars per request
(1m since 2020-09 would be ~15,000 requests) and has no funding history before ~3 months ago.
Binance UM BTCUSDT 1m bars track Bitget's within a few bps (Smart Trader RG01 parity: close
difference p99 3.2 bps on 4,582 15m bars; this project re-measures in data/quality.py).

Everything downloaded is recorded in data/manifests/*.jsonl with url, sha256, size, fetch time.
Nothing is fabricated: a month that is missing from the archive stays missing and is reported.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

import pandas as pd
import requests

from b1k.config import PATHS

BASE = "https://data.binance.vision/data/futures/um"
KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
              "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


@dataclass(frozen=True)
class FetchRecord:
    url: str
    status: int
    sha256: str | None
    bytes: int
    fetched_at: str
    rows: int


def _get(url: str, retries: int = 4, timeout: int = 120) -> requests.Response | None:
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return r
        except requests.RequestException:
            pass
        if attempt < retries:
            time.sleep(delay)
            delay *= 2
    return None


def _manifest_append(name: str, rec: FetchRecord) -> None:
    PATHS.manifests.mkdir(parents=True, exist_ok=True)
    with open(PATHS.manifests / f"{name}.jsonl", "a") as f:
        f.write(json.dumps(asdict(rec)) + "\n")


def _read_zip_csv(content: bytes, names: list[str] | None) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        inner = z.namelist()[0]
        raw = z.read(inner)
    head = raw[:200].decode("utf-8", "ignore").split("\n")[0]
    has_header = not head.split(",")[0].strip().lstrip("-").isdigit()
    return pd.read_csv(io.BytesIO(raw), header=0 if has_header else None,
                       names=None if has_header else names)


def _months(start: str, end: str) -> list[str]:
    s = date.fromisoformat(start).replace(day=1)
    e = date.fromisoformat(end).replace(day=1)
    out = []
    while s <= e:
        out.append(s.strftime("%Y-%m"))
        s = (s.replace(day=28) + timedelta(days=4)).replace(day=1)
    return out


def fetch_klines_month(symbol: str, interval: str, ym: str) -> pd.DataFrame | None:
    url = f"{BASE}/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{ym}.zip"
    return _fetch_klines(url, f"klines_{interval}")


def fetch_klines_day(symbol: str, interval: str, d: str) -> pd.DataFrame | None:
    url = f"{BASE}/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{d}.zip"
    return _fetch_klines(url, f"klines_{interval}")


def _fetch_klines(url: str, manifest: str) -> pd.DataFrame | None:
    r = _get(url)
    now = datetime.now(timezone.utc).isoformat()
    if r is None or r.status_code != 200:
        _manifest_append(manifest, FetchRecord(url, -1 if r is None else r.status_code, None, 0, now, 0))
        return None
    df = _read_zip_csv(r.content, KLINE_COLS)
    df.columns = KLINE_COLS[: len(df.columns)]
    df = df[["open_time", "open", "high", "low", "close", "volume", "quote_volume", "count",
             "taker_buy_volume"]].copy()
    # Binance switched open_time to microseconds for 2025+ files; normalise to ms
    if df["open_time"].iloc[0] > 10**14:
        df["open_time"] = df["open_time"] // 1000
    df["open_time"] = df["open_time"].astype("int64")
    for c in ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_volume"]:
        df[c] = df[c].astype("float64")
    df["count"] = df["count"].astype("int64")
    _manifest_append(manifest, FetchRecord(url, 200, hashlib.sha256(r.content).hexdigest(),
                                           len(r.content), now, len(df)))
    return df


def fetch_funding_month(symbol: str, ym: str) -> pd.DataFrame | None:
    url = f"{BASE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"
    r = _get(url)
    now = datetime.now(timezone.utc).isoformat()
    if r is None or r.status_code != 200:
        _manifest_append("funding", FetchRecord(url, -1 if r is None else r.status_code, None, 0, now, 0))
        return None
    df = _read_zip_csv(r.content, ["calc_time", "funding_interval_hours", "last_funding_rate"])
    df = df.rename(columns={"calc_time": "funding_time", "last_funding_rate": "funding_rate"})
    if df["funding_time"].iloc[0] > 10**14:
        df["funding_time"] = df["funding_time"] // 1000
    df = df[["funding_time", "funding_rate"]].astype({"funding_time": "int64", "funding_rate": "float64"})
    _manifest_append("funding", FetchRecord(url, 200, hashlib.sha256(r.content).hexdigest(),
                                            len(r.content), now, len(df)))
    return df


def build_klines(symbol: str = "BTCUSDT", interval: str = "1m", start: str = "2020-01-01",
                 end: str | None = None) -> Path:
    """Download monthly files from start to the last full month, then daily files for the current
    month up to `end` (default: yesterday UTC). Writes one parquet per month under data/parquet/."""
    end_d = date.fromisoformat(end) if end else datetime.now(timezone.utc).date() - timedelta(days=1)
    out_dir = PATHS.data_parquet / f"{symbol}_{interval}"
    out_dir.mkdir(parents=True, exist_ok=True)
    last_full = (end_d.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    missing: list[str] = []
    for ym in _months(start, last_full + "-01"):
        p = out_dir / f"{ym}.parquet"
        if p.exists():
            continue
        df = fetch_klines_month(symbol, interval, ym)
        if df is None:
            missing.append(ym)
            continue
        df.to_parquet(p, index=False)
    # current (partial) month from daily files
    cur = end_d.strftime("%Y-%m")
    if cur != last_full:
        frames = []
        d = end_d.replace(day=1)
        while d <= end_d:
            df = fetch_klines_day(symbol, interval, d.isoformat())
            if df is None:
                missing.append(d.isoformat())
            else:
                frames.append(df)
            d += timedelta(days=1)
        if frames:
            pd.concat(frames).to_parquet(out_dir / f"{cur}.partial.parquet", index=False)
    (out_dir / "MISSING.json").write_text(json.dumps(missing))
    return out_dir


def build_funding(symbol: str = "BTCUSDT", start: str = "2020-01-01", end: str | None = None) -> Path:
    end_d = date.fromisoformat(end) if end else datetime.now(timezone.utc).date()
    out = PATHS.data_parquet / f"{symbol}_funding.parquet"
    frames, missing = [], []
    last_full = (end_d.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    for ym in _months(start, last_full + "-01"):
        df = fetch_funding_month(symbol, ym)
        (frames if df is not None else missing).append(df if df is not None else ym)
    if frames:
        pd.concat(frames).drop_duplicates("funding_time").sort_values("funding_time").to_parquet(out, index=False)
    (PATHS.data_parquet / f"{symbol}_funding.MISSING.json").write_text(json.dumps(missing))
    return out


def build_premium_index(symbol: str = "BTCUSDT", interval: str = "1m", start: str = "2020-01-01",
                        end: str | None = None) -> Path:
    """premiumIndexKlines: (mark - index)/index per bar, the input to funding. Monthly files only."""
    end_d = date.fromisoformat(end) if end else datetime.now(timezone.utc).date()
    out_dir = PATHS.data_parquet / f"{symbol}_premium_{interval}"
    out_dir.mkdir(parents=True, exist_ok=True)
    last_full = (end_d.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    missing = []
    for ym in _months(start, last_full + "-01"):
        p = out_dir / f"{ym}.parquet"
        if p.exists():
            continue
        url = f"{BASE}/monthly/premiumIndexKlines/{symbol}/{interval}/{symbol}-{interval}-{ym}.zip"
        df = _fetch_klines(url, "premium")
        if df is None:
            missing.append(ym)
            continue
        df[["open_time", "open", "high", "low", "close"]].to_parquet(p, index=False)
    (out_dir / "MISSING.json").write_text(json.dumps(missing))
    return out_dir


def build_metrics(symbol: str = "BTCUSDT", start: str = "2021-06-01", end: str | None = None) -> Path:
    """Daily metrics files (5-minute open interest, long/short ratios, taker ratio). One parquet per month."""
    end_d = date.fromisoformat(end) if end else datetime.now(timezone.utc).date() - timedelta(days=1)
    out_dir = PATHS.data_parquet / f"{symbol}_metrics_5m"
    out_dir.mkdir(parents=True, exist_ok=True)
    missing = []
    d = date.fromisoformat(start)
    frames, cur = [], d.strftime("%Y-%m")
    while d <= end_d:
        ym = d.strftime("%Y-%m")
        if ym != cur:
            if frames:
                pd.concat(frames).to_parquet(out_dir / f"{cur}.parquet", index=False)
            frames, cur = [], ym
        if not (out_dir / f"{ym}.parquet").exists():
            url = f"{BASE}/daily/metrics/{symbol}/{symbol}-metrics-{d.isoformat()}.zip"
            r = _get(url)
            now = datetime.now(timezone.utc).isoformat()
            if r is None or r.status_code != 200:
                missing.append(d.isoformat())
                _manifest_append("metrics", FetchRecord(url, -1 if r is None else r.status_code, None, 0, now, 0))
            else:
                df = _read_zip_csv(r.content, None)
                df["create_time"] = pd.to_datetime(df["create_time"], utc=True).astype("int64") // 10**6
                df = df.rename(columns={"create_time": "open_time"}).drop(columns=["symbol"])
                frames.append(df)
                _manifest_append("metrics", FetchRecord(url, 200, hashlib.sha256(r.content).hexdigest(),
                                                        len(r.content), now, len(df)))
        d += timedelta(days=1)
    if frames:
        pd.concat(frames).to_parquet(out_dir / f"{cur}.parquet", index=False)
    (out_dir / "MISSING.json").write_text(json.dumps(missing))
    return out_dir


if __name__ == "__main__":
    import sys
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "klines"):
        print(build_klines())
    if what in ("all", "funding"):
        print(build_funding())
    if what in ("premium",):
        print(build_premium_index())
    if what in ("metrics",):
        print(build_metrics())
