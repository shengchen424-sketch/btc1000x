"""EXP-007 — FOMC pre-announcement drift (position-based, daily clock).

Pyo & Lee (2020): BTC +0.96 % on the day before an FOMC statement, -1 % on the statement day.
Statement dates from evidence/alt/fomc_statement_dates.json (federalreserve.gov). The schedule is
public a year ahead, so a position decided on the close of D-2 for the day D-1 is point-in-time.

PRE_LONG : target +1 decided at the close of D-2 (held during day D-1), flat at the close of D-1.
DAY_SHORT: target -1 decided at the close of D-1 (held during day D), flat at the close of D.
BOTH     : the two combined.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from b1k.config import PATHS


def statement_days() -> set[str]:
    j = json.loads((PATHS.evidence / "alt" / "fomc_statement_dates.json").read_text())
    return set(j["dates"])


def fomc_positions(daily: pd.DataFrame, mode: str = "PRE_LONG") -> pd.Series:
    days = statement_days()
    ds = pd.to_datetime(daily["open_time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d").to_numpy()
    idx = {d: i for i, d in enumerate(ds)}
    pos = np.zeros(len(daily))
    for d in days:
        if d not in idx:
            continue
        i = idx[d]
        if mode in ("PRE_LONG", "BOTH") and i - 2 >= 0:
            pos[i - 2] = 1.0       # decided at close of D-2 -> held during D-1
        if mode in ("DAY_SHORT", "BOTH") and i - 1 >= 0:
            pos[i - 1] = -1.0      # decided at close of D-1 -> held during D
    return pd.Series(pos, index=daily.index)
