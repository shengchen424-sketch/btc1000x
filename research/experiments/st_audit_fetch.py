"""ST-AUDIT-001 data: daily klines for every Binance UM USDT perpetual (public archive), to rebuild the
Smart Trader flow book's universe panel independently. Usage: python st_audit_fetch.py SYMBOLS_FILE START_YM END_YM"""
from __future__ import annotations

import io
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from b1k.config import PATHS

OUT = PATHS.data_parquet / "um_1d"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count",
        "taker_buy_volume", "taker_buy_quote", "ignore"]
S = requests.Session()


def months(a: str, b: str):
    d = date.fromisoformat(a + "-01"); e = date.fromisoformat(b + "-01")
    while d <= e:
        yield d.strftime("%Y-%m")
        d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)


def fetch(sym: str, ym: str):
    url = f"{BASE}/{sym}/1d/{sym}-1d-{ym}.zip"
    for a in range(3):
        try:
            r = S.get(url, timeout=40)
            if r.status_code == 404:
                return sym, ym, None
            if r.status_code == 200:
                z = zipfile.ZipFile(io.BytesIO(r.content))
                raw = z.read(z.namelist()[0])
                head = raw[:100].decode("utf-8", "ignore").split("\n")[0]
                df = pd.read_csv(io.BytesIO(raw), header=0 if head.startswith("open") else None, names=None if head.startswith("open") else COLS)
                df.columns = COLS[: len(df.columns)]
                if df["open_time"].iloc[0] > 10**14:
                    df["open_time"] = df["open_time"] // 1000
                df = df[["open_time", "open", "high", "low", "close", "volume", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote"]].copy()
                df["symbol"] = sym
                return sym, ym, df
        except Exception:
            pass
        time.sleep(1.0 * (a + 1))
    return sym, ym, "ERR"


def main(symfile: str, a: str, b: str) -> None:
    syms = [s.strip() for s in open(symfile) if s.strip().endswith("USDT") and s.strip().isascii()]
    jobs = [(s, ym) for s in syms for ym in months(a, b)]
    print("jobs", len(jobs), flush=True)
    frames, errs, n = [], [], 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for sym, ym, df in ex.map(lambda j: fetch(*j), jobs):
            n += 1
            if isinstance(df, pd.DataFrame):
                frames.append(df)
            elif df == "ERR":
                errs.append((sym, ym))
            if n % 2000 == 0:
                print("done", n, "frames", len(frames), "errs", len(errs), flush=True)
                pd.concat(frames).to_parquet(OUT / "um_1d_partial.parquet", index=False)
    panel = pd.concat(frames).sort_values(["symbol", "open_time"]).reset_index(drop=True)
    panel.to_parquet(OUT / "um_1d.parquet", index=False)
    Path(OUT / "ERRORS.txt").write_text("\n".join(f"{s},{m}" for s, m in errs))
    print("rows", len(panel), "symbols", panel["symbol"].nunique(), "errs", len(errs))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
