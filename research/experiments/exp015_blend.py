"""EXP-015: flow ranking blended with 14-day residual momentum, paired against the flow book."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp001_baseline import git_head  # noqa: E402
from st_audit_book import build_panel, signals, load_funding_daily  # noqa: E402
from exp013_incremental import compare, IND, DEV  # noqa: E402
from exp014_relative_value import residual_scores, run_book  # noqa: E402

from b1k.config import PATHS

OUT = PATHS.results / "EXP-015"


def z(df: pd.DataFrame) -> pd.DataFrame:
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)


def main():
    head = git_head()
    OUT.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    px, flow, in_univ = signals(panel)
    funding = load_funding_daily(px.index)
    A = pd.read_parquet(PATHS.results / "EXP-013" / "daily_A.parquet")["A"]
    rm14 = residual_scores(px, in_univ, 14)
    zf, zr = z(flow), z(rm14)
    books = {"BLEND50": (zf + zr).where(in_univ & flow.notna() & rm14.notna()),
             "BLEND25": (zf + 0.5 * zr).where(in_univ & flow.notna() & rm14.notna())}
    results = {}
    for name, score in books.items():
        B = run_book(px, score, funding)
        B.rename(name).to_frame().to_parquet(OUT / f"daily_{name}.parquet")
        ind, dev = compare(A, B, *IND), compare(A, B, *DEV)
        same = np.sign(ind["ann_diff_pct"]) == np.sign(dev["ann_diff_pct"])
        gate = "DISCARD"
        if ind["ann_diff_pct"] > 0 and ind["ci95_ann_pct"][0] > 0 and ind["p_one_sided"] < 0.025 and same:
            gate = "ADOPT-CANDIDATE"
        elif ind["ann_diff_pct"] > 0 and ind["p_one_sided"] < 0.05 and same:
            gate = "LEAD"
        results[name] = {"independent_2025_26": ind, "dev_2023_24": dev, "same_sign": bool(same), "gate": gate}
        print(name, "| 2025-26 diff", ind["ann_diff_pct"], "CI", ind["ci95_ann_pct"], "p", round(ind["p_one_sided"], 4),
              "| 2023-24 diff", dev["ann_diff_pct"], "| B", ind["B"], "| A", ind["A"], "|", gate, flush=True)
    json.dump({"experiment": "EXP-015", "git_head": head, "results": results}, open(OUT / "verdict.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
